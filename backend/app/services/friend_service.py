"""好友系统核心服务。

实现好友申请、好友管理、拉黑功能的业务逻辑。

核心业务规则：
1. 好友申请：发送打招呼语 -> 对方同意/忽略 -> 自动建立好友关系+创建会话
2. 过期机制：7天未处理自动过期，过期后申请自动标记为 expired
3. 冷却期：过期后24小时内不能再次向同一用户发送申请
4. 申请限制：同一用户30天内最多发送3次好友申请
5. 官方AI账号：小温/老黑/阿理可被添加为好友，添加后自动建立好友关系
6. 删除好友：对方不收到通知，聊天记录保留但无法继续发送消息
7. 拉黑：对方无法查看动态和主页，无法发送好友申请，聊天记录从双方聊天列表消失
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.chat import Conversation, Friendship, FriendRequest, UserBlock
from app.models.user import User
from app.schemas.friend import (
    BlockedUserResponse,
    BlockListResponse,
    BlockUserResponse,
    CooldownCheckResponse,
    DeleteFriendResponse,
    FriendListResponse,
    FriendRequestListResponse,
    FriendRequestResponse,
    FriendRequestSender,
    FriendResponse,
    FriendUserInfo,
    HandleFriendRequestResponse,
    SendFriendRequestRequest,
    SendFriendRequestResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 好友申请过期时间（7天）
REQUEST_EXPIRE_DAYS = 7

# 过期后冷却期（24小时）
COOLDOWN_HOURS = 24

# 30天内最大申请次数
MAX_REQUESTS_PER_30_DAYS = 3

# 官方AI账号配置
OFFICIAL_AI_ACCOUNTS: dict[str, dict[str, str]] = {
    "xiaowen": {
        "nickname": "小温",
        "avatar_url": "/assets/avatars/xiaowen.png",
        "persona_type": "xiaowen",
    },
    "lahei": {
        "nickname": "老黑",
        "avatar_url": "/assets/avatars/lahei.png",
        "persona_type": "lahei",
    },
    "ali": {
        "nickname": "阿理",
        "avatar_url": "/assets/avatars/ali.png",
        "persona_type": "ali",
    },
}


class FriendService:
    """好友系统核心服务。

    实现：
    1. 好友申请发送、同意、忽略
    2. 好友列表查询、删除好友
    3. 拉黑/取消拉黑
    4. 官方AI账号好友管理
    5. 过期自动标记
    6. 冷却期和申请次数限制

    使用示例：
        service = FriendService()
        result = await service.send_friend_request(user_id, request, db)
    """

    def __init__(self) -> None:
        """初始化好友服务。"""
        logger.info("[FriendService] 初始化完成")

    # =========================================================================
    # 好友申请
    # =========================================================================

    async def send_friend_request(
        self,
        user_id: str,
        request: SendFriendRequestRequest,
        db: AsyncSession,
    ) -> SendFriendRequestResponse:
        """发送好友申请。

        业务规则：
        1. 不能向自己发送申请
        2. 不能向已拉黑自己的用户发送申请
        3. 不能向自己已拉黑的用户发送申请
        4. 不能重复发送（已有 pending 申请时）
        5. 已是好友则不能发送
        6. 过期后需等待24小时冷却期
        7. 同一用户30天内最多3次申请

        Args:
            user_id: 发送者用户ID
            request: 申请请求
            db: 数据库会话

        Returns:
            发送好友申请响应

        Raises:
            AppError: 各种业务规则校验失败
        """
        recipient_id = request.recipient_id

        # 1. 不能向自己发送申请
        if user_id == recipient_id:
            raise AppError(
                code=ErrorCode.CANNOT_ADD_SELF,
                message="不能向自己发送好友申请",
                status_code=400,
            )

        # 2. 检查接收者是否存在
        recipient = await self._get_user_or_raise(recipient_id, db)

        # 3. 检查是否被对方拉黑
        block_stmt = select(UserBlock).where(
            UserBlock.blocker_id == recipient_id,
            UserBlock.blocked_id == user_id,
        )
        block_result = await db.execute(block_stmt)
        if block_result.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.BLOCKED_BY_USER,
                message="对方已将你拉黑，无法发送好友申请",
                status_code=403,
            )

        # 4. 检查是否已拉黑对方
        my_block_stmt = select(UserBlock).where(
            UserBlock.blocker_id == user_id,
            UserBlock.blocked_id == recipient_id,
        )
        my_block_result = await db.execute(my_block_stmt)
        if my_block_result.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.USER_ALREADY_BLOCKED,
                message="你已拉黑对方，请先取消拉黑",
                status_code=403,
            )

        # 5. 检查是否已是好友
        is_friend = await self._check_friendship(user_id, recipient_id, db)
        if is_friend:
            raise AppError(
                code=ErrorCode.ALREADY_FRIENDS,
                message="你们已经是好友了",
                status_code=400,
            )

        # 6. 检查是否有 pending 状态的申请（任一方发送的）
        pending_stmt = select(FriendRequest).where(
            or_(
                and_(
                    FriendRequest.sender_id == user_id,
                    FriendRequest.recipient_id == recipient_id,
                ),
                and_(
                    FriendRequest.sender_id == recipient_id,
                    FriendRequest.recipient_id == user_id,
                ),
            ),
            FriendRequest.status == "pending",
        )
        pending_result = await db.execute(pending_stmt)
        if pending_result.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_ALREADY_HANDLED,
                message="已存在待处理的好友申请",
                status_code=400,
            )

        # 7. 检查冷却期和申请次数限制
        cooldown_check = await self._check_cooldown_and_limits(
            user_id, recipient_id, db,
        )
        if not cooldown_check.can_send:
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_EXPIRED,
                message=cooldown_check.message,
                status_code=429,
            )

        # 8. 标记过期的申请（对当前用户对的过期申请进行标记）
        await self._expire_old_requests(user_id, recipient_id, db)

        # 9. 计算申请序号
        request_number = await self._get_next_request_number(
            user_id, recipient_id, db,
        )

        # 10. 创建好友申请
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=REQUEST_EXPIRE_DAYS)

        friend_request = FriendRequest(
            id=str(uuid.uuid4()),
            sender_id=user_id,
            recipient_id=recipient_id,
            greeting_message=request.greeting_message,
            status="pending",
            expires_at=expires_at,
            request_number=request_number,
        )
        db.add(friend_request)

        logger.info(
            "[FriendService] 发送好友申请，发送者: %s，接收者: %s，申请ID: %s",
            user_id, recipient_id, friend_request.id,
        )

        return SendFriendRequestResponse(
            request_id=friend_request.id,
            expires_at=expires_at,
            greeting_message=request.greeting_message,
            message="好友申请已发送",
        )

    async def list_friend_requests(
        self,
        user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> FriendRequestListResponse:
        """获取收到的好友申请列表。

        自动标记过期申请，按时间倒序排列。

        Args:
            user_id: 当前用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            好友申请列表响应
        """
        now = datetime.now(timezone.utc)

        # 自动标记过期的申请
        await self._auto_expire_requests(user_id, db)

        # 查询收到的申请总数
        count_stmt = select(func.count(FriendRequest.id)).where(
            FriendRequest.recipient_id == user_id,
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询待处理数量
        pending_count_stmt = select(func.count(FriendRequest.id)).where(
            FriendRequest.recipient_id == user_id,
            FriendRequest.status == "pending",
        )
        pending_count_result = await db.execute(pending_count_stmt)
        pending_count = pending_count_result.scalar() or 0

        # 查询申请列表（按时间倒序，pending 优先）
        stmt = (
            select(FriendRequest)
            .where(FriendRequest.recipient_id == user_id)
            .order_by(
                # pending 状态排在最前
                func.field(FriendRequest.status, "pending", "accepted", "rejected", "expired"),
                desc(FriendRequest.created_at),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        requests = result.scalars().all()

        # 批量查询发送者信息
        sender_ids = [r.sender_id for r in requests]
        senders_map: dict[str, User] = {}
        if sender_ids:
            sender_stmt = select(User).where(User.id.in_(set(sender_ids)))
            sender_result = await db.execute(sender_stmt)
            for user in sender_result.scalars().all():
                senders_map[user.id] = user

        # 构建响应
        request_responses = []
        for req in requests:
            sender = senders_map.get(req.sender_id)
            sender_info = FriendRequestSender(
                user_id=req.sender_id,
                nickname=sender.nickname if sender else None,
                avatar_url=sender.avatar_url if sender else None,
            )

            is_expired = req.status == "expired" or (
                req.status == "pending" and now >= req.expires_at
            )

            request_responses.append(
                FriendRequestResponse(
                    id=req.id,
                    sender=sender_info,
                    greeting_message=req.greeting_message,
                    status=req.status if req.status != "pending" or not is_expired else "expired",
                    created_at=req.created_at,
                    expires_at=req.expires_at,
                    is_expired=is_expired,
                )
            )

        pagination = {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "hasMore": page * page_size < total,
        }

        return FriendRequestListResponse(
            data=request_responses,
            pending_count=pending_count,
            pagination=pagination,
        )

    async def accept_friend_request(
        self,
        user_id: str,
        request_id: str,
        db: AsyncSession,
    ) -> HandleFriendRequestResponse:
        """同意好友申请。

        业务规则：
        1. 申请必须存在且属于当前用户
        2. 申请状态必须为 pending
        3. 同意后自动创建好友关系和会话
        4. 同意后发送者收到通知

        Args:
            user_id: 当前用户ID（接收者）
            request_id: 好友申请ID
            db: 数据库会话

        Returns:
            处理好友申请响应

        Raises:
            AppError: 申请不存在、已处理或已过期
        """
        now = datetime.now(timezone.utc)

        # 查询好友申请（使用行级锁防止并发竞态条件）
        friend_request = await self._get_request_or_raise(
            request_id, user_id, db, must_be_recipient=True, for_update=True,
        )

        # 检查状态
        if friend_request.status != "pending":
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_ALREADY_HANDLED,
                message="该好友申请已被处理",
                status_code=400,
            )

        # 检查是否过期
        if now >= friend_request.expires_at:
            # 自动标记为过期
            friend_request.status = "expired"
            friend_request.handled_at = now
            await db.flush()
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_EXPIRED,
                message="该好友申请已过期",
                status_code=400,
            )

        # 检查是否已是好友（可能对方在申请期间通过其他方式成为好友）
        is_friend = await self._check_friendship(
            user_id, friend_request.sender_id, db,
        )
        if is_friend:
            friend_request.status = "accepted"
            friend_request.handled_at = now
            await db.flush()
            raise AppError(
                code=ErrorCode.ALREADY_FRIENDS,
                message="你们已经是好友了",
                status_code=400,
            )

        # 更新申请状态
        friend_request.status = "accepted"
        friend_request.handled_at = now

        # 创建好友关系
        friendship, conversation = await self._create_friendship_and_conversation(
            user_id_1=friend_request.sender_id,
            user_id_2=user_id,
            request_id=friend_request.id,
            db=db,
        )

        logger.info(
            "[FriendService] 同意好友申请，申请ID: %s，好友关系: %s，会话: %s",
            request_id, friendship.id, conversation.id,
        )

        return HandleFriendRequestResponse(
            success=True,
            message="已通过好友申请，去打个招呼吧~",
            conversation_id=conversation.id,
        )

    async def reject_friend_request(
        self,
        user_id: str,
        request_id: str,
        db: AsyncSession,
    ) -> HandleFriendRequestResponse:
        """忽略好友申请。

        业务规则：
        1. 申请必须存在且属于当前用户
        2. 申请状态必须为 pending
        3. 忽略后发送者不会收到通知（降低社交压力）

        Args:
            user_id: 当前用户ID（接收者）
            request_id: 好友申请ID
            db: 数据库会话

        Returns:
            处理好友申请响应

        Raises:
            AppError: 申请不存在或已处理
        """
        now = datetime.now(timezone.utc)

        # 查询好友申请
        friend_request = await self._get_request_or_raise(
            request_id, user_id, db, must_be_recipient=True,
        )

        # 检查状态
        if friend_request.status != "pending":
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_ALREADY_HANDLED,
                message="该好友申请已被处理",
                status_code=400,
            )

        # 更新申请状态（忽略，发送者不收到通知）
        friend_request.status = "rejected"
        friend_request.handled_at = now

        logger.info(
            "[FriendService] 忽略好友申请，申请ID: %s，用户: %s",
            request_id, user_id,
        )

        return HandleFriendRequestResponse(
            success=True,
            message="已忽略该好友申请",
            conversation_id=None,
        )

    # =========================================================================
    # 好友管理
    # =========================================================================

    async def list_friends(
        self,
        user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> FriendListResponse:
        """获取好友列表。

        包含好友基本信息和会话状态，按最后消息时间排序。

        Args:
            user_id: 当前用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            好友列表响应
        """
        # 查询好友关系
        friend_stmt = select(Friendship).where(
            or_(
                Friendship.user_id_1 == user_id,
                Friendship.user_id_2 == user_id,
            ),
        )
        friend_result = await db.execute(friend_stmt)
        friendships = friend_result.scalars().all()

        # 获取好友ID列表
        friend_ids: list[str] = []
        friendship_map: dict[str, Friendship] = {}
        for f in friendships:
            friend_id = f.user_id_2 if f.user_id_1 == user_id else f.user_id_1
            friend_ids.append(friend_id)
            friendship_map[friend_id] = f

        # 查询好友总数
        total = len(friend_ids)

        # 分页处理
        start = (page - 1) * page_size
        end = start + page_size
        paged_friend_ids = friend_ids[start:end]

        if not paged_friend_ids:
            return FriendListResponse(
                data=[],
                total_count=total,
                pagination={
                    "page": page,
                    "pageSize": page_size,
                    "total": total,
                    "hasMore": False,
                },
            )

        # 批量查询好友用户信息
        user_stmt = select(User).where(User.id.in_(paged_friend_ids))
        user_result = await db.execute(user_stmt)
        users_map: dict[str, User] = {}
        for user in user_result.scalars().all():
            users_map[user.id] = user

        # 批量查询会话信息（优化：避免 N+1 查询）
        conversations_map: dict[str, Conversation] = {}
        if paged_friend_ids:
            # 查询当前用户相关的所有会话，然后筛选好友对应的会话
            conv_stmt = select(Conversation).where(
                or_(
                    Conversation.user_id_1 == user_id,
                    Conversation.user_id_2 == user_id,
                )
            )
            conv_result = await db.execute(conv_stmt)
            for conv in conv_result.scalars().all():
                # 找出会话中的好友ID
                friend_id = conv.user_id_2 if conv.user_id_1 == user_id else conv.user_id_1
                if friend_id in paged_friend_ids:
                    conversations_map[friend_id] = conv

        # 构建响应（按最后消息时间排序，无消息的排在后面）
        friend_responses: list[FriendResponse] = []
        for friend_id in paged_friend_ids:
            friend_user = users_map.get(friend_id)
            friendship = friendship_map.get(friend_id)
            conversation = conversations_map.get(friend_id)

            if not friend_user or not friendship:
                continue

            # 检查是否为官方AI账号
            is_official_ai = friend_id in self._get_official_ai_user_ids()

            friend_info = FriendUserInfo(
                user_id=friend_id,
                nickname=friend_user.nickname,
                avatar_url=friend_user.avatar_url,
                is_official_ai=is_official_ai,
            )

            friend_responses.append(
                FriendResponse(
                    friendship_id=friendship.id,
                    friend=friend_info,
                    conversation_id=conversation.id if conversation else None,
                    last_message_preview=conversation.last_message_preview if conversation else None,
                    last_message_at=conversation.last_message_at if conversation else None,
                    created_at=friendship.created_at,
                )
            )

        # 排序：有最后消息时间的按时间倒序，无消息的排在后面
        friend_responses.sort(
            key=lambda x: x.last_message_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        pagination = {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "hasMore": page * page_size < total,
        }

        return FriendListResponse(
            data=friend_responses,
            total_count=total,
            pagination=pagination,
        )

    async def delete_friend(
        self,
        user_id: str,
        friend_user_id: str,
        db: AsyncSession,
    ) -> DeleteFriendResponse:
        """删除好友。

        业务规则：
        1. 对方不会收到通知
        2. 聊天记录保留但无法继续发送消息
        3. 删除后可以重新发送好友申请

        Args:
            user_id: 当前用户ID
            friend_user_id: 要删除的好友用户ID
            db: 数据库会话

        Returns:
            删除好友响应

        Raises:
            AppError: 好友关系不存在
        """
        # 查找好友关系
        friendship = await self._get_friendship_or_raise(user_id, friend_user_id, db)

        # 删除好友关系（物理删除，聊天记录保留在 conversations 中）
        await db.delete(friendship)

        logger.info(
            "[FriendService] 删除好友，用户: %s，好友: %s",
            user_id, friend_user_id,
        )

        return DeleteFriendResponse(
            deleted=True,
            message="已删除好友",
        )

    # =========================================================================
    # 拉黑管理
    # =========================================================================

    async def block_user(
        self,
        user_id: str,
        blocked_user_id: str,
        db: AsyncSession,
        reason: str | None = None,
    ) -> BlockUserResponse:
        """拉黑用户。

        业务规则：
        1. 不能拉黑自己
        2. 不能重复拉黑
        3. 拉黑后自动删除好友关系
        4. 拉黑后对方无法查看动态和主页
        5. 拉黑后对方无法发送好友申请
        6. 聊天记录从双方的聊天列表中消失

        Args:
            user_id: 当前用户ID
            blocked_user_id: 被拉黑用户ID
            db: 数据库会话
            reason: 拉黑原因

        Returns:
            拉黑用户响应

        Raises:
            AppError: 不能拉黑自己或已被拉黑
        """
        # 不能拉黑自己
        if user_id == blocked_user_id:
            raise AppError(
                code=ErrorCode.CANNOT_ADD_SELF,
                message="不能拉黑自己",
                status_code=400,
            )

        # 检查被拉黑用户是否存在
        blocked_user = await self._get_user_or_raise(blocked_user_id, db)

        # 检查是否已拉黑
        existing_block_stmt = select(UserBlock).where(
            UserBlock.blocker_id == user_id,
            UserBlock.blocked_id == blocked_user_id,
        )
        existing_block_result = await db.execute(existing_block_stmt)
        if existing_block_result.scalar_one_or_none():
            raise AppError(
                code=ErrorCode.USER_ALREADY_BLOCKED,
                message="你已经拉黑了该用户",
                status_code=400,
            )

        # 创建拉黑记录
        block = UserBlock(
            id=str(uuid.uuid4()),
            blocker_id=user_id,
            blocked_id=blocked_user_id,
            reason=reason,
        )
        db.add(block)

        # 删除好友关系（如果存在）
        friendship_stmt = select(Friendship).where(
            or_(
                and_(
                    Friendship.user_id_1 == min(user_id, blocked_user_id),
                    Friendship.user_id_2 == max(user_id, blocked_user_id),
                ),
            ),
        )
        friendship_result = await db.execute(friendship_stmt)
        friendship = friendship_result.scalar_one_or_none()
        if friendship:
            await db.delete(friendship)
            logger.info(
                "[FriendService] 拉黑时自动删除好友关系，用户: %s，被拉黑: %s",
                user_id, blocked_user_id,
            )

        # 拒绝所有待处理的申请（双向）
        pending_stmt = select(FriendRequest).where(
            or_(
                and_(
                    FriendRequest.sender_id == user_id,
                    FriendRequest.recipient_id == blocked_user_id,
                ),
                and_(
                    FriendRequest.sender_id == blocked_user_id,
                    FriendRequest.recipient_id == user_id,
                ),
            ),
            FriendRequest.status == "pending",
        )
        pending_result = await db.execute(pending_stmt)
        pending_requests = pending_result.scalars().all()

        now = datetime.now(timezone.utc)
        for req in pending_requests:
            req.status = "rejected"
            req.handled_at = now

        logger.info(
            "[FriendService] 拉黑用户，拉黑者: %s，被拉黑: %s",
            user_id, blocked_user_id,
        )

        blocked_info = FriendUserInfo(
            user_id=blocked_user_id,
            nickname=blocked_user.nickname,
            avatar_url=blocked_user.avatar_url,
            is_official_ai=False,
        )

        return BlockUserResponse(
            block_id=block.id,
            blocked_user=blocked_info,
            message="已拉黑该用户",
        )

    async def unblock_user(
        self,
        user_id: str,
        blocked_user_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """取消拉黑用户。

        Args:
            user_id: 当前用户ID
            blocked_user_id: 被拉黑用户ID
            db: 数据库会话

        Returns:
            取消拉黑结果

        Raises:
            AppError: 拉黑记录不存在
        """
        # 查找拉黑记录
        block_stmt = select(UserBlock).where(
            UserBlock.blocker_id == user_id,
            UserBlock.blocked_id == blocked_user_id,
        )
        block_result = await db.execute(block_stmt)
        block = block_result.scalar_one_or_none()

        if not block:
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_NOT_FOUND,
                message="未拉黑该用户",
                status_code=404,
            )

        # 删除拉黑记录
        await db.delete(block)

        logger.info(
            "[FriendService] 取消拉黑，用户: %s，被拉黑: %s",
            user_id, blocked_user_id,
        )

        return {"unblocked": True, "message": "已取消拉黑"}

    async def list_blocked_users(
        self,
        user_id: str,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> BlockListResponse:
        """获取拉黑列表。

        Args:
            user_id: 当前用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            拉黑列表响应
        """
        # 查询总数
        count_stmt = select(func.count(UserBlock.id)).where(
            UserBlock.blocker_id == user_id,
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询拉黑列表
        stmt = (
            select(UserBlock)
            .where(UserBlock.blocker_id == user_id)
            .order_by(desc(UserBlock.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        blocks = result.scalars().all()

        # 批量查询被拉黑用户信息
        blocked_ids = [b.blocked_id for b in blocks]
        users_map: dict[str, User] = {}
        if blocked_ids:
            user_stmt = select(User).where(User.id.in_(set(blocked_ids)))
            user_result = await db.execute(user_stmt)
            for user in user_result.scalars().all():
                users_map[user.id] = user

        # 构建响应
        blocked_responses = []
        for block in blocks:
            blocked_user = users_map.get(block.blocked_id)
            blocked_info = FriendUserInfo(
                user_id=block.blocked_id,
                nickname=blocked_user.nickname if blocked_user else None,
                avatar_url=blocked_user.avatar_url if blocked_user else None,
                is_official_ai=False,
            )

            blocked_responses.append(
                BlockedUserResponse(
                    block_id=block.id,
                    blocked_user=blocked_info,
                    reason=block.reason,
                    created_at=block.created_at,
                )
            )

        pagination = {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "hasMore": page * page_size < total,
        }

        return BlockListResponse(
            data=blocked_responses,
            total_count=total,
            pagination=pagination,
        )

    # =========================================================================
    # 官方AI账号好友
    # =========================================================================

    async def add_official_ai_friend(
        self,
        user_id: str,
        ai_user_id: str,
        db: AsyncSession,
    ) -> HandleFriendRequestResponse:
        """添加官方AI账号为好友。

        官方AI账号（小温/老黑/阿理）添加后自动建立好友关系，
        无需申请流程。

        Args:
            user_id: 当前用户ID
            ai_user_id: 官方AI账号用户ID
            db: 数据库会话

        Returns:
            处理结果

        Raises:
            AppError: 非官方AI账号或已是好友
        """
        # 检查是否为官方AI账号
        official_ai_ids = self._get_official_ai_user_ids()
        if ai_user_id not in official_ai_ids:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="该用户不是官方AI账号",
                status_code=400,
            )

        # 检查是否已是好友
        is_friend = await self._check_friendship(user_id, ai_user_id, db)
        if is_friend:
            raise AppError(
                code=ErrorCode.ALREADY_FRIENDS,
                message="你已经添加了该AI好友",
                status_code=400,
            )

        # 直接建立好友关系和会话
        friendship, conversation = await self._create_friendship_and_conversation(
            user_id_1=user_id,
            user_id_2=ai_user_id,
            request_id=None,
            db=db,
        )

        logger.info(
            "[FriendService] 添加官方AI好友，用户: %s，AI: %s，好友关系: %s",
            user_id, ai_user_id, friendship.id,
        )

        return HandleFriendRequestResponse(
            success=True,
            message="已添加AI好友",
            conversation_id=conversation.id,
        )

    # =========================================================================
    # 冷却期检查
    # =========================================================================

    async def check_cooldown(
        self,
        user_id: str,
        target_user_id: str,
        db: AsyncSession,
    ) -> CooldownCheckResponse:
        """检查是否可以向目标用户发送好友申请。

        Args:
            user_id: 发送者用户ID
            target_user_id: 目标用户ID
            db: 数据库会话

        Returns:
            冷却期检查响应
        """
        return await self._check_cooldown_and_limits(user_id, target_user_id, db)

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

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

    async def _get_request_or_raise(
        self,
        request_id: str,
        user_id: str,
        db: AsyncSession,
        must_be_recipient: bool = True,
        for_update: bool = False,
    ) -> FriendRequest:
        """获取好友申请或抛出异常。

        Args:
            request_id: 申请ID
            user_id: 当前用户ID
            db: 数据库会话
            must_be_recipient: 是否必须是接收者
            for_update: 是否使用行级锁（防止并发问题）

        Returns:
            FriendRequest 对象

        Raises:
            AppError: 申请不存在或无权限
        """
        stmt = select(FriendRequest).where(FriendRequest.id == request_id)

        # 添加行级锁防止并发竞态条件
        if for_update:
            stmt = stmt.with_for_update()

        result = await db.execute(stmt)
        friend_request = result.scalar_one_or_none()

        if not friend_request:
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_NOT_FOUND,
                message="好友申请不存在",
                status_code=404,
            )

        # 验证权限
        if must_be_recipient and friend_request.recipient_id != user_id:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权处理该好友申请",
                status_code=403,
            )

        return friend_request

    async def _check_friendship(
        self,
        user_id_1: str,
        user_id_2: str,
        db: AsyncSession,
    ) -> bool:
        """检查两个用户是否是好友。

        Args:
            user_id_1: 用户ID 1
            user_id_2: 用户ID 2
            db: 数据库会话

        Returns:
            是否是好友
        """
        small_id = min(user_id_1, user_id_2)
        large_id = max(user_id_1, user_id_2)

        stmt = select(Friendship).where(
            Friendship.user_id_1 == small_id,
            Friendship.user_id_2 == large_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _get_friendship_or_raise(
        self,
        user_id: str,
        friend_user_id: str,
        db: AsyncSession,
    ) -> Friendship:
        """获取好友关系或抛出异常。

        Args:
            user_id: 用户ID
            friend_user_id: 好友用户ID
            db: 数据库会话

        Returns:
            Friendship 对象

        Raises:
            AppError: 好友关系不存在
        """
        small_id = min(user_id, friend_user_id)
        large_id = max(user_id, friend_user_id)

        stmt = select(Friendship).where(
            Friendship.user_id_1 == small_id,
            Friendship.user_id_2 == large_id,
        )
        result = await db.execute(stmt)
        friendship = result.scalar_one_or_none()

        if not friendship:
            raise AppError(
                code=ErrorCode.FRIEND_REQUEST_NOT_FOUND,
                message="好友关系不存在",
                status_code=404,
            )

        return friendship

    async def _check_cooldown_and_limits(
        self,
        user_id: str,
        target_user_id: str,
        db: AsyncSession,
    ) -> CooldownCheckResponse:
        """检查冷却期和申请次数限制。

        业务规则：
        1. 过期后24小时冷却期内不能再次发送申请
        2. 同一用户30天内最多发送3次申请

        Args:
            user_id: 发送者用户ID
            target_user_id: 目标用户ID
            db: 数据库会话

        Returns:
            冷却期检查响应
        """
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        # 查询发送者向目标用户发送的所有申请
        stmt = select(FriendRequest).where(
            FriendRequest.sender_id == user_id,
            FriendRequest.recipient_id == target_user_id,
        ).order_by(desc(FriendRequest.created_at))
        result = await db.execute(stmt)
        all_requests = result.scalars().all()

        # 30天内的申请次数
        recent_requests = [
            r for r in all_requests
            if r.created_at >= thirty_days_ago
        ]
        request_count = len(recent_requests)

        # 检查30天限制
        if request_count >= MAX_REQUESTS_PER_30_DAYS:
            # 找到最早的申请时间，计算30天窗口何时重置
            earliest_recent = min(r.created_at for r in recent_requests)
            reset_time = earliest_recent + timedelta(days=30)

            return CooldownCheckResponse(
                can_send=False,
                cooldown_until=reset_time,
                request_count_in_30_days=request_count,
                max_requests_per_30_days=MAX_REQUESTS_PER_30_DAYS,
                message=f"30天内最多发送{MAX_REQUESTS_PER_30_DAYS}次好友申请，请于{reset_time.strftime('%Y-%m-%d %H:%M')}后再试",
            )

        # 检查冷却期（最近一次过期/拒绝的申请后24小时）
        # 遍历找到第一条 expired 或 rejected 状态的申请（按时间倒序，all_requests 已经是倒序）
        for req in all_requests:
            if req.status in ("expired", "rejected"):
                # expired: 从 expires_at 开始计算冷却期（自动过期时 handled_at 可能为空）
                # rejected: 从 handled_at 开始计算冷却期（人工拒绝时一定有 handled_at）
                if req.status == "rejected":
                    cooldown_start = req.handled_at
                else:
                    # expired 状态，使用 expires_at 作为冷却期起点
                    cooldown_start = req.expires_at

                if cooldown_start:
                    cooldown_until = cooldown_start + timedelta(hours=COOLDOWN_HOURS)
                    if now < cooldown_until:
                        return CooldownCheckResponse(
                            can_send=False,
                            cooldown_until=cooldown_until,
                            request_count_in_30_days=request_count,
                            max_requests_per_30_days=MAX_REQUESTS_PER_30_DAYS,
                            message=f"请等待冷却期结束后再发送申请（{cooldown_until.strftime('%Y-%m-%d %H:%M')}后）",
                        )
                # 找到第一条符合条件的申请后退出循环
                break

        return CooldownCheckResponse(
            can_send=True,
            cooldown_until=None,
            request_count_in_30_days=request_count,
            max_requests_per_30_days=MAX_REQUESTS_PER_30_DAYS,
            message="可以发送好友申请",
        )

    async def _expire_old_requests(
        self,
        user_id: str,
        target_user_id: str,
        db: AsyncSession,
    ) -> None:
        """标记过期的申请。

        将超过 expires_at 且状态为 pending 的申请标记为 expired。

        Args:
            user_id: 发送者用户ID
            target_user_id: 目标用户ID
            db: 数据库会话
        """
        now = datetime.now(timezone.utc)

        stmt = select(FriendRequest).where(
            or_(
                and_(
                    FriendRequest.sender_id == user_id,
                    FriendRequest.recipient_id == target_user_id,
                ),
                and_(
                    FriendRequest.sender_id == target_user_id,
                    FriendRequest.recipient_id == user_id,
                ),
            ),
            FriendRequest.status == "pending",
            FriendRequest.expires_at < now,
        )
        result = await db.execute(stmt)
        expired_requests = result.scalars().all()

        for req in expired_requests:
            req.status = "expired"
            req.handled_at = now

        if expired_requests:
            logger.info(
                "[FriendService] 标记 %d 条过期申请，用户对: %s <-> %s",
                len(expired_requests), user_id, target_user_id,
            )

    async def _auto_expire_requests(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> None:
        """自动标记用户收到的过期申请。

        Args:
            user_id: 当前用户ID
            db: 数据库会话
        """
        now = datetime.now(timezone.utc)

        stmt = select(FriendRequest).where(
            FriendRequest.recipient_id == user_id,
            FriendRequest.status == "pending",
            FriendRequest.expires_at < now,
        )
        result = await db.execute(stmt)
        expired_requests = result.scalars().all()

        for req in expired_requests:
            req.status = "expired"
            req.handled_at = now

        if expired_requests:
            logger.info(
                "[FriendService] 自动标记 %d 条过期申请，用户: %s",
                len(expired_requests), user_id,
            )

    async def _get_next_request_number(
        self,
        user_id: str,
        target_user_id: str,
        db: AsyncSession,
    ) -> int:
        """获取下一个申请序号。

        Args:
            user_id: 发送者用户ID
            target_user_id: 目标用户ID
            db: 数据库会话

        Returns:
            下一个申请序号
        """
        stmt = select(func.max(FriendRequest.request_number)).where(
            FriendRequest.sender_id == user_id,
            FriendRequest.recipient_id == target_user_id,
        )
        result = await db.execute(stmt)
        max_number = result.scalar() or 0
        return max_number + 1

    async def _create_friendship_and_conversation(
        self,
        user_id_1: str,
        user_id_2: str,
        request_id: str | None,
        db: AsyncSession,
    ) -> tuple[Friendship, Conversation]:
        """创建好友关系和会话。

        使用较小的 ID 作为 user_id_1，确保存储一致性。

        Args:
            user_id_1: 用户ID 1
            user_id_2: 用户ID 2
            request_id: 关联的好友申请ID（可选）
            db: 数据库会话

        Returns:
            (Friendship, Conversation) 元组
        """
        small_id = min(user_id_1, user_id_2)
        large_id = max(user_id_1, user_id_2)

        # 创建好友关系
        friendship = Friendship(
            id=str(uuid.uuid4()),
            user_id_1=small_id,
            user_id_2=large_id,
            request_id=request_id,
        )
        db.add(friendship)

        # 创建会话
        conversation = Conversation(
            id=str(uuid.uuid4()),
            friendship_id=friendship.id,
            user_id_1=small_id,
            user_id_2=large_id,
        )
        db.add(conversation)

        await db.flush()

        return friendship, conversation

    def _get_official_ai_user_ids(self) -> set[str]:
        """获取官方AI账号的用户ID集合。

        注意：实际运行时需要从数据库查询。
        此处返回空集合作为默认值，具体ID由数据库预置数据决定。
        在迁移脚本中预置了固定UUID的AI账号。

        Returns:
            官方AI账号用户ID集合
        """
        # 官方AI账号的固定UUID（与迁移脚本中保持一致）
        return {
            "ai000001-0000-0000-0000-000000000001",  # 小温
            "ai000002-0000-0000-0000-000000000002",  # 老黑
            "ai000003-0000-0000-0000-000000000003",  # 阿理
        }


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_friend_service() -> FriendService:
    """创建好友系统服务实例。

    Returns:
        FriendService 实例
    """
    return FriendService()