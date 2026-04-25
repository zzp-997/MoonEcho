"""危机关键词检测服务。

提供三层危机信号检测：
- 第一层（LOW）：情绪低落，如"好累"、"撑不下去"、"没有意义"
- 第二层（MEDIUM）：自残意念，如"想死"、"不想活了"、"结束一切"
- 第三层（HIGH）：紧急信号，如"已经吃了"、"马上就"、"告别"

检测到危机信号时，根据级别返回相应的安全响应（含热线信息）。
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 危机级别枚举
# ---------------------------------------------------------------------------

class CrisisLevel(str, Enum):
    """危机级别枚举。"""
    LOW = "low"           # 情绪低落，AI 深度关怀模式
    MEDIUM = "medium"     # 自残意念，AI 危机关怀 + 提供热线
    HIGH = "high"         # 紧急信号，AI 持续陪伴 + 弹窗热线 + 标记人工复核


# ---------------------------------------------------------------------------
# 危机关键词配置
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
    "只是想", "开玩笑", "说笑", "打趣",
]


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


# ---------------------------------------------------------------------------
# 危机响应模板
# ---------------------------------------------------------------------------

CRISIS_RESPONSES: dict[CrisisLevel, dict[str, Any]] = {
    CrisisLevel.LOW: {
        "message": "我能感受到你现在很不容易。如果愿意的话，可以多和我说说你的感受。",
        "append_hotline": False,
        "require_human_review": False,
        "suggestion": "建议尝试一些放松方式，比如深呼吸、散步，或与信任的人聊聊。",
    },
    CrisisLevel.MEDIUM: {
        "message": "你说的话让我很担心。请记住，你不是一个人，有很多人愿意帮助你。\n\n{helpline}",
        "append_hotline": True,
        "require_human_review": True,
        "suggestion": "建议立即拨打心理援助热线，获取专业支持。",
    },
    CrisisLevel.HIGH: {
        "message": "你现在的情况非常紧急，请立即寻求帮助！\n\n{helpline}\n\n如果你正处于危险中，请立即拨打 120 急救电话或 110 报警电话。",
        "append_hotline": True,
        "require_human_review": True,
        "suggestion": "紧急情况，建议立即拨打急救或报警电话。",
        "alert_popup": True,  # 前端弹窗提示
    },
}


# ---------------------------------------------------------------------------
# 危机检测器
# ---------------------------------------------------------------------------

class CrisisDetector:
    """危机关键词检测器。

    检测用户输入中的危机信号，返回危机级别和相应响应。

    使用示例：
        detector = CrisisDetector()
        result = detector.detect("我想死")
        if result:
            print(result.level)  # CrisisLevel.MEDIUM
            print(result.response)  # 危机响应信息
    """

    def __init__(self) -> None:
        """初始化危机检测器。"""
        # 编译正则表达式以提高效率
        self._low_pattern = self._compile_pattern(CRISIS_KEYWORDS_LOW)
        self._medium_pattern = self._compile_pattern(CRISIS_KEYWORDS_MEDIUM)
        self._high_pattern = self._compile_pattern(CRISIS_KEYWORDS_HIGH)
        self._negation_pattern = self._compile_pattern(NEGATION_WORDS)

        logger.info("[CrisisDetector] 初始化完成")

    def _compile_pattern(self, keywords: list[str]) -> re.Pattern | None:
        """编译关键词列表为正则表达式。

        Args:
            keywords: 关键词列表

        Returns:
            编译后的正则表达式，如果列表为空则返回 None
        """
        if not keywords:
            return None
        # 使用 | 连接所有关键词，按长度降序排列以优先匹配长词
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

    def detect(self, text: str) -> dict[str, Any] | None:
        """检测文本中的危机信号。

        检测优先级：HIGH > MEDIUM > LOW

        Args:
            text: 用户输入文本

        Returns:
            危机检测结果字典，包含：
            - level: CrisisLevel 枚举值
            - keywords: 匹配到的关键词列表
            - response: 危机响应信息
            如果未检测到危机信号，返回 None
        """
        if not text or not text.strip():
            return None

        # 检查是否包含否定词（排除误判）
        has_negation = self._contains_negation(text)

        # 按优先级检测：HIGH > MEDIUM > LOW
        # 第三层：紧急信号
        high_keywords = self._match_keywords(text, self._high_pattern)
        if high_keywords:
            logger.warning(
                "[CrisisDetector] 检测到 HIGH 级别危机信号，关键词: %s",
                high_keywords
            )
            return self._build_result(CrisisLevel.HIGH, high_keywords, text)

        # 第二层：自残意念
        medium_keywords = self._match_keywords(text, self._medium_pattern)
        if medium_keywords and not has_negation:
            logger.warning(
                "[CrisisDetector] 检测到 MEDIUM 级别危机信号，关键词: %s",
                medium_keywords
            )
            return self._build_result(CrisisLevel.MEDIUM, medium_keywords, text)

        # 第一层：情绪低落
        low_keywords = self._match_keywords(text, self._low_pattern)
        if low_keywords and not has_negation:
            logger.info(
                "[CrisisDetector] 检测到 LOW 级别危机信号，关键词: %s",
                low_keywords
            )
            return self._build_result(CrisisLevel.LOW, low_keywords, text)

        return None

    def _build_result(
        self,
        level: CrisisLevel,
        keywords: list[str],
        text: str,
    ) -> dict[str, Any]:
        """构建检测结果字典。

        Args:
            level: 危机级别
            keywords: 匹配到的关键词
            text: 原始文本

        Returns:
            检测结果字典
        """
        response_template = CRISIS_RESPONSES[level]
        helpline_text = self._format_helpline()

        # 格式化消息
        message = response_template["message"]
        if response_template.get("append_hotline"):
            message = message.format(helpline=helpline_text)

        return {
            "level": level,
            "keywords": keywords,
            "response": {
                "message": message,
                "helpline": helpline_text if response_template.get("append_hotline") else None,
                "require_human_review": response_template.get("require_human_review", False),
                "alert_popup": response_template.get("alert_popup", False),
                "suggestion": response_template.get("suggestion"),
            },
        }

    def _format_helpline(self) -> str:
        """格式化热线信息。

        Returns:
            格式化后的热线信息文本
        """
        lines = [
            f"- {HELPLINE_INFO['national']}",
            f"- {HELPLINE_INFO['youth']}",
            f"- {HELPLINE_INFO['beijing']}",
        ]
        return "\n".join(lines)

    def get_response(self, level: CrisisLevel) -> dict[str, Any]:
        """根据危机级别返回响应。

        Args:
            level: 危机级别

        Returns:
            危机响应信息字典
        """
        response_template = CRISIS_RESPONSES[level]
        helpline_text = self._format_helpline()

        message = response_template["message"]
        if response_template.get("append_hotline"):
            message = message.format(helpline=helpline_text)

        return {
            "message": message,
            "helpline": helpline_text if response_template.get("append_hotline") else None,
            "require_human_review": response_template.get("require_human_review", False),
            "alert_popup": response_template.get("alert_popup", False),
            "suggestion": response_template.get("suggestion"),
        }

    def get_safety_appendix(self, level: CrisisLevel) -> str:
        """获取追加到 AI 回复后的安全提示。

        Args:
            level: 危机级别

        Returns:
            安全提示文本
        """
        if level == CrisisLevel.HIGH:
            return (
                "\n\n---\n"
                "紧急求助信息：\n"
                f"{HELPLINE_INFO['emergency']}\n"
                f"{HELPLINE_INFO['national']}\n"
                "请立即寻求专业帮助，你的生命很重要。"
            )
        elif level == CrisisLevel.MEDIUM:
            return (
                "\n\n---\n"
                "如果你正在经历困难，请记住有人愿意帮助你：\n"
                f"{HELPLINE_INFO['national']}\n"
                f"{HELPLINE_INFO['youth']}"
            )
        else:
            return ""


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------

_crisis_detector: CrisisDetector | None = None


def get_crisis_detector() -> CrisisDetector:
    """获取全局危机检测器实例。

    Returns:
        CrisisDetector 实例
    """
    global _crisis_detector
    if _crisis_detector is None:
        _crisis_detector = CrisisDetector()
    return _crisis_detector


def reset_crisis_detector() -> None:
    """重置全局危机检测器实例（用于测试）。"""
    global _crisis_detector
    _crisis_detector = None
