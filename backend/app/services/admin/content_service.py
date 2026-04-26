"""内容管理服务模块。

提供内容管理相关的核心业务逻辑：
- 内容列表（树洞/广场）
- 内容查看
- 内容隐藏/显示
- 内容推荐/取消推荐
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import (
    and_,
    desc,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.post import Post
from app.models.report import Report
from app.models.treehole import TreeholePost
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.report import (
    AdminContentDetail,
    AdminContentListItem,
    AdminContentListRequest,
    AdminContentStatusRequest,
    AdminContentStatusResponse,
    ContentStatus,
    ContentType,
)

logger = logging.getLogger(__name__)


class AdminContentService:
    """内容管理服务。

    封装内容管理的核心业务逻辑。
    """

    def __init__(self, redis: Any) -> None:
        self._redis = redis

    # -----------------------------------------------------------------------
    # 内容列表
    # -----------------------------------------------------------------------

    async def get_contents(
        self,
        db: AsyncSession,
        params: AdminContentListRequest,
    ) -> PaginatedResponse[AdminContentListItem]:
        """查询内容列表。

        支持树洞帖子和广场动态的统一查询。

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            分页内容列表
        """
        # 根据内容类型选择查询方式
        if params.content_type == ContentType.POST:
            return await self._get_posts(db, params)
        elif params.content_type == ContentType.TREEHOLE_POST:
            return await self._get_treehole_posts(db, params)
        else:
            # 未指定类型时，返回两种内容的混合列表
            return await self._get_mixed_contents(db, params)

    async def _get_posts(
        self,
        db: AsyncSession,
        params: AdminContentListRequest,
    ) -> PaginatedResponse[AdminContentListItem]:
        """查询广场动态列表。"""
        # 构建基础查询
        stmt = select(Post)

        # 应用筛选条件
        if params.author_id:
            stmt = stmt.where(Post.user_id == params.author_id)
        if params.start_time:
            stmt = stmt.where(Post.created_at >= params.start_time)
        if params.end_time:
            stmt = stmt.where(Post.created_at <= params.end_time)
        if params.search:
            search_pattern = f"%{params.search}%"
            stmt = stmt.where(Post.content.ilike(search_pattern))

        # 状态筛选
        if params.status:
            if params.status == ContentStatus.ACTIVE:
                stmt = stmt.where(Post.deleted_at.is_(None))
            elif params.status == ContentStatus.HIDDEN:
                stmt = stmt.where(Post.deleted_at.isnot(None))
            elif params.status == ContentStatus.DELETED:
                stmt = stmt.where(Post.deleted_at.isnot(None))

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 排序和分页
        sort_column = getattr(Post, params.sort_by, Post.created_at)
        if params.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(sort_column)

        stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        # 执行查询
        result = await db.execute(stmt)
        posts = result.scalars().all()

        # 查询关联数据
        data = await self._enrich_posts(db, posts)

        return PaginatedResponse.create(
            data=data,
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    async def _get_treehole_posts(
        self,
        db: AsyncSession,
        params: AdminContentListRequest,
    ) -> PaginatedResponse[AdminContentListItem]:
        """查询树洞帖子列表。"""
        # 构建基础查询
        stmt = select(TreeholePost)

        # 应用筛选条件
        if params.author_id:
            stmt = stmt.where(TreeholePost.user_id == params.author_id)
        if params.start_time:
            stmt = stmt.where(TreeholePost.created_at >= params.start_time)
        if params.end_time:
            stmt = stmt.where(TreeholePost.created_at <= params.end_time)
        if params.search:
            search_pattern = f"%{params.search}%"
            stmt = stmt.where(TreeholePost.content.ilike(search_pattern))

        # 状态筛选
        if params.status:
            if params.status == ContentStatus.ACTIVE:
                stmt = stmt.where(
                    TreeholePost.deleted_at.is_(None),
                    TreeholePost.status == "active",
                )
            elif params.status == ContentStatus.HIDDEN:
                stmt = stmt.where(
                    or_(
                        TreeholePost.deleted_at.isnot(None),
                        TreeholePost.status != "active",
                    )
                )

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 排序和分页
        sort_column = getattr(TreeholePost, params.sort_by, TreeholePost.created_at)
        if params.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(sort_column)

        stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        # 执行查询
        result = await db.execute(stmt)
        posts = result.scalars().all()

        # 查询关联数据
        data = await self._enrich_treehole_posts(db, posts)

        return PaginatedResponse.create(
            data=data,
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    async def _get_mixed_contents(
        self,
        db: AsyncSession,
        params: AdminContentListRequest,
    ) -> PaginatedResponse[AdminContentListItem]:
        """查询混合内容列表。

        由于两种内容类型不同，这里简化为分页查询其中一种。
        实际项目中可以考虑使用 UNION 查询或分开查询后合并。
        """
        # 简化实现：优先查询广场动态
        return await self._get_posts(db, params)

    async def _enrich_posts(
        self,
        db: AsyncSession,
        posts: list[Post],
    ) -> list[AdminContentListItem]:
        """丰富广场动态数据。"""
        if not posts:
            return []

        # 查询作者昵称
        author_ids = {p.user_id for p in posts}
        author_stmt = select(User.id, User.nickname).where(User.id.in_(author_ids))
        author_result = await db.execute(author_stmt)
        author_nicknames = {row[0]: row[1] for row in author_result.all()}

        # 查询举报次数
        post_ids = {p.id for p in posts}
        report_counts = await self._get_report_counts(db, "post", post_ids)

        return [
            AdminContentListItem(
                id=post.id,
                content_type=ContentType.POST.value,
                content=self._truncate_content(post.content),
                author_id=post.user_id,
                author_nickname=author_nicknames.get(post.user_id),
                status=ContentStatus.DELETED.value if post.deleted_at else ContentStatus.ACTIVE.value,
                is_recommended=False,  # 广场动态暂无推荐功能
                report_count=report_counts.get(str(post.id), 0),
                like_count=post.like_count,
                comment_count=post.comment_count,
                created_at=post.created_at,
            )
            for post in posts
        ]

    async def _enrich_treehole_posts(
        self,
        db: AsyncSession,
        posts: list[TreeholePost],
    ) -> list[AdminContentListItem]:
        """丰富树洞帖子数据。"""
        if not posts:
            return []

        # 查询作者昵称
        author_ids = {p.user_id for p in posts}
        author_stmt = select(User.id, User.nickname).where(User.id.in_(author_ids))
        author_result = await db.execute(author_stmt)
        author_nicknames = {row[0]: row[1] for row in author_result.all()}

        # 查询举报次数
        post_ids = {p.id for p in posts}
        report_counts = await self._get_report_counts(db, "treehole_post", post_ids)

        return [
            AdminContentListItem(
                id=post.id,
                content_type=ContentType.TREEHOLE_POST.value,
                content=self._truncate_content(post.content),
                author_id=post.user_id,
                author_nickname=author_nicknames.get(post.user_id),
                status=post.status if not post.deleted_at else ContentStatus.DELETED.value,
                is_recommended=False,  # 树洞暂无推荐功能
                report_count=report_counts.get(str(post.id), 0),
                like_count=post.resonance_count,  # 树洞使用共鸣数
                comment_count=post.comment_count,
                created_at=post.created_at,
            )
            for post in posts
        ]

    async def _get_report_counts(
        self,
        db: AsyncSession,
        content_type: str,
        content_ids: set,
    ) -> dict[str, int]:
        """统计内容的举报次数。"""
        if not content_ids:
            return {}

        stmt = (
            select(
                Report.reported_content_id,
                func.count().label("count"),
            )
            .where(
                Report.reported_content_type == content_type,
                Report.reported_content_id.in_([str(cid) for cid in content_ids]),
                Report.deleted_at.is_(None),
            )
            .group_by(Report.reported_content_id)
        )
        result = await db.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    # -----------------------------------------------------------------------
    # 内容详情
    # -----------------------------------------------------------------------

    async def get_content_detail(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str | UUID,
    ) -> AdminContentDetail:
        """获取内容详情。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID

        Returns:
            内容详情

        Raises:
            AppError: 内容不存在时抛出
        """
        if content_type == ContentType.POST.value:
            return await self._get_post_detail(db, content_id)
        elif content_type == ContentType.TREEHOLE_POST.value:
            return await self._get_treehole_post_detail(db, content_id)
        else:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="不支持的内容类型",
                status_code=400,
            )

    async def _get_post_detail(
        self,
        db: AsyncSession,
        content_id: str | UUID,
    ) -> AdminContentDetail:
        """获取广场动态详情。"""
        stmt = select(Post).where(Post.id == content_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.CONTENT_NOT_FOUND,
                message="内容不存在",
                status_code=404,
            )

        # 查询作者信息
        author_stmt = select(User).where(User.id == post.user_id)
        author_result = await db.execute(author_stmt)
        author = author_result.scalar_one_or_none()

        # 查询举报次数
        report_count_stmt = select(func.count()).select_from(Report).where(
            Report.reported_content_type == ContentType.POST.value,
            Report.reported_content_id == str(content_id),
            Report.deleted_at.is_(None),
        )
        report_count_result = await db.execute(report_count_stmt)
        report_count = report_count_result.scalar() or 0

        return AdminContentDetail(
            id=post.id,
            content_type=ContentType.POST.value,
            content=post.content,
            image_urls=post.image_urls,
            author_id=post.user_id,
            author_nickname=author.nickname if author else None,
            author_phone=self._mask_phone(author.phone) if author else None,
            status=ContentStatus.DELETED.value if post.deleted_at else ContentStatus.ACTIVE.value,
            is_recommended=False,
            visibility=post.visibility,
            topic_tag=None,
            report_count=report_count,
            like_count=post.like_count,
            comment_count=post.comment_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    async def _get_treehole_post_detail(
        self,
        db: AsyncSession,
        content_id: str | UUID,
    ) -> AdminContentDetail:
        """获取树洞帖子详情。"""
        stmt = select(TreeholePost).where(TreeholePost.id == content_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.CONTENT_NOT_FOUND,
                message="内容不存在",
                status_code=404,
            )

        # 查询作者信息
        author_stmt = select(User).where(User.id == post.user_id)
        author_result = await db.execute(author_stmt)
        author = author_result.scalar_one_or_none()

        # 查询举报次数
        report_count_stmt = select(func.count()).select_from(Report).where(
            Report.reported_content_type == ContentType.TREEHOLE_POST.value,
            Report.reported_content_id == str(content_id),
            Report.deleted_at.is_(None),
        )
        report_count_result = await db.execute(report_count_stmt)
        report_count = report_count_result.scalar() or 0

        return AdminContentDetail(
            id=post.id,
            content_type=ContentType.TREEHOLE_POST.value,
            content=post.content,
            image_urls=post.image_urls,
            author_id=post.user_id,
            author_nickname=author.nickname if author else None,
            author_phone=self._mask_phone(author.phone) if author else None,
            status=post.status if not post.deleted_at else ContentStatus.DELETED.value,
            is_recommended=False,
            visibility=None,
            topic_tag=post.topic_tag,
            report_count=report_count,
            like_count=post.resonance_count,
            comment_count=post.comment_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    # -----------------------------------------------------------------------
    # 内容状态管理
    # -----------------------------------------------------------------------

    async def update_content_status(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str | UUID,
        request: AdminContentStatusRequest,
        admin_id: str,
        ip_address: str | None = None,
        log_action: Any = None,
    ) -> AdminContentStatusResponse:
        """更新内容状态。

        支持隐藏、显示、推荐、取消推荐操作。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID
            request: 状态修改请求
            admin_id: 管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            操作结果

        Raises:
            AppError: 内容不存在时抛出
        """
        if content_type == ContentType.POST.value:
            return await self._update_post_status(
                db, content_id, request, admin_id, ip_address, log_action
            )
        elif content_type == ContentType.TREEHOLE_POST.value:
            return await self._update_treehole_post_status(
                db, content_id, request, admin_id, ip_address, log_action
            )
        else:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="不支持的内容类型",
                status_code=400,
            )

    async def _update_post_status(
        self,
        db: AsyncSession,
        content_id: str | UUID,
        request: AdminContentStatusRequest,
        admin_id: str,
        ip_address: str | None,
        log_action: Any,
    ) -> AdminContentStatusResponse:
        """更新广场动态状态。"""
        # 查询内容
        stmt = select(Post).where(Post.id == content_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.CONTENT_NOT_FOUND,
                message="内容不存在",
                status_code=404,
            )

        now = datetime.now(timezone.utc)
        current_status = ContentStatus.DELETED.value if post.deleted_at else ContentStatus.ACTIVE.value

        # 执行操作
        if request.action == "hide":
            if post.deleted_at:
                raise AppError(
                    code=ErrorCode.CONTENT_ALREADY_HIDDEN,
                    message="内容已被隐藏",
                    status_code=400,
                )
            post.deleted_at = now

        elif request.action == "show":
            if not post.deleted_at:
                raise AppError(
                    code=ErrorCode.CONTENT_ALREADY_VISIBLE,
                    message="内容已处于显示状态",
                    status_code=400,
                )
            post.deleted_at = None

        # 广场动态暂不支持推荐功能
        # elif request.action == "recommend":
        #     pass
        # elif request.action == "unrecommend":
        #     pass

        # 记录审计日志
        if log_action:
            await log_action(
                db=db,
                admin_id=admin_id,
                action="update_content_status",
                target_type="post",
                target_id=str(content_id),
                details={
                    "action": request.action,
                    "reason": request.reason,
                    "previous_status": current_status,
                },
                ip_address=ip_address,
                auto_commit=False,
            )

        await db.commit()

        logger.info(
            "更新内容状态: content_type=post, content_id=%s, action=%s, admin_id=%s",
            content_id,
            request.action,
            admin_id,
        )

        new_status = ContentStatus.DELETED.value if post.deleted_at else ContentStatus.ACTIVE.value

        return AdminContentStatusResponse(
            id=str(content_id),
            content_type=ContentType.POST.value,
            status=new_status,
            is_recommended=False,
            action=request.action,
            message=f"内容已{'隐藏' if request.action == 'hide' else '显示'}",
        )

    async def _update_treehole_post_status(
        self,
        db: AsyncSession,
        content_id: str | UUID,
        request: AdminContentStatusRequest,
        admin_id: str,
        ip_address: str | None,
        log_action: Any,
    ) -> AdminContentStatusResponse:
        """更新树洞帖子状态。"""
        # 查询内容
        stmt = select(TreeholePost).where(TreeholePost.id == content_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.CONTENT_NOT_FOUND,
                message="内容不存在",
                status_code=404,
            )

        now = datetime.now(timezone.utc)
        current_status = post.status

        # 执行操作
        if request.action == "hide":
            if post.deleted_at or post.status != "active":
                raise AppError(
                    code=ErrorCode.CONTENT_ALREADY_HIDDEN,
                    message="内容已被隐藏",
                    status_code=400,
                )
            post.deleted_at = now
            post.status = "deleted"

        elif request.action == "show":
            if not post.deleted_at and post.status == "active":
                raise AppError(
                    code=ErrorCode.CONTENT_ALREADY_VISIBLE,
                    message="内容已处于显示状态",
                    status_code=400,
                )
            post.deleted_at = None
            post.status = "active"

        # 记录审计日志
        if log_action:
            await log_action(
                db=db,
                admin_id=admin_id,
                action="update_content_status",
                target_type="treehole_post",
                target_id=str(content_id),
                details={
                    "action": request.action,
                    "reason": request.reason,
                    "previous_status": current_status,
                },
                ip_address=ip_address,
                auto_commit=False,
            )

        await db.commit()

        logger.info(
            "更新内容状态: content_type=treehole_post, content_id=%s, action=%s, admin_id=%s",
            content_id,
            request.action,
            admin_id,
        )

        new_status = post.status if not post.deleted_at else ContentStatus.DELETED.value

        return AdminContentStatusResponse(
            id=str(content_id),
            content_type=ContentType.TREEHOLE_POST.value,
            status=new_status,
            is_recommended=False,
            action=request.action,
            message=f"内容已{'隐藏' if request.action == 'hide' else '显示'}",
        )

    # -----------------------------------------------------------------------
    # 工具方法
    # -----------------------------------------------------------------------

    @staticmethod
    def _mask_phone(phone: str | None) -> str | None:
        """手机号脱敏处理。"""
        if not phone or len(phone) < 7:
            return phone
        return f"{phone[:3]}****{phone[-4:]}"

    @staticmethod
    def _truncate_content(content: str | None, max_length: int = 100) -> str | None:
        """截断内容。"""
        if not content:
            return None
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."
