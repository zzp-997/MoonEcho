"""树洞场景审核器。

实现 modules_design.md 7.3 规定的树洞审核策略：
- 审核严格度：中高
- 事前拦截：色情/广告/暴恐
- 特殊处理：自残触发关怀流程
- 温和反馈设计

关键区分：
- "领导傻X"（情绪宣泄）→ 不拦
- "@某人你傻X"（定向辱骂）→ 要拦
"""

from __future__ import annotations

import logging
import re
from typing import Any

from .base import (
    AuditCheckResult,
    AuditLabel,
    AuditResult,
    AuditStrictness,
    BaseAudit,
    PERSONAL_ATTACK_KEYWORDS,
    ADVERTISEMENT_KEYWORDS,
    PORNOGRAPHY_KEYWORDS,
    VIOLENCE_KEYWORDS,
    get_gentle_feedback,
)

logger = logging.getLogger(__name__)


# 人身攻击模式（@某人 + 辱骂）
PERSONAL_ATTACK_PATTERNS: list[tuple[str, str]] = [
    (r"[@@]\s*\S+.*(?:傻逼|傻x|sb|贱人|婊子|畜生|王八蛋|混蛋)", "定向辱骂"),
    (r"你\s*(?:是|真|好|这个)\s*(?:傻逼|傻x|sb|贱人|婊子|畜生|王八蛋|混蛋)", "定向辱骂"),
    (r"(?:傻逼|傻x|sb|贱人|婊子|畜生|王八蛋|混蛋)\s*(?:去死|滚|消失)", "威胁辱骂"),
]

# 广告引流模式
ADVERTISEMENT_PATTERNS: list[tuple[str, str]] = [
    (r"加\s*(?:微信|vx|qq|群)", "引流"),
    (r"联系\s*(?:我|微信|qq)", "引流"),
    (r"私信\s*(?:我|获取|领取)", "引流"),
    (r"添加微信|加微信|扫码|二维码", "引流"),
]


class TreeholeAuditor(BaseAudit):
    """树洞场景内容审核器。

    根据 modules_design.md 4.6 差异化审核策略：
    - 自伤内容：允许发布，触发关怀流程（不拦截）
    - 人身攻击：区分情绪宣泄和定向攻击
    - 广告引流：拦截
    - 色情内容：拦截
    - 暴力恐怖：拦截

    温和审核反馈遵循 modules_design.md 7.11 规范。
    """

    def __init__(self) -> None:
        """初始化树洞审核器（中高严格度）。"""
        super().__init__(strictness=AuditStrictness.HIGH)

        # 编译额外模式
        self._attack_pattern = self._compile_tuple_patterns(PERSONAL_ATTACK_PATTERNS)
        self._ad_pattern = self._compile_tuple_patterns(ADVERTISEMENT_PATTERNS)
        self._porn_pattern = self._compile_pattern(PORNOGRAPHY_KEYWORDS)
        self._violence_pattern = self._compile_pattern(VIOLENCE_KEYWORDS)
        self._attack_keywords_pattern = self._compile_pattern(PERSONAL_ATTACK_KEYWORDS)
        self._ad_keywords_pattern = self._compile_pattern(ADVERTISEMENT_KEYWORDS)

    @staticmethod
    def _compile_tuple_patterns(
        patterns: list[tuple[str, str]]
    ) -> list[tuple[re.Pattern, str]]:
        """编译元组模式列表。

        Args:
            patterns: (正则表达式字符串, 标签) 列表

        Returns:
            编译后的 (Pattern, 标签) 列表
        """
        return [(re.compile(p, re.IGNORECASE), label) for p, label in patterns]

    def _match_tuple_patterns(
        self,
        text: str,
        patterns: list[tuple[re.Pattern, str]],
    ) -> list[str]:
        """匹配元组模式列表。

        Args:
            text: 用户输入文本
            patterns: 编译后的 (Pattern, 标签) 列表

        Returns:
            匹配到的标签列表
        """
        matched: list[str] = []
        for pattern, label in patterns:
            if pattern.search(text):
                matched.append(label)
        return matched

    async def check(self, content: str, **kwargs: Any) -> AuditCheckResult:
        """审核树洞内容。

        审核流程：
        1. 检测自伤/危机内容（最高优先级）
        2. 检测定向人身攻击
        3. 检测广告引流
        4. 检测色情内容
        5. 检测暴力恐怖内容

        Args:
            content: 待审核内容
            **kwargs: 额外参数（未使用）

        Returns:
            审核结果
        """
        # 1. 检测危机/自伤内容（最高优先级，允许发布但触发关怀）
        crisis = self._detect_crisis(content)
        if crisis:
            level, keywords = crisis
            return AuditCheckResult.care_result(
                care_level=level,
                labels=[AuditLabel.SELF_HARM.value],
                reason=f"检测到自伤内容: {', '.join(keywords)}",
            )

        # 2. 检测定向人身攻击
        attack_pattern_matched = self._match_tuple_patterns(content, self._attack_pattern)
        if attack_pattern_matched:
            # @某人 + 辱骂模式，直接拦截
            return AuditCheckResult.block_result(
                label=AuditLabel.PERSONAL_ATTACK.value,
                reason=f"检测到定向攻击: {', '.join(attack_pattern_matched)}",
            )

        # 检查纯辱骂词汇
        attack_keywords = self._match_keywords(content, self._attack_keywords_pattern)
        if attack_keywords:
            # 判断是否针对具体人
            if "@" in content or self._has_specific_target(content):
                return AuditCheckResult.block_result(
                    label=AuditLabel.PERSONAL_ATTACK.value,
                    reason=f"检测到定向攻击: {', '.join(attack_keywords)}",
                )
            else:
                # 纯情绪宣泄，警告但不拦截
                return AuditCheckResult.warn_result(
                    label="emotional_expression",
                    reason=f"检测到情绪宣泄词汇: {', '.join(attack_keywords)}",
                )

        # 3. 检测广告引流
        ad_pattern_matched = self._match_tuple_patterns(content, self._ad_pattern)
        ad_keywords = self._match_keywords(content, self._ad_keywords_pattern)

        if ad_pattern_matched or (ad_keywords and len(ad_keywords) >= 2):
            return AuditCheckResult.block_result(
                label=AuditLabel.ADVERTISEMENT.value,
                reason=f"检测到广告引流: {', '.join(ad_pattern_matched + ad_keywords)}",
            )

        # 4. 检测色情内容
        porn_keywords = self._match_keywords(content, self._porn_pattern)
        if porn_keywords:
            return AuditCheckResult.block_result(
                label=AuditLabel.PORNOGRAPHY.value,
                reason=f"检测到色情内容: {', '.join(porn_keywords)}",
            )

        # 5. 检测暴力恐怖内容
        violence_keywords = self._match_keywords(content, self._violence_pattern)
        if violence_keywords:
            return AuditCheckResult.block_result(
                label=AuditLabel.VIOLENCE.value,
                reason=f"检测到暴力内容: {', '.join(violence_keywords)}",
            )

        # 通过审核
        return AuditCheckResult.pass_result()

    def _has_specific_target(self, content: str) -> bool:
        """判断内容是否针对具体对象。

        Args:
            content: 用户内容

        Returns:
            是否针对具体对象
        """
        target_patterns = [
            r"你\s*(?:是|真|好)",
            r"那个\s*\S+",
            r"[他她它]",
        ]
        for pattern in target_patterns:
            if re.search(pattern, content):
                return True
        return False
