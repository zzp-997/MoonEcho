"""私聊服务模块。

提供私聊功能的业务逻辑：
- 消息发送与持久化
- 离线消息管理
- 会话列表查询
- 消息历史查询
- 骚扰检测（速率限制）
- 图片消息处理（90天过期）

设计要点：
1. 发送消息前验证好友关系
2. 消息持久化到 chat_messages 表
3. 图片消息设置90天过期时间
4. 骚扰检测：1分钟内超过10条消息触发速率限制
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.chat import ChatMessage, Conversation, Friendship
from app.models.user import User
from app.schemas.chat import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUser,
    MessageListResponse,
    MessageResponse,
    MessageSender,
    MessageSentResponse,
    MessageType,
    SendMessageRequest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 图片消息过期时间（天）
IMAGE_EXPIRE_DAYS = 90

# 骚扰检测时间窗口（秒）
RATE_LIMIT_WINDOW = 60  # 1分钟

# 骚扰检测阈值
RATE_LIMIT_THRESHOLD = 10  # 1分钟内超过10条消息

# 离线消息拉取默认限制
DEFAULT_OFFLINE_LIMIT = 100

# 消息历史查询默认限制
DEFAULT_MESSAGE_LIMIT = 50


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

def _rate_limit_key(user_id: str, conversation_id: str) -> str:
    """骚扰检测速率限制 key。"""
    return f"chat:rate:{user_id}:{conversation_id}"


def _last_message_key(user_id: str) -> str:
    """用户最后消息ID key（用于离线消息拉取）。"""
    return f"chat:last_msg:{user_id}"


# ---------------------------------------------------------------------------
# ChatService 核心类
# ---------------------------------------------------------------------------

class ChatService:
    """私聊核心服务。

    实现：
    1. 消息发送与持久化
    2. 离线消息管理
    3. 会话列表查询
    4. 消息历史查询
    5. 骚扰检测
    6. 图片消息过期处理

    使用示例：
        service = ChatService(redis_client)
        result = await service.send_message(user_id, request, db)
    """

    def __init__(self, redis: Any) -> None:
        """初始化私聊服务。

        Args:
            redis: Redis 客户端（用于速率限制）
        """
        self._redis = redis
        logger.info("[ChatService] 初始化完成")

    # =========================================================================
    # 消息发送
    # =========================================================================

    async def send_message(
        self,
        user_id: str,
        request: SendMessageRequest,
        db: AsyncSession,
    ) -> MessageSentResponse:
        """发送消息。

        业务规则：
        1. 验证双方是否为好友
        2. 骚扰检测（速率限制）
        3. 创建消息记录
        4. 更新会话最后消息
        5. 返回消息详情

        Args:
            user_id: 发送者用户ID
            request: 发送消息请求
            db: 数据库会话

        Returns:
            消息发送响应

        Raises:
            AppError: 不是好友、超出速率限制等
        """
        conversation_id = request.conversation_id

        # 1. 查询会话并验证权限
        conversation = await self._get_conversation_or_raise(
            conversation_id, user_id, db,
        )

        # 2. 获取接收者ID
        recipient_id = (
            conversation.user_id_2
            if conversation.user_id_1 == user_id
            else conversation.user_id_1
        )

        # 3. 验证好友关系
        await self._verify_friendship(user_id, recipient_id, db)

        # 4. 骚扰检测
        await self._check_rate_limit(user_id, conversation_id)

        # 5. 验证消息内容
        await self._validate_message_content(request)

        # 6. 创建消息记录
        now = datetime.now(timezone.utc)
        message = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            sender_id=user_id,
            message_type=request.message_type.value,
            content=request.content,
            media_url=request.media_url,
            is_read=False,
        )

        # 如果是图片消息，设置过期时间
        if request.message_type == MessageType.IMAGE:
            message.expires_at = now + timedelta(days=IMAGE_EXPIRE_DAYS)

        db.add(message)

        # 7. 更新会话最后消息
        preview = self._generate_preview(request)
        conversation.last_message_at = now
        conversation.last_message_preview = preview

        await db.flush()

        # 8. 构建响应
        sender = await self._get_user_info(user_id, db)
        message_response = MessageResponse(
            id=message.id,
            conversation_id=conversation_id,
            sender=sender,
            message_type=request.message_type,
            content=request.content,
            media_url=request.media_url,
            is_read=False,
            read_at=None,
            created_at=message.created_at,
            is_expired=False,
        )

        logger.info(
            "[ChatService] 消息发送成功: message_id=%s, from=%s, to=%s",
            message.id, user_id, recipient_id
        )

        return MessageSentResponse(
            message=message_response,
            client_message_id=request.client_message_id,
        )

    async def send_message_via_http(
        self,
        user_id: str,
        request: SendMessageRequest,
        db: AsyncSession,
    ) -> MessageSentResponse:
        """通过 HTTP 发送消息（WebSocket 降级方案）。

        与 send_message 相同，但明确标记为 HTTP 降级使用。

        Args:
            user_id: 发送者用户ID
            request: 发送消息请求
            db: 数据库会话

        Returns:
            消息发送响应
        """
        return await self.send_message(user_id, request, db)

    # =========================================================================
    # 离线消息
    # =========================================================================

    async def get_offline_messages(
        self,
        user_id: str,
        after_message_id: str | None,
        limit: int = DEFAULT_OFFLINE_LIMIT,
    ) -> list[MessageResponse]:
        """获取离线消息。

        拉取用户在所有会话中 after_message_id 之后的消息。

        Args:
            user_id: 用户ID
            after_message_id: 起始消息ID（不包含）
            limit: 消息数量限制

        Returns:
            消息响应列表
        """
        # 此方法需要数据库会话，将在路由层通过 db 参数调用
        # 这里只是接口定义，实际实现在 get_conversation_messages 中
        raise NotImplementedError("请使用 get_conversation_messages 方法")

    # =========================================================================
    # 会话管理
    # =========================================================================

    async def list_conversations(
        self,
        user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> ConversationListResponse:
        """获取会话列表。

        包含好友信息、最后消息、未读数，按最后消息时间排序。

        Args:
            user_id: 用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            会话列表响应
        """
        # 1. 查询用户相关的所有会话
        conv_stmt = (
            select(Conversation)
            .where(
                or_(
                    Conversation.user_id_1 == user_id,
                    Conversation.user_id_2 == user_id,
                )
            )
            .order_by(desc(Conversation.last_message_at))
        )
        conv_result = await db.execute(conv_stmt)
        conversations = conv_result.scalars().all()

        total = len(conversations)

        # 2. 分页处理
        start = (page - 1) * page_size
        end = start + page_size
        paged_conversations = conversations[start:end]

        if not paged_conversations:
            return ConversationListResponse(
                data=[],
                total_count=total,
                pagination={
                    "page": page,
                    "pageSize": page_size,
                    "total": total,
                    "hasMore": False,
                },
            )

        # 3. 批量获取好友信息
        friend_ids = []
        for conv in paged_conversations:
            friend_id = (
                conv.user_id_2
                if conv.user_id_1 == user_id
                else conv.user_id_1
            )
            friend_ids.append(friend_id)

        user_stmt = select(User).where(User.id.in_(set(friend_ids)))
        user_result = await db.execute(user_stmt)
        users_map: dict[str, User] = {}
        for user in user_result.scalars().all():
            users_map[user.id] = user

        # 4. 批量获取未读数
        unread_counts = await self._batch_get_unread_counts(
            user_id, [c.id for c in paged_conversations], db,
        )

        # 5. 批量获取最后一条消息（优化：避免 N+1 查询）
        conversation_ids = [c.id for c in paged_conversations]
        last_messages_map: dict[str, ChatMessage] = {}

        if conversation_ids:
            # 使用子查询获取每个会话的最新消息
            from sqlalchemy import func

            # 方法：使用窗口函数一次性获取所有会话的最后消息
            last_msg_subq = (
                select(
                    ChatMessage,
                    func.row_number()
                    .over(
                        partition_by=ChatMessage.conversation_id,
                        order_by=desc(ChatMessage.created_at)
                    )
                    .label("rn")
                )
                .where(ChatMessage.conversation_id.in_(conversation_ids))
                .subquery()
            )

            last_msg_stmt = select(last_msg_subq).where(last_msg_subq.c.rn == 1)
            last_msg_result = await db.execute(last_msg_stmt)
            for row in last_msg_result.all():
                # row 是一个 Row 对象，包含 ChatMessage 的所有字段
                conv_id = row.conversation_id
                msg = ChatMessage(
                    id=row.id,
                    conversation_id=row.conversation_id,
                    sender_id=row.sender_id,
                    message_type=row.message_type,
                    content=row.content,
                    media_url=row.media_url,
                    is_read=row.is_read,
                    read_at=row.read_at,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                )
                last_messages_map[conv_id] = msg

        # 6. 构建响应
        conv_responses: list[ConversationResponse] = []
        for conv in paged_conversations:
            friend_id = (
                conv.user_id_2
                if conv.user_id_1 == user_id
                else conv.user_id_1
            )
            friend_user = users_map.get(friend_id)

            if not friend_user:
                continue

            # 检查是否为官方AI账号
            is_official_ai = friend_id in self._get_official_ai_user_ids()

            friend_info = ConversationUser(
                user_id=friend_id,
                nickname=friend_user.nickname,
                avatar_url=friend_user.avatar_url,
                is_official_ai=is_official_ai,
            )

            # 从预查询的结果中获取最后一条消息
            last_message = None
            last_msg = last_messages_map.get(conv.id)
            if last_msg:
                sender_user = users_map.get(last_msg.sender_id, friend_user)
                sender_info = MessageSender(
                    user_id=last_msg.sender_id,
                    nickname=sender_user.nickname if sender_user else None,
                    avatar_url=sender_user.avatar_url if sender_user else None,
                )
                last_message = MessageResponse(
                    id=last_msg.id,
                    conversation_id=conv.id,
                    sender=sender_info,
                    message_type=MessageType(last_msg.message_type),
                    content=last_msg.content,
                    media_url=last_msg.media_url,
                    is_read=last_msg.is_read,
                    read_at=last_msg.read_at,
                    created_at=last_msg.created_at,
                    is_expired=self._is_message_expired(last_msg),
                )

            conv_responses.append(
                ConversationResponse(
                    id=conv.id,
                    friend=friend_info,
                    last_message=last_message,
                    last_message_at=conv.last_message_at,
                    unread_count=unread_counts.get(conv.id, 0),
                    created_at=conv.created_at,
                )
            )

        pagination = {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "hasMore": page * page_size < total,
        }

        return ConversationListResponse(
            data=conv_responses,
            total_count=total,
            pagination=pagination,
        )

    async def get_conversation_detail(
        self,
        user_id: str,
        conversation_id: str,
        db: AsyncSession,
    ) -> ConversationDetailResponse:
        """获取会话详情。

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            db: 数据库会话

        Returns:
            会话详情响应

        Raises:
            AppError: 会话不存在或无权限
        """
        conversation = await self._get_conversation_or_raise(
            conversation_id, user_id, db,
        )

        # 获取好友ID
        friend_id = (
            conversation.user_id_2
            if conversation.user_id_1 == user_id
            else conversation.user_id_1
        )

        # 获取好友用户信息
        friend_user = await self._get_user_or_raise(friend_id, db)

        # 检查是否为官方AI账号
        is_official_ai = friend_id in self._get_official_ai_user_ids()

        friend_info = ConversationUser(
            user_id=friend_id,
            nickname=friend_user.nickname,
            avatar_url=friend_user.avatar_url,
            is_official_ai=is_official_ai,
        )

        # 查询好友关系ID
        friendship = await self._get_friendship(user_id, friend_id, db)

        return ConversationDetailResponse(
            id=conversation.id,
            friend=friend_info,
            friendship_id=friendship.id if friendship else None,
            created_at=conversation.created_at,
        )

    async def get_conversation_messages(
        self,
        user_id: str,
        conversation_id: str,
        db: AsyncSession,
        after_message_id: str | None = None,
        before_message_id: str | None = None,
        limit: int = DEFAULT_MESSAGE_LIMIT,
    ) -> MessageListResponse:
        """获取会话历史消息。

        支持双向分页：
        - after_message_id: 拉取此消息之后的消息（向下翻页）
        - before_message_id: 拉取此消息之前的消息（向上翻页）

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            db: 数据库会话
            after_message_id: 起始消息ID（不包含）
            before_message_id: 结束消息ID（不包含）
            limit: 消息数量限制

        Returns:
            消息列表响应

        Raises:
            AppError: 会话不存在或无权限
        """
        # 1. 验证会话权限
        await self._get_conversation_or_raise(conversation_id, user_id, db)

        # 2. 构建查询
        stmt = select(ChatMessage).where(
            ChatMessage.conversation_id == conversation_id
        )

        if after_message_id:
            # 获取 after_message_id 的时间戳
            after_msg = await self._get_message_or_raise(
                after_message_id, conversation_id, db,
            )
            stmt = stmt.where(ChatMessage.created_at > after_msg.created_at)
            stmt = stmt.order_by(ChatMessage.created_at.asc())
        elif before_message_id:
            # 获取 before_message_id 的时间戳
            before_msg = await self._get_message_or_raise(
                before_message_id, conversation_id, db,
            )
            stmt = stmt.where(ChatMessage.created_at < before_msg.created_at)
            stmt = stmt.order_by(desc(ChatMessage.created_at))
        else:
            # 默认按时间倒序
            stmt = stmt.order_by(desc(ChatMessage.created_at))

        stmt = stmt.limit(limit)

        # 3. 执行查询
        result = await db.execute(stmt)
        messages = result.scalars().all()

        # 4. 批量获取发送者信息
        sender_ids = {m.sender_id for m in messages}
        sender_stmt = select(User).where(User.id.in_(sender_ids))
        sender_result = await db.execute(sender_stmt)
        senders_map: dict[str, User] = {}
        for user in sender_result.scalars().all():
            senders_map[user.id] = user

        # 5. 构建响应
        message_responses: list[MessageResponse] = []
        for msg in messages:
            sender_user = senders_map.get(msg.sender_id)
            sender_info = MessageSender(
                user_id=msg.sender_id,
                nickname=sender_user.nickname if sender_user else None,
                avatar_url=sender_user.avatar_url if sender_user else None,
            )

            message_responses.append(
                MessageResponse(
                    id=msg.id,
                    conversation_id=conversation_id,
                    sender=sender_info,
                    message_type=MessageType(msg.message_type),
                    content=msg.content,
                    media_url=msg.media_url,
                    is_read=msg.is_read,
                    read_at=msg.read_at,
                    created_at=msg.created_at,
                    is_expired=self._is_message_expired(msg),
                )
            )

        # 如果是 after 查询，需要反转顺序（按时间正序）
        if after_message_id:
            message_responses.reverse()

        return MessageListResponse(
            data=message_responses,
            conversation_id=conversation_id,
            pagination={
                "limit": limit,
                "hasMore": len(message_responses) >= limit,
            },
        )

    # =========================================================================
    # 已读标记
    # =========================================================================

    async def mark_messages_read(
        self,
        user_id: str,
        conversation_id: str,
        last_message_id: str,
        db: AsyncSession,
    ) -> int:
        """标记消息为已读。

        将会话中所有早于 last_message_id 的消息标记为已读。

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            last_message_id: 最后一条已读消息ID
            db: 数据库会话

        Returns:
            更新的消息数量
        """
        # 1. 验证会话权限
        await self._get_conversation_or_raise(conversation_id, user_id, db)

        # 2. 获取最后消息
        last_msg = await self._get_message_or_raise(
            last_message_id, conversation_id, db,
        )

        # 3. 批量更新已读状态（只更新发送给当前用户的消息）
        now = datetime.now(timezone.utc)

        # 获取当前用户是 user_id_1 还是 user_id_2
        conv_stmt = select(Conversation).where(Conversation.id == conversation_id)
        conv_result = await db.execute(conv_stmt)
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            return 0

        # 当前用户是接收者，需要标记发送给他的消息为已读
        stmt = (
            update(ChatMessage)
            .where(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.sender_id != user_id,
                ChatMessage.created_at <= last_msg.created_at,
                ChatMessage.is_read == False,  # noqa: E712
            )
            .values(is_read=True, read_at=now)
        )

        result = await db.execute(stmt)
        count = result.rowcount or 0

        logger.info(
            "[ChatService] 标记已读: user_id=%s, conversation_id=%s, count=%d",
            user_id, conversation_id, count
        )

        return count

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    async def _get_conversation_or_raise(
        self,
        conversation_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> Conversation:
        """获取会话或抛出异常。

        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            Conversation 对象

        Raises:
            AppError: 会话不存在或无权限
        """
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise AppError(
                code=ErrorCode.CONVERSATION_NOT_FOUND,
                message="会话不存在",
                status_code=404,
            )

        # 验证用户是否属于该会话
        if conversation.user_id_1 != user_id and conversation.user_id_2 != user_id:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权访问此会话",
                status_code=403,
            )

        return conversation

    async def _get_message_or_raise(
        self,
        message_id: str,
        conversation_id: str,
        db: AsyncSession,
    ) -> ChatMessage:
        """获取消息或抛出异常。

        Args:
            message_id: 消息ID
            conversation_id: 会话ID
            db: 数据库会话

        Returns:
            ChatMessage 对象

        Raises:
            AppError: 消息不存在
        """
        stmt = select(ChatMessage).where(
            ChatMessage.id == message_id,
            ChatMessage.conversation_id == conversation_id,
        )
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise AppError(
                code=ErrorCode.MESSAGE_NOT_FOUND,
                message="消息不存在",
                status_code=404,
            )

        return message

    async def _get_user_or_raise(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> User:
        """获取用户或抛出异常。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            User 对象

        Raises:
            AppError: 用户不存在
        """
        stmt = select(User).where(
            User.id == user_id,
            User.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        return user

    async def _verify_friendship(
        self,
        user_id: str,
        friend_id: str,
        db: AsyncSession,
    ) -> None:
        """验证好友关系。

        Args:
            user_id: 用户ID
            friend_id: 好友ID
            db: 数据库会话

        Raises:
            AppError: 不是好友
        """
        small_id = min(user_id, friend_id)
        large_id = max(user_id, friend_id)

        stmt = select(Friendship).where(
            Friendship.user_id_1 == small_id,
            Friendship.user_id_2 == large_id,
        )
        result = await db.execute(stmt)
        friendship = result.scalar_one_or_none()

        if not friendship:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="你们还不是好友，无法发送消息",
                status_code=403,
            )

    async def _get_friendship(
        self,
        user_id: str,
        friend_id: str,
        db: AsyncSession,
    ) -> Friendship | None:
        """获取好友关系。

        Args:
            user_id: 用户ID
            friend_id: 好友ID
            db: 数据库会话

        Returns:
            Friendship 对象或 None
        """
        small_id = min(user_id, friend_id)
        large_id = max(user_id, friend_id)

        stmt = select(Friendship).where(
            Friendship.user_id_1 == small_id,
            Friendship.user_id_2 == large_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_rate_limit(
        self,
        user_id: str,
        conversation_id: str,
    ) -> None:
        """检查骚扰检测速率限制。

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Raises:
            AppError: 超出速率限制
        """
        key = _rate_limit_key(user_id, conversation_id)

        try:
            # 获取当前计数
            count = await self._redis.get(key)

            if count is not None:
                count_val = int(count) if isinstance(count, (int, bytes, str)) else 0
                if isinstance(count, bytes):
                    count_val = int(count.decode("utf-8"))
                elif isinstance(count, str):
                    count_val = int(count)

                if count_val >= RATE_LIMIT_THRESHOLD:
                    ttl = await self._redis.ttl(key)
                    raise AppError(
                        code=ErrorCode.MESSAGE_TOO_FREQUENT,
                        message=f"消息发送过于频繁，请 {ttl} 秒后再试",
                        status_code=429,
                    )

            # 增加计数（每次都重置 TTL 以防止时间窗口滑动问题）
            new_count = await self._redis.incr(key)
            # 每次计数都重置过期时间，确保严格的速率限制
            await self._redis.expire(key, RATE_LIMIT_WINDOW)

        except AppError:
            raise
        except Exception as e:
            logger.warning("[ChatService] 速率限制检查失败: %s", str(e))

    async def _validate_message_content(
        self,
        request: SendMessageRequest,
    ) -> None:
        """验证消息内容。

        Args:
            request: 发送消息请求

        Raises:
            AppError: 消息内容无效
        """
        if request.message_type == MessageType.TEXT:
            if not request.content or not request.content.strip():
                raise AppError(
                    code=ErrorCode.CONTENT_EMPTY,
                    message="消息内容不能为空",
                    status_code=400,
                )
            if len(request.content) > 5000:
                raise AppError(
                    code=ErrorCode.CONTENT_TOO_LONG,
                    message="消息内容不能超过5000字",
                    status_code=400,
                )

        elif request.message_type == MessageType.IMAGE:
            if not request.media_url:
                raise AppError(
                    code=ErrorCode.INVALID_PARAMETER,
                    message="图片消息必须包含图片URL",
                    status_code=400,
                )

    def _generate_preview(
        self,
        request: SendMessageRequest,
    ) -> str:
        """生成消息预览文本。

        Args:
            request: 发送消息请求

        Returns:
            预览文本
        """
        if request.message_type == MessageType.TEXT:
            content = request.content or ""
            # 截取前100个字符作为预览
            return content[:100] + ("..." if len(content) > 100 else "")
        elif request.message_type == MessageType.IMAGE:
            return "[图片]"
        else:
            return "[消息]"

    async def _get_user_info(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> MessageSender:
        """获取用户信息。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            消息发送者信息
        """
        user = await self._get_user_or_raise(user_id, db)
        return MessageSender(
            user_id=user.id,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
        )

    async def _batch_get_unread_counts(
        self,
        user_id: str,
        conversation_ids: list[str],
        db: AsyncSession,
    ) -> dict[str, int]:
        """批量获取会话未读数。

        Args:
            user_id: 用户ID
            conversation_ids: 会话ID列表
            db: 数据库会话

        Returns:
            会话ID -> 未读数映射
        """
        if not conversation_ids:
            return {}

        # 查询每个会话中发送给当前用户且未读的消息数
        stmt = (
            select(
                ChatMessage.conversation_id,
                func.count(ChatMessage.id).label("count"),
            )
            .where(
                ChatMessage.conversation_id.in_(conversation_ids),
                ChatMessage.sender_id != user_id,
                ChatMessage.is_read == False,  # noqa: E712
            )
            .group_by(ChatMessage.conversation_id)
        )

        result = await db.execute(stmt)
        rows = result.all()

        return {row.conversation_id: row.count for row in rows}

    def _is_message_expired(self, message: ChatMessage) -> bool:
        """检查消息是否已过期（图片消息）。

        Args:
            message: 消息对象

        Returns:
            是否已过期
        """
        if message.message_type != MessageType.IMAGE.value:
            return False

        if message.expires_at is None:
            return False

        return datetime.now(timezone.utc) > message.expires_at

    def _get_official_ai_user_ids(self) -> set[str]:
        """获取官方AI账号的用户ID集合。

        Returns:
            官方AI账号用户ID集合
        """
        return {
            "ai000001-0000-0000-0000-000000000001",  # 小温
            "ai000002-0000-0000-0000-000000000002",  # 老黑
            "ai000003-0000-0000-0000-000000000003",  # 阿理
        }


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_chat_service(redis: Any) -> ChatService:
    """创建私聊服务实例。

    Args:
        redis: Redis 客户端

    Returns:
        ChatService 实例
    """
    return ChatService(redis=redis)
