"""审核服务模块。

提供分场景差异化审核能力：
- TreeholeAuditor: 树洞审核（中高严格度）
- PostAuditor: 动态广场审核（高严格度）
- ChatAuditor: 私聊审核（中严格度）
- AIChatAuditor: AI对话审核（低严格度）

使用示例：
    from app.services.audit import TreeholeAuditor, AuditResult

    auditor = TreeholeAuditor()
    result = await auditor.check(content)
    if result.passed:
        # 允许发布
        pass
    elif result.trigger_care:
        # 触发关怀流程
        pass
    else:
        # 显示 result.feedback 给用户
        pass
"""

from .base import (
    AuditCheckResult,
    AuditLabel,
    AuditResult,
    AuditStrictness,
    BaseAuditor,
    GENTLE_FEEDBACK,
    HELPLINE_INFO,
    NEGATION_WORDS,
    format_helpline,
    get_gentle_feedback,
)

__all__ = [
    # 基础类和枚举
    "AuditResult",
    "AuditLabel",
    "AuditStrictness",
    "AuditCheckResult",
    "BaseAuditor",
    # 工具函数
    "get_gentle_feedback",
    "format_helpline",
    # 配置
    "GENTLE_FEEDBACK",
    "HELPLINE_INFO",
    "NEGATION_WORDS",
]
