"""用户服务模块。

提供用户资料管理、兴趣标签管理等核心业务逻辑。

主要功能：
1. 用户资料CRUD：昵称、头像、城市、职业等
2. 兴趣标签管理：添加、删除、查询
3. 用户公开信息查询（查看他人）
4. 用户公开动态查询（查看他人）

使用示例：
    service = UserService()
    user = await service.get_my_profile(user_id, db)
    await service.update_profile(user_id, update_data, db)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.post import Post
from app.models.user import User, UserTag
from app.schemas.user import (
    AIProfileTagResponse,
    BehaviorStats,
    ProfileTagItem,
    PublicPostItem,
    PublicPostsResponse,
    SocialLevelResponse,
    SocialLevelUnlockStatus,
    UserDetailResponse,
    UserPublicInfo,
    UserTagCreateRequest,
    UserTagResponse,
    UserTagsResponse,
    UserUpdateRequest,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 用户最大兴趣标签数量
MAX_USER_TAGS = 10

# 公开动态最大返回数量
MAX_PUBLIC_POSTS = 5


# ---------------------------------------------------------------------------
# 用户服务类
# ---------------------------------------------------------------------------

class UserService:
    """用户服务。

    提供：
    1. 用户资料CRUD
    2. 兴趣标签管理
    3. 用户公开信息查询
    4. 用户公开动态查询

    使用示例：
        service = UserService()
        profile = await service.get_my_profile(user_id, db)
        await service.update_profile(user_id, request, db)
    """

    def __init__(self) -> None:
        """初始化用户服务。"""
        logger.info("[UserService] 初始化完成")

    # =========================================================================
    # 用户资料CRUD
    # =========================================================================

    async def get_my_profile(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> UserDetailResponse:
        """获取自己的用户资料。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            用户详细信息响应

        Raises:
            AppError: 用户不存在
        """
        # 查询用户
        stmt = select(User).where(
            User.id == user_id,
            User.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 查询用户标签
        tag_stmt = select(UserTag).where(UserTag.user_id == user_id)
        tag_result = await db.execute(tag_stmt)
        tags = tag_result.scalars().all()

        # 构建响应
        tag_responses = [
            UserTagResponse(
                id=tag.id,
                tag_key=tag.tag_key,
                tag_value=tag.tag_value,
                created_at=tag.created_at,
            )
            for tag in tags
        ]

        # 脱敏手机号
        phone_masked = self._mask_phone(user.phone)

        return UserDetailResponse(
            id=user.id,
            phone=phone_masked,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            age_range=user.age_range,
            city=user.city,
            occupation=user.occupation,
            is_minor=user.is_minor,
            social_energy=user.social_energy,
            created_at=user.created_at,
            tags=tag_responses,
        )

    async def update_profile(
        self,
        user_id: str,
        request: UserUpdateRequest,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """更新用户资料。

        可更新字段：昵称、头像URL、城市、职业。
        年龄段不可修改（注册时确定）。

        Args:
            user_id: 用户ID
            request: 更新请求
            db: 数据库会话

        Returns:
            更新结果

        Raises:
            AppError: 用户不存在或参数无效
        """
        # 查询用户
        stmt = select(User).where(
            User.id == user_id,
            User.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 更新字段（仅更新非空字段）
        updated_fields: list[str] = []

        if request.nickname is not None:
            user.nickname = request.nickname
            updated_fields.append("nickname")

        if request.avatar_url is not None:
            user.avatar_url = request.avatar_url
            updated_fields.append("avatar_url")

        if request.city is not None:
            user.city = request.city
            updated_fields.append("city")

        if request.occupation is not None:
            user.occupation = request.occupation
            updated_fields.append("occupation")

        if updated_fields:
            await db.flush()
            logger.info(
                "[UserService] 更新用户资料: user_id=%s, fields=%s",
                user_id, updated_fields,
            )

        return {
            "updated": True,
            "updated_fields": updated_fields,
            "message": "资料更新成功",
        }

    # =========================================================================
    # 兴趣标签管理
    # =========================================================================

    async def get_my_tags(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> UserTagsResponse:
        """获取我的兴趣标签列表。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            兴趣标签列表响应
        """
        # 查询用户的兴趣标签
        stmt = select(UserTag).where(
            UserTag.user_id == user_id,
            UserTag.tag_key == "interest",
        ).order_by(UserTag.created_at.desc())

        result = await db.execute(stmt)
        tags = result.scalars().all()

        tag_responses = [
            UserTagResponse(
                id=tag.id,
                tag_key=tag.tag_key,
                tag_value=tag.tag_value,
                created_at=tag.created_at,
            )
            for tag in tags
        ]

        return UserTagsResponse(
            tags=tag_responses,
            total=len(tag_responses),
        )

    async def add_tag(
        self,
        user_id: str,
        request: UserTagCreateRequest,
        db: AsyncSession,
    ) -> UserTagResponse:
        """添加兴趣标签。

        业务规则：
        1. 每个用户最多10个兴趣标签
        2. 同一用户同一标签值不能重复

        Args:
            user_id: 用户ID
            request: 添加标签请求
            db: 数据库会话

        Returns:
            新增的标签响应

        Raises:
            AppError: 标签数量超限或重复
        """
        # 检查当前标签数量
        count_stmt = select(func.count(UserTag.id)).where(
            UserTag.user_id == user_id,
            UserTag.tag_key == "interest",
        )
        count_result = await db.execute(count_stmt)
        current_count = count_result.scalar() or 0

        if current_count >= MAX_USER_TAGS:
            raise AppError(
                code=ErrorCode.FRIEND_LIMIT_EXCEEDED,  # 使用通用限制错误码
                message=f"兴趣标签最多{MAX_USER_TAGS}个，请先删除后再添加",
                status_code=400,
            )

        # 检查是否已存在相同标签
        existing_stmt = select(UserTag).where(
            UserTag.user_id == user_id,
            UserTag.tag_key == request.tag_key,
            UserTag.tag_value == request.tag_value,
        )
        existing_result = await db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.ALREADY_FRIENDS,  # 使用通用重复错误码
                message="该标签已存在",
                status_code=400,
            )

        # 创建新标签
        new_tag = UserTag(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tag_key=request.tag_key,
            tag_value=request.tag_value,
        )
        db.add(new_tag)
        await db.flush()

        logger.info(
            "[UserService] 添加兴趣标签: user_id=%s, tag_key=%s, tag_value=%s",
            user_id, request.tag_key, request.tag_value,
        )

        return UserTagResponse(
            id=new_tag.id,
            tag_key=new_tag.tag_key,
            tag_value=new_tag.tag_value,
            created_at=new_tag.created_at,
        )

    async def delete_tag(
        self,
        user_id: str,
        tag_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """删除兴趣标签。

        Args:
            user_id: 用户ID
            tag_id: 标签ID
            db: 数据库会话

        Returns:
            删除结果

        Raises:
            AppError: 标签不存在或不属于当前用户
        """
        # 查询标签
        stmt = select(UserTag).where(
            UserTag.id == tag_id,
            UserTag.user_id == user_id,
        )
        result = await db.execute(stmt)
        tag = result.scalar_one_or_none()

        if not tag:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="标签不存在",
                status_code=404,
            )

        # 删除标签
        await db.delete(tag)

        logger.info(
            "[UserService] 删除兴趣标签: user_id=%s, tag_id=%s",
            user_id, tag_id,
        )

        return {
            "deleted": True,
            "message": "标签已删除",
        }

    # =========================================================================
    # AI画像标签
    # =========================================================================

    async def get_profile_tags(
        self,
        user_id: str,
        profile_service: Any,  # AIProfileService
        db: AsyncSession,
    ) -> AIProfileTagResponse:
        """获取AI画像标签。

        Args:
            user_id: 用户ID
            profile_service: AI画像标签服务
            db: 数据库会话

        Returns:
            AI画像标签响应
        """
        result = await profile_service.get_profile_tags(user_id, db)

        tags = [
            ProfileTagItem(
                tag_type=tag.get("tag_type", ""),
                tag_name=tag.get("tag_name", ""),
                tag_value=tag.get("tag_value", ""),
                is_visible=tag.get("is_visible", True),
            )
            for tag in result.get("tags", [])
        ]

        # 解析生成时间
        generated_at_str = result.get("generated_at")
        generated_at = None
        if generated_at_str:
            try:
                generated_at = generated_at_str  # 保持字符串格式
            except Exception:
                pass

        return AIProfileTagResponse(
            tags=tags,
            generated_at=generated_at if isinstance(generated_at, str) else None,
            message=result.get("message"),
        )

    # =========================================================================
    # 社交暴露级别
    # =========================================================================

    async def get_social_level(
        self,
        user_id: str,
        social_level_service: Any,  # SocialLevelService
        db: AsyncSession,
    ) -> SocialLevelResponse:
        """获取渐进式社交暴露级别。

        Args:
            user_id: 用户ID
            social_level_service: 社交暴露级别服务
            db: 数据库会话

        Returns:
            社交暴露级别响应
        """
        result = await social_level_service.get_social_level(user_id, db)

        stats_data = result.get("behavior_stats", {})
        unlock_data = result.get("unlock_status", {})

        return SocialLevelResponse(
            current_level=result.get("current_level", 1),
            level_name=result.get("level_name", ""),
            description=result.get("description", ""),
            progress_description=result.get("progress_description", ""),
            unlock_status=SocialLevelUnlockStatus(
                level_1=unlock_data.get("level_1", True),
                level_2=unlock_data.get("level_2", False),
                level_3=unlock_data.get("level_3", False),
                level_4=unlock_data.get("level_4", False),
                level_5=unlock_data.get("level_5", False),
                level_6=unlock_data.get("level_6", False),
            ),
            next_action=result.get("next_action"),
            behavior_stats=BehaviorStats(
                browse_count=stats_data.get("browse_count", 0),
                like_count=stats_data.get("like_count", 0),
                comment_count=stats_data.get("comment_count", 0),
                follow_count=stats_data.get("follow_count", 0),
                friend_request_count=stats_data.get("friend_request_count", 0),
                chat_count=stats_data.get("chat_count", 0),
            ),
        )

    # =========================================================================
    # 查看他人公开信息
    # =========================================================================

    async def get_user_public_info(
        self,
        user_id: str,
        target_user_id: str,
        profile_service: Any,  # AIProfileService
        db: AsyncSession,
    ) -> UserPublicInfo:
        """查看他人公开信息。

        返回对方的公开信息（昵称/头像/画像标签），
        用于好友申请时展示"Ta的公开动态"和个人主页查看他人信息。

        隐私保护：
        - 不返回私密数据（手机号、详细资料等）
        - 画像标签仅返回用户选择可见的部分

        Args:
            user_id: 当前用户ID（用于权限检查）
            target_user_id: 目标用户ID
            profile_service: AI画像标签服务
            db: 数据库会话

        Returns:
            用户公开信息

        Raises:
            AppError: 用户不存在或被拉黑
        """
        # 查询目标用户
        stmt = select(User).where(
            User.id == target_user_id,
            User.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 检查是否被目标用户拉黑
        from app.models.chat import UserBlock

        block_stmt = select(UserBlock).where(
            UserBlock.blocker_id == target_user_id,
            UserBlock.blocked_id == user_id,
        )
        block_result = await db.execute(block_stmt)
        if block_result.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.BLOCKED_BY_USER,
                message="对方已将你拉黑",
                status_code=403,
            )

        # 获取目标用户的AI画像标签（仅可见部分）
        profile_result = await profile_service.get_profile_tags(target_user_id, db)
        visible_tags = [
            ProfileTagItem(
                tag_type=tag.get("tag_type", ""),
                tag_name=tag.get("tag_name", ""),
                tag_value=tag.get("tag_value", ""),
                is_visible=tag.get("is_visible", True),
            )
            for tag in profile_result.get("tags", [])
            if tag.get("is_visible", True)  # 仅返回可见的标签
        ]

        logger.info(
            "[UserService] 查看他人公开信息: user_id=%s, target_user_id=%s",
            user_id, target_user_id,
        )

        return UserPublicInfo(
            user_id=target_user.id,
            nickname=target_user.nickname,
            avatar_url=target_user.avatar_url,
            profile_tags=visible_tags,
        )

    async def get_user_public_posts(
        self,
        user_id: str,
        target_user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 5,
    ) -> PublicPostsResponse:
        """查看他人公开动态列表。

        返回对方的最近公开动态（分页，最多5条），
        用于好友申请时展示"Ta的公开动态"。

        隐私保护：
        - 仅返回公开动态（visibility='public'）
        - 不返回匿名动态
        - 不返回被拉黑用户的动态

        Args:
            user_id: 当前用户ID（用于权限检查）
            target_user_id: 目标用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量（默认5，最大5）

        Returns:
            公开动态列表响应

        Raises:
            AppError: 用户不存在或被拉黑
        """
        # 检查权限（复用公开信息的检查逻辑）
        await self._check_public_access(user_id, target_user_id, db)

        # 限制每页数量
        page_size = min(page_size, MAX_PUBLIC_POSTS)

        # 查询目标用户的公开动态
        # 条件：
        # 1. visibility='public'
        # 2. is_anonymous=False（实名动态）
        # 3. is_active=True
        count_stmt = select(func.count(Post.id)).where(
            Post.user_id == target_user_id,
            Post.visibility == "public",
            Post.is_anonymous == False,  # noqa: E712
            Post.is_active == True,  # noqa: E712
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(Post)
            .where(
                Post.user_id == target_user_id,
                Post.visibility == "public",
                Post.is_anonymous == False,  # noqa: E712
                Post.is_active == True,  # noqa: E712
            )
            .order_by(desc(Post.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        posts = result.scalars().all()

        # 构建响应
        post_items = [
            PublicPostItem(
                post_id=post.id,
                content=post.content,
                image_urls=post.image_urls,
                like_count=post.like_count,
                comment_count=post.comment_count,
                created_at=post.created_at,
            )
            for post in posts
        ]

        return PublicPostsResponse.create(
            data=post_items,
            page=page,
            page_size=page_size,
            total=total,
        )

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    async def _check_public_access(
        self,
        user_id: str,
        target_user_id: str,
        db: AsyncSession,
    ) -> None:
        """检查是否有权限查看目标用户的公开信息。

        Args:
            user_id: 当前用户ID
            target_user_id: 目标用户ID
            db: 数据库会话

        Raises:
            AppError: 用户不存在或被拉黑
        """
        # 查询目标用户
        stmt = select(User).where(
            User.id == target_user_id,
            User.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 检查是否被目标用户拉黑
        from app.models.chat import UserBlock

        block_stmt = select(UserBlock).where(
            UserBlock.blocker_id == target_user_id,
            UserBlock.blocked_id == user_id,
        )
        block_result = await db.execute(block_stmt)
        if block_result.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.BLOCKED_BY_USER,
                message="对方已将你拉黑",
                status_code=403,
            )

    def _mask_phone(self, phone: str) -> str:
        """脱敏手机号。

        Args:
            phone: 原始手机号（可能是加密后的长字符串）

        Returns:
            脱敏后的手机号
        """
        # 加密后的手机号很长，直接返回占位符
        if len(phone) > 20:
            return "***已加密***"

        # 普通手机号脱敏
        if len(phone) >= 11:
            return f"{phone[:3]}****{phone[-4:]}"
        return "***"


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_user_service() -> UserService:
    """创建用户服务实例。

    Returns:
        UserService 实例
    """
    return UserService()