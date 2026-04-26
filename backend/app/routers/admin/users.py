"""用户管理路由模块。

提供管理后台用户管理相关的 API 端点：
- GET  /api/admin/v1/users           用户列表
- GET  /api/admin/v1/users/:id       用户详情
- POST /api/admin/v1/users/:id/ban   封禁用户
- POST /api/admin/v1/users/:id/unban 解封用户
- GET  /api/admin/v1/users/:id/diaries 用户日记统计
- GET  /api/admin/v1/users/:id/social  用户社交数据
- PUT  /api/admin/v1/users/:id/minor   设置青少年模式
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import paginated_response, success_response
from app.middleware.admin_auth import (
    ClientIP,
    CurrentAdmin,
    get_client_ip,
    require_permission,
)
from app.models.admin import Admin
from app.schemas.admin import (
    AdminBanUserRequest,
    AdminMinorModeRequest,
    AdminUnbanUserRequest,
    AdminUserDetail,
    AdminUserDiaryStats,
    AdminUserListRequest,
    AdminUserSocialStats,
)
from app.services.admin.admin_log_service import AdminLogService
from app.services.admin.user_service import AdminUserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/users", tags=["admin-users"])


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

async def _get_user_service(request: Request) -> AdminUserService:
    """从应用状态获取用户管理服务实例。"""
    redis = request.app.state.redis
    return AdminUserService(redis)


async def _get_log_service(request: Request) -> AdminLogService:
    """从应用状态获取审计日志服务实例。"""
    redis = request.app.state.redis
    return AdminLogService(redis)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/users — 用户列表
# ---------------------------------------------------------------------------

@router.get("", summary="用户列表")
async def get_users(
    request: Request,
    admin: Admin = require_permission("user:view"),
    db: AsyncSession = Depends(_get_db),
    user_service: AdminUserService = Depends(_get_user_service),
) -> dict[str, Any]:
    """查询用户列表。

    支持以下功能：
    - 搜索：昵称/手机号模糊匹配
    - 筛选：年龄段、注册时间、青少年模式、封禁状态
    - 分页：page, page_size
    - 排序：created_at（注册时间）、last_active_at（最后活跃时间）

    权限要求：user:view
    """
    request_id = getattr(request.state, "request_id", "")

    # 解析查询参数
    params = AdminUserListRequest(
        page=int(request.query_params.get("page", 1)),
        page_size=int(request.query_params.get("page_size", 20)),
        search=request.query_params.get("search"),
        age_range=request.query_params.get("age_range"),
        is_minor=request.query_params.get("is_minor") == "true" if request.query_params.get("is_minor") else None,
        is_banned=request.query_params.get("is_banned") == "true" if request.query_params.get("is_banned") else None,
        sort_by=request.query_params.get("sort_by", "created_at"),
        sort_order=request.query_params.get("sort_order", "desc"),
    )

    # 处理时间参数（ISO 格式字符串转 datetime）
    register_start = request.query_params.get("register_start")
    register_end = request.query_params.get("register_end")
    if register_start:
        params.register_start = datetime.fromisoformat(register_start.replace("Z", "+00:00"))
    if register_end:
        params.register_end = datetime.fromisoformat(register_end.replace("Z", "+00:00"))

    # 查询用户列表
    result = await user_service.get_users(
        db=db,
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        age_range=params.age_range,
        is_minor=params.is_minor,
        is_banned=params.is_banned,
        register_start=params.register_start,
        register_end=params.register_end,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
    )

    return paginated_response(
        data=[item.model_dump() for item in result.data],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# GET /api/admin/v1/users/:id — 用户详情
# ---------------------------------------------------------------------------

@router.get("/{user_id}", summary="用户详情")
async def get_user_detail(
    user_id: uuid.UUID,
    request: Request,
    admin: Admin = require_permission("user:view"),
    db: AsyncSession = Depends(_get_db),
    user_service: AdminUserService = Depends(_get_user_service),
) -> dict[str, Any]:
    """获取用户详情。

    返回用户基本信息，包括：
    - 账号信息：手机号（脱敏）、昵称、头像
    - 画像信息：年龄段、城市、职业
    - 状态信息：青少年模式、封禁状态
    - 统计信息：社交能量值、注册时间、最后活跃时间

    权限要求：user:view
    """
    request_id = getattr(request.state, "request_id", "")
    result = await user_service.get_user_detail(db, user_id)
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/users/:id/ban — 封禁用户
# ---------------------------------------------------------------------------

@router.post("/{user_id}/ban", summary="封禁用户")
async def ban_user(
    user_id: uuid.UUID,
    body: AdminBanUserRequest,
    request: Request,
    admin: Admin = require_permission("user:ban"),
    db: AsyncSession = Depends(_get_db),
    user_service: AdminUserService = Depends(_get_user_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """封禁用户。

    请求体参数：
    - reason: 封禁原因（必填，5-500字）
    - duration_days: 封禁天数（可选，null 表示永久封禁）
    - notify_user: 是否通知用户（默认 true）

    权限要求：user:ban
    """
    request_id = getattr(request.state, "request_id", "")

    result = await user_service.ban_user(
        db=db,
        user_id=user_id,
        request=body,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/users/:id/unban — 解封用户
# ---------------------------------------------------------------------------

@router.post("/{user_id}/unban", summary="解封用户")
async def unban_user(
    user_id: uuid.UUID,
    body: AdminUnbanUserRequest,
    request: Request,
    admin: Admin = require_permission("user:ban"),
    db: AsyncSession = Depends(_get_db),
    user_service: AdminUserService = Depends(_get_user_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """解封用户。

    请求体参数：
    - reason: 解封原因（必填，5-500字）
    - notify_user: 是否通知用户（默认 true）

    权限要求：user:ban
    """
    request_id = getattr(request.state, "request_id", "")

    result = await user_service.unban_user(
        db=db,
        user_id=user_id,
        request=body,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/users/:id/diaries — 用户日记统计
# ---------------------------------------------------------------------------

@router.get("/{user_id}/diaries", summary="用户日记统计")
async def get_user_diary_stats(
    user_id: uuid.UUID,
    request: Request,
    admin: Admin = require_permission("user:view"),
    db: AsyncSession = Depends(_get_db),
    user_service: AdminUserService = Depends(_get_user_service),
) -> dict[str, Any]:
    """获取用户日记统计。

    返回：
    - total_count: 日记总数
    - this_month_count: 本月日记数
    - emotion_distribution: 情绪基调分布
    - recent_emotions: 最近7天情绪标签

    权限要求：user:view
    """
    request_id = getattr(request.state, "request_id", "")
    result = await user_service.get_user_diary_stats(db, user_id)
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/users/:id/social — 用户社交数据
# ---------------------------------------------------------------------------

@router.get("/{user_id}/social", summary="用户社交数据")
async def get_user_social_stats(
    user_id: uuid.UUID,
    request: Request,
    admin: Admin = require_permission("user:view"),
    db: AsyncSession = Depends(_get_db),
    user_service: AdminUserService = Depends(_get_user_service),
) -> dict[str, Any]:
    """获取用户社交数据统计。

    返回：
    - friend_count: 好友数
    - post_count: 动态数
    - treehole_count: 树洞帖子数
    - comment_count: 评论数

    权限要求：user:view
    """
    request_id = getattr(request.state, "request_id", "")
    result = await user_service.get_user_social_stats(db, user_id)
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# PUT /api/admin/v1/users/:id/minor — 设置青少年模式
# ---------------------------------------------------------------------------

@router.put("/{user_id}/minor", summary="设置青少年模式")
async def set_minor_mode(
    user_id: uuid.UUID,
    body: AdminMinorModeRequest,
    request: Request,
    admin: Admin = require_permission("user:ban"),
    db: AsyncSession = Depends(_get_db),
    user_service: AdminUserService = Depends(_get_user_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """设置青少年模式。

    请求体参数：
    - is_minor: 是否开启青少年模式
    - guardian_phone: 监护人手机号（开启时必填）

    权限要求：user:ban
    """
    request_id = getattr(request.state, "request_id", "")

    result = await user_service.set_minor_mode(
        db=db,
        user_id=user_id,
        request=body,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    return success_response(result, request_id)
