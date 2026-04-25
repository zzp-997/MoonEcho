"""用户相关请求/响应模型。

包含用户信息、用户画像等 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 用户基础信息
# ---------------------------------------------------------------------------

class UserBase(BaseSchema):
    """用户基础信息模型。"""

    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    age_range: str | None = Field(None, description="年龄段")
    city: str | None = Field(None, description="所在城市")
    occupation: str | None = Field(None, description="职业")


class UserResponse(UserBase):
    """用户信息响应模型。"""

    id: str = Field(..., description="用户ID")
    phone: str = Field(..., description="手机号（脱敏）")
    is_minor: bool = Field(..., description="是否未成年人")
    social_energy: Decimal | None = Field(None, description="社交能量值")
    created_at: datetime = Field(..., description="注册时间")


# ---------------------------------------------------------------------------
# 用户更新
# ---------------------------------------------------------------------------

class UserUpdateRequest(BaseSchema):
    """用户信息更新请求模型。"""

    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    city: str | None = Field(None, description="所在城市")
    occupation: str | None = Field(None, description="职业")


# ---------------------------------------------------------------------------
# 用户画像
# ---------------------------------------------------------------------------

class UserTagResponse(BaseSchema):
    """用户画像标签响应模型。"""

    tag_key: str = Field(..., description="标签键")
    tag_value: str = Field(..., description="标签值")


class UserDetailResponse(UserResponse):
    """用户详细信息响应模型（含画像标签）。"""

    tags: list[UserTagResponse] = Field(default_factory=list, description="用户画像标签")
