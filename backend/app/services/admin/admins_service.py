"""管理员管理服务模块。

提供管理员 CRUD 相关的业务逻辑：
- 管理员列表查询
- 管理员创建（含密码哈希）
- 管理员详情查询
- 管理员信息更新
- 管理员删除（软删除）
- 角色列表查询
- 操作日志查询
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.admin import Admin, AdminLog
from app.schemas.admin import (
    ADMIN_ROLES,
    ROLE_DESCRIPTIONS,
    ROLE_DISPLAY_NAMES,
    ROLE_PERMISSIONS,
    AdminCreateRequest,
    AdminDetailResponse,
    AdminListItem,
    AdminLogListRequest,
    AdminLogResponse,
    AdminUpdateRequest,
    RoleListItem,
)
from app.schemas.base import PaginatedResponse
from app.services.admin.admin_log_service import AdminLogService
from app.services.admin.admin_service import AdminAuthService

logger = logging.getLogger(__name__)


class AdminsService:
    """管理员管理服务。

    依赖外部注入：
    - redis: Redis 客户端
    """

    def __init__(self, redis: Any) -> None:
        self._redis = redis
        self._log_service = AdminLogService(redis)

    # ---------------------------------------------------------------------------
    # 管理员列表
    # ---------------------------------------------------------------------------

    async def get_admins(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> PaginatedResponse[AdminListItem]:
        """查询管理员列表。

        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页条数
            search: 搜索关键词（用户名/昵称）
            role: 角色筛选
            is_active: 状态筛选
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            PaginatedResponse[AdminListItem]: 分页管理员列表
        """
        # 构建查询条件
        stmt = select(Admin).where(Admin.is_active == True)  # noqa: E712

        if search:
            stmt = stmt.where(
                or_(
                    Admin.username.ilike(f"%{search}%"),
                    Admin.nickname.ilike(f"%{search}%"),
                )
            )

        if role:
            stmt = stmt.where(Admin.role == role)

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 排序
        order_col = getattr(Admin, sort_by, Admin.created_at)
        if sort_order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)

        # 分页
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(stmt)
        admins = result.scalars().all()

        # 转换为响应模型
        data = [
            AdminListItem(
                id=admin.id,
                username=admin.username,
                nickname=admin.nickname,
                role=admin.role,
                is_active=admin.is_active,
                last_login_at=admin.last_login_at,
                last_login_ip=admin.last_login_ip,
                created_at=admin.created_at,
            )
            for admin in admins
        ]

        return PaginatedResponse.create(
            data=data,
            page=page,
            page_size=page_size,
            total=total,
        )

    # ---------------------------------------------------------------------------
    # 创建管理员
    # ---------------------------------------------------------------------------

    async def create_admin(
        self,
        db: AsyncSession,
        request: AdminCreateRequest,
        operator_id: str,
        ip_address: str,
        user_agent: str,
    ) -> AdminDetailResponse:
        """创建管理员。

        Args:
            db: 数据库会话
            request: 创建请求
            operator_id: 操作者ID
            ip_address: 客户端IP
            user_agent: 客户端UA

        Returns:
            AdminDetailResponse: 创建的管理员详情

        Raises:
            AppError: 用户名已存在时抛出
        """
        # 检查用户名是否已存在
        existing = await db.execute(
            select(Admin).where(Admin.username == request.username)
        )
        if existing.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.ADMIN_USERNAME_EXISTS,
                message=f"用户名 '{request.username}' 已存在",
                status_code=400,
            )

        # 哈希密码
        password_hash = AdminAuthService.hash_password(request.password)

        # 创建管理员
        admin = Admin(
            id=uuid4().hex,
            username=request.username,
            password_hash=password_hash,
            nickname=request.nickname,
            role=request.role,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        # 记录操作日志
        await self._log_service.log_action_sync(
            db=db,
            admin_id=operator_id,
            action="admin_create",
            target_type="admin",
            target_id=admin.id,
            details={
                "username": admin.username,
                "role": admin.role,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info("创建管理员成功: username=%s, role=%s", admin.username, admin.role)

        return AdminDetailResponse(
            id=admin.id,
            username=admin.username,
            nickname=admin.nickname,
            role=admin.role,
            permissions=ROLE_PERMISSIONS.get(admin.role, []),
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            last_login_ip=admin.last_login_ip,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
        )

    # ---------------------------------------------------------------------------
    # 管理员详情
    # ---------------------------------------------------------------------------

    async def get_admin_detail(
        self,
        db: AsyncSession,
        admin_id: str,
    ) -> AdminDetailResponse:
        """获取管理员详情。

        Args:
            db: 数据库会话
            admin_id: 管理员ID

        Returns:
            AdminDetailResponse: 管理员详情

        Raises:
            AppError: 管理员不存在时抛出
        """
        stmt = select(Admin).where(Admin.id == admin_id)
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin is None:
            raise AppError(
                code=ErrorCode.ADMIN_NOT_FOUND,
                message="管理员不存在",
                status_code=404,
            )

        return AdminDetailResponse(
            id=admin.id,
            username=admin.username,
            nickname=admin.nickname,
            role=admin.role,
            permissions=ROLE_PERMISSIONS.get(admin.role, []),
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            last_login_ip=admin.last_login_ip,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
        )

    # ---------------------------------------------------------------------------
    # 更新管理员
    # ---------------------------------------------------------------------------

    async def update_admin(
        self,
        db: AsyncSession,
        admin_id: str,
        request: AdminUpdateRequest,
        operator_id: str,
        ip_address: str,
        user_agent: str,
    ) -> AdminDetailResponse:
        """更新管理员信息。

        Args:
            db: 数据库会话
            admin_id: 管理员ID
            request: 更新请求
            operator_id: 操作者ID
            ip_address: 客户端IP
            user_agent: 客户端UA

        Returns:
            AdminDetailResponse: 更新后的管理员详情

        Raises:
            AppError: 管理员不存在或无权修改时抛出
        """
        # 查询管理员
        stmt = select(Admin).where(Admin.id == admin_id)
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin is None:
            raise AppError(
                code=ErrorCode.ADMIN_NOT_FOUND,
                message="管理员不存在",
                status_code=404,
            )

        # 记录变更详情
        changes = {}

        # 更新昵称
        if request.nickname is not None:
            changes["nickname"] = {"old": admin.nickname, "new": request.nickname}
            admin.nickname = request.nickname

        # 更新角色（不能修改超级管理员的角色）
        if request.role is not None and admin.role != "super_admin":
            if admin.role != request.role:
                changes["role"] = {"old": admin.role, "new": request.role}
                admin.role = request.role

        # 更新状态
        if request.is_active is not None:
            if admin.is_active != request.is_active:
                changes["is_active"] = {"old": admin.is_active, "new": request.is_active}
                admin.is_active = request.is_active

        # 更新密码
        if request.password:
            password_hash = AdminAuthService.hash_password(request.password)
            changes["password"] = "已更新"
            admin.password_hash = password_hash

        # 保存变更
        if changes:
            admin.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(admin)

            # 记录操作日志
            await self._log_service.log_action_sync(
                db=db,
                admin_id=operator_id,
                action="admin_update",
                target_type="admin",
                target_id=admin.id,
                details={
                    "username": admin.username,
                    "changes": changes,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info("更新管理员成功: username=%s, changes=%s", admin.username, changes)

        return AdminDetailResponse(
            id=admin.id,
            username=admin.username,
            nickname=admin.nickname,
            role=admin.role,
            permissions=ROLE_PERMISSIONS.get(admin.role, []),
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            last_login_ip=admin.last_login_ip,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
        )

    # ---------------------------------------------------------------------------
    # 删除管理员
    # ---------------------------------------------------------------------------

    async def delete_admin(
        self,
        db: AsyncSession,
        admin_id: str,
        operator_id: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """删除管理员（软删除）。

        Args:
            db: 数据库会话
            admin_id: 管理员ID
            operator_id: 操作者ID
            ip_address: 客户端IP
            user_agent: 客户端UA

        Raises:
            AppError: 管理员不存在、不能删除自己、不能删除超级管理员时抛出
        """
        # 不能删除自己
        if admin_id == operator_id:
            raise AppError(
                code=ErrorCode.ADMIN_CANNOT_DELETE_SELF,
                message="不能删除自己的账号",
                status_code=400,
            )

        # 查询管理员
        stmt = select(Admin).where(Admin.id == admin_id)
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin is None:
            raise AppError(
                code=ErrorCode.ADMIN_NOT_FOUND,
                message="管理员不存在",
                status_code=404,
            )

        # 不能删除超级管理员
        if admin.role == "super_admin":
            raise AppError(
                code=ErrorCode.ADMIN_CANNOT_MODIFY_SUPER_ADMIN,
                message="不能删除超级管理员",
                status_code=403,
            )

        # 软删除（设置 is_active = False）
        admin.is_active = False
        admin.updated_at = datetime.now(timezone.utc)
        await db.commit()

        # 记录操作日志
        await self._log_service.log_action_sync(
            db=db,
            admin_id=operator_id,
            action="admin_delete",
            target_type="admin",
            target_id=admin.id,
            details={
                "username": admin.username,
                "role": admin.role,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info("删除管理员成功: username=%s", admin.username)

    # ---------------------------------------------------------------------------
    # 角色列表
    # ---------------------------------------------------------------------------

    async def get_roles(self) -> list[RoleListItem]:
        """获取角色列表。

        Returns:
            list[RoleListItem]: 角色列表
        """
        roles = []
        for role_name in ADMIN_ROLES:
            roles.append(RoleListItem(
                name=role_name,
                display_name=ROLE_DISPLAY_NAMES.get(role_name, role_name),
                permissions=ROLE_PERMISSIONS.get(role_name, []),
                description=ROLE_DESCRIPTIONS.get(role_name),
            ))
        return roles

    # ---------------------------------------------------------------------------
    # 操作日志列表
    # ---------------------------------------------------------------------------

    async def get_logs(
        self,
        db: AsyncSession,
        params: AdminLogListRequest,
    ) -> PaginatedResponse[AdminLogResponse]:
        """查询操作日志列表。

        Args:
            db: 数据库会话
            params: 查询参数

        Returns:
            PaginatedResponse[AdminLogResponse]: 分页日志列表
        """
        return await self._log_service.get_logs(
            db=db,
            page=params.page,
            page_size=params.page_size,
            admin_id=params.admin_id,
            action=params.action,
            target_type=params.target_type,
            start_time=params.start_time,
            end_time=params.end_time,
        )
