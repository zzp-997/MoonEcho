"""举报管理服务模块。

提供举报管理相关的核心业务逻辑：
- C 端举报提交（去重、自动下架）
- 举报列表查询（筛选、分页、合并展示）
- 举报详情查询（含被举报内容）
- 举报处理（通过/驳回/封禁用户）
- 申诉审核
- 举报反馈通知闭环
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
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
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.admin import Admin
from app.models.post import Post
from app.models.report import Report
from app.models.treehole import TreeholeComment, TreeholePost
from app.models.user import AnonymousIdentity, User
from app.schemas.base import PaginatedResponse
from app.schemas.report import (
    AdminAppealListItem,
    AdminAppealReviewRequest,
    AdminAppealReviewResponse,
    AdminReportDetail,
    AdminReportListItem,
    AdminReportListRequest,
    AdminReportProcessRequest,
    AdminReportProcessResponse,
    ReportContentInfo,
    ReportCreateRequest,
    ReportCreateResponse,
)
from app.services.crypto import decrypt_data

logger = logging.getLogger(__name__)


# 自动下架阈值：同一内容被举报次数
AUTO_TAKE_DOWN_THRESHOLD = 3


class AdminReportService:
    """举报管理服务。

    封装举报管理的核心业务逻辑。
    """

    def __init__(self, redis: Any) -> None:
        self._redis = redis

    # -----------------------------------------------------------------------
    # C 端举报提交
    # -----------------------------------------------------------------------

    async def create_report(
        self,
        db: AsyncSession,
        user_id: str,
        request: ReportCreateRequest,
        ip_address: str | None = None,
    ) -> ReportCreateResponse:
        """创建举报记录。

        检查重复举报，创建举报记录，检查是否触发自动下架。

        Args:
            db: 数据库会话
            user_id: 举报人ID
            request: 举报请求
            ip_address: 客户端IP

        Returns:
            举报创建响应

        Raises:
            AppError: 重复举报时抛出
        """
        # 检查是否已举报过同一内容
        existing_stmt = select(Report).where(
            Report.reporter_id == user_id,
            Report.reported_content_type == request.reported_content_type.value,
            Report.reported_content_id == request.reported_content_id,
            Report.deleted_at.is_(None),
        )
        existing_result = await db.execute(existing_stmt)
        existing_report = existing_result.scalar_one_or_none()

        if existing_report:
            raise AppError(
                code=ErrorCode.REPORT_DUPLICATE,
                message="您已举报过该内容",
                status_code=400,
            )

        # 获取被举报内容的作者ID
        reported_user_id = await self._get_content_author(
            db,
            request.reported_content_type.value,
            request.reported_content_id,
        )

        # 如果请求中提供了被举报用户ID，优先使用
        if request.reported_user_id:
            reported_user_id = request.reported_user_id

        # 创建举报记录
        report = Report(
            reporter_id=user_id,
            reported_user_id=reported_user_id,
            reported_content_type=request.reported_content_type.value,
            reported_content_id=request.reported_content_id,
            report_type=request.report_type.value,
            reason=request.reason,
            status="pending",
        )
        db.add(report)
        await db.flush()

        # 检查是否触发自动下架（同一内容被举报次数达到阈值）
        await self._check_auto_take_down(
            db,
            request.reported_content_type.value,
            request.reported_content_id,
        )

        await db.commit()

        logger.info(
            "创建举报: report_id=%s, reporter_id=%s, content_type=%s, content_id=%s",
            report.id,
            user_id,
            request.reported_content_type.value,
            request.reported_content_id,
        )

        return ReportCreateResponse(
            id=report.id,
            status=report.status,
            message="举报已提交，我们将在24小时内处理",
            created_at=report.created_at,
        )

    async def _get_content_author(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str | None,
    ) -> str | None:
        """获取内容作者ID。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID

        Returns:
            作者ID，不存在返回 None
        """
        if not content_id:
            return None

        if content_type == "post":
            stmt = select(Post.user_id).where(Post.id == content_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

        elif content_type == "treehole_post":
            # 通过匿名身份获取加密的用户ID并解密
            from app.services.crypto import decrypt_data
            stmt = select(TreeholePost).where(TreeholePost.id == content_id)
            result = await db.execute(stmt)
            post = result.scalar_one_or_none()
            if post and post.encrypted_user_id:
                try:
                    return decrypt_data(post.encrypted_user_id)
                except Exception:
                    return None
            return None

        elif content_type == "comment":
            # 树洞评论通过匿名身份关联获取用户ID
            from app.services.crypto import decrypt_data
            stmt = select(TreeholeComment).where(TreeholeComment.id == content_id)
            result = await db.execute(stmt)
            comment = result.scalar_one_or_none()
            if comment and comment.anon_identity_id:
                # 通过匿名身份获取加密的用户ID
                anon_stmt = select(AnonymousIdentity).where(
                    AnonymousIdentity.id == comment.anon_identity_id
                )
                anon_result = await db.execute(anon_stmt)
                anon = anon_result.scalar_one_or_none()
                if anon and anon.encrypted_user_id:
                    try:
                        return decrypt_data(anon.encrypted_user_id)
                    except Exception:
                        return None
            return None

        return None

    async def _check_auto_take_down(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str | None,
    ) -> None:
        """检查是否触发自动下架。

        同一内容被举报次数达到阈值时自动下架，并通知内容作者。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID
        """
        if not content_id:
            return

        # 统计同一内容的举报次数
        count_stmt = select(func.count()).select_from(Report).where(
            Report.reported_content_type == content_type,
            Report.reported_content_id == content_id,
            Report.deleted_at.is_(None),
        )
        count_result = await db.execute(count_stmt)
        report_count = count_result.scalar() or 0

        if report_count >= AUTO_TAKE_DOWN_THRESHOLD:
            logger.warning(
                "内容触发自动下架: content_type=%s, content_id=%s, report_count=%d",
                content_type,
                content_id,
                report_count,
            )

            # 获取内容作者ID
            author_id = await self._get_content_author(db, content_type, content_id)

            # 执行下架操作
            await self._take_down_content(db, content_type, content_id)

            # 发送通知给内容作者
            if author_id:
                await self._notify_content_taken_down(db, content_type, content_id, author_id, report_count)

    async def _notify_content_taken_down(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str,
        author_id: str,
        report_count: int,
    ) -> None:
        """通知内容作者内容已被下架。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID
            author_id: 作者ID
            report_count: 举报次数
        """
        # 内容类型中文映射
        content_type_names = {
            "post": "广场动态",
            "treehole_post": "树洞帖子",
            "comment": "评论",
        }
        content_type_name = content_type_names.get(content_type, "内容")

        logger.info(
            "发送内容下架通知: author_id=%s, content_type=%s, content_id=%s, report_count=%d",
            author_id,
            content_type,
            content_id,
            report_count,
        )

        # TODO: 实现实际的通知逻辑
        # 可以通过以下方式通知用户：
        # 1. 站内消息通知
        # 2. 推送通知
        # 3. 短信通知（如果绑定）
        #
        # 示例：创建站内消息
        # notification = Notification(
        #     user_id=author_id,
        #     type="content_takedown",
        #     title=f"您的{content_type_name}已被下架",
        #     content=f"您的{content_type_name}因收到{report_count}次举报已被自动下架，如有异议请提交申诉。",
        #     metadata={
        #         "content_type": content_type,
        #         "content_id": content_id,
        #         "report_count": report_count,
        #     },
        # )
        # db.add(notification)

    async def _take_down_content(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str,
    ) -> None:
        """下架内容。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID
        """
        now = datetime.now(timezone.utc)

        if content_type == "post":
            stmt = (
                update(Post)
                .where(Post.id == content_id)
                .values(deleted_at=now)
            )
            await db.execute(stmt)

        elif content_type == "treehole_post":
            stmt = (
                update(TreeholePost)
                .where(TreeholePost.id == content_id)
                .values(deleted_at=now, status="deleted")
            )
            await db.execute(stmt)

        elif content_type == "comment":
            stmt = (
                update(TreeholeComment)
                .where(TreeholeComment.id == content_id)
                .values(deleted_at=now)
            )
            await db.execute(stmt)

    # -----------------------------------------------------------------------
    # 管理端举报列表
    # -----------------------------------------------------------------------

    async def get_reports(
        self,
        db: AsyncSession,
        params: AdminReportListRequest,
    ) -> PaginatedResponse[AdminReportListItem]:
        """查询举报列表。

        支持筛选、分页、排序，同一内容的举报合并展示。

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            分页举报列表
        """
        # 构建基础查询
        stmt = select(Report).where(Report.deleted_at.is_(None))

        # 应用筛选条件
        if params.status:
            stmt = stmt.where(Report.status == params.status.value)
        if params.report_type:
            stmt = stmt.where(Report.report_type == params.report_type.value)
        if params.content_type:
            stmt = stmt.where(Report.reported_content_type == params.content_type.value)
        if params.reporter_id:
            stmt = stmt.where(Report.reporter_id == params.reporter_id)
        if params.reported_user_id:
            stmt = stmt.where(Report.reported_user_id == params.reported_user_id)
        if params.start_time:
            stmt = stmt.where(Report.created_at >= params.start_time)
        if params.end_time:
            stmt = stmt.where(Report.created_at <= params.end_time)

        # 申诉筛选
        if params.has_appeal is True:
            stmt = stmt.where(Report.appeal_status.isnot(None))
        elif params.has_appeal is False:
            stmt = stmt.where(Report.appeal_status.is_(None))

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 应用排序
        sort_column = getattr(Report, params.sort_by, Report.created_at)
        if params.sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(sort_column)

        # 分页
        stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        # 执行查询
        result = await db.execute(stmt)
        reports = result.scalars().all()

        # 查询关联数据（举报人昵称、被举报人昵称、处理人姓名）
        reporter_ids = {r.reporter_id for r in reports if r.reporter_id}
        reported_user_ids = {r.reported_user_id for r in reports if r.reported_user_id}
        processor_ids = {r.processed_by for r in reports if r.processed_by}

        # 查询用户昵称
        user_nicknames = {}
        if reporter_ids or reported_user_ids:
            all_user_ids = reporter_ids | reported_user_ids
            user_stmt = select(User.id, User.nickname).where(User.id.in_(all_user_ids))
            user_result = await db.execute(user_stmt)
            user_nicknames = {row[0]: row[1] for row in user_result.all()}

        # 查询管理员姓名
        admin_names = {}
        if processor_ids:
            admin_stmt = select(Admin.id, Admin.nickname).where(Admin.id.in_(processor_ids))
            admin_result = await db.execute(admin_stmt)
            admin_names = {row[0]: row[1] for row in admin_result.all()}

        # 统计同一内容的举报次数
        content_report_counts = await self._get_content_report_counts(db, reports)

        # 转换为响应模型
        data = []
        for report in reports:
            item = AdminReportListItem(
                id=report.id,
                reporter_id=report.reporter_id,
                reporter_nickname=user_nicknames.get(report.reporter_id),
                reported_user_id=report.reported_user_id,
                reported_user_nickname=user_nicknames.get(report.reported_user_id),
                reported_content_type=report.reported_content_type,
                reported_content_id=report.reported_content_id,
                report_type=report.report_type,
                reason=report.reason,
                status=report.status,
                process_result=report.process_result,
                processed_by=report.processed_by,
                processed_by_name=admin_names.get(report.processed_by),
                processed_at=report.processed_at,
                appeal_status=report.appeal_status,
                created_at=report.created_at,
                same_content_report_count=content_report_counts.get(
                    f"{report.reported_content_type}:{report.reported_content_id}", 1
                ),
            )
            data.append(item)

        return PaginatedResponse.create(
            data=data,
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    async def _get_content_report_counts(
        self,
        db: AsyncSession,
        reports: list[Report],
    ) -> dict[str, int]:
        """统计各内容的举报次数。

        Args:
            db: 数据库会话
            reports: 举报列表

        Returns:
            内容举报次数映射
        """
        # 收集所有内容信息
        content_keys = []
        for r in reports:
            if r.reported_content_id:
                content_keys.append((r.reported_content_type, r.reported_content_id))

        if not content_keys:
            return {}

        # 使用单次批量查询统计各内容的举报次数（修复 N+1 查询问题）
        # 构建 OR 条件组
        conditions = []
        for content_type, content_id in content_keys:
            conditions.append(
                and_(
                    Report.reported_content_type == content_type,
                    Report.reported_content_id == content_id,
                )
            )

        # 执行批量查询，按内容类型和ID分组统计
        count_stmt = (
            select(
                Report.reported_content_type,
                Report.reported_content_id,
                func.count().label("count"),
            )
            .where(
                Report.deleted_at.is_(None),
                or_(*conditions),
            )
            .group_by(Report.reported_content_type, Report.reported_content_id)
        )

        count_result = await db.execute(count_stmt)
        rows = count_result.all()

        # 构建结果映射
        counts = {}
        for row in rows:
            key = f"{row[0]}:{row[1]}"
            counts[key] = row[2] or 1

        return counts

    # -----------------------------------------------------------------------
    # 举报详情
    # -----------------------------------------------------------------------

    async def get_report_detail(
        self,
        db: AsyncSession,
        report_id: str | UUID,
    ) -> AdminReportDetail:
        """获取举报详情。

        包含被举报内容详情和关联举报列表。

        Args:
            db: 数据库会话
            report_id: 举报ID

        Returns:
            举报详情

        Raises:
            AppError: 举报不存在时抛出
        """
        # 查询举报记录
        stmt = select(Report).where(
            Report.id == report_id,
            Report.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise AppError(
                code=ErrorCode.REPORT_NOT_FOUND,
                message="举报记录不存在",
                status_code=404,
            )

        # 查询举报人信息
        reporter_stmt = select(User).where(User.id == report.reporter_id)
        reporter_result = await db.execute(reporter_stmt)
        reporter = reporter_result.scalar_one_or_none()

        # 查询被举报人信息
        reported_user = None
        if report.reported_user_id:
            reported_user_stmt = select(User).where(User.id == report.reported_user_id)
            reported_user_result = await db.execute(reported_user_stmt)
            reported_user = reported_user_result.scalar_one_or_none()

        # 查询处理人信息
        processor = None
        if report.processed_by:
            processor_stmt = select(Admin).where(Admin.id == report.processed_by)
            processor_result = await db.execute(processor_stmt)
            processor = processor_result.scalar_one_or_none()

        # 查询被举报内容详情
        content_info = await self._get_content_info(
            db,
            report.reported_content_type,
            report.reported_content_id,
        )

        # 查询同一内容的其他举报
        related_reports = await self._get_related_reports(
            db,
            report.reported_content_type,
            report.reported_content_id,
            exclude_id=str(report.id),
        )

        return AdminReportDetail(
            id=report.id,
            reporter_id=report.reporter_id,
            reporter_nickname=reporter.nickname if reporter else None,
            reporter_phone=self._mask_phone(reporter.phone) if reporter else None,
            reported_user_id=report.reported_user_id,
            reported_user_nickname=reported_user.nickname if reported_user else None,
            reported_user_phone=self._mask_phone(reported_user.phone) if reported_user else None,
            reported_content_type=report.reported_content_type,
            reported_content_id=report.reported_content_id,
            report_type=report.report_type,
            reason=report.reason,
            status=report.status,
            process_result=report.process_result,
            processed_by=report.processed_by,
            processed_by_name=processor.nickname if processor else None,
            processed_at=report.processed_at,
            appeal_status=report.appeal_status,
            appeal_reason=report.appeal_reason,
            created_at=report.created_at,
            updated_at=report.updated_at,
            content_info=content_info,
            related_reports=related_reports,
        )

    async def _get_content_info(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str | None,
    ) -> ReportContentInfo | None:
        """获取被举报内容详情。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID

        Returns:
            内容详情，不存在返回 None
        """
        if not content_id:
            return None

        if content_type == "post":
            stmt = select(Post).where(Post.id == content_id)
            result = await db.execute(stmt)
            post = result.scalar_one_or_none()

            if not post:
                return ReportContentInfo(
                    id=content_id,
                    type=content_type,
                    content=None,
                    author_id=None,
                    author_nickname=None,
                    created_at=None,
                    status="deleted",
                )

            # 查询作者昵称
            author_stmt = select(User.nickname).where(User.id == post.user_id)
            author_result = await db.execute(author_stmt)
            author_nickname = author_result.scalar_one_or_none()

            return ReportContentInfo(
                id=post.id,
                type=content_type,
                content=self._truncate_content(post.content),
                author_id=post.user_id,
                author_nickname=author_nickname,
                created_at=post.created_at,
                status="deleted" if post.deleted_at else "active",
            )

        elif content_type == "treehole_post":
            stmt = select(TreeholePost).where(TreeholePost.id == content_id)
            result = await db.execute(stmt)
            post = result.scalar_one_or_none()

            if not post:
                return ReportContentInfo(
                    id=content_id,
                    type=content_type,
                    content=None,
                    author_id=None,
                    author_nickname=None,
                    created_at=None,
                    status="deleted",
                )

            # 解密用户ID并查询作者昵称
            try:
                author_id = decrypt_data(post.encrypted_user_id)
            except Exception:
                author_id = None

            author_nickname = None
            if author_id:
                author_stmt = select(User.nickname).where(User.id == author_id)
                author_result = await db.execute(author_stmt)
                author_nickname = author_result.scalar_one_or_none()

            return ReportContentInfo(
                id=post.id,
                type=content_type,
                content=self._truncate_content(post.content),
                author_id=author_id,
                author_nickname=author_nickname,
                created_at=post.created_at,
                status=post.status,
            )

        elif content_type == "comment":
            stmt = select(TreeholeComment).where(TreeholeComment.id == content_id)
            result = await db.execute(stmt)
            comment = result.scalar_one_or_none()

            if not comment:
                return ReportContentInfo(
                    id=content_id,
                    type=content_type,
                    content=None,
                    author_id=None,
                    author_nickname=None,
                    created_at=None,
                    status="deleted",
                )

            # 通过匿名身份获取用户ID并查询作者昵称
            author_id = None
            author_nickname = None
            if comment.anon_identity_id:
                anon_stmt = select(AnonymousIdentity).where(
                    AnonymousIdentity.id == comment.anon_identity_id
                )
                anon_result = await db.execute(anon_stmt)
                anon = anon_result.scalar_one_or_none()
                if anon and anon.encrypted_user_id:
                    try:
                        author_id = decrypt_data(anon.encrypted_user_id)
                        if author_id:
                            author_stmt = select(User.nickname).where(User.id == author_id)
                            author_result = await db.execute(author_stmt)
                            author_nickname = author_result.scalar_one_or_none()
                    except Exception:
                        author_id = None

            return ReportContentInfo(
                id=comment.id,
                type=content_type,
                content=self._truncate_content(comment.content),
                author_id=author_id,
                author_nickname=author_nickname,
                created_at=comment.created_at,
                status="deleted" if comment.deleted_at else "active",
            )

        return None

    async def _get_related_reports(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str | None,
        exclude_id: str,
    ) -> list[dict]:
        """获取同一内容的其他举报。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID
            exclude_id: 排除的举报ID

        Returns:
            相关举报列表
        """
        if not content_id:
            return []

        stmt = select(Report).where(
            Report.reported_content_type == content_type,
            Report.reported_content_id == content_id,
            Report.id != exclude_id,
            Report.deleted_at.is_(None),
        ).order_by(Report.created_at.desc()).limit(10)

        result = await db.execute(stmt)
        reports = result.scalars().all()

        return [
            {
                "id": r.id,
                "reporter_id": r.reporter_id,
                "report_type": r.report_type,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]

    # -----------------------------------------------------------------------
    # 举报处理
    # -----------------------------------------------------------------------

    async def process_report(
        self,
        db: AsyncSession,
        report_id: str | UUID,
        request: AdminReportProcessRequest,
        admin_id: str,
        ip_address: str | None = None,
        log_action: Any = None,
    ) -> AdminReportProcessResponse:
        """处理举报。

        支持通过、驳回、封禁用户三种操作。

        Args:
            db: 数据库会话
            report_id: 举报ID
            request: 处理请求
            admin_id: 管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            处理结果

        Raises:
            AppError: 举报不存在或已处理时抛出
        """
        # 查询举报记录
        stmt = select(Report).where(
            Report.id == report_id,
            Report.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise AppError(
                code=ErrorCode.REPORT_NOT_FOUND,
                message="举报记录不存在",
                status_code=404,
            )

        if report.status not in ["pending", "processing"]:
            raise AppError(
                code=ErrorCode.REPORT_ALREADY_PROCESSED,
                message="该举报已处理",
                status_code=400,
            )

        now = datetime.now(timezone.utc)

        # 更新举报状态
        if request.action == "approve":
            report.status = "approved"
        elif request.action == "reject":
            report.status = "rejected"
        elif request.action == "ban_user":
            report.status = "approved"
            # 封禁用户
            await self._ban_user(
                db,
                report.reported_user_id,
                request.reason,
                request.ban_duration_days,
            )

        report.process_result = request.reason
        report.processed_by = admin_id
        report.processed_at = now

        # 隐藏被举报内容
        if request.hide_content and report.reported_content_id:
            await self._take_down_content(
                db,
                report.reported_content_type,
                report.reported_content_id,
            )

        # 记录审计日志
        if log_action:
            await log_action(
                db=db,
                admin_id=admin_id,
                action="process_report",
                target_type="report",
                target_id=str(report_id),
                details={
                    "action": request.action,
                    "reason": request.reason,
                    "ban_duration_days": request.ban_duration_days,
                    "hide_content": request.hide_content,
                    "notify_reporter": request.notify_reporter,
                    "notify_reported_user": request.notify_reported_user,
                },
                ip_address=ip_address,
                auto_commit=False,
            )

        await db.commit()

        logger.info(
            "处理举报: report_id=%s, action=%s, admin_id=%s",
            report_id,
            request.action,
            admin_id,
        )

        # TODO: 发送通知给举报人和被举报人
        # if request.notify_reporter:
        #     await self._notify_reporter(db, report)
        # if request.notify_reported_user:
        #     await self._notify_reported_user(db, report)

        return AdminReportProcessResponse(
            id=report.id,
            status=report.status,
            action=request.action,
            message=f"举报已{'通过' if request.action != 'reject' else '驳回'}",
        )

    async def _ban_user(
        self,
        db: AsyncSession,
        user_id: str | None,
        reason: str,
        duration_days: int | None,
    ) -> None:
        """封禁用户。

        Args:
            db: 数据库会话
            user_id: 用户ID
            reason: 封禁原因
            duration_days: 封禁天数，None表示永久封禁
        """
        if not user_id:
            return

        ban_until = None
        if duration_days:
            ban_until = datetime.now(timezone.utc) + timedelta(days=duration_days)

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                is_banned=True,
                ban_reason=reason,
                ban_until=ban_until,
            )
        )
        await db.execute(stmt)

    # -----------------------------------------------------------------------
    # 申诉管理
    # -----------------------------------------------------------------------

    async def get_appeals(
        self,
        db: AsyncSession,
        params: AdminAppealListRequest,
    ) -> PaginatedResponse[AdminAppealListItem]:
        """查询申诉列表。

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            分页申诉列表
        """
        # 构建查询条件
        stmt = select(Report).where(
            Report.appeal_status.isnot(None),
            Report.deleted_at.is_(None),
        )

        if params.appeal_status:
            stmt = stmt.where(Report.appeal_status == params.appeal_status.value)
        if params.start_time:
            stmt = stmt.where(Report.updated_at >= params.start_time)
        if params.end_time:
            stmt = stmt.where(Report.updated_at <= params.end_time)

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页查询
        stmt = stmt.order_by(desc(Report.updated_at))
        stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        result = await db.execute(stmt)
        reports = result.scalars().all()

        # 查询用户昵称
        user_ids = {r.reporter_id for r in reports if r.reporter_id} | {r.reported_user_id for r in reports if r.reported_user_id}
        user_nicknames = {}
        if user_ids:
            user_stmt = select(User.id, User.nickname).where(User.id.in_(user_ids))
            user_result = await db.execute(user_stmt)
            user_nicknames = {row[0]: row[1] for row in user_result.all()}

        # 转换为响应模型
        data = [
            AdminAppealListItem(
                id=r.id,
                report_id=r.id,
                reporter_id=r.reporter_id,
                reporter_nickname=user_nicknames.get(r.reporter_id),
                reported_user_id=r.reported_user_id,
                reported_user_nickname=user_nicknames.get(r.reported_user_id),
                report_type=r.report_type,
                appeal_status=r.appeal_status,
                appeal_reason=r.appeal_reason,
                created_at=r.created_at,
            )
            for r in reports
        ]

        return PaginatedResponse.create(
            data=data,
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    async def review_appeal(
        self,
        db: AsyncSession,
        report_id: str | UUID,
        request: AdminAppealReviewRequest,
        admin_id: str,
        ip_address: str | None = None,
        log_action: Any = None,
    ) -> AdminAppealReviewResponse:
        """审核申诉。

        Args:
            db: 数据库会话
            report_id: 举报ID
            request: 审核请求
            admin_id: 管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            审核结果

        Raises:
            AppError: 举报不存在或申诉状态不正确时抛出
        """
        # 查询举报记录
        stmt = select(Report).where(
            Report.id == report_id,
            Report.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            raise AppError(
                code=ErrorCode.REPORT_NOT_FOUND,
                message="举报记录不存在",
                status_code=404,
            )

        if report.appeal_status != "pending":
            raise AppError(
                code=ErrorCode.APPEAL_NOT_FOUND,
                message="该申诉已处理",
                status_code=400,
            )

        now = datetime.now(timezone.utc)

        # 更新申诉状态
        report.appeal_status = request.action

        # 如果申诉通过，可选择解封用户和恢复内容
        if request.action == "approve":
            if request.unban_user and report.reported_user_id:
                await self._unban_user(db, report.reported_user_id)
            if request.restore_content and report.reported_content_id:
                await self._restore_content(
                    db,
                    report.reported_content_type,
                    report.reported_content_id,
                )

        # 记录审计日志
        if log_action:
            await log_action(
                db=db,
                admin_id=admin_id,
                action="review_appeal",
                target_type="report",
                target_id=str(report_id),
                details={
                    "action": request.action,
                    "reason": request.reason,
                    "unban_user": request.unban_user,
                    "restore_content": request.restore_content,
                },
                ip_address=ip_address,
                auto_commit=False,
            )

        await db.commit()

        logger.info(
            "审核申诉: report_id=%s, action=%s, admin_id=%s",
            report_id,
            request.action,
            admin_id,
        )

        return AdminAppealReviewResponse(
            id=report.id,
            appeal_status=report.appeal_status,
            action=request.action,
            message=f"申诉已{'通过' if request.action == 'approve' else '驳回'}",
        )

    async def _unban_user(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> None:
        """解封用户。

        Args:
            db: 数据库会话
            user_id: 用户ID
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                is_banned=False,
                ban_reason=None,
                ban_until=None,
            )
        )
        await db.execute(stmt)

    async def _restore_content(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str,
    ) -> None:
        """恢复内容。

        注意：只能恢复因举报下架的内容，无法恢复用户主动永久删除的内容。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID
        """
        # 首先检查内容是否存在以及是否被永久删除
        content_exists = await self._check_content_exists(db, content_type, content_id)
        if not content_exists:
            logger.warning(
                "内容不存在或已被永久删除，无法恢复: content_type=%s, content_id=%s",
                content_type,
                content_id,
            )
            return

        if content_type == "post":
            stmt = (
                update(Post)
                .where(Post.id == content_id)
                .values(deleted_at=None)
            )
            await db.execute(stmt)

        elif content_type == "treehole_post":
            stmt = (
                update(TreeholePost)
                .where(TreeholePost.id == content_id)
                .values(deleted_at=None, status="active")
            )
            await db.execute(stmt)

        elif content_type == "comment":
            stmt = (
                update(TreeholeComment)
                .where(TreeholeComment.id == content_id)
                .values(deleted_at=None)
            )
            await db.execute(stmt)

    async def _check_content_exists(
        self,
        db: AsyncSession,
        content_type: str,
        content_id: str,
    ) -> bool:
        """检查内容是否存在（区分举报下架和用户删除）。

        Args:
            db: 数据库会话
            content_type: 内容类型
            content_id: 内容ID

        Returns:
            内容是否存在
        """
        if content_type == "post":
            stmt = select(Post.id).where(Post.id == content_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none() is not None

        elif content_type == "treehole_post":
            stmt = select(TreeholePost.id).where(TreeholePost.id == content_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none() is not None

        elif content_type == "comment":
            stmt = select(TreeholeComment.id).where(TreeholeComment.id == content_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none() is not None

        return False

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
    def _truncate_content(content: str | None, max_length: int = 200) -> str | None:
        """截断内容。"""
        if not content:
            return None
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."
