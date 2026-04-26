"""管理端内容管理路由模块。

提供管理后台内容管理相关的 API 端点：
- GET    /api/admin/v1/contents        内容列表
- GET    /api/admin/v1/contents/:id    内容详情
- PATCH  /api/admin/v1/contents/:id/status 内容状态修改

"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import paginated_response, success_response
from app.middleware.admin_auth import (
    CurrentAdmin,
    get_client_ip,
    require_permission,
)
from app.models.admin import Admin
from app.schemas.report import (
    AdminContentDetail,
    AdminContentListRequest,
    AdminContentStatusRequest,
    AdminContentStatusResponse,
    ContentType,
)
from app.services.admin.admin_log_service import AdminLogService
from app.services.admin.content_service import AdminContentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/contents", tags=["admin-contents"])


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class ContentPathParams(BaseModel):
    """内容路径参数。"""

    content_type: str = Field(
        ...,
        description="内容类型：post/treehole_post",
    )
    content_id: str = Field(..., description="内容ID")


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

async def _get_content_service(request: Request) -> AdminContentService:
    """从应用状态获取内容管理服务实例。"""
    redis = request.app.state.redis
    return AdminContentService(redis)


async def _get_log_service(request: Request) -> AdminLogService:
    """从应用状态获取审计日志服务实例。"""
    redis = request.app.state.redis
    return AdminLogService(redis)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/contents — 内容列表
# ---------------------------------------------------------------------------

@router.get("", summary="内容列表")
async def get_contents(
    request: Request,
    admin: Admin = require_permission("content:view"),
    db: AsyncSession = Depends(_get_db),
    content_service: AdminContentService = Depends(_get_content_service),
) -> dict[str, Any]:
    """查询内容列表。

    支持两种内容类型：
    - post: 广场动态
    - treehole_post: 树洞帖子

    筛选条件：
    - content_type: 内容类型
    - status: 状态（active/hidden/deleted）
    - author_id: 作者ID
    - is_recommended: 是否推荐
    - start_time/end_time: 创建时间范围
    - search: 内容搜索关键词

    权限要求：content:view
    """
    request_id = getattr(request.state, "request_id", "")

    # 解析查询参数
    params = AdminContentListRequest(
        page=int(request.query_params.get("page", 1)),
        page_size=int(request.query_params.get("page_size", 20)),
        content_type=request.query_params.get("content_type"),
        status=request.query_params.get("status"),
        author_id=request.query_params.get("author_id"),
        is_recommended=request.query_params.get("is_recommended") == "true" if request.query_params.get("is_recommended") else None,
        sort_by=request.query_params.get("sort_by", "created_at"),
        sort_order=request.query_params.get("sort_order", "desc"),
        search=request.query_params.get("search"),
    )

    # 处理时间参数
    start_time = request.query_params.get("start_time")
    end_time = request.query_params.get("end_time")
    if start_time:
        params.start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    if end_time:
        params.end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

    # 查询内容列表
    result = await content_service.get_contents(db, params)

    return paginated_response(
        data=[item.model_dump() for item in result.data],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# GET /api/admin/v1/contents/:type/:id — 内容详情
# ---------------------------------------------------------------------------

@router.get("/{content_type}/{content_id}", summary="内容详情")
async def get_content_detail(
    content_type: str,
    content_id: uuid.UUID,
    request: Request,
    admin: Admin = require_permission("content:view"),
    db: AsyncSession = Depends(_get_db),
    content_service: AdminContentService = Depends(_get_content_service),
) -> dict[str, Any]:
    """获取内容详情。

    包含：
    - 内容文本
    - 图片列表
    - 作者信息（手机号脱敏）
    - 状态信息
    - 举报次数
    - 点赞数/评论数

    权限要求：content:view
    """
    request_id = getattr(request.state, "request_id", "")

    result = await content_service.get_content_detail(
        db=db,
        content_type=content_type,
        content_id=content_id,
    )

    return success_response(result.model_dump(), request_id)


# ---------------------------------------------------------------------------
# PATCH /api/admin/v1/contents/:type/:id/status — 内容状态修改
# ---------------------------------------------------------------------------

@router.patch("/{content_type}/{content_id}/status", summary="内容状态修改")
async def update_content_status(
    content_type: str,
    content_id: uuid.UUID,
    body: AdminContentStatusRequest,
    request: Request,
    admin: Admin = require_permission("content:moderate"),
    db: AsyncSession = Depends(_get_db),
    content_service: AdminContentService = Depends(_get_content_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """修改内容状态。

    操作类型：
    - hide: 隐藏内容
    - show: 显示内容
    - recommend: 推荐内容（暂不支持）
    - unrecommend: 取消推荐（暂不支持）

    注意：
    - 隐藏内容会设置 deleted_at，但不会真正删除
    - 显示内容会清除 deleted_at

    权限要求：content:moderate
    """
    request_id = getattr(request.state, "request_id", "")

    result = await content_service.update_content_status(
        db=db,
        content_type=content_type,
        content_id=content_id,
        request=body,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    logger.info(
        "[AdminContents] 管理员修改内容状态: content_type=%s, content_id=%s, action=%s, admin_id=%s",
        content_type,
        content_id,
        body.action,
        admin.id,
    )

    return success_response(result.model_dump(), request_id)
