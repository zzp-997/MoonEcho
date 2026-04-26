"""管理端危机干预路由模块。

提供管理后台危机干预相关的 API 端点：
- GET  /api/admin/v1/crisis/list      危机事件列表
- GET  /api/admin/v1/crisis/:id       危机事件详情
- POST /api/admin/v1/crisis/:id/resolve 处理危机事件
- POST /api/admin/v1/crisis/:id/intervene 标记人工介入

"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import paginated_response, success_response
from app.middleware.admin_auth import (
    CurrentAdmin,
    get_client_ip,
    require_permission,
)
from app.models.admin import Admin
from app.schemas.report import (
    AdminCrisisDetail,
    AdminCrisisListRequest,
    AdminCrisisResolveRequest,
    AdminCrisisResolveResponse,
)
from app.services.admin.admin_log_service import AdminLogService
from app.services.admin.crisis_service import AdminCrisisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/crisis", tags=["admin-crisis"])


def parse_datetime_safe(datetime_str: str | None) -> datetime | None:
    """安全解析时间字符串，避免异常。

    Args:
        datetime_str: 时间字符串

    Returns:
        datetime 对象，解析失败返回 None

    Raises:
        HTTPException: 时间格式无效时抛出 400 错误
    """
    if not datetime_str:
        return None

    try:
        # 处理 ISO 格式时间，支持多种格式
        # 替换 Z 为 UTC 时区标识
        normalized = datetime_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        # 尝试其他常见格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue

        raise HTTPException(
            status_code=400,
            detail=f"时间格式无效: {datetime_str}，请使用 ISO 8601 格式（如 2024-01-01T00:00:00Z）",
        )


# ---------------------------------------------------------------------------
# 依赖注入：获取数据库会话
# ---------------------------------------------------------------------------

async def _get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """从请求状态获取数据库会话。"""
    async_session_factory = request.app.state.async_session_factory
    async with async_session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# 依赖注入：获取服务实例
# ---------------------------------------------------------------------------

async def _get_crisis_service(request: Request) -> AdminCrisisService:
    """从应用状态获取危机干预服务实例。"""
    redis = request.app.state.redis
    return AdminCrisisService(redis)


async def _get_log_service(request: Request) -> AdminLogService:
    """从应用状态获取审计日志服务实例。"""
    redis = request.app.state.redis
    return AdminLogService(redis)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/crisis/list — 危机事件列表
# ---------------------------------------------------------------------------

@router.get("/list", summary="危机事件列表")
async def get_crisis_events(
    request: Request,
    admin: Admin = require_permission("crisis:view"),
    db: AsyncSession = Depends(_get_db),
    crisis_service: AdminCrisisService = Depends(_get_crisis_service),
) -> dict[str, Any]:
    """查询危机事件列表。

    危机级别：
    - high: 紧急信号（优先级最高）
    - medium: 自残意念
    - low: 情绪低落

    列表按危机级别和时间综合排序，高危事件优先显示。

    筛选条件：
    - level: 危机级别（high/medium/low）
    - status: 处理状态（pending/intervening/resolved/false_positive）
    - user_id: 用户ID
    - start_time/end_time: 创建时间范围

    权限要求：crisis:view
    """
    request_id = getattr(request.state, "request_id", "")

    # 解析查询参数
    params = AdminCrisisListRequest(
        page=int(request.query_params.get("page", 1)),
        page_size=int(request.query_params.get("page_size", 20)),
        level=request.query_params.get("level"),
        status=request.query_params.get("status"),
        user_id=request.query_params.get("user_id"),
        sort_by=request.query_params.get("sort_by", "created_at"),
        sort_order=request.query_params.get("sort_order", "desc"),
    )

    # 处理时间参数（使用安全解析函数）
    start_time = request.query_params.get("start_time")
    end_time = request.query_params.get("end_time")
    params.start_time = parse_datetime_safe(start_time)
    params.end_time = parse_datetime_safe(end_time)

    # 查询危机事件列表
    result = await crisis_service.get_crisis_events(db, params)

    return paginated_response(
        data=[item.model_dump() for item in result.data],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# GET /api/admin/v1/crisis/:id — 危机事件详情
# ---------------------------------------------------------------------------

@router.get("/{message_id}", summary="危机事件详情")
async def get_crisis_detail(
    message_id: uuid.UUID,
    request: Request,
    admin: Admin = require_permission("crisis:view"),
    db: AsyncSession = Depends(_get_db),
    crisis_service: AdminCrisisService = Depends(_get_crisis_service),
) -> dict[str, Any]:
    """获取危机事件详情。

    包含：
    - 用户信息（手机号脱敏）
    - 触发消息内容（脱敏）
    - 触发关键词
    - AI 回复内容
    - 用户历史危机统计
    - 处理状态

    权限要求：crisis:view
    """
    request_id = getattr(request.state, "request_id", "")

    result = await crisis_service.get_crisis_detail(db, message_id)
    return success_response(result.model_dump(), request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/crisis/:id/resolve — 处理危机事件
# ---------------------------------------------------------------------------

@router.post("/{message_id}/resolve", summary="处理危机事件")
async def resolve_crisis(
    message_id: uuid.UUID,
    body: AdminCrisisResolveRequest,
    request: Request,
    admin: Admin = require_permission("crisis:resolve"),
    db: AsyncSession = Depends(_get_db),
    crisis_service: AdminCrisisService = Depends(_get_crisis_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """处理危机事件。

    处理状态：
    - resolved: 已解决
    - false_positive: 误报

    高危情况建议：
    - 联系用户（notify_user=true）
    - 必要时联系监护人或紧急服务

    权限要求：crisis:resolve
    """
    request_id = getattr(request.state, "request_id", "")

    result = await crisis_service.resolve_crisis(
        db=db,
        message_id=message_id,
        request=body,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    logger.info(
        "[AdminCrisis] 管理员处理危机事件: message_id=%s, status=%s, admin_id=%s",
        message_id,
        body.status,
        admin.id,
    )

    return success_response(result.model_dump(), request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/crisis/:id/intervene — 标记人工介入
# ---------------------------------------------------------------------------

@router.post("/{message_id}/intervene", summary="标记人工介入")
async def mark_intervention(
    message_id: uuid.UUID,
    request: Request,
    admin: Admin = require_permission("crisis:resolve"),
    db: AsyncSession = Depends(_get_db),
    crisis_service: AdminCrisisService = Depends(_get_crisis_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """标记人工介入。

    用于标记正在处理的危机事件，防止重复介入。
    标记后其他管理员可以看到该事件正在被处理。

    权限要求：crisis:resolve
    """
    request_id = getattr(request.state, "request_id", "")

    result = await crisis_service.mark_human_intervention(
        db=db,
        message_id=message_id,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    logger.info(
        "[AdminCrisis] 管理员标记人工介入: message_id=%s, admin_id=%s",
        message_id,
        admin.id,
    )

    return success_response(result, request_id)
