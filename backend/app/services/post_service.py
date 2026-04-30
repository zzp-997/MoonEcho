"""动态广场核心服务。

实现动态帖子 CRUD、信息流排序算法、共鸣/评论/收藏功能。

信息流排序算法（冷启动阶段）：
- 排序分 = 时间新鲜度 × 0.4 + 互动热度 × 0.3 + 内容完整度 × 0.2 + 随机因子 × 0.1
- 时间新鲜度：1/(发布小时数+1)，上限24小时
- 互动热度：(共鸣×2 + 评论×3 + 收藏×1.5) / 活跃用户数
- 内容完整度：有图片+0.3，文字>20字+0.2
- 随机因子：确定性伪随机，基于用户ID+帖子ID+日期，确保分页稳定
"""

from __future__ import annotations

import hashlib
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.post import Post, PostComment, PostLike, PostFavorite, PostFollow
from app.models.user import User, AnonymousIdentity, UserAnonMapping
from app.models.chat import Friendship
from app.schemas.post import (
    AnonIdentityResponse,
    PostCommentCreateRequest,
    PostCommentResponse,
    PostCreateRequest,
    PostFavoriteResponse,
    PostFollowResponse,
    PostLikeResponse,
    PostListResponse,
    PostResponse,
    PostUpdateRequest,
    UserInfoResponse,
    format_relative_time,
    PostVisibility,
)
from app.services.anonymous_identity import AnonymousIdentityService
from app.services.crypto import encrypt_data
from app.services.content_audit import (
    ContentAuditProtocol,
    AuditResult,
    create_content_audit_service,
    get_audit_feedback,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 信息流排序算法参数
# ---------------------------------------------------------------------------

# 权重配置（冷启动阶段）
WEIGHT_TIME_FRESHNESS = 0.4      # 时间新鲜度权重
WEIGHT_INTERACTION_HEAT = 0.3    # 互动热度权重
WEIGHT_CONTENT_COMPLETENESS = 0.2  # 内容完整度权重
WEIGHT_RANDOM_FACTOR = 0.1       # 随机因子权重

# 时间参数
DECAY_HOURS_LIMIT = 24           # 时间衰减上限（小时）

# 活跃用户数基数（用于归一化互动热度）
ACTIVE_USER_BASE = 100


# ---------------------------------------------------------------------------
# 动态广场核心服务
# ---------------------------------------------------------------------------

class PostService:
    """动态广场核心服务。

    实现：
    1. 动态帖子 CRUD
    2. 信息流排序算法
    3. 共鸣/评论/收藏功能
    4. 悄悄关注功能

    使用示例：
        service = PostService(settings, redis)
        result = await service.list_posts(user_id, db, page=1, page_size=20)
    """

    # 场景常量
    SCENE_SQUARE = "square"

    def __init__(
        self,
        settings: Any,
        redis: Any,
        anon_identity_service: AnonymousIdentityService | None = None,
        content_audit_provider: str = "local",
    ) -> None:
        """初始化动态广场服务。

        Args:
            settings: 应用配置
            redis: Redis 客户端
            anon_identity_service: 匿名身份服务（可选）
            content_audit_provider: 内容审核服务提供者（默认 local）
        """
        self._settings = settings
        self._redis = redis
        self._anon_identity_service = anon_identity_service
        self._content_audit_provider = content_audit_provider
        self._content_audit: ContentAuditProtocol | None = None

        logger.info("[PostService] 初始化完成，内容审核服务: %s", content_audit_provider)

    def _get_anon_identity_service(self) -> AnonymousIdentityService:
        """获取匿名身份服务实例。"""
        if self._anon_identity_service is None:
            self._anon_identity_service = AnonymousIdentityService(self._settings)
        return self._anon_identity_service

    def _get_content_audit(self) -> ContentAuditProtocol:
        """获取内容审核服务实例。"""
        if self._content_audit is None:
            self._content_audit = create_content_audit_service(self._content_audit_provider)
        return self._content_audit

    def _compute_user_id_hash(self, user_id: str) -> str:
        """计算用户ID的哈希值（加盐）。

        用于快速查询映射关系，不暴露真实用户ID。

        Args:
            user_id: 用户ID

        Returns:
            SHA-256 哈希值
        """
        encryption_key = self._settings.ENCRYPTION_KEY
        data = f"{encryption_key}:{user_id}"
        return hashlib.sha256(data.encode()).hexdigest()

    # =========================================================================
    # 信息流排序算法
    # =========================================================================

    def _calculate_time_freshness(
        self,
        created_at: datetime,
        now: datetime | None = None,
    ) -> float:
        """计算时间新鲜度。

        公式：1 / (发布小时数 + 1)，上限24小时

        Args:
            created_at: 创建时间
            now: 当前时间

        Returns:
            时间新鲜度 (0.0 - 1.0)
        """
        if now is None:
            now = datetime.now(timezone.utc)

        hours_elapsed = (now - created_at).total_seconds() / 3600
        hours_for_calc = min(hours_elapsed, DECAY_HOURS_LIMIT)
        return 1.0 / (hours_for_calc + 1)

    def _calculate_interaction_heat(
        self,
        like_count: int,
        comment_count: int,
        favorite_count: int,
        active_user_count: int = ACTIVE_USER_BASE,
    ) -> float:
        """计算互动热度。

        公式：(共鸣×2 + 评论×3 + 收藏×1.5) / 活跃用户数（归一化到 0-1）

        Args:
            like_count: 共鸣数
            comment_count: 评论数
            favorite_count: 收藏数
            active_user_count: 活跃用户数（归一化基数）

        Returns:
            互动热度 (0.0 - 1.0)
        """
        if active_user_count <= 0:
            active_user_count = ACTIVE_USER_BASE

        score = (like_count * 2 + comment_count * 3 + favorite_count * 1.5) / active_user_count
        return min(score, 1.0)

    def _calculate_content_completeness(
        self,
        content: str,
        image_urls: list[str] | None,
    ) -> float:
        """计算内容完整度。

        规则：
        - 有图片 +0.3
        - 文字超过20字 +0.2
        - 基础分 0.5

        Args:
            content: 动态内容
            image_urls: 图片URL列表

        Returns:
            内容完整度 (0.5 - 1.0)
        """
        score = 0.5  # 基础分

        # 有图片加分
        if image_urls and len(image_urls) > 0:
            score += 0.3

        # 文字超过20字加分
        if len(content) > 20:
            score += 0.2

        return min(score, 1.0)

    def _calculate_random_factor(
        self,
        post_id: str,
        user_id: str,
        seed_date: datetime | None = None,
    ) -> float:
        """计算确定性伪随机因子。

        使用用户 ID + 帖子 ID 的哈希值作为种子，确保同一用户看到的排序相对稳定，
        避免分页时出现重复或遗漏。

        Args:
            post_id: 帖子 ID
            user_id: 当前用户 ID
            seed_date: 种子日期（可选，用于每天变化）

        Returns:
            伪随机因子 (0.0 - 1.0)
        """
        # 使用用户 ID + 帖子 ID + 日期作为种子
        if seed_date is None:
            seed_date = datetime.now(timezone.utc)

        # 日期部分变化，确保每天排序略有不同但同一天内稳定
        date_str = seed_date.strftime("%Y-%m-%d")
        seed_str = f"{user_id}:{post_id}:{date_str}"

        # 使用哈希计算确定性随机值
        hash_value = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        # 映射到 0-1 范围
        return hash_value / 0xFFFFFFFF

    def calculate_post_score(
        self,
        post: Post,
        user_id: str,
        now: datetime | None = None,
    ) -> float:
        """计算动态排序分。

        排序分 = 时间新鲜度 × 0.4 + 互动热度 × 0.3 + 内容完整度 × 0.2 + 随机因子 × 0.1

        Args:
            post: 动态对象
            user_id: 用户 ID（用于生成确定性随机因子）
            now: 当前时间（可选）

        Returns:
            排序分
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # 计算各因子
        time_freshness = self._calculate_time_freshness(post.created_at, now)
        interaction_heat = self._calculate_interaction_heat(
            post.like_count, post.comment_count, post.favorite_count
        )
        content_completeness = self._calculate_content_completeness(
            post.content, post.image_urls
        )
        # 使用确定性伪随机因子，确保分页稳定
        random_factor = self._calculate_random_factor(post.id, user_id, now)

        # 计算排序分
        score = (
            time_freshness * WEIGHT_TIME_FRESHNESS +
            interaction_heat * WEIGHT_INTERACTION_HEAT +
            content_completeness * WEIGHT_CONTENT_COMPLETENESS +
            random_factor * WEIGHT_RANDOM_FACTOR
        )

        return round(score, 4)

    # =========================================================================
    # 动态帖子 CRUD
    # =========================================================================

    async def list_posts(
        self,
        current_user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        visibility: str | None = None,
    ) -> PostListResponse:
        """获取动态列表。

        使用信息流排序算法，支持可见性筛选。
        优化：批量查询共鸣/收藏/关注状态，避免 N+1 问题。

        Args:
            current_user_id: 当前用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量
            visibility: 可见性筛选（可选）

        Returns:
            动态列表响应
        """
        now = datetime.now(timezone.utc)

        # 构建查询条件
        conditions = [
            Post.deleted_at.is_(None),
        ]

        # 可见性筛选：只显示公开的动态
        # TODO: 后续实现好友可见逻辑
        conditions.append(Post.visibility == PostVisibility.PUBLIC.value)

        # 查询帖子
        stmt = (
            select(Post)
            .where(and_(*conditions))
            .order_by(desc(Post.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size + 1)  # 多查一条判断是否有更多
        )

        result = await db.execute(stmt)
        posts = result.scalars().all()

        # 查询总数
        count_stmt = select(func.count(Post.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # ========== 批量查询优化，避免 N+1 问题 ==========
        post_ids = [p.id for p in posts]
        user_ids = [p.user_id for p in posts if not p.is_anonymous]
        anon_ids = [p.anon_identity_id for p in posts if p.anon_identity_id]

        # 批量查询共鸣状态
        liked_post_ids: set[str] = set()
        if post_ids:
            like_stmt = select(PostLike.post_id).where(
                PostLike.post_id.in_(post_ids),
                PostLike.user_id == current_user_id,
            )
            like_result = await db.execute(like_stmt)
            liked_post_ids = {row[0] for row in like_result.fetchall()}

        # 批量查询收藏状态
        favorited_post_ids: set[str] = set()
        if post_ids:
            fav_stmt = select(PostFavorite.post_id).where(
                PostFavorite.post_id.in_(post_ids),
                PostFavorite.user_id == current_user_id,
            )
            fav_result = await db.execute(fav_stmt)
            favorited_post_ids = {row[0] for row in fav_result.fetchall()}

        # 批量查询关注状态（实名动态的作者）
        following_user_ids: set[str] = set()
        real_user_ids = [p.user_id for p in posts if not p.is_anonymous and p.user_id != current_user_id]
        if real_user_ids:
            follow_stmt = select(PostFollow.following_id).where(
                PostFollow.follower_id == current_user_id,
                PostFollow.following_id.in_(real_user_ids),
            )
            follow_result = await db.execute(follow_stmt)
            following_user_ids = {row[0] for row in follow_result.fetchall()}

        # 批量查询用户信息
        users_map: dict[str, User] = {}
        if user_ids:
            user_stmt = select(User).where(User.id.in_(set(user_ids)))
            user_result = await db.execute(user_stmt)
            for user in user_result.scalars().all():
                users_map[user.id] = user

        # 批量查询匿名身份
        anon_map: dict[str, AnonymousIdentity] = {}
        if anon_ids:
            anon_stmt = select(AnonymousIdentity).where(AnonymousIdentity.id.in_(set(anon_ids)))
            anon_result = await db.execute(anon_stmt)
            for anon in anon_result.scalars().all():
                anon_map[anon.id] = anon

        # 计算排序分并排序
        posts_with_score = []
        for post in posts:
            score = self.calculate_post_score(post, current_user_id, now)
            posts_with_score.append((post, score))

        # 按排序分降序排序
        posts_with_score.sort(key=lambda x: x[1], reverse=True)

        # 构建响应（使用预查询的数据）
        post_responses = []
        for post, score in posts_with_score[:page_size]:
            response = self._build_post_response_optimized(
                post=post,
                current_user_id=current_user_id,
                now=now,
                liked_post_ids=liked_post_ids,
                favorited_post_ids=favorited_post_ids,
                following_user_ids=following_user_ids,
                users_map=users_map,
                anon_map=anon_map,
            )
            response.score = score
            post_responses.append(response)

        # 构建分页信息
        pagination = {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "hasMore": len(posts) > page_size,
        }

        return PostListResponse(
            data=post_responses,
            pagination=pagination,
        )

    async def get_post(
        self,
        post_id: str,
        current_user_id: str,
        db: AsyncSession,
    ) -> PostResponse:
        """获取动态详情。

        Args:
            post_id: 动态ID
            current_user_id: 当前用户ID
            db: 数据库会话

        Returns:
            动态详情响应

        Raises:
            AppError: 动态不存在
        """
        # 查询动态
        stmt = select(Post).where(
            Post.id == post_id,
            Post.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.POST_NOT_FOUND,
                message="动态不存在",
                status_code=404,
            )

        # 检查可见性权限
        await self._check_visibility(post, current_user_id, db)

        now = datetime.now(timezone.utc)
        return await self._build_post_response(post, current_user_id, now, db)

    async def create_post(
        self,
        user_id: str,
        request: PostCreateRequest,
        db: AsyncSession,
    ) -> PostResponse:
        """创建动态。

        支持实名/匿名切换，匿名时生成虚拟身份。
        发布前进行内容安全审核。

        Args:
            user_id: 用户ID
            request: 创建请求
            db: 数据库会话

        Returns:
            动态响应

        Raises:
            AppError: 内容审核不通过
        """
        # 内容安全审核
        if request.content:
            audit_result = await self._get_content_audit().check(request.content)
            if not audit_result.get("pass", True):
                # 审核不通过，返回温和提示
                feedback = audit_result.get("feedback") or get_audit_feedback(
                    AuditResult.BLOCK,
                    audit_result.get("labels", [None])[0] if audit_result.get("labels") else None,
                )
                raise AppError(
                    code=ErrorCode.CONTENT_AUDIT_FAILED,
                    message=feedback,
                    status_code=400,
                )

        anon_identity = None
        anon_identity_id = None

        # 如果是匿名发布，获取或创建匿名身份
        if request.is_anonymous:
            anon_service = self._get_anon_identity_service()
            anon_identity = await self._get_or_create_square_identity(
                user_id, db
            )
            anon_identity_id = anon_identity.id

        # 创建动态
        post = Post(
            id=str(uuid.uuid4()),
            user_id=user_id,
            anon_identity_id=anon_identity_id,
            content=request.content,
            image_urls=request.image_urls,
            is_anonymous=request.is_anonymous,
            visibility=request.visibility.value,
        )
        db.add(post)
        await db.flush()

        now = datetime.now(timezone.utc)
        logger.info(
            "[PostService] 创建动态，动态: %s，用户: %s，匿名: %s",
            post.id, user_id, request.is_anonymous
        )

        return await self._build_post_response(post, user_id, now, db)

    async def update_post(
        self,
        post_id: str,
        user_id: str,
        request: PostUpdateRequest,
        db: AsyncSession,
    ) -> PostResponse:
        """更新动态。

        仅限自己的动态。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            request: 更新请求
            db: 数据库会话

        Returns:
            动态响应

        Raises:
            AppError: 动态不存在或无权限
        """
        # 查询动态
        stmt = select(Post).where(
            Post.id == post_id,
            Post.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.POST_NOT_FOUND,
                message="动态不存在",
                status_code=404,
            )

        # 验证所有者
        if post.user_id != user_id:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权限修改此动态",
                status_code=403,
            )

        # 更新字段
        if request.content is not None:
            post.content = request.content
        if request.visibility is not None:
            post.visibility = request.visibility.value

        post.updated_at = datetime.now(timezone.utc)
        await db.flush()

        now = datetime.now(timezone.utc)
        logger.info(
            "[PostService] 更新动态，动态: %s，用户: %s",
            post_id, user_id
        )

        return await self._build_post_response(post, user_id, now, db)

    async def delete_post(
        self,
        post_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> bool:
        """删除动态（软删除）。

        仅限自己的动态。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            是否成功

        Raises:
            AppError: 动态不存在或无权限
        """
        # 查询动态
        stmt = select(Post).where(
            Post.id == post_id,
            Post.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.POST_NOT_FOUND,
                message="动态不存在",
                status_code=404,
            )

        # 验证所有者
        if post.user_id != user_id:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权限删除此动态",
                status_code=403,
            )

        # 软删除
        post.deleted_at = datetime.now(timezone.utc)

        logger.info(
            "[PostService] 删除动态，动态: %s，用户: %s",
            post_id, user_id
        )

        return True

    # =========================================================================
    # 共鸣功能
    # =========================================================================

    async def like_post(
        self,
        post_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> PostLikeResponse:
        """共鸣（点赞）动态。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            共鸣响应

        Raises:
            AppError: 动态不存在
        """
        # 检查动态是否存在
        post = await self._get_post_or_raise(post_id, db)

        # 检查是否已共鸣
        check_stmt = select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id,
        )
        check_result = await db.execute(check_stmt)
        existing = check_result.scalar_one_or_none()

        if existing:
            # 已共鸣，返回当前状态
            return PostLikeResponse(
                like_count=post.like_count,
                is_liked=True,
                message="你已经共鸣过了",
            )

        # 创建共鸣记录
        like = PostLike(
            id=str(uuid.uuid4()),
            post_id=post_id,
            user_id=user_id,
        )
        db.add(like)

        # 更新动态共鸣数
        post.like_count += 1

        logger.info(
            "[PostService] 创建共鸣，动态: %s，用户: %s",
            post_id, user_id
        )

        return PostLikeResponse(
            like_count=post.like_count,
            is_liked=True,
            message="有人和你共鸣了",
        )

    async def unlike_post(
        self,
        post_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> PostLikeResponse:
        """取消共鸣。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            共鸣响应

        Raises:
            AppError: 动态不存在
        """
        # 检查动态是否存在
        post = await self._get_post_or_raise(post_id, db)

        # 检查是否已共鸣
        check_stmt = select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id,
        )
        check_result = await db.execute(check_stmt)
        existing = check_result.scalar_one_or_none()

        if not existing:
            # 未共鸣，返回当前状态
            return PostLikeResponse(
                like_count=post.like_count,
                is_liked=False,
                message="你还没有共鸣",
            )

        # 删除共鸣记录
        await db.delete(existing)

        # 更新动态共鸣数
        if post.like_count > 0:
            post.like_count -= 1

        logger.info(
            "[PostService] 取消共鸣，动态: %s，用户: %s",
            post_id, user_id
        )

        return PostLikeResponse(
            like_count=post.like_count,
            is_liked=False,
            message="已取消共鸣",
        )

    # =========================================================================
    # 收藏功能
    # =========================================================================

    async def favorite_post(
        self,
        post_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> PostFavoriteResponse:
        """收藏动态。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            收藏响应

        Raises:
            AppError: 动态不存在
        """
        # 检查动态是否存在
        post = await self._get_post_or_raise(post_id, db)

        # 检查是否已收藏
        check_stmt = select(PostFavorite).where(
            PostFavorite.post_id == post_id,
            PostFavorite.user_id == user_id,
        )
        check_result = await db.execute(check_stmt)
        existing = check_result.scalar_one_or_none()

        if existing:
            # 已收藏，返回当前状态
            return PostFavoriteResponse(
                favorite_count=post.favorite_count,
                is_favorited=True,
                message="你已经收藏过了",
            )

        # 创建收藏记录
        favorite = PostFavorite(
            id=str(uuid.uuid4()),
            post_id=post_id,
            user_id=user_id,
        )
        db.add(favorite)

        # 更新动态收藏数
        post.favorite_count += 1

        logger.info(
            "[PostService] 收藏动态，动态: %s，用户: %s",
            post_id, user_id
        )

        return PostFavoriteResponse(
            favorite_count=post.favorite_count,
            is_favorited=True,
            message="已收藏",
        )

    async def unfavorite_post(
        self,
        post_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> PostFavoriteResponse:
        """取消收藏。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            收藏响应

        Raises:
            AppError: 动态不存在
        """
        # 检查动态是否存在
        post = await self._get_post_or_raise(post_id, db)

        # 检查是否已收藏
        check_stmt = select(PostFavorite).where(
            PostFavorite.post_id == post_id,
            PostFavorite.user_id == user_id,
        )
        check_result = await db.execute(check_stmt)
        existing = check_result.scalar_one_or_none()

        if not existing:
            # 未收藏，返回当前状态
            return PostFavoriteResponse(
                favorite_count=post.favorite_count,
                is_favorited=False,
                message="你还没有收藏",
            )

        # 删除收藏记录
        await db.delete(existing)

        # 更新动态收藏数
        if post.favorite_count > 0:
            post.favorite_count -= 1

        logger.info(
            "[PostService] 取消收藏，动态: %s，用户: %s",
            post_id, user_id
        )

        return PostFavoriteResponse(
            favorite_count=post.favorite_count,
            is_favorited=False,
            message="已取消收藏",
        )

    # =========================================================================
    # 悄悄关注功能
    # =========================================================================

    async def follow_author(
        self,
        post_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> PostFollowResponse:
        """悄悄关注动态作者。

        仅实名动态才能关注，匿名动态不可被关注。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            关注响应

        Raises:
            AppError: 动态不存在或匿名动态
        """
        # 检查动态是否存在
        post = await self._get_post_or_raise(post_id, db)

        # 匿名动态不可被关注
        if post.is_anonymous:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="匿名动态不能被关注",
                status_code=403,
            )

        # 不能关注自己
        if post.user_id == user_id:
            raise AppError(
                code=ErrorCode.CANNOT_ADD_SELF,
                message="不能关注自己",
                status_code=400,
            )

        # 检查是否已关注
        check_stmt = select(PostFollow).where(
            PostFollow.follower_id == user_id,
            PostFollow.following_id == post.user_id,
        )
        check_result = await db.execute(check_stmt)
        existing = check_result.scalar_one_or_none()

        if existing:
            # 已关注，返回当前状态
            return PostFollowResponse(
                is_following=True,
                message="你已经悄悄关注了TA",
            )

        # 创建关注记录
        follow = PostFollow(
            id=str(uuid.uuid4()),
            post_id=post_id,
            follower_id=user_id,
            following_id=post.user_id,
        )
        db.add(follow)

        logger.info(
            "[PostService] 悄悄关注，动态: %s，关注者: %s，被关注者: %s",
            post_id, user_id, post.user_id
        )

        return PostFollowResponse(
            is_following=True,
            message="已悄悄关注",
        )

    async def unfollow_author(
        self,
        post_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> PostFollowResponse:
        """取消悄悄关注。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            关注响应

        Raises:
            AppError: 动态不存在
        """
        # 检查动态是否存在
        post = await self._get_post_or_raise(post_id, db)

        # 检查是否已关注
        check_stmt = select(PostFollow).where(
            PostFollow.follower_id == user_id,
            PostFollow.following_id == post.user_id,
        )
        check_result = await db.execute(check_stmt)
        existing = check_result.scalar_one_or_none()

        if not existing:
            # 未关注，返回当前状态
            return PostFollowResponse(
                is_following=False,
                message="你还没有关注TA",
            )

        # 删除关注记录
        await db.delete(existing)

        logger.info(
            "[PostService] 取消悄悄关注，动态: %s，关注者: %s",
            post_id, user_id
        )

        return PostFollowResponse(
            is_following=False,
            message="已取消关注",
        )

    # =========================================================================
    # 评论功能
    # =========================================================================

    async def list_comments(
        self,
        post_id: str,
        current_user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> list[PostCommentResponse]:
        """获取评论列表。

        Args:
            post_id: 动态ID
            current_user_id: 当前用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            评论列表

        Raises:
            AppError: 动态不存在
        """
        # 检查动态是否存在
        await self._get_post_or_raise(post_id, db)

        # 查询评论
        stmt = (
            select(PostComment)
            .where(
                PostComment.post_id == post_id,
                PostComment.deleted_at.is_(None),
            )
            .order_by(PostComment.created_at)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        comments = result.scalars().all()

        now = datetime.now(timezone.utc)
        comment_responses = []

        for comment in comments:
            response = await self._build_comment_response(comment, now, db)
            comment_responses.append(response)

        return comment_responses

    async def create_comment(
        self,
        post_id: str,
        user_id: str,
        request: PostCommentCreateRequest,
        db: AsyncSession,
    ) -> PostCommentResponse:
        """创建评论。

        发布前进行内容安全审核。

        Args:
            post_id: 动态ID
            user_id: 用户ID
            request: 创建请求
            db: 数据库会话

        Returns:
            评论响应

        Raises:
            AppError: 动态不存在或内容审核不通过
        """
        # 检查动态是否存在
        post = await self._get_post_or_raise(post_id, db)

        # 内容安全审核
        if request.content:
            audit_result = await self._get_content_audit().check(request.content)
            if not audit_result.get("pass", True):
                # 审核不通过，返回温和提示
                feedback = audit_result.get("feedback") or get_audit_feedback(
                    AuditResult.BLOCK,
                    audit_result.get("labels", [None])[0] if audit_result.get("labels") else None,
                )
                raise AppError(
                    code=ErrorCode.CONTENT_AUDIT_FAILED,
                    message=feedback,
                    status_code=400,
                )

        anon_identity = None
        anon_identity_id = None

        # 如果是匿名评论，获取或创建匿名身份
        if request.is_anonymous:
            anon_identity = await self._get_or_create_square_identity(
                user_id, db
            )
            anon_identity_id = anon_identity.id

        # 验证回复评论是否存在
        if request.reply_to_comment_id:
            reply_stmt = select(PostComment).where(
                PostComment.id == request.reply_to_comment_id,
                PostComment.deleted_at.is_(None),
            )
            reply_result = await db.execute(reply_stmt)
            reply_comment = reply_result.scalar_one_or_none()

            if not reply_comment:
                raise AppError(
                    code=ErrorCode.POST_NOT_FOUND,
                    message="回复的评论不存在",
                    status_code=404,
                )

        # 创建评论
        comment = PostComment(
            id=str(uuid.uuid4()),
            post_id=post_id,
            user_id=user_id,
            anon_identity_id=anon_identity_id,
            content=request.content,
            is_anonymous=request.is_anonymous,
            reply_to_comment_id=request.reply_to_comment_id,
        )
        db.add(comment)

        # 更新动态评论数
        post.comment_count += 1

        now = datetime.now(timezone.utc)
        logger.info(
            "[PostService] 创建评论，动态: %s，用户: %s，匿名: %s",
            post_id, user_id, request.is_anonymous
        )

        return await self._build_comment_response(comment, now, db)

    # =========================================================================
    # 辅助方法
    # =========================================================================

    async def _get_post_or_raise(
        self,
        post_id: str,
        db: AsyncSession,
    ) -> Post:
        """获取动态或抛出异常。

        Args:
            post_id: 动态ID
            db: 数据库会话

        Returns:
            Post 对象

        Raises:
            AppError: 动态不存在
        """
        stmt = select(Post).where(
            Post.id == post_id,
            Post.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.POST_NOT_FOUND,
                message="动态不存在",
                status_code=404,
            )

        return post

    async def _check_visibility(
        self,
        post: Post,
        user_id: str,
        db: AsyncSession,
    ) -> None:
        """检查动态可见性权限。

        Args:
            post: 动态对象
            user_id: 用户ID
            db: 数据库会话

        Raises:
            AppError: 无权限访问
        """
        # 自己的动态始终可见
        if post.user_id == user_id:
            return

        # 公开动态可见
        if post.visibility == PostVisibility.PUBLIC.value:
            return

        # 仅好友可见
        if post.visibility == PostVisibility.FRIENDS.value:
            # 检查是否是好友
            friend_stmt = select(Friendship).where(
                or_(
                    and_(
                        Friendship.initiator_id == user_id,
                        Friendship.recipient_id == post.user_id,
                        Friendship.status == "accepted",
                    ),
                    and_(
                        Friendship.initiator_id == post.user_id,
                        Friendship.recipient_id == user_id,
                        Friendship.status == "accepted",
                    ),
                ),
            )
            friend_result = await db.execute(friend_stmt)
            is_friend = friend_result.scalar_one_or_none() is not None

            if not is_friend:
                raise AppError(
                    code=ErrorCode.POST_VISIBILITY_DENIED,
                    message="该动态仅好友可见",
                    status_code=403,
                )
            return

        # 仅自己可见
        if post.visibility == PostVisibility.PRIVATE.value:
            raise AppError(
                code=ErrorCode.POST_VISIBILITY_DENIED,
                message="该动态为私密内容",
                status_code=403,
            )

    async def _get_or_create_square_identity(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> AnonymousIdentity:
        """获取或创建用户在动态广场的匿名身份。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            AnonymousIdentity 实例
        """
        # 计算用户ID哈希（用于快速查询，满足匿名隔离要求）
        user_id_hash = self._compute_user_id_hash(user_id)

        # 查询现有映射（通过哈希查询）
        stmt = select(UserAnonMapping).where(
            UserAnonMapping.user_id_hash == user_id_hash,
            UserAnonMapping.scene == self.SCENE_SQUARE,
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if mapping:
            # 已存在映射，获取匿名身份
            anon_stmt = select(AnonymousIdentity).where(
                AnonymousIdentity.id == mapping.anon_identity_id,
                AnonymousIdentity.deleted_at.is_(None),
            )
            anon_result = await db.execute(anon_stmt)
            anon_identity = anon_result.scalar_one_or_none()

            if anon_identity:
                return anon_identity

        # 创建新的匿名身份
        anon_service = self._get_anon_identity_service()
        anon_identity = await anon_service.create_anonymous_identity(
            user_id=user_id,
            scene=self.SCENE_SQUARE,
            db=db,
        )

        # 创建映射关系（使用哈希和加密存储）
        new_mapping = UserAnonMapping(
            id=str(uuid.uuid4()),
            user_id_hash=user_id_hash,
            encrypted_user_id=encrypt_data(user_id),
            anon_identity_id=anon_identity.id,
            scene=self.SCENE_SQUARE,
        )
        db.add(new_mapping)

        return anon_identity

    async def _build_post_response(
        self,
        post: Post,
        current_user_id: str,
        now: datetime,
        db: AsyncSession,
    ) -> PostResponse:
        """构建动态响应对象。

        Args:
            post: 动态对象
            current_user_id: 当前用户ID
            now: 当前时间
            db: 数据库会话

        Returns:
            动态响应
        """
        user_info = None
        anon_identity_info = None

        # 根据是否匿名决定显示用户信息还是匿名身份
        if post.is_anonymous and post.anon_identity_id:
            # 匿名发布，获取匿名身份信息
            anon_stmt = select(AnonymousIdentity).where(
                AnonymousIdentity.id == post.anon_identity_id,
            )
            anon_result = await db.execute(anon_stmt)
            anon = anon_result.scalar_one_or_none()

            if anon:
                anon_identity_info = AnonIdentityResponse(
                    anon_id=anon.id,
                    anon_nickname=anon.anon_nickname,
                    persona_tag=anon.persona_type,
                    anon_avatar_url=anon.anon_avatar_url,
                )
        else:
            # 实名发布，获取用户信息
            user_stmt = select(User).where(User.id == post.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if user:
                user_info = UserInfoResponse(
                    user_id=user.id,
                    nickname=user.nickname,
                    avatar_url=user.avatar_url,
                )

        # 检查当前用户是否已共鸣
        is_liked = False
        like_stmt = select(PostLike).where(
            PostLike.post_id == post.id,
            PostLike.user_id == current_user_id,
        )
        like_result = await db.execute(like_stmt)
        is_liked = like_result.scalar_one_or_none() is not None

        # 检查当前用户是否已收藏
        is_favorited = False
        favorite_stmt = select(PostFavorite).where(
            PostFavorite.post_id == post.id,
            PostFavorite.user_id == current_user_id,
        )
        favorite_result = await db.execute(favorite_stmt)
        is_favorited = favorite_result.scalar_one_or_none() is not None

        # 检查当前用户是否已关注作者（仅实名动态）
        is_following = False
        if not post.is_anonymous and post.user_id != current_user_id:
            follow_stmt = select(PostFollow).where(
                PostFollow.follower_id == current_user_id,
                PostFollow.following_id == post.user_id,
            )
            follow_result = await db.execute(follow_stmt)
            is_following = follow_result.scalar_one_or_none() is not None

        return PostResponse(
            id=post.id,
            content=post.content,
            image_urls=post.image_urls,
            is_anonymous=post.is_anonymous,
            visibility=post.visibility,
            like_count=post.like_count,
            comment_count=post.comment_count,
            favorite_count=post.favorite_count,
            user=user_info,
            anon_identity=anon_identity_info,
            is_liked=is_liked,
            is_favorited=is_favorited,
            is_following=is_following,
            created_at=post.created_at,
        )

    def _build_post_response_optimized(
        self,
        post: Post,
        current_user_id: str,
        now: datetime,
        liked_post_ids: set[str],
        favorited_post_ids: set[str],
        following_user_ids: set[str],
        users_map: dict[str, User],
        anon_map: dict[str, AnonymousIdentity],
    ) -> PostResponse:
        """构建动态响应对象（优化版，使用预查询数据）。

        Args:
            post: 动态对象
            current_user_id: 当前用户ID
            now: 当前时间
            liked_post_ids: 已共鸣的帖子ID集合
            favorited_post_ids: 已收藏的帖子ID集合
            following_user_ids: 已关注的用户ID集合
            users_map: 用户信息映射
            anon_map: 匿名身份映射

        Returns:
            动态响应
        """
        user_info = None
        anon_identity_info = None

        # 根据是否匿名决定显示用户信息还是匿名身份
        if post.is_anonymous and post.anon_identity_id:
            # 从预查询的匿名身份映射中获取
            anon = anon_map.get(post.anon_identity_id)
            if anon:
                anon_identity_info = AnonIdentityResponse(
                    anon_id=anon.id,
                    anon_nickname=anon.anon_nickname,
                    persona_tag=anon.persona_type,
                    anon_avatar_url=anon.anon_avatar_url,
                )
        else:
            # 从预查询的用户映射中获取
            user = users_map.get(post.user_id)
            if user:
                user_info = UserInfoResponse(
                    user_id=user.id,
                    nickname=user.nickname,
                    avatar_url=user.avatar_url,
                )

        # 从预查询的状态集合中判断
        is_liked = post.id in liked_post_ids
        is_favorited = post.id in favorited_post_ids
        is_following = (
            not post.is_anonymous
            and post.user_id != current_user_id
            and post.user_id in following_user_ids
        )

        return PostResponse(
            id=post.id,
            content=post.content,
            image_urls=post.image_urls,
            is_anonymous=post.is_anonymous,
            visibility=post.visibility,
            like_count=post.like_count,
            comment_count=post.comment_count,
            favorite_count=post.favorite_count,
            user=user_info,
            anon_identity=anon_identity_info,
            is_liked=is_liked,
            is_favorited=is_favorited,
            is_following=is_following,
            created_at=post.created_at,
        )

    async def _build_comment_response(
        self,
        comment: PostComment,
        now: datetime,
        db: AsyncSession,
    ) -> PostCommentResponse:
        """构建评论响应对象。

        Args:
            comment: 评论对象
            now: 当前时间
            db: 数据库会话

        Returns:
            评论响应
        """
        user_info = None
        anon_identity_info = None
        reply_to_user = None

        # 根据是否匿名决定显示用户信息还是匿名身份
        if comment.is_anonymous and comment.anon_identity_id:
            # 匿名评论，获取匿名身份信息
            anon_stmt = select(AnonymousIdentity).where(
                AnonymousIdentity.id == comment.anon_identity_id,
            )
            anon_result = await db.execute(anon_stmt)
            anon = anon_result.scalar_one_or_none()

            if anon:
                anon_identity_info = AnonIdentityResponse(
                    anon_id=anon.id,
                    anon_nickname=anon.anon_nickname,
                    persona_tag=anon.persona_type,
                    anon_avatar_url=anon.anon_avatar_url,
                )
        else:
            # 实名评论，获取用户信息
            user_stmt = select(User).where(User.id == comment.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if user:
                user_info = UserInfoResponse(
                    user_id=user.id,
                    nickname=user.nickname,
                    avatar_url=user.avatar_url,
                )

        # 获取被回复用户信息
        if comment.reply_to_comment_id:
            reply_stmt = select(PostComment).where(
                PostComment.id == comment.reply_to_comment_id,
            )
            reply_result = await db.execute(reply_stmt)
            reply_comment = reply_result.scalar_one_or_none()

            if reply_comment and not reply_comment.is_anonymous:
                reply_user_stmt = select(User).where(
                    User.id == reply_comment.user_id
                )
                reply_user_result = await db.execute(reply_user_stmt)
                reply_user = reply_user_result.scalar_one_or_none()

                if reply_user:
                    reply_to_user = UserInfoResponse(
                        user_id=reply_user.id,
                        nickname=reply_user.nickname,
                        avatar_url=reply_user.avatar_url,
                    )

        return PostCommentResponse(
            id=comment.id,
            content=comment.content,
            is_anonymous=comment.is_anonymous,
            user=user_info,
            anon_identity=anon_identity_info,
            reply_to_comment_id=comment.reply_to_comment_id,
            reply_to_user=reply_to_user,
            created_at=comment.created_at,
        )


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_post_service(
    settings: Any,
    redis: Any,
    anon_identity_service: AnonymousIdentityService | None = None,
    content_audit_provider: str = "local",
) -> PostService:
    """创建动态广场服务实例。

    Args:
        settings: 应用配置
        redis: Redis 客户端
        anon_identity_service: 匿名身份服务（可选）
        content_audit_provider: 内容审核服务提供者（默认 local）

    Returns:
        PostService 实例
    """
    return PostService(
        settings=settings,
        redis=redis,
        anon_identity_service=anon_identity_service,
        content_audit_provider=content_audit_provider,
    )
