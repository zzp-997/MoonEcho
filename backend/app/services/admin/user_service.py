"""用户管理服务模块。

提供管理后台用户管理相关的核心业务逻辑：
- 用户列表查询（搜索、筛选、分页、排序）
- 用户详情查询
- 封禁/解封操作
- 青少年模式管理
- 用户日记统计
- 用户社交数据统计
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID, uuid4

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
from app.models.chat import Friendship
from app.models.diary import EmotionDiary
from app.models.post import Post
from app.models.treehole import TreeholeComment, TreeholePost
from app.models.user import User
from app.schemas.admin import (
    AdminBanUserRequest,
    AdminMinorModeRequest,
    AdminUnbanUserRequest,
    AdminUserDetail,
    AdminUserDiaryStats,
    AdminUserListItem,
    AdminUserSocialStats,
)
from app.schemas.base import PaginatedResponse

logger = logging.getLogger(__name__)


class AdminUserService:
    """用户管理服务。

    封装管理后台用户相关操作的核心业务逻辑。
    """

    def __init__(self, redis: Any) -> None:
        self._redis = redis

    # -----------------------------------------------------------------------
    # 用户列表查询
    # -----------------------------------------------------------------------

    async def get_users(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        age_range: str | None = None,
        is_minor: bool | None = None,
        is_banned: bool | None = None,
        register_start: datetime | None = None,
        register_end: datetime | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> PaginatedResponse[AdminUserListItem]:
        """查询用户列表。

        支持以下筛选条件：
        - search: 昵称/手机号模糊搜索
        - age_range: 年龄段筛选
        - is_minor: 青少年模式筛选
        - is_banned: 封禁状态筛选
        - register_start/register_end: 注册时间范围

        支持以下排序：
        - created_at: 注册时间
        - last_active_at: 最后活跃时间

        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页条数
            search: 搜索关键词
            age_range: 年龄段
            is_minor: 是否未成年人
            is_banned: 是否被封禁
            register_start: 注册时间起始
            register_end: 注册时间截止
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            分页用户列表
        """
        # 构建基础查询
        stmt = select(User).where(User.deleted_at.is_(None))

        # 应用搜索条件
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.nickname.ilike(search_pattern),
                    User.phone.ilike(search_pattern),
                )
            )

        # 应用年龄段筛选
        if age_range:
            stmt = stmt.where(User.age_range == age_range)

        # 应用青少年模式筛选
        if is_minor is not None:
            stmt = stmt.where(User.is_minor == is_minor)

        # 应用封禁状态筛选
        if is_banned is not None:
            stmt = stmt.where(User.is_banned == is_banned)

        # 应用注册时间范围筛选
        if register_start:
            stmt = stmt.where(User.created_at >= register_start)
        if register_end:
            stmt = stmt.where(User.created_at <= register_end)

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 应用排序
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(sort_column)

        # 分页
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # 执行查询
        result = await db.execute(stmt)
        users = result.scalars().all()

        # 转换为响应模型
        data = [self._to_user_list_item(user) for user in users]

        return PaginatedResponse.create(
            data=data,
            page=page,
            page_size=page_size,
            total=total,
        )

    def _to_user_list_item(self, user: User) -> AdminUserListItem:
        """将 User ORM 对象转换为 AdminUserListItem。"""
        # 手机号脱敏：显示前3位和后4位，中间用 * 替代
        phone_masked = self._mask_phone(user.phone)

        return AdminUserListItem(
            id=user.id,
            phone=phone_masked,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            age_range=user.age_range,
            is_minor=user.is_minor,
            is_banned=user.is_banned,
            ban_reason=user.ban_reason,
            ban_until=user.ban_until,
            social_energy=float(user.social_energy) if user.social_energy else None,
            created_at=user.created_at,
            last_active_at=user.last_active_at,
        )

    # -----------------------------------------------------------------------
    # 用户详情查询
    # -----------------------------------------------------------------------

    async def get_user_detail(
        self,
        db: AsyncSession,
        user_id: UUID | str,
    ) -> AdminUserDetail:
        """查询用户详情。

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户详情

        Raises:
            AppError: 用户不存在时抛出
        """
        user = await self._get_user_by_id(db, user_id)

        # 手机号脱敏
        phone_masked = self._mask_phone(user.phone)
        guardian_phone_masked = self._mask_phone(user.guardian_phone) if user.guardian_phone else None

        return AdminUserDetail(
            id=user.id,
            phone=phone_masked,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            age_range=user.age_range,
            city=user.city,
            occupation=user.occupation,
            is_minor=user.is_minor,
            guardian_phone=guardian_phone_masked,
            is_banned=user.is_banned,
            ban_reason=user.ban_reason,
            ban_until=user.ban_until,
            social_energy=float(user.social_energy) if user.social_energy else None,
            created_at=user.created_at,
            last_active_at=user.last_active_at,
            notification_settings=user.notification_settings,
        )

    async def _get_user_by_id(self, db: AsyncSession, user_id: UUID | str) -> User:
        """根据 ID 获取用户，不存在则抛出异常。"""
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        return user

    # -----------------------------------------------------------------------
    # 封禁/解封操作
    # -----------------------------------------------------------------------

    async def ban_user(
        self,
        db: AsyncSession,
        user_id: UUID | str,
        request: AdminBanUserRequest,
        admin_id: str,
        ip_address: str,
        log_action: Any,
    ) -> AdminUserDetail:
        """封禁用户。

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 封禁请求
            admin_id: 操作管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            更新后的用户详情

        Raises:
            AppError: 用户不存在或已被封禁时抛出
        """
        user = await self._get_user_by_id(db, user_id)

        # 检查是否已被封禁
        if user.is_banned:
            raise AppError(
                code=ErrorCode.USER_DISABLED,
                message="用户已被封禁",
                status_code=400,
            )

        # 计算封禁结束时间
        ban_until = None
        if request.duration_days:
            ban_until = datetime.now(timezone.utc) + timedelta(days=request.duration_days)

        # 更新用户状态
        user.is_banned = True
        user.ban_reason = request.reason
        user.ban_until = ban_until

        # 记录操作日志（关键操作使用同步写入确保审计日志不丢失）
        # 使用 auto_commit=False 确保日志和用户状态更新在同一事务中
        await log_action(
            db=db,
            admin_id=admin_id,
            action="ban_user",
            target_type="user",
            target_id=user_id,
            details={
                "reason": request.reason,
                "duration_days": request.duration_days,
                "ban_until": ban_until.isoformat() if ban_until else None,
                "notify_user": request.notify_user,
            },
            ip_address=ip_address,
            auto_commit=False,
        )

        # 统一提交事务，确保用户状态更新和日志记录的原子性
        await db.commit()

        logger.info("用户被封禁: user_id=%s, reason=%s, duration=%s", user_id, request.reason, request.duration_days)

        # TODO: 发送通知给用户
        if request.notify_user:
            pass  # 后续实现通知推送

        return await self.get_user_detail(db, user_id)

    async def unban_user(
        self,
        db: AsyncSession,
        user_id: UUID | str,
        request: AdminUnbanUserRequest,
        admin_id: str,
        ip_address: str,
        log_action: Any,
    ) -> AdminUserDetail:
        """解封用户。

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 解封请求
            admin_id: 操作管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            更新后的用户详情

        Raises:
            AppError: 用户不存在或未被封禁时抛出
        """
        user = await self._get_user_by_id(db, user_id)

        # 检查是否被封禁
        if not user.is_banned:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="用户未被封禁",
                status_code=400,
            )

        # 更新用户状态
        user.is_banned = False
        user.ban_reason = None
        user.ban_until = None

        # 记录操作日志（关键操作使用同步写入确保审计日志不丢失）
        # 使用 auto_commit=False 确保日志和用户状态更新在同一事务中
        await log_action(
            db=db,
            admin_id=admin_id,
            action="unban_user",
            target_type="user",
            target_id=user_id,
            details={
                "reason": request.reason,
                "notify_user": request.notify_user,
            },
            ip_address=ip_address,
            auto_commit=False,
        )

        # 统一提交事务，确保用户状态更新和日志记录的原子性
        await db.commit()

        logger.info("用户已解封: user_id=%s, reason=%s", user_id, request.reason)

        # TODO: 发送通知给用户
        if request.notify_user:
            pass  # 后续实现通知推送

        return await self.get_user_detail(db, user_id)

    # -----------------------------------------------------------------------
    # 青少年模式管理
    # -----------------------------------------------------------------------

    async def set_minor_mode(
        self,
        db: AsyncSession,
        user_id: UUID | str,
        request: AdminMinorModeRequest,
        admin_id: str,
        ip_address: str,
        log_action: Any,
    ) -> AdminUserDetail:
        """设置青少年模式。

        Args:
            db: 数据库会话
            user_id: 用户ID
            request: 青少年模式设置请求
            admin_id: 操作管理员ID
            ip_address: 操作IP
            log_action: 审计日志记录函数

        Returns:
            更新后的用户详情
        """
        user = await self._get_user_by_id(db, user_id)

        old_is_minor = user.is_minor
        old_guardian_phone = user.guardian_phone

        # 更新用户状态
        user.is_minor = request.is_minor
        user.guardian_phone = request.guardian_phone

        # 记录操作日志（关键操作使用同步写入确保审计日志不丢失）
        # 使用 auto_commit=False 确保日志和用户状态更新在同一事务中
        await log_action(
            db=db,
            admin_id=admin_id,
            action="set_minor_mode",
            target_type="user",
            target_id=user_id,
            details={
                "old_is_minor": old_is_minor,
                "new_is_minor": request.is_minor,
                "old_guardian_phone": self._mask_phone(old_guardian_phone) if old_guardian_phone else None,
                "new_guardian_phone": self._mask_phone(request.guardian_phone) if request.guardian_phone else None,
            },
            ip_address=ip_address,
            auto_commit=False,
        )

        # 统一提交事务，确保用户状态更新和日志记录的原子性
        await db.commit()

        logger.info("设置青少年模式: user_id=%s, is_minor=%s", user_id, request.is_minor)

        return await self.get_user_detail(db, user_id)

    # -----------------------------------------------------------------------
    # 用户日记统计
    # -----------------------------------------------------------------------

    async def get_user_diary_stats(
        self,
        db: AsyncSession,
        user_id: UUID | str,
    ) -> AdminUserDiaryStats:
        """获取用户日记统计。

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户日记统计
        """
        # 验证用户存在
        await self._get_user_by_id(db, user_id)

        # 计算本月开始时间
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        # 计算最近7天开始时间
        week_ago = now - timedelta(days=7)

        # 查询日记总数
        total_stmt = select(func.count()).select_from(EmotionDiary).where(
            EmotionDiary.user_id == user_id,
            EmotionDiary.deleted_at.is_(None),
        )
        total_result = await db.execute(total_stmt)
        total_count = total_result.scalar() or 0

        # 查询本月日记数
        month_stmt = select(func.count()).select_from(EmotionDiary).where(
            EmotionDiary.user_id == user_id,
            EmotionDiary.deleted_at.is_(None),
            EmotionDiary.created_at >= month_start,
        )
        month_result = await db.execute(month_stmt)
        this_month_count = month_result.scalar() or 0

        # 查询情绪基调分布
        emotion_stmt = (
            select(
                EmotionDiary.emotion_tone,
                func.count().label("count"),
            )
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
                EmotionDiary.emotion_tone.isnot(None),
            )
            .group_by(EmotionDiary.emotion_tone)
        )
        emotion_result = await db.execute(emotion_stmt)
        emotion_distribution = {
            row.emotion_tone or "unknown": row.count
            for row in emotion_result.all()
        }

        # 查询最近7天情绪标签
        recent_emotion_stmt = (
            select(EmotionDiary.emotion_labels)
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
                EmotionDiary.created_at >= week_ago,
                EmotionDiary.emotion_labels.isnot(None),
            )
            .order_by(desc(EmotionDiary.created_at))
            .limit(10)
        )
        recent_result = await db.execute(recent_emotion_stmt)
        recent_emotions_set = set()
        for row in recent_result.scalars().all():
            if row:
                recent_emotions_set.update(row)
        recent_emotions = list(recent_emotions_set)[:20]  # 限制返回数量

        return AdminUserDiaryStats(
            total_count=total_count,
            this_month_count=this_month_count,
            emotion_distribution=emotion_distribution,
            recent_emotions=recent_emotions,
        )

    # -----------------------------------------------------------------------
    # 用户社交数据统计
    # -----------------------------------------------------------------------

    async def get_user_social_stats(
        self,
        db: AsyncSession,
        user_id: UUID | str,
    ) -> AdminUserSocialStats:
        """获取用户社交数据统计。

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户社交数据统计
        """
        # 验证用户存在
        await self._get_user_by_id(db, user_id)

        # 查询好友数（统计 user_id_1 或 user_id_2 是该用户的已接受好友关系）
        friend_stmt = select(func.count()).select_from(Friendship).where(
            and_(
                or_(
                    Friendship.user_id_1 == user_id,
                    Friendship.user_id_2 == user_id,
                ),
                Friendship.status == "accepted",
            )
        )
        friend_result = await db.execute(friend_stmt)
        friend_count = friend_result.scalar() or 0

        # 查询动态数
        post_stmt = select(func.count()).select_from(Post).where(
            Post.user_id == user_id,
            Post.deleted_at.is_(None),
        )
        post_result = await db.execute(post_stmt)
        post_count = post_result.scalar() or 0

        # 查询树洞帖子数（直接通过 user_id 关联）
        treehole_stmt = select(func.count()).select_from(TreeholePost).where(
            TreeholePost.user_id == user_id,
            TreeholePost.deleted_at.is_(None),
        )
        treehole_result = await db.execute(treehole_stmt)
        treehole_count = treehole_result.scalar() or 0

        # 查询评论数（树洞评论 - 通过 user_id 直接关联）
        comment_stmt = select(func.count()).select_from(TreeholeComment).where(
            TreeholeComment.user_id == user_id,
            TreeholeComment.deleted_at.is_(None),
        )
        comment_result = await db.execute(comment_stmt)
        comment_count = comment_result.scalar() or 0

        return AdminUserSocialStats(
            friend_count=friend_count,
            post_count=post_count,
            treehole_count=treehole_count,
            comment_count=comment_count,
        )

    # -----------------------------------------------------------------------
    # 工具方法
    # -----------------------------------------------------------------------

    @staticmethod
    def _mask_phone(phone: str | None) -> str | None:
        """手机号脱敏处理。

        显示前3位和后4位，中间用 * 替代。
        如：13812345678 -> 138****5678
        """
        if not phone or len(phone) < 7:
            return phone
        return f"{phone[:3]}****{phone[-4:]}"
