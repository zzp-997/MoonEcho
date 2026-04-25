"""认证相关请求/响应模型。

包含短信验证码、登录、注册、Token 刷新等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 发送验证码
# ---------------------------------------------------------------------------

class SendCodeRequest(BaseSchema):
    """发送验证码请求模型。"""

    phone: str = Field(
        ...,
        description="手机号码",
        examples=["13800138000"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式（简单校验 11 位数字）。"""
        v = v.strip()
        if not v.isdigit() or len(v) != 11:
            raise ValueError("手机号格式不正确，需为 11 位数字")
        if not v.startswith("1"):
            raise ValueError("手机号必须以 1 开头")
        return v


class SendCodeResponse(BaseSchema):
    """发送验证码响应模型。"""

    message_id: str = Field(..., description="消息ID")
    expires_in: int = Field(..., description="验证码有效期（秒）")


# ---------------------------------------------------------------------------
# 验证码登录/注册
# ---------------------------------------------------------------------------

class VerifyCodeRequest(BaseSchema):
    """验证码登录/注册请求模型。"""

    phone: str = Field(
        ...,
        description="手机号码",
        examples=["13800138000"],
    )
    code: str = Field(
        ...,
        description="验证码",
        examples=["123456"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式。"""
        v = v.strip()
        if not v.isdigit() or len(v) != 11:
            raise ValueError("手机号格式不正确，需为 11 位数字")
        if not v.startswith("1"):
            raise ValueError("手机号必须以 1 开头")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """验证验证码格式。"""
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("验证码格式不正确，需为 6 位数字")
        return v


class VerifyCodeResponse(BaseSchema):
    """验证码登录/注册响应模型。"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="access_token 有效期（秒）")
    is_new_user: bool = Field(..., description="是否新用户")
    profile_completed: bool = Field(..., description="资料是否已完善")


# ---------------------------------------------------------------------------
# 完善资料（昵称+年龄段）
# ---------------------------------------------------------------------------

AGE_RANGE_OPTIONS = [
    "18岁以下",
    "18-25",
    "26-35",
    "36-45",
    "45以上",
]


class CompleteProfileRequest(BaseSchema):
    """完善资料请求模型。"""

    nickname: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="用户昵称",
        examples=["小明"],
    )
    age_range: str = Field(
        ...,
        description=f"年龄段，可选值：{AGE_RANGE_OPTIONS}",
        examples=["18-25"],
    )

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        """验证昵称。"""
        v = v.strip()
        if not v:
            raise ValueError("昵称不能为空")
        if len(v) > 20:
            raise ValueError("昵称长度不能超过 20 个字符")
        return v

    @field_validator("age_range")
    @classmethod
    def validate_age_range(cls, v: str) -> str:
        """验证年龄段。"""
        v = v.strip()
        if v not in AGE_RANGE_OPTIONS:
            raise ValueError(f"年龄段不正确，可选值：{AGE_RANGE_OPTIONS}")
        return v


class CompleteProfileResponse(BaseSchema):
    """完善资料响应模型。"""

    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="access_token 有效期（秒）")


# ---------------------------------------------------------------------------
# Token 刷新
# ---------------------------------------------------------------------------

class RefreshTokenRequest(BaseSchema):
    """刷新令牌请求模型。"""

    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseSchema):
    """刷新令牌响应模型。"""

    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="access_token 有效期（秒）")


# ---------------------------------------------------------------------------
# 当前用户信息
# ---------------------------------------------------------------------------

class CurrentUserResponse(BaseSchema):
    """当前用户信息响应模型。"""

    id: str = Field(..., description="用户ID")
    phone: str = Field(..., description="手机号（脱敏）")
    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    age_range: str | None = Field(None, description="年龄段")
    is_minor: bool = Field(..., description="是否未成年人")
    profile_completed: bool = Field(..., description="资料是否已完善")
    created_at: datetime = Field(..., description="注册时间")
