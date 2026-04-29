"""数据看板路由模块。

提供管理后台数据看板相关的 API 端点：
- GET  /api/admin/v1/dashboard/overview  概览数据
- GET  /api/admin/v1/dashboard/users     用户增长趋势
- GET  /api/admin/v1/dashboard/retention 留存数据
- GET  /api/admin/v1/dashboard/emotion    情绪分布统计
- GET  /api/admin/v1/dashboard/ai        AI 服务数据
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.middleware.admin_auth import require_permission
from app.models.admin import Admin
from app.schemas.admin_dashboard import DashboardPeriodRequest
from app.services.admin.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/dashboard", tags=["admin-dashboard"])


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

async def _get_dashboard_service(request: Request) -> DashboardService:
    """从应用状态获取数据看板服务实例。"""
    redis = request.app.state.redis
    return DashboardService(redis)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/dashboard/overview — 概览数据
# ---------------------------------------------------------------------------

@router.get("/overview", summary="数据看板概览")
async def get_overview(
    request: Request,
    admin: Admin = require_permission("dashboard:read"),
    db: AsyncSession = Depends(_get_db),
    dashboard_service: DashboardService = Depends(_get_dashboard_service),
) -> dict[str, Any]:
    """获取数据看板概览数据。

    返回以下核心指标：
    - 用户数据：总用户数、DAU、WAU、MAU、新增用户趋势
    - AI 服务数据：对话次数、平均轮次
    - 社交数据：好友关系、私聊消息
    - 内容数据：日记、树洞、动态
    - 运营数据：待处理举报、危机事件

    权限要求：dashboard:read
    """
    request_id = getattr(request.state, "request_id", "")

    result = await dashboard_service.get_overview(db)

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/dashboard/users — 用户增长趋势
# ---------------------------------------------------------------------------

@router.get("/users", summary="用户增长趋势")
async def get_user_growth_trend(
    request: Request,
    admin: Admin = require_permission("dashboard:read"),
    db: AsyncSession = Depends(_get_db),
    dashboard_service: DashboardService = Depends(_get_dashboard_service),
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """获取用户增长趋势数据。

    查询参数：
    - period: 统计周期（day/week/month）
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）

    返回：
    - 日期维度的用户新增、累计、活跃数据

    权限要求：dashboard:read
    """
    request_id = getattr(request.state, "request_id", "")

    params = DashboardPeriodRequest(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    result = await dashboard_service.get_user_growth_trend(db, params)

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/dashboard/retention — 留存数据
# ---------------------------------------------------------------------------

@router.get("/retention", summary="用户留存数据")
async def get_retention(
    request: Request,
    admin: Admin = require_permission("dashboard:read"),
    db: AsyncSession = Depends(_get_db),
    dashboard_service: DashboardService = Depends(_get_dashboard_service),
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """获取用户留存数据。

    查询参数：
    - period: 统计周期（day/week）
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）

    返回：
    - 同期群留存数据（次日/7日/30日留存率）

    Note:
        开发阶段返回 Mock 数据，后续接入真实计算。

    权限要求：dashboard:read
    """
    request_id = getattr(request.state, "request_id", "")

    params = DashboardPeriodRequest(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    result = await dashboard_service.get_retention(db, params)

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/dashboard/emotion — 情绪分布统计
# ---------------------------------------------------------------------------

@router.get("/emotion", summary="情绪分布统计")
async def get_emotion_distribution(
    request: Request,
    admin: Admin = require_permission("dashboard:read"),
    db: AsyncSession = Depends(_get_db),
    dashboard_service: DashboardService = Depends(_get_dashboard_service),
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """获取情绪分布统计数据。

    查询参数：
    - period: 统计周期（day/week/month）
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）

    返回：
    - 情绪基调分布（开心、难过、焦虑等）
    - 各情绪的日记数量和占比

    权限要求：dashboard:read
    """
    request_id = getattr(request.state, "request_id", "")

    params = DashboardPeriodRequest(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    result = await dashboard_service.get_emotion_distribution(db, params)

    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/dashboard/ai — AI 服务数据
# ---------------------------------------------------------------------------

@router.get("/ai", summary="AI 服务数据")
async def get_ai_service_data(
    request: Request,
    admin: Admin = require_permission("dashboard:read"),
    db: AsyncSession = Depends(_get_db),
    dashboard_service: DashboardService = Depends(_get_dashboard_service),
    period: str = "day",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """获取 AI 服务统计数据。

    查询参数：
    - period: 统计周期（day/week/month）
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）

    返回：
    - AI 对话次数趋势
    - 平均对话轮次
    - 使用 AI 的用户数

    Note:
        开发阶段部分数据为 Mock，后续接入 AIConversation 表。

    权限要求：dashboard:read
    """
    request_id = getattr(request.state, "request_id", "")

    params = DashboardPeriodRequest(
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    result = await dashboard_service.get_ai_service_data(db, params)

    return success_response(result, request_id)
