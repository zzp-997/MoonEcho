"""中期记忆服务。

使用 MySQL 存储对话摘要和关键事实，支持：
- 对话摘要生成（每 10 轮对话生成一次）
- 关键事实提取（人物关系、生活状态、情绪模式）
- 30 天滚动淘汰（expires_at 过期清理）
- 记忆检索与上下文注入
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIMemory
from app.services.ai_chat import MockAIChat, GLMChatService, create_ai_chat_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 摘要生成触发阈值（消息数量，10 轮 = 20 条消息）
SUMMARY_TRIGGER_MESSAGES = 20

# 中期记忆过期天数
MID_TERM_MEMORY_EXPIRE_DAYS = 30

# 默认重要度
DEFAULT_IMPORTANCE = 5

# 记忆类型
MEMORY_TYPE_MID_TERM = "mid_term"
MEMORY_TYPE_PERSON_INFO = "person_info"
MEMORY_TYPE_EVENT = "event"


# ---------------------------------------------------------------------------
# 摘要生成 Prompt 模板
# ---------------------------------------------------------------------------

SUMMARY_SYSTEM_PROMPT = """你是一个对话分析助手，负责从对话中提取有价值的信息。

你的任务是分析对话内容，生成：
1. 一段简洁的对话摘要（100字以内）
2. 提取的关键事实（JSON格式）

关键事实类型包括：
- person_relations: 人物关系（如"有一个同事叫小李"、"和女朋友在一起两年了"）
- life_status: 生活状态（如"最近在准备考试"、"刚换了工作"）
- emotion_patterns: 情绪模式（如"深夜容易焦虑"、"周一上班前总是很紧张"）
- preferences: 沟通偏好（如"喜欢被倾听不喜欢建议"、"希望能被理解"）

请以JSON格式返回结果：
{
    "summary": "对话摘要...",
    "key_facts": {
        "person_relations": ["..."],
        "life_status": ["..."],
        "emotion_patterns": ["..."],
        "preferences": ["..."]
    },
    "importance": 5
}

importance 取值 1-10，表示记忆的重要程度：
- 1-3: 一般性信息（如日常琐事）
- 4-6: 有价值的信息（如生活状态、人际关系）
- 7-10: 重要信息（如重大事件、情绪危机）

注意：
- 只提取用户明确表达的信息，不要推测
- 如果没有明显的关键事实，返回空数组
- 摘要要简洁，突出重点"""

SUMMARY_USER_PROMPT_TEMPLATE = """请分析以下对话内容：

{conversation_text}

请生成摘要和提取关键事实。"""


# ---------------------------------------------------------------------------
# 中期记忆服务类
# ---------------------------------------------------------------------------

class MidTermMemory:
    """中期记忆服务，使用 MySQL 存储。

    功能：
    1. 对话摘要生成 - 每 10 轮对话生成一次摘要，调用 AI 生成
    2. 关键事实提取 - 从对话中提取人物关系、生活状态、情绪模式
    3. 30 天滚动淘汰 - expires_at 设置 30 天后过期
    4. 记忆检索 - 根据重要度和访问时间排序

    注意：
    - 摘要生成使用 MockAIChat 或 GLMChatService（根据配置）
    - 关键事实存储在 key_facts JSON 字段中
    - 每次检索时更新 access_count 和 last_accessed_at
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
    ) -> None:
        """初始化中期记忆服务。

        Args:
            db: 数据库会话
            ai_provider: AI 服务提供者（mock/glm_free/glm）
            zhipu_api_key: 智谱 API Key
        """
        self._db = db
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key

        # AI 服务实例（延迟初始化）
        self._ai_service: MockAIChat | GLMChatService | None = None

        logger.info(
            "[MidTermMemory] 初始化完成，AI Provider: %s",
            ai_provider
        )

    def _get_ai_service(self) -> MockAIChat | GLMChatService:
        """获取 AI 服务实例（延迟初始化）。

        使用 GLM-4-Flash 模型进行摘要生成，成本较低。

        Returns:
            AI 服务实例
        """
        if self._ai_service is None:
            self._ai_service = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                model="glm-4-flash",  # 使用便宜的模型
                personality="xiaowen",  # 使用温柔的风格
            )
        return self._ai_service

    async def should_generate_summary(
        self,
        conversation_id: str,
    ) -> bool:
        """检查是否需要生成摘要。

        每 20 条消息（10 轮对话）生成一次摘要。

        Args:
            conversation_id: 对话 ID

        Returns:
            是否需要生成摘要
        """
        from app.models.ai import AIMessage
        from sqlalchemy import func

        # 只计数消息数量，不加载全部数据
        message_count_stmt = (
            select(func.count(AIMessage.id))
            .where(AIMessage.conversation_id == conversation_id)
        )
        message_count = (await self._db.execute(message_count_stmt)).scalar() or 0

        # 检查是否达到触发阈值
        if message_count < SUMMARY_TRIGGER_MESSAGES:
            return False

        # 检查是否已经在该数量节点生成过摘要
        # 例如：20条时生成第一次，40条时生成第二次...
        expected_summary_count = message_count // SUMMARY_TRIGGER_MESSAGES

        # 只计数已有摘要数量
        summary_count_stmt = (
            select(func.count(AIMemory.id))
            .where(
                AIMemory.conversation_id == conversation_id,
                AIMemory.memory_type == MEMORY_TYPE_MID_TERM,
            )
        )
        existing_summary_count = (await self._db.execute(summary_count_stmt)).scalar() or 0

        # 如果已有摘要数量小于预期数量，则需要生成
        return existing_summary_count < expected_summary_count

    async def generate_summary(
        self,
        user_id: str,
        conversation_id: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any] | None:
        """生成对话摘要并提取关键事实。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            messages: 对话消息列表，格式为 [{"role": "user/assistant", "content": "..."}]

        Returns:
            生成结果字典，包含 summary、key_facts、importance；
            如果生成失败返回 None
        """
        if not messages:
            logger.debug(
                "[MidTermMemory] 无消息内容，跳过摘要生成"
            )
            return None

        try:
            # 构建对话文本
            conversation_text = self._format_conversation(messages)

            # 调用 AI 生成摘要
            ai_service = self._get_ai_service()

            # 构建请求
            prompt = SUMMARY_USER_PROMPT_TEMPLATE.format(
                conversation_text=conversation_text
            )

            context = {
                "history": [],  # 不需要历史上下文
            }

            # 调用 AI 服务
            response = await ai_service.chat(prompt, context)

            # 解析 JSON 响应
            result = self._parse_summary_response(response)

            if result:
                # 保存到数据库
                await self.save_memory(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    memory_type=MEMORY_TYPE_MID_TERM,
                    content=result.get("summary", ""),
                    key_facts=result.get("key_facts", {}),
                    importance=result.get("importance", DEFAULT_IMPORTANCE),
                )

                logger.info(
                    "[MidTermMemory] 摘要生成成功，对话: %s，重要度: %d",
                    conversation_id,
                    result.get("importance", DEFAULT_IMPORTANCE)
                )

            return result

        except Exception as e:
            logger.warning(
                "[MidTermMemory] 摘要生成失败: %s",
                str(e)
            )
            return None

    async def extract_key_facts(
        self,
        user_id: str,
        conversation_id: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        """从对话中提取关键事实。

        单独提取关键事实，不生成摘要。用于特定类型信息的提取。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            messages: 对话消息列表

        Returns:
            关键事实字典
        """
        # 复用 generate_summary 的逻辑，但只返回 key_facts
        result = await self.generate_summary(user_id, conversation_id, messages)

        if result:
            return result.get("key_facts", {})

        return {
            "person_relations": [],
            "life_status": [],
            "emotion_patterns": [],
            "preferences": [],
        }

    async def save_memory(
        self,
        user_id: str,
        conversation_id: str | None,
        memory_type: str,
        content: str,
        key_facts: dict[str, Any] | None = None,
        importance: int = DEFAULT_IMPORTANCE,
        source: str = "chat",
    ) -> AIMemory:
        """保存记忆到数据库。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID（可选）
            memory_type: 记忆类型（mid_term/person_info/event）
            content: 记忆内容
            key_facts: 关键事实（JSON）
            importance: 重要度（1-10）
            source: 来源（chat/diary/behavior）

        Returns:
            创建的 AIMemory 对象
        """
        # 计算过期时间（30天后）
        expires_at = datetime.now(timezone.utc) + timedelta(days=MID_TERM_MEMORY_EXPIRE_DAYS)

        memory = AIMemory(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            key_facts=key_facts,
            importance=max(1, min(10, importance)),  # 限制在 1-10 范围内
            source=source,
            expires_at=expires_at,
            access_count=0,
        )

        self._db.add(memory)
        await self._db.flush()

        logger.debug(
            "[MidTermMemory] 保存记忆成功，类型: %s，重要度: %d",
            memory_type,
            importance
        )

        return memory

    async def get_memories(
        self,
        user_id: str,
        max_memories: int = 10,
        memory_types: list[str] | None = None,
    ) -> list[AIMemory]:
        """获取用户的中期记忆。

        按重要度和访问时间排序，优先返回重要且最近访问的记忆。
        每次检索时更新 access_count 和 last_accessed_at。

        Args:
            user_id: 用户 ID
            max_memories: 最大记忆数量
            memory_types: 记忆类型过滤（可选）

        Returns:
            AIMemory 对象列表
        """
        now = datetime.now(timezone.utc)

        # 构建查询
        stmt = (
            select(AIMemory)
            .where(
                AIMemory.user_id == user_id,
                # 未过期或无过期时间
                (AIMemory.expires_at.is_(None)) | (AIMemory.expires_at > now),
            )
        )

        # 添加记忆类型过滤
        if memory_types:
            stmt = stmt.where(AIMemory.memory_type.in_(memory_types))

        # 排序和限制
        stmt = stmt.order_by(
            desc(AIMemory.importance),
            desc(AIMemory.last_accessed_at),
        ).limit(max_memories)

        result = await self._db.execute(stmt)
        memories = result.scalars().all()

        # 更新访问计数和最后访问时间
        for mem in memories:
            mem.access_count += 1
            mem.last_accessed_at = now

        if memories:
            await self._db.flush()
            logger.debug(
                "[MidTermMemory] 获取记忆成功，数量: %d",
                len(memories)
            )

        return list(memories)

    async def get_memories_for_context(
        self,
        user_id: str,
        max_memories: int = 10,
    ) -> list[dict[str, Any]]:
        """获取用于上下文注入的记忆列表。

        返回格式化的记忆列表，用于 AI 对话上下文。

        Args:
            user_id: 用户 ID
            max_memories: 最大记忆数量

        Returns:
            记忆列表，格式为 [{"type": "...", "content": "...", "importance": ...}]
        """
        memories = await self.get_memories(user_id, max_memories)

        result = []
        for mem in memories:
            result.append({
                "type": mem.memory_type,
                "content": mem.content,
                "importance": mem.importance,
            })

        return result

    async def cleanup_expired(self) -> int:
        """清理过期的记忆。

        删除 expires_at 小于当前时间的记忆记录。

        Returns:
            删除的记录数量
        """
        now = datetime.now(timezone.utc)

        stmt = (
            delete(AIMemory)
            .where(AIMemory.expires_at < now)
            .where(AIMemory.expires_at.isnot(None))
        )

        result = await self._db.execute(stmt)
        deleted_count = result.rowcount

        await self._db.commit()

        if deleted_count > 0:
            logger.info(
                "[MidTermMemory] 清理过期记忆完成，删除: %d 条",
                deleted_count
            )

        return deleted_count

    async def delete_memories_by_conversation(
        self,
        conversation_id: str,
    ) -> int:
        """删除指定对话的所有记忆。

        Args:
            conversation_id: 对话 ID

        Returns:
            删除的记录数量
        """
        stmt = (
            delete(AIMemory)
            .where(AIMemory.conversation_id == conversation_id)
        )

        result = await self._db.execute(stmt)
        deleted_count = result.rowcount

        await self._db.commit()

        logger.debug(
            "[MidTermMemory] 删除对话记忆完成，对话: %s，删除: %d 条",
            conversation_id,
            deleted_count
        )

        return deleted_count

    async def update_importance(
        self,
        memory_id: str,
        importance: int,
    ) -> bool:
        """更新记忆的重要度。

        Args:
            memory_id: 记忆 ID
            importance: 新的重要度（1-10）

        Returns:
            是否更新成功
        """
        stmt = (
            select(AIMemory)
            .where(AIMemory.id == memory_id)
        )
        result = await self._db.execute(stmt)
        memory = result.scalar_one_or_none()

        if not memory:
            return False

        memory.importance = max(1, min(10, importance))
        await self._db.commit()

        return True

    # -----------------------------------------------------------------------
    # 私有方法
    # -----------------------------------------------------------------------

    def _format_conversation(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """将消息列表格式化为对话文本。

        Args:
            messages: 消息列表

        Returns:
            格式化后的对话文本
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"AI: {content}")

        return "\n".join(lines)

    def _parse_summary_response(
        self,
        response: str,
    ) -> dict[str, Any] | None:
        """解析 AI 返回的摘要响应。

        尝试从响应中提取 JSON 结构。

        Args:
            response: AI 返回的文本

        Returns:
            解析后的字典，解析失败返回 None
        """
        if not response:
            return None

        try:
            # 尝试直接解析为 JSON
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        import re
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, response)

        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 如果无法解析 JSON，使用响应作为摘要
        logger.warning(
            "[MidTermMemory] 无法解析 AI 响应为 JSON，使用原始文本作为摘要"
        )

        return {
            "summary": response[:200],  # 限制长度
            "key_facts": {
                "person_relations": [],
                "life_status": [],
                "emotion_patterns": [],
                "preferences": [],
            },
            "importance": DEFAULT_IMPORTANCE,
        }


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------

def create_mid_term_memory(
    db: AsyncSession,
    ai_provider: str = "mock",
    zhipu_api_key: str = "",
) -> MidTermMemory:
    """创建中期记忆服务实例。

    Args:
        db: 数据库会话
        ai_provider: AI 服务提供者
        zhipu_api_key: 智谱 API Key

    Returns:
        MidTermMemory 实例
    """
    return MidTermMemory(
        db=db,
        ai_provider=ai_provider,
        zhipu_api_key=zhipu_api_key,
    )
