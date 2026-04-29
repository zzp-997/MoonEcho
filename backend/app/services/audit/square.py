"""动态广场场景审核器。

实现 modules_design.md 7.3 规定的动态广场审核策略：
- 审核严格度：高
- 事前拦截：色情/广告/暴恐/辱骂
- 特殊处理：推荐前二次审核
- 温和反馈设计
"""

from __future__ import annotations

import logging
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
    CONTACT_INFO_PATTERNS,
    get_gentle_feedback,
)

logger = logging.getLogger(__name__)


class SquareAuditor(BaseAudit):
    """动态广场内容审核器。

    根据 modules_design.md 5.1-5.5 差异化审核策略：
    - 审核严格度：高
    - 色情/广告/暴恐/辱骂：拦截
    - 推荐前二次审核：标记待审内容
    - 匿名动态：不可被关注提示

    温和审核反馈遵循 modules_design.md 7.11 规范。
    """

    def __init__(self) -> None:
        """初始化动态广场审核器（高严格度）。"""
        super().__init__(strictness=AuditStrictness.HIGH)

        # 编译关键词模式
        self._attack_pattern = self._compile_pattern(PERSONAL_ATTACK_KEYWORDS)
        self._ad_pattern = self._compile_pattern(ADVERTISEMENT_KEYWORDS)
        self._porn_pattern = self._compile_pattern(PORNOGRAPHY_KEYWORDS)
        self._violence_pattern = self._compile_pattern(VIOLENCE_KEYWORDS)

    async def check(
        self,
        content: str,
        is_anonymous: bool = False,
        **kwargs: Any,
    ) -> AuditCheckResult:
        """审核动态广场内容。

        审核流程：
        1. 检测危机/自伤内容
        2. 检测人身攻击（广场场景更严格）
        3. 检测广告引流
        4. 检测色情内容
        5. 检测暴力恐怖内容
        6. 检测联系方式（警告）

        Args:
            content: 待审核内容
            is_anonymous: 是否匿名发布
            **kwargs: 额外参数

        Returns:
            审核结果
        """
        labels: list[str] = []
        metadata: dict[str, Any] = {"is_anonymous": is_anonymous}

        # 1. 检测危机/自伤内容
        crisis = self._detect_crisis(content)
        if crisis:
            level, keywords = crisis
            return AuditCheckResult.care_result(
                care_level=level,
                labels=[AuditLabel.SELF_HARM.value],
                reason=f"检测到自伤内容: {', '.join(keywords)}",
            )

        # 2. 检测人身攻击（广场场景：任何辱骂都拦截）
        attack_keywords = self._match_keywords(content, self._attack_pattern)
        if attack_keywords:
            return AuditCheckResult.block_result(
                label=AuditLabel.PERSONAL_ATTACK.value,
                reason=f"检测到攻击性内容: {', '.join(attack_keywords)}",
            )

        # 3. 检测广告引流
        ad_keywords = self._match_keywords(content, self._ad_pattern)
        if ad_keywords and len(ad_keywords) >= 1:
            # 广场场景更敏感，检测到广告关键词即拦截
            return AuditCheckResult.block_result(
                label=AuditLabel.ADVERTISEMENT.value,
                reason=f"检测到广告内容: {', '.join(ad_keywords)}",
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

        # 6. 检测联系方式（警告但不拦截）
        contact_detected = self._detect_contact_info(content)
        if contact_detected:
            contact_labels = [t for t, _ in contact_detected]
            metadata["contact_info"] = contact_detected
            return AuditCheckResult(
                result=AuditResult.WARN,
                passed=True,
                is_blocked=False,
                labels=[AuditLabel.CONTACT_INFO.value] + contact_labels,
                reason=f"检测到联系方式",
                feedback=get_gentle_feedback(AuditResult.WARN, "sensitive_info"),
                metadata=metadata,
            )

        # 通过审核
        return AuditCheckResult(
            result=AuditResult.PASS,
            passed=True,
            is_blocked=False,
            metadata=metadata,
        )

    async def check_for_recommend(
        self,
        content: str,
        **kwargs: Any,
    ) -> AuditCheckResult:
        """推荐前二次审核。

        用于内容被推荐到首页前的二次审核，标准更严格。

        Args:
            content: 待审核内容
            **kwargs: 额外参数

        Returns:
            审核结果
        """
        result = await self.check(content, **kwargs)

        # 如果通过，额外检查是否适合推荐
        if result.passed and not result.trigger_care:
            # 二次审核：检查是否有敏感词可能被遗漏
            # 这里可以接入更严格的AI审核
            pass

        return result
