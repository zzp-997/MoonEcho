"""AI 文案润色服务模块。

提供动态广场发布前的 AI 文案润色功能：
- 多种风格可选（温暖治愈、轻松幽默、真诚分享）
- 生成 2 个版本供用户选择
- 保留原意和情感基调
- 使用 GLM-4-Flash 模型（成本低、速度快）
- 输出内容安全检查
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any

import httpx

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.schemas.ai_polish import PolishStyle

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 智谱 GLM-4-Flash 模型（成本低、速度快）
GLM_MODEL = "glm-4-flash"
GLM_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# 请求配置
REQUEST_TIMEOUT = 30.0  # 请求超时（秒）
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAYS = [1, 2, 4]  # 重试间隔（秒）

# 润色参数
MAX_CONTENT_LENGTH = 500  # 单次润色最大字数
VERSION_COUNT = 2  # 生成版本数量（减少 token 消耗）

# Redis 配置
REDIS_KEY_PREFIX = "ai:polish:rate:"
RATE_LIMIT_WINDOW = 60  # 频率限制时间窗口（秒）
RATE_LIMIT_MAX_REQUESTS = 5  # 每用户每分钟最大请求数


# ---------------------------------------------------------------------------
# 输出安全检查
# ---------------------------------------------------------------------------

# 敏感词黑名单（AI 输出不应包含的内容）
BLOCKED_PATTERNS = [
    # 自伤相关关键词
    r"自杀|自残|不想活|活着没意思|结束生命",
    # 违法内容
    r"毒品|吸毒|赌博|诈骗|传销",
    # 联系方式（不应包含）
    r"\d{11}",  # 手机号
    r"微信[号]?[:：]?\s*[a-zA-Z0-9_-]+",
    r"QQ[号]?[:：]?\s*\d+",
    # 广告引流
    r"加我|联系我|私聊|加好友",
    # 网址链接
    r"https?://",
]


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


def _sanitize_output(content: str, original: str) -> str:
    """清理输出内容，移除可能的问题。

    Args:
        content: AI 输出内容
        original: 原始内容

    Returns:
        清理后的内容，如果清理失败则返回原文
    """
    # 检查安全性
    is_safe, matched_pattern = _check_output_safety(content)
    if is_safe:
        return content

    # 记录警告
    logger.warning(
        "[AIPolish] 检测到敏感内容，模式: %s，将返回原文",
        matched_pattern
    )

    # 返回原文
    return original


# ---------------------------------------------------------------------------
# 润色风格 Prompt 模板
# ---------------------------------------------------------------------------

# 风格描述
STYLE_DESCRIPTIONS: dict[str, str] = {
    "warm": """温暖治愈风：
- 语气温柔、细腻，像朋友在轻声安慰
- 适当使用"呢"、"呀"、"吧"等柔和语气词
- 保留用户的情感表达，但用更温和的方式呈现
- 传递陪伴感和共情，让读者感到被理解""",

    "funny": """轻松幽默风：
- 语气活泼、幽默，像损友在调侃打趣
- 可以适当使用网络流行语（但不要过度）
- 用轻松的方式化解沉重，但不嘲讽用户的真实感受
- 保持接地气的口语化表达""",

    "sincere": """真诚分享风：
- 语气朴实、真挚，像朋友在私下交心
- 不刻意修饰，保持原汁原味的真实感
- 减少华丽的辞藻，用简单的语言表达
- 保留用户的个人特色表达方式""",
}


def _get_system_prompt(style: PolishStyle) -> str:
    """获取润色风格的 System Prompt。

    Args:
        style: 润色风格

    Returns:
        System Prompt 字符串
    """
    style_desc = STYLE_DESCRIPTIONS.get(style.value, STYLE_DESCRIPTIONS["warm"])

    return f"""你是一位专业的文案润色助手，帮助用户优化社交媒体的动态内容。

【润色原则】
1. 保留用户原意，不改变核心内容和情感基调
2. 润色后字数不超过原文的 1.5 倍
3. 保留用户的口语化表达（如"哈哈"、"呜呜"等）
4. 不添加虚构内容，不夸张
5. 保持内容的真实性，让读者感到真诚

【润色风格要求】
{style_desc}

【输出格式要求】
请严格按照以下 JSON 格式输出，不要有任何额外内容：
{{
    "versions": [
        {{"id": 1, "content": "润色版本1的内容"}},
        {{"id": 2, "content": "润色版本2的内容"}}
    ]
}}

注意：
- 必须输出 2 个不同的润色版本
- 两个版本在表达方式上要有明显差异
- 只输出 JSON，不要有任何其他文字"""  # noqa: E501


def _get_user_prompt(content: str, style: PolishStyle) -> str:
    """获取用户输入的 Prompt。

    Args:
        content: 用户原始内容
        style: 润色风格

    Returns:
        用户 Prompt 字符串
    """
    style_name = {
        "warm": "温暖治愈风",
        "funny": "轻松幽默风",
        "sincere": "真诚分享风",
    }.get(style.value, "温暖治愈风")

    return f"""请帮我润色以下内容，使用「{style_name}」风格：

原文：
{content}

请按照 JSON 格式输出 2 个润色版本。"""


class AIPolishService:
    """AI 文案润色服务。

    提供文案润色能力，支持多种风格：
    - 温暖治愈风：温柔、安慰、陪伴感
    - 轻松幽默风：活泼、有趣、接地气
    - 真诚分享风：朴实、真挚、无修饰
    """

    def __init__(
        self,
        api_key: str = "",
        timeout: float = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        """初始化 AI 润色服务。

        Args:
            api_key: 智谱 API Key，为空时无法调用 API
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._base_url = GLM_API_BASE_URL
        self._model = GLM_MODEL

        # 标记 API Key 是否可用
        self._api_available = bool(api_key)

        if not self._api_available:
            logger.warning(
                "[AIPolish] API Key 未配置，服务将返回错误提示。"
                "请在环境变量中设置 ZHIPU_API_KEY"
            )
        else:
            logger.info("[AIPolish] 初始化完成，模型: %s", self._model)

    def _get_retry_delay(self, attempt: int) -> float:
        """获取重试延迟时间。

        Args:
            attempt: 当前重试次数（从 0 开始）

        Returns:
            延迟时间（秒）
        """
        if attempt < len(RETRY_DELAYS):
            return RETRY_DELAYS[attempt]
        return RETRY_DELAYS[-1] * 2

    async def _call_api(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """调用智谱 API。

        Args:
            system_prompt: System Prompt
            user_prompt: 用户 Prompt

        Returns:
            (响应数据, 错误信息)：成功时返回 (data, None)，失败时返回 (None, error)
        """
        if not self._api_available:
            return None, "API Key 未配置"

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,  # 保留一定创造性
            "max_tokens": 1024,  # 润色内容不会太长
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
                    return data, None

            except httpx.TimeoutException:
                last_error = f"请求超时（{self._timeout}秒）"
                logger.warning("[AIPolish] 请求超时（第%d次）", attempt + 1)
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP 错误: {e.response.status_code}"
                logger.warning(
                    "[AIPolish] HTTP 错误（第%d次）: %s",
                    attempt + 1,
                    last_error
                )
            except Exception as e:
                last_error = f"未知错误: {str(e)}"
                logger.error(
                    "[AIPolish] 未知错误（第%d次）: %s",
                    attempt + 1,
                    last_error
                )

            # 重试前等待
            if attempt < self._max_retries - 1:
                delay = self._get_retry_delay(attempt)
                logger.info("[AIPolish] 等待 %.1f 秒后重试...", delay)
                await asyncio.sleep(delay)

        return None, last_error or "未知错误"

    def _parse_response(self, response_text: str) -> list[dict[str, Any]]:
        """解析 AI 返回的 JSON 响应。

        Args:
            response_text: AI 返回的文本

        Returns:
            润色版本列表

        Raises:
            AppError: 解析失败时抛出
        """
        # 尝试提取 JSON 内容
        text = response_text.strip()

        # 尝试直接解析
        try:
            data = json.loads(text)
            if "versions" in data:
                return data["versions"]
        except json.JSONDecodeError:
            pass

        # 尝试从 markdown 代码块中提取
        import re
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if "versions" in data:
                    return data["versions"]
            except json.JSONDecodeError:
                pass

        # 尝试提取任何 JSON 对象
        json_match = re.search(r'\{[\s\S]*"versions"[\s\S]*\}', text)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if "versions" in data:
                    return data["versions"]
            except json.JSONDecodeError:
                pass

        raise AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message="AI 服务返回数据格式异常，请稍后重试",
            status_code=500,
        )

    async def polish(
        self,
        content: str,
        style: PolishStyle = PolishStyle.WARM,
    ) -> dict[str, Any]:
        """执行文案润色。

        Args:
            content: 用户原始内容
            style: 润色风格

        Returns:
            润色结果，包含 original 和 versions 字段

        Raises:
            AppError: API 调用失败或解析失败时抛出
        """
        # 验证内容长度
        if len(content) > MAX_CONTENT_LENGTH:
            raise AppError(
                code=ErrorCode.CONTENT_TOO_LONG,
                message=f"内容超过最大长度限制（{MAX_CONTENT_LENGTH}字）",
                status_code=400,
            )

        if not self._api_available:
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="AI 服务暂时不可用，请稍后重试",
                status_code=503,
            )

        # 构建 Prompt
        system_prompt = _get_system_prompt(style)
        user_prompt = _get_user_prompt(content, style)

        logger.info(
            "[AIPolish] 开始润色，风格: %s，内容长度: %d",
            style.value,
            len(content)
        )

        # 调用 API
        data, error = await self._call_api(system_prompt, user_prompt)

        if error:
            logger.error("[AIPolish] API 调用失败: %s", error)
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="AI 服务暂时不可用，请稍后重试",
                status_code=503,
            )

        # 解析响应
        try:
            response_text = data["choices"][0]["message"]["content"]
            versions = self._parse_response(response_text)

            # 对每个版本进行安全检查
            safe_versions = []
            for v in versions:
                v["style"] = style.value
                # 安全检查，如果检测到敏感内容则用原文替代
                safe_content = _sanitize_output(v.get("content", ""), content)
                v["content"] = safe_content
                safe_versions.append(v)

            logger.info(
                "[AIPolish] 润色完成，生成 %d 个版本",
                len(safe_versions)
            )

            return {
                "original": content,
                "versions": safe_versions,
            }
        except (KeyError, IndexError) as e:
            logger.error("[AIPolish] 解析响应失败: %s, 数据: %s", e, data)
            raise AppError(
                code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                message="AI 服务返回数据异常，请稍后重试",
                status_code=500,
            )

    @staticmethod
    def get_rate_limit_key(user_id: str) -> str:
        """获取用户频率限制的 Redis 键。

        Args:
            user_id: 用户 ID

        Returns:
            Redis 键字符串
        """
        return f"{REDIS_KEY_PREFIX}{user_id}"


async def check_rate_limit(
    redis_client: Any,
    user_id: str,
) -> tuple[bool, int]:
    """检查用户润色请求频率限制。

    Args:
        redis_client: Redis 客户端
        user_id: 用户 ID

    Returns:
        (是否允许, 剩余次数)
    """
    key = AIPolishService.get_rate_limit_key(user_id)

    # 获取当前计数
    count_str = await redis_client.get(key)
    current_count = int(count_str) if count_str else 0

    if current_count >= RATE_LIMIT_MAX_REQUESTS:
        # 获取剩余时间
        ttl = await redis_client.ttl(key)
        return False, 0

    return True, RATE_LIMIT_MAX_REQUESTS - current_count - 1


async def increment_rate_limit(
    redis_client: Any,
    user_id: str,
) -> None:
    """增加用户润色请求计数（原子操作）。

    使用 incr 原子操作，如果 key 不存在会自动创建并返回 1。
    当返回值为 1 时，说明是新键，设置过期时间。

    Args:
        redis_client: Redis 客户端
        user_id: 用户 ID
    """
    key = AIPolishService.get_rate_limit_key(user_id)

    # incr 是原子操作，如果 key 不存在会自动创建并返回 1
    count = await redis_client.incr(key)

    # 当 count == 1 时说明是新键，设置过期时间
    if count == 1:
        await redis_client.expire(key, RATE_LIMIT_WINDOW)


def create_polish_service(api_key: str = "") -> AIPolishService:
    """创建 AI 润色服务实例。

    Args:
        api_key: 智谱 API Key，为空时从环境变量读取

    Returns:
        AIPolishService 实例
    """
    if not api_key:
        api_key = os.getenv("ZHIPU_API_KEY", "")

    return AIPolishService(api_key=api_key)
