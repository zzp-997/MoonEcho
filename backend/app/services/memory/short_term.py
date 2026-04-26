"""短期记忆服务。

使用 Redis List 存储最近 5-10 轮对话原文，支持：
- 24 小时 TTL 自动过期
- 快速访问当前会话上下文
- 优雅降级（Redis 不可用时返回空列表）
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


# 默认配置
DEFAULT_MAX_MESSAGES = 10      # 最多保留 10 条消息（5 轮对话）
DEFAULT_TTL_SECONDS = 86400    # 24 小时 TTL

# Redis Key 前缀
REDIS_KEY_PREFIX = "ai:memory:short:"


class ShortTermMemory:
    """短期记忆服务，使用 Redis List 存储对话上下文。

    Key 设计：
    - ai:memory:short:{user_id}:{conversation_id} - 对话上下文列表

    数据结构：
    - Redis List，每条记录是 JSON：{"role": "user/assistant", "content": "..."}
    - 最多保留 10 条（5 轮对话）
    - TTL 24 小时

    使用示例：
        memory = ShortTermMemory(redis_client)
        await memory.add_message(user_id, conversation_id, "user", "你好")
        context = await memory.get_context(user_id, conversation_id)
    """

    def __init__(
        self,
        redis_client: Any,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """初始化短期记忆服务。

        Args:
            redis_client: Redis 异步客户端（redis.asyncio.Redis 或 MockRedis）
            max_messages: 最大消息数量（默认 10 条，即 5 轮对话）
            ttl_seconds: TTL 秒数（默认 24 小时）
        """
        self._redis = redis_client
        self._max_messages = max_messages
        self._ttl_seconds = ttl_seconds

    def _build_key(self, user_id: str, conversation_id: str) -> str:
        """构建 Redis Key。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID

        Returns:
            Redis Key 字符串
        """
        return f"{REDIS_KEY_PREFIX}{user_id}:{conversation_id}"

    async def add_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
    ) -> bool:
        """添加消息到短期记忆。

        将消息添加到 Redis List 的尾部，并限制列表长度。
        每次添加消息时刷新 TTL。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            role: 角色（user/assistant）
            content: 消息内容

        Returns:
            是否添加成功
        """
        if not self._redis:
            logger.debug(
                "[ShortTermMemory] Redis 客户端未初始化，跳过短期记忆存储"
            )
            return False

        try:
            key = self._build_key(user_id, conversation_id)
            message_data = json.dumps(
                {"role": role, "content": content},
                ensure_ascii=False
            )

            # 使用 pipeline 优化多个操作
            # 1. RPUSH 添加消息到列表尾部
            # 2. LTRIM 保留最新的 N 条消息
            # 3. EXPIRE 刷新 TTL

            # 检查是否支持 pipeline
            if hasattr(self._redis, 'pipeline'):
                async with self._redis.pipeline() as pipe:
                    pipe.rpush(key, message_data)
                    # LTRIM 保留最后 max_messages 条（负索引表示从尾部算起）
                    pipe.ltrim(key, -self._max_messages, -1)
                    pipe.expire(key, self._ttl_seconds)
                    await pipe.execute()
            else:
                # MockRedis 不支持 pipeline，逐个执行
                await self._redis.rpush(key, message_data)
                await self._redis.ltrim(key, -self._max_messages, -1)
                await self._redis.expire(key, self._ttl_seconds)

            logger.debug(
                "[ShortTermMemory] 添加消息成功，Key: %s，角色: %s",
                key, role
            )
            return True

        except Exception as e:
            logger.warning(
                "[ShortTermMemory] 添加消息失败: %s",
                str(e)
            )
            return False

    async def get_context(
        self,
        user_id: str,
        conversation_id: str,
        max_messages: int | None = None,
    ) -> list[dict[str, str]]:
        """获取对话上下文。

        从 Redis List 读取最近的对话历史。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            max_messages: 最大消息数量（可选，默认使用初始化时的配置）

        Returns:
            对话历史列表，格式为 [{"role": "user/assistant", "content": "..."}]
            如果 Redis 不可用或无数据，返回空列表
        """
        if not self._redis:
            logger.debug(
                "[ShortTermMemory] Redis 客户端未初始化，返回空上下文"
            )
            return []

        try:
            key = self._build_key(user_id, conversation_id)
            limit = max_messages or self._max_messages

            # LRANGE 获取指定范围内的消息（0 到 limit-1）
            messages = await self._redis.lrange(key, 0, limit - 1)

            if not messages:
                logger.debug(
                    "[ShortTermMemory] 无短期记忆数据，Key: %s",
                    key
                )
                return []

            # 解析 JSON 数据
            context = []
            for msg in messages:
                try:
                    # 处理 bytes 或 str 类型
                    if isinstance(msg, bytes):
                        msg = msg.decode('utf-8')
                    context.append(json.loads(msg))
                except json.JSONDecodeError as e:
                    logger.warning(
                        "[ShortTermMemory] 消息解析失败: %s",
                        str(e)
                    )
                    continue

            logger.debug(
                "[ShortTermMemory] 获取上下文成功，Key: %s，数量: %d",
                key, len(context)
            )
            return context

        except Exception as e:
            logger.warning(
                "[ShortTermMemory] 获取上下文失败: %s",
                str(e)
            )
            return []

    async def clear(
        self,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        """清空对话的短期记忆。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID

        Returns:
            是否清空成功
        """
        if not self._redis:
            return False

        try:
            key = self._build_key(user_id, conversation_id)
            await self._redis.delete(key)

            logger.debug(
                "[ShortTermMemory] 清空短期记忆成功，Key: %s",
                key
            )
            return True

        except Exception as e:
            logger.warning(
                "[ShortTermMemory] 清空短期记忆失败: %s",
                str(e)
            )
            return False

    async def set_ttl(
        self,
        user_id: str,
        conversation_id: str,
        seconds: int | None = None,
    ) -> bool:
        """设置或刷新短期记忆的 TTL。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            seconds: TTL 秒数（可选，默认使用初始化时的配置）

        Returns:
            是否设置成功
        """
        if not self._redis:
            return False

        try:
            key = self._build_key(user_id, conversation_id)
            ttl = seconds or self._ttl_seconds
            await self._redis.expire(key, ttl)

            logger.debug(
                "[ShortTermMemory] 设置 TTL 成功，Key: %s，TTL: %d 秒",
                key, ttl
            )
            return True

        except Exception as e:
            logger.warning(
                "[ShortTermMemory] 设置 TTL 失败: %s",
                str(e)
            )
            return False

    async def cache_from_database(
        self,
        user_id: str,
        conversation_id: str,
        messages: list[dict[str, str]],
    ) -> bool:
        """从数据库消息列表缓存到 Redis。

        当 Redis 中没有数据时，从数据库加载最近的对话历史并缓存。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            messages: 消息列表，格式为 [{"role": "user/assistant", "content": "..."}]

        Returns:
            是否缓存成功
        """
        if not self._redis or not messages:
            return False

        try:
            key = self._build_key(user_id, conversation_id)

            # 先清空现有数据
            await self._redis.delete(key)

            # 批量添加消息
            for msg in messages[-self._max_messages:]:
                message_data = json.dumps(msg, ensure_ascii=False)
                await self._redis.rpush(key, message_data)

            # 设置 TTL
            await self._redis.expire(key, self._ttl_seconds)

            logger.info(
                "[ShortTermMemory] 从数据库缓存成功，Key: %s，数量: %d",
                key, len(messages[-self._max_messages:])
            )
            return True

        except Exception as e:
            logger.warning(
                "[ShortTermMemory] 从数据库缓存失败: %s",
                str(e)
            )
            return False
