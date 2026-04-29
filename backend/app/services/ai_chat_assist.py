"""AI 聊天辅助服务模块。

提供聊天场景下的 AI 辅助功能：
- 冷场救急：双方超10分钟无人回复时，生成话题建议
- 回复建议：停留1分钟未输入时，提供2-3个回复建议
- 语气优化：用户点击"AI润色"时，优化措辞让聊天更融洽
- 温柔退出：生成自然的结束语，帮助用户优雅结束对话

设计要点：
1. 复用现有 GLMChatService 实现 AI 能力
2. 频率限制防止滥用
3. 输出内容安全检查
4. 上下文敏感的个性化建议
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import httpx

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 智谱 GLM-4-Flash 模型
GLM_MODEL = "glm-4-flash"
GLM_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# 请求配置
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]

# 频率限制配置（Redis Key 前缀）
REDIS_KEY_PREFIX = "ai:chat_assist:rate:"
RATE_LIMIT_WINDOW = 60  # 时间窗口（秒）
RATE_LIMIT_MAX_REQUESTS = 10  # 每用户每分钟最大请求数

# 不同功能的自定义限制
RATE_LIMITS = {
    "topic": {"window": 120, "max": 3},      # 冷场话题：每2分钟最多3次
    "reply": {"window": 60, "max": 5},       # 回复建议：每分钟最多5次
    "polish": {"window": 60, "max": 10},     # 语气优化：每分钟最多10次
    "exit": {"window": 120, "max": 3},       # 温柔退出：每2分钟最多3次
}

# 内容长度限制
MAX_CONTEXT_LENGTH = 1000  # 对话上下文最大长度
MAX_INPUT_LENGTH = 500     # 用户输入最大长度

# 敏感词黑名单（AI 输出不应包含的内容）
BLOCKED_PATTERNS = [
    r"自杀|自残|不想活",
    r"毒品|吸毒|赌博",
    r"\d{11}",  # 手机号
    r"https?://",  # 网址链接
]


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

TOPIC_SUGGESTION_PROMPT = """你是一个聊天话题建议助手，擅长找到让聊天重新活跃起来的话题。

## 对话背景
{context}

## 任务
对话已经冷场一段时间，请生成 3 个有趣的话题建议，帮助打破沉默。

## 要求
1. 话题要自然、有趣，不要太刻意
2. 基于之前的对话内容，找到合理的延续点
3. 每个话题控制在一句话（最多30字）
4. 不要涉及敏感话题（政治、宗教等）
5. 语气温和，不给压力

## 输出格式
请严格按以下 JSON 格式输出，不要有任何额外内容：
{{
    "topics": [
        {{"id": 1, "content": "话题1内容"}},
        {{"id": 2, "content": "话题2内容"}},
        {{"id": 3, "content": "话题3内容"}}
    ]
}}"""

REPLY_SUGGESTION_PROMPT = """你是一个聊天回复建议助手，帮助用户找到合适的回复内容。

## 对话背景
{context}

## 对方最后说的话
{last_message}

## 任务
请生成 2-3 个回复建议，帮助用户不知道说什么时参考。

## 要求
1. 回复要自然、有温度
2. 可以是延续话题、表达感受、或者关心对方
3. 每个回复控制在20字以内
4. 不要用太正式的表达，保持聊天感

## 输出格式
请严格按以下 JSON 格式输出，不要有任何额外内容：
{{
    "replies": [
        {{"id": 1, "content": "回复1内容", "tone": "温和/轻松/关心"}},
        {{"id": 2, "content": "回复2内容", "tone": "温和/轻松/关心"}},
        {{"id": 3, "content": "回复3内容", "tone": "温和/轻松/关心"}}
    ]
}}"""

POLISH_MESSAGE_PROMPT = """你是一个聊天文案润色助手，帮助用户优化措辞，让聊天更融洽。

## 用户原始输入
{original_text}

## 任务
请将用户的输入优化为更温暖、更融洽的表达方式。

## 要求
1. 保持原意，不要改变核心内容
2. 让语气更温和、有温度
3. 适当使用语气词（如"呢"、"呀"、"吧"）让表达更柔和
4. 不要改变太多，保留用户的个性
5. 输出一句润色后的内容即可

## 输出格式
请直接输出润色后的文本，不要包含任何其他内容。"""

EXIT_MESSAGE_PROMPT = """你是一个聊天结束语建议助手，帮助用户生成自然的结尾语。

## 对话背景
{context}

## 任务
请生成 2-3 个自然的结束语，帮助用户优雅地结束对话。

## 要求
1. 结束语要自然、不突兀
2. 可以表达感谢、期待下次聊天、或者简单的告别
3. 每个结束语控制在30字以内
4. 不要太正式，保持聊天感
5. 不要让人感觉冷漠或敷衍

## 输出格式
请严格按以下 JSON 格式输出，不要有任何额外内容：
{{
    "exits": [
        {{"id": 1, "content": "结束语1内容"}},
        {{"id": 2, "content": "结束语2内容"}},
        {{"id": 3, "content": "结束语3内容"}}
    ]
}}"""


# ---------------------------------------------------------------------------
# 输出安全检查
# ---------------------------------------------------------------------------

def _check_output_safety(content: str) -> tuple[bool, str | None]:
    """检查 AI 输出内容是否安全。

    Args:
        content: 待检查的内容

    Returns:
        (是否安全, 匹配的模式或 None)
    """
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, content):
            return False, pattern
    return True, None


# ---------------------------------------------------------------------------
# AI 聊天辅助服务类
# ---------------------------------------------------------------------------

class AIChatAssistService:
    """AI 聊天辅助服务。

    提供聊天场景下的 AI 辅助功能。

    使用示例：
        service = AIChatAssistService(zhipu_api_key, redis)
        topics = await service.suggest_topics(user_id, context)
    """

    def __init__(
        self,
        api_key: str = "",
        redis: Any = None,
        timeout: float = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        """初始化 AI 聊天辅助服务。

        Args:
            api_key: 智谱 API Key
            redis: Redis 客户端（用于频率限制）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self._api_key = api_key
        self._redis = redis
        self._timeout = timeout
        self._max_retries = max_retries
        self._base_url = GLM_API_BASE_URL
        self._model = GLM_MODEL

        self._api_available = bool(api_key)

        if not self._api_available:
            logger.warning(
                "[AIChatAssist] API Key 未配置，服务将返回错误提示。"
            )
        else:
            logger.info("[AIChatAssist] 初始化完成，模型: %s", self._model)

    # =========================================================================
    # 公开接口
    # =========================================================================

    async def suggest_topics(
        self,
        user_id: str,
        context: str,
    ) -> dict[str, Any]:
        """生成冷场救急话题建议。

        Args:
            user_id: 用户ID
            context: 对话上下文

        Returns:
            话题建议结果

        Raises:
            AppError: API 调用失败或频率超限
        """
        # 检查频率限制
        await self._check_rate_limit(user_id, "topic")

        # 验证输入
        context = context[:MAX_CONTEXT_LENGTH]

        # 构建 Prompt
        prompt = TOPIC_SUGGESTION_PROMPT.format(context=context)

        # 调用 AI
        result = await self._call_ai(prompt)

        # 解析结果
        topics = self._parse_topics_result(result)

        # 记录频率使用
        await self._record_rate_limit(user_id, "topic")

        return {
            "type": "topic_suggestion",
            "topics": topics,
            "message": "试试这些话题吧~",
        }

    async def suggest_replies(
        self,
        user_id: str,
        context: str,
        last_message: str,
    ) -> dict[str, Any]:
        """生成回复建议。

        Args:
            user_id: 用户ID
            context: 对话上下文
            last_message: 对方最后说的话

        Returns:
            回复建议结果

        Raises:
            AppError: API 调用失败或频率超限
        """
        # 检查频率限制
        await self._check_rate_limit(user_id, "reply")

        # 验证输入
        context = context[:MAX_CONTEXT_LENGTH]
        last_message = last_message[:MAX_INPUT_LENGTH]

        # 构建 Prompt
        prompt = REPLY_SUGGESTION_PROMPT.format(
            context=context,
            last_message=last_message,
        )

        # 调用 AI
        result = await self._call_ai(prompt)

        # 解析结果
        replies = self._parse_replies_result(result)

        # 记录频率使用
        await self._record_rate_limit(user_id, "reply")

        return {
            "type": "reply_suggestion",
            "replies": replies,
            "message": "不知道说什么？参考这些吧~",
        }

    async def polish_message(
        self,
        user_id: str,
        original_text: str,
    ) -> dict[str, Any]:
        """润色用户消息。

        Args:
            user_id: 用户ID
            original_text: 用户原始输入

        Returns:
            润色结果

        Raises:
            AppError: API 调用失败或频率超限
        """
        # 检查频率限制
        await self._check_rate_limit(user_id, "polish")

        # 验证输入
        if not original_text or not original_text.strip():
            raise AppError(
                code=ErrorCode.CONTENT_EMPTY,
                message="请输入要润色的内容",
                status_code=400,
            )

        original_text = original_text[:MAX_INPUT_LENGTH]

        # 构建 Prompt
        prompt = POLISH_MESSAGE_PROMPT.format(original_text=original_text)

        # 调用 AI
        result = await self._call_ai(prompt)

        # 清理结果（去掉可能的引号和空格）
        polished_text = result.strip().strip('"').strip("'")

        # 安全检查
        is_safe, _ = _check_output_safety(polished_text)
        if not is_safe:
            polished_text = original_text  # 不安全则返回原文

        # 记录频率使用
        await self._record_rate_limit(user_id, "polish")

        return {
            "type": "polish",
            "original": original_text,
            "polished": polished_text,
            "message": "帮你润色了一下，看看这样表达会不会更好~",
        }

    async def suggest_exits(
        self,
        user_id: str,
        context: str,
    ) -> dict[str, Any]:
        """生成温柔退出结束语。

        Args:
            user_id: 用户ID
            context: 对话上下文

        Returns:
            结束语建议结果

        Raises:
            AppError: API 调用失败或频率超限
        """
        # 检查频率限制
        await self._check_rate_limit(user_id, "exit")

        # 验证输入
        context = context[:MAX_CONTEXT_LENGTH]

        # 构建 Prompt
        prompt = EXIT_MESSAGE_PROMPT.format(context=context)

        # 调用 AI
        result = await self._call_ai(prompt)

        # 解析结果
        exits = self._parse_exits_result(result)

        # 记录频率使用
        await self._record_rate_limit(user_id, "exit")

        return {
            "type": "exit_suggestion",
            "exits": exits,
            "message": "想结束了？试试这些说法~",
        }

    # =========================================================================
    # 频率限制
    # =========================================================================

    async def _check_rate_limit(self, user_id: str, action: str) -> None:
        """检查频率限制。

        Args:
            user_id: 用户ID
            action: 操作类型

        Raises:
            AppError: 频率超限
        """
        if not self._redis:
            return

        config = RATE_LIMITS.get(action, {"window": RATE_LIMIT_WINDOW, "max": RATE_LIMIT_MAX_REQUESTS})
        key = f"{REDIS_KEY_PREFIX}{action}:{user_id}"

        try:
            count = await self._redis.get(key)
            if count is not None:
                count_val = int(count) if isinstance(count, (int, str)) else 0
                if isinstance(count, bytes):
                    count_val = int(count.decode())

                if count_val >= config["max"]:
                    ttl = await self._redis.ttl(key)
                    raise AppError(
                        code=ErrorCode.RATE_LIMIT_EXCEEDED,
                        message=f"操作过于频繁，请 {ttl} 秒后再试",
                        status_code=429,
                    )
        except AppError:
            raise
        except Exception as e:
            logger.warning("[AIChatAssist] 频率限制检查失败: %s", str(e))

    async def _record_rate_limit(self, user_id: str, action: str) -> None:
        """记录频率使用。

        Args:
            user_id: 用户ID
            action: 操作类型
        """
        if not self._redis:
            return

        config = RATE_LIMITS.get(action, {"window": RATE_LIMIT_WINDOW, "max": RATE_LIMIT_MAX_REQUESTS})
        key = f"{REDIS_KEY_PREFIX}{action}:{user_id}"

        try:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, config["window"])
        except Exception as e:
            logger.warning("[AIChatAssist] 记录频率使用失败: %s", str(e))

    # =========================================================================
    # AI 调用
    # =========================================================================

    async def _call_ai(self, prompt: str) -> str:
        """调用 AI API。

        Args:
            prompt: 用户 Prompt

        Returns:
            AI 响应文本

        Raises:
            AppError: API 调用失败
        """
        if not self._api_available:
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="AI 服务暂时不可用",
                status_code=503,
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        last_error = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return content

            except httpx.TimeoutException:
                last_error = "请求超时"
                logger.warning("[AIChatAssist] 请求超时（第%d次）", attempt + 1)
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP 错误: {e.response.status_code}"
                logger.warning("[AIChatAssist] HTTP 错误（第%d次）: %s", attempt + 1, last_error)
            except Exception as e:
                last_error = f"未知错误: {str(e)}"
                logger.error("[AIChatAssist] 未知错误（第%d次）: %s", attempt + 1, last_error)

            if attempt < self._max_retries - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                await asyncio.sleep(delay)

        raise AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message=f"AI 服务暂时不可用: {last_error}",
            status_code=503,
        )

    # =========================================================================
    # 结果解析
    # =========================================================================

    def _parse_topics_result(self, result: str) -> list[dict[str, Any]]:
        """解析话题建议结果。

        Args:
            result: AI 返回的文本

        Returns:
            话题列表
        """
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{[\s\S]*"topics"[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group(0))
                return data.get("topics", [])
        except (json.JSONDecodeError, KeyError):
            pass

        # 降级：按行解析
        topics = []
        lines = result.strip().split("\n")
        for i, line in enumerate(lines[:3]):
            # 移除序号
            content = re.sub(r'^\d+[.、)）]\s*', '', line).strip()
            if content and len(content) <= 50:
                topics.append({"id": i + 1, "content": content})

        # 如果还是没有结果，返回默认建议
        if not topics:
            topics = [
                {"id": 1, "content": "最近有什么有趣的事吗？"},
                {"id": 2, "content": "你今天心情怎么样？"},
                {"id": 3, "content": "最近在忙什么呢？"},
            ]

        return topics

    def _parse_replies_result(self, result: str) -> list[dict[str, Any]]:
        """解析回复建议结果。

        Args:
            result: AI 返回的文本

        Returns:
            回复列表
        """
        try:
            json_match = re.search(r'\{[\s\S]*"replies"[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group(0))
                return data.get("replies", [])
        except (json.JSONDecodeError, KeyError):
            pass

        # 降级：按行解析
        replies = []
        lines = result.strip().split("\n")
        tones = ["温和", "轻松", "关心"]
        for i, line in enumerate(lines[:3]):
            content = re.sub(r'^\d+[.、)）]\s*', '', line).strip()
            if content and len(content) <= 30:
                replies.append({
                    "id": i + 1,
                    "content": content,
                    "tone": tones[i % len(tones)],
                })

        if not replies:
            replies = [
                {"id": 1, "content": "嗯嗯，你可以多说一点", "tone": "温和"},
                {"id": 2, "content": "原来是这样呀", "tone": "轻松"},
                {"id": 3, "content": "那你觉得怎么样呢？", "tone": "关心"},
            ]

        return replies

    def _parse_exits_result(self, result: str) -> list[dict[str, Any]]:
        """解析结束语建议结果。

        Args:
            result: AI 返回的文本

        Returns:
            结束语列表
        """
        try:
            json_match = re.search(r'\{[\s\S]*"exits"[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group(0))
                return data.get("exits", [])
        except (json.JSONDecodeError, KeyError):
            pass

        # 降级：按行解析
        exits = []
        lines = result.strip().split("\n")
        for i, line in enumerate(lines[:3]):
            content = re.sub(r'^\d+[.、)）]\s*', '', line).strip()
            if content and len(content) <= 50:
                exits.append({"id": i + 1, "content": content})

        if not exits:
            exits = [
                {"id": 1, "content": "我先忙一会儿，回头再聊~"},
                {"id": 2, "content": "今天先聊到这吧，下次继续"},
                {"id": 3, "content": "那我就不打扰啦，好好休息"},
            ]

        return exits


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_ai_chat_assist_service(
    api_key: str = "",
    redis: Any = None,
) -> AIChatAssistService:
    """创建 AI 聊天辅助服务实例。

    Args:
        api_key: 智谱 API Key
        redis: Redis 客户端

    Returns:
        AIChatAssistService 实例
    """
    return AIChatAssistService(api_key=api_key, redis=redis)
