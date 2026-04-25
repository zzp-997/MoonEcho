"""JWT 认证中间件。

提供 JWT Token 校验和用户身份注入能力：
- get_current_user: 依赖注入，从 Token 中获取当前用户 ORM 对象
- get_current_user_payload: 依赖注入，仅验证 Token 返回载荷（不查询数据库）
- require_adult: 依赖注入，校验用户是否成年
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Authorization Header 提取
# ---------------------------------------------------------------------------

async def _get_authorization_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    """从 Authorization header 中提取 Bearer Token。

    Args:
        authorization: Authorization header 值

    Returns:
        Token 字符串

    Raises:
        AppError: Token 缺失或格式错误时抛出
    """
    if authorization is None:
        raise AppError(
            code=ErrorCode.TOKEN_MISSING,
            message="请先登录",
            status_code=401,
        )

    # 检查 Bearer 前缀
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AppError(
            code=ErrorCode.TOKEN_INVALID,
            message="无效的认证方式",
            status_code=401,
        )

    return parts[1]


# ---------------------------------------------------------------------------
# Token 验证与用户加载
# ---------------------------------------------------------------------------

async def _get_auth_service(request: Request) -> Any:
    """从应用状态获取认证服务实例。"""
    # auth_service 在 startup 事件中挂载
    return request.app.state.auth_service


async def _get_db_session(request: Request) -> AsyncSession:
    """从应用状态获取数据库会话。"""
    # 使用 request.app.state.db_pool 获取连接池
    # 或者通过依赖注入系统
    async_session_factory = request.app.state.async_session_factory
    async with async_session_factory() as session:
        yield session


async def get_current_user_payload(
    request: Request,
    token: str = Depends(_get_authorization_token),
    auth_service: Any = Depends(_get_auth_service),
) -> dict[str, Any]:
    """验证 Token 并返回载荷（不查询数据库）。

    适用于只需要验证身份但不需要用户详细信息的场景。

    Args:
        request: FastAPI 请求对象
        token: JWT Token
        auth_service: 认证服务

    Returns:
        Token 载荷字典

    Raises:
        AppError: Token 无效时抛出
    """
    payload = await auth_service.verify_access_token(token)
    return payload


async def get_current_user(
    request: Request,
    token: str = Depends(_get_authorization_token),
    auth_service: Any = Depends(_get_auth_service),
    db: AsyncSession = Depends(_get_db_session),
) -> User:
    """验证 Token 并返回用户 ORM 对象。

    适用于需要操作用户数据的场景。

    Args:
        request: FastAPI 请求对象
        token: JWT Token
        auth_service: 认证服务
        db: 数据库会话

    Returns:
        User ORM 对象

    Raises:
        AppError: Token 无效或用户不存在时抛出
    """
    # 验证 Token
    payload = await auth_service.verify_access_token(token)
    user_id = payload.get("sub")

    # 查询用户
    stmt = select(User).where(
        User.id == user_id,
        User.is_active == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AppError(
            code=ErrorCode.USER_NOT_FOUND,
            message="用户不存在",
            status_code=404,
        )

    # 将 token 存储在 request.state 中，便于后续登出使用
    request.state.access_token = token

    return user


async def get_current_user_optional(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_service: Any = Depends(_get_auth_service),
    db: AsyncSession = Depends(_get_db_session),
) -> User | None:
    """可选的用户身份验证。

    若提供了有效的 Token，返回用户对象；否则返回 None。
    适用于既支持登录用户也支持匿名访问的接口。

    Args:
        request: FastAPI 请求对象
        authorization: Authorization header
        auth_service: 认证服务
        db: 数据库会话

    Returns:
        User ORM 对象或 None
    """
    if authorization is None:
        return None

    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        token = parts[1]

        payload = await auth_service.verify_access_token(token)
        user_id = payload.get("sub")

        stmt = select(User).where(
            User.id == user_id,
            User.is_active == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            request.state.access_token = token
        return user
    except AppError:
        return None


async def require_adult(
    user: User = Depends(get_current_user),
) -> User:
    """验证用户是否成年。

    Args:
        user: 当前用户

    Returns:
        User ORM 对象

    Raises:
        AppError: 用户为未成年人时抛出 USER_UNDERAGE
    """
    if user.is_minor:
        raise AppError(
            code=ErrorCode.USER_UNDERAGE,
            message="青少年模式下无法访问此功能",
            status_code=403,
        )
    return user


# ---------------------------------------------------------------------------
# 类型别名，方便使用
# ---------------------------------------------------------------------------

# 当前用户载荷（不含数据库查询）
CurrentUserPayload = Annotated[dict[str, Any], Depends(get_current_user_payload)]

# 当前用户（ORM 对象）
CurrentUser = Annotated[User, Depends(get_current_user)]

# 可选用户（ORM 对象或 None）
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]

# 成年用户（已验证非未成年人）
AdultUser = Annotated[User, Depends(require_adult)]
