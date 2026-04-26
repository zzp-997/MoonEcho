"""骚扰识别规则引擎。

实现 modules_design.md 7.4 第一层规则引擎，基于 Redis 频率计数：

规则列表：
1. 同一对话1分钟内超过10条消息 → 速率限制
2. 单日向超过10人发好友申请 → 冻结申请功能24小时
3. 消息中出现微信号/手机号格式 → 标记+提醒
4. 同一用户单日对另一用户评论超5条 → 提示"对方可能需要空间"
5. 树洞场景：单日评论超5条提示、单日发布帖子超3条限速

设计要点：
- 使用 Redis 做频率计数，key 格式：harassment:{type}:{user_id}:{target_id}:{date}
- 支持可配置的阈值参数
- 兼容 MockRedis（开发环境）
- 所有操作均为建议性提醒，由上层决定是否强制执行
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 骚扰检测规则类型枚举
# ---------------------------------------------------------------------------

class HarassmentRuleType(str, Enum):
    """骚扰检测规则类型。"""

    # 对话消息速率限制
    CHAT_MESSAGE_RATE = "chat_message_rate"

    # 好友申请频率限制
    FRIEND_REQUEST_RATE = "friend_request_rate"

    # 联系方式检测（微信号/手机号）
    CONTACT_INFO_DETECTED = "contact_info_detected"

    # 针对同一用户的评论频率
    TARGETED_COMMENT_RATE = "targeted_comment_rate"

    # 树洞评论频率
    TREEHOLE_COMMENT_RATE = "treehole_comment_rate"

    # 树洞发布频率
    TREEHOLE_POST_RATE = "treehole_post_rate"


# ---------------------------------------------------------------------------
# 骚扰检测结果
# ---------------------------------------------------------------------------

class HarassmentLevel(str, Enum):
    """骚扰检测级别。"""

    NONE = "none"           # 无异常
    WARN = "warn"           # 提醒（建议性，不强制）
    RATE_LIMIT = "rate_limit"  # 限速（强制执行）


@dataclass(slots=True)
class HarassmentCheckResult:
    """单条规则检测结果。"""

    rule_type: HarassmentRuleType
    level: HarassmentLevel = HarassmentLevel.NONE
    triggered: bool = False
    current_count: int = 0
    threshold: int = 0
    message: str = ""
    action: str = ""  # none / warn / rate_limit / freeze


@dataclass(slots=True)
class HarassmentDetectionResult:
    """骚扰检测综合结果。"""

    has_warning: bool = False
    has_rate_limit: bool = False
    results: list[HarassmentCheckResult] = field(default_factory=list)
    warning_messages: list[str] = field(default_factory=list)
    rate_limit_message: str = ""

    def add_result(self, result: HarassmentCheckResult) -> None:
        """添加一条检测结果。"""
        self.results.append(result)
        if result.triggered:
            if result.level == HarassmentLevel.WARN:
                self.has_warning = True
                self.warning_messages.append(result.message)
            elif result.level == HarassmentLevel.RATE_LIMIT:
                self.has_rate_limit = True
                if not self.rate_limit_message:
                    self.rate_limit_message = result.message


# ---------------------------------------------------------------------------
# 默认阈值配置
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class HarassmentThresholds:
    """骚扰检测阈值配置。

    所有阈值均可通过构造函数覆盖以支持动态配置。

    Attributes:
        chat_message_window_seconds: 对话消息速率检测窗口（秒）
        chat_message_max_count: 窗口内最大消息数
        friend_request_max_per_day: 单日好友申请最大数
        friend_request_freeze_hours: 好友申请冻结时长（小时）
        targeted_comment_max_per_day: 单日对同一用户最大评论数
        treehole_comment_max_per_day: 单日树洞最大评论数
        treehole_post_max_per_day: 单日树洞最大发布数
        treehole_post_rate_limit_seconds: 树洞发布限速间隔（秒）
    """

    # 对话消息速率
    chat_message_window_seconds: int = 60
    chat_message_max_count: int = 10

    # 好友申请频率
    friend_request_max_per_day: int = 10
    friend_request_freeze_hours: int = 24

    # 针对同一用户的评论频率
    targeted_comment_max_per_day: int = 5

    # 树洞场景频率
    treehole_comment_max_per_day: int = 5
    treehole_post_max_per_day: int = 3
    treehole_post_rate_limit_seconds: int = 300  # 5分钟


# ---------------------------------------------------------------------------
# 联系方式正则模式
# ---------------------------------------------------------------------------

# 微信号格式检测（6-20位字母开头，允许字母数字下划线连字符）
WECHAT_ID_PATTERN = re.compile(
    r'(?:微信号?|微信|vx|weixin)[:\s：]?\s*'
    r'([a-zA-Z][a-zA-Z0-9_-]{5,19})',
    re.IGNORECASE,
)

# 手机号格式检测（中国大陆手机号）
PHONE_NUMBER_PATTERN = re.compile(
    r'(?:手机号?|电话|tel|phone|联系方式)[:\s：]?\s*'
    r'(1[3-9]\d{9})'
    r'|'
    r'(1[3-9]\d{9})',  # 直接出现的手机号
)

# QQ号格式检测
QQ_NUMBER_PATTERN = re.compile(
    r'(?:QQ号?|qq号?|加QQ|加qq)[:\s：]?\s*(\d{5,12})',
    re.IGNORECASE,
)

# 通用联系方式检测（宽松模式，检测内容中直接出现的联系方式）
CONTACT_INFO_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("wechat", WECHAT_ID_PATTERN),
    ("phone", PHONE_NUMBER_PATTERN),
    ("qq", QQ_NUMBER_PATTERN),
]


# ---------------------------------------------------------------------------
# 骚扰规则引擎核心
# ---------------------------------------------------------------------------

class HarassmentDetector:
    """骚扰识别规则引擎。

    基于 Redis 频率计数实现多层骚扰检测。
    所有检测均为建议性结果，由上层服务决定是否强制执行。

    使用示例：
        detector = HarassmentDetector(redis_client)
        result = await detector.check_treehole_post_rate(user_id)
        if result.has_rate_limit:
            # 限速处理
    """

    def __init__(
        self,
        redis: Any,
        thresholds: HarassmentThresholds | None = None,
    ) -> None:
        """初始化骚扰规则引擎。

        Args:
            redis: Redis 客户端（兼容 MockRedis）
            thresholds: 阈值配置（可选，使用默认值）
        """
        self._redis = redis
        self._thresholds = thresholds or HarassmentThresholds()

        logger.info(
            "[HarassmentDetector] 初始化完成，阈值配置: "
            "chat_max=%d/%ds, friend_max=%d/d, comment_max=%d/d, "
            "treehole_comment_max=%d/d, treehole_post_max=%d/d",
            self._thresholds.chat_message_max_count,
            self._thresholds.chat_message_window_seconds,
            self._thresholds.friend_request_max_per_day,
            self._thresholds.targeted_comment_max_per_day,
            self._thresholds.treehole_comment_max_per_day,
            self._thresholds.treehole_post_max_per_day,
        )

    # =========================================================================
    # Redis 操作封装
    # =========================================================================

    async def _incr_and_get(
        self,
        key: str,
        ttl_seconds: int,
    ) -> int:
        """原子递增并获取计数值，同时设置过期时间。

        兼容 MockRedis，使用 incr + expire 分步操作。

        Args:
            key: Redis key
            ttl_seconds: 过期时间（秒）

        Returns:
            递增后的计数值
        """
        try:
            count = await self._redis.incr(key)
            # 仅在首次创建时设置过期时间
            if count == 1:
                await self._redis.expire(key, ttl_seconds)
            return count
        except Exception as e:
            logger.error(
                "[HarassmentDetector] Redis incr 操作异常, key=%s: %s",
                key, str(e)
            )
            # Redis 异常时不应阻断业务，返回 0 表示无限制
            return 0

    async def _get_count(self, key: str) -> int:
        """获取当前计数值。

        Args:
            key: Redis key

        Returns:
            当前计数值，key 不存在返回 0
        """
        try:
            value = await self._redis.get(key)
            if value is not None:
                # 兼容 bytes 和 str 类型（真实 Redis 返回 bytes）
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                return int(value)
            return 0
        except Exception as e:
            logger.error(
                "[HarassmentDetector] Redis get 操作异常, key=%s: %s",
                key, str(e)
            )
            return 0

    async def _set_with_ttl(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        """设置值并指定过期时间。

        Args:
            key: Redis key
            value: 值
            ttl_seconds: 过期时间（秒）
        """
        try:
            await self._redis.set(key, value, ex=ttl_seconds)
        except Exception as e:
            logger.error(
                "[HarassmentDetector] Redis set 操作异常, key=%s: %s",
                key, str(e)
            )

    def _build_key(
        self,
        rule_type: str,
        user_id: str,
        target_id: str = "",
        date: str | None = None,
    ) -> str:
        """构建 Redis key。

        格式：harassment:{type}:{user_id}:{target_id}:{date}

        Args:
            rule_type: 规则类型
            user_id: 用户ID
            target_id: 目标ID（可选）
            date: 日期字符串（可选，默认当天）

        Returns:
            Redis key
        """
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"harassment:{rule_type}:{user_id}:{target_id}:{date}"

    # =========================================================================
    # 对话消息速率检测
    # =========================================================================

    async def check_chat_message_rate(
        self,
        user_id: str,
        conversation_id: str,
    ) -> HarassmentCheckResult:
        """检测同一对话的消息速率。

        规则：同一对话1分钟内超过10条消息 → 速率限制

        Args:
            user_id: 用户ID
            conversation_id: 对话ID

        Returns:
            检测结果
        """
        key = self._build_key(
            HarassmentRuleType.CHAT_MESSAGE_RATE.value,
            user_id,
            conversation_id,
            datetime.now(timezone.utc).strftime("%Y%m%d%H%M"),  # 精确到分钟
        )
        count = await self._incr_and_get(
            key, self._thresholds.chat_message_window_seconds
        )

        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.CHAT_MESSAGE_RATE,
            current_count=count,
            threshold=self._thresholds.chat_message_max_count,
        )

        if count > self._thresholds.chat_message_max_count:
            result.triggered = True
            result.level = HarassmentLevel.RATE_LIMIT
            result.message = "消息发送太快了，先歇一歇吧"
            result.action = "rate_limit"
            logger.warning(
                "[HarassmentDetector] 对话消息速率超限，用户: %s, 对话: %s, 计数: %d",
                user_id, conversation_id, count,
            )

        return result

    # =========================================================================
    # 好友申请频率检测
    # =========================================================================

    async def check_friend_request_rate(
        self,
        user_id: str,
    ) -> HarassmentCheckResult:
        """检测好友申请频率。

        规则：单日向超过10人发好友申请 → 冻结申请功能24小时

        Args:
            user_id: 用户ID

        Returns:
            检测结果
        """
        # 检查是否已冻结
        freeze_key = self._build_key(
            "friend_request_freeze", user_id,
        )
        freeze_remaining = await self._get_count(freeze_key)
        if freeze_remaining > 0:
            return HarassmentCheckResult(
                rule_type=HarassmentRuleType.FRIEND_REQUEST_RATE,
                triggered=True,
                level=HarassmentLevel.RATE_LIMIT,
                current_count=0,
                threshold=self._thresholds.friend_request_max_per_day,
                message="好友申请功能暂不可用，请稍后再试",
                action="freeze",
            )

        # 递增当日申请计数
        count_key = self._build_key(
            HarassmentRuleType.FRIEND_REQUEST_RATE.value,
            user_id,
        )
        count = await self._incr_and_get(count_key, 86400)  # 24小时过期

        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.FRIEND_REQUEST_RATE,
            current_count=count,
            threshold=self._thresholds.friend_request_max_per_day,
        )

        if count > self._thresholds.friend_request_max_per_day:
            result.triggered = True
            result.level = HarassmentLevel.RATE_LIMIT
            result.message = "今日好友申请次数已达上限，请明天再试"
            result.action = "freeze"

            # 设置冻结标记
            freeze_seconds = self._thresholds.friend_request_freeze_hours * 3600
            await self._set_with_ttl(freeze_key, 1, freeze_seconds)

            logger.warning(
                "[HarassmentDetector] 好友申请频率超限，用户: %s, 计数: %d, 冻结: %dh",
                user_id, count, self._thresholds.friend_request_freeze_hours,
            )

        return result

    # =========================================================================
    # 联系方式检测
    # =========================================================================

    def check_contact_info(
        self,
        content: str,
    ) -> HarassmentCheckResult:
        """检测消息中的联系方式（微信号/手机号/QQ号）。

        规则：消息中出现联系方式格式 → 标记+提醒（建议性）

        Args:
            content: 消息内容

        Returns:
            检测结果
        """
        detected_types: list[str] = []

        for label, pattern in CONTACT_INFO_PATTERNS:
            if pattern.search(content):
                detected_types.append(label)

        # 额外检测：内容中直接出现的11位手机号（无前缀）
        if re.search(r'(?<!\d)1[3-9]\d{9}(?!\d)', content):
            if "phone" not in detected_types:
                detected_types.append("phone")

        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.CONTACT_INFO_DETECTED,
        )

        if detected_types:
            result.triggered = True
            result.level = HarassmentLevel.WARN
            type_labels = {
                "wechat": "微信号",
                "phone": "手机号",
                "qq": "QQ号",
            }
            labels = [type_labels.get(t, t) for t in detected_types]
            result.message = (
                f"你发送的内容中可能包含{'、'.join(labels)}，"
                "注意保护个人隐私哦"
            )
            result.action = "warn"

            logger.info(
                "[HarassmentDetector] 检测到联系方式，类型: %s",
                ", ".join(detected_types),
            )

        return result

    # =========================================================================
    # 针对同一用户的评论频率检测
    # =========================================================================

    async def check_targeted_comment_rate(
        self,
        user_id: str,
        target_user_id: str,
    ) -> HarassmentCheckResult:
        """检测对同一用户的评论频率。

        规则：同一用户单日对另一用户评论超5条 → 提示"对方可能需要空间"

        Args:
            user_id: 评论者用户ID
            target_user_id: 被评论者用户ID

        Returns:
            检测结果
        """
        count_key = self._build_key(
            HarassmentRuleType.TARGETED_COMMENT_RATE.value,
            user_id,
            target_user_id,
        )
        count = await self._incr_and_get(count_key, 86400)

        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.TARGETED_COMMENT_RATE,
            current_count=count,
            threshold=self._thresholds.targeted_comment_max_per_day,
        )

        if count > self._thresholds.targeted_comment_max_per_day:
            result.triggered = True
            result.level = HarassmentLevel.WARN
            result.message = "对方可能需要一些空间，也许稍后再聊聊？"
            result.action = "warn"

            logger.info(
                "[HarassmentDetector] 针对性评论频率超限，"
                "评论者: %s, 被评论者: %s, 计数: %d",
                user_id, target_user_id, count,
            )

        return result

    # =========================================================================
    # 树洞场景频率检测
    # =========================================================================

    async def check_treehole_comment_rate(
        self,
        user_id: str,
    ) -> HarassmentCheckResult:
        """检测树洞评论频率。

        规则：单日评论超5条 → 提示

        Args:
            user_id: 用户ID

        Returns:
            检测结果
        """
        count_key = self._build_key(
            HarassmentRuleType.TREEHOLE_COMMENT_RATE.value,
            user_id,
        )
        count = await self._incr_and_get(count_key, 86400)

        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.TREEHOLE_COMMENT_RATE,
            current_count=count,
            threshold=self._thresholds.treehole_comment_max_per_day,
        )

        if count > self._thresholds.treehole_comment_max_per_day:
            result.triggered = True
            result.level = HarassmentLevel.WARN
            result.message = "今天在树洞说了很多话了，要留些时间给自己哦"
            result.action = "warn"

            logger.info(
                "[HarassmentDetector] 树洞评论频率超限，用户: %s, 计数: %d",
                user_id, count,
            )

        return result

    async def check_treehole_post_rate(
        self,
        user_id: str,
    ) -> HarassmentCheckResult:
        """检测树洞发布频率。

        规则：单日发布帖子超3条 → 限速

        Args:
            user_id: 用户ID

        Returns:
            检测结果
        """
        # 先检查限速标记
        rate_limit_key = self._build_key(
            "treehole_post_limit", user_id,
        )
        limit_remaining = await self._get_count(rate_limit_key)
        if limit_remaining > 0:
            return HarassmentCheckResult(
                rule_type=HarassmentRuleType.TREEHOLE_POST_RATE,
                triggered=True,
                level=HarassmentLevel.RATE_LIMIT,
                current_count=0,
                threshold=self._thresholds.treehole_post_max_per_day,
                message="今天在树洞说了不少了，明天再来分享吧",
                action="rate_limit",
            )

        # 递增当日发布计数
        count_key = self._build_key(
            HarassmentRuleType.TREEHOLE_POST_RATE.value,
            user_id,
        )
        count = await self._incr_and_get(count_key, 86400)

        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.TREEHOLE_POST_RATE,
            current_count=count,
            threshold=self._thresholds.treehole_post_max_per_day,
        )

        if count > self._thresholds.treehole_post_max_per_day:
            result.triggered = True
            result.level = HarassmentLevel.RATE_LIMIT
            result.message = "今天在树洞说了不少了，明天再来分享吧"
            result.action = "rate_limit"

            # 设置限速标记
            await self._set_with_ttl(
                rate_limit_key, 1,
                self._thresholds.treehole_post_rate_limit_seconds,
            )

            logger.info(
                "[HarassmentDetector] 树洞发布频率超限，用户: %s, 计数: %d",
                user_id, count,
            )

        return result

    # =========================================================================
    # 综合检测入口
    # =========================================================================

    async def check_treehole_interaction(
        self,
        user_id: str,
        action: str = "post",
        target_user_id: str | None = None,
    ) -> HarassmentDetectionResult:
        """树洞场景综合骚扰检测。

        根据操作类型运行对应的规则检测，返回综合结果。

        Args:
            user_id: 用户ID
            action: 操作类型，post / comment
            target_user_id: 被评论帖子作者ID（评论时使用）

        Returns:
            综合检测结果
        """
        overall = HarassmentDetectionResult()

        if action == "post":
            # 树洞发布频率检测
            post_result = await self.check_treehole_post_rate(user_id)
            overall.add_result(post_result)

        elif action == "comment":
            # 树洞评论频率检测
            comment_result = await self.check_treehole_comment_rate(user_id)
            overall.add_result(comment_result)

            # 针对同一用户的评论频率检测
            if target_user_id and target_user_id != user_id:
                targeted_result = await self.check_targeted_comment_rate(
                    user_id, target_user_id
                )
                overall.add_result(targeted_result)

        return overall


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_harassment_detector(
    redis: Any,
    thresholds: HarassmentThresholds | None = None,
) -> HarassmentDetector:
    """创建骚扰规则引擎实例。

    Args:
        redis: Redis 客户端
        thresholds: 阈值配置（可选）

    Returns:
        HarassmentDetector 实例
    """
    return HarassmentDetector(redis=redis, thresholds=thresholds)
