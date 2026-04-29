"""AI画像标签生成服务。

基于用户行为数据生成画像标签，包括：
- 情绪模式（emotion_pattern）：用户常见的情绪状态
- 社交偏好（social_preference）：用户社交互动模式
- 兴趣领域（interest）：用户感兴趣的话题/领域

画像标签异步生成，结果缓存至 Redis（24小时有效期）。

数据来源：
1. 用户兴趣标签（user_tags表）
2. 用户动态内容分析（posts表）
3. AI对话历史分析（ai_conversations表）
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.user import User, UserTag

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# Redis 缓存配置
PROFILE_CACHE_PREFIX = "ai_profile:"
PROFILE_CACHE_TTL = 86400  # 24小时

# 画像标签类型
PROFILE_TAG_TYPES = ["emotion_pattern", "social_preference", "interest"]

# 默认画像标签（当无法生成时的兜底）
DEFAULT_PROFILE_TAGS = [
    {"tag_type": "emotion_pattern", "tag_name": "情绪模式", "tag_value": "平和稳定", "is_visible": True},
    {"tag_type": "social_preference", "tag_name": "社交偏好", "tag_value": "温和内敛", "is_visible": True},
    {"tag_type": "interest", "tag_name": "兴趣领域", "tag_value": "生活日常", "is_visible": True},
]


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class ProfileTag:
    """画像标签数据结构."""

    tag_type: str
    tag_name: str
    tag_value: str
    is_visible: bool = True


# ---------------------------------------------------------------------------
# AI画像标签服务
# ---------------------------------------------------------------------------

class AIProfileService:
    """AI画像标签生成服务。

    基于用户行为数据生成画像标签，支持：
    1. 从用户兴趣标签中提取
    2. 从用户动态内容中分析
    3. 异步生成并缓存结果

    使用示例：
        service = AIProfileService(redis)
        tags = await service.get_profile_tags(user_id, db)
    """

    def __init__(self, redis: Any) -> None:
        """初始化AI画像标签服务。

        Args:
            redis: Redis 客户端（用于缓存）
        """
        self._redis = redis
        logger.info("[AIProfileService] 初始化完成")

    # =========================================================================
    # 主要接口
    # =========================================================================

    async def get_profile_tags(
        self,
        user_id: str,
        db: AsyncSession,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """获取用户AI画像标签。

        优先从缓存读取，缓存未命中时异步生成。

        Args:
            user_id: 用户ID
            db: 数据库会话
            use_cache: 是否使用缓存（默认True）

        Returns:
            画像标签响应字典，包含：
            - tags: 画像标签列表
            - generated_at: 生成时间
            - message: 提示信息
        """
        # 尝试从缓存读取
        if use_cache:
            cached = await self._get_from_cache(user_id)
            if cached:
                logger.debug("[AIProfileService] 命中缓存: user_id=%s", user_id)
                return cached

        # 缓存未命中，生成新标签
        tags = await self._generate_profile_tags(user_id, db)

        # 缓存结果
        result = {
            "tags": [self._tag_to_dict(tag) for tag in tags],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "message": "画像标签已生成",
        }

        await self._save_to_cache(user_id, result)

        logger.info("[AIProfileService] 生成画像标签: user_id=%s, tags_count=%d", user_id, len(tags))

        return result

    async def invalidate_cache(self, user_id: str) -> None:
        """清除用户画像标签缓存。

        在用户行为发生重大变化后调用（如发布新动态、修改兴趣标签等）。

        Args:
            user_id: 用户ID
        """
        key = f"{PROFILE_CACHE_PREFIX}{user_id}"
        try:
            await self._redis.delete(key)
            logger.debug("[AIProfileService] 清除缓存: user_id=%s", user_id)
        except Exception as e:
            logger.warning("[AIProfileService] 清除缓存失败: %s", str(e))

    # =========================================================================
    # 标签生成逻辑
    # =========================================================================

    async def _generate_profile_tags(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> list[ProfileTag]:
        """生成用户画像标签。

        标签来源：
        1. 用户兴趣标签（user_tags表）-> interest
        2. 用户动态内容分析 -> emotion_pattern, interest
        3. 用户活跃度分析 -> social_preference

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            画像标签列表
        """
        tags: list[ProfileTag] = []

        # 1. 从用户兴趣标签提取
        interest_tags = await self._extract_interest_tags(user_id, db)
        tags.extend(interest_tags)

        # 2. 从动态内容分析情绪模式
        emotion_tag = await self._analyze_emotion_pattern(user_id, db)
        if emotion_tag:
            tags.append(emotion_tag)

        # 3. 分析社交偏好
        social_tag = await self._analyze_social_preference(user_id, db)
        if social_tag:
            tags.append(social_tag)

        # 如果无法生成任何标签，返回默认标签
        if not tags:
            tags = [self._dict_to_tag(d) for d in DEFAULT_PROFILE_TAGS]

        return tags

    async def _extract_interest_tags(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> list[ProfileTag]:
        """从用户兴趣标签中提取画像标签。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            兴趣类画像标签列表
        """
        # 查询用户的兴趣标签
        stmt = select(UserTag).where(
            UserTag.user_id == user_id,
            UserTag.tag_key == "interest",
        ).limit(5)  # 最多取5个

        result = await db.execute(stmt)
        user_tags = result.scalars().all()

        tags: list[ProfileTag] = []
        for tag in user_tags:
            tags.append(ProfileTag(
                tag_type="interest",
                tag_name="兴趣领域",
                tag_value=tag.tag_value,
                is_visible=True,
            ))

        return tags

    async def _analyze_emotion_pattern(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> ProfileTag | None:
        """从用户动态内容分析情绪模式。

        简化版实现：基于动态内容关键词匹配。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            情绪模式标签，或None
        """
        # 获取用户最近的动态（最多10条）
        stmt = select(Post.content).where(
            Post.user_id == user_id,
            Post.is_active == True,  # noqa: E712
        ).order_by(Post.created_at.desc()).limit(10)

        result = await db.execute(stmt)
        contents = [row[0] for row in result.fetchall()]

        if not contents:
            return None

        # 简单关键词匹配分析情绪
        # 实际生产环境应该使用 NLP 模型
        emotion_keywords = {
            "积极向上": ["开心", "快乐", "幸福", "美好", "感谢", "感恩", "喜欢", "爱", "棒", "好"],
            "平和稳定": ["平静", "安宁", "舒适", "放松", "惬意", "简单", "日常"],
            "感性细腻": ["感动", "温暖", "心酸", "思念", "怀念", "回忆", "感慨"],
            "积极进取": ["努力", "奋斗", "加油", "坚持", "目标", "梦想", "追求"],
        }

        # 统计各情绪关键词出现次数
        emotion_counts: dict[str, int] = {k: 0 for k in emotion_keywords}
        all_text = " ".join(contents)

        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                emotion_counts[emotion] += all_text.count(keyword)

        # 找出最突出的情绪
        max_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        if max_emotion[1] > 0:
            return ProfileTag(
                tag_type="emotion_pattern",
                tag_name="情绪模式",
                tag_value=max_emotion[0],
                is_visible=True,
            )

        return ProfileTag(
            tag_type="emotion_pattern",
            tag_name="情绪模式",
            tag_value="平和稳定",
            is_visible=True,
        )

    async def _analyze_social_preference(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> ProfileTag | None:
        """分析用户社交偏好。

        基于用户动态发布频率和互动情况判断。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            社交偏好标签，或None
        """
        # 统计用户动态数量
        post_count_stmt = select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.is_active == True,  # noqa: E712
        )
        post_result = await db.execute(post_count_stmt)
        post_count = post_result.scalar() or 0

        # 统计用户互动情况（点赞+评论）
        from app.models.post import PostLike, PostComment

        like_count_stmt = select(func.count(PostLike.id)).where(
            PostLike.user_id == user_id,
        )
        like_result = await db.execute(like_count_stmt)
        like_count = like_result.scalar() or 0

        comment_count_stmt = select(func.count(PostComment.id)).where(
            PostComment.user_id == user_id,
            PostComment.is_active == True,  # noqa: E712
        )
        comment_result = await db.execute(comment_count_stmt)
        comment_count = comment_result.scalar() or 0

        interaction_count = like_count + comment_count

        # 判断社交偏好
        if post_count == 0 and interaction_count == 0:
            return ProfileTag(
                tag_type="social_preference",
                tag_name="社交偏好",
                tag_value="内敛观察",
                is_visible=True,
            )
        elif interaction_count > post_count * 2:
            return ProfileTag(
                tag_type="social_preference",
                tag_name="社交偏好",
                tag_value="互动活跃",
                is_visible=True,
            )
        elif post_count > interaction_count * 2:
            return ProfileTag(
                tag_type="social_preference",
                tag_name="社交偏好",
                tag_value="表达型",
                is_visible=True,
            )
        else:
            return ProfileTag(
                tag_type="social_preference",
                tag_name="社交偏好",
                tag_value="温和内敛",
                is_visible=True,
            )

    # =========================================================================
    # 缓存操作
    # =========================================================================

    async def _get_from_cache(self, user_id: str) -> dict[str, Any] | None:
        """从缓存获取画像标签。

        Args:
            user_id: 用户ID

        Returns:
            缓存的画像标签响应，或None
        """
        key = f"{PROFILE_CACHE_PREFIX}{user_id}"
        try:
            cached = await self._redis.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning("[AIProfileService] 读取缓存失败: %s", str(e))
            return None

    async def _save_to_cache(
        self,
        user_id: str,
        data: dict[str, Any],
    ) -> None:
        """保存画像标签到缓存。

        Args:
            user_id: 用户ID
            data: 画像标签数据
        """
        key = f"{PROFILE_CACHE_PREFIX}{user_id}"
        try:
            await self._redis.setex(
                key,
                PROFILE_CACHE_TTL,
                json.dumps(data, ensure_ascii=False),
            )
        except Exception as e:
            logger.warning("[AIProfileService] 保存缓存失败: %s", str(e))

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _tag_to_dict(self, tag: ProfileTag) -> dict[str, Any]:
        """将 ProfileTag 转换为字典。"""
        return {
            "tag_type": tag.tag_type,
            "tag_name": tag.tag_name,
            "tag_value": tag.tag_value,
            "is_visible": tag.is_visible,
        }

    def _dict_to_tag(self, data: dict[str, Any]) -> ProfileTag:
        """将字典转换为 ProfileTag。"""
        return ProfileTag(
            tag_type=data.get("tag_type", ""),
            tag_name=data.get("tag_name", ""),
            tag_value=data.get("tag_value", ""),
            is_visible=data.get("is_visible", True),
        )


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_ai_profile_service(redis: Any) -> AIProfileService:
    """创建AI画像标签服务实例。

    Args:
        redis: Redis 客户端

    Returns:
        AIProfileService 实例
    """
    return AIProfileService(redis=redis)
