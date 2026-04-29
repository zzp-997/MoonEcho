"""管理员管理路由模块。

提供管理后台管理员管理相关的 API 端点：
- GET    /api/admin/v1/admins      管理员列表
- POST   /api/admin/v1/admins      创建管理员
- GET    /api/admin/v1/admins/:id  管理员详情
- PATCH  /api/admin/v1/admins/:id  更新管理员
- DELETE /api/admin/v1/admins/:id  删除管理员
- GET    /api/admin/v1/roles       角色列表
- GET    /api/admin/v1/admin-logs   操作日志列表
"""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import paginated_response, success_response
from app.middleware.admin_auth import (
    get_client_ip,
    get_user_agent,
    require_permission,
)
from app.models.admin import Admin
from app.schemas.admin import (
    AdminCreateRequest,
    AdminLogListRequest,
    AdminUpdateRequest,
)
from app.services.admin.admin_log_service import AdminLogService
from app.services.admin.admins_service import AdminsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/admins", tags=["admin-admins"])


# ---------------------------------------------------------------------------
# 依赖注入：获取数据库会话
# ---------------------------------------------------------------------------

async def _get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """从请求状态获取数据库会话。

    返回异步上下文管理器，确保会话自动关闭。
    """
    async_session_factory = request.app.state.async_session_factory
    async with async_session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# 依赖注入：获取服务实例
# ---------------------------------------------------------------------------

async def _get_admins_service(request: Request) -> AdminsService:
    """从应用状态获取管理员管理服务实例。"""
    redis = request.app.state.redis
    return AdminsService(redis)


async def _get_log_service(request: Request) -> AdminLogService:
    """从应用状态获取审计日志服务实例。"""
    redis = request.app.state.redis
    return AdminLogService(redis)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/admins — 管理员列表
# ---------------------------------------------------------------------------

@router.get("", summary="管理员列表")
async def get_admins(
    request: Request,
    admin: Admin = require_permission("admin:view"),
    db: AsyncSession = Depends(_get_db),
    admins_service: AdminsService = Depends(_get_admins_service),
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """查询管理员列表。

    支持以下功能：
    - 搜索：用户名/昵称模糊匹配
    - 筛选：角色、状态
    - 分页：page, page_size
    - 排序：created_at（创建时间）、last_login_at（最后登录时间）、username

    权限要求：admin:view
    """
    request_id = getattr(request.state, "request_id", "")

    result = await admins_service.get_admins(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return paginated_response(
        data=[item.model_dump() for item in result.data],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# POST /api/admin/v1/admins — 创建管理员
# ---------------------------------------------------------------------------

@router.post("", summary="创建管理员")
async def create_admin(
    body: AdminCreateRequest,
    request: Request,
    admin: Admin = require_permission("admin:create"),
    db: AsyncSession = Depends(_get_db),
    admins_service: AdminsService = Depends(_get_admins_service),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
) -> dict[str, Any]:
    """创建新管理员账号。

    请求体参数：
    - username: 用户名（3-50字符，字母数字下划线连字符）
    - password: 密码（至少8位，包含字母和数字）
    - nickname: 昵称（可选）
    - role: 角色（super_admin/admin/operator，默认 operator）

    权限要求：admin:create
    """
    request_id = getattr(request.state, "request_id", "")

    result = await admins_service.create_admin(
        db=db,
        request=body,
        operator_id=admin.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info(
        "管理员创建成功: username=%s, operator=%s",
        body.username,
        admin.username,
    )

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/admins/:id — 管理员详情
# ---------------------------------------------------------------------------

@router.get("/{admin_id}", summary="管理员详情")
async def get_admin_detail(
    admin_id: str,
    request: Request,
    admin: Admin = require_permission("admin:view"),
    db: AsyncSession = Depends(_get_db),
    admins_service: AdminsService = Depends(_get_admins_service),
) -> dict[str, Any]:
    """获取管理员详情。

    返回：
    - 基本信息：用户名、昵称、角色
    - 权限列表：该角色拥有的权限节点
    - 状态信息：是否启用、最后登录时间和IP
    - 时间信息：创建时间、更新时间

    权限要求：admin:view
    """
    request_id = getattr(request.state, "request_id", "")

    result = await admins_service.get_admin_detail(db, admin_id)

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# PATCH /api/admin/v1/admins/:id — 更新管理员
# ---------------------------------------------------------------------------

@router.patch("/{admin_id}", summary="更新管理员信息")
async def update_admin(
    admin_id: str,
    body: AdminUpdateRequest,
    request: Request,
    admin: Admin = require_permission("admin:update"),
    db: AsyncSession = Depends(_get_db),
    admins_service: AdminsService = Depends(_get_admins_service),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
) -> dict[str, Any]:
    """更新管理员信息。

    请求体参数（均为可选）：
    - nickname: 昵称
    - role: 角色（不能修改超级管理员的角色）
    - is_active: 是否启用
    - password: 新密码（至少8位，包含字母和数字）

    注意：
    - 不能修改自己的角色和状态
    - 不能修改超级管理员的角色

    权限要求：admin:update
    """
    request_id = getattr(request.state, "request_id", "")

    result = await admins_service.update_admin(
        db=db,
        admin_id=admin_id,
        request=body,
        operator_id=admin.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info(
        "管理员更新成功: admin_id=%s, operator=%s",
        admin_id,
        admin.username,
    )

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# DELETE /api/admin/v1/admins/:id — 删除管理员
# ---------------------------------------------------------------------------

@router.delete("/{admin_id}", summary="删除管理员")
async def delete_admin(
    admin_id: str,
    request: Request,
    admin: Admin = require_permission("admin:delete"),
    db: AsyncSession = Depends(_get_db),
    admins_service: AdminsService = Depends(_get_admins_service),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
) -> dict[str, Any]:
    """删除管理员（软删除）。

    注意：
    - 不能删除自己的账号
    - 不能删除超级管理员

    权限要求：admin:delete
    """
    request_id = getattr(request.state, "request_id", "")

    await admins_service.delete_admin(
        db=db,
        admin_id=admin_id,
        operator_id=admin.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info(
        "管理员删除成功: admin_id=%s, operator=%s",
        admin_id,
        admin.username,
    )

    return success_response({"message": "删除成功"}, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/roles — 角色列表
# ---------------------------------------------------------------------------

@router.get("/roles", summary="角色列表")
async def get_roles(
    request: Request,
    admin: Admin = require_permission("admin:view"),
    admins_service: AdminsService = Depends(_get_admins_service),
) -> dict[str, Any]:
    """获取角色列表。

    返回所有可用角色及其权限说明：
    - super_admin: 超级管理员，拥有全部权限
    - admin: 管理员，拥有大部分权限
    - operator: 运营人员，拥有基础权限

    权限要求：admin:view
    """
    request_id = getattr(request.state, "request_id", "")

    result = await admins_service.get_roles()

    return success_response({"roles": result}, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/admin-logs — 操作日志列表
# ---------------------------------------------------------------------------

@router.get("/logs", summary="操作日志列表")
async def get_admin_logs(
    request: Request,
    admin: Admin = require_permission("log:view"),
    db: AsyncSession = Depends(_get_db),
    admins_service: AdminsService = Depends(_get_admins_service),
    page: int = 1,
    page_size: int = 20,
    admin_id: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    """查询操作日志列表。

    支持以下筛选条件：
    - admin_id: 管理员ID
    - action: 操作类型（login/logout/create/update/delete/export等）
    - target_type: 操作对象类型（user/post/comment/report等）
    - start_time: 开始时间（ISO格式）
    - end_time: 结束时间（ISO格式）

    分页：
    - page: 页码
    - page_size: 每页条数（最大100）

    权限要求：log:view
    """
    request_id = getattr(request.state, "request_id", "")

    # 处理时间参数
    from datetime import datetime as dt

    start_datetime = None
    end_datetime = None

    if start_time:
        try:
            start_datetime = dt.fromisoformat(start_time.replace("Z", "+00:00"))
        except ValueError:
            pass

    if end_time:
        try:
            end_datetime = dt.fromisoformat(end_time.replace("Z", "+00:00"))
        except ValueError:
            pass

    params = AdminLogListRequest(
        page=page,
        page_size=page_size,
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        start_time=start_datetime,
        end_time=end_datetime,
    )

    result = await admins_service.get_logs(db, params)

    return paginated_response(
        data=[item.model_dump() for item in result.data],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        request_id=request_id,
    )
