"""审核服务基类和公共定义。

提供审核系统的基础设施：
- 审核结果枚举（AuditResult）
- 审核标签枚举（AuditLabel）
- 审核严格度枚举（AuditStrictness）
- 温和反馈文案
- 审核基类（BaseAuditor）

设计要点：
- 四大场景差异化审核策略
- 温和、非对抗性的反馈文案
- 支持关键词和AI审核的混合策略
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 审核结果枚举
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
    SUICIDE_IDEATION = "suicide_ideation"

    # 人身攻击
    PERSONAL_ATTACK = "personal_attack"
    HARASSMENT = "harassment"
    INSULT = "insult"

    # 广告引流
    ADVERTISEMENT = "advertisement"
    PROMOTION = "promotion"
    SPAM = "spam"

    # 色情
    PORNOGRAPHY = "pornography"
    SEXUAL_CONTENT = "sexual_content"

    # 暴力恐怖
    VIOLENCE = "violence"
    TERRORISM = "terrorism"

    # 其他
    SENSITIVE = "sensitive"
    ILLEGAL = "illegal"
    CONTACT_INFO = "contact_info"


class AuditStrictness(str, Enum):
    """审核严格度级别。"""

    LOW = "low"        # 低严格度：仅危机检测
    MEDIUM = "medium"  # 中严格度：拦截色情/广告
    HIGH = "high"      # 高严格度：拦截色情/广告/暴恐/辱骂


# ---------------------------------------------------------------------------
# 温和审核反馈文案（modules_design.md 7.11）
# ---------------------------------------------------------------------------

GENTLE_FEEDBACK = {
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
        "harassment": (
            "我们注意到这条内容可能会让对方感到不适。"
            "回声是大家的安全角落，让我们一起守护吧。"
        ),
        "advertisement": "这里不是广告位哦，让我们保持空间的纯净吧。",
        "promotion": "这里不适合发推广内容，换个地方试试？",
        "spam": "发送太频繁啦，先歇一歇吧。",
        "pornography": "这条内容不太适合在这里发布，换个方式试试？",
        "sexual_content": "这条内容不太适合在这里发布，换个方式试试？",
        "violence": "这条内容好像不太适合在这里发出来，也许是情绪太强烈了？",
        "terrorism": "这条内容涉及敏感话题，无法发布。",
        "contact_info": (
            "你发送的内容中可能包含联系方式，"
            "注意保护个人隐私哦，这里不适合分享这类信息。"
        ),
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
        "emotional_expression": (
            "听起来你现在情绪很强烈，要不要和AI朋友聊聊？"
        ),
    },
    "care": {
        "self_harm": (
            "我能感受到你现在很不容易。"
            "如果愿意的话，可以多和我说说你的感受。"
        ),
        "suicide_ideation": (
            "你说的话让我很担心。请记住，你不是一个人，"
            "有很多人愿意帮助你。"
        ),
    },
}


def get_gentle_feedback(
    result: AuditResult,
    label: str | AuditLabel | None = None,
) -> str:
    """获取温和审核反馈文案。

    Args:
        result: 审核结果类型
        label: 审核标签

    Returns:
        温和的审核反馈文案
    """
    # 处理 PASS_WITH_CARE 情况
    if result == AuditResult.PASS_WITH_CARE:
        label_str = label.value if isinstance(label, AuditLabel) else label
        if label_str:
            for key in ["self_harm", "suicide_ideation"]:
                if key in label_str.lower():
                    return GENTLE_FEEDBACK["care"].get(
                        key, GENTLE_FEEDBACK["care"]["self_harm"]
                    )
        return GENTLE_FEEDBACK["care"]["self_harm"]

    # 处理 BLOCK 情况
    if result == AuditResult.BLOCK:
        result_key = "block"
    elif result == AuditResult.WARN:
        result_key = "warn"
    else:
        return ""

    feedback_map = GENTLE_FEEDBACK.get(result_key, {})
    label_str = label.value if isinstance(label, AuditLabel) else label

    if label_str and label_str in feedback_map:
        return feedback_map[label_str]

    return feedback_map.get("default", "内容审核未通过，请修改后重试。")


# ---------------------------------------------------------------------------
# 审核结果数据类
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class AuditResultData:
    """审核结果数据类。

    包含审核的完整结果信息，支持序列化和便捷访问。
    """

    result: AuditResult = AuditResult.PASS
    passed: bool = True
    is_blocked: bool = False
    labels: list[str] = field(default_factory=list)
    reason: str | None = None
    feedback: str | None = None
    trigger_care: bool = False
    care_level: str | None = None  # low / medium / high
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式。"""
        return {
            "result": self.result.value,
            "passed": self.passed,
            "is_blocked": self.is_blocked,
            "labels": self.labels,
            "reason": self.reason,
            "feedback": self.feedback,
            "trigger_care": self.trigger_care,
            "care_level": self.care_level,
            "metadata": self.metadata,
        }

    @classmethod
    def pass_result(cls) -> "AuditResultData":
        """创建通过结果。"""
        return cls(result=AuditResult.PASS, passed=True, is_blocked=False)

    @classmethod
    def block_result(
        cls,
        label: str,
        reason: str,
        feedback: str | None = None,
    ) -> "AuditResultData":
        """创建拦截结果。"""
        return cls(
            result=AuditResult.BLOCK,
            passed=False,
            is_blocked=True,
            labels=[label],
            reason=reason,
            feedback=feedback or get_gentle_feedback(AuditResult.BLOCK, label),
        )

    @classmethod
    def warn_result(
        cls,
        label: str,
        reason: str,
        feedback: str | None = None,
    ) -> "AuditResultData":
        """创建警告结果。"""
        return cls(
            result=AuditResult.WARN,
            passed=True,
            is_blocked=False,
            labels=[label],
            reason=reason,
            feedback=feedback or get_gentle_feedback(AuditResult.WARN, label),
        )

    @classmethod
    def care_result(
        cls,
        care_level: str,
        labels: list[str],
        reason: str,
    ) -> "AuditResultData":
        """创建关怀触发结果。"""
        return cls(
            result=AuditResult.PASS_WITH_CARE,
            passed=True,
            is_blocked=False,
            labels=labels,
            reason=reason,
            feedback=None,  # 不给用户反馈，后台处理
            trigger_care=True,
            care_level=care_level,
        )


# 别名，保持向后兼容
AuditCheckResult = AuditResultData


# ---------------------------------------------------------------------------
# 危机关键词配置（三层检测）
# ---------------------------------------------------------------------------

# 第一层：情绪低落关键词
CRISIS_KEYWORDS_LOW: list[str] = [
    "好累", "撑不下去", "没有意义", "没意义", "活着没意思",
    "生无可恋", "绝望", "崩溃", "窒息", "透不过气",
    "好痛苦", "太痛苦了", "扛不住", "受不了了", "不想面对",
    "没有希望", "没希望", "看不到未来", "毫无意义",
]

# 第二层：自残意念关键词
CRISIS_KEYWORDS_MEDIUM: list[str] = [
    "想死", "自杀", "不想活", "了结", "结束生命",
    "解脱", "离开这个世界", "不再醒来", "怎么死", "跳楼",
    "割腕", "服药", "消失", "最好的方式", "去死",
    "活着好累", "没有活下去", "想结束", "结束一切",
    "划自己", "割自己", "伤害自己", "自残",
    "用刀", "拿刀", "烫自己", "掐自己", "拿头撞墙",
]

# 第三层：紧急信号关键词
CRISIS_KEYWORDS_HIGH: list[str] = [
    "已经吃了", "马上就", "告别", "最后一次",
    "吃了一整瓶药", "吃了好多药", "吃药了", "准备好了",
    "现在就去", "写好了遗书", "安排好后事",
    "今晚就", "明天就去", "再见世界",
]

# 否定词（用于排除误判）
NEGATION_WORDS: list[str] = [
    "不想死", "不想自杀", "不会自杀", "不想伤害自己",
    "只是想", "开玩笑", "说笑", "打趣", "比喻",
]


# ---------------------------------------------------------------------------
# 违规内容关键词配置
# ---------------------------------------------------------------------------

# 人身攻击关键词
PERSONAL_ATTACK_KEYWORDS: list[str] = [
    "傻逼", "傻x", "sb", "贱人", "婊子", "畜生",
    "王八蛋", "混蛋", "渣男", "渣女", "恶心",
    "滚蛋", "死开", "该死", "你妈", "他妈",
]

# 广告引流关键词
ADVERTISEMENT_KEYWORDS: list[str] = [
    "兼职", "赚钱", "招聘", "代理", "招商",
    "低价", "优惠", "折扣", "促销", "特价",
    "代购", "微商", "团购", "秒杀", "抢购",
    "返利", "佣金", "提成", "收益", "月入",
]

# 色情关键词
PORNOGRAPHY_KEYWORDS: list[str] = [
    "约炮", "一夜情", "炮友", "裸聊", "裸照",
    "情趣", "成人", "黄色", "性服务", "包养",
]

# 暴力恐怖关键词
VIOLENCE_KEYWORDS: list[str] = [
    "杀人", "砍死", "捅死", "打死", "弄死",
    "恐怖", "炸弹", "爆炸", "袭击", "报复社会",
]


# ---------------------------------------------------------------------------
# 联系方式正则模式
# ---------------------------------------------------------------------------

# 微信号格式检测
WECHAT_ID_PATTERN = re.compile(
    r'(?:微信号?|微信|vx|weixin|加我)[:\s：]*\s*'
    r'([a-zA-Z][a-zA-Z0-9_-]{5,19})',
    re.IGNORECASE,
)

# 手机号格式检测（中国大陆）
PHONE_NUMBER_PATTERN = re.compile(
    r'(?:手机号?|电话|tel|phone|联系方式|联系我)[:\s：]*\s*'
    r'(1[3-9]\d{9})'
    r'|'
    r'(?<!\d)(1[3-9]\d{9})(?!\d)',  # 直接出现的手机号
)

# QQ号格式检测
QQ_NUMBER_PATTERN = re.compile(
    r'(?:QQ号?|qq号?|加QQ|加qq)[:\s：]*\s*(\d{5,12})',
    re.IGNORECASE,
)

# 外链检测
URL_PATTERN = re.compile(
    r'https?://(?:www\.)?[^\s/$.?#].[^\s]*',
    re.IGNORECASE,
)

# 联系方式检测模式集合
CONTACT_INFO_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("wechat", WECHAT_ID_PATTERN),
    ("phone", PHONE_NUMBER_PATTERN),
    ("qq", QQ_NUMBER_PATTERN),
    ("url", URL_PATTERN),
]


# ---------------------------------------------------------------------------
# 审核基类
# ---------------------------------------------------------------------------

class BaseAudit(ABC):
    """审核服务基类。

    定义审核服务的公共接口和工具方法。
    子类需要实现 check() 方法以提供具体的审核逻辑。

    Attributes:
        strictness: 审核严格度级别
    """

    def __init__(self, strictness: AuditStrictness = AuditStrictness.MEDIUM) -> None:
        """初始化审核器。

        Args:
            strictness: 审核严格度级别
        """
        self._strictness = strictness
        self._low_pattern = self._compile_pattern(CRISIS_KEYWORDS_LOW)
        self._medium_pattern = self._compile_pattern(CRISIS_KEYWORDS_MEDIUM)
        self._high_pattern = self._compile_pattern(CRISIS_KEYWORDS_HIGH)
        self._negation_pattern = self._compile_pattern(NEGATION_WORDS)

        logger.info(
            "[%s] 初始化完成，严格度: %s",
            self.__class__.__name__,
            strictness.value
        )

    @staticmethod
    def _compile_pattern(keywords: list[str]) -> re.Pattern | None:
        """编译关键词列表为正则表达式。

        Args:
            keywords: 关键词列表

        Returns:
            编译后的正则表达式，如果列表为空则返回 None
        """
        if not keywords:
            return None
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        pattern_str = "|".join(re.escape(kw) for kw in sorted_keywords)
        return re.compile(pattern_str)

    def _contains_negation(self, text: str) -> bool:
        """检查文本中是否包含否定词。

        Args:
            text: 用户输入文本

        Returns:
            是否包含否定词
        """
        if self._negation_pattern is None:
            return False
        return bool(self._negation_pattern.search(text))

    def _match_keywords(self, text: str, pattern: re.Pattern | None) -> list[str]:
        """匹配文本中的关键词。

        Args:
            text: 用户输入文本
            pattern: 编译后的正则表达式

        Returns:
            匹配到的关键词列表
        """
        if pattern is None:
            return []
        matches = pattern.findall(text)
        return list(set(matches)) if matches else []

    def _detect_crisis(self, text: str) -> tuple[str, list[str]] | None:
        """检测文本中的危机信号。

        按优先级检测：HIGH > MEDIUM > LOW

        Args:
            text: 用户输入文本

        Returns:
            (危机级别, 匹配关键词) 或 None
        """
        has_negation = self._contains_negation(text)

        # 第三层：紧急信号
        high_keywords = self._match_keywords(text, self._high_pattern)
        if high_keywords:
            logger.warning(
                "[%s] 检测到 HIGH 级别危机信号，关键词: %s",
                self.__class__.__name__,
                high_keywords
            )
            return ("high", high_keywords)

        # 第二层：自残意念
        medium_keywords = self._match_keywords(text, self._medium_pattern)
        if medium_keywords and not has_negation:
            logger.warning(
                "[%s] 检测到 MEDIUM 级别危机信号，关键词: %s",
                self.__class__.__name__,
                medium_keywords
            )
            return ("medium", medium_keywords)

        # 第一层：情绪低落
        low_keywords = self._match_keywords(text, self._low_pattern)
        if low_keywords and not has_negation:
            logger.info(
                "[%s] 检测到 LOW 级别危机信号，关键词: %s",
                self.__class__.__name__,
                low_keywords
            )
            return ("low", low_keywords)

        return None

    def _detect_contact_info(self, text: str) -> list[tuple[str, str]]:
        """检测文本中的联系方式。

        Args:
            text: 用户输入文本

        Returns:
            检测到的联系方式列表 [(类型, 匹配内容), ...]
        """
        detected: list[tuple[str, str]] = []

        for label, pattern in CONTACT_INFO_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                for match in matches if isinstance(matches, list) else [matches]:
                    if isinstance(match, tuple):
                        match = match[0] or match[1] if len(match) > 1 else match[0]
                    detected.append((label, str(match)))

        return detected

    @abstractmethod
    async def check(self, content: str, **kwargs: Any) -> AuditCheckResult:
        """审核内容。

        Args:
            content: 待审核的文本内容
            **kwargs: 额外的审核参数

        Returns:
            审核结果
        """
        ...

    def get_strictness(self) -> AuditStrictness:
        """获取当前审核严格度。

        Returns:
            审核严格度级别
        """
        return self._strictness


# ---------------------------------------------------------------------------
# 热线信息
# ---------------------------------------------------------------------------

HELPLINE_INFO = {
    "national": "全国24小时心理援助热线：400-161-9995",
    "beijing": "北京心理危机研究与干预中心：010-82951332",
    "youth": "青少年服务热线：12355",
    "emergency": "急救电话：120",
    "police": "报警电话：110",
}


def format_helpline(level: str = "medium") -> str:
    """格式化热线信息。

    Args:
        level: 危机级别

    Returns:
        格式化后的热线信息文本
    """
    if level == "high":
        return (
            f"{HELPLINE_INFO['emergency']}\n"
            f"{HELPLINE_INFO['national']}\n"
            "请立即寻求专业帮助，你的生命很重要。"
        )
    elif level == "medium":
        return (
            f"{HELPLINE_INFO['national']}\n"
            f"{HELPLINE_INFO['youth']}"
        )
    else:
        return (
            f"{HELPLINE_INFO['national']}"
        )
