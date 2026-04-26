"""AI 对话服务层。

管理对话上下文、消息持久化、配额检查等业务逻辑。
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai import AIConversation, AIMessage, AIMemory
from app.services.ai_chat import (
    MockAIChat,
    GLMChatService,
    create_ai_chat_service,
)
from app.services.ai_config import get_greeting, get_daily_count_key
from app.services.crisis_detection import CrisisDetector, CrisisLevel, get_crisis_detector
from app.services.memory.short_term import ShortTermMemory
from app.services.memory.mid_term import MidTermMemory
from app.services.memory.long_term import LongTermMemory
from app.core.errors import AppError
from app.enums.error_codes import ErrorCode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 默认对话上下文轮数（1轮 = 1次用户 + 1次AI）
DEFAULT_MAX_CONTEXT_ROUNDS = 5

# 默认性格
DEFAULT_PERSONALITY = "xiaowen"


# ---------------------------------------------------------------------------
# AI 对话服务
# ---------------------------------------------------------------------------

class AIConversationService:
    """AI 对话服务，管理对话上下文和持久化。

    提供以下功能：
    - 同步对话（chat）
    - 流式对话（chat_stream）
    - 获取对话列表（get_conversations）
    - 获取开场白（get_greeting）
    - 对话上下文管理
    - 危机关键词检测
    - 配额检查

    使用示例：
        service = AIConversationService(db, settings)
        result = await service.chat(user_id, "你好", "xiaowen", None)
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
        daily_limit: int = 10,
        daily_limit_vip: int = 100,
        crisis_detector: CrisisDetector | None = None,
        redis_client: Any = None,
    ) -> None:
        """初始化 AI 对话服务。

        Args:
            db: 数据库会话
            ai_provider: AI 服务提供者（mock/glm_free/glm）
            zhipu_api_key: 智谱 API Key
            daily_limit: 普通用户每日对话限制
            daily_limit_vip: VIP 用户每日对话限制
            crisis_detector: 危机检测器（可选，默认使用全局实例）
            redis_client: Redis 客户端（可选，用于配额计数和短期记忆）
        """
        self._db = db
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key
        self._daily_limit = daily_limit
        self._daily_limit_vip = daily_limit_vip
        self._crisis_detector = crisis_detector or get_crisis_detector()
        self._redis = redis_client

        # 初始化短期记忆服务
        self._short_term_memory = ShortTermMemory(redis_client) if redis_client else None

        # 初始化中期记忆服务
        self._mid_term_memory = MidTermMemory(
            db=db,
            ai_provider=ai_provider,
            zhipu_api_key=zhipu_api_key,
        )

        # 初始化长期记忆服务
        self._long_term_memory = LongTermMemory(
            db=db,
            ai_provider=ai_provider,
            zhipu_api_key=zhipu_api_key,
        )

        # AI 服务实例缓存（按性格区分）
        self._ai_services: dict[str, MockAIChat | GLMChatService] = {}

        logger.info(
            "[AIConversationService] 初始化完成，Provider: %s，短期记忆: %s，中期记忆: 已启用，长期记忆: 已启用",
            ai_provider,
            "已启用" if self._short_term_memory else "未启用"
        )

    def _handle_background_task_exception(self, task: asyncio.Task) -> None:
        """处理后台任务的异常。"""
        try:
            if task.cancelled():
                logger.debug("[AIConversationService] 后台任务被取消")
                return
            exc = task.exception()
            if exc:
                logger.error(
                    "[AIConversationService] 后台任务执行异常: %s",
                    str(exc),
                    exc_info=exc
                )
        except asyncio.CancelledError:
            logger.debug("[AIConversationService] 后台任务被取消")
        except Exception as e:
            logger.error(
                "[AIConversationService] 获取后台任务异常失败: %s",
                str(e)
            )

    def _create_background_task(self, coro) -> asyncio.Task:
        """创建后台任务并添加异常处理回调。"""
        task = asyncio.create_task(coro)
        task.add_done_callback(self._handle_background_task_exception)
        return task

    def _get_ai_service(
        self,
        personality: str,
    ) -> MockAIChat | GLMChatService:
        """获取指定性格的 AI 服务实例。

        Args:
            personality: 性格标识

        Returns:
            AI 服务实例
        """
        if personality not in self._ai_services:
            self._ai_services[personality] = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                personality=personality,
            )
        return self._ai_services[personality]

    async def _get_or_create_conversation(
        self,
        user_id: str,
        personality: str,
        conversation_id: str | None = None,
    ) -> AIConversation:
        """获取或创建对话。

        如果 conversation_id 存在，返回对应的对话；
        否则创建新对话。

        Args:
            user_id: 用户 ID
            personality: 性格标识
            conversation_id: 对话 ID（可选）

        Returns:
            AIConversation 对象

        Raises:
            AppError: 对话不存在或不属于当前用户
        """
        if conversation_id:
            # 查找现有对话
            stmt = (
                select(AIConversation)
                .where(
                    AIConversation.id == conversation_id,
                    AIConversation.user_id == user_id,
                    AIConversation.is_active == True,  # noqa: E712
                )
            )
            result = await self._db.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise AppError(
                    code=ErrorCode.AI_CONVERSATION_NOT_FOUND,
                    message="对话不存在或已结束",
                    status_code=404,
                )

            return conversation

        # 创建新对话
        conversation = AIConversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ai_persona=personality,
            is_active=True,
            last_message_at=datetime.now(timezone.utc),
        )
        self._db.add(conversation)
        await self._db.flush()

        logger.info(
            "[AIConversationService] 创建新对话，ID: %s，性格: %s",
            conversation.id,
            personality
        )

        return conversation

    async def _get_context(
        self,
        conversation_id: str,
        user_id: str | None = None,
        max_rounds: int = DEFAULT_MAX_CONTEXT_ROUNDS,
    ) -> list[dict[str, str]]:
        """获取最近 N 轮对话上下文。

        1轮 = 1次用户消息 + 1次AI回复

        优先从 Redis 短期记忆获取，如果不存在则从数据库获取并缓存。

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID（可选，用于短期记忆缓存）
            max_rounds: 最大轮数

        Returns:
            对话历史列表，格式为 [{"role": "user/assistant", "content": "..."}]
        """
        max_messages = max_rounds * 2

        # 优先从 Redis 短期记忆获取
        if self._short_term_memory and user_id:
            context = await self._short_term_memory.get_context(
                user_id, conversation_id, max_messages
            )
            if context:
                logger.debug(
                    "[AIConversationService] 从短期记忆获取上下文，对话: %s，数量: %d",
                    conversation_id, len(context)
                )
                return context

        # 从数据库获取
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(desc(AIMessage.created_at))
            .limit(max_messages)
        )
        result = await self._db.execute(stmt)
        messages = result.scalars().all()

        # 按时间正序排列（最早的在前）
        history = []
        for msg in reversed(messages):
            history.append({
                "role": msg.role,
                "content": msg.content,
            })

        # 如果有数据但短期记忆中没有，缓存到 Redis
        if history and self._short_term_memory and user_id:
            await self._short_term_memory.cache_from_database(
                user_id, conversation_id, history
            )
            logger.debug(
                "[AIConversationService] 从数据库获取上下文并缓存，对话: %s，数量: %d",
                conversation_id, len(history)
            )

        return history

    async def _get_memories(
        self,
        user_id: str,
        max_memories: int = 10,
    ) -> list[dict[str, Any]]:
        """获取用户的记忆用于上下文注入。

        从 ai_memories 表中获取用户的记忆，包括：
        - 长期记忆：用户画像、重要事件
        - 中期记忆：对话摘要、关键事实

        按重要度和访问时间排序返回。

        Args:
            user_id: 用户 ID
            max_memories: 最大记忆数量

        Returns:
            记忆列表，格式为 [{"type": "...", "content": "..."}]
        """
        # 优先获取长期记忆（用户画像、重要事件）
        long_term_memories = []
        if self._long_term_memory:
            long_term_memories = await self._long_term_memory.get_memories_for_context(
                user_id, max_memories=max_memories // 2
            )

        # 获取中期记忆
        mid_term_memories = []
        if self._mid_term_memory:
            mid_term_memories = await self._mid_term_memory.get_memories_for_context(
                user_id, max_memories=max_memories - len(long_term_memories)
            )

        # 合并记忆，长期记忆优先
        all_memories = long_term_memories + mid_term_memories

        # 如果两个服务都不可用，降级为直接查询
        if not all_memories and not self._long_term_memory and not self._mid_term_memory:
            now = datetime.now(timezone.utc)
            stmt = (
                select(AIMemory)
                .where(
                    AIMemory.user_id == user_id,
                    (AIMemory.expires_at.is_(None)) | (AIMemory.expires_at > now),
                )
                .order_by(
                    desc(AIMemory.importance),
                    desc(AIMemory.last_accessed_at),
                )
                .limit(max_memories)
            )
            result = await self._db.execute(stmt)
            memories = result.scalars().all()

            for mem in memories:
                all_memories.append({
                    "type": mem.memory_type,
                    "content": mem.content,
                    "importance": mem.importance,
                })
                mem.access_count += 1
                mem.last_accessed_at = now

            if all_memories:
                await self._db.flush()

        logger.debug(
            "[AIConversationService] 注入记忆，长期: %d，中期: %d",
            len(long_term_memories),
            len(mid_term_memories)
        )

        return all_memories

    def _format_memories_for_context(
        self,
        memories: list[dict[str, Any]],
        personality: str,
    ) -> str | None:
        """将记忆格式化为 System Prompt 注入内容。

        根据记忆类型分组格式化：
        - person_info: 用户画像信息
        - event: 重要事件
        - mid_term: 对话摘要和关键事实

        Args:
            memories: 记忆列表
            personality: 性格标识

        Returns:
            格式化后的记忆文本，如果无记忆则返回 None
        """
        if not memories:
            return None

        # 按类型分组
        person_info = []
        events = []
        facts = []

        for mem in memories:
            mem_type = mem.get("type", "")
            content = mem.get("content", "")
            key_facts = mem.get("key_facts", {})

            if mem_type == "person_info":
                # 用户画像信息
                if key_facts:
                    # 从 key_facts 中提取详细信息
                    life_status = key_facts.get("life_status", {})
                    if life_status:
                        if life_status.get("occupation"):
                            person_info.append(f"职业是{life_status['occupation']}")
                        if life_status.get("city"):
                            person_info.append(f"住在{life_status['city']}")
                        if life_status.get("pets"):
                            person_info.append(life_status["pets"])

                    interests = key_facts.get("interests", [])
                    if interests:
                        person_info.append(f"兴趣爱好：{'+'.join(interests[:5])}")

                    relations = key_facts.get("person_relations", [])
                    for rel in relations[:3]:
                        if isinstance(rel, dict) and rel.get("relation"):
                            info = rel.get("info", "")
                            person_info.append(f"{rel['relation']}({info})" if info else rel['relation'])

                # 如果没有 key_facts，使用 content
                if content and not person_info:
                    person_info.append(content)

            elif mem_type == "event" or mem_type == "long_term":
                # 重要事件
                if key_facts:
                    event_name = key_facts.get("event_name", "")
                    event_date = key_facts.get("event_date", "")
                    related_person = key_facts.get("related_person", "")
                    if event_name:
                        event_text = f"{related_person}的{event_name}" if related_person else event_name
                        if event_date:
                            event_text += f"（{event_date}）"
                        events.append(event_text)
                elif content:
                    events.append(content)

            else:
                # 中期记忆（摘要、关键事实）
                facts.append(content)

        # 构建注入文本
        parts = []

        if person_info:
            parts.append("【你对用户的了解】")
            parts.extend(f"- {info}" for info in person_info[:8])  # 最多8条

        if events:
            parts.append("\n【重要事件】")
            parts.extend(f"- {event}" for event in events[:5])  # 最多5条

        if facts:
            parts.append("\n【近期对话要点】")
            parts.extend(f"- {fact}" for fact in facts[:5])  # 最多5条

        if not parts:
            return None

        return "\n".join(parts)

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        user_id: str | None = None,
        token_count: int | None = None,
        crisis_level: str | None = None,
        crisis_keywords: str | None = None,
    ) -> AIMessage:
        """保存消息到数据库，并同步写入短期记忆。

        Args:
            conversation_id: 对话 ID
            role: 角色（user/assistant）
            content: 消息内容
            user_id: 用户 ID（可选，用于短期记忆缓存）
            token_count: Token 消耗数（可选）
            crisis_level: 危机级别（low/medium/high，可选）
            crisis_keywords: 匹配到的危机关键词（逗号分隔，可选）

        Returns:
            AIMessage 对象
        """
        message = AIMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_count=token_count,
            crisis_level=crisis_level,
            crisis_keywords=crisis_keywords,
        )
        self._db.add(message)

        # 更新会话的最后消息时间
        stmt = (
            select(AIConversation)
            .where(AIConversation.id == conversation_id)
        )
        result = await self._db.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.last_message_at = datetime.now(timezone.utc)

        await self._db.flush()

        # 写入短期记忆
        if self._short_term_memory and user_id:
            await self._short_term_memory.add_message(
                user_id=user_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
            )

        logger.debug(
            "[AIConversationService] 保存消息，对话: %s，角色: %s，长度: %d",
            conversation_id,
            role,
            len(content)
        )

        return message

    async def chat(
        self,
        user_id: str,
        message: str,
        personality: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """同步对话。

        Args:
            user_id: 用户 ID
            message: 用户消息
            personality: 性格标识
            conversation_id: 对话 ID（可选）

        Returns:
            包含对话结果的字典：
            - conversation_id: 对话 ID
            - message: AI 回复
            - personality: 性格标识
        """
        # 获取或创建对话
        conversation = await self._get_or_create_conversation(
            user_id, personality, conversation_id
        )

        # 获取对话上下文（优先从 Redis 短期记忆获取）
        history = await self._get_context(conversation.id, user_id)

        # 获取用户记忆用于注入
        memories = await self._get_memories(user_id)
        memory_context = self._format_memories_for_context(memories, personality)

        # 检测危机关键词
        crisis_result = self._crisis_detector.detect(message)
        if crisis_result:
            logger.warning(
                "[AIConversationService] 检测到危机信号，级别: %s",
                crisis_result["level"].value
            )

        # 保存用户消息（含危机标记，同时写入短期记忆）
        crisis_level_str = crisis_result["level"].value if crisis_result else None
        crisis_keywords_str = ",".join(crisis_result["keywords"]) if crisis_result else None
        await self._save_message(
            conversation.id, "user", message,
            user_id=user_id,
            crisis_level=crisis_level_str,
            crisis_keywords=crisis_keywords_str,
        )

        # 检查并增加配额
        await self._check_and_increment_quota(user_id)

        # 调用 AI 服务
        ai_service = self._get_ai_service(personality)
        context = {"history": history} if history else None
        # 如果有记忆上下文，注入到 context 中
        if memory_context:
            context = context or {}
            context["memory"] = memory_context
        ai_response = await ai_service.chat(message, context)

        # 如果检测到危机，追加安全信息并记录日志
        if crisis_result:
            safety_appendix = self._crisis_detector.get_safety_appendix(
                crisis_result["level"]
            )
            if safety_appendix:
                ai_response += safety_appendix

        # 保存 AI 回复（同时写入短期记忆）
        await self._save_message(conversation.id, "assistant", ai_response, user_id=user_id)

        # 提交事务
        await self._db.commit()

        # 异步生成摘要和提取长期记忆（真正的异步执行，不阻塞响应）
        self._create_background_task(self._try_generate_summary(user_id, conversation.id))
        self._create_background_task(self._try_extract_long_term_memory(user_id, conversation.id))

        return {
            "conversation_id": conversation.id,
            "message": ai_response,
            "personality": personality,
            "crisis_level": crisis_level_str,
            "crisis_keywords": crisis_keywords_str,
        }

    async def chat_stream(
        self,
        user_id: str,
        message: str,
        personality: str,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话（SSE 格式）。

        Args:
            user_id: 用户 ID
            message: 用户消息
            personality: 性格标识
            conversation_id: 对话 ID（可选）

        Yields:
            SSE 格式的文本片段：
            data: {"content": "xxx", "done": false}\\n\\n
            data: {"content": "", "done": true}\\n\\n
        """
        # 获取或创建对话
        conversation = await self._get_or_create_conversation(
            user_id, personality, conversation_id
        )

        # 获取对话上下文（优先从 Redis 短期记忆获取）
        history = await self._get_context(conversation.id, user_id)

        # 获取用户记忆用于注入
        memories = await self._get_memories(user_id)
        memory_context = self._format_memories_for_context(memories, personality)

        # 检测危机关键词
        crisis_result = self._crisis_detector.detect(message)
        if crisis_result:
            logger.warning(
                "[AIConversationService] 流式对话检测到危机信号，级别: %s",
                crisis_result["level"].value
            )

        # 保存用户消息（含危机标记，同时写入短期记忆）
        crisis_level_str = crisis_result["level"].value if crisis_result else None
        crisis_keywords_str = ",".join(crisis_result["keywords"]) if crisis_result else None
        await self._save_message(
            conversation.id, "user", message,
            user_id=user_id,
            crisis_level=crisis_level_str,
            crisis_keywords=crisis_keywords_str,
        )
        await self._db.commit()  # 提交用户消息

        # 检查并增加配额
        await self._check_and_increment_quota(user_id)

        # 调用 AI 流式服务
        ai_service = self._get_ai_service(personality)
        context = {"history": history} if history else None
        # 如果有记忆上下文，注入到 context 中
        if memory_context:
            context = context or {}
            context["memory"] = memory_context

        # 收集完整响应用于保存
        full_response = []

        try:
            async for sse_chunk in ai_service.chat_stream(message, context):
                # 解析 SSE 数据
                if sse_chunk.startswith("data: "):
                    data_str = sse_chunk[6:].strip()
                    if data_str:
                        try:
                            chunk_data = json.loads(data_str)
                            content = chunk_data.get("content", "")
                            is_done = chunk_data.get("done", False)
                            if content:
                                full_response.append(content)

                            # 拦截 AI 服务的原始 done 标记，延后发送
                            if is_done:
                                continue
                        except json.JSONDecodeError:
                            pass

                # 转发非结束的 SSE 数据
                yield sse_chunk

        except Exception as e:
            logger.error(
                "[AIConversationService] 流式对话异常: %s",
                str(e)
            )
            # 发送错误消息
            error_data = json.dumps(
                {"content": "抱歉，AI服务出现问题，请稍后重试。", "done": True},
                ensure_ascii=False
            )
            yield f"data: {error_data}\n\n"
            return

        # 流结束后追加危机安全信息（如果有）
        if crisis_result:
            safety_appendix = self._crisis_detector.get_safety_appendix(
                crisis_result["level"]
            )
            if safety_appendix:
                for char in safety_appendix:
                    sse_data = json.dumps(
                        {"content": char, "done": False},
                        ensure_ascii=False
                    )
                    yield f"data: {sse_data}\n\n"

                full_response.append(safety_appendix)

        # 保存完整的 AI 回复（同时写入短期记忆）
        complete_response = "".join(full_response)
        await self._save_message(conversation.id, "assistant", complete_response, user_id=user_id)
        await self._db.commit()

        logger.info(
            "[AIConversationService] 流式对话完成，对话: %s，回复长度: %d",
            conversation.id,
            len(complete_response)
        )

        # 发送带危机信息的结束标记
        end_data = json.dumps(
            {
                "content": "",
                "done": True,
                "crisis_level": crisis_level_str,
                "crisis_keywords": crisis_keywords_str,
            },
            ensure_ascii=False,
        )
        yield f"data: {end_data}\n\n"

        # 异步生成摘要和提取长期记忆（真正的异步执行，不阻塞响应）
        self._create_background_task(self._try_generate_summary(user_id, conversation.id))
        self._create_background_task(self._try_extract_long_term_memory(user_id, conversation.id))

    async def get_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取用户的对话列表。

        Args:
            user_id: 用户 ID
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            包含对话列表的字典：
            - items: 对话列表
            - total: 总数
            - page: 当前页码
            - page_size: 每页数量
        """
        # 查询对话数量
        count_stmt = (
            select(AIConversation)
            .where(
                AIConversation.user_id == user_id,
                AIConversation.is_active == True,  # noqa: E712
            )
        )
        count_result = await self._db.execute(count_stmt)
        total = len(count_result.all())

        # 查询对话列表
        offset = (page - 1) * page_size
        stmt = (
            select(AIConversation)
            .where(
                AIConversation.user_id == user_id,
                AIConversation.is_active == True,  # noqa: E712
            )
            .order_by(desc(AIConversation.last_message_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await self._db.execute(stmt)
        conversations = result.scalars().all()

        # 构建返回数据
        items = []
        for conv in conversations:
            # 获取最后一条消息预览
            last_msg_stmt = (
                select(AIMessage)
                .where(AIMessage.conversation_id == conv.id)
                .order_by(desc(AIMessage.created_at))
                .limit(1)
            )
            last_msg_result = await self._db.execute(last_msg_stmt)
            last_message = last_msg_result.scalar_one_or_none()

            items.append({
                "id": conv.id,
                "personality": conv.ai_persona,
                "title": conv.title,
                "last_message": last_message.content[:100] if last_message else None,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "created_at": conv.created_at.isoformat(),
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_greeting(
        self,
        user_id: str,
        personality: str | None = None,
    ) -> dict[str, Any]:
        """获取 AI 开场白。

        如果用户有活跃对话，返回上次对话的性格；
        否则创建新对话并返回开场白。

        Args:
            user_id: 用户 ID
            personality: 性格标识（可选，默认使用上次或默认性格）

        Returns:
            包含开场白的字典：
            - greeting: 开场白内容
            - personality: 性格标识
            - conversation_id: 对话 ID
        """
        # 如果未指定性格，查找上次使用的性格
        if not personality:
            last_conv_stmt = (
                select(AIConversation)
                .where(
                    AIConversation.user_id == user_id,
                    AIConversation.is_active == True,  # noqa: E712
                )
                .order_by(desc(AIConversation.last_message_at))
                .limit(1)
            )
            last_conv_result = await self._db.execute(last_conv_stmt)
            last_conv = last_conv_result.scalar_one_or_none()

            if last_conv:
                personality = last_conv.ai_persona
            else:
                personality = DEFAULT_PERSONALITY

        # 获取开场白
        greeting_text = get_greeting(personality)

        # 创建新对话
        conversation = await self._get_or_create_conversation(
            user_id, personality, None
        )

        # 如果是全新对话，保存开场白作为第一条 AI 消息
        # 检查是否已有消息
        msg_count_stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation.id)
        )
        msg_count_result = await self._db.execute(msg_count_stmt)
        existing_messages = msg_count_result.all()

        if not existing_messages:
            await self._save_message(conversation.id, "assistant", greeting_text, user_id=user_id)

        await self._db.commit()

        return {
            "greeting": greeting_text,
            "personality": personality,
            "conversation_id": conversation.id,
        }

    async def check_quota(self, user_id: str, is_vip: bool = False) -> dict[str, Any]:
        """检查用户的对话配额。

        Args:
            user_id: 用户 ID
            is_vip: 是否为 VIP 用户

        Returns:
            包含配额信息的字典：
            - daily_limit: 每日限制
            - used: 已使用次数
            - remaining: 剩余次数
            - can_chat: 是否可以继续对话
        """
        daily_limit = self._daily_limit_vip if is_vip else self._daily_limit

        # 从 Redis 获取当日已使用次数
        used = 0
        if self._redis:
            try:
                redis_key = get_daily_count_key(user_id)
                count_str = await self._redis.get(redis_key)
                if count_str:
                    used = int(count_str)
            except Exception as e:
                logger.warning(
                    "[AIConversationService] Redis 配额查询失败: %s，使用默认值 0",
                    str(e)
                )

        return {
            "daily_limit": daily_limit,
            "used": used,
            "remaining": daily_limit - used,
            "can_chat": used < daily_limit,
        }

    async def increment_quota(self, user_id: str) -> int:
        """增加用户的对话计数。

        Args:
            user_id: 用户 ID

        Returns:
            增加后的计数值
        """
        if not self._redis:
            return 0

        try:
            redis_key = get_daily_count_key(user_id)
            count = await self._redis.incr(redis_key)

            # 如果是第一次使用，设置过期时间为当天结束
            if count == 1:
                # 计算当天结束时间（第二天零点）
                now = datetime.now(timezone.utc)
                tomorrow = now.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                ttl_seconds = int((tomorrow - now).total_seconds())
                await self._redis.expire(redis_key, ttl_seconds)

            return count
        except Exception as e:
            logger.warning(
                "[AIConversationService] Redis 配额增量失败: %s",
                str(e)
            )
            return 0

    async def _check_and_increment_quota(self, user_id: str, is_vip: bool = False) -> None:
        """检查并增加配额，若超限则抛出异常。

        Args:
            user_id: 用户 ID
            is_vip: 是否为 VIP 用户

        Raises:
            AppError: 配额超限时抛出
        """
        quota = await self.check_quota(user_id, is_vip)
        if not quota["can_chat"]:
            raise AppError(
                code=ErrorCode.AI_QUOTA_EXCEEDED,
                message="今日对话次数已达上限，明天再来吧",
                status_code=429,
            )

        # 增加配额计数
        await self.increment_quota(user_id)

    async def _try_generate_summary(
        self,
        user_id: str,
        conversation_id: str,
    ) -> None:
        """尝试生成对话摘要。

        检查是否达到摘要生成条件，如果达到则异步生成。
        此方法不抛出异常，失败时仅记录日志。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
        """
        if not self._mid_term_memory:
            return

        try:
            # 检查是否需要生成摘要
            should_generate = await self._mid_term_memory.should_generate_summary(
                conversation_id
            )

            if not should_generate:
                return

            # 获取最近的对话消息用于摘要生成
            history = await self._get_context(conversation_id, user_id, max_rounds=10)

            if not history:
                return

            # 生成摘要
            logger.info(
                "[AIConversationService] 触发摘要生成，对话: %s",
                conversation_id
            )

            result = await self._mid_term_memory.generate_summary(
                user_id=user_id,
                conversation_id=conversation_id,
                messages=history,
            )

            if result:
                await self._db.commit()
                logger.info(
                    "[AIConversationService] 摘要生成成功，对话: %s",
                    conversation_id
                )

        except Exception as e:
            # 摘要生成失败不应影响对话流程
            logger.warning(
                "[AIConversationService] 摘要生成失败，对话: %s，错误: %s",
                conversation_id,
                str(e)
            )

    async def _try_extract_long_term_memory(
        self,
        user_id: str,
        conversation_id: str,
    ) -> None:
        """尝试从对话中提取长期记忆。

        分析对话内容，提取用户画像信息和重要事件。
        此方法不抛出异常，失败时仅记录日志。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
        """
        if not self._long_term_memory:
            return

        try:
            # 获取最近的对话消息用于提取
            history = await self._get_context(conversation_id, user_id, max_rounds=10)

            if not history:
                return

            # 先检查是否值得分析（使用规则快速过滤）
            conversation_text = " ".join([m.get("content", "") for m in history])
            should_remember_flag, _ = self._long_term_memory.should_remember(conversation_text)

            if not should_remember_flag:
                logger.debug(
                    "[AIConversationService] 对话内容不符合长期记忆提取条件，跳过"
                )
                return

            logger.info(
                "[AIConversationService] 触发长期记忆提取，对话: %s",
                conversation_id
            )

            result = await self._long_term_memory.extract_and_save(
                user_id=user_id,
                conversation_id=conversation_id,
                messages=history,
            )

            if result:
                await self._db.commit()
                logger.info(
                    "[AIConversationService] 长期记忆提取成功，对话: %s，画像更新: %s，事件数: %d",
                    conversation_id,
                    bool(result.get("profile_updates")),
                    len(result.get("events_created", []))
                )

        except Exception as e:
            # 长期记忆提取失败不应影响对话流程
            logger.warning(
                "[AIConversationService] 长期记忆提取失败，对话: %s，错误: %s",
                conversation_id,
                str(e)
            )

    async def cleanup_expired_memories(self) -> int:
        """清理过期的中期记忆。

        可由定时任务调用。

        Returns:
            删除的记忆数量
        """
        if not self._mid_term_memory:
            return 0

        return await self._mid_term_memory.cleanup_expired()
