"""私聊路由模块。

提供私聊功能的 API 端点：
- WebSocket /api/v1/ws/chat        WebSocket 连接端点
- GET     /api/v1/conversations   会话列表
- GET     /api/v1/conversations/:id/messages 历史消息
- POST    /api/v1/conversations/:id/messages 发送消息（HTTP 降级）
- GET     /api/v1/conversations/:id 会话详情

设计原则：
- WebSocket 用于实时消息推送
- HTTP 端点作为降级方案
- 发送消息前验证好友关系
- 图片消息90天自动过期
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)

from app.core.errors import AppError
from app.core.responses import paginated_response, success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.schemas.chat import (
    ConversationDetailResponse,
    ConversationListResponse,
    MarkReadRequest,
    MessageListResponse,
    MessageSentResponse,
    MessageType,
    PullOfflineRequest,
    PullOfflineResponse,
    SendMessageRequest,
    WsEventType,
    WsMessage,
)
from app.services.chat_service import ChatService, create_chat_service
from app.services.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _get_db_session(request: Request) -> Any:
    """从应用状态获取数据库会话工厂。"""
    return request.app.state.db_session


def _get_redis(request: Request) -> Any:
    """从应用状态获取 Redis 客户端。"""
    return request.app.state.redis


def _get_auth_service(request: Request) -> Any:
    """从应用状态获取认证服务。"""
    return request.app.state.auth_service


def _get_connection_manager(request: Request) -> ConnectionManager:
    """从应用状态获取连接管理器。"""
    return request.app.state.connection_manager


def _create_chat_service(redis: Any = Depends(_get_redis)) -> ChatService:
    """创建聊天服务实例。"""
    return create_chat_service(redis=redis)


# ---------------------------------------------------------------------------
# WebSocket 端点
# ---------------------------------------------------------------------------

@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Token"),
    device_id: str = Query(default="default", description="设备ID"),
):
    """WebSocket 聊天端点。

    连接流程：
    1. 从查询参数获取 JWT Token
    2. 验证 Token 有效性
    3. 建立 WebSocket 连接
    4. 进入消息循环

    消息类型：
    - ping: 心跳请求
    - send_message: 发送消息
    - mark_read: 标记已读
    - pull_offline: 拉取离线消息
    """
    # 获取应用状态中的服务实例
    auth_service = websocket.app.state.auth_service
    redis = websocket.app.state.redis
    connection_manager: ConnectionManager = websocket.app.state.connection_manager
    db_session_factory = websocket.app.state.db_session

    # 验证 Token
    try:
        payload = await auth_service.verify_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            # 使用标准 WebSocket 关闭码 1008 (Policy Violation)
            await websocket.close(code=1008, reason="无效的Token")
            return

    except AppError as e:
        await websocket.close(code=1008, reason=e.message)
        return
    except Exception as e:
        logger.error("[WebSocket] Token 验证异常: error_type=%s", type(e).__name__)
        await websocket.close(code=1008, reason="认证失败")
        return

    # 创建聊天服务
    chat_service = create_chat_service(redis=redis)

    # 设置消息处理器
    async def message_handler(
        ws: WebSocket,
        conn_info: Any,
        event_type: WsEventType,
        message: dict[str, Any],
    ) -> None:
        """处理 WebSocket 消息。"""
        try:
            if event_type == WsEventType.SEND_MESSAGE:
                await _handle_send_message(
                    ws, conn_info, message, chat_service,
                    connection_manager, db_session_factory
                )
            elif event_type == WsEventType.MARK_READ:
                await _handle_mark_read(
                    ws, conn_info, message, chat_service,
                    db_session_factory
                )
            elif event_type == WsEventType.PULL_OFFLINE:
                await _handle_pull_offline(
                    ws, conn_info, message, chat_service,
                    db_session_factory
                )
            else:
                logger.warning(
                    "[WebSocket] 未处理的消息类型: %s, user_id=%s",
                    event_type, conn_info.user_id
                )
        except Exception as e:
            logger.error(
                "[WebSocket] 消息处理异常: %s, user_id=%s",
                str(e), conn_info.user_id
            )
            await connection_manager.send_error(
                ws, ErrorCode.INTERNAL_ERROR.value, "服务器内部错误"
            )

    connection_manager.set_message_handler(message_handler)

    # 处理连接
    try:
        await connection_manager.handle_connection(websocket, user_id, device_id)
    except Exception as e:
        logger.error("[WebSocket] 连接处理异常: %s", str(e))


async def _handle_send_message(
    websocket: WebSocket,
    conn_info: Any,
    message: dict[str, Any],
    chat_service: ChatService,
    connection_manager: ConnectionManager,
    db_session_factory: Any,
) -> None:
    """处理发送消息请求。"""
    data = message.get("data", {})

    try:
        # 构建请求
        request = SendMessageRequest(
            conversation_id=data.get("conversation_id"),
            message_type=MessageType(data.get("message_type", "text")),
            content=data.get("content"),
            media_url=data.get("media_url"),
            client_message_id=data.get("client_message_id"),
        )
    except Exception as e:
        await connection_manager.send_error(
            websocket, ErrorCode.INVALID_PARAMETER.value, f"请求参数无效: {str(e)}"
        )
        return

    # 发送消息
    async with db_session_factory() as db:
        try:
            result = await chat_service.send_message(
                user_id=conn_info.user_id,
                request=request,
                db=db,
            )
            await db.commit()

            # 发送成功确认
            await connection_manager.send_personal_message(
                conn_info.user_id,
                {
                    "type": WsEventType.MESSAGE_SENT.value,
                    "data": result.model_dump(mode="json"),
                }
            )

            # 获取会话中的另一个用户
            from sqlalchemy import select
            from app.models.chat import Conversation

            conv_stmt = select(Conversation).where(
                Conversation.id == request.conversation_id
            )
            conv_result = await db.execute(conv_stmt)
            conversation = conv_result.scalar_one_or_none()

            if conversation:
                recipient_id = (
                    conversation.user_id_2
                    if conversation.user_id_1 == conn_info.user_id
                    else conversation.user_id_1
                )

                # 推送给接收者
                await connection_manager.send_personal_message(
                    recipient_id,
                    {
                        "type": WsEventType.NEW_MESSAGE.value,
                        "data": result.message.model_dump(mode="json"),
                    }
                )

        except AppError as e:
            await connection_manager.send_error(
                websocket, e.code.value, e.message
            )
        except Exception as e:
            logger.error("[WebSocket] 发送消息异常: %s", str(e))
            await connection_manager.send_error(
                websocket, ErrorCode.INTERNAL_ERROR.value, "发送消息失败"
            )


async def _handle_mark_read(
    websocket: WebSocket,
    conn_info: Any,
    message: dict[str, Any],
    chat_service: ChatService,
    db_session_factory: Any,
) -> None:
    """处理标记已读请求。"""
    data = message.get("data", {})

    try:
        request = MarkReadRequest(
            conversation_id=data.get("conversation_id"),
            last_message_id=data.get("last_message_id"),
        )
    except Exception as e:
        await connection_manager.send_error(
            websocket, ErrorCode.INVALID_PARAMETER.value, f"请求参数无效: {str(e)}"
        )
        return

    async with db_session_factory() as db:
        try:
            count = await chat_service.mark_messages_read(
                user_id=conn_info.user_id,
                conversation_id=request.conversation_id,
                last_message_id=request.last_message_id,
                db=db,
            )
            await db.commit()

            # 发送已读回执
            await connection_manager.send_personal_message(
                conn_info.user_id,
                {
                    "type": WsEventType.MESSAGE_READ.value,
                    "data": {
                        "conversation_id": request.conversation_id,
                        "last_message_id": request.last_message_id,
                        "count": count,
                    },
                }
            )

        except AppError as e:
            await connection_manager.send_error(
                websocket, e.code.value, e.message
            )


async def _handle_pull_offline(
    websocket: WebSocket,
    conn_info: Any,
    message: dict[str, Any],
    chat_service: ChatService,
    db_session_factory: Any,
) -> None:
    """处理拉取离线消息请求。"""
    data = message.get("data", {})

    try:
        request = PullOfflineRequest(
            after_message_id=data.get("after_message_id"),
        )
    except Exception as e:
        await connection_manager.send_error(
            websocket, ErrorCode.INVALID_PARAMETER.value, f"请求参数无效: {str(e)}"
        )
        return

    # 暂时不实现，使用 HTTP 端点获取消息


# ---------------------------------------------------------------------------
# HTTP 端点
# ---------------------------------------------------------------------------

@router.get(
    "/conversations",
    summary="获取会话列表",
)
async def list_conversations(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    chat_service: ChatService = Depends(_create_chat_service),
) -> dict[str, Any]:
    """获取会话列表。

    包含好友信息、最后消息、未读数，按最后消息时间排序。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            result = await chat_service.list_conversations(
                user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Chat] 获取会话列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取会话列表失败",
                status_code=500,
            )


@router.get(
    "/conversations/{conversation_id}",
    summary="获取会话详情",
)
async def get_conversation(
    user: CurrentUser,
    request: Request,
    conversation_id: str = Path(..., description="会话ID"),
    chat_service: ChatService = Depends(_create_chat_service),
) -> dict[str, Any]:
    """获取会话详情。

    包含好友信息和会话基本信息。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            result = await chat_service.get_conversation_detail(
                user_id=user.id,
                conversation_id=conversation_id,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Chat] 获取会话详情异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取会话详情失败",
                status_code=500,
            )


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="获取历史消息",
)
async def get_messages(
    user: CurrentUser,
    request: Request,
    conversation_id: str = Path(..., description="会话ID"),
    after: str | None = Query(default=None, description="起始消息ID（向下翻页）"),
    before: str | None = Query(default=None, description="结束消息ID（向上翻页）"),
    limit: int = Query(default=50, ge=1, le=100, description="消息数量"),
    chat_service: ChatService = Depends(_create_chat_service),
) -> dict[str, Any]:
    """获取历史消息。

    支持双向分页：
    - after: 拉取此消息之后的消息（向下翻页）
    - before: 拉取此消息之前的消息（向上翻页）
    - 不传参数则获取最新消息
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            result = await chat_service.get_conversation_messages(
                user_id=user.id,
                conversation_id=conversation_id,
                db=db,
                after_message_id=after,
                before_message_id=before,
                limit=limit,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Chat] 获取历史消息异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取历史消息失败",
                status_code=500,
            )


@router.post(
    "/conversations/{conversation_id}/messages",
    summary="发送消息（HTTP 降级）",
)
async def send_message_http(
    user: CurrentUser,
    request: Request,
    chat_service: ChatService = Depends(_create_chat_service),
    connection_manager: ConnectionManager = Depends(_get_connection_manager),
    conversation_id: str = Path(..., description="会话ID"),
    body: SendMessageRequest = Body(..., description="发送消息请求"),
) -> dict[str, Any]:
    """发送消息（HTTP 降级方案）。

    当 WebSocket 不可用时，通过 HTTP 发送消息。
    """
    request_id = getattr(request.state, "request_id", "")

    # 确保会话ID一致
    body.conversation_id = conversation_id

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            result = await chat_service.send_message_via_http(
                user_id=user.id,
                request=body,
                db=db,
            )
            await db.commit()

            # 如果接收者在线，尝试通过 WebSocket 推送
            from sqlalchemy import select
            from app.models.chat import Conversation

            conv_stmt = select(Conversation).where(Conversation.id == conversation_id)
            conv_result = await db.execute(conv_stmt)
            conversation = conv_result.scalar_one_or_none()

            if conversation:
                recipient_id = (
                    conversation.user_id_2
                    if conversation.user_id_1 == user.id
                    else conversation.user_id_1
                )

                # 推送给接收者
                await connection_manager.send_personal_message(
                    recipient_id,
                    {
                        "type": WsEventType.NEW_MESSAGE.value,
                        "data": result.message.model_dump(mode="json"),
                    }
                )

            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Chat] 发送消息异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="发送消息失败",
                status_code=500,
            )


@router.post(
    "/conversations/{conversation_id}/read",
    summary="标记已读",
)
async def mark_read(
    user: CurrentUser,
    request: Request,
    chat_service: ChatService = Depends(_create_chat_service),
    conversation_id: str = Path(..., description="会话ID"),
    body: MarkReadRequest = Body(..., description="标记已读请求"),
) -> dict[str, Any]:
    """标记消息为已读。"""
    request_id = getattr(request.state, "request_id", "")

    body.conversation_id = conversation_id

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            count = await chat_service.mark_messages_read(
                user_id=user.id,
                conversation_id=conversation_id,
                last_message_id=body.last_message_id,
                db=db,
            )
            await db.commit()

            return success_response({
                "marked": True,
                "count": count,
            }, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Chat] 标记已读异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="标记已读失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# 图片上传端点
# ---------------------------------------------------------------------------

@router.post(
    "/chat/images",
    summary="上传聊天图片",
)
async def upload_chat_image(
    user: CurrentUser,
    request: Request,
    file: UploadFile = File(..., description="图片文件"),
) -> dict[str, Any]:
    """上传聊天图片。

    图片会被压缩并存储，90天后自动过期。

    限制：
    - 最大文件大小：10MB
    - 支持格式：jpg/png/webp
    """
    request_id = getattr(request.state, "request_id", "")

    # 文件大小限制
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

    # 获取图片服务
    image_service = request.app.state.image_service
    storage_service = request.app.state.storage_service

    try:
        # 读取文件内容
        file_bytes = await file.read()
        filename = file.filename or "image.jpg"

        # 检查文件大小
        if len(file_bytes) > MAX_IMAGE_SIZE:
            raise AppError(
                code=ErrorCode.FILE_TOO_LARGE,
                message=f"图片大小不能超过10MB，当前大小: {len(file_bytes) / 1024 / 1024:.1f}MB",
                status_code=400,
            )

        # 验证格式
        if not await image_service.validate_format(filename):
            raise AppError(
                code=ErrorCode.FILE_TYPE_NOT_ALLOWED,
                message="不支持的图片格式，仅支持 jpg/png/webp",
                status_code=400,
            )

        # 压缩图片
        compressed = await image_service.compress(file_bytes, max_width=1080, quality=85)

        # 保存图片
        url = await storage_service.save(compressed, filename)

        # 计算过期时间
        from datetime import datetime, timedelta, timezone
        expires_at = datetime.now(timezone.utc) + timedelta(days=90)

        return success_response({
            "url": url,
            "expires_at": expires_at.isoformat(),
            "message": "图片上传成功",
        }, request_id)

    except AppError:
        raise
    except Exception as e:
        logger.error("[Chat] 上传图片异常: %s", str(e))
        raise AppError(
            code=ErrorCode.FILE_UPLOAD_FAILED,
            message="图片上传失败",
            status_code=500,
        )
