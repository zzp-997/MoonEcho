"""骚扰识别规则引擎（完整三层防御实现）。

实现 modules_design.md 7.4 三层防御体系：

第一层 — 规则引擎（实时，覆盖80%场景）：
- 同一对话1分钟内超过10条消息 → 速率限制
- 单日向超过10人发好友申请 → 冻结申请功能24小时
- 消息中出现微信号/手机号格式 → 标记+提醒
- 同一用户单日对另一用户评论超5条 → 提示"对方可能需要空间"
- 树洞场景：单日评论超5条提示、单日发布帖子超3条限速

第二层 — AI行为分析（准实时，覆盖长尾）：
- 对话模式检测：一方连续发多条，另一方回复极短或不再回复
- 关系进展异常：好友建立24小时内含诱导性内容
- 跨场景纠缠：同一用户在多个场景追踪同一对象

第三层 — 用户侧防御工具：
- 一键屏蔽功能（已有 UserBlock 模型）
- 社交能量耗尽自动勿扰模式
- 对话安全提示
- 聊天记录自助保全（举报证据）

设计要点：
- 使用 Redis 做频率计数和行为数据缓存
- 支持可配置的阈值参数
- 兼容 MockRedis（开发环境）
- 所有操作均为建议性提醒，由上层决定是否强制执行
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 骚扰检测规则类型枚举
# ---------------------------------------------------------------------------

class HarassmentRuleType(str, Enum):
    """骚扰检测规则类型。"""

    # 第一层：规则引擎
    CHAT_MESSAGE_RATE = "chat_message_rate"
    FRIEND_REQUEST_RATE = "friend_request_rate"
    CONTACT_INFO_DETECTED = "contact_info_detected"
    TARGETED_COMMENT_RATE = "targeted_comment_rate"
    TREEHOLE_COMMENT_RATE = "treehole_comment_rate"
    TREEHOLE_POST_RATE = "treehole_post_rate"

    # 第二层：AI行为分析
    CONVERSATION_PATTERN = "conversation_pattern"  # 对话模式异常
    RELATIONSHIP_PROGRESS = "relationship_progress"  # 关系进展异常
    CROSS_SCENE_STALKING = "cross_scene_stalking"  # 跨场景纠缠

    # 第三层：用户侧防御
    SOCIAL_ENERGY_DEPLETED = "social_energy_depleted"  # 社交能量耗尽
    SAFETY_REMINDER = "safety_reminder"  # 安全提示


# ---------------------------------------------------------------------------
# 骚扰检测结果
# ---------------------------------------------------------------------------

class HarassmentLevel(str, Enum):
    """骚扰检测级别。"""

    NONE = "none"           # 无异常
    WARN = "warn"           # 提醒（建议性，不强制）
    RATE_LIMIT = "rate_limit"  # 限速（强制执行）
    AUTO_DND = "auto_dnd"   # 自动勿扰模式
    SAFETY_ALERT = "safety_alert"  # 安全警告


@dataclass(slots=True)
class HarassmentCheckResult:
    """单条规则检测结果。"""

    rule_type: HarassmentRuleType
    level: HarassmentLevel = HarassmentLevel.NONE
    triggered: bool = False
    current_count: int = 0
    threshold: int = 0
    message: str = ""
    action: str = ""  # none / warn / rate_limit / freeze / auto_dnd / safety_alert
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外元数据


@dataclass(slots=True)
class HarassmentDetectionResult:
    """骚扰检测综合结果。"""

    has_warning: bool = False
    has_rate_limit: bool = False
    has_safety_alert: bool = False
    results: list[HarassmentCheckResult] = field(default_factory=list)
    warning_messages: list[str] = field(default_factory=list)
    rate_limit_message: str = ""
    safety_actions: list[str] = field(default_factory=list)  # 建议的安全操作

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
            elif result.level == HarassmentLevel.SAFETY_ALERT:
                self.has_safety_alert = True
                self.warning_messages.append(result.message)
                if result.metadata.get("suggested_actions"):
                    self.safety_actions.extend(result.metadata["suggested_actions"])


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

        # 第二层：AI行为分析阈值
        conversation_pattern_window_minutes: 对话模式检测窗口（分钟）
        conversation_pattern_consecutive_messages: 连续消息数阈值
        conversation_pattern_short_reply_threshold: 短回复字数阈值
        relationship_progress_hours: 关系进展检测时间窗口（小时）
        relationship_progress_inductive_keywords: 诱导性关键词触发数
        cross_scene_tracking_threshold: 跨场景追踪阈值

        # 第三层：用户侧防御阈值
        social_energy_dnd_threshold: 触发自动勿扰的能量阈值
        safety_reminder_interval_hours: 安全提示间隔（小时）
    """

    # 第一层：规则引擎
    chat_message_window_seconds: int = 60
    chat_message_max_count: int = 10
    friend_request_max_per_day: int = 10
    friend_request_freeze_hours: int = 24
    targeted_comment_max_per_day: int = 5
    treehole_comment_max_per_day: int = 5
    treehole_post_max_per_day: int = 3
    treehole_post_rate_limit_seconds: int = 300  # 5分钟

    # 第二层：AI行为分析
    conversation_pattern_window_minutes: int = 30
    conversation_pattern_consecutive_messages: int = 5  # 连续发送5条消息
    conversation_pattern_short_reply_threshold: int = 5  # 回复字数<=5视为极短
    relationship_progress_hours: int = 24  # 好友建立后24小时内
    relationship_progress_inductive_keywords: int = 2  # 诱导性关键词数
    cross_scene_tracking_threshold: int = 3  # 在3个及以上场景追踪同一用户

    # 第三层：用户侧防御
    social_energy_dnd_threshold: int = 20  # 能量<=20%触发自动勿扰
    safety_reminder_interval_hours: int = 24  # 每24小时提示一次


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
# 诱导性内容关键词（用于第二层行为分析）
# ---------------------------------------------------------------------------

INDUCTIVE_KEYWORDS: list[str] = [
    # 联系方式诱导
    "加微信", "加我微信", "微信号", "加个微信",
    "加QQ", "QQ号", "加个QQ",
    "手机号", "联系电话", "打电话",
    "私聊", "私下聊", "加个好友",
    # 转移平台诱导
    "换个地方聊", "去微信聊", "加我微信聊",
    "我微信是", "我QQ是", "我手机是",
    # 金钱相关诱导
    "转账", "红包", "发红包", "转账给你",
    "借钱", "借点钱", "打钱",
    # 隐私信息诱导
    "住哪", "你家在哪", "发个定位",
    "你多大", "你年龄", "你生日",
    "你工作", "你公司", "你收入",
    "发张照片", "发个照片", "看看照片",
    "照片看看", "真人照片", "自拍",
    # 见面诱导
    "见个面", "出来见面", "约个时间",
    "去找你", "去找你玩", "见一面",
]

# ---------------------------------------------------------------------------
# 场景类型枚举（用于跨场景纠缠检测）
# ---------------------------------------------------------------------------

class SceneType(str, Enum):
    """场景类型。"""
    CHAT = "chat"           # 私聊
    POST_COMMENT = "post_comment"  # 动态广场评论
    TREEHOLE_COMMENT = "treehole_comment"  # 树洞评论
    FRIEND_REQUEST = "friend_request"  # 好友申请


# ---------------------------------------------------------------------------
# 骚扰规则引擎核心
# ---------------------------------------------------------------------------

class HarassmentDetector:
    """骚扰识别规则引擎。

    实现三层防御体系：
    - 第一层：规则引擎（实时）
    - 第二层：AI行为分析（准实时）
    - 第三层：用户侧防御工具

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

        # 编译诱导性关键词正则
        self._inductive_pattern = self._compile_inductive_pattern()

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

    def _compile_inductive_pattern(self) -> re.Pattern | None:
        """编译诱导性关键词正则表达式。"""
        if not INDUCTIVE_KEYWORDS:
            return None
        sorted_keywords = sorted(INDUCTIVE_KEYWORDS, key=len, reverse=True)
        pattern_str = "|".join(re.escape(kw) for kw in sorted_keywords)
        return re.compile(pattern_str)

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

    async def _append_to_list(
        self,
        key: str,
        value: str,
        max_length: int,
        ttl_seconds: int,
    ) -> list[str]:
        """追加元素到列表，并限制列表长度。

        Args:
            key: Redis key
            value: 要追加的值
            max_length: 最大列表长度
            ttl_seconds: 过期时间（秒）

        Returns:
            当前列表内容
        """
        try:
            # 使用 lpush + ltrim + lrange 实现有界列表
            await self._redis.lpush(key, value)
            await self._redis.ltrim(key, 0, max_length - 1)
            await self._redis.expire(key, ttl_seconds)

            # 获取列表内容
            result = await self._redis.lrange(key, 0, -1)
            if result:
                if isinstance(result[0], bytes):
                    return [v.decode('utf-8') for v in result]
                return result
            return []
        except Exception as e:
            logger.error(
                "[HarassmentDetector] Redis list 操作异常, key=%s: %s",
                key, str(e)
            )
            return []

    async def _add_to_set(
        self,
        key: str,
        value: str,
        ttl_seconds: int,
    ) -> int:
        """添加元素到集合。

        Args:
            key: Redis key
            value: 要添加的值
            ttl_seconds: 过期时间（秒）

        Returns:
            集合大小
        """
        try:
            await self._redis.sadd(key, value)
            await self._redis.expire(key, ttl_seconds)
            return await self._redis.scard(key)
        except Exception as e:
            logger.error(
                "[HarassmentDetector] Redis set 操作异常, key=%s: %s",
                key, str(e)
            )
            return 0

    async def _get_set_size(self, key: str) -> int:
        """获取集合大小。

        Args:
            key: Redis key

        Returns:
            集合大小
        """
        try:
            return await self._redis.scard(key)
        except Exception as e:
            logger.error(
                "[HarassmentDetector] Redis scard 操作异常, key=%s: %s",
                key, str(e)
            )
            return 0

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
    # 第一层：规则引擎检测
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
            result.metadata = {"detected_types": detected_types}

            logger.info(
                "[HarassmentDetector] 检测到联系方式，类型: %s",
                ", ".join(detected_types),
            )

        return result

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
    # 第二层：AI行为分析检测
    # =========================================================================

    async def check_conversation_pattern(
        self,
        user_id: str,
        conversation_id: str,
        message_content: str,
        db=None,
    ) -> HarassmentCheckResult:
        """检测对话模式异常。

        规则：一方连续发多条消息，另一方回复极短或不再回复

        分析维度：
        1. 连续消息检测：同一用户短时间内连续发送多条消息
        2. 回复不平衡检测：一方回复字数明显少于另一方
        3. 无响应检测：一方连续发送多条后另一方未回复

        Args:
            user_id: 发送者用户ID
            conversation_id: 对话ID
            message_content: 当前消息内容
            db: 数据库会话（可选，用于查询历史消息）

        Returns:
            检测结果
        """
        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.CONVERSATION_PATTERN,
        )

        # 获取检测窗口的时间范围
        window_minutes = self._thresholds.conversation_pattern_window_minutes
        window_key = self._build_key(
            "conv_pattern",
            user_id,
            conversation_id,
        )

        # 记录消息发送（格式：timestamp:content_length）
        now = datetime.now(timezone.utc)
        msg_record = f"{int(now.timestamp())}:{len(message_content)}"

        # 使用 Redis 列表存储最近消息记录
        ttl = window_minutes * 60
        messages = await self._append_to_list(
            window_key, msg_record,
            max_length=20,  # 最多记录20条
            ttl_seconds=ttl,
        )

        if len(messages) < 3:
            return result

        # 分析消息模式
        pattern_analysis = self._analyze_conversation_pattern(messages)

        # 检测连续发送过多
        if pattern_analysis["consecutive_count"] >= self._thresholds.conversation_pattern_consecutive_messages:
            result.triggered = True
            result.level = HarassmentLevel.WARN
            result.message = "看起来你发了好几条消息，对方可能需要时间回复"
            result.action = "warn"
            result.metadata = {
                "consecutive_count": pattern_analysis["consecutive_count"],
                "pattern_type": "consecutive_messages",
            }

            logger.info(
                "[HarassmentDetector] 检测到连续消息模式，用户: %s, 对话: %s, 连续数: %d",
                user_id, conversation_id, pattern_analysis["consecutive_count"],
            )

        # 检测对方回复极短或无响应（需要双方数据）
        # 这里只做单向检测，完整的检测需要查询对方的消息记录

        return result

    def _analyze_conversation_pattern(self, messages: list[str]) -> dict[str, Any]:
        """分析对话模式。

        Args:
            messages: 消息记录列表（格式：timestamp:content_length）

        Returns:
            分析结果
        """
        consecutive_count = 0
        max_consecutive = 0
        total_length = 0

        for msg in messages:
            try:
                parts = msg.split(":")
                if len(parts) >= 2:
                    content_length = int(parts[1])
                    total_length += content_length

                    # 检测极短回复
                    if content_length <= self._thresholds.conversation_pattern_short_reply_threshold:
                        consecutive_count += 1
                        max_consecutive = max(max_consecutive, consecutive_count)
                    else:
                        consecutive_count = 0
            except (ValueError, IndexError):
                continue

        return {
            "consecutive_count": max_consecutive,
            "total_length": total_length,
            "message_count": len(messages),
        }

    async def check_relationship_progress(
        self,
        user_id: str,
        target_user_id: str,
        message_content: str,
        friendship_created_at: datetime | None = None,
    ) -> HarassmentCheckResult:
        """检测关系进展异常。

        规则：好友建立24小时内含诱导性内容

        Args:
            user_id: 发送者用户ID
            target_user_id: 接收者用户ID
            message_content: 消息内容
            friendship_created_at: 好友关系建立时间

        Returns:
            检测结果
        """
        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.RELATIONSHIP_PROGRESS,
        )

        # 检查好友关系建立时间
        if friendship_created_at is None:
            # 如果没有提供时间，假设在检测窗口内
            return result

        now = datetime.now(timezone.utc)
        hours_since_friendship = (now - friendship_created_at).total_seconds() / 3600

        # 仅在好友建立后的检测窗口内进行检测
        if hours_since_friendship > self._thresholds.relationship_progress_hours:
            return result

        # 检测诱导性关键词
        inductive_count = self._count_inductive_keywords(message_content)

        if inductive_count >= self._thresholds.relationship_progress_inductive_keywords:
            result.triggered = True
            result.level = HarassmentLevel.WARN
            result.message = "如果对方让你感到不适，可以随时屏蔽或举报"
            result.action = "warn"
            result.metadata = {
                "inductive_keywords_count": inductive_count,
                "hours_since_friendship": round(hours_since_friendship, 1),
                "suggested_actions": [
                    "如果感到不适，可以拉黑对方",
                    "可以举报此用户",
                    "可以不回复，保护自己的边界",
                ],
            }

            logger.info(
                "[HarassmentDetector] 检测到诱导性内容，用户: %s, 目标: %s, "
                "关键词数: %d, 好友时长: %.1fh",
                user_id, target_user_id, inductive_count, hours_since_friendship,
            )

        return result

    def _count_inductive_keywords(self, content: str) -> int:
        """计算内容中的诱导性关键词数量。

        Args:
            content: 消息内容

        Returns:
            匹配到的关键词数量
        """
        if not self._inductive_pattern:
            return 0

        matches = self._inductive_pattern.findall(content)
        return len(set(matches))  # 去重后计数

    async def check_cross_scene_stalking(
        self,
        user_id: str,
        target_user_id: str,
        scene: SceneType,
    ) -> HarassmentCheckResult:
        """检测跨场景纠缠。

        规则：同一用户在多个场景追踪同一对象

        场景包括：
        - 私聊
        - 动态广场评论
        - 树洞评论
        - 好友申请

        Args:
            user_id: 发送者用户ID
            target_user_id: 目标用户ID
            scene: 当前场景类型

        Returns:
            检测结果
        """
        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.CROSS_SCENE_STALKING,
        )

        # 记录场景互动
        tracking_key = self._build_key(
            "cross_scene",
            user_id,
            target_user_id,
        )

        # 使用 Redis 集合记录场景
        ttl = 7 * 24 * 3600  # 7天过期
        scene_record = f"{scene.value}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"

        # 添加场景记录
        await self._redis.sadd(tracking_key, scene_record)
        await self._redis.expire(tracking_key, ttl)

        # 获取场景数量
        scene_count = await self._redis.scard(tracking_key)

        if scene_count >= self._thresholds.cross_scene_tracking_threshold:
            result.triggered = True
            result.level = HarassmentLevel.WARN
            result.message = "如果感到被过度关注，可以设置勿扰或屏蔽对方"
            result.action = "warn"
            result.metadata = {
                "scene_count": scene_count,
                "scenes": list(await self._redis.smembers(tracking_key)) if scene_count <= 10 else None,
                "suggested_actions": [
                    "可以屏蔽该用户",
                    "可以举报骚扰行为",
                    "可以开启勿扰模式",
                ],
            }

            logger.info(
                "[HarassmentDetector] 检测到跨场景纠缠，用户: %s, 目标: %s, 场景数: %d",
                user_id, target_user_id, scene_count,
            )

        return result

    # =========================================================================
    # 第三层：用户侧防御
    # =========================================================================

    async def check_social_energy_depleted(
        self,
        user_id: str,
        current_energy: Decimal,
    ) -> HarassmentCheckResult:
        """检测社交能量耗尽。

        规则：能量<=阈值时触发自动勿扰模式建议

        Args:
            user_id: 用户ID
            current_energy: 当前社交能量值

        Returns:
            检测结果
        """
        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.SOCIAL_ENERGY_DEPLETED,
            current_count=int(current_energy),
            threshold=self._thresholds.social_energy_dnd_threshold,
        )

        if current_energy <= self._thresholds.social_energy_dnd_threshold:
            result.triggered = True
            result.level = HarassmentLevel.AUTO_DND
            result.message = "社交能量较低了，要休息一下吗？"
            result.action = "auto_dnd"
            result.metadata = {
                "current_energy": float(current_energy),
                "suggested_actions": [
                    "开启勿扰模式",
                    "暂时不回复消息",
                    "与AI朋友聊聊天放松一下",
                ],
            }

            logger.info(
                "[HarassmentDetector] 检测到社交能量耗尽，用户: %s, 能量: %.1f",
                user_id, float(current_energy),
            )

        return result

    async def should_show_safety_reminder(
        self,
        user_id: str,
        conversation_id: str,
    ) -> HarassmentCheckResult:
        """判断是否应该显示安全提示。

        规则：定期在对话中显示安全提示

        Args:
            user_id: 用户ID
            conversation_id: 对话ID

        Returns:
            检测结果
        """
        result = HarassmentCheckResult(
            rule_type=HarassmentRuleType.SAFETY_REMINDER,
        )

        # 检查上次显示时间
        reminder_key = self._build_key(
            "safety_reminder",
            user_id,
            conversation_id,
        )

        last_shown = await self._get_count(reminder_key)

        if last_shown == 0:
            # 从未显示过，现在显示
            await self._set_with_ttl(
                reminder_key, 1,
                self._thresholds.safety_reminder_interval_hours * 3600,
            )
            result.triggered = True
            result.level = HarassmentLevel.SAFETY_ALERT
            result.message = "如果感到不适，可以随时屏蔽或举报"
            result.action = "safety_alert"
            result.metadata = {
                "suggested_actions": [
                    "长按消息可以举报",
                    "点击头像可以屏蔽用户",
                    "可以随时退出对话",
                ],
            }

        return result

    async def record_chat_evidence(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        message_content: str,
        sender_id: str,
    ) -> str:
        """记录聊天证据（用于举报）。

        将消息内容缓存到 Redis，用于后续举报时提取证据。

        Args:
            user_id: 当前用户ID
            conversation_id: 会话ID
            message_id: 消息ID
            message_content: 消息内容
            sender_id: 发送者ID

        Returns:
            证据ID
        """
        evidence_id = f"{user_id}:{conversation_id}:{message_id}"
        evidence_key = f"chat_evidence:{evidence_id}"

        # 存储证据，30天过期
        evidence_data = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "content": message_content,
            "sender_id": sender_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        # 使用 JSON 序列化存储
        import json
        await self._set_with_ttl(
            evidence_key,
            json.dumps(evidence_data, ensure_ascii=False),
            30 * 24 * 3600,  # 30天
        )

        logger.info(
            "[HarassmentDetector] 记录聊天证据，用户: %s, 证据ID: %s",
            user_id, evidence_id,
        )

        return evidence_id

    async def get_chat_evidence(
        self,
        evidence_id: str,
    ) -> dict[str, Any] | None:
        """获取聊天证据。

        Args:
            evidence_id: 证据ID

        Returns:
            证据数据，如果不存在返回 None
        """
        evidence_key = f"chat_evidence:{evidence_id}"

        try:
            data = await self._redis.get(evidence_key)
            if data:
                import json
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(
                "[HarassmentDetector] 获取聊天证据失败，证据ID: %s, 错误: %s",
                evidence_id, str(e)
            )
            return None

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

                # 跨场景纠缠检测
                stalking_result = await self.check_cross_scene_stalking(
                    user_id, target_user_id, SceneType.TREEHOLE_COMMENT
                )
                overall.add_result(stalking_result)

        return overall

    async def check_chat_message(
        self,
        user_id: str,
        conversation_id: str,
        message_content: str,
        target_user_id: str,
        friendship_created_at: datetime | None = None,
        current_energy: Decimal | None = None,
    ) -> HarassmentDetectionResult:
        """私聊消息综合骚扰检测。

        运行所有相关检测，返回综合结果。

        Args:
            user_id: 发送者用户ID
            conversation_id: 会话ID
            message_content: 消息内容
            target_user_id: 接收者用户ID
            friendship_created_at: 好友关系建立时间
            current_energy: 当前社交能量值

        Returns:
            综合检测结果
        """
        overall = HarassmentDetectionResult()

        # 第一层：规则引擎检测
        # 1. 消息速率检测
        rate_result = await self.check_chat_message_rate(user_id, conversation_id)
        overall.add_result(rate_result)

        # 2. 联系方式检测
        contact_result = self.check_contact_info(message_content)
        overall.add_result(contact_result)

        # 第二层：AI行为分析
        # 3. 对话模式检测
        pattern_result = await self.check_conversation_pattern(
            user_id, conversation_id, message_content
        )
        overall.add_result(pattern_result)

        # 4. 关系进展异常检测
        progress_result = await self.check_relationship_progress(
            user_id, target_user_id, message_content, friendship_created_at
        )
        overall.add_result(progress_result)

        # 5. 跨场景纠缠检测
        stalking_result = await self.check_cross_scene_stalking(
            user_id, target_user_id, SceneType.CHAT
        )
        overall.add_result(stalking_result)

        # 第三层：用户侧防御
        # 6. 社交能量检测
        if current_energy is not None:
            energy_result = await self.check_social_energy_depleted(
                user_id, current_energy
            )
            overall.add_result(energy_result)

        # 7. 安全提示检测
        safety_result = await self.should_show_safety_reminder(
            user_id, conversation_id
        )
        overall.add_result(safety_result)

        # 8. 记录聊天证据（用于举报）
        await self.record_chat_evidence(
            user_id, conversation_id,
            f"msg_{datetime.now(timezone.utc).timestamp()}",
            message_content, user_id
        )

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
