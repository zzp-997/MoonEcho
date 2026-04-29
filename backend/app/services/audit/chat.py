"""私聊场景审核器。

实现 modules_design.md 7.3 规定的私聊审核策略：
- 审核严格度：中
- 事前拦截：色情/广告
- 特殊处理：骚扰检测
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
    PORNOGRAPHY_KEYWORDS,
    ADVERTISEMENT_KEYWORDS,
    get_gentle_feedback,
)

logger = logging.getLogger(__name__)


class ChatAuditor(BaseAudit):
    """私聊内容审核器。

    根据 modules_design.md 7.3 差异化审核策略：
    - 审核严格度：中
    - 色情/广告：拦截
    - 骚扰：标记+提醒
    - 联系方式：提示保护隐私

    私聊场景相对宽松，主要关注色情、广告和骚扰。
    """

    def __init__(self) -> None:
        """初始化私聊审核器（中严格度）。"""
        super().__init__(strictness=AuditStrictness.MEDIUM)

        self._porn_pattern = self._compile_pattern(PORNOGRAPHY_KEYWORDS)
        self._ad_pattern = self._compile_pattern(ADVERTISEMENT_KEYWORDS)

    async def check(
        self,
        content: str,
        sender_id: str | None = None,
        receiver_id: str | None = None,
        **kwargs: Any,
    ) -> AuditCheckResult:
        """审核私聊内容。

        审核流程：
        1. 检测色情内容
        2. 检测广告引流
        3. 检测联系方式（警告）

        Args:
            content: 待审核内容
            sender_id: 发送者ID
            receiver_id: 接收者ID
            **kwargs: 额外参数

        Returns:
            审核结果
        """
        metadata: dict[str, Any] = {}
        if sender_id:
            metadata["sender_id"] = sender_id
        if receiver_id:
            metadata["receiver_id"] = receiver_id

        # 1. 检测色情内容
        porn_keywords = self._match_keywords(content, self._porn_pattern)
        if porn_keywords:
            return AuditCheckResult.block_result(
                label=AuditLabel.PORNOGRAPHY.value,
                reason=f"检测到不当内容: {', '.join(porn_keywords)}",
            )

        # 2. 检测广告引流（私聊场景需要多个关键词才拦截）
        ad_keywords = self._match_keywords(content, self._ad_pattern)
        if ad_keywords and len(ad_keywords) >= 3:
            return AuditCheckResult.block_result(
                label=AuditLabel.ADVERTISEMENT.value,
                reason=f"检测到广告内容: {', '.join(ad_keywords)}",
            )

        # 3. 检测联系方式（警告但不拦截）
        contact_detected = self._detect_contact_info(content)
        if contact_detected:
            contact_labels = [t for t, _ in contact_detected]
            metadata["contact_info"] = contact_detected
            return AuditCheckResult(
                result=AuditResult.WARN,
                passed=True,
                is_blocked=False,
                labels=[AuditLabel.CONTACT_INFO.value] + contact_labels,
                reason="检测到联系方式",
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
