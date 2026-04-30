"""数据统计 API 路由模块。

提供验证门控所需的统计 API 端点：
- POST /api/v1/analytics/events    批量事件上报（前端tracking.ts调用）
- GET  /api/v1/stats/retention/7d     获取7日留存率
- GET  /api/v1/stats/conversation-rounds/daily  获取日均对话轮次
- GET  /api/v1/stats/diary-continuation/7d  获取情绪日记7日连续记录率
- POST /api/v1/stats/nps             提交 NPS 评分
- GET  /api/v1/stats/nps             获取 NPS 评分统计
- GET  /api/v1/stats/verification-gate  获取验证门控综合状态
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Path, Query, Request
from pydantic import BaseModel, Field

from app.core.errors import AppError
from app.core.responses import success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.services.stats_service import create_stats_service, batch_record_events

logger = logging.getLogger(__name__)

# 事件上报路由（前端tracking.ts调用）
analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# 统计路由
stats_router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _get_db_session(request: Request) -> Any:
    """从应用状态获取数据库会话工厂。"""
    return request.app.state.db_session


# ---------------------------------------------------------------------------
# Schema 定义
# ---------------------------------------------------------------------------

class TrackingEventSchema(BaseModel):
    """单个跟踪事件"""
    name: str = Field(..., description="事件名称")
    properties: dict[str, Any] | None = Field(None, description="事件属性")
    timestamp: int = Field(..., description="时间戳（毫秒）")
    user_id: str | None = Field(None, description="用户ID（可选）")
    device_id: str = Field(..., description="设备ID")
    session_id: str = Field(..., description="会话ID")
    platform: str = Field(..., description="平台：h5/app/mp-weixin")
    app_version: str | None = Field(None, description="App版本")


class EventBatchSubmitRequest(BaseModel):
    """批量事件提交请求"""
    events: list[TrackingEventSchema] = Field(..., description="事件列表")


class EventBatchSubmitResponse(BaseModel):
    """批量事件提交响应"""
    success: bool
    recorded_count: int
    skipped_count: int
    message: str


class NPSSubmitRequest(BaseModel):
    """NPS 评分提交请求。"""
    score: int = Field(..., ge=0, le=10, description="NPS 评分（0-10 分）")
    feedback: str | None = Field(None, description="用户反馈（可选）")


class RetentionResponse(BaseModel):
    """7日留存率响应。"""
    retention_rate: float
    retained_users: int
    total_registered: int
    target: float
    is_met: bool
    status: str


class ConversationRoundsResponse(BaseModel):
    """日均对话轮次响应。"""
    daily_avg_rounds: float
    total_rounds: float
    active_users: int
    days: int
    target: float
    is_met: bool
    status: str


class DiaryContinuationResponse(BaseModel):
    """情绪日记7日连续记录率响应。"""
    continuation_rate: float
    consecutive_7d_users: int
    total_users: int
    target: float
    is_met: bool
    status: str


class NPSScoreResponse(BaseModel):
    """NPS 评分响应。"""
    nps_score: int
    total_responses: int
    promoters: int
    passives: int
    detractors: int
    target: int
    is_met: bool
    status: str


# ---------------------------------------------------------------------------
# GET /api/v1/stats/retention/7d — 获取7日留存率
# ---------------------------------------------------------------------------

@stats_router.get(
    "/retention/7d",
    summary="获取7日留存率",
    description="计算7日留存率，验证门控标准：≥ 30% 为达标，< 15% 暂停社交层开发",
)
async def get_retention_rate_7d(
    request: Request,
) -> dict[str, Any]:
    """获取 7 日留存率统计。

    7日留存率 = (今日活跃且注册时间在7天前的用户数) / (7天前注册的用户总数)
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_stats_service()
            result = await service.get_retention_rate_7d(db)
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Stats] 获取7日留存率异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取7日留存率失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/stats/conversation-rounds/daily — 获取日均对话轮次
# ---------------------------------------------------------------------------

@stats_router.get(
    "/conversation-rounds/daily",
    summary="获取日均对话轮次",
    description="计算日均AI对话轮次，验证门控标准：≥ 10轮为达标，< 10回到AI体验优化",
)
async def get_daily_conversation_rounds(
    request: Request,
    days: int = Query(default=7, ge=1, le=30, description="统计天数"),
) -> dict[str, Any]:
    """获取日均 AI 对话轮次统计。

    日均对话轮次 = 总对话轮次 / 活跃用户数 / 天数
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_stats_service()
            result = await service.get_daily_conversation_rounds(days=days, db=db)
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Stats] 获取日均对话轮次异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取日均对话轮次失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/stats/diary-continuation/7d — 获取情绪日记7日连续记录率
# ---------------------------------------------------------------------------

@stats_router.get(
    "/diary-continuation/7d",
    summary="获取情绪日记7日连续记录率",
    description="计算情绪日记7日连续记录率，验证门控标准：≥ 20% 为达标，< 20% 优化日记引导",
)
async def get_diary_7d_continuation(
    request: Request,
) -> dict[str, Any]:
    """获取情绪日记 7 日连续记录率统计。

    7日连续记录率 = (过去7天中连续记录≥7天的用户数) / (总用户数)
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_stats_service()
            result = await service.get_diary_7d_continuation_rate(db)
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Stats] 获取情绪日记7日连续记录率异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取情绪日记7日连续记录率失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/stats/nps — 提交 NPS 评分
# ---------------------------------------------------------------------------

@stats_router.post(
    "/nps",
    summary="提交 NPS 评分",
    description="提交用户的 NPS 评分（0-10分），验证门控标准：≥ 30 为达标，< 0 重新评估产品方向",
)
async def submit_nps(
    user: CurrentUser,
    request: Request,
    nps_data: NPSSubmitRequest,
) -> dict[str, Any]:
    """提交用户的 NPS 评分。

    NPS（Net Promoter Score）评分：
    - 9-10 分：推荐者
    - 7-8 分：中性者
    - 0-6 分：贬损者
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_stats_service()
            result = await service.submit_nps(
                user_id=user.id,
                score=nps_data.score,
                feedback=nps_data.feedback,
                db=db,
            )
            return success_response(result, request_id)
        except ValueError as e:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message=str(e),
                status_code=400,
            )
        except AppError:
            raise
        except Exception as e:
            logger.error("[Stats] 提交NPS评分异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="提交NPS评分失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/stats/nps — 获取 NPS 评分统计
# ---------------------------------------------------------------------------

@stats_router.get(
    "/nps",
    summary="获取 NPS 评分统计",
    description="获取 NPS 评分统计，验证门控标准：≥ 30 为达标，< 0 重新评估产品方向",
)
async def get_nps_score(
    request: Request,
) -> dict[str, Any]:
    """获取 NPS 评分统计。

    NPS = 推荐者比例（9-10分）- 贬损者比例（0-6分）
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_stats_service()
            result = await service.get_nps_score(db)
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Stats] 获取NPS评分统计异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取NPS评分统计失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/stats/verification-gate — 获取验证门控综合状态
# ---------------------------------------------------------------------------

@stats_router.get(
    "/verification-gate",
    summary="获取验证门控综合状态",
    description="获取所有验证门控指标的综合状态",
)
async def get_verification_gate_status(
    request: Request,
) -> dict[str, Any]:
    """获取验证门控综合状态。

    返回所有指标的状态：
    - 7日留存率 ≥ 30%
    - 日均对话轮次 ≥ 10轮
    - 情绪日记7日连续记录率 ≥ 20%
    - NPS ≥ 30
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_stats_service()
            result = await service.get_verification_gate_status(db)
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Stats] 获取验证门控状态异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取验证门控状态失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/analytics/events — 批量事件上报
# ---------------------------------------------------------------------------

@analytics_router.post(
    "/events",
    summary="批量事件上报",
    description="接收前端tracking.ts的批量事件上报，用于数据统计和验证门控",
)
async def submit_event_batch(
    request: Request,
    batch_data: EventBatchSubmitRequest,
) -> dict[str, Any]:
    """批量上报用户行为事件。

    前端 tracking.ts 会批量发送事件到该端点：
    - 事件存储到 user_events 表
    - 支持批量写入提升性能
    - 失败时静默处理，不影响前端业务
    """
    request_id = getattr(request.state, "request_id", "")

    # 转换前端事件格式为服务层格式
    events = []
    for event in batch_data.events:
        events.append({
            "user_id": event.user_id,
            "event_type": event.name,
            "event_data": {
                "properties": event.properties,
                "timestamp": event.timestamp,
                "device_id": event.device_id,
                "session_id": event.session_id,
                "platform": event.platform,
                "app_version": event.app_version,
            },
            "source": event.platform,
        })

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            result = await batch_record_events(events=events, db=db)
            return success_response(result, request_id)
        except Exception as e:
            logger.error("[Analytics] 批量事件上报异常: %s", str(e))
            # 静默处理，不抛出异常
            return success_response({
                "success": True,
                "recorded_count": 0,
                "skipped_count": len(events),
                "message": "事件接收成功",
            }, request_id)


# ---------------------------------------------------------------------------
# 路由导出（供 routers/__init__.py 注册）
# ---------------------------------------------------------------------------

# 导出两个路由：analytics（事件上报）和 stats（统计查询）
__all__ = ["analytics_router", "stats_router"]
