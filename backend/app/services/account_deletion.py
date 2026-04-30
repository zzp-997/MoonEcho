"""账户注销服务模块。

实现用户账户注销的核心业务逻辑，包括：
1. 注销预检查（检查是否可以注销）
2. 数据导出备份（可选）
3. 全量数据删除/匿名化处理
4. 注销进度追踪

安全设计：
- 软删除用户记录（保留审计需要）
- 匿名化敏感数据（手机号、昵称等）
- 级联删除/匿名化关联数据
- 注销后使所有 Token 失效

数据删除策略：
- users: 软删除 + 匿名化
- emotion_diaries: 软删除
- posts: 软删除
- treehole_posts: 匿名化（保留帖子内容但移除用户关联）
- treehole_comments: 匿名化
- anonymous_identities: 硬删除
- ai_conversations: 软删除
- friendships: 硬删除
- friend_requests: 硬删除
- user_blocks: 硬删除
- conversations: 硬删除
- chat_messages: 硬删除
- notifications: 硬删除
- reports: 匿名化（保留举报记录但移除举报人关联）
"""

from __future__ import annotations

import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.ai import AIConversation, AIMemory, AIMessage
from app.models.chat import (
    Conversation,
    FriendRequest,
    Friendship,
    UserBlock,
)
from app.models.diary import EmotionDiary
from app.models.holiday import UserHoliday
from app.models.notification import Notification, PushRecord
from app.models.penalty import DeviceBan, PenaltyRecord
from app.models.post import Post, PostComment, PostFavorite, PostFollow, PostLike
from app.models.report import Report
from app.models.treehole import TreeholeComment, TreeholePost
from app.models.user import (
    AnonymousIdentity,
    User,
    UserAnonMapping,
    UserBoundarySettings,
    UserTag,
)
from app.schemas.account import (
    AccountDeletionResponse,
    DataExportResponse,
    DeletionPreCheckResponse,
    DeletionProgressItem,
    DeletionProgressResponse,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 注销冷却期（秒）- 防止误操作
DELETION_COOLDOWN_SECONDS = 86400  # 24小时

# 数据导出链接有效期（秒）
EXPORT_LINK_EXPIRE_SECONDS = 86400  # 24小时

# 匿名化前缀
ANONYMIZED_PREFIX = "deleted_user_"


# ---------------------------------------------------------------------------
# 账户注销服务
# ---------------------------------------------------------------------------

class AccountDeletionService:
    """账户注销服务。

    提供账户注销的完整流程：
    1. 预检查：检查是否可以注销
    2. 数据导出：可选的数据备份导出
    3. 执行注销：删除/匿名化所有数据
    4. 后处理：使 Token 失效、发送通知等
    """

    def __init__(self, redis: Any) -> None:
        """初始化账户注销服务。

        Args:
            redis: Redis 客户端，用于存储注销进度和使 Token 失效
        """
        self._redis = redis
        logger.info("[AccountDeletionService] 初始化完成")

    # =========================================================================
    # 注销预检查
    # =========================================================================

    async def pre_check(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> DeletionPreCheckResponse:
        """注销预检查。

        检查用户是否可以注销，并展示数据摘要和警告信息。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            DeletionPreCheckResponse: 预检查结果
        """
        warnings: list[str] = []
        can_delete = True

        # 检查是否有待处理的好友申请
        pending_requests_count = await self._count_pending_friend_requests(user_id, db)
        if pending_requests_count > 0:
            warnings.append(f"您有 {pending_requests_count} 条待处理的好友申请")
            # 不阻止注销，只是提醒

        # 检查是否正在注销中
        if await self._is_deletion_in_progress(user_id):
            can_delete = False
            warnings.append("您的账户正在注销处理中")

        # 获取数据摘要
        data_summary = await self._get_data_summary(user_id, db)

        # 添加警告信息
        if data_summary.get("friendships", 0) > 0:
            warnings.append(f"您有 {data_summary['friendships']} 位好友，注销后将解除好友关系")
        if data_summary.get("conversations", 0) > 0:
            warnings.append(f"您有 {data_summary['conversations']} 个聊天会话，聊天记录将被删除")

        return DeletionPreCheckResponse(
            can_delete=can_delete,
            warnings=warnings,
            data_summary=data_summary,
            irreversible_warning="账户注销后，您的所有数据将被永久删除或匿名化处理，此操作不可恢复。",
        )

    # =========================================================================
    # 执行账户注销
    # =========================================================================

    async def execute_deletion(
        self,
        user_id: str,
        reason: str | None,
        export_data: bool,
        auth_service: Any,
        access_token: str,
        db: AsyncSession,
    ) -> AccountDeletionResponse:
        """执行账户注销。

        完整的账户注销流程：
        1. 检查是否可以注销
        2. 可选：生成数据导出
        3. 删除/匿名化所有数据
        4. 使用户 Token 失效
        5. 记录注销日志

        Args:
            user_id: 用户ID
            reason: 注销原因
            export_data: 是否需要导出数据
            auth_service: 认证服务（用于使 Token 失效）
            access_token: 当前访问令牌
            db: 数据库会话

        Returns:
            AccountDeletionResponse: 注销结果

        Raises:
            AppError: 注销失败时抛出
        """
        # 检查是否正在注销中
        if await self._is_deletion_in_progress(user_id):
            raise AppError(
                code=ErrorCode.ACCOUNT_DELETION_IN_PROGRESS,
                message="您的账户正在注销处理中，请勿重复操作",
                status_code=400,
            )

        # 检查用户是否存在
        user = await self._get_user(user_id, db)
        if not user or not user.is_active:
            raise AppError(
                code=ErrorCode.ACCOUNT_ALREADY_DELETED,
                message="账户不存在或已被删除",
                status_code=404,
            )

        # 标记注销进行中
        await self._set_deletion_in_progress(user_id)

        # 开始注销
        started_at = datetime.now(timezone.utc)
        deletion_summary: dict[str, int] = {}

        try:
            # 1. 处理好友关系
            deletion_summary["friendships"] = await self._delete_friendships(user_id, db)
            deletion_summary["friend_requests"] = await self._delete_friend_requests(user_id, db)
            deletion_summary["user_blocks"] = await self._delete_user_blocks(user_id, db)

            # 2. 处理聊天数据
            deletion_summary["conversations"] = await self._delete_conversations(user_id, db)
            deletion_summary["chat_messages"] = await self._delete_chat_messages(user_id, db)

            # 3. 处理动态广场数据
            deletion_summary["posts"] = await self._soft_delete_posts(user_id, db)
            deletion_summary["post_comments"] = await self._soft_delete_post_comments(user_id, db)
            deletion_summary["post_likes"] = await self._delete_post_likes(user_id, db)
            deletion_summary["post_favorites"] = await self._delete_post_favorites(user_id, db)
            deletion_summary["post_follows"] = await self._delete_post_follows(user_id, db)

            # 4. 处理树洞数据（匿名化）
            deletion_summary["treehole_posts"] = await self._anonymize_treehole_posts(user_id, db)
            deletion_summary["treehole_comments"] = await self._anonymize_treehole_comments(user_id, db)

            # 5. 处理情绪日记
            deletion_summary["emotion_diaries"] = await self._soft_delete_diaries(user_id, db)

            # 6. 处理AI对话数据
            deletion_summary["ai_conversations"] = await self._soft_delete_ai_conversations(user_id, db)
            deletion_summary["ai_memories"] = await self._delete_ai_memories(user_id, db)

            # 7. 处理匿名身份
            deletion_summary["anonymous_identities"] = await self._delete_anonymous_identities(user_id, db)

            # 8. 处理通知数据
            deletion_summary["notifications"] = await self._delete_notifications(user_id, db)
            deletion_summary["push_records"] = await self._delete_push_records(user_id, db)

            # 9. 处理举报记录（匿名化）
            deletion_summary["reports"] = await self._anonymize_reports(user_id, db)

            # 10. 处理其他关联数据
            deletion_summary["user_tags"] = await self._delete_user_tags(user_id, db)
            deletion_summary["user_holidays"] = await self._delete_user_holidays(user_id, db)
            deletion_summary["user_boundary_settings"] = await self._delete_user_boundary_settings(user_id, db)
            deletion_summary["weekly_reports"] = await self._soft_delete_weekly_reports(user_id, db)

            # 11. 处理处罚记录
            deletion_summary["penalty_records"] = await self._delete_penalty_records(user_id, db)
            deletion_summary["device_bans"] = await self._clear_device_ban_user_id(user_id, db)

            # 12. 处理用户主表（软删除 + 匿名化）
            await self._anonymize_user(user, reason, db)

            # 提交事务
            await db.commit()

            # 使所有 Token 失效
            await self._invalidate_all_tokens(user_id, auth_service, access_token)

            # 清除注销进行中标记
            await self._clear_deletion_in_progress(user_id)

            deleted_at = datetime.now(timezone.utc)
            logger.info(
                "[AccountDeletion] 账户注销成功: user_id=%s, reason=%s, duration=%s",
                user_id,
                reason,
                deleted_at - started_at,
            )

            return AccountDeletionResponse(
                success=True,
                message="账户已成功注销，感谢您的使用。",
                deleted_at=deleted_at,
                deletion_summary=deletion_summary,
            )

        except AppError:
            await self._clear_deletion_in_progress(user_id)
            raise
        except Exception as e:
            await self._clear_deletion_in_progress(user_id)
            logger.error("[AccountDeletion] 账户注销失败: user_id=%s, error=%s", user_id, str(e))
            raise AppError(
                code=ErrorCode.ACCOUNT_DELETION_FAILED,
                message="账户注销失败，请稍后重试",
                status_code=500,
            )

    # =========================================================================
    # 数据导出（可选功能）
    # =========================================================================

    async def export_user_data(
        self,
        user_id: str,
        db: AsyncSession,
        include_diaries: bool = True,
        include_posts: bool = True,
        include_treehole: bool = True,
        include_ai_conversations: bool = True,
        include_friends: bool = True,
    ) -> DataExportResponse:
        """导出用户数据。

        生成用户数据备份文件，供用户下载。

        Args:
            user_id: 用户ID
            db: 数据库会话
            include_diaries: 是否包含情绪日记
            include_posts: 是否包含动态广场帖子
            include_treehole: 是否包含树洞内容
            include_ai_conversations: 是否包含AI对话记录
            include_friends: 是否包含好友关系

        Returns:
            DataExportResponse: 导出结果
        """
        # 检查是否正在导出
        export_key = f"account:export:{user_id}"
        if await self._redis.exists(export_key):
            raise AppError(
                code=ErrorCode.DATA_EXPORT_IN_PROGRESS,
                message="数据导出正在进行中，请稍后",
                status_code=400,
            )

        # 标记导出进行中
        await self._redis.setex(export_key, 300, "1")  # 5分钟过期

        try:
            export_data: dict[str, Any] = {
                "export_time": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
            }

            # 导出情绪日记
            if include_diaries:
                export_data["diaries"] = await self._export_diaries(user_id, db)

            # 导出动态广场帖子
            if include_posts:
                export_data["posts"] = await self._export_posts(user_id, db)

            # 导出树洞内容
            if include_treehole:
                export_data["treehole"] = await self._export_treehole(user_id, db)

            # 导出AI对话记录
            if include_ai_conversations:
                export_data["ai_conversations"] = await self._export_ai_conversations(user_id, db)

            # 导出好友关系
            if include_friends:
                export_data["friends"] = await self._export_friends(user_id, db)

            # 生成导出文件
            # 实际项目中应该上传到对象存储服务
            # 这里简化处理，生成一个临时链接
            export_id = secrets.token_urlsafe(16)
            export_json = json.dumps(export_data, ensure_ascii=False, default=str)

            # 存储到 Redis（实际应该存储到对象存储）
            export_storage_key = f"export:file:{export_id}"
            await self._redis.setex(
                export_storage_key,
                EXPORT_LINK_EXPIRE_SECONDS,
                export_json,
            )

            expires_at = datetime.now(timezone.utc) + timedelta(seconds=EXPORT_LINK_EXPIRE_SECONDS)

            return DataExportResponse(
                export_url=f"/api/v1/users/me/export/{export_id}",
                expires_at=expires_at,
                file_size=len(export_json.encode("utf-8")),
                format="json",
            )

        finally:
            # 清除导出进行中标记
            await self._redis.delete(export_key)

    # =========================================================================
    # 内部方法：数据删除/匿名化
    # =========================================================================

    async def _get_user(self, user_id: str, db: AsyncSession) -> User | None:
        """获取用户对象。"""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _anonymize_user(
        self,
        user: User,
        reason: str | None,
        db: AsyncSession,
    ) -> None:
        """匿名化用户数据并软删除。

        将用户的敏感信息替换为匿名值，保留审计需要的最小信息。
        """
        # 生成匿名ID
        anon_id = f"{ANONYMIZED_PREFIX}{secrets.token_hex(8)}"

        # 匿名化敏感字段
        user.phone = anon_id
        user.phone_hash = anon_id  # 哈希也匿名化
        user.nickname = None
        user.avatar_url = None
        user.city = None
        user.occupation = None
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        user.social_energy = None
        user.last_active_at = None
        user.notification_settings = None

        db.add(user)
        await db.flush()

        logger.info("[AccountDeletion] 用户数据已匿名化: user_id=%s", user.id)

    async def _delete_friendships(self, user_id: str, db: AsyncSession) -> int:
        """删除好友关系。"""
        stmt = delete(Friendship).where(
            or_(Friendship.user_id_1 == user_id, Friendship.user_id_2 == user_id)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_friend_requests(self, user_id: str, db: AsyncSession) -> int:
        """删除好友申请。"""
        stmt = delete(FriendRequest).where(
            or_(FriendRequest.sender_id == user_id, FriendRequest.recipient_id == user_id)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_user_blocks(self, user_id: str, db: AsyncSession) -> int:
        """删除拉黑关系。"""
        stmt = delete(UserBlock).where(
            or_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == user_id)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_conversations(self, user_id: str, db: AsyncSession) -> int:
        """删除会话。"""
        from app.models.chat import ChatMessage

        # 先删除会话中的消息
        # 查找用户相关的会话ID
        stmt = select(Conversation.id).where(
            or_(Conversation.user_id_1 == user_id, Conversation.user_id_2 == user_id)
        )
        result = await db.execute(stmt)
        conversation_ids = [row[0] for row in result.fetchall()]

        if conversation_ids:
            # 删除消息
            msg_stmt = delete(ChatMessage).where(ChatMessage.conversation_id.in_(conversation_ids))
            await db.execute(msg_stmt)

            # 删除会话
            conv_stmt = delete(Conversation).where(Conversation.id.in_(conversation_ids))
            conv_result = await db.execute(conv_stmt)
            return conv_result.rowcount

        return 0

    async def _delete_chat_messages(self, user_id: str, db: AsyncSession) -> int:
        """删除用户发送的消息（会话删除时已处理，这里处理遗漏）。"""
        from app.models.chat import ChatMessage

        stmt = delete(ChatMessage).where(ChatMessage.sender_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _soft_delete_posts(self, user_id: str, db: AsyncSession) -> int:
        """软删除动态广场帖子。"""
        now = datetime.now(timezone.utc)
        stmt = (
            update(Post)
            .where(Post.user_id == user_id, Post.is_active == True)  # noqa: E712
            .values(is_active=False, deleted_at=now)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _soft_delete_post_comments(self, user_id: str, db: AsyncSession) -> int:
        """软删除动态评论。"""
        now = datetime.now(timezone.utc)
        stmt = (
            update(PostComment)
            .where(PostComment.user_id == user_id, PostComment.is_active == True)  # noqa: E712
            .values(is_active=False, deleted_at=now)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_post_likes(self, user_id: str, db: AsyncSession) -> int:
        """删除点赞记录。"""
        stmt = delete(PostLike).where(PostLike.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_post_favorites(self, user_id: str, db: AsyncSession) -> int:
        """删除收藏记录。"""
        stmt = delete(PostFavorite).where(PostFavorite.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_post_follows(self, user_id: str, db: AsyncSession) -> int:
        """删除悄悄关注记录。"""
        stmt = delete(PostFollow).where(
            or_(PostFollow.follower_id == user_id, PostFollow.following_id == user_id)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _anonymize_treehole_posts(self, user_id: str, db: AsyncSession) -> int:
        """匿名化树洞帖子。

        保留帖子内容但移除与用户的关联。
        树洞本身就是匿名的，这里主要是移除匿名身份关联。
        """
        # 查找用户的匿名身份
        anon_ids = await self._get_user_anon_identity_ids(user_id, db)

        if not anon_ids:
            return 0

        # 移除帖子与匿名身份的关联
        stmt = (
            update(TreeholePost)
            .where(TreeholePost.anon_identity_id.in_(anon_ids))
            .values(anon_identity_id=None)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _anonymize_treehole_comments(self, user_id: str, db: AsyncSession) -> int:
        """匿名化树洞评论。"""
        anon_ids = await self._get_user_anon_identity_ids(user_id, db)

        if not anon_ids:
            return 0

        stmt = (
            update(TreeholeComment)
            .where(TreeholeComment.anon_identity_id.in_(anon_ids))
            .values(anon_identity_id=None)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _soft_delete_diaries(self, user_id: str, db: AsyncSession) -> int:
        """软删除情绪日记。"""
        now = datetime.now(timezone.utc)
        stmt = (
            update(EmotionDiary)
            .where(EmotionDiary.user_id == user_id, EmotionDiary.is_active == True)  # noqa: E712
            .values(is_active=False, deleted_at=now)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _soft_delete_ai_conversations(self, user_id: str, db: AsyncSession) -> int:
        """软删除AI对话会话。"""
        now = datetime.now(timezone.utc)
        stmt = (
            update(AIConversation)
            .where(AIConversation.user_id == user_id, AIConversation.is_active == True)  # noqa: E712
            .values(is_active=False)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_ai_memories(self, user_id: str, db: AsyncSession) -> int:
        """删除AI记忆。"""
        stmt = delete(AIMemory).where(AIMemory.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_anonymous_identities(self, user_id: str, db: AsyncSession) -> int:
        """删除匿名身份和映射关系。"""
        anon_ids = await self._get_user_anon_identity_ids(user_id, db)

        if not anon_ids:
            return 0

        # 删除映射关系
        mapping_stmt = delete(UserAnonMapping).where(UserAnonMapping.anon_identity_id.in_(anon_ids))
        await db.execute(mapping_stmt)

        # 删除匿名身份
        anon_stmt = delete(AnonymousIdentity).where(AnonymousIdentity.id.in_(anon_ids))
        result = await db.execute(anon_stmt)
        return result.rowcount

    async def _delete_notifications(self, user_id: str, db: AsyncSession) -> int:
        """删除通知。"""
        stmt = delete(Notification).where(Notification.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_push_records(self, user_id: str, db: AsyncSession) -> int:
        """删除推送记录。"""
        stmt = delete(PushRecord).where(PushRecord.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _anonymize_reports(self, user_id: str, db: AsyncSession) -> int:
        """匿名化举报记录。

        保留举报记录用于审核统计，但移除举报人关联。
        """
        # 举报人匿名化
        stmt = (
            update(Report)
            .where(Report.reporter_id == user_id)
            .values(reporter_id=None)
        )
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_user_tags(self, user_id: str, db: AsyncSession) -> int:
        """删除用户标签。"""
        stmt = delete(UserTag).where(UserTag.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_user_holidays(self, user_id: str, db: AsyncSession) -> int:
        """删除用户自定义节日。"""
        stmt = delete(UserHoliday).where(UserHoliday.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_user_boundary_settings(self, user_id: str, db: AsyncSession) -> int:
        """删除用户边界设置。"""
        stmt = delete(UserBoundarySettings).where(UserBoundarySettings.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _soft_delete_weekly_reports(self, user_id: str, db: AsyncSession) -> int:
        """软删除情绪周报。

        周报没有软删除字段，直接硬删除。
        """
        from app.models.weekly_report import WeeklyReport

        stmt = delete(WeeklyReport).where(WeeklyReport.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _delete_penalty_records(self, user_id: str, db: AsyncSession) -> int:
        """删除处罚记录。

        处罚记录硬删除，因为用户已注销。
        """
        stmt = delete(PenaltyRecord).where(PenaltyRecord.user_id == user_id)
        result = await db.execute(stmt)
        return result.rowcount

    async def _clear_device_ban_user_id(self, user_id: str, db: AsyncSession) -> int:
        """清除设备封禁记录中的用户ID关联。

        设备封禁记录保留，但清除用户关联。
        """
        stmt = (
            update(DeviceBan)
            .where(DeviceBan.user_id == user_id)
            .values(user_id=None)
        )
        result = await db.execute(stmt)
        return result.rowcount

    # =========================================================================
    # 内部方法：辅助函数
    # =========================================================================

    async def _get_user_anon_identity_ids(self, user_id: str, db: AsyncSession) -> list[str]:
        """获取用户的匿名身份ID列表。

        通过 UserAnonMapping 表查找用户关联的匿名身份。
        由于 user_id 是加密存储的，这里通过遍历所有映射来匹配。
        """
        # 查询所有映射关系，然后解密匹配
        stmt = select(UserAnonMapping)
        result = await db.execute(stmt)
        mappings = result.scalars().all()

        anon_ids = []
        for mapping in mappings:
            # 解密 encrypted_user_id 进行匹配
            try:
                from app.services.crypto import decrypt_data
                decrypted_user_id = decrypt_data(mapping.encrypted_user_id)
                if decrypted_user_id == user_id:
                    anon_ids.append(mapping.anon_identity_id)
            except Exception:
                # 解密失败，跳过
                continue

        return anon_ids

    async def _count_pending_friend_requests(self, user_id: str, db: AsyncSession) -> int:
        """统计待处理的好友申请数量。"""
        stmt = select(func.count(FriendRequest.id)).where(
            FriendRequest.recipient_id == user_id,
            FriendRequest.status == "pending",
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _get_data_summary(self, user_id: str, db: AsyncSession) -> dict[str, int]:
        """获取用户数据摘要。"""
        summary: dict[str, int] = {}

        # 好友数量
        stmt = select(func.count(Friendship.id)).where(
            or_(Friendship.user_id_1 == user_id, Friendship.user_id_2 == user_id)
        )
        result = await db.execute(stmt)
        summary["friendships"] = result.scalar() or 0

        # 动态数量
        stmt = select(func.count(Post.id)).where(Post.user_id == user_id, Post.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        summary["posts"] = result.scalar() or 0

        # 日记数量
        stmt = select(func.count(EmotionDiary.id)).where(
            EmotionDiary.user_id == user_id, EmotionDiary.is_active == True  # noqa: E712
        )
        result = await db.execute(stmt)
        summary["diaries"] = result.scalar() or 0

        # AI对话数量
        stmt = select(func.count(AIConversation.id)).where(
            AIConversation.user_id == user_id, AIConversation.is_active == True  # noqa: E712
        )
        result = await db.execute(stmt)
        summary["ai_conversations"] = result.scalar() or 0

        # 会话数量
        stmt = select(func.count(Conversation.id)).where(
            or_(Conversation.user_id_1 == user_id, Conversation.user_id_2 == user_id)
        )
        result = await db.execute(stmt)
        summary["conversations"] = result.scalar() or 0

        return summary

    async def _is_deletion_in_progress(self, user_id: str) -> bool:
        """检查是否正在注销中。"""
        key = f"account:deletion:in_progress:{user_id}"
        return await self._redis.exists(key) > 0

    async def _set_deletion_in_progress(self, user_id: str) -> None:
        """标记注销进行中。"""
        key = f"account:deletion:in_progress:{user_id}"
        await self._redis.setex(key, 3600, "1")  # 1小时过期

    async def _clear_deletion_in_progress(self, user_id: str) -> None:
        """清除注销进行中标记。"""
        key = f"account:deletion:in_progress:{user_id}"
        await self._redis.delete(key)

    async def _invalidate_all_tokens(
        self,
        user_id: str,
        auth_service: Any,
        access_token: str,
    ) -> None:
        """使用户所有 Token 失效。

        将当前 Token 加入黑名单，并标记用户所有 Token 无效。
        """
        # 将当前 access_token 加入黑名单
        await auth_service.logout(user_id, access_token)

        # 标记用户所有 Token 需要重新验证
        # 这样新的 Token 也会因为用户已被删除而无法使用
        invalidation_key = f"account:deleted:{user_id}"
        await self._redis.setex(invalidation_key, 86400 * 7, "1")  # 7天过期（refresh_token有效期）

    # =========================================================================
    # 内部方法：数据导出
    # =========================================================================

    async def _export_diaries(self, user_id: str, db: AsyncSession) -> list[dict[str, Any]]:
        """导出情绪日记。"""
        stmt = select(EmotionDiary).where(
            EmotionDiary.user_id == user_id,
            EmotionDiary.is_active == True,  # noqa: E712
        ).order_by(EmotionDiary.record_date.desc())
        result = await db.execute(stmt)
        diaries = result.scalars().all()

        return [
            {
                "id": d.id,
                "record_date": str(d.record_date),
                "emotion_tone": d.emotion_tone,
                "emotion_labels": d.emotion_labels,
                "created_at": d.created_at.isoformat(),
            }
            for d in diaries
        ]

    async def _export_posts(self, user_id: str, db: AsyncSession) -> list[dict[str, Any]]:
        """导出动态广场帖子。"""
        stmt = select(Post).where(
            Post.user_id == user_id,
            Post.is_active == True,  # noqa: E712
        ).order_by(Post.created_at.desc())
        result = await db.execute(stmt)
        posts = result.scalars().all()

        return [
            {
                "id": p.id,
                "content": p.content,
                "image_urls": p.image_urls,
                "visibility": p.visibility,
                "like_count": p.like_count,
                "comment_count": p.comment_count,
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ]

    async def _export_treehole(self, user_id: str, db: AsyncSession) -> list[dict[str, Any]]:
        """导出树洞内容。"""
        anon_ids = await self._get_user_anon_identity_ids(user_id, db)
        if not anon_ids:
            return []

        stmt = select(TreeholePost).where(
            TreeholePost.anon_identity_id.in_(anon_ids),
            TreeholePost.status == "active",
        ).order_by(TreeholePost.created_at.desc())
        result = await db.execute(stmt)
        posts = result.scalars().all()

        return [
            {
                "id": p.id,
                "content": p.content,
                "topic_tag": p.topic_tag,
                "resonance_count": p.resonance_count,
                "comment_count": p.comment_count,
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ]

    async def _export_ai_conversations(self, user_id: str, db: AsyncSession) -> list[dict[str, Any]]:
        """导出AI对话记录。"""
        stmt = select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.is_active == True,  # noqa: E712
        ).order_by(AIConversation.created_at.desc())
        result = await db.execute(stmt)
        conversations = result.scalars().all()

        export_data = []
        for conv in conversations:
            # 获取对话消息
            msg_stmt = select(AIMessage).where(
                AIMessage.conversation_id == conv.id
            ).order_by(AIMessage.created_at)
            msg_result = await db.execute(msg_stmt)
            messages = msg_result.scalars().all()

            export_data.append({
                "id": conv.id,
                "ai_persona": conv.ai_persona,
                "title": conv.title,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in messages
                ],
                "created_at": conv.created_at.isoformat(),
            })

        return export_data

    async def _export_friends(self, user_id: str, db: AsyncSession) -> list[dict[str, Any]]:
        """导出好友关系。"""
        stmt = select(Friendship).where(
            or_(Friendship.user_id_1 == user_id, Friendship.user_id_2 == user_id)
        )
        result = await db.execute(stmt)
        friendships = result.scalars().all()

        friends = []
        for f in friendships:
            # 获取好友信息
            friend_id = f.user_id_2 if f.user_id_1 == user_id else f.user_id_1
            friend_stmt = select(User).where(User.id == friend_id)
            friend_result = await db.execute(friend_stmt)
            friend = friend_result.scalar_one_or_none()

            if friend:
                friends.append({
                    "friend_id": friend_id,
                    "nickname": friend.nickname,
                    "created_at": f.created_at.isoformat(),
                })

        return friends


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_account_deletion_service(redis: Any) -> AccountDeletionService:
    """创建账户注销服务实例。

    Args:
        redis: Redis 客户端

    Returns:
        AccountDeletionService 实例
    """
    return AccountDeletionService(redis)