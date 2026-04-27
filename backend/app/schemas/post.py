"""动态广场相关请求/响应模型。

包含动态帖子创建、列表、详情、评论、共鸣、收藏等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 可见性枚举
# ---------------------------------------------------------------------------

class PostVisibility(str, Enum):
    """动态可见性枚举。

    - public: 全部公开（默认）
    - friends: 仅好友可见
    - private: 仅自己可见（私密）
    """

    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


# ---------------------------------------------------------------------------
# 用户信息响应模型
# ---------------------------------------------------------------------------

class UserInfoResponse(BaseSchema):
    """用户基本信息响应模型。

    用于动态列表中展示发布者信息（实名发布时）。
    """

    user_id: str = Field(..., description="用户ID")
    nickname: str | None = Field(None, description="用户昵称")
    avatar_url: str | None = Field(None, description="用户头像URL")


# ---------------------------------------------------------------------------
# 匿名身份响应模型
# ---------------------------------------------------------------------------

class AnonIdentityResponse(BaseSchema):
    """匿名身份响应模型。

    用于匿名动态中展示虚拟身份信息。
    """

    anon_id: str = Field(..., description="匿名身份ID")
    anon_nickname: str = Field(..., description="匿名昵称，如「月亮收集者」")
    persona_tag: str | None = Field(None, description="气质标签，如「倾听者」")
    anon_avatar_url: str | None = Field(None, description="匿名头像URL")


# ---------------------------------------------------------------------------
# 动态创建请求
# ---------------------------------------------------------------------------

class PostCreateRequest(BaseSchema):
    """创建动态请求模型。

    支持实名/匿名切换，可见范围设置。
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="动态内容，最多1000字",
        examples=["今天天气真好，心情也不错~"],
    )
    image_urls: list[str] | None = Field(
        default=None,
        max_length=9,
        description="图片URL列表，最多9张",
    )
    is_anonymous: bool = Field(
        default=False,
        description="是否匿名发布",
    )
    visibility: PostVisibility = Field(
        default=PostVisibility.PUBLIC,
        description="可见性：public/friends/private",
    )

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """验证内容不为空且去除首尾空格。"""
        if not v or not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()

    @field_validator("image_urls", mode="before")
    @classmethod
    def validate_image_urls(cls, v: list[str] | None) -> list[str] | None:
        """验证图片URL列表。"""
        if v is None:
            return None
        # 去重并去空
        urls = [url.strip() for url in v if url and url.strip()]
        if len(urls) == 0:
            return None
        if len(urls) > 9:
            raise ValueError("图片最多9张")
        return urls


# ---------------------------------------------------------------------------
# 动态更新请求
# ---------------------------------------------------------------------------

class PostUpdateRequest(BaseSchema):
    """更新动态请求模型。

    仅支持更新内容和可见性。
    """

    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="动态内容",
    )
    visibility: PostVisibility | None = Field(
        default=None,
        description="可见性",
    )

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        """验证内容不为空且去除首尾空格。"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()


# ---------------------------------------------------------------------------
# 动态响应模型
# ---------------------------------------------------------------------------

class PostResponse(BaseSchema):
    """动态响应模型。

    用于列表和详情显示。
    """

    id: str = Field(..., description="动态ID")
    content: str = Field(..., description="动态内容")
    image_urls: list[str] | None = Field(None, description="图片URL列表")
    is_anonymous: bool = Field(..., description="是否匿名发布")
    visibility: str = Field(..., description="可见性")
    like_count: int = Field(default=0, description="共鸣数")
    comment_count: int = Field(default=0, description="评论数")
    favorite_count: int = Field(default=0, description="收藏数")
    user: UserInfoResponse | None = Field(
        None,
        description="用户信息（实名发布时）",
    )
    anon_identity: AnonIdentityResponse | None = Field(
        None,
        description="匿名身份信息（匿名发布时）",
    )
    is_liked: bool = Field(
        default=False,
        description="当前用户是否已共鸣",
    )
    is_favorited: bool = Field(
        default=False,
        description="当前用户是否已收藏",
    )
    is_following: bool = Field(
        default=False,
        description="当前用户是否已关注作者",
    )
    created_at: datetime = Field(..., description="创建时间")
    # 排序分（内部使用，不暴露给前端）
    score: float | None = Field(
        None,
        description="排序分（内部使用）",
        exclude=True,
    )


class PostListResponse(BaseSchema):
    """动态列表响应模型。"""

    data: list[PostResponse] = Field(
        default_factory=list,
        description="动态列表",
    )
    pagination: dict[str, Any] = Field(..., description="分页信息")


class PostDetailResponse(BaseSchema):
    """动态详情响应模型。

    包含动态详情和评论列表。
    """

    post: PostResponse = Field(..., description="动态信息")
    comments: list["PostCommentResponse"] = Field(
        default_factory=list,
        description="评论列表",
    )


# ---------------------------------------------------------------------------
# 评论相关模型
# ---------------------------------------------------------------------------

class PostCommentCreateRequest(BaseSchema):
    """创建动态评论请求模型。"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="评论内容，最多500字",
        examples=["很棒的分享！"],
    )
    is_anonymous: bool = Field(
        default=False,
        description="是否匿名评论",
    )
    reply_to_comment_id: str | None = Field(
        default=None,
        description="回复的评论ID（支持评论回复）",
    )

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """验证内容不为空且去除首尾空格。"""
        if not v or not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()


class PostCommentResponse(BaseSchema):
    """动态评论响应模型。"""

    id: str = Field(..., description="评论ID")
    content: str = Field(..., description="评论内容")
    is_anonymous: bool = Field(..., description="是否匿名评论")
    user: UserInfoResponse | None = Field(
        None,
        description="用户信息（实名评论时）",
    )
    anon_identity: AnonIdentityResponse | None = Field(
        None,
        description="匿名身份信息（匿名评论时）",
    )
    reply_to_comment_id: str | None = Field(
        None,
        description="回复的评论ID",
    )
    reply_to_user: UserInfoResponse | None = Field(
        None,
        description="被回复用户信息",
    )
    created_at: datetime = Field(..., description="创建时间")


class PostCommentListResponse(BaseSchema):
    """动态评论列表响应模型。"""

    data: list[PostCommentResponse] = Field(
        default_factory=list,
        description="评论列表",
    )
    pagination: dict[str, Any] = Field(..., description="分页信息")


# ---------------------------------------------------------------------------
# 共鸣/收藏响应模型
# ---------------------------------------------------------------------------

class PostLikeResponse(BaseSchema):
    """共鸣（点赞）响应模型。"""

    like_count: int = Field(..., description="当前共鸣数")
    is_liked: bool = Field(..., description="是否已共鸣")
    message: str = Field(
        default="有人和你共鸣了",
        description="提示信息",
    )


class PostFavoriteResponse(BaseSchema):
    """收藏响应模型。"""

    favorite_count: int = Field(..., description="当前收藏数")
    is_favorited: bool = Field(..., description="是否已收藏")
    message: str = Field(
        default="已收藏",
        description="提示信息",
    )


class PostFollowResponse(BaseSchema):
    """悄悄关注响应模型。"""

    is_following: bool = Field(..., description="是否已关注")
    message: str = Field(
        default="已悄悄关注",
        description="提示信息",
    )


# ---------------------------------------------------------------------------
# 时间辅助函数
# ---------------------------------------------------------------------------

def format_relative_time(
    created_at: datetime,
    now: datetime | None = None,
) -> str:
    """格式化相对时间显示。

    Args:
        created_at: 创建时间
        now: 当前时间（可选）

    Returns:
        相对时间字符串，如"刚刚"、"5分钟前"
    """
    from datetime import datetime as dt, timezone

    if now is None:
        now = dt.now(timezone.utc)

    diff = now - created_at
    total_seconds = int(diff.total_seconds())
    minutes = total_seconds // 60
    hours = minutes // 60
    days = hours // 24

    if minutes < 1:
        return "刚刚"
    elif minutes < 60:
        return f"{minutes}分钟前"
    elif hours < 24:
        return f"{hours}小时前"
    elif days == 1:
        return "昨天"
    elif days < 7:
        return f"{days}天前"
    elif days < 30:
        return f"{days // 7}周前"
    else:
        return "很久了"


# ---------------------------------------------------------------------------
# 更新模型前向引用
# ---------------------------------------------------------------------------

PostDetailResponse.model_rebuild()
PostCommentListResponse.model_rebuild()
