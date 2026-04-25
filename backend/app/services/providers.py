"""Provider 注册表模块。

聚合各服务模块的 Provider，提供统一的注册表构建能力。
维护与原有代码的兼容性，同时支持从子模块获取 Provider。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import AppSettings
from app.services.ai_chat import AIChatProtocol, create_ai_chat_service
from app.services.content_audit import (
    ContentAuditProtocol,
    create_content_audit_service,
)
from app.services.push import PushProtocol, create_push_service
from app.services.sms import SMSServiceProtocol, create_sms_service
from app.services.storage import StorageProtocol, create_storage_service


# ---------------------------------------------------------------------------
# Provider 注册表 — 管理所有 Provider 实例
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ProviderRegistry:
    """Provider 注册表，包含所有服务的 Provider 实例。"""

    sms: SMSServiceProtocol
    content_audit: ContentAuditProtocol
    storage: StorageProtocol
    push: PushProtocol
    ai: AIChatProtocol


# ---------------------------------------------------------------------------
# Provider 名称映射表 — 用于配置验证和错误提示
# ---------------------------------------------------------------------------

SMS_PROVIDERS = {
    "mock": "Mock 短信验证码（固定验证码 123456）",
    "console": "控制台短信（验证码输出到日志）",
    "aliyun": "阿里云短信（需要配置 AccessKey）",
}

CONTENT_AUDIT_PROVIDERS = {
    "pass": "直接通过审核（开发环境）",
    "local": "本地关键词过滤（测试环境）",
    "aliyun": "阿里云内容安全（生产环境）",
}

STORAGE_PROVIDERS = {
    "local": "本地文件系统存储（开发/测试）",
    "minio": "MinIO 对象存储（私有化部署）",
    "oss": "阿里云 OSS 对象存储（生产环境）",
}

PUSH_PROVIDERS = {
    "mock": "Mock 推送（控制台日志）",
    "jpush_free": "极光推送免费版",
    "jpush": "极光推送正式版",
}

AI_PROVIDERS = {
    "mock": "Mock AI 对话（关键词匹配）",
    "glm_free": "智谱 GLM-4-Flash 免费",
    "glm": "智谱 GLM-4-Plus",
}


# ---------------------------------------------------------------------------
# Provider 注册表构建函数
# ---------------------------------------------------------------------------

def build_provider_registry(settings: AppSettings) -> ProviderRegistry:
    """根据配置构建 Provider 注册表。

    Args:
        settings: 应用配置实例

    Returns:
        ProviderRegistry: 包含所有 Provider 实例的注册表

    Raises:
        ValueError: 当配置的 Provider 名称不存在时抛出

    Example:
        >>> settings = load_settings()
        >>> registry = build_provider_registry(settings)
        >>> result = await registry.sms.send_code("13800138000")
        >>> print(result["code"])
        '123456'
    """
    sms = create_sms_service(settings.sms_provider)
    content_audit = create_content_audit_service(settings.content_audit_provider)
    storage = create_storage_service(settings.storage_provider)
    push = create_push_service(settings.push_provider)
    ai = create_ai_chat_service(settings.ai_provider)

    return ProviderRegistry(
        sms=sms,
        content_audit=content_audit,
        storage=storage,
        push=push,
        ai=ai,
    )


# ---------------------------------------------------------------------------
# 兼容旧代码的 Provider 类导出
# 从子模块重新导出，保持向后兼容
# ---------------------------------------------------------------------------

# SMS Providers
from app.services.sms import (
    MockSMSService as MockSMSProvider,
    ConsoleSMSService as ConsoleSMSProvider,
    AliyunSMSService as AliyunSMSProvider,
)

# Content Audit Providers
from app.services.content_audit import (
    PassAudit as MockContentAuditProvider,
    LocalContentAudit as LocalContentAuditProvider,
    AliyunContentAudit as AliyunContentAuditProvider,
)

# Storage Providers
from app.services.storage import (
    LocalStorage as MockStorageProvider,
    MinIOStorage as MinIOStorageProvider,
    OSSStorage as OSSStorageProvider,
)

# Push Providers
from app.services.push import (
    JPushService,
    MockPushService as MockPushProvider,
)
JPushProvider = JPushService
JPushFreeProvider = JPushService

# AI Providers
from app.services.ai_chat import (
    GLMChatService,
    MockAIChat as MockAIProvider,
)
GLMProvider = GLMChatService
GLMFreeProvider = GLMChatService
