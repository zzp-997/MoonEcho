"""渐进式社交暴露级别计算服务。

实现 modules_design.md 6.4 中定义的六级渐进式社交暴露机制：

Level 1：浏览动态广场（零社交压力）
    ↓ 浏览3次以上
Level 2：点共鸣/点赞（最小社交动作）
    ↓ 共鸣3次以上
Level 3：评论互动（轻度社交）
    ↓ 评论2次以上
Level 4：悄悄关注（单向关注）
    ↓ 关注1人以上
Level 5：发送好友申请（双向连接）
    ↓ 成为好友后
Level 6：私聊（深度社交）

该服务基于用户行为统计数据实时计算社交暴露级别。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Conversation, Friendship
from app.models.post import Post, PostComment, PostFollow, PostLike
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 各级别升级 threshold
LEVEL_THRESHOLDS = {
    1: {"browse": 0},           # Level 1: 默认解锁
    2: {"browse": 3},           # Level 2: 浏览3次以上
    3: {"like": 3},             # Level 3: 共鸣3次以上
    4: {"comment": 2},          # Level 4: 评论2次以上
    5: {"follow": 1},           # Level 5: 关注1人以上
    6: {"friend": 1},           # Level 6: 成为好友后（好友数量>=1）
}

# 级别名称映射
LEVEL_NAMES = {
    1: "观察者",
    2: "共鸣者",
    3: "互动者",
    4: "关注者",
    5: "连接者",
    6: "深度社交",
}

# 级别描述
LEVEL_DESCRIPTIONS = {
    1: "浏览动态广场，零社交压力",
    2: "点共鸣/点赞，最小社交动作",
    3: "评论互动，轻度社交",
    4: "悄悄关注，单向关注",
    5: "发送好友申请，双向连接",
    6: "私聊，深度社交",
}


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class BehaviorStats:
    """用户社交行为统计."""

    browse_count: int = 0       # 浏览动态广场次数
    like_count: int = 0         # 共鸣/点赞次数
    comment_count: int = 0      # 评论次数
    follow_count: int = 0       # 悄悄关注人数
    friend_request_count: int = 0  # 好友申请次数（发送的）
    chat_count: int = 0         # 私聊开启次数


@dataclass
class LevelProgress:
    """级别进度."""

    current_level: int
    level_name: str
    description: str
    progress_description: str
    next_action: str | None


@dataclass
class LevelUnlockStatus:
    """各级别解锁状态."""

    level_1: bool = True
    level_2: bool = False
    level_3: bool = False
    level_4: bool = False
    level_5: bool = False
    level_6: bool = False


# ---------------------------------------------------------------------------
# 社交暴露级别服务
# ---------------------------------------------------------------------------

class SocialLevelService:
    """渐进式社交暴露级别计算服务。

    基于用户行为统计数据实时计算当前社交暴露级别，
    不存储级别值，每次查询时动态计算。

    使用示例：
        service = SocialLevelService()
        result = await service.get_social_level(user_id, db)
    """

    def __init__(self) -> None:
        """初始化社交暴露级别服务。"""
        logger.info("[SocialLevelService] 初始化完成")

    # =========================================================================
    # 主要接口
    # =========================================================================

    async def get_social_level(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """获取用户当前社交暴露级别。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            社交暴露级别响应字典，包含：
            - current_level: 当前级别（1-6）
            - level_name: 级别名称
            - description: 级别描述
            - progress_description: 进度描述
            - unlock_status: 各级别解锁状态
            - next_action: 建议下一步行动
            - behavior_stats: 行为统计数据
        """
        # 1. 收集用户行为统计数据
        stats = await self._collect_behavior_stats(user_id, db)

        # 2. 根据统计数据计算当前级别
        progress = self._calculate_level_progress(stats)

        # 3. 计算各级别解锁状态
        unlock_status = self._calculate_unlock_status(stats)

        # 4. 构建响应
        return {
            "current_level": progress.current_level,
            "level_name": progress.level_name,
            "description": progress.description,
            "progress_description": progress.progress_description,
            "unlock_status": {
                "level_1": unlock_status.level_1,
                "level_2": unlock_status.level_2,
                "level_3": unlock_status.level_3,
                "level_4": unlock_status.level_4,
                "level_5": unlock_status.level_5,
                "level_6": unlock_status.level_6,
            },
            "next_action": progress.next_action,
            "behavior_stats": {
                "browse_count": stats.browse_count,
                "like_count": stats.like_count,
                "comment_count": stats.comment_count,
                "follow_count": stats.follow_count,
                "friend_request_count": stats.friend_request_count,
                "chat_count": stats.chat_count,
            },
        }

    # =========================================================================
    # 行为数据收集
    # =========================================================================

    async def _collect_behavior_stats(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> BehaviorStats:
        """收集用户社交行为统计数据。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            BehaviorStats 实例
        """
        # 1. 共鸣/点赞次数（用户发起的）
        like_count = await self._count_user_likes(user_id, db)

        # 2. 评论次数
        comment_count = await self._count_user_comments(user_id, db)

        # 3. 悄悄关注人数
        follow_count = await self._count_user_follows(user_id, db)

        # 4. 好友申请次数（发送的）
        friend_request_count = await self._count_friend_requests(user_id, db)

        # 5. 好友数量（用于判断Level 6）
        friend_count = await self._count_friends(user_id, db)

        # 6. 私聊开启次数
        chat_count = await self._count_conversations(user_id, db)

        # 注意：浏览次数（browse_count）目前没有埋点数据存储
        # 暂时使用点赞+评论作为活跃度替代指标，设为 like_count + comment_count
        # 后续可接入埋点数据
        browse_count = like_count + comment_count

        return BehaviorStats(
            browse_count=browse_count,
            like_count=like_count,
            comment_count=comment_count,
            follow_count=follow_count,
            friend_request_count=friend_request_count,
            chat_count=chat_count,
            # 内部使用 friend_count 判断 Level 6，但返回时用 chat_count
            _friend_count=friend_count,
        )

    async def _count_user_likes(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> int:
        """统计用户的共鸣/点赞次数。"""
        stmt = select(func.count(PostLike.id)).where(
            PostLike.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_user_comments(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> int:
        """统计用户的评论次数。"""
        stmt = select(func.count(PostComment.id)).where(
            PostComment.user_id == user_id,
            PostComment.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_user_follows(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> int:
        """统计用户的悄悄关注人数。"""
        stmt = select(func.count(PostFollow.id)).where(
            PostFollow.follower_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_friend_requests(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> int:
        """统计用户发送的好友申请次数。"""
        from app.models.chat import FriendRequest

        stmt = select(func.count(FriendRequest.id)).where(
            FriendRequest.sender_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_friends(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> int:
        """统计用户的好友数量。"""
        from sqlalchemy import or_

        stmt = select(func.count(Friendship.id)).where(
            or_(
                Friendship.user_id_1 == user_id,
                Friendship.user_id_2 == user_id,
            ),
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _count_conversations(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> int:
        """统计用户参与私聊的会话数（有消息记录的）。"""
        from sqlalchemy import or_

        # 查询有消息记录的会话数
        stmt = select(func.count(Conversation.id)).where(
            or_(
                Conversation.user_id_1 == user_id,
                Conversation.user_id_2 == user_id,
            ),
            Conversation.last_message_at.isnot(None),  # 有消息记录
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    # =========================================================================
    # 级别计算
    # =========================================================================

    def _calculate_level_progress(
        self,
        stats: BehaviorStats,
    ) -> LevelProgress:
        """根据行为统计数据计算当前级别和进度。

        级别判断逻辑：
        - Level 1: 默认（所有用户）
        - Level 2: 浏览 >= 3 次
        - Level 3: 点赞 >= 3 次
        - Level 4: 评论 >= 2 次
        - Level 5: 关注 >= 1 人
        - Level 6: 好友数 >= 1 且有私聊记录

        Args:
            stats: 行为统计数据

        Returns:
            LevelProgress 实例
        """
        # 获取内部存储的好友数量
        friend_count = getattr(stats, "_friend_count", 0)

        # 判断当前级别
        current_level = 1

        # Level 6: 有好友且有私聊记录
        if friend_count >= 1 and stats.chat_count >= 1:
            current_level = 6
        # Level 5: 关注1人以上 或 有好友
        elif stats.follow_count >= 1 or friend_count >= 1:
            current_level = 5
        # Level 4: 评论2次以上
        elif stats.comment_count >= 2:
            current_level = 4
        # Level 3: 共鸣3次以上
        elif stats.like_count >= 3:
            current_level = 3
        # Level 2: 浏览3次以上
        elif stats.browse_count >= 3:
            current_level = 2

        # 计算进度描述
        progress_description, next_action = self._calculate_progress_description(
            current_level, stats, friend_count
        )

        return LevelProgress(
            current_level=current_level,
            level_name=LEVEL_NAMES.get(current_level, "未知"),
            description=LEVEL_DESCRIPTIONS.get(current_level, ""),
            progress_description=progress_description,
            next_action=next_action,
        )

    def _calculate_progress_description(
        self,
        current_level: int,
        stats: BehaviorStats,
        friend_count: int,
    ) -> tuple[str, str | None]:
        """计算进度描述和下一步行动建议。

        Args:
            current_level: 当前级别
            stats: 行为统计
            friend_count: 好友数量

        Returns:
            (进度描述, 下一步行动建议)
        """
        # 根据当前级别计算下一步需要什么
        if current_level == 1:
            # 需要浏览3次升级
            remaining = 3 - stats.browse_count
            if remaining <= 0:
                remaining = 1  # 兜底
            return (
                f"Level 1，还需浏览{remaining}次可升级到Level 2",
                "去动态广场看看吧，发现有趣的内容"
            )

        elif current_level == 2:
            # 需要共鸣3次升级
            remaining = 3 - stats.like_count
            if remaining <= 0:
                remaining = 1
            return (
                f"Level 2，还需共鸣{remaining}次可升级到Level 3",
                "为喜欢的动态点个共鸣，表达你的认同"
            )

        elif current_level == 3:
            # 需要评论2次升级
            remaining = 2 - stats.comment_count
            if remaining <= 0:
                remaining = 1
            return (
                f"Level 3，还需评论{remaining}次可升级到Level 4",
                "留下你的评论，与他人展开对话"
            )

        elif current_level == 4:
            # 需要关注1人升级
            remaining = 1 - stats.follow_count
            if remaining <= 0:
                remaining = 1
            return (
                f"Level 4，还需关注{remaining}人可升级到Level 5",
                "悄悄关注感兴趣的发布者，建立连接"
            )

        elif current_level == 5:
            # Level 5：发送好友申请后成为好友可升级
            if friend_count >= 1:
                return (
                    "Level 5，已有好友，可开始私聊升级到Level 6",
                    "发送消息给好友，开始深度交流"
                )
            return (
                "Level 5，发送好友申请建立连接",
                "发送好友申请，建立双向连接"
            )

        else:  # current_level == 6
            return (
                "Level 6，深度社交达人",
                None  # 已达最高级别
            )

    def _calculate_unlock_status(
        self,
        stats: BehaviorStats,
    ) -> LevelUnlockStatus:
        """计算各级别解锁状态。

        Args:
            stats: 行为统计

        Returns:
            LevelUnlockStatus 实例
        """
        friend_count = getattr(stats, "_friend_count", 0)

        return LevelUnlockStatus(
            level_1=True,  # 默认解锁
            level_2=stats.browse_count >= 3,
            level_3=stats.like_count >= 3,
            level_4=stats.comment_count >= 2,
            level_5=stats.follow_count >= 1 or friend_count >= 1,
            level_6=friend_count >= 1 and stats.chat_count >= 1,
        )


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_social_level_service() -> SocialLevelService:
    """创建社交暴露级别服务实例。

    Returns:
        SocialLevelService 实例
    """
    return SocialLevelService()
