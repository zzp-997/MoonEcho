"""管理员认证服务模块。

核心业务逻辑层，封装以下能力：
- 管理员登录验证（bcrypt 密码校验）
- JWT Token 签发与刷新（独立 secret/issuer，与 C 端用户隔离）
- 登录失败锁定（Redis 计数，5 次/30 分钟锁定）
- 操作审计日志记录
- 权限检查（基于角色的 RBAC）
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings
from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.admin import Admin, AdminLog
from app.schemas.admin import (
    ADMIN_ROLES,
    ROLE_PERMISSIONS,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminRefreshTokenRequest,
    AdminRefreshTokenResponse,
    CurrentAdminResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
)
from app.services.admin.admin_log_service import AdminLogService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

def _admin_lock_key(username: str) -> str:
    """管理员登录锁定 key。"""
    return f"admin:lock:{username}"


def _admin_token_jti_blacklist_key(jti: str) -> str:
    """管理员 Token 黑名单 key（基于 jti）。"""
    return f"admin:token:blacklist:{jti}"


# ---------------------------------------------------------------------------
# JWT 配置常量（管理后台独立配置）
# ---------------------------------------------------------------------------

JWT_ALGORITHM = "HS256"
ADMIN_ACCESS_TOKEN_EXPIRE_HOURS = 2  # 管理后台 access_token 有效期 2 小时
ADMIN_REFRESH_TOKEN_EXPIRE_DAYS = 7  # 管理后台 refresh_token 有效期 7 天
ADMIN_JWT_ISSUER = "echo-admin"  # 管理后台 JWT issuer
ADMIN_JWT_AUDIENCE = "echo-admin-api"  # 管理后台 JWT audience

# 登录失败锁定配置
MAX_LOGIN_ATTEMPTS = 5  # 最大尝试次数
LOCK_DURATION_MINUTES = 30  # 锁定时长（分钟）


class AdminAuthService:
    """管理员认证服务，封装所有管理后台认证相关业务逻辑。

    依赖外部注入：
    - settings: 应用配置
    - redis: Redis 客户端（aioredis）
    """

    def __init__(
        self,
        settings: AppSettings,
        redis: Any,
    ) -> None:
        self._settings = settings
        self._redis = redis
        self._jwt_secret = self._load_admin_jwt_secret()
        self._log_service = AdminLogService(redis)

    # -----------------------------------------------------------------------
    # JWT 密钥（管理后台独立）
    # -----------------------------------------------------------------------

    @staticmethod
    def _load_admin_jwt_secret() -> str:
        """从环境变量加载管理后台专用 JWT 密钥。"""
        secret = os.getenv("ADMIN_JWT_SECRET_KEY")
        if not secret:
            logger.warning(
                "未配置 ADMIN_JWT_SECRET_KEY 环境变量，使用默认密钥。"
                "生产环境务必配置独立的密钥！"
            )
            # 使用默认开发密钥（仅限开发环境）
            secret = "echo-admin-jwt-secret-key-dev-only-2024"
            # 生产环境检查：如果设置了 ENVIRONMENT=production，则拒绝启动
            env = os.getenv("ENVIRONMENT", "development")
            if env.lower() in ("production", "prod"):
                raise RuntimeError(
                    "生产环境必须配置 ADMIN_JWT_SECRET_KEY 环境变量！"
                )
        return secret

    # -----------------------------------------------------------------------
    # 管理员登录
    # -----------------------------------------------------------------------

    async def login(
        self,
        request: AdminLoginRequest,
        db: AsyncSession,
        ip_address: str,
        user_agent: str,
    ) -> AdminLoginResponse:
        """管理员登录。

        流程：
        1. 检查账户是否被锁定
        2. 验证用户名和密码
        3. 检查账户是否启用
        4. 记录登录成功日志
        5. 更新最后登录信息
        6. 签发 JWT Token

        Args:
            request: 登录请求
            db: 数据库会话
            ip_address: 客户端IP
            user_agent: 客户端UA

        Returns:
            AdminLoginResponse: 登录结果（含 Token）

        Raises:
            AppError: 账户锁定、认证失败、账户禁用时抛出
        """
        username = request.username

        # 1. 检查账户是否被锁定
        lock_key = _admin_lock_key(username)
        lock_ttl = await self._redis.ttl(lock_key)
        if lock_ttl and lock_ttl > 0:
            raise AppError(
                code=ErrorCode.ADMIN_ACCOUNT_LOCKED,
                message=f"账户已被锁定，请在 {lock_ttl // 60} 分钟后重试",
                status_code=403,
            )

        # 2. 查询管理员
        stmt = select(Admin).where(Admin.username == username)
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        # 3. 验证密码
        if admin is None or not self._verify_password(request.password, admin.password_hash):
            # 记录登录失败
            await self._record_login_failure(username)
            await self._log_service.log_action(
                admin_id=None,
                action="login_failed",
                target_type="admin",
                target_id=None,
                details={"username": username, "reason": "invalid_credentials"},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AppError(
                code=ErrorCode.ADMIN_AUTH_FAILED,
                message="用户名或密码错误",
                status_code=401,
            )

        # 4. 检查账户是否启用
        if not admin.is_active:
            await self._log_service.log_action(
                admin_id=admin.id,
                action="login_failed",
                target_type="admin",
                target_id=admin.id,
                details={"reason": "account_disabled"},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AppError(
                code=ErrorCode.ADMIN_ACCOUNT_LOCKED,
                message="账户已被禁用，请联系超级管理员",
                status_code=403,
            )

        # 5. 清除登录失败记录
        await self._redis.delete(lock_key)

        # 6. 更新最后登录信息
        admin.last_login_at = datetime.now(timezone.utc)
        admin.last_login_ip = ip_address
        await db.commit()

        # 7. 获取权限列表
        permissions = self._get_permissions(admin.role)

        # 8. 签发 JWT Token
        access_token, refresh_token = self._create_tokens(admin)

        # 9. 记录登录成功日志
        await self._log_service.log_action(
            admin_id=admin.id,
            action="login",
            target_type="admin",
            target_id=admin.id,
            details={"role": admin.role},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info("管理员登录成功: username=%s, role=%s", username, admin.role)

        return AdminLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ADMIN_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            admin_id=admin.id,
            username=admin.username,
            nickname=admin.nickname,
            role=admin.role,
            permissions=permissions,
        )

    # -----------------------------------------------------------------------
    # Token 刷新
    # -----------------------------------------------------------------------

    async def refresh_token(
        self,
        request: AdminRefreshTokenRequest,
    ) -> AdminRefreshTokenResponse:
        """刷新管理员 JWT Token。

        Args:
            request: 刷新令牌请求

        Returns:
            AdminRefreshTokenResponse: 新的 Token 对

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

        # 验证 issuer
        if payload.get("iss") != ADMIN_JWT_ISSUER:
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="无效的令牌签发者",
                status_code=401,
            )

        admin_id = payload.get("sub")
        role = payload.get("role")
        jti = payload.get("jti")

        # 检查 Token 是否在黑名单中
        if jti and await self._is_token_blacklisted(jti):
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="令牌已失效，请重新登录",
                status_code=401,
            )

        # 签发新的 token 对
        access_token = self._create_access_token(
            admin_id=admin_id,
            role=role,
        )
        refresh_token = self._create_refresh_token(
            admin_id=admin_id,
            role=role,
        )

        # 将旧的 refresh_token 的 jti 加入黑名单
        if jti:
            await self._add_token_to_blacklist(jti, days=ADMIN_REFRESH_TOKEN_EXPIRE_DAYS)

        return AdminRefreshTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ADMIN_ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        )

    # -----------------------------------------------------------------------
    # 登出
    # -----------------------------------------------------------------------

    async def logout(
        self,
        admin_id: str,
        access_token: str,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """管理员登出。

        将当前 access_token 的 jti 加入黑名单，使其在剩余有效期内无法使用。

        Args:
            admin_id: 管理员ID
            access_token: 当前访问令牌
            ip_address: 客户端IP
            user_agent: 客户端UA
        """
        try:
            payload = self._decode_token(access_token)
            exp = payload.get("exp", 0)
            jti = payload.get("jti")
            now = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - now)
            if ttl > 0 and jti:
                # 将 access_token 的 jti 加入黑名单
                await self._add_token_to_blacklist(jti, seconds=ttl)

            # 记录登出日志
            await self._log_service.log_action(
                admin_id=admin_id,
                action="logout",
                target_type="admin",
                target_id=admin_id,
                details=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            logger.info("管理员登出: admin_id=%s", admin_id)
        except JWTError:
            # Token 已无效，无需加入黑名单
            pass

    # -----------------------------------------------------------------------
    # 获取当前管理员信息
    # -----------------------------------------------------------------------

    async def get_current_admin_info(
        self,
        admin: Admin,
    ) -> CurrentAdminResponse:
        """获取当前管理员信息。

        Args:
            admin: 当前管理员 ORM 对象

        Returns:
            CurrentAdminResponse: 管理员信息
        """
        permissions = self._get_permissions(admin.role)

        return CurrentAdminResponse(
            id=admin.id,
            username=admin.username,
            nickname=admin.nickname,
            role=admin.role,
            permissions=permissions,
            last_login_at=admin.last_login_at,
            last_login_ip=admin.last_login_ip,
            created_at=admin.created_at,
        )

    # -----------------------------------------------------------------------
    # 权限检查
    # -----------------------------------------------------------------------

    async def check_permission(
        self,
        admin: Admin,
        request: PermissionCheckRequest,
    ) -> PermissionCheckResponse:
        """检查管理员是否拥有指定权限。

        Args:
            admin: 当前管理员
            request: 权限检查请求

        Returns:
            PermissionCheckResponse: 权限检查结果
        """
        permissions = self._get_permissions(admin.role)
        has_permission = request.permission in permissions

        return PermissionCheckResponse(
            has_permission=has_permission,
            permission=request.permission,
            role=admin.role,
        )

    # -----------------------------------------------------------------------
    # 验证 access_token（供中间件使用）
    # -----------------------------------------------------------------------

    async def verify_access_token(self, token: str) -> dict[str, Any]:
        """验证管理员 access_token 有效性。

        流程：
        1. 解码 Token
        2. 验证 Token 类型和 issuer
        3. 检查黑名单（基于 jti）

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

        if payload.get("iss") != ADMIN_JWT_ISSUER:
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="无效的令牌签发者",
                status_code=401,
            )

        # 检查黑名单（基于 jti）
        jti = payload.get("jti")
        if jti and await self._is_token_blacklisted(jti):
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="登录凭证已失效，请重新登录",
                status_code=401,
            )

        return payload

    # -----------------------------------------------------------------------
    # 检查管理员是否拥有指定权限
    # -----------------------------------------------------------------------

    def has_permission(self, role: str, permission: str) -> bool:
        """检查角色是否拥有指定权限。

        Args:
            role: 角色名称
            permission: 权限节点

        Returns:
            是否拥有该权限
        """
        permissions = self._get_permissions(role)
        return permission in permissions

    # -----------------------------------------------------------------------
    # 内部方法：密码处理
    # -----------------------------------------------------------------------

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码是否正确。

        Args:
            plain_password: 明文密码
            hashed_password: bcrypt 哈希后的密码

        Returns:
            密码是否匹配
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password,
            )
        except Exception:
            return False

    @staticmethod
    def hash_password(password: str, rounds: int = 12) -> str:
        """使用 bcrypt 对密码进行哈希。

        Args:
            password: 明文密码
            rounds: bcrypt cost factor，默认 12（约 250ms）
                    建议范围：10-12，值越大越安全但越慢

        Returns:
            哈希后的密码字符串
        """
        salt = bcrypt.gensalt(rounds=rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    # -----------------------------------------------------------------------
    # 内部方法：Token 签发
    # -----------------------------------------------------------------------

    def _create_tokens(self, admin: Admin) -> tuple[str, str]:
        """为管理员创建 access_token 和 refresh_token 对。"""
        access_token = self._create_access_token(
            admin_id=admin.id,
            role=admin.role,
        )
        refresh_token = self._create_refresh_token(
            admin_id=admin.id,
            role=admin.role,
        )
        return access_token, refresh_token

    def _create_access_token(
        self,
        admin_id: str,
        role: str,
    ) -> str:
        """签发 access_token（2 小时有效）。"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": admin_id,
            "role": role,
            "type": "access",
            "iss": ADMIN_JWT_ISSUER,
            "aud": ADMIN_JWT_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(hours=ADMIN_ACCESS_TOKEN_EXPIRE_HOURS),
            "jti": uuid4().hex,
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=JWT_ALGORITHM)

    def _create_refresh_token(
        self,
        admin_id: str,
        role: str,
    ) -> str:
        """签发 refresh_token（7 天有效）。"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": admin_id,
            "role": role,
            "type": "refresh",
            "iss": ADMIN_JWT_ISSUER,
            "aud": ADMIN_JWT_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(days=ADMIN_REFRESH_TOKEN_EXPIRE_DAYS),
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
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[JWT_ALGORITHM],
                issuer=ADMIN_JWT_ISSUER,
                audience=ADMIN_JWT_AUDIENCE,
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AppError(
                code=ErrorCode.TOKEN_EXPIRED,
                message="登录已过期，请重新登录",
                status_code=401,
            )
        except JWTError as exc:
            logger.warning("管理员 JWT 解码失败: %s", exc)
            raise AppError(
                code=ErrorCode.TOKEN_INVALID,
                message="无效的登录凭证",
                status_code=401,
            )

    # -----------------------------------------------------------------------
    # 内部方法：权限获取
    # -----------------------------------------------------------------------

    def _get_permissions(self, role: str) -> list[str]:
        """根据角色获取权限列表。

        Args:
            role: 角色名称

        Returns:
            权限节点列表
        """
        return ROLE_PERMISSIONS.get(role, [])

    # -----------------------------------------------------------------------
    # 内部方法：登录失败处理
    # -----------------------------------------------------------------------

    async def _record_login_failure(self, username: str) -> None:
        """记录登录失败，达到阈值后锁定账户。

        Args:
            username: 用户名
        """
        lock_key = _admin_lock_key(username)
        count = await self._redis.incr(lock_key)
        if count == 1:
            # 首次失败，设置过期时间
            await self._redis.expire(lock_key, LOCK_DURATION_MINUTES * 60)

        if count >= MAX_LOGIN_ATTEMPTS:
            logger.warning(
                "管理员账户已锁定: username=%s, attempts=%d",
                username,
                count,
            )

    # -----------------------------------------------------------------------
    # 内部方法：Token 黑名单
    # -----------------------------------------------------------------------

    async def _add_token_to_blacklist(
        self,
        jti: str,
        days: int = 0,
        seconds: int = 0,
    ) -> None:
        """将 Token 的 jti 加入黑名单。

        Args:
            jti: JWT Token 的唯一标识符
            days: 过期天数
            seconds: 过期秒数
        """
        blacklist_key = _admin_token_jti_blacklist_key(jti)
        ttl = days * 86400 + seconds
        if ttl > 0:
            await self._redis.setex(blacklist_key, ttl, "1")

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """检查 Token 的 jti 是否在黑名单中。

        Args:
            jti: JWT Token 的唯一标识符

        Returns:
            是否在黑名单中
        """
        blacklist_key = _admin_token_jti_blacklist_key(jti)
        result = await self._redis.exists(blacklist_key)
        # Redis exists 返回整数或 bool，统一转换为 bool
        return bool(result)
