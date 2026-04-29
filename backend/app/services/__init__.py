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
    TreeholeContentAudit,
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
from app.services.notification_service import NotificationService
from app.services.weekly_report_service import WeeklyReportService
from app.services.care_service import CareService
from app.services.care_triggers import (
    CareEventType,
    CareTriggerService,
    create_care_trigger_service,
)
from app.services.treehole_care import (
    TreeholeCareService,
    create_treehole_care_service,
)
from app.services.harassment_detector import (
    HarassmentDetector,
    HarassmentDetectionResult,
    HarassmentLevel,
    HarassmentRuleType,
    HarassmentThresholds,
    create_harassment_detector,
)
from app.services.identity_detector import (
    IdentityDetector,
    IdentityDetectionResult,
    IdentityInfoType,
    create_identity_detector,
)
from app.services.scheduler import SchedulerManager, create_scheduler_manager
from app.services.friend_service import FriendService, create_friend_service
from app.services.social_energy import (
    SocialEnergyService,
    create_social_energy_service,
)
from app.services.ai_chat_assist import (
    AIChatAssistService,
    create_ai_chat_assist_service,
)
from app.services.social_level import (
    SocialLevelService,
    create_social_level_service,
)
from app.services.ai_profile import (
    AIProfileService,
    create_ai_profile_service,
)
from app.services.user_service import (
    UserService,
    create_user_service,
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
    "TreeholeContentAudit",
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
    # 周报服务
    "WeeklyReportService",
    # 通知服务
    "NotificationService",
    # 关怀服务
    "CareService",
    # 事件驱动关怀触发
    "CareEventType",
    "CareTriggerService",
    "create_care_trigger_service",
    # 树洞联动关怀
    "TreeholeCareService",
    "create_treehole_care_service",
    # 骚扰规则引擎
    "HarassmentDetector",
    "HarassmentDetectionResult",
    "HarassmentLevel",
    "HarassmentRuleType",
    "HarassmentThresholds",
    "create_harassment_detector",
    # 脱敏提醒服务
    "IdentityDetector",
    "IdentityDetectionResult",
    "IdentityInfoType",
    "create_identity_detector",
    # 调度器
    "SchedulerManager",
    "create_scheduler_manager",
    # 好友服务
    "FriendService",
    "create_friend_service",
    # 社交能量服务
    "SocialEnergyService",
    "create_social_energy_service",
    # AI 聊天辅助服务
    "AIChatAssistService",
    "create_ai_chat_assist_service",
    # 社交暴露级别服务
    "SocialLevelService",
    "create_social_level_service",
    # AI画像标签服务
    "AIProfileService",
    "create_ai_profile_service",
    # 用户服务
    "UserService",
    "create_user_service",
]
