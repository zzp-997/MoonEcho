"""AI对话场景审核器。

实现 modules_design.md 7.3 规定的AI对话审核策略：
- 审核严格度：低
- 仅自残预警触发

AI对话场景原则上不审核对话内容，唯一例外是自残/自杀风险检测。
"""

from __future__ import annotations

import logging
from typing import Any

from .base import (
    AuditCheckResult,
    AuditLabel,
    AuditStrictness,
    BaseAudit,
    format_helpline,
)

logger = logging.getLogger(__name__)


class AIChatAuditor(BaseAudit):
    """AI对话内容审核器。

    根据 modules_design.md 7.3 差异化审核策略：
    - 审核严格度：低
    - 仅自残/自杀风险检测触发

    核心原则：
    - AI对话是用户最私密的倾诉空间，不审核常规内容
    - 唯一例外是检测到自伤/自杀风险时触发关怀流程
    - 危机干预不是审核、不是拦截，是关怀、陪伴、引导求助
    """

    def __init__(self) -> None:
        """初始化AI对话审核器（低严格度）。"""
        super().__init__(strictness=AuditStrictness.LOW)

    async def check(
        self,
        content: str,
        **kwargs: Any,
    ) -> AuditCheckResult:
        """审核AI对话内容。

        仅检测自残/自杀风险，其他内容一律通过。

        Args:
            content: 待审核内容
            **kwargs: 额外参数

        Returns:
            审核结果
        """
        # 仅检测危机/自伤内容
        crisis = self._detect_crisis(content)
        if crisis:
            level, keywords = crisis

            # 构建包含热线信息的结果
            helpline = format_helpline(level)

            return AuditCheckResult(
                result=AuditCheckResult.__annotations__['result'].__args__[0].PASS_WITH_CARE,
                passed=True,
                is_blocked=False,
                labels=[AuditLabel.SELF_HARM.value, AuditLabel.SUICIDE_IDEATION.value],
                reason=f"检测到危机信号: {', '.join(keywords)}",
                feedback=None,  # AI对话中由AI自己处理回复
                trigger_care=True,
                care_level=level,
                metadata={
                    "helpline": helpline,
                    "keywords": keywords,
                },
            )

        # 通过审核（AI对话场景不审核其他内容）
        return AuditCheckResult.pass_result()

    def get_crisis_response(self, level: str) -> str:
        """获取危机响应提示。

        根据危机级别返回相应的AI回复提示。

        Args:
            level: 危机级别 (low/medium/high)

        Returns:
            AI回复提示
        """
        responses = {
            "low": (
                "我听到了你的疲惫。如果愿意的话，"
                "可以多和我说说你的感受，我会一直在这里。"
            ),
            "medium": (
                "你说的话让我很担心。请记住，你不是一个人，"
                "有很多人愿意帮助你。如果需要，可以拨打：\n"
                f"{format_helpline('medium')}"
            ),
            "high": (
                "我能感受到你正在经历非常困难的时刻。"
                "请立即寻求专业帮助，你的生命很重要。\n"
                f"{format_helpline('high')}"
            ),
        }
        return responses.get(level, responses["low"])
