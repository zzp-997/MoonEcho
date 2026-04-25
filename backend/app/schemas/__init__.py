"""Schemas package."""

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

__all__ = [
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
]
