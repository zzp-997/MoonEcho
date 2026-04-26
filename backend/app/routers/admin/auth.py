"""管理员认证路由模块。

提供管理后台认证相关的 API 端点：
- POST /api/admin/v1/auth/login     管理员登录
- POST /api/admin/v1/auth/refresh   刷新 token
- POST /api/admin/v1/auth/logout    登出
- GET  /api/admin/v1/auth/me        当前管理员信息
- POST /api/admin/v1/auth/check-permission 权限检查
"""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.middleware.admin_auth import (
    CurrentAdmin,
    get_client_ip,
    get_user_agent,
    _get_admin_auth_service,
)
from app.models.admin import Admin
from app.schemas.admin import (
    AdminLoginRequest,
    AdminRefreshTokenRequest,
    PermissionCheckRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/auth", tags=["admin-auth"])


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
# POST /api/admin/v1/auth/login — 管理员登录
# ---------------------------------------------------------------------------

@router.post("/login", summary="管理员登录")
async def admin_login(
    body: AdminLoginRequest,
    request: Request,
    auth_service: Any = Depends(_get_admin_auth_service),
    db: AsyncSession = Depends(_get_db),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
) -> dict[str, Any]:
    """管理员登录。

    - 用户名 + 密码登录
    - 连续 5 次错误锁定 30 分钟
    - access_token 有效期 2 小时
    - refresh_token 有效期 7 天
    - 与 C 端用户 Token 隔离（使用不同的 JWT secret/issuer）
    """
    request_id = getattr(request.state, "request_id", "")
    result = await auth_service.login(
        request=body,
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/auth/refresh — 刷新 Token
# ---------------------------------------------------------------------------

@router.post("/refresh", summary="刷新Token")
async def admin_refresh_token(
    body: AdminRefreshTokenRequest,
    request: Request,
    auth_service: Any = Depends(_get_admin_auth_service),
) -> dict[str, Any]:
    """刷新管理员 JWT Token。

    - 使用 refresh_token 获取新的 token 对
    - refresh_token 有效期 7 天
    - 新的 access_token 有效期 2 小时
    - 旧的 refresh_token 会被加入黑名单
    """
    request_id = getattr(request.state, "request_id", "")
    result = await auth_service.refresh_token(body)
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/auth/logout — 登出
# ---------------------------------------------------------------------------

@router.post("/logout", summary="管理员登出")
async def admin_logout(
    admin: CurrentAdmin,
    request: Request,
    auth_service: Any = Depends(_get_admin_auth_service),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
) -> dict[str, Any]:
    """管理员登出。

    - 将当前 access_token 加入黑名单
    - 黑名单有效期为 Token 剩余有效期
    - 需要登录（Bearer Token）
    - 记录登出日志
    """
    request_id = getattr(request.state, "request_id", "")
    access_token = getattr(request.state, "admin_access_token", "")
    await auth_service.logout(
        admin_id=admin.id,
        access_token=access_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return success_response({"message": "登出成功"}, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/auth/me — 获取当前管理员信息
# ---------------------------------------------------------------------------

@router.get("/me", summary="获取当前管理员信息")
async def get_admin_me(
    admin: CurrentAdmin,
    request: Request,
    auth_service: Any = Depends(_get_admin_auth_service),
) -> dict[str, Any]:
    """获取当前登录管理员信息。

    - 返回管理员基本信息
    - 返回角色和权限列表
    - 返回最后登录时间和 IP
    - 需要登录（Bearer Token）
    """
    request_id = getattr(request.state, "request_id", "")
    result = await auth_service.get_current_admin_info(admin)
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/auth/check-permission — 权限检查
# ---------------------------------------------------------------------------

@router.post("/check-permission", summary="权限检查")
async def check_permission(
    body: PermissionCheckRequest,
    admin: CurrentAdmin,
    request: Request,
    auth_service: Any = Depends(_get_admin_auth_service),
) -> dict[str, Any]:
    """检查当前管理员是否拥有指定权限。

    - 输入权限节点（如 user:ban）
    - 返回是否拥有该权限
    - 需要登录（Bearer Token）
    """
    request_id = getattr(request.state, "request_id", "")
    result = await auth_service.check_permission(admin, body)
    return success_response(result, request_id)