"""内容审核服务模块。

提供内容安全审核能力，支持直接通过、本地关键词过滤、阿里云内容安全三种 Provider。

审核策略（modules_design.md 4.6, 7.3）：
- 树洞吐槽区：中高严格度
  - 自伤内容：允许发布，触发关怀流程
  - 人身攻击：拦截，显示温和提示
  - 广告引流：拦截
  - 色情内容：拦截
- 温和审核反馈（modules_design.md 7.11）：
  - 拦截时："这条内容好像不太适合在这里发出来..."
  - 警告时："我们注意到你发布的内容可能让其他人感到不适..."
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 审核结果类型枚举
# ---------------------------------------------------------------------------

class AuditResult(str, Enum):
    """审核结果类型。"""

    PASS = "pass"                    # 通过
    BLOCK = "block"                  # 拦截
    WARN = "warn"                    # 警告（允许发布但提示）
    PASS_WITH_CARE = "pass_with_care"  # 通过但触发关怀流程（自伤内容）


class AuditLabel(str, Enum):
    """审核标签类型。"""

    # 自伤相关（允许发布但触发关怀）
    SELF_HARM = "self_harm"

    # 人身攻击
    PERSONAL_ATTACK = "personal_attack"

    # 广告引流
    ADVERTISEMENT = "advertisement"
    PROMOTION = "promotion"

    # 色情
    PORNOGRAPHY = "pornography"

    # 暴力恐怖
    VIOLENCE = "violence"

    # 其他
    SPAM = "spam"
    SENSITIVE = "sensitive"


# ---------------------------------------------------------------------------
# 温和审核反馈文案（modules_design.md 7.11）
# ---------------------------------------------------------------------------

AUDIT_FEEDBACK = {
    "block": {
        "default": (
            "这条内容好像不太适合在这里发出来。"
            "也许是情绪太强烈了？你可以试着换个方式表达，"
            "或者跟AI朋友聊聊，ta随时都在。"
        ),
        "personal_attack": (
            "这条内容好像不太适合在这里发出来。"
            "也许是情绪太强烈了？你可以试着换个方式表达，"
            "或者跟AI朋友聊聊，ta随时都在。"
        ),
        "advertisement": "这里不是广告位哦，让我们保持树洞的纯净吧。",
        "pornography": "这条内容不太适合在这里发布，换个方式试试？",
        "violence": "这条内容好像不太适合在这里发出来，也许是情绪太强烈了？",
    },
    "warn": {
        "default": (
            "我们注意到你发布的内容可能让其他人感到不适。"
            "回声是大家的安全角落，一起守护好吗？"
        ),
        "sensitive_info": (
            "你发布的内容里可能包含一些个人信息，"
            "要注意保护隐私哦。"
        ),
    },
}


def get_audit_feedback(
    result: AuditResult,
    label: str | None = None,
) -> str:
    """获取审核反馈文案。

    Args:
        result: 审核结果类型
        label: 审核标签

    Returns:
        温和的审核反馈文案
    """
    result_key = result.value if result != AuditResult.PASS_WITH_CARE else "block"

    if result_key in AUDIT_FEEDBACK:
        feedback_map = AUDIT_FEEDBACK[result_key]
        if label and label in feedback_map:
            return feedback_map[label]
        return feedback_map["default"]

    return "内容审核未通过，请修改后重试。"


# ---------------------------------------------------------------------------
# Protocol 定义 — 内容审核服务接口契约
# ---------------------------------------------------------------------------

class ContentAuditProtocol(Protocol):
    """内容审核服务接口。"""

    async def check(self, content: str) -> dict[str, Any]:
        """审核内容，返回审核结果。

        Args:
            content: 待审核的文本内容

        Returns:
            {"pass": bool, "risk_level": str, "labels": [...], "reason": str|None}
        """
        ...


# ---------------------------------------------------------------------------
# Pass 实现 — 直接通过，不做审核
# ---------------------------------------------------------------------------

class PassAudit:
    """直接通过的内容审核服务。

    适用于开发环境或无需审核的场景，所有内容默认通过。
    """

    async def check(self, content: str) -> dict[str, Any]:
        logger.debug("[PassAudit] 跳过审核，直接通过: %s", content[:50] if len(content) > 50 else content)
        return {
            "pass": True,
            "risk_level": "none",
            "labels": [],
            "reason": None,
        }


# ---------------------------------------------------------------------------
# Local 实现 — 本地关键词过滤
# ---------------------------------------------------------------------------

class LocalContentAudit:
    """本地关键词内容审核服务。

    基于敏感词列表进行本地匹配，适用于测试环境或低风险场景。
    """

    # 敏感词列表 - 实际生产环境应从数据库或配置文件加载
    SENSITIVE_KEYWORDS: list[str] = [
        # 违禁词
        "违规", "违禁", "敏感词", "广告",
        # 政治敏感词（示例）
        "政治敏感", "反动",
        # 色情暴力
        "色情", "暴力", "血腥",
        # 赌博诈骗
        "赌博", "诈骗", "传销",
        # 毒品
        "毒品", "吸毒",
        # 其他违规内容
        "代开发票", "刷单", "兼职赚钱",
    ]

    # 正则表达式模式 - 用于检测更复杂的违规模式
    PATTERNS: list[tuple[str, str]] = [
        (r"\d{11}", "手机号"),  # 手机号
        (r"银行卡", "银行卡信息"),
        (r"微信号|添加微信|加微信", "微信引流"),
        (r"QQ.*群", "QQ群引流"),
    ]

    async def check(self, content: str) -> dict[str, Any]:
        matched_keywords: list[str] = []

        # 关键词匹配
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in content:
                matched_keywords.append(keyword)

        # 正则模式匹配
        for pattern, label in self.PATTERNS:
            if re.search(pattern, content):
                matched_keywords.append(label)

        if matched_keywords:
            logger.warning(
                "[LocalAudit] 内容审核不通过，匹配到敏感词: %s",
                ", ".join(matched_keywords),
            )
            return {
                "pass": False,
                "risk_level": "high",
                "labels": matched_keywords,
                "reason": f"内容包含敏感词: {', '.join(matched_keywords)}",
            }

        logger.debug("[LocalAudit] 内容审核通过")
        return {
            "pass": True,
            "risk_level": "none",
            "labels": [],
            "reason": None,
        }


# ---------------------------------------------------------------------------
# Treehole 实现 — 树洞场景差异化审核（modules_design.md 4.6）
# ---------------------------------------------------------------------------

class TreeholeContentAudit:
    """树洞场景内容审核服务。

    根据 modules_design.md 4.6 差异化审核策略：
    - 自伤内容：允许发布，触发关怀流程（不拦截）
    - 人身攻击：拦截，显示温和提示
    - 广告引流：拦截
    - 色情内容：拦截
    - 其他违规：拦截

    温和审核反馈遵循 modules_design.md 7.11 规范。
    """

    # 人身攻击关键词（针对具体个人的攻击）
    PERSONAL_ATTACK_KEYWORDS: list[str] = [
        # 针对个人的辱骂（需要检测 @ 或具体名字上下文）
        "傻逼", "傻x", "sb", "贱人", "婊子", "畜生",
        "王八蛋", "混蛋", "渣男", "渣女", "恶心",
        "滚", "死", "该死", "你妈", "他妈",
    ]

    # 人身攻击模式（@某人 + 辱骂）
    PERSONAL_ATTACK_PATTERNS: list[tuple[str, str]] = [
        (r"[@@]\s*\S+.*傻逼|sb|贱人|婊子|畜生|王八蛋|混蛋", "定向辱骂"),
        (r"你\s*(是|真|好|这个)\s*(傻逼|sb|贱人|婊子|畜生|王八蛋|混蛋)", "定向辱骂"),
        (r"(傻逼|sb|贱人|婊子|畜生|王八蛋|混蛋)\s*(去死|滚|消失)", "威胁辱骂"),
    ]

    # 广告引流关键词
    ADVERTISEMENT_KEYWORDS: list[str] = [
        "兼职", "赚钱", "招聘", "代理", "招商",
        "低价", "优惠", "折扣", "促销", "特价",
        "代购", "微商", "团购", "秒杀", "抢购",
        "返利", "佣金", "提成", "收益",
    ]

    # 广告引流模式
    ADVERTISEMENT_PATTERNS: list[tuple[str, str]] = [
        (r"加\s*(微信|vx|qq|群)", "引流"),
        (r"联系\s*(我|微信|qq)", "引流"),
        (r"私信\s*(我|获取|领取)", "引流"),
        (r"http[s]?://\S+", "外链"),
        (r"添加微信|加微信|扫码|二维码", "引流"),
    ]

    # 色情关键词
    PORNOGRAPHY_KEYWORDS: list[str] = [
        "约炮", "一夜情", "炮友", "裸聊", "裸照",
        "情趣", "成人", "黄色", "性服务",
    ]

    # 暴力恐怖关键词
    VIOLENCE_KEYWORDS: list[str] = [
        "杀人", "砍死", "捅死", "打死", "弄死",
        "恐怖", "炸弹", "爆炸", "袭击",
    ]

    # 自伤关键词（允许发布但触发关怀）
    SELF_HARM_KEYWORDS: list[str] = [
        "想死", "自杀", "不想活", "了结", "结束生命",
        "解脱", "离开这个世界", "不再醒来", "怎么死", "跳楼",
        "割腕", "服药", "消失", "去死",
        "活着好累", "没有活下去", "想结束", "结束一切",
        "划自己", "割自己", "伤害自己", "自残",
        "用刀", "拿刀", "烫自己", "掐自己", "拿头撞墙",
        "已经吃了", "马上就", "告别", "最后一次",
        "吃了一整瓶药", "吃了好多药", "吃药了", "准备好了",
    ]

    # 否定词（用于排除误判）
    NEGATION_WORDS: list[str] = [
        "不想死", "不想自杀", "不会自杀", "不想伤害自己",
        "只是想", "开玩笑", "说笑", "打趣", "比喻",
    ]

    async def check(self, content: str) -> dict[str, Any]:
        """审核树洞内容。

        Args:
            content: 待审核内容

        Returns:
            审核结果字典，包含：
            - result: AuditResult 枚举值
            - pass: 是否允许发布
            - labels: 匹配的标签列表
            - reason: 审核原因（内部使用）
            - feedback: 温和的审核反馈文案
            - trigger_care: 是否触发关怀流程
        """
        matched_labels: list[str] = []
        result = AuditResult.PASS
        feedback = None
        trigger_care = False

        # 1. 检测自伤内容（最高优先级，允许发布但触发关怀）
        has_negation = self._contains_negation(content)
        self_harm_matched = self._match_keywords(content, self.SELF_HARM_KEYWORDS)

        if self_harm_matched and not has_negation:
            result = AuditResult.PASS_WITH_CARE
            matched_labels.append(AuditLabel.SELF_HARM.value)
            trigger_care = True
            logger.warning(
                "[TreeholeAudit] 检测到自伤内容，允许发布但触发关怀: %s",
                self_harm_matched
            )
            # 自伤内容通过，返回结果但标记触发关怀
            return {
                "result": result.value,
                "pass": True,
                "labels": matched_labels,
                "reason": f"检测到自伤内容: {', '.join(self_harm_matched)}",
                "feedback": None,  # 不给用户反馈，后台处理
                "trigger_care": True,
                "care_level": self._determine_care_level(self_harm_matched),
            }

        # 2. 检测人身攻击（拦截）
        personal_attack_matched = self._match_keywords(
            content, self.PERSONAL_ATTACK_KEYWORDS
        )
        personal_attack_pattern_matched = self._match_patterns(
            content, self.PERSONAL_ATTACK_PATTERNS
        )

        if personal_attack_pattern_matched:
            # @某人 + 辩骂模式，直接拦截
            result = AuditResult.BLOCK
            matched_labels.append(AuditLabel.PERSONAL_ATTACK.value)
            matched_labels.extend(personal_attack_pattern_matched)
            feedback = get_audit_feedback(result, "personal_attack")
            logger.warning(
                "[TreeholeAudit] 检测到定向人身攻击，拦截: %s",
                personal_attack_pattern_matched
            )
        elif personal_attack_matched:
            # 纔粹骂人词汇，需要判断是否针对具体人
            # "领导傻X" 是情绪宣泄，"@某人你傻X" 是定向攻击
            if "@" in content or self._has_specific_target(content):
                result = AuditResult.BLOCK
                matched_labels.append(AuditLabel.PERSONAL_ATTACK.value)
                matched_labels.extend(personal_attack_matched)
                feedback = get_audit_feedback(result, "personal_attack")
                logger.warning(
                    "[TreeholeAudit] 检测到定向人身攻击，拦截: %s",
                    personal_attack_matched
                )
            else:
                # 纯情绪宣泄，警告但不拦截
                result = AuditResult.WARN
                matched_labels.append("emotional_expression")
                feedback = get_audit_feedback(result, "default")
                logger.info(
                    "[TreeholeAudit] 检测到情绪宣泄词汇，警告: %s",
                    personal_attack_matched
                )

        # 3. 检测广告引流（拦截）
        if result == AuditResult.PASS:
            ad_matched = self._match_keywords(content, self.ADVERTISEMENT_KEYWORDS)
            ad_pattern_matched = self._match_patterns(
                content, self.ADVERTISEMENT_PATTERNS
            )

            if ad_pattern_matched or (ad_matched and len(ad_matched) >= 2):
                result = AuditResult.BLOCK
                matched_labels.append(AuditLabel.ADVERTISEMENT.value)
                matched_labels.extend(ad_matched + ad_pattern_matched)
                feedback = get_audit_feedback(result, "advertisement")
                logger.warning(
                    "[TreeholeAudit] 检测到广告引流，拦截: %s",
                    ad_matched + ad_pattern_matched
                )

        # 4. 检测色情内容（拦截）
        if result == AuditResult.PASS:
            porn_matched = self._match_keywords(content, self.PORNOGRAPHY_KEYWORDS)
            if porn_matched:
                result = AuditResult.BLOCK
                matched_labels.append(AuditLabel.PORNOGRAPHY.value)
                matched_labels.extend(porn_matched)
                feedback = get_audit_feedback(result, "pornography")
                logger.warning(
                    "[TreeholeAudit] 检测到色情内容，拦截: %s",
                    porn_matched
                )

        # 5. 检测暴力恐怖内容（拦截）
        if result == AuditResult.PASS:
            violence_matched = self._match_keywords(content, self.VIOLENCE_KEYWORDS)
            if violence_matched:
                result = AuditResult.BLOCK
                matched_labels.append(AuditLabel.VIOLENCE.value)
                matched_labels.extend(violence_matched)
                feedback = get_audit_feedback(result, "violence")
                logger.warning(
                    "[TreeholeAudit] 检测到暴力恐怖内容，拦截: %s",
                    violence_matched
                )

        # 构建返回结果
        return {
            "result": result.value,
            "pass": result in (AuditResult.PASS, AuditResult.PASS_WITH_CARE, AuditResult.WARN),
            "labels": matched_labels,
            "reason": f"检测到: {', '.join(matched_labels)}" if matched_labels else None,
            "feedback": feedback,
            "trigger_care": trigger_care,
        }

    def _contains_negation(self, content: str) -> bool:
        """检查内容是否包含否定词。

        Args:
            content: 用户内容

        Returns:
            是否包含否定词
        """
        for negation in self.NEGATION_WORDS:
            if negation in content:
                return True
        return False

    def _match_keywords(
        self,
        content: str,
        keywords: list[str],
    ) -> list[str]:
        """匹配关键词列表。

        Args:
            content: 用户内容
            keywords: 关键词列表

        Returns:
            匹配到的关键词列表
        """
        matched = []
        for keyword in keywords:
            if keyword.lower() in content.lower():
                matched.append(keyword)
        return matched

    def _match_patterns(
        self,
        content: str,
        patterns: list[tuple[str, str]],
    ) -> list[str]:
        """匹配正则模式。

        Args:
            content: 用户内容
            patterns: 正则模式列表 (pattern, label)

        Returns:
            匹配到的标签列表
        """
        matched = []
        for pattern, label in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                matched.append(label)
        return matched

    def _has_specific_target(self, content: str) -> bool:
        """判断内容是否针对具体对象。

        Args:
            content: 用户内容

        Returns:
            是否针对具体对象
        """
        # 检测是否包含具体人名或称呼
        target_patterns = [
            r"你\s*(是|真|好)",  # "你是..."
            r"那个\s*\S+",  # "那个..."
            r"他|她|它",
        ]
        for pattern in target_patterns:
            if re.search(pattern, content):
                return True
        return False

    def _determine_care_level(self, matched_keywords: list[str]) -> str:
        """根据自伤关键词确定关怀级别。

        Args:
            matched_keywords: 匹配到的自伤关键词

        Returns:
            关怀级别: low / medium / high
        """
        # 紧急信号关键词
        high_keywords = [
            "已经吃了", "马上就", "告别", "最后一次",
            "吃了一整瓶药", "吃了好多药", "吃药了", "准备好了",
        ]
        # 自残意念关键词
        medium_keywords = [
            "想死", "自杀", "不想活", "了结", "结束生命",
            "割腕", "服药", "跳楼", "怎么死",
        ]

        for kw in matched_keywords:
            if kw in high_keywords:
                return "high"

        for kw in matched_keywords:
            if kw in medium_keywords:
                return "medium"

        return "low"


# ---------------------------------------------------------------------------
# 阿里云内容安全 — 真实调用占位
# ---------------------------------------------------------------------------

class AliyunContentAudit:
    """阿里云内容安全审核服务（真实调用占位）。

    TODO: 接入阿里云内容安全 SDK
    - 需要配置 AccessKey、SecretKey
    - 支持文本、图片、视频等多种内容类型
    - 返回详细的审核结果和风险等级
    """

    async def check(self, content: str) -> dict[str, Any]:
        # TODO: 接入阿里云内容安全 SDK
        # from alibabacloud_green20220302.client import Client
        # from alibabacloud_green20220302 import models as green_models
        logger.warning("[AliyunAudit] 阿里云内容安全 SDK 尚未接入，返回占位响应")
        return {
            "pass": True,
            "risk_level": "none",
            "labels": [],
            "reason": "aliyun audit placeholder",
        }


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

CONTENT_AUDIT_SERVICES: dict[str, type[PassAudit | LocalContentAudit | TreeholeContentAudit | AliyunContentAudit]] = {
    "pass": PassAudit,
    "local": LocalContentAudit,
    "treehole": TreeholeContentAudit,
    "aliyun": AliyunContentAudit,
}


def create_content_audit_service(
    provider: str = "pass",
) -> PassAudit | LocalContentAudit | TreeholeContentAudit | AliyunContentAudit:
    """根据配置创建内容审核服务实例。

    Args:
        provider: 服务提供者名称，可选 pass / local / treehole / aliyun

    Returns:
        内容审核服务实例

    Raises:
        ValueError: 当 provider 名称不在可用列表中时
    """
    if provider not in CONTENT_AUDIT_SERVICES:
        available = ", ".join(CONTENT_AUDIT_SERVICES.keys())
        raise ValueError(f"未知的内容审核服务 Provider: {provider}，可用选项: [{available}]")
    return CONTENT_AUDIT_SERVICES[provider]()
