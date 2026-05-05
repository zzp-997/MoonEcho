"""认证服务模块。

核心业务逻辑层，封装以下能力：
- 短信验证码发送与验证（Redis 存储，5 分钟有效，60 秒冷却）
- JWT Token 签发与刷新（HS256，access_token 15 分钟，refresh_token 7 天）
- 用户注册与登录（手机号加密存储，SHA-256 哈希唯一索引）
- 速率限制（Redis 计数器：登录 5 次/15 分钟，验证码 1 次/分钟）
- 青少年模式（18 岁以下自动标记，受限接口拦截）
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings
from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.user import User
from app.schemas.auth import (
    AGE_RANGE_OPTIONS,
    CompleteProfileRequest,
    CurrentUserResponse,
    RefreshTokenRequest,
    SendCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from app.services.crypto import decrypt_phone, encrypt_phone, phone_hash
from app.services.sms import SMSServiceProtocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

def _sms_code_key(phone: str) -> str:
    """验证码存储 key。"""
    return f"sms:code:{phone}"


def _sms_cooldown_key(phone: str) -> str:
    """验证码发送冷却 key。"""
    return f"sms:cooldown:{phone}"


def _rate_limit_login_key(phone: str) -> str:
    """登录速率限制 key。"""
    return f"rate:login:{phone}"


# ---------------------------------------------------------------------------
# JWT 配置常量
# ---------------------------------------------------------------------------

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ---------------------------------------------------------------------------
# 认证服务
# ---------------------------------------------------------------------------

class AuthService:
    """认证服务，封装所有认证相关业务逻辑。

    依赖外部注入：
    - sms_service: 短信验证码服务
    - settings: 应用配置
    - redis: Redis 客户端（aioredis）
    """

    def __init__(
        self,
        sms_service: SMSServiceProtocol,
        settings: AppSettings,
        redis: Any,
    ) -> None:
        self._sms = sms_service
        self._settings = settings
        self._redis = redis
        self._jwt_secret = self._load_jwt_secret()

    # -----------------------------------------------------------------------
    # JWT 密钥
    # -----------------------------------------------------------------------

    @staticmethod
    def _load_jwt_secret() -> str:
        """从环境变量加载 JWT 密钥。

        生产环境强制要求配置 JWT_SECRET_KEY，否则启动时抛出异常。
        这是为了防止攻击者使用已知的默认密钥伪造 JWT Token。

        Raises:
            RuntimeError: 生产环境未配置 JWT_SECRET_KEY 时抛出
        """
        import os

        from app.core.config import _environment_name

        secret = os.getenv("JWT_SECRET_KEY")
        if not secret:
            env = _environment_name()
            if env == "production":
                # 生产环境强制要求配置 JWT 密钥
                raise RuntimeError(
                    "生产环境必须配置 JWT_SECRET_KEY 环境变量！"
                    "请生成一个高强度的随机密钥（建议 32 字节以上）并配置到环境变量中。"
                )
            logger.warning(
                "未配置 JWT_SECRET_KEY 环境变量，使用默认密钥。"
                "此密钥仅用于开发/测试环境，生产环境务必配置独立密钥！"
            )
            secret = "echo-jwt-secret-key-dev-only-2024"
        return secret

    # -----------------------------------------------------------------------
    # 发送验证码
    # -----------------------------------------------------------------------

    async def send_code(self, phone: str) -> SendCodeResponse:
        """发送短信验证码。

        流程：
        1. 检查 60 秒冷却期
        2. 调用 SMS 服务发送验证码
        3. 存储验证码到 Redis（5 分钟有效）
        4. 设置冷却标记（60 秒）

        Args:
            phone: 明文手机号

        Returns:
            SendCodeResponse: 发送结果

        Raises:
            AppError: 发送过于频繁时抛出
        """
        # 1. 检查冷却期
        cooldown_key = _sms_cooldown_key(phone)
        cooldown_remaining = await self._redis.ttl(cooldown_key)
        if cooldown_remaining and cooldown_remaining > 0:
            raise AppError(
                code=ErrorCode.VERIFICATION_CODE_TOO_FREQUENT,
                message=f"验证码发送过于频繁，请 {cooldown_remaining} 秒后重试",
                status_code=429,
            )

        # 2. 调用 SMS 服务发送验证码
        result = await self._sms.send_code(phone)
        code = result["code"]
        expires_in = result["expires_in"]
        message_id = result["message_id"]

        # 3. 存储验证码到 Redis（5 分钟有效）
        code_key = _sms_code_key(phone)
        await self._redis.setex(code_key, expires_in, code)

        # 4. 设置冷却标记（60 秒）
        await self._redis.setex(cooldown_key, 60, "1")

        logger.info("验证码已发送: phone=***%s, message_id=%s", phone[-4:], message_id)

        return SendCodeResponse(
            message_id=message_id,
            expires_in=expires_in,
        )

    # -----------------------------------------------------------------------
    # 验证码登录/注册
    # -----------------------------------------------------------------------

    async def verify_code(
        self,
        request: VerifyCodeRequest,
        db: AsyncSession,
    ) -> VerifyCodeResponse:
        """验证码登录/注册。

        流程：
        1. 检查登录速率限制
        2. 从 Redis 读取验证码并校验
        3. 查找用户（通过 phone_hash）
        4. 新用户自动创建
        5. 签发 JWT Token

        Args:
            request: 验证码登录请求
            db: 数据库会话

        Returns:
            VerifyCodeResponse: 登录/注册结果

        Raises:
            AppError: 验证码过期、无效或登录次数过多时抛出
        """
        phone = request.phone
        code = request.code

        # 1. 检查登录速率限制
        await self._check_login_rate_limit(phone)

        # 2. 从 Redis 读取并校验验证码
        code_key = _sms_code_key(phone)
        stored_code = await self._redis.get(code_key)

        if stored_code is None:
            raise AppError(
                code=ErrorCode.VERIFICATION_CODE_EXPIRED,
                message="验证码已过期，请重新获取",
                status_code=400,
            )

        # Redis 返回的可能是 bytes 类型，需要解码
        if isinstance(stored_code, bytes):
            stored_code = stored_code.decode("utf-8")

        if stored_code != code:
            # 增加登录失败计数
            await self._increment_login_rate_limit(phone)
            raise AppError(
                code=ErrorCode.VERIFICATION_CODE_INVALID,
                message="验证码错误",
                status_code=400,
            )

        # 验证成功，删除验证码（一次性使用）
        await self._redis.delete(code_key)
        # 清除登录失败计数
        rate_key = _rate_limit_login_key(phone)
        await self._redis.delete(rate_key)

        # 3. 查找用户
        hash_value = phone_hash(phone)
        stmt = select(User).where(
            User.phone_hash == hash_value,
            User.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # 4. 新用户自动创建
        is_new_user = False
        if user is None:
            user = User(
                phone=phone,
                phone_hash=hash_value,
                is_minor=False,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            is_new_user = True
            logger.info("新用户注册: user_id=%s", user.id)

        # 5. 签发 JWT Token
        profile_completed = user.nickname is not None and user.age_range is not None
        access_token, refresh_token = self._create_tokens(user)

        return VerifyCodeResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            is_new_user=is_new_user,
            profile_completed=profile_completed,
        )

    # -----------------------------------------------------------------------
    # 完善资料
    # -----------------------------------------------------------------------

    async def complete_profile(
        self,
        user: User,
        request: CompleteProfileRequest,
        db: AsyncSession,
    ) -> VerifyCodeResponse:
        """完善用户资料（昵称 + 年龄段）。

        流程：
        1. 合并用户对象到当前会话（避免跨会话冲突）
        2. 更新昵称和年龄段
        3. 18 岁以下自动标记 is_minor=True
        4. 重新签发 Token（载荷包含 is_minor/age_range）

        Args:
            user: 当前用户（可能来自不同会话）
            request: 完善资料请求
            db: 数据库会话

        Returns:
            VerifyCodeResponse: 新的 Token 信息
        """
        # 合并用户对象到当前会话，避免跨会话冲突
        # 当 user 对象来自其他会话（如认证中间件的会话）时，
        # 需要将其合并到当前会话才能进行操作
        user = await db.merge(user)

        user.nickname = request.nickname
        user.age_range = request.age_range

        # 18 岁以下自动标记为未成年人
        if request.age_range == "18岁以下":
            user.is_minor = True
            logger.info("用户标记为未成年人: user_id=%s", user.id)

        await db.commit()
        await db.refresh(user)

        # 重新签发 Token（is_minor 可能变化）
        access_token, refresh_token = self._create_tokens(user)

        return VerifyCodeResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            is_new_user=False,
            profile_completed=True,
        )

    # -----------------------------------------------------------------------
    # Token 刷新
    # -----------------------------------------------------------------------

    async def refresh_token(self, request: RefreshTokenRequest) -> VerifyCodeResponse:
        """刷新 JWT Token。

        流程：
        1. 解码 refresh_token
        2. 校验 token 类型和有效期
        3. 签发新的 token 对

        Args:
            request: 刷新令牌请求

        Returns:
            VerifyCodeResponse: 新的 Token 信息

        Raises:
            AppError: Token 无效或过期时抛出
        """
        payload = self._decode_token(request.refresh_token)

        if payload.get("type") != "refresh":
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="无效的刷新令牌",
                status_code=401,
            )

        user_id = payload.get("sub")
        is_minor = payload.get("is_minor", False)
        age_range = payload.get("age_range")

        # 签发新的 token 对
        access_token = self._create_access_token(
            user_id=user_id,
            is_minor=is_minor,
            age_range=age_range,
        )
        refresh_token = self._create_refresh_token(
            user_id=user_id,
            is_minor=is_minor,
            age_range=age_range,
        )

        return VerifyCodeResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            is_new_user=False,
            profile_completed=age_range is not None,
        )

    # -----------------------------------------------------------------------
    # 登出
    # -----------------------------------------------------------------------

    async def logout(self, user_id: str, access_token: str) -> None:
        """用户登出。

        将当前 access_token 加入黑名单，使其在剩余有效期内无法使用。

        Args:
            user_id: 用户ID
            access_token: 当前访问令牌
        """
        try:
            payload = jwt.decode(access_token, self._jwt_secret, algorithms=[JWT_ALGORITHM])
            exp = payload.get("exp", 0)
            now = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - now)
            if ttl > 0:
                # 将 token 加入黑名单，TTL 为 token 剩余有效期
                blacklist_key = f"token:blacklist:{access_token}"
                await self._redis.setex(blacklist_key, ttl, user_id)
                logger.info("用户登出: user_id=%s", user_id)
        except JWTError:
            # Token 已无效，无需加入黑名单
            pass

    # -----------------------------------------------------------------------
    # 获取当前用户信息
    # -----------------------------------------------------------------------

    async def get_current_user_info(self, user: User) -> CurrentUserResponse:
        """获取当前用户信息。

        Args:
            user: 当前用户 ORM 对象

        Returns:
            CurrentUserResponse: 用户信息
        """
        # 解密手机号并脱敏
        try:
            decrypted_phone = decrypt_phone(user.phone)
            # 脱敏：保留前 3 位和后 4 位
            masked_phone = f"{decrypted_phone[:3]}****{decrypted_phone[-4:]}"
        except ValueError:
            masked_phone = "****"

        profile_completed = user.nickname is not None and user.age_range is not None

        return CurrentUserResponse(
            id=user.id,
            phone=masked_phone,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            age_range=user.age_range,
            is_minor=user.is_minor,
            profile_completed=profile_completed,
            created_at=user.created_at,
        )

    # -----------------------------------------------------------------------
    # 青少年模式检查
    # -----------------------------------------------------------------------

    @staticmethod
    def check_minor_access(user: User, scene: str) -> None:
        """检查青少年用户是否有权限访问指定场景。

        受限场景：
        - treehole: 树洞内容
        - ai_sensitive: AI 对话敏感话题
        - chat_image: 私聊图片

        Args:
            user: 当前用户
            scene: 场景标识

        Raises:
            AppError: 青少年用户访问受限场景时抛出 USER_UNDERAGE
        """
        if not user.is_minor:
            return

        restricted_scenes = {"treehole", "ai_sensitive", "chat_image"}
        if scene in restricted_scenes:
            raise AppError(
                code=ErrorCode.USER_UNDERAGE,
                message="青少年模式下无法访问此内容",
                status_code=403,
            )

    # -----------------------------------------------------------------------
    # Token 签发与解析（内部方法）
    # -----------------------------------------------------------------------

    def _create_tokens(self, user: User) -> tuple[str, str]:
        """为用户创建 access_token 和 refresh_token 对。"""
        access_token = self._create_access_token(
            user_id=user.id,
            is_minor=user.is_minor,
            age_range=user.age_range,
        )
        refresh_token = self._create_refresh_token(
            user_id=user.id,
            is_minor=user.is_minor,
            age_range=user.age_range,
        )
        return access_token, refresh_token

    def _create_access_token(
        self,
        user_id: str,
        is_minor: bool,
        age_range: str | None,
    ) -> str:
        """签发 access_token（15 分钟有效）。"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "is_minor": is_minor,
            "age_range": age_range,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": uuid4().hex,  # JWT ID，用于黑名单
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=JWT_ALGORITHM)

    def _create_refresh_token(
        self,
        user_id: str,
        is_minor: bool,
        age_range: str | None,
    ) -> str:
        """签发 refresh_token（7 天有效）。"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "is_minor": is_minor,
            "age_range": age_range,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": uuid4().hex,
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=JWT_ALGORITHM)

    def _decode_token(self, token: str) -> dict[str, Any]:
        """解码并验证 JWT Token。

        Args:
            token: JWT Token 字符串

        Returns:
            Token 载荷字典

        Raises:
            AppError: Token 过期或无效时抛出
        """
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise AppError(
                code=ErrorCode.TOKEN_EXPIRED,
                message="登录已过期，请重新登录",
                status_code=401,
            )
        except JWTError as exc:
            logger.warning("JWT 解码失败: %s", exc)
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="无效的登录凭证",
                status_code=401,
            )

    # -----------------------------------------------------------------------
    # 速率限制（内部方法）
    # -----------------------------------------------------------------------

    async def _check_login_rate_limit(self, phone: str) -> None:
        """检查登录速率限制（5 次/15 分钟）。

        Args:
            phone: 手机号

        Raises:
            AppError: 超出速率限制时抛出
        """
        rate_key = _rate_limit_login_key(phone)
        count = await self._redis.get(rate_key)
        if count is not None:
            count_val = int(count) if isinstance(count, (int, bytes, str)) else 0
            if isinstance(count, bytes):
                count_val = int(count.decode("utf-8"))
            elif isinstance(count, str):
                count_val = int(count)
            if count_val >= 5:
                ttl = await self._redis.ttl(rate_key)
                raise AppError(
                    code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    message=f"登录尝试次数过多，请 {ttl} 秒后重试",
                    status_code=429,
                )

    async def _increment_login_rate_limit(self, phone: str) -> None:
        """增加登录失败计数。"""
        rate_key = _rate_limit_login_key(phone)
        count = await self._redis.incr(rate_key)
        if count == 1:
            # 首次失败，设置 15 分钟过期
            await self._redis.expire(rate_key, 15 * 60)

    # -----------------------------------------------------------------------
    # Token 黑名单检查
    # -----------------------------------------------------------------------

    async def is_token_blacklisted(self, token: str) -> bool:
        """检查 Token 是否在黑名单中（用于登出后使 Token 失效）。"""
        blacklist_key = f"token:blacklist:{token}"
        return await self._redis.exists(blacklist_key) > 0

    # -----------------------------------------------------------------------
    # 解码 access_token 获取载荷（供中间件使用）
    # -----------------------------------------------------------------------

    async def verify_access_token(self, token: str) -> dict[str, Any]:
        """验证 access_token 有效性。

        流程：
        1. 解码 Token
        2. 检查 Token 类型是否为 access
        3. 检查 Token 是否在黑名单中

        Args:
            token: access_token 字符串

        Returns:
            Token 载荷字典

        Raises:
            AppError: Token 无效、过期或已登出时抛出
        """
        payload = self._decode_token(token)

        if payload.get("type") != "access":
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="无效的访问令牌",
                status_code=401,
            )

        # 检查黑名单
        if await self.is_token_blacklisted(token):
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="登录凭证已失效，请重新登录",
                status_code=401,
            )

        return payload
