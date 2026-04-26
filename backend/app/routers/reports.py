"""C 端举报路由模块。

提供用户举报提交相关的 API 端点：
- POST /api/v1/reports 提交举报

"""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.middleware.auth import CurrentUser
from app.schemas.report import ReportCreateRequest, ReportCreateResponse
from app.services.admin.report_service import AdminReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


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

async def _get_report_service(request: Request) -> AdminReportService:
    """从应用状态获取举报管理服务实例。"""
    redis = request.app.state.redis
    return AdminReportService(redis)


async def _get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址。"""
    # 优先从 X-Forwarded-For 获取
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # 从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 使用请求的 client.host
    if request.client:
        return request.client.host

    return "unknown"


# ---------------------------------------------------------------------------
# POST /api/v1/reports — 提交举报
# ---------------------------------------------------------------------------

@router.post("", summary="提交举报", response_model=ReportCreateResponse)
async def create_report(
    body: ReportCreateRequest,
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(_get_db),
    report_service: AdminReportService = Depends(_get_report_service),
    ip_address: str = Depends(_get_client_ip),
) -> dict[str, Any]:
    """提交内容举报。

    举报类型：
    - porn: 色情低俗
    - ad: 广告引流
    - harassment: 骚扰
    - abuse: 辱骂攻击
    - scam: 诈骗
    - self_harm: 自杀自残倾向
    - other: 其他

    举报对象：
    - post: 广场动态
    - treehole_post: 树洞帖子
    - comment: 评论
    - user: 用户

    注意：
    - 同一用户对同一内容只能举报一次
    - 3人以上举报同一内容会自动触发下架

    Returns:
        举报创建结果
    """
    request_id = getattr(request.state, "request_id", "")

    result = await report_service.create_report(
        db=db,
        user_id=user.id,
        request=body,
        ip_address=ip_address,
    )

    logger.info(
        "[Reports] 用户提交举报: user_id=%s, content_type=%s, content_id=%s",
        user.id,
        body.reported_content_type.value,
        body.reported_content_id,
    )

    return success_response(result.model_dump(), request_id)
