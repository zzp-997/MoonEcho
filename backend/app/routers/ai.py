"""AI 对话路由模块。

提供 AI 对话相关的 API 端点：
- POST /api/v1/ai/chat              同步对话
- POST /api/v1/ai/chat/stream       SSE 流式对话
- GET  /api/v1/ai/conversations     获取对话列表
- POST /api/v1/ai/greeting          获取 AI 开场白
- POST /api/v1/ai/generate-greeting AI 生成打招呼语

AI 聊天辅助端点：
- POST /api/v1/ai/chat-assist/topic      冷场救急话题建议
- POST /api/v1/ai/chat-assist/reply      回复建议
- POST /api/v1/ai/chat-assist/polish     语气优化
- POST /api/v1/ai/chat-assist/exit       温柔退出结束语
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.responses import paginated_response, success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.models.user import User
from app.schemas.ai_chat_assist import (
    ExitSuggestionRequest,
    ExitSuggestionResponse,
    PolishRequest,
    PolishResponse,
    ReplySuggestionRequest,
    ReplySuggestionResponse,
    TopicSuggestionRequest,
    TopicSuggestionResponse,
)
from app.schemas.ai_greeting import (
    GenerateGreetingRequest,
    GenerateGreetingResponse,
    GreetingQuotaResponse,
)
from app.services.ai_chat_assist import create_ai_chat_assist_service
from app.services.ai_conversation_service import AIConversationService
from app.services.ai_greeting import AIGreetingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


# ---------------------------------------------------------------------------
# 请求/响应 Schema
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """对话请求体。"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    personality: str = Field(default="xiaowen", description="AI性格：xiaowen/laohei/ali")
    conversation_id: str | None = Field(default=None, description="对话ID（可选，续聊时传入）")


class GreetingRequest(BaseModel):
    """开场白请求体。"""
    personality: str | None = Field(default=None, description="AI性格（可选，默认上次选择的性格）")


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


def _create_conversation_service(
    db: AsyncSession,
    settings: Any,
    redis_client: Any = None,
) -> AIConversationService:
    """创建 AI 对话服务实例。

    Args:
        db: 数据库会话
        settings: 应用配置
        redis_client: Redis 客户端（可选）

    Returns:
        AIConversationService 实例
    """
    return AIConversationService(
        db=db,
        ai_provider=settings.ai_provider,
        zhipu_api_key=settings.zhipu_api_key,
        daily_limit=settings.ai_daily_limit,
        daily_limit_vip=settings.ai_daily_limit_vip,
        redis_client=redis_client,
    )


def _validate_personality(personality: str) -> None:
    """验证性格标识是否有效。

    Args:
        personality: 性格标识

    Raises:
        AppError: 性格标识无效时抛出
    """
    valid_personalities = ("xiaowen", "laohei", "ali")
    if personality not in valid_personalities:
        raise AppError(
            code=ErrorCode.INVALID_PARAMETER,
            message=f"无效的性格标识: {personality}，可用选项: {', '.join(valid_personalities)}",
            status_code=400,
        )


# ---------------------------------------------------------------------------
# POST /api/v1/ai/chat — 同步对话
# ---------------------------------------------------------------------------

@router.post("/chat", summary="同步对话")
async def chat(
    body: ChatRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """同步对话接口。

    发送消息并等待 AI 完整回复。

    - 如果有 conversation_id，加载历史上下文（最近5轮）
    - 调用 AI 服务同步回复
    - 保存用户消息和 AI 回复
    - 检测危机关键词，必要时追加安全信息
    """
    request_id = getattr(request.state, "request_id", "")

    # 验证性格标识
    _validate_personality(body.personality)

    # 获取数据库会话和服务
    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_conversation_service(db, settings, redis_client)
            result = await service.chat(
                user_id=user.id,
                message=body.message,
                personality=body.personality,
                conversation_id=body.conversation_id,
            )
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[AI Chat] 同步对话异常: %s", str(e))
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="AI 服务暂时不可用，请稍后重试",
                status_code=503,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/ai/chat/stream — SSE 流式对话
# ---------------------------------------------------------------------------

@router.post("/chat/stream", summary="SSE流式对话")
async def chat_stream(
    body: ChatRequest,
    user: CurrentUser,
    request: Request,
) -> StreamingResponse:
    """SSE 流式对话接口。

    使用 Server-Sent Events 逐步返回 AI 回复。

    - 如果有 conversation_id，加载历史上下文（最近5轮）
    - 流式输出 AI 回复
    - 流结束后保存完整对话记录
    - 检测危机关键词
    """
    # 验证性格标识
    _validate_personality(body.personality)

    # 获取数据库会话和服务
    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async def event_generator():
        """SSE 事件生成器。"""
        async with session_factory() as db:
            try:
                service = _create_conversation_service(db, settings, redis_client)
                async for chunk in service.chat_stream(
                    user_id=user.id,
                    message=body.message,
                    personality=body.personality,
                    conversation_id=body.conversation_id,
                ):
                    yield chunk
            except AppError as e:
                # 业务异常通过 SSE 传递
                error_data = json.dumps(
                    {"content": e.message, "done": True, "error": True},
                    ensure_ascii=False,
                )
                yield f"data: {error_data}\n\n"
            except Exception as e:
                logger.error("[AI Chat Stream] 流式对话异常: %s", str(e))
                error_data = json.dumps(
                    {"content": "AI 服务暂时不可用，请稍后重试", "done": True, "error": True},
                    ensure_ascii=False,
                )
                yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/ai/conversations — 获取对话列表
# ---------------------------------------------------------------------------

@router.get("/conversations", summary="获取对话列表")
async def get_conversations(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
) -> dict[str, Any]:
    """获取用户的对话列表。

    - 按最近活跃时间排序
    - 包含每条对话的最后一条消息预览
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_conversation_service(db, settings, redis_client)
            result = await service.get_conversations(
                user_id=user.id,
                page=page,
                page_size=page_size,
            )
            return paginated_response(
                data=result["items"],
                page=result["page"],
                page_size=result["page_size"],
                total=result["total"],
                request_id=request_id,
            )
        except AppError:
            raise
        except Exception as e:
            logger.error("[AI Conversations] 获取对话列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取对话列表失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/ai/greeting — 获取 AI 开场白
# ---------------------------------------------------------------------------

@router.post("/greeting", summary="获取AI开场白")
async def get_greeting(
    body: GreetingRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取 AI 开场白。

    - 根据当前时间返回动态开场白
    - 如果用户没有对话记录，创建新对话
    - 如果未指定性格，使用上次选择的性格
    """
    request_id = getattr(request.state, "request_id", "")

    # 验证性格标识（如果指定了的话）
    if body.personality:
        _validate_personality(body.personality)

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_conversation_service(db, settings, redis_client)
            result = await service.get_greeting(
                user_id=user.id,
                personality=body.personality,
            )
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[AI Greeting] 获取开场白异常: %s", str(e))
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="获取开场白失败，请稍后重试",
                status_code=503,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/ai/generate-greeting — AI 生成打招呼语
# ---------------------------------------------------------------------------

@router.post(
    "/generate-greeting",
    summary="AI生成打招呼语",
    response_model=GenerateGreetingResponse,
)
async def generate_greeting(
    body: GenerateGreetingRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """AI 生成打招呼语接口。

    用于好友申请场景，AI 协助生成个性化的打招呼语。

    - 分析目标用户的公开动态（最近10条）
    - 分析双方的共同点（共同兴趣标签、相似年龄段等）
    - 生成 3 个版本：温暖型/轻松型/真诚型
    - 频率限制：每用户每天最多使用 10 次
    - 打招呼语长度限制在 50-200 字

    触发时机：
    1. 用户点击"AI帮我想想"按钮
    2. 输入框停留超 30 秒（前端检测，调用同一 API）
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = AIGreetingService(
                db=db,
                zhipu_api_key=settings.zhipu_api_key,
                redis_client=redis_client,
            )
            result = await service.generate_greeting(
                sender_id=user.id,
                target_user_id=body.target_user_id,
            )
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[AI Greeting Generator] 生成打招呼语异常: %s", str(e))
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="打招呼语生成服务暂时不可用，请稍后重试",
                status_code=503,
            )


@router.get(
    "/greeting-quota",
    summary="获取招呼语生成配额",
    response_model=GreetingQuotaResponse,
)
async def get_greeting_quota(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取用户的招呼语生成配额。

    - 返回每日限制、已使用次数、剩余次数
    - 用于前端显示配额状态
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    # check_quota 仅需 Redis，无需数据库会话
    service = AIGreetingService(
        zhipu_api_key=settings.zhipu_api_key,
        redis_client=redis_client,
    )

    try:
        result = await service.check_quota(user.id)
        return success_response(result, request_id)
    except Exception as e:
        logger.error("[AI Greeting Quota] 获取配额异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="获取配额失败",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# AI 聊天辅助端点
# ---------------------------------------------------------------------------

@router.post(
    "/chat-assist/topic",
    summary="冷场救急话题建议",
)
async def suggest_topics(
    body: TopicSuggestionRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """生成冷场救急话题建议。

    场景：双方超10分钟无人回复时，输入框上方提示"AI帮我想想话题"。

    - 分析对话上下文
    - 生成3个有趣的话题建议
    - 频率限制：每用户每2分钟最多3次
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = create_ai_chat_assist_service(
            api_key=settings.zhipu_api_key,
            redis=redis_client,
        )
        result = await service.suggest_topics(
            user_id=user.id,
            context=body.context,
        )
        return success_response(result, request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[AI Chat Assist] 话题建议异常: %s", str(e))
        raise AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message="AI 服务暂时不可用，请稍后重试",
            status_code=503,
        )


@router.post(
    "/chat-assist/reply",
    summary="回复建议",
)
async def suggest_replies(
    body: ReplySuggestionRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """生成回复建议。

    场景：停留1分钟未输入时，输入框上方浮层展示2-3个回复建议。

    - 分析对话上下文和对方最后说的话
    - 生成2-3个回复建议
    - 频率限制：每用户每分钟最多5次
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = create_ai_chat_assist_service(
            api_key=settings.zhipu_api_key,
            redis=redis_client,
        )
        result = await service.suggest_replies(
            user_id=user.id,
            context=body.context,
            last_message=body.last_message,
        )
        return success_response(result, request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[AI Chat Assist] 回复建议异常: %s", str(e))
        raise AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message="AI 服务暂时不可用，请稍后重试",
            status_code=503,
        )


@router.post(
    "/chat-assist/polish",
    summary="语气优化（润色）",
)
async def polish_message(
    body: PolishRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """语气优化（润色）。

    场景：用户点击"AI润色"按钮，优化措辞让聊天更融洽。

    - 保持原意，让语气更温和
    - 适当使用语气词让表达更柔和
    - 频率限制：每用户每分钟最多10次
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = create_ai_chat_assist_service(
            api_key=settings.zhipu_api_key,
            redis=redis_client,
        )
        result = await service.polish_message(
            user_id=user.id,
            original_text=body.original_text,
        )
        return success_response(result, request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[AI Chat Assist] 语气优化异常: %s", str(e))
        raise AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message="AI 服务暂时不可用，请稍后重试",
            status_code=503,
        )


@router.post(
    "/chat-assist/exit",
    summary="温柔退出结束语",
)
async def suggest_exits(
    body: ExitSuggestionRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """生成温柔退出结束语。

    场景：用户想结束聊天但不知道怎么开口，点击右上角"..." → [温柔退出当前对话]。

    - 分析对话上下文
    - 生成2-3个自然的结束语
    - 频率限制：每用户每2分钟最多3次
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = create_ai_chat_assist_service(
            api_key=settings.zhipu_api_key,
            redis=redis_client,
        )
        result = await service.suggest_exits(
            user_id=user.id,
            context=body.context,
        )
        return success_response(result, request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[AI Chat Assist] 温柔退出异常: %s", str(e))
        raise AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message="AI 服务暂时不可用，请稍后重试",
            status_code=503,
        )
