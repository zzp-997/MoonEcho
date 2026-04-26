"""Schemas package."""

from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ConversationListItem,
    ConversationListResponse,
    GreetingRequest,
    GreetingResponse,
    PersonaInfo,
    PersonaListResponse,
    QuotaResponse,
)
from app.schemas.auth import (
    AGE_RANGE_OPTIONS,
    CompleteProfileRequest,
    CompleteProfileResponse,
    CurrentUserResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    SendCodeRequest,
    SendCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from app.schemas.user import (
    UserBase,
    UserDetailResponse,
    UserResponse,
    UserTagResponse,
    UserUpdateRequest,
)
from app.schemas.notification import (
    DEFAULT_DISABLED_TYPES,
    DEFAULT_ENABLED_TYPES,
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdateRequest,
    NotificationType,
    PushFrequencyConfig,
    PushRequest,
    PushResult,
)
from app.schemas.weekly_report import (
    EmptyWeeklyReportResponse,
    WeeklyReportGenerateRequest,
    WeeklyReportHistoryResponse,
    WeeklyReportResponse,
)

__all__ = [
    # AI 对话相关
    "ChatRequest",
    "ChatResponse",
    "ConversationListItem",
    "ConversationListResponse",
    "GreetingRequest",
    "GreetingResponse",
    "PersonaInfo",
    "PersonaListResponse",
    "QuotaResponse",
    # 认证相关
    "SendCodeRequest",
    "SendCodeResponse",
    "VerifyCodeRequest",
    "VerifyCodeResponse",
    "CompleteProfileRequest",
    "CompleteProfileResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "CurrentUserResponse",
    "AGE_RANGE_OPTIONS",
    # 用户相关
    "UserBase",
    "UserResponse",
    "UserUpdateRequest",
    "UserTagResponse",
    "UserDetailResponse",
    # 周报相关
    "EmptyWeeklyReportResponse",
    "WeeklyReportGenerateRequest",
    "WeeklyReportHistoryResponse",
    "WeeklyReportResponse",
    # 通知相关
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationSettingResponse",
    "NotificationSettingUpdateRequest",
    "NotificationType",
    "PushRequest",
    "PushResult",
    "PushFrequencyConfig",
    "DEFAULT_ENABLED_TYPES",
    "DEFAULT_DISABLED_TYPES",
]
