"""树洞与 AI 朋友联动关怀服务。

基于 modules_design.md 4.5 实现：
- 用户发布树洞吐槽后，AI 主动发起关怀对话
- 基于树洞内容生成个性化关怀开场白
- 危机内容触发特殊关怀流程
- 24小时无人回应时 AI 主动关怀

核心设计原则：
1. AI 永远不引用日记内容（日记绝对私密）
2. 只引用用户主动发布在树洞的内容
3. 用户可删除 AI 的引用
4. 危机内容优先处理
"""

from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIConversation, AIMessage
from app.models.treehole import TreeholePost, TreeholeComment
from app.models.user import User
from app.services.ai_chat import MockAIChat, GLMChatService, create_ai_chat_service
from app.services.crisis_detection import CrisisDetector, CrisisLevel, get_crisis_detector
from app.services.crypto import decrypt_data

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

REDIS_KEY_TREEHOLE_CARE_SENT = "treehole:care:{user_id}:{post_id}"
REDIS_KEY_TREEHOLE_NO_RESPONSE = "treehole:no_response:{post_id}"
REDIS_KEY_TREEHOLE_CARE_TODAY = "treehole:care:today:{user_id}"


# ---------------------------------------------------------------------------
# 关怀文案 Prompt 模板
# ---------------------------------------------------------------------------

TREEHOLE_CARE_PROMPT_TEMPLATE = """你是一个温暖的 AI 陪伴助手，用户刚在树洞发布了吐槽，你想主动发起关怀对话。

## 用户信息
- 昵称：{nickname}

## 树洞内容预览
{post_preview}

## 输出要求
1. 开场白控制在 40 字以内
2. 语气温和、不评判、不说教
3. 不要完全重复树洞内容，可以提及或回应
4. 用自然的过渡，比如"刚在树洞看到你说的..."
5. 不要使用感叹号，避免过度热情
6. 不要使用"你应该""你需要"等命令式语言
7. 输出纯文本，不要包含任何 Markdown 格式

## 示例
- 刚在树洞看到你说的，如果你愿意，可以跟我聊聊。
- 看到你发在树洞的内容，感觉你可能不太好。
- 树洞里看到你的吐槽了，想问问你现在怎么样。

请生成一条关怀开场白："""


CRISIS_CARE_PROMPT_TEMPLATE = """你是一个温暖的 AI 陪伴助手，用户发表了包含危机信号的内容，你需要主动关怀。

## 用户信息
- 昵称：{nickname}

## 危机级别
{crisis_level_desc}

## 树洞内容预览
{post_preview}

## 输出要求
1. 开场白控制在 50 字以内
2. 语气温柔、坚定、不说教
3. 表达关心，但不吓唬用户
4. 如果是高危情况，提醒专业求助热线
5. 避免使用"你应该"等命令式语言
6. 输出纯文本，不要包含任何 Markdown 格式

## 热线信息
- 全国24小时心理援助热线：400-161-9995
- 北京心理危机研究与干预中心：010-82951332

## 示例
- 我看到你说的，很担心你。如果你愿意，可以跟我说说。
- 感觉你今天不太好，我在这里。如果你需要专业帮助，可以拨打400-161-9995。

请生成一条关怀开场白："""


NO_RESPONSE_CARE_TEMPLATE = """你是一个温暖的 AI 陪伴助手，用户的树洞吐槽24小时没有人回应，你想安慰TA。

## 用户信息
- 昵称：{nickname}

## 树洞内容预览
{post_preview}

## 输出要求
1. 开场白控制在 40 字以内
2. 语气温暖、理解、不评判
3. 告诉用户：说出来本身就是有意义的
4. 不要追问原因，只是温柔地陪伴
5. 输出纯文本，不要包含任何 Markdown 格式

## 示例
- 就算没有人回，你说出来的那一刻，已经有人在听了。
- 树洞里的话我看到啦，说不出来也没关系，你做了就好。

请生成一条关怀开场白："""


# ---------------------------------------------------------------------------
# 默认开场白（降级使用）
# ---------------------------------------------------------------------------

DEFAULT_TREEHOLE_OPENERS = [
    "刚在树洞看到你说的，如果你愿意，可以跟我聊聊。",
    "看到你发在树洞的内容，感觉你可能不太好。",
    "树洞里看到你的吐槽了，想问问你现在怎么样。",
]

DEFAULT_CRISIS_OPENERS = {
    CrisisLevel.LOW: [
        "我看到你说的，如果你愿意，可以跟我说说。",
        "感觉你今天不太好，我在这里。",
    ],
    CrisisLevel.MEDIUM: [
        "看到你的内容，我很担心你。如果你需要，可以拨打400-161-9995。",
        "我在意你说的。如果你现在很难受，试试和专业的人聊聊？400-161-9995。",
    ],
    CrisisLevel.HIGH: [
        "你说的让我很担心。请立刻拨打400-161-9995，他们在等你。",
        "我很在意你。请拨打心理援助热线400-161-9995，我就在这里陪你。",
    ],
}

DEFAULT_NO_RESPONSE_OPENERS = [
    "就算没有人回，你说出来的那一刻，已经有人在听了。",
    "树洞里的话我看到啦，说不出来也没关系，你做了就好。",
    "没有回应不代表没人懂你，我看到你了。",
]


# ---------------------------------------------------------------------------
# AI 对话服务接口
# ---------------------------------------------------------------------------

class AIConversationServiceProtocol(Protocol):
    """AI 对话服务接口协议。"""

    async def chat(
        self,
        user_id: str,
        message: str,
        personality: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """发送对话消息。"""
        ...

    async def get_greeting(
        self,
        user_id: str,
        personality: str | None = None,
    ) -> dict[str, Any]:
        """获取开场白。"""
        ...


# ---------------------------------------------------------------------------
# 树洞联动关怀服务
# ---------------------------------------------------------------------------

class TreeholeCareService:
    """树洞与 AI 朋友联动关怀服务。

    实现树洞发布后 AI 主动关怀、危机内容特殊处理、
    24小时无人回应安慰等功能。

    使用示例：
        service = TreeholeCareService(db, redis, ai_service)

        # 用户发布树洞后触发
        await service.on_post_created(user_id, post_id, db)

        # 24小时无人回应时触发
        await service.check_no_response_posts(db)

        # 用户获得共鸣后通知
        await service.on_resonance_received(user_id, post_id, db)
    """

    def __init__(
        self,
        settings: Any,
        redis: Any,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
        crisis_detector: CrisisDetector | None = None,
    ) -> None:
        """初始化树洞联动关怀服务。

        Args:
            settings: 应用配置
            redis: Redis 客户端
            ai_provider: AI 服务提供者（mock/glm_free/glm）
            zhipu_api_key: 智谱 API Key
            crisis_detector: 危机检测器（可选）
        """
        self._settings = settings
        self._redis = redis
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key
        self._crisis_detector = crisis_detector or get_crisis_detector()

        # AI 服务实例缓存
        self._ai_service: MockAIChat | GLMChatService | None = None

        logger.info(
            "[TreeholeCareService] 初始化完成，AI Provider: %s",
            ai_provider
        )

    def _get_ai_service(self) -> MockAIChat | GLMChatService:
        """获取 AI 服务实例（使用 GLM-4-Flash 降低成本）。"""
        if self._ai_service is None:
            self._ai_service = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                model="glm-4-flash",
                personality="xiaowen",
            )
        return self._ai_service

    # =========================================================================
    # 频率控制
    # =========================================================================

    async def _has_sent_care_for_post(
        self,
        user_id: str,
        post_id: str,
    ) -> bool:
        """检查是否已为该帖子发送过关怀。

        Args:
            user_id: 用户 ID
            post_id: 帖子 ID

        Returns:
            是否已发送
        """
        key = REDIS_KEY_TREEHOLE_CARE_SENT.format(user_id=user_id, post_id=post_id)
        return bool(await self._redis.exists(key))

    async def _mark_care_sent_for_post(
        self,
        user_id: str,
        post_id: str,
    ) -> None:
        """标记已为该帖子发送关怀。

        Args:
            user_id: 用户 ID
            post_id: 帖子 ID
        """
        key = REDIS_KEY_TREEHOLE_CARE_SENT.format(user_id=user_id, post_id=post_id)
        # 缓存 7 天
        await self._redis.setex(key, 86400 * 7, datetime.now(timezone.utc).isoformat())

    async def _has_sent_care_today(self, user_id: str) -> bool:
        """检查今天是否已发送过树洞关怀。

        Args:
            user_id: 用户 ID

        Returns:
            是否已发送
        """
        key = REDIS_KEY_TREEHOLE_CARE_TODAY.format(user_id=user_id)
        return bool(await self._redis.exists(key))

    async def _mark_care_sent_today(self, user_id: str) -> None:
        """标记今天已发送树洞关怀。

        Args:
            user_id: 用户 ID
        """
        key = REDIS_KEY_TREEHOLE_CARE_TODAY.format(user_id=user_id)
        await self._redis.setex(key, 86400, "1")

    # =========================================================================
    # 文案生成
    # =========================================================================

    async def _generate_care_opener(
        self,
        user: User,
        post_content: str,
        crisis_level: CrisisLevel | None = None,
    ) -> str:
        """生成关怀开场白。

        Args:
            user: 用户对象
            post_content: 帖子内容
            crisis_level: 危机级别（可选）

        Returns:
            关怀开场白
        """
        post_preview = post_content[:100] if post_content else ""

        try:
            ai_service = self._get_ai_service()

            if crisis_level:
                # 危机模板
                crisis_level_desc = {
                    CrisisLevel.LOW: "情绪低落",
                    CrisisLevel.MEDIUM: "有自伤意念",
                    CrisisLevel.HIGH: "紧急情况",
                }.get(crisis_level, "需要关注")

                prompt = CRISIS_CARE_PROMPT_TEMPLATE.format(
                    nickname=user.nickname or "用户",
                    crisis_level_desc=crisis_level_desc,
                    post_preview=post_preview,
                )
            else:
                # 普通模板
                prompt = TREEHOLE_CARE_PROMPT_TEMPLATE.format(
                    nickname=user.nickname or "用户",
                    post_preview=post_preview,
                )

            response = await ai_service.chat(prompt, context={})
            message = response.strip().strip('"').strip("'")

            # 限制长度
            max_len = 60 if crisis_level else 50
            if len(message) > max_len:
                message = message[:max_len - 3] + "..."

            return message

        except Exception as e:
            logger.error("[TreeholeCareService] AI 生成开场白失败: %s", str(e))
            return self._get_fallback_opener(crisis_level)

    def _get_fallback_opener(
        self,
        crisis_level: CrisisLevel | None = None,
    ) -> str:
        """获取降级开场白。

        Args:
            crisis_level: 危机级别（可选）

        Returns:
            默认开场白
        """
        if crisis_level:
            openers = DEFAULT_CRISIS_OPENERS.get(
                crisis_level,
                DEFAULT_CRISIS_OPENERS[CrisisLevel.LOW]
            )
        else:
            openers = DEFAULT_TREEHOLE_OPENERS
        return random.choice(openers)

    async def _generate_no_response_opener(
        self,
        user: User,
        post_content: str,
    ) -> str:
        """生成 24 小时无回应安慰开场白。

        Args:
            user: 用户对象
            post_content: 帖子内容

        Returns:
            安慰开场白
        """
        post_preview = post_content[:80] if post_content else ""

        try:
            ai_service = self._get_ai_service()
            prompt = NO_RESPONSE_CARE_TEMPLATE.format(
                nickname=user.nickname or "用户",
                post_preview=post_preview,
            )

            response = await ai_service.chat(prompt, context={})
            message = response.strip().strip('"').strip("'")

            if len(message) > 50:
                message = message[:47] + "..."

            return message

        except Exception as e:
            logger.error(
                "[TreeholeCareService] AI 生成无回应安慰开场白失败: %s",
                str(e)
            )
            return random.choice(DEFAULT_NO_RESPONSE_OPENERS)

    # =========================================================================
    # AI 对话发起
    # =========================================================================

    async def _create_ai_conversation_with_message(
        self,
        user_id: str,
        message: str,
        db: AsyncSession,
        personality: str = "xiaowen",
        related_post_id: str | None = None,
    ) -> AIConversation:
        """创建 AI 对话并发送首条消息。

        Args:
            user_id: 用户 ID
            message: 首条消息内容
            db: 数据库会话
            personality: AI 人设
            related_post_id: 关联的树洞帖子 ID（可选）

        Returns:
            创建的对话对象
        """
        # 创建新对话
        conversation = AIConversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ai_persona=personality,
            is_active=True,
            last_message_at=datetime.now(timezone.utc),
        )
        db.add(conversation)
        await db.flush()

        # 创建 AI 消息
        ai_message = AIMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=message,
        )
        db.add(ai_message)

        logger.info(
            "[TreeholeCareService] 创建 AI 对话，用户: %s，对话: %s",
            user_id, conversation.id
        )

        return conversation

    async def _send_ai_message_to_existing_conversation(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        db: AsyncSession,
    ) -> bool:
        """向现有对话发送 AI 消息。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            message: 消息内容
            db: 数据库会话

        Returns:
            是否成功
        """
        try:
            # 验证对话存在
            conv_stmt = select(AIConversation).where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
                AIConversation.is_active.is_(True),
            )
            conv_result = await db.execute(conv_stmt)
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                logger.warning(
                    "[TreeholeCareService] 对话不存在或不属于用户，对话: %s，用户: %s",
                    conversation_id, user_id
                )
                return False

            # 发送消息
            ai_message = AIMessage(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="assistant",
                content=message,
            )
            db.add(ai_message)

            # 更新对话最后消息时间
            conversation.last_message_at = datetime.now(timezone.utc)

            return True

        except Exception as e:
            logger.error(
                "[TreeholeCareService] 发送 AI 消息失败，对话: %s，错误: %s",
                conversation_id, str(e)
            )
            return False

    # =========================================================================
    # 核心触发方法
    # =========================================================================

    async def on_post_created(
        self,
        user_id: str,
        post_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """用户发布树洞后触发 AI 主动关怀。

        检测内容是否包含危机信号，根据情况生成相应关怀开场白。

        Args:
            user_id: 用户 ID
            post_id: 帖子 ID
            db: 数据库会话

        Returns:
            触发结果
        """
        result = {
            "success": False,
            "skipped": False,
            "reason": None,
            "crisis_detected": False,
            "conversation_id": None,
        }

        try:
            # 获取帖子内容（解密加密的用户ID验证归属）
            post_stmt = select(TreeholePost).where(
                TreeholePost.id == post_id,
                TreeholePost.deleted_at.is_(None),
            )
            post_result = await db.execute(post_stmt)
            post = post_result.scalar_one_or_none()

            if not post:
                result["reason"] = "帖子不存在"
                return result

            # 获取用户信息
            user_stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                result["reason"] = "用户不存在"
                return result

            # 检查是否已发送过关怀
            if await self._has_sent_care_for_post(user_id, post_id):
                result["skipped"] = True
                result["reason"] = "已发送过关怀"
                return result

            # 检查今天是否已发送过树洞关怀（频率控制）
            if await self._has_sent_care_today(user_id):
                result["skipped"] = True
                result["reason"] = "今日已发送树洞关怀"
                return result

            # 检测危机内容
            crisis_result = self._crisis_detector.detect(post.content)
            crisis_level = None
            if crisis_result:
                crisis_level = crisis_result.get("level")
                result["crisis_detected"] = True
                logger.warning(
                    "[TreeholeCareService] 检测到危机内容，用户: %s，帖子: %s，级别: %s",
                    user_id, post_id, crisis_level.value if crisis_level else "未知"
                )

            # 生成关怀开场白
            care_message = await self._generate_care_opener(
                user, post.content, crisis_level
            )

            # 创建 AI 对话
            conversation = await self._create_ai_conversation_with_message(
                user_id=user_id,
                message=care_message,
                db=db,
                personality="xiaowen",  # 树洞关怀默认使用温柔的小温
                related_post_id=post_id,
            )

            # 标记已发送
            await self._mark_care_sent_for_post(user_id, post_id)
            await self._mark_care_sent_today(user_id)

            result["success"] = True
            result["conversation_id"] = conversation.id

            logger.info(
                "[TreeholeCareService] 树洞关怀触发成功，用户: %s，帖子: %s，危机: %s",
                user_id, post_id, crisis_level.value if crisis_level else "无"
            )

        except Exception as e:
            result["reason"] = str(e)
            logger.error(
                "[TreeholeCareService] 树洞关怀触发失败，用户: %s，帖子: %s，错误: %s",
                user_id, post_id, str(e)
            )

        return result

    async def on_resonance_received(
        self,
        user_id: str,
        post_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """用户获得共鸣后，AI 在下次对话时提及。

        这个方法不立即发送消息，而是标记用户获得了共鸣，
        在下次 AI 对话时自然提及。

        Args:
            user_id: 用户 ID
            post_id: 帖子 ID
            db: 数据库会话

        Returns:
            处理结果
        """
        result = {
            "success": True,
            "message": "共鸣已记录，下次对话时会提及",
        }

        # 存储共鸣事件，供下次对话时注入上下文
        key = f"treehole:resonance:{user_id}:{post_id}"
        await self._redis.setex(
            key,
            86400 * 3,  # 3 天有效
            json.dumps({
                "post_id": post_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        )

        logger.info(
            "[TreeholeCareService] 共鸣事件已记录，用户: %s，帖子: %s",
            user_id, post_id
        )

        return result

    async def check_no_response_posts(
        self,
        db: AsyncSession,
        hours: int = 24,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """检查 24 小时无人回应的帖子，发送安慰关怀。

        可由定时任务调用。

        Args:
            db: 数据库会话
            hours: 无回应的小时数阈值
            batch_size: 批量处理数量

        Returns:
            处理统计
        """
        stats = {
            "checked": 0,
            "sent": 0,
            "skipped": 0,
            "failed": 0,
        }

        try:
            # 查询超过指定小时且无共鸣无评论的帖子
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            stmt = (
                select(TreeholePost)
                .where(
                    TreeholePost.deleted_at.is_(None),
                    TreeholePost.status == "active",
                    TreeholePost.created_at < cutoff_time,
                    TreeholePost.resonance_count == 0,
                    TreeholePost.comment_count == 0,
                )
                .limit(batch_size)
            )

            result = await db.execute(stmt)
            posts = result.scalars().all()

            stats["checked"] = len(posts)

            for post in posts:
                try:
                    # 检查是否已发送过无回应安慰
                    no_response_key = REDIS_KEY_TREEHOLE_NO_RESPONSE.format(post_id=post.id)
                    if await self._redis.exists(no_response_key):
                        stats["skipped"] += 1
                        continue

                    # 解密用户ID
                    try:
                        user_id = decrypt_data(post.encrypted_user_id)
                    except Exception:
                        stats["skipped"] += 1
                        continue

                    # 获取用户
                    user_stmt = select(User).where(
                        User.id == user_id,
                        User.deleted_at.is_(None),
                    )
                    user_result = await db.execute(user_stmt)
                    user = user_result.scalar_one_or_none()

                    if not user:
                        stats["skipped"] += 1
                        continue

                    # 生成安慰开场白
                    care_message = await self._generate_no_response_opener(
                        user, post.content
                    )

                    # 创建 AI 对话
                    await self._create_ai_conversation_with_message(
                        user_id=user_id,
                        message=care_message,
                        db=db,
                    )

                    # 标记已发送
                    await self._redis.setex(no_response_key, 86400 * 30, "1")  # 30 天内不重复

                    stats["sent"] += 1

                    logger.info(
                        "[TreeholeCareService] 无回应安慰发送成功，用户: %s，帖子: %s",
                        user_id, post.id
                    )

                except Exception as e:
                    stats["failed"] += 1
                    logger.error(
                        "[TreeholeCareService] 无回应安慰发送失败，帖子: %s，错误: %s",
                        post.id, str(e)
                    )

            # 提交事务
            await db.commit()

        except Exception as e:
            logger.error(
                "[TreeholeCareService] 无回应检查任务失败: %s",
                str(e)
            )
            # 发生异常时回滚事务
            try:
                await db.rollback()
            except Exception as rollback_error:
                logger.error(
                    "[TreeholeCareService] 事务回滚失败: %s",
                    str(rollback_error)
                )

        logger.info(
            "[TreeholeCareService] 无回应检查完成，检查: %d，发送: %d，跳过: %d，失败: %d",
            stats["checked"],
            stats["sent"],
            stats["skipped"],
            stats["failed"],
        )

        return stats

    async def get_care_context_for_conversation(
        self,
        user_id: str,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """获取用于 AI 对话上下文注入的树洞关怀信息。

        在 AI 对话时调用，获取需要自然提及的树洞相关内容。

        Args:
            user_id: 用户 ID
            db: 数据库会话（可选）

        Returns:
            上下文列表
        """
        context_items = []
        keys_to_delete = []  # 收集待删除的 key，在处理完成后统一删除

        try:
            # 使用 SCAN 代替 KEYS 避免阻塞 Redis
            resonance_pattern = f"treehole:resonance:{user_id}:*"
            cursor = 0

            # 兼容不同 Redis 客户端
            if hasattr(self._redis, 'scan'):
                while len(context_items) < 3:
                    cursor, keys = await self._redis.scan(
                        cursor=cursor,
                        match=resonance_pattern,
                        count=10
                    )
                    for key in keys:
                        if len(context_items) >= 3:
                            break
                        data = await self._redis.get(key)
                        if data:
                            try:
                                # 处理 bytes 类型
                                if isinstance(data, bytes):
                                    data = data.decode("utf-8")
                                event = json.loads(data)
                                context_items.append({
                                    "type": "resonance_gained",
                                    "post_id": event.get("post_id"),
                                    "message": "有人懂你诶",
                                })
                                keys_to_delete.append(key)
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                pass
                    # 扫描完成
                    if cursor == 0:
                        break
            elif hasattr(self._redis, 'keys'):
                # 降级方案：使用 keys（仅用于兼容旧客户端）
                resonance_keys = await self._redis.keys(resonance_pattern)
                for key in resonance_keys[:3]:  # 最多 3 个
                    data = await self._redis.get(key)
                    if data:
                        try:
                            # 处理 bytes 类型
                            if isinstance(data, bytes):
                                data = data.decode("utf-8")
                            event = json.loads(data)
                            context_items.append({
                                "type": "resonance_gained",
                                "post_id": event.get("post_id"),
                                "message": "有人懂你诶",
                            })
                            keys_to_delete.append(key)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass

            # 成功获取上下文后，标记删除（设置短 TTL 让其自然过期）
            for key in keys_to_delete:
                # 将 TTL 设置为 5 分钟，而不是立即删除
                # 这样如果对话后续失败，上下文可恢复
                await self._redis.expire(key, 300)

        except Exception as e:
            logger.warning(
                "[TreeholeCareService] 获取关怀上下文失败: %s",
                str(e)
            )

        return context_items


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_treehole_care_service(
    settings: Any,
    redis: Any,
    ai_provider: str = "mock",
    zhipu_api_key: str = "",
) -> TreeholeCareService:
    """创建树洞联动关怀服务实例。

    Args:
        settings: 应用配置
        redis: Redis 客户端
        ai_provider: AI 服务提供者
        zhipu_api_key: 智谱 API Key

    Returns:
        TreeholeCareService 实例
    """
    return TreeholeCareService(
        settings=settings,
        redis=redis,
        ai_provider=ai_provider,
        zhipu_api_key=zhipu_api_key,
    )
