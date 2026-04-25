"""Services package — 服务层统一导出。

从各子模块导出 Protocol、实现类、工厂函数，
以及聚合的 ProviderRegistry 和 build_provider_registry。
"""

from app.services.ai_chat import (
    AIChatProtocol,
    CRISIS_SAFETY_RESPONSES,
    GLMChatService,
    MockAIChat,
    PERSONALITY_GREETINGS,
    PERSONALITY_RESPONSES,
    create_ai_chat_service,
)
from app.services.auth_service import AuthService
from app.services.content_audit import (
    AliyunContentAudit,
    ContentAuditProtocol,
    LocalContentAudit,
    PassAudit,
    create_content_audit_service,
)
from app.services.crypto import decrypt_phone, encrypt_phone, phone_hash
from app.services.image import (
    ImageServiceProtocol,
    PillowImageService,
    create_image_service,
)
from app.services.push import (
    JPushService,
    MockPushService,
    PushProtocol,
    create_push_service,
)
from app.services.sms import (
    AliyunSMSService,
    ConsoleSMSService,
    MockSMSService,
    SMSServiceProtocol,
    create_sms_service,
)
from app.services.storage import (
    LocalStorage,
    MinIOStorage,
    OSSStorage,
    StorageProtocol,
    create_storage_service,
)

__all__ = [
    # SMS 短信服务
    "SMSServiceProtocol",
    "MockSMSService",
    "ConsoleSMSService",
    "AliyunSMSService",
    "create_sms_service",
    # 认证服务
    "AuthService",
    # 加密服务
    "encrypt_phone",
    "decrypt_phone",
    "phone_hash",
    # 内容审核服务
    "ContentAuditProtocol",
    "PassAudit",
    "LocalContentAudit",
    "AliyunContentAudit",
    "create_content_audit_service",
    # 文件存储服务
    "StorageProtocol",
    "LocalStorage",
    "MinIOStorage",
    "OSSStorage",
    "create_storage_service",
    # 推送服务
    "PushProtocol",
    "MockPushService",
    "JPushService",
    "create_push_service",
    # AI 对话服务
    "AIChatProtocol",
    "MockAIChat",
    "GLMChatService",
    "PERSONALITY_RESPONSES",
    "PERSONALITY_GREETINGS",
    "CRISIS_SAFETY_RESPONSES",
    "create_ai_chat_service",
    # 图片处理服务
    "ImageServiceProtocol",
    "PillowImageService",
    "create_image_service",
]
