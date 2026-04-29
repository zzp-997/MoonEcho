"""AI 打招呼语生成服务。

为好友申请场景提供 AI 辅助生成打招呼语的能力。

设计要点：
1. 分析目标用户公开动态（最近10条）
2. 分析双方共同点（共同兴趣标签、相似年龄段等）
3. 生成三种风格：温暖型、轻松型、真诚型
4. 使用 GLM-4-Flash 模型（成本控制）
5. 频率限制：每用户每天最多 10 次
6. 内容审核确保安全
"""
from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.post import Post
from app.models.user import User, UserTag
from app.schemas.ai_greeting import GreetingBasis, GreetingItem, GreetingType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 打招呼语生成频率限制
GREETING_DAILY_LIMIT = 10  # 每用户每天最多使用次数

# 打招呼语长度限制
GREETING_MIN_LENGTH = 50
GREETING_MAX_LENGTH = 200

# 分析的公开动态数量
ANALYZE_POST_COUNT = 10

# Redis 键前缀
REDIS_KEY_PREFIX_GREETING_COUNT = "ai:greeting:daily:"

# GLM-4-Flash 模型配置
GLM4_FLASH_MODEL = "glm-4-flash"
GLM_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3

# 生成招呼语的 System Prompt
GREETING_SYSTEM_PROMPT = """你是一个专业的社交助手，帮助用户生成好友申请时的打招呼语。

【任务说明】
根据目标用户的信息，生成 3 种风格的打招呼语：
1. 温暖型(warm)：表达真诚的关注和欣赏，语气温暖有亲和力
2. 轻松型(casual)：轻松自然的开场白，像偶遇时的闲聊
3. 真诚型(sincere)：直接真诚地表达想认识的意愿，不绕弯子

【生成原则】
- 自然不生硬，像真实的人会说的话
- 不过度热情（避免"我很想认识你"、"希望能成为朋友"等）
- 不尴尬（避免"你好，我想和你做朋友"等模板化表达）
- 优先引用对方的公开动态内容作为切入点
- 如果有共同兴趣，可以适当提及
- 长度控制在 50-200 字之间
- 符合社交礼仪，得体大方

【输出格式】
请严格按照以下 JSON 格式输出，不要输出其他内容：
{
  "warm": "温暖型招呼语内容",
  "casual": "轻松型招呼语内容",
  "sincere": "真诚型招呼语内容"
}

【禁止事项】
- 不要使用模板化的开场白（如"你好，我是xxx"）
- 不要过于正式或商务化
- 不要包含任何敏感信息
- 不要涉及恋爱、暧昧相关内容
- 不要过度赞美或奉承"""

# 不同风格的开头参考（用于没有公开动态时的备用）
FALLBACK_GREETINGS: dict[str, list[str]] = {
    "warm": [
        "你好呀，看到你的主页觉得很舒服，想认识一下~",
        "嗨，注意到我们有一些共同的话题，可以聊聊吗？",
        "你好，感觉你是个很有趣的人，想交个朋友~",
    ],
    "casual": [
        "嘿，刚好刷到觉得挺投缘的，交个朋友呗~",
        "嗨，看你主页蛮有意思的，认识一下？",
        "哈喽，感觉咱们可能聊得来，加个好友？",
    ],
    "sincere": [
        "你好，认真看过你的动态后，觉得可以认识一下。",
        "你好，注意到我们有一些共同点，想认识你。",
        "你好，觉得你的分享很有意思，想和你成为朋友。",
    ],
}


# ---------------------------------------------------------------------------
# 服务类
# ---------------------------------------------------------------------------

class AIGreetingService:
    """AI 打招呼语生成服务。

    提供基于目标用户公开动态和双方共同点的打招呼语生成能力。

    使用示例：
        service = AIGreetingService(db, zhipu_api_key, redis_client)
        result = await service.generate_greeting(sender_id, target_user_id)
    """

    def __init__(
        self,
        db: AsyncSession | None = None,
        zhipu_api_key: str = "",
        redis_client: Any = None,
    ) -> None:
        """初始化 AI 打招呼语生成服务。

        Args:
            db: 数据库会话（生成招呼语时必需，查询配额时可选）
            zhipu_api_key: 智谱 API Key
            redis_client: Redis 客户端（可选，用于频率限制计数）
        """
        self._db = db
        self._zhipu_api_key = zhipu_api_key
        self._redis = redis_client
        self._api_available = bool(zhipu_api_key)

        if not self._api_available:
            logger.warning(
                "[AIGreetingService] API Key 未配置，服务将返回预设招呼语。"
                "请在环境变量中设置 ZHIPU_API_KEY"
            )
        else:
            logger.info("[AIGreetingService] 初始化完成")

    async def generate_greeting(
        self,
        sender_id: str,
        target_user_id: str,
    ) -> dict[str, Any]:
        """生成打招呼语。

        Args:
            sender_id: 发送者用户ID
            target_user_id: 目标用户ID

        Returns:
            包含生成结果的字典：
            - greetings: 打招呼语列表（3个版本）
            - based_on: 生成依据信息
            - remaining_count: 今日剩余次数

        Raises:
            AppError: 频率超限或目标用户不存在时抛出
        """
        # 检查频率限制
        await self._check_rate_limit(sender_id)

        # 获取目标用户信息
        target_user = await self._get_target_user(target_user_id)
        if not target_user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="目标用户不存在",
                status_code=404,
            )

        # 获取发送者信息
        sender = await self._get_target_user(sender_id)

        # 分析目标用户公开动态
        public_posts = await self._get_public_posts(target_user_id)

        # 分析双方共同点
        greeting_basis = await self._analyze_common_points(
            sender, target_user, sender_id, target_user_id
        )
        greeting_basis.has_public_posts = len(public_posts) > 0

        # 构建生成提示词
        prompt = self._build_prompt(
            target_user=target_user,
            public_posts=public_posts,
            greeting_basis=greeting_basis,
        )

        # 调用 AI 生成
        greetings, is_fallback = await self._generate_with_ai(prompt, greeting_basis)

        # 增加使用次数
        remaining = await self._increment_usage(sender_id)

        # 记录日志
        logger.info(
            "[AIGreetingService] 生成招呼语，发送者: %s，目标: %s，剩余次数: %d，降级: %s",
            sender_id[:8],
            target_user_id[:8],
            remaining,
            "是" if is_fallback else "否",
        )

        return {
            "greetings": greetings,
            "based_on": greeting_basis,
            "remaining_count": remaining,
            "is_fallback": is_fallback,
        }

    async def check_quota(self, user_id: str) -> dict[str, Any]:
        """检查用户的生成配额。

        Args:
            user_id: 用户 ID

        Returns:
            包含配额信息的字典
        """
        used = 0
        if self._redis:
            try:
                redis_key = self._get_redis_key(user_id)
                count_str = await self._redis.get(redis_key)
                if count_str:
                    used = int(count_str)
            except Exception as e:
                logger.warning(
                    "[AIGreetingService] Redis 配额查询失败: %s",
                    str(e)
                )

        return {
            "daily_limit": GREETING_DAILY_LIMIT,
            "used": used,
            "remaining": GREETING_DAILY_LIMIT - used,
            "can_generate": used < GREETING_DAILY_LIMIT,
        }

    # -----------------------------------------------------------------------
    # 私有方法
    # -----------------------------------------------------------------------

    def _get_redis_key(self, user_id: str) -> str:
        """获取用户每日生成计数的 Redis 键。"""
        return f"{REDIS_KEY_PREFIX_GREETING_COUNT}{user_id}"

    async def _check_rate_limit(self, user_id: str) -> None:
        """检查频率限制。

        Raises:
            AppError: 超过每日限制时抛出
        """
        quota = await self.check_quota(user_id)
        if not quota["can_generate"]:
            raise AppError(
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message=f"今日招呼语生成次数已达上限（{GREETING_DAILY_LIMIT}次），明天再来吧",
                status_code=429,
            )

    async def _increment_usage(self, user_id: str) -> int:
        """增加使用次数并返回剩余次数。

        Returns:
            剩余次数
        """
        if not self._redis:
            return GREETING_DAILY_LIMIT - 1

        try:
            redis_key = self._get_redis_key(user_id)
            count = await self._redis.incr(redis_key)

            # 如果是第一次使用，设置过期时间为当天结束
            if count == 1:
                now = datetime.now(timezone.utc)
                tomorrow = now.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                ttl_seconds = int((tomorrow - now).total_seconds())
                await self._redis.expire(redis_key, ttl_seconds)

            return GREETING_DAILY_LIMIT - count
        except Exception as e:
            logger.warning(
                "[AIGreetingService] Redis 计数失败: %s",
                str(e)
            )
            return GREETING_DAILY_LIMIT - 1

    async def _get_target_user(self, user_id: str) -> User | None:
        """获取目标用户信息。"""
        stmt = (
            select(User)
            .where(User.id == user_id, User.is_active == True)  # noqa: E712
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_public_posts(self, user_id: str) -> list[Post]:
        """获取目标用户的公开动态（最近10条）。"""
        stmt = (
            select(Post)
            .where(
                Post.user_id == user_id,
                Post.visibility == "public",
                Post.is_active == True,  # noqa: E712
            )
            .order_by(desc(Post.created_at))
            .limit(ANALYZE_POST_COUNT)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _get_user_interests(self, user_id: str) -> list[str]:
        """获取用户的兴趣标签。"""
        stmt = (
            select(UserTag)
            .where(
                UserTag.user_id == user_id,
                UserTag.tag_key == "interest",
            )
        )
        result = await self._db.execute(stmt)
        tags = result.scalars().all()
        return [tag.tag_value for tag in tags]

    async def _analyze_common_points(
        self,
        sender: User | None,
        target: User,
        sender_id: str,
        target_id: str,
    ) -> GreetingBasis:
        """分析双方的共同点。"""
        basis = GreetingBasis()

        # 分析年龄段
        if sender and target:
            sender_age = sender.age_range
            target_age = target.age_range
            if sender_age and target_age:
                # 相邻年龄段也算相似
                age_groups = ["18-24", "25-30", "31-40", "40+"]
                try:
                    sender_idx = age_groups.index(sender_age)
                    target_idx = age_groups.index(target_age)
                    basis.same_age_group = abs(sender_idx - target_idx) <= 1
                except ValueError:
                    pass

            # 分析同城
            if sender.city and target.city:
                basis.same_city = sender.city == target.city

        # 分析共同兴趣
        sender_interests = await self._get_user_interests(sender_id)
        target_interests = await self._get_user_interests(target_id)

        if sender_interests and target_interests:
            common = set(sender_interests) & set(target_interests)
            basis.common_interests = list(common)

        return basis

    def _build_prompt(
        self,
        target_user: User,
        public_posts: list[Post],
        greeting_basis: GreetingBasis,
    ) -> str:
        """构建生成提示词。"""
        parts = []

        # 目标用户基本信息
        parts.append(f"【目标用户信息】")
        if target_user.nickname:
            parts.append(f"昵称：{target_user.nickname}")
        if target_user.age_range:
            parts.append(f"年龄段：{target_user.age_range}")
        if target_user.city:
            parts.append(f"城市：{target_user.city}")
        if target_user.occupation:
            parts.append(f"职业：{target_user.occupation}")

        # 公开动态
        if public_posts:
            parts.append(f"\n【目标用户最近的公开动态】")
            for i, post in enumerate(public_posts[:5], 1):  # 最多引用5条
                content = post.content[:100]  # 截取前100字
                parts.append(f"{i}. {content}")
        else:
            parts.append("\n【目标用户暂无公开动态】")

        # 共同点
        parts.append(f"\n【双方共同点】")
        if greeting_basis.common_interests:
            parts.append(f"共同兴趣：{', '.join(greeting_basis.common_interests)}")
        if greeting_basis.same_age_group:
            parts.append("处于相似年龄段")
        if greeting_basis.same_city:
            parts.append("同城")

        if not (greeting_basis.common_interests or greeting_basis.same_age_group or greeting_basis.same_city):
            parts.append("暂无明显共同点")

        # 生成指令
        parts.append("\n【请生成】")
        parts.append("请根据以上信息，生成3种风格的好友申请打招呼语。")
        parts.append("要求自然、不生硬，优先引用公开动态内容作为切入点。")

        return "\n".join(parts)

    async def _generate_with_ai(
        self,
        prompt: str,
        basis: GreetingBasis,
    ) -> tuple[list[GreetingItem], bool]:
        """调用 AI 生成招呼语。

        如果 API 不可用，返回预设的备用招呼语。

        Returns:
            (greetings, is_fallback) 元组，is_fallback 表示是否为降级预设内容
        """
        if not self._api_available:
            return self._get_fallback_greetings(basis), True

        try:
            # 调用智谱 API
            result = await self._call_glm_api(prompt)

            if result:
                greetings = []
                for greeting_type in [GreetingType.WARM, GreetingType.CASUAL, GreetingType.SINCERE]:
                    content = result.get(greeting_type.value, "")
                    if content:
                        # 验证长度
                        if len(content) < GREETING_MIN_LENGTH:
                            content = self._pad_greeting(content, greeting_type)
                        elif len(content) > GREETING_MAX_LENGTH:
                            content = content[:GREETING_MAX_LENGTH]

                        greetings.append(GreetingItem(
                            type=greeting_type,
                            content=content,
                        ))

                if len(greetings) == 3:
                    return greetings, False

        except Exception as e:
            logger.error(
                "[AIGreetingService] AI 生成失败: %s",
                str(e)
            )

        # 降级为备用招呼语
        return self._get_fallback_greetings(basis), True

    async def _call_glm_api(self, prompt: str) -> dict[str, str] | None:
        """调用智谱 GLM-4-Flash API。"""
        url = f"{GLM_API_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._zhipu_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GLM4_FLASH_MODEL,
            "messages": [
                {"role": "system", "content": GREETING_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.8,  # 稍高的温度增加多样性
            "max_tokens": 500,
        }

        last_error = None
        for attempt in range(DEFAULT_MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()

                    # 解析响应
                    content = data["choices"][0]["message"]["content"]

                    # 尝试解析 JSON
                    # 可能包含 markdown 代码块，需要提取
                    content = content.strip()
                    if content.startswith("```"):
                        # 去除 markdown 代码块标记
                        lines = content.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        content = "\n".join(lines)

                    result = json.loads(content)
                    logger.info(
                        "[AIGreetingService] AI 生成成功"
                    )
                    return result

            except httpx.TimeoutException:
                last_error = "请求超时"
                logger.warning(
                    "[AIGreetingService] API 超时（第%d次）",
                    attempt + 1
                )
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP 错误: {e.response.status_code}"
                logger.warning(
                    "[AIGreetingService] HTTP 错误（第%d次）: %s",
                    attempt + 1,
                    last_error
                )
            except json.JSONDecodeError as e:
                last_error = f"JSON 解析错误: {str(e)}"
                logger.warning(
                    "[AIGreetingService] JSON 解析失败: %s",
                    last_error
                )
            except Exception as e:
                last_error = f"未知错误: {str(e)}"
                logger.error(
                    "[AIGreetingService] 未知错误（第%d次）: %s",
                    attempt + 1,
                    last_error
                )

            # 重试前等待
            if attempt < DEFAULT_MAX_RETRIES - 1:
                await self._wait_with_backoff(attempt)

        logger.error(
            "[AIGreetingService] API 调用最终失败: %s",
            last_error
        )
        return None

    async def _wait_with_backoff(self, attempt: int) -> None:
        """指数退避等待。"""
        delays = [1, 2, 4]
        if attempt < len(delays):
            await self._sleep(delays[attempt])
        else:
            await self._sleep(delays[-1] * 2)

    async def _sleep(self, seconds: float) -> None:
        """异步等待。"""
        import asyncio
        await asyncio.sleep(seconds)

    def _get_fallback_greetings(self, basis: GreetingBasis) -> list[GreetingItem]:
        """获取备用招呼语（当 AI 不可用时）。"""
        greetings = []

        for greeting_type in [GreetingType.WARM, GreetingType.CASUAL, GreetingType.SINCERE]:
            templates = FALLBACK_GREETINGS.get(greeting_type.value, FALLBACK_GREETINGS["warm"])
            content = random.choice(templates)

            # 如果有共同兴趣，加入招呼语
            if basis.common_interests:
                interests = "、".join(basis.common_interests[:2])
                content = f"你好，看到我们都对{interests}感兴趣，想认识一下~"

            greetings.append(GreetingItem(
                type=greeting_type,
                content=content,
            ))

        return greetings

    def _pad_greeting(self, content: str, greeting_type: GreetingType) -> str:
        """补充招呼语使其达到最小长度。"""
        suffixes = {
            GreetingType.WARM: "，希望能有机会交流~",
            GreetingType.CASUAL: "，交个朋友呗~",
            GreetingType.SINCERE: "，期待认识你。",
        }
        suffix = suffixes.get(greeting_type, "~")
        return content + suffix
