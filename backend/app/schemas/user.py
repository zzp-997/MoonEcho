"""用户相关请求/响应模型。

包含用户信息、用户画像、公开信息、社交级别等 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, PaginatedResponse


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

    nickname: str | None = Field(None, description="昵称（2-12字符）")
    avatar_url: str | None = Field(None, description="头像URL")
    city: str | None = Field(None, description="所在城市")
    occupation: str | None = Field(None, description="职业")

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str | None) -> str | None:
        """验证昵称长度。"""
        if v is not None:
            if len(v) < 2 or len(v) > 12:
                raise ValueError("昵称长度需要在2-12字符之间")
        return v


# ---------------------------------------------------------------------------
# 用户画像标签
# ---------------------------------------------------------------------------

class UserTagResponse(BaseSchema):
    """用户画像标签响应模型。"""

    id: str = Field(..., description="标签ID")
    tag_key: str = Field(..., description="标签键")
    tag_value: str = Field(..., description="标签值")
    created_at: datetime = Field(..., description="创建时间")


class UserTagCreateRequest(BaseSchema):
    """用户添加兴趣标签请求模型。"""

    tag_key: str = Field(default="interest", description="标签键，默认为interest")
    tag_value: str = Field(..., description="标签值")


class UserTagsResponse(BaseSchema):
    """用户兴趣标签列表响应模型。"""

    tags: list[UserTagResponse] = Field(default_factory=list, description="标签列表")
    total: int = Field(..., description="标签总数")


# ---------------------------------------------------------------------------
# 用户详细信息
# ---------------------------------------------------------------------------

class UserDetailResponse(UserResponse):
    """用户详细信息响应模型（含画像标签）。"""

    tags: list[UserTagResponse] = Field(default_factory=list, description="用户画像标签")


# ---------------------------------------------------------------------------
# 用户公开信息（查看他人）
# ---------------------------------------------------------------------------

class UserPublicInfo(BaseSchema):
    """用户公开信息模型（查看他人主页时返回）。"""

    user_id: str = Field(..., description="用户ID")
    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    profile_tags: list[ProfileTagItem] = Field(
        default_factory=list, description="AI画像标签（用户可见的部分）"
    )


class ProfileTagItem(BaseSchema):
    """AI画像标签项。"""

    tag_type: str = Field(..., description="标签类型：emotion_pattern/social_preference/interest")
    tag_name: str = Field(..., description="标签名称")
    tag_value: str = Field(..., description="标签值")
    is_visible: bool = Field(True, description="是否对他人可见")


# ---------------------------------------------------------------------------
# AI画像标签
# ---------------------------------------------------------------------------

class AIProfileTagResponse(BaseSchema):
    """AI画像标签响应模型。"""

    tags: list[ProfileTagItem] = Field(default_factory=list, description="画像标签列表")
    generated_at: datetime | None = Field(None, description="生成时间")
    message: str | None = Field(None, description="提示信息")


# ---------------------------------------------------------------------------
# 渐进式社交暴露级别
# ---------------------------------------------------------------------------

class SocialLevelProgress(BaseSchema):
    """社交暴露级别进度详情。"""

    current_level: int = Field(..., ge=1, le=6, description="当前级别（1-6）")
    level_name: str = Field(..., description="级别名称")
    description: str = Field(..., description="级别描述")
    progress_description: str = Field(..., description="进度描述")


class SocialLevelUnlockStatus(BaseSchema):
    """各级别解锁状态。"""

    level_1: bool = Field(True, description="Level 1：浏览动态广场")
    level_2: bool = Field(False, description="Level 2：点共鸣/点赞")
    level_3: bool = Field(False, description="Level 3：评论互动")
    level_4: bool = Field(False, description="Level 4：悄悄关注")
    level_5: bool = Field(False, description="Level 5：发送好友申请")
    level_6: bool = Field(False, description="Level 6：私聊")


class SocialLevelResponse(BaseSchema):
    """渐进式社交暴露级别响应模型。"""

    current_level: int = Field(..., ge=1, le=6, description="当前级别（1-6）")
    level_name: str = Field(..., description="级别名称")
    description: str = Field(..., description="级别描述")
    progress_description: str = Field(..., description="进度描述，如'还需评论1次可升级到Level 4'")
    unlock_status: SocialLevelUnlockStatus = Field(..., description="各级别解锁状态")
    next_action: str | None = Field(None, description="建议下一步行动")
    behavior_stats: "BehaviorStats" = Field(..., description="行为统计数据")


class BehaviorStats(BaseSchema):
    """用户社交行为统计数据模型。"""

    browse_count: int = Field(0, ge=0, description="浏览动态广场次数")
    like_count: int = Field(0, ge=0, description="共鸣/点赞次数")
    comment_count: int = Field(0, ge=0, description="评论次数")
    follow_count: int = Field(0, ge=0, description="悄悄关注人数")
    friend_request_count: int = Field(0, ge=0, description="好友申请次数")
    chat_count: int = Field(0, ge=0, description="私聊开启次数")


# ---------------------------------------------------------------------------
# 他人公开动态
# ---------------------------------------------------------------------------

class PublicPostItem(BaseSchema):
    """公开动态项。"""

    post_id: str = Field(..., description="动态ID")
    content: str = Field(..., description="动态内容")
    image_urls: list[str] | None = Field(None, description="图片URL列表")
    like_count: int = Field(0, description="共鸣数")
    comment_count: int = Field(0, description="评论数")
    created_at: datetime = Field(..., description="发布时间")


class PublicPostsResponse(PaginatedResponse[PublicPostItem]):
    """他人公开动态列表响应模型。"""

    pass


# ---------------------------------------------------------------------------
# 用户重要日期（本地存储）Schema
# ---------------------------------------------------------------------------

class ImportantDateItem(BaseSchema):
    """重要日期项（仅用于前端本地存储的格式建议）。"""

    date_id: str = Field(..., description="日期ID（本地生成）")
    date_type: str = Field(..., description="日期类型：birthday/anniversary/custom")
    date_value: str = Field(..., description="日期值（YYYY-MM-DD格式）")
    label: str = Field(..., description="日期标签/备注")
    is_recurring: bool = Field(True, description="是否每年重复")


class ImportantDatesSchema(BaseSchema):
    """用户重要日期Schema（格式建议，前端本地存储用）。"""

    dates: list[ImportantDateItem] = Field(
        default_factory=list,
        description="重要日期列表，最多10个"
    )

    @field_validator("dates")
    @classmethod
    def validate_dates_count(cls, v: list[ImportantDateItem]) -> list[ImportantDateItem]:
        """验证日期数量限制。"""
        if len(v) > 10:
            raise ValueError("最多只能添加10个重要日期")
        return v
