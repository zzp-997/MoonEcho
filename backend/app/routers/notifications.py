"""通知路由模块。

提供通知相关的 API 端点：
- GET    /api/v1/notifications           获取通知列表
- PATCH  /api/v1/notifications/{id}/read 标记单条已读
- PATCH  /api/v1/notifications/read-all  全部标记已读
- GET    /api/v1/notifications/settings  获取通知设置
- PATCH  /api/v1/notifications/settings  更新通知设置

"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.responses import paginated_response, success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdateRequest,
)
from app.services.notification_service import NotificationService
from app.services.push import create_push_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _get_db_session(request: Request) -> Any:
    """从应用状态获取数据库会话工厂。"""
    return request.app.state.db_session


def _get_settings(request: Request) -> Any:
    """从应用状态获取应用配置。"""
    return request.app.state.settings


def _get_redis(request: Request) -> Any:
    """从应用状态获取 Redis 客户端。"""
    return request.app.state.redis


def _create_notification_service(
    settings: Any,
    redis_client: Any,
) -> NotificationService:
    """创建通知服务实例。

    Args:
        settings: 应用配置
        redis_client: Redis 客户端

    Returns:
        NotificationService 实例
    """
    push_provider = create_push_service(settings.push_provider)
    return NotificationService(
        settings=settings,
        redis=redis_client,
        push_provider=push_provider,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/notifications — 获取通知列表
# ---------------------------------------------------------------------------

@router.get("", summary="获取通知列表")
async def list_notifications(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    unread_only: bool = Query(default=False, description="只显示未读"),
    notification_type: str | None = Query(default=None, description="按类型筛选"),
) -> dict[str, Any]:
    """获取用户通知列表。

    - 支持按类型筛选
    - 支持只显示未读
    - 返回未读数量
    - 按创建时间倒序排列
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_notification_service(settings, redis_client)
            result = await service.list_notifications(
                user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
                unread_only=unread_only,
                notification_type=notification_type,
            )

            # 使用自定义响应格式（包含未读数量）
            return {
                "success": True,
                "data": [n.model_dump() for n in result["data"]],
                "pagination": {
                    "page": result["page"],
                    "pageSize": result["page_size"],
                    "total": result["total"],
                    "hasMore": result["page"] * result["page_size"] < result["total"],
                    "unreadCount": result["unread_count"],
                },
                "meta": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "requestId": request_id,
                },
            }
        except AppError:
            raise
        except Exception as e:
            logger.error("[Notifications] 获取通知列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取通知列表失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/notifications/unread-count — 获取未读数量
# ---------------------------------------------------------------------------

@router.get("/unread-count", summary="获取未读数量")
async def get_unread_count(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取用户未读通知数量。

    用于显示通知徽章数字。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_notification_service(settings, redis_client)
            count = await service.get_unread_count(user_id=user.id, db=db)
            return success_response({"unread_count": count}, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Notifications] 获取未读数量异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取未读数量失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# PATCH /api/v1/notifications/{id}/read — 标记单条已读
# ---------------------------------------------------------------------------

class MarkReadPathParams(BaseModel):
    """标记已读路径参数。"""

    notification_id: str = Field(..., description="通知ID")


@router.patch(
    "/{notification_id}/read",
    summary="标记单条已读",
    response_model=NotificationResponse,
)
async def mark_as_read(
    user: CurrentUser,
    request: Request,
    notification_id: str,
) -> dict[str, Any]:
    """标记单条通知为已读。

    - 通知必须属于当前用户
    - 已读通知不能重复标记
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_notification_service(settings, redis_client)
            result = await service.mark_as_read(
                user_id=user.id,
                notification_id=notification_id,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Notifications] 标记已读异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="标记已读失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# PATCH /api/v1/notifications/read-all — 全部标记已读
# ---------------------------------------------------------------------------

@router.patch("/read-all", summary="全部标记已读")
async def mark_all_as_read(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """标记全部通知为已读。

    - 批量更新所有未读通知
    - 返回更新的数量
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_notification_service(settings, redis_client)
            result = await service.mark_all_as_read(user_id=user.id, db=db)
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Notifications] 全部标记已读异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="全部标记已读失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/notifications/settings — 获取通知设置
# ---------------------------------------------------------------------------

@router.get(
    "/settings",
    summary="获取通知设置",
    response_model=NotificationSettingResponse,
)
async def get_settings(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取用户通知设置。

    - 包含推送总开关
    - 包含各类型通知开关
    - 危机干预推送强制开启（不可关闭）
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_notification_service(settings, redis_client)
            result = await service.get_settings(user_id=user.id, db=db)
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Notifications] 获取通知设置异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取通知设置失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# PATCH /api/v1/notifications/settings — 更新通知设置
# ---------------------------------------------------------------------------

@router.patch(
    "/settings",
    summary="更新通知设置",
    response_model=NotificationSettingResponse,
)
async def update_settings(
    body: NotificationSettingUpdateRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """更新用户通知设置。

    - 支持部分更新
    - 危机干预推送不可关闭（自动强制开启）
    - 更新后清除缓存
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_notification_service(settings, redis_client)
            result = await service.update_settings(
                user_id=user.id,
                request=body,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Notifications] 更新通知设置异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="更新通知设置失败",
                status_code=500,
            )