"""管理端举报管理路由模块。

提供管理后台举报管理相关的 API 端点：
- GET  /api/admin/v1/reports          举报列表
- GET  /api/admin/v1/reports/:id      举报详情
- POST /api/admin/v1/reports/:id/process 处理举报
- GET  /api/admin/v1/reports/appeals  申诉列表
- POST /api/admin/v1/reports/appeals/:id/review 审核申诉

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
    AdminAppealListRequest,
    AdminAppealReviewRequest,
    AdminAppealReviewResponse,
    AdminReportDetail,
    AdminReportListRequest,
    AdminReportProcessRequest,
    AdminReportProcessResponse,
)
from app.services.admin.admin_log_service import AdminLogService
from app.services.admin.report_service import AdminReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/reports", tags=["admin-reports"])


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
        # 尗试其他常见格式
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

async def _get_report_service(request: Request) -> AdminReportService:
    """从应用状态获取举报管理服务实例。"""
    redis = request.app.state.redis
    return AdminReportService(redis)


async def _get_log_service(request: Request) -> AdminLogService:
    """从应用状态获取审计日志服务实例。"""
    redis = request.app.state.redis
    return AdminLogService(redis)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/reports — 举报列表
# ---------------------------------------------------------------------------

@router.get("", summary="举报列表")
async def get_reports(
    request: Request,
    admin: Admin = require_permission("report:view"),
    db: AsyncSession = Depends(_get_db),
    report_service: AdminReportService = Depends(_get_report_service),
) -> dict[str, Any]:
    """查询举报列表。

    支持以下筛选条件：
    - status: 处理状态（pending/processing/approved/rejected）
    - report_type: 举报类型（porn/ad/harassment/abuse/scam/self_harm/other）
    - content_type: 内容类型（post/treehole_post/comment/user）
    - reporter_id: 举报人ID
    - reported_user_id: 被举报人ID
    - start_time/end_time: 创建时间范围
    - has_appeal: 是否有申诉

    支持分页和排序。

    权限要求：report:view
    """
    request_id = getattr(request.state, "request_id", "")

    # 解析查询参数
    params = AdminReportListRequest(
        page=int(request.query_params.get("page", 1)),
        page_size=int(request.query_params.get("page_size", 20)),
        status=request.query_params.get("status"),
        report_type=request.query_params.get("report_type"),
        content_type=request.query_params.get("content_type"),
        reporter_id=request.query_params.get("reporter_id"),
        reported_user_id=request.query_params.get("reported_user_id"),
        sort_by=request.query_params.get("sort_by", "created_at"),
        sort_order=request.query_params.get("sort_order", "desc"),
    )

    # 处理时间参数（使用安全解析函数）
    start_time = request.query_params.get("start_time")
    end_time = request.query_params.get("end_time")
    params.start_time = parse_datetime_safe(start_time)
    params.end_time = parse_datetime_safe(end_time)

    # 处理布尔参数
    has_appeal = request.query_params.get("has_appeal")
    if has_appeal:
        params.has_appeal = has_appeal == "true"

    # 查询举报列表
    result = await report_service.get_reports(db, params)

    return paginated_response(
        data=[item.model_dump() for item in result.data],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# GET /api/admin/v1/reports/:id — 举报详情
# ---------------------------------------------------------------------------

@router.get("/{report_id}", summary="举报详情")
async def get_report_detail(
    report_id: uuid.UUID,
    request: Request,
    admin: Admin = require_permission("report:view"),
    db: AsyncSession = Depends(_get_db),
    report_service: AdminReportService = Depends(_get_report_service),
) -> dict[str, Any]:
    """获取举报详情。

    包含：
    - 举报人信息
    - 被举报人信息
    - 被举报内容详情
    - 同一内容的其他举报（合并展示）
    - 处理历史

    权限要求：report:view
    """
    request_id = getattr(request.state, "request_id", "")

    result = await report_service.get_report_detail(db, report_id)
    return success_response(result.model_dump(), request_id)


# ---------------------------------------------------------------------------
# POST /api/admin/v1/reports/:id/process — 处理举报
# ---------------------------------------------------------------------------

@router.post("/{report_id}/process", summary="处理举报")
async def process_report(
    report_id: uuid.UUID,
    body: AdminReportProcessRequest,
    request: Request,
    admin: Admin = require_permission("report:process"),
    db: AsyncSession = Depends(_get_db),
    report_service: AdminReportService = Depends(_get_report_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """处理举报。

    处理动作：
    - approve: 通过举报（举报成立）
    - reject: 驳回举报（举报不成立）
    - ban_user: 封禁用户（通过举报并封禁被举报人）

    可选操作：
    - hide_content: 隐藏被举报内容
    - notify_reporter: 通知举报人（默认 true）
    - notify_reported_user: 通知被举报人（默认 false）

    权限要求：report:process
    """
    request_id = getattr(request.state, "request_id", "")

    result = await report_service.process_report(
        db=db,
        report_id=report_id,
        request=body,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    logger.info(
        "[AdminReports] 管理员处理举报: report_id=%s, action=%s, admin_id=%s",
        report_id,
        body.action,
        admin.id,
    )

    return success_response(result.model_dump(), request_id)


# ---------------------------------------------------------------------------
# GET /api/admin/v1/reports/appeals — 申诉列表
# ---------------------------------------------------------------------------

@router.get("/appeals", summary="申诉列表")
async def get_appeals(
    request: Request,
    admin: Admin = require_permission("report:view"),
    db: AsyncSession = Depends(_get_db),
    report_service: AdminReportService = Depends(_get_report_service),
) -> dict[str, Any]:
    """查询申诉列表。

    筛选条件：
    - appeal_status: 申诉状态（pending/approved/rejected）
    - start_time/end_time: 时间范围

    权限要求：report:view
    """
    request_id = getattr(request.state, "request_id", "")

    # 解析查询参数
    params = AdminAppealListRequest(
        page=int(request.query_params.get("page", 1)),
        page_size=int(request.query_params.get("page_size", 20)),
        appeal_status=request.query_params.get("appeal_status"),
    )

    # 处理时间参数（使用安全解析函数）
    start_time = request.query_params.get("start_time")
    end_time = request.query_params.get("end_time")
    params.start_time = parse_datetime_safe(start_time)
    params.end_time = parse_datetime_safe(end_time)

    # 查询申诉列表
    result = await report_service.get_appeals(db, params)

    return paginated_response(
        data=[item.model_dump() for item in result.data],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# POST /api/admin/v1/reports/appeals/:id/review — 审核申诉
# ---------------------------------------------------------------------------

@router.post("/appeals/{report_id}/review", summary="审核申诉")
async def review_appeal(
    report_id: uuid.UUID,
    body: AdminAppealReviewRequest,
    request: Request,
    admin: Admin = require_permission("report:process"),
    db: AsyncSession = Depends(_get_db),
    report_service: AdminReportService = Depends(_get_report_service),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """审核申诉。

    审核动作：
    - approve: 申诉通过（误判）
    - reject: 申诉驳回

    可选操作（仅 approve 时有效）：
    - unban_user: 解封用户
    - restore_content: 恢复内容

    权限要求：report:process
    """
    request_id = getattr(request.state, "request_id", "")

    result = await report_service.review_appeal(
        db=db,
        report_id=report_id,
        request=body,
        admin_id=admin.id,
        ip_address=ip_address,
        log_action=log_service.log_action_sync,
    )

    logger.info(
        "[AdminReports] 管理员审核申诉: report_id=%s, action=%s, admin_id=%s",
        report_id,
        body.action,
        admin.id,
    )

    return success_response(result.model_dump(), request_id)
