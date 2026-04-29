"""推送管理路由模块。

提供管理后台推送任务相关的 API 端点：
- GET  /api/admin/v1/push/tasks   推送任务列表
- POST /api/admin/v1/push/tasks   创建推送任务

Note:
    开发阶段返回 Mock 数据，后续接入推送服务（如极光推送、阿里云推送）。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import paginated_response, success_response
from app.middleware.admin_auth import (
    ClientIP,
    get_client_ip,
    require_permission,
)
from app.models.admin import Admin
from app.services.admin.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/v1/push", tags=["admin-push"])


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

async def _get_log_service(request: Request) -> AdminLogService:
    """从应用状态获取审计日志服务实例。"""
    redis = request.app.state.redis
    return AdminLogService(redis)


# ---------------------------------------------------------------------------
# Schema 定义（本地简化版）
# ---------------------------------------------------------------------------

class PushTaskListItem(BaseModel):
    """推送任务列表项。"""

    id: str = Field(..., description="任务ID")
    title: str = Field(..., description="推送标题")
    content: str = Field(..., description="推送内容")
    target_type: str = Field(..., description="目标类型：all/user_ids/tag")
    target_count: int = Field(..., description="目标用户数")
    status: str = Field(..., description="状态：pending/sending/sent/failed")
    sent_count: int = Field(default=0, description="已发送数")
    failed_count: int = Field(default=0, description="失败数")
    scheduled_at: datetime | None = Field(None, description="计划发送时间")
    sent_at: datetime | None = Field(None, description="实际发送时间")
    created_at: datetime = Field(..., description="创建时间")
    creator_name: str | None = Field(None, description="创建者名称")


class PushTaskCreateRequest(BaseModel):
    """创建推送任务请求。"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="推送标题",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="推送内容",
    )
    target_type: str = Field(
        default="all",
        description="目标类型：all（全部用户）/user_ids（指定用户）/tag（标签用户）",
    )
    target_user_ids: list[str] | None = Field(
        None,
        description="目标用户ID列表（target_type=user_ids时必填）",
    )
    target_tag: str | None = Field(
        None,
        description="目标用户标签（target_type=tag时必填）",
    )
    scheduled_at: datetime | None = Field(
        None,
        description="计划发送时间（可选，默认立即发送）",
    )
    deep_link: str | None = Field(
        None,
        description="点击跳转链接",
    )

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, v: str) -> str:
        """验证目标类型。"""
        allowed = ["all", "user_ids", "tag"]
        if v not in allowed:
            raise ValueError(f"目标类型必须是: {allowed}")
        return v


class PushTaskCreateResponse(BaseModel):
    """创建推送任务响应。"""

    id: str = Field(..., description="任务ID")
    title: str = Field(..., description="推送标题")
    content: str = Field(..., description="推送内容")
    target_type: str = Field(..., description="目标类型")
    target_count: int = Field(..., description="目标用户数")
    status: str = Field(..., description="状态")
    scheduled_at: datetime | None = Field(None, description="计划发送时间")
    created_at: datetime = Field(..., description="创建时间")


# ---------------------------------------------------------------------------
# Mock 数据存储（开发阶段）
# ---------------------------------------------------------------------------

# 内存存储推送任务（仅用于开发阶段演示）
_mock_push_tasks: list[dict] = []


# ---------------------------------------------------------------------------
# GET /api/admin/v1/push/tasks — 推送任务列表
# ---------------------------------------------------------------------------

@router.get("/tasks", summary="推送任务列表")
async def get_push_tasks(
    request: Request,
    admin: Admin = require_permission("push:view"),
    db: AsyncSession = Depends(_get_db),
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    """查询推送任务列表。

    支持以下功能：
    - 筛选：状态（pending/sending/sent/failed）
    - 分页：page, page_size

    Note:
        开发阶段返回 Mock 数据。

    权限要求：push:view
    """
    request_id = getattr(request.state, "request_id", "")

    # Mock 数据
    now = datetime.now(timezone.utc)
    mock_tasks = [
        PushTaskListItem(
            id="push_001",
            title="新功能上线通知",
            content="AI 情绪陪伴功能已上线，快来体验吧！",
            target_type="all",
            target_count=1000,
            status="sent",
            sent_count=980,
            failed_count=20,
            sent_at=now,
            created_at=now,
            creator_name="运营管理员",
        ),
        PushTaskListItem(
            id="push_002",
            title="周末活动提醒",
            content="本周六下午3点线上分享会，不见不散~",
            target_type="tag",
            target_count=150,
            status="pending",
            scheduled_at=now,
            created_at=now,
            creator_name="活动运营",
        ),
    ]

    # 状态筛选
    if status:
        mock_tasks = [t for t in mock_tasks if t.status == status]

    # 分页
    total = len(mock_tasks)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_tasks = mock_tasks[start:end]

    return paginated_response(
        data=[t.model_dump() for t in paginated_tasks],
        page=page,
        page_size=page_size,
        total=total,
        request_id=request_id,
    )


# ---------------------------------------------------------------------------
# POST /api/admin/v1/push/tasks — 创建推送任务
# ---------------------------------------------------------------------------

@router.post("/tasks", summary="创建推送任务")
async def create_push_task(
    body: PushTaskCreateRequest,
    request: Request,
    admin: Admin = require_permission("push:create"),
    db: AsyncSession = Depends(_get_db),
    log_service: AdminLogService = Depends(_get_log_service),
    ip_address: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """创建推送任务。

    请求体参数：
    - title: 推送标题（1-50字符）
    - content: 推送内容（1-200字符）
    - target_type: 目标类型（all/user_ids/tag）
    - target_user_ids: 目标用户ID列表（可选）
    - target_tag: 目标用户标签（可选）
    - scheduled_at: 计划发送时间（可选）
    - deep_link: 点击跳转链接（可选）

    Note:
        开发阶段仅创建 Mock 任务，不实际发送推送。

    权限要求：push:create
    """
    request_id = getattr(request.state, "request_id", "")

    now = datetime.now(timezone.utc)

    # 计算目标用户数（Mock）
    target_count = 0
    if body.target_type == "all":
        target_count = 1000  # Mock 总用户数
    elif body.target_type == "user_ids" and body.target_user_ids:
        target_count = len(body.target_user_ids)
    elif body.target_type == "tag":
        target_count = 150  # Mock 标签用户数

    # 创建任务
    task_id = f"push_{uuid.uuid4().hex[:8]}"
    task = PushTaskCreateResponse(
        id=task_id,
        title=body.title,
        content=body.content,
        target_type=body.target_type,
        target_count=target_count,
        status="pending",
        scheduled_at=body.scheduled_at,
        created_at=now,
    )

    # 记录操作日志
    await log_service.log_action_sync(
        db=db,
        admin_id=admin.id,
        action="push_create",
        target_type="push_task",
        target_id=task_id,
        details={
            "title": body.title,
            "content": body.content,
            "target_type": body.target_type,
            "target_count": target_count,
        },
        ip_address=ip_address,
        user_agent="admin-api",
    )

    logger.info(
        "推送任务创建成功: task_id=%s, title=%s, operator=%s",
        task_id,
        body.title,
        admin.username,
    )

    return success_response(task, request_id)