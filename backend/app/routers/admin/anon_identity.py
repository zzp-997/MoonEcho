"""管理后台匿名身份反查路由（带二次认证）。

实现 PRD 7.5 要求：
- 管理后台查真实身份需二次认证
- 记录敏感审计日志
- 查询频率限制
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.middleware.admin_auth import Admin, require_permission
from app.models.user import AnonymousIdentity
from app.services.admin.admin_log_service import AdminLogService
from app.services.anonymous_identity import AnonymousIdentityService
from app.services.crypto import decrypt_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/anon-identity", tags=["管理后台-匿名身份"])


# ---------------------------------------------------------------------------
# 数据库会话依赖
# ---------------------------------------------------------------------------

async def _get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """从请求状态获取数据库会话。

    返回异步上下文管理器，确保会话自动关闭。
    """
    async_session_factory = request.app.state.async_session_factory
    async with async_session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------

class SecondaryAuthRequest(BaseModel):
    """二次认证请求。"""

    password: str = Field(..., min_length=6, description="管理员密码")
    otp_code: str | None = Field(None, description="动态验证码（可选）")


class AnonIdentityRevealResponse(BaseModel):
    """匿名身份反查响应。"""

    anon_id: str
    user_id: str
    anon_nickname: str
    persona_type: str | None
    created_at: datetime
    revealed_by: str
    revealed_at: datetime
    reveal_reason: str


# ---------------------------------------------------------------------------
# 二次认证依赖
# ---------------------------------------------------------------------------

# 每个管理员每小时最多查询次数
MAX_REVEAL_PER_HOUR = 5

# 二次认证令牌有效期（分钟）
SECONDARY_AUTH_TTL_MINUTES = 15


async def verify_secondary_auth(
    admin: Admin,
    request: Request,
    x_secondary_auth: str | None = Header(None, description="二次认证令牌"),
    db: AsyncSession = Depends(_get_db),
) -> bool:
    """验证二次认证。

    Args:
        admin: 当前管理员
        request: 请求对象
        x_secondary_auth: 二次认证令牌
        db: 数据库会话

    Returns:
        是否验证通过

    Raises:
        AppError: 二次认证失败
    """
    import hashlib
    import secrets
    import time

    if not x_secondary_auth:
        raise AppError(
            code=ErrorCode.SECONDARY_AUTH_REQUIRED,
            message="访问敏感数据需要二次认证，请输入密码或验证码",
            status_code=401,
        )

    # 解析令牌：格式为 "timestamp:hash"
    try:
        parts = x_secondary_auth.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid token format")

        timestamp = int(parts[0])
        token_hash = parts[1]
    except Exception:
        raise AppError(
            code=ErrorCode.TOKEN_INVALID,
            message="二次认证令牌格式无效",
            status_code=401,
        )

    # 检查令牌是否过期
    now = int(time.time())
    if now - timestamp > SECONDARY_AUTH_TTL_MINUTES * 60:
        raise AppError(
            code=ErrorCode.TOKEN_EXPIRED,
            message=f"二次认证令牌已过期，请重新认证",
            status_code=401,
        )

    # 验证令牌哈希（这里简化实现，实际应使用更安全的机制）
    settings = get_settings()
    expected_hash = hashlib.sha256(
        f"{admin.id}:{timestamp}:{settings.SECRET_KEY}".encode()
    ).hexdigest()[:32]

    if not secrets.compare_digest(token_hash, expected_hash):
        raise AppError(
            code=ErrorCode.TOKEN_INVALID,
            message="二次认证令牌无效",
            status_code=401,
        )

    return True


async def check_reveal_rate_limit(
    admin: Admin,
    redis: Any,
) -> None:
    """检查反查频率限制。

    Args:
        admin: 当前管理员
        redis: Redis 客户端

    Raises:
        AppError: 超过频率限制
    """
    key = f"anon_reveal:{admin.id}"
    count = await redis.get(key)

    if count and int(count) >= MAX_REVEAL_PER_HOUR:
        raise AppError(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"反查操作过于频繁，每小时最多 {MAX_REVEAL_PER_HOUR} 次",
            status_code=429,
        )

    # 增加计数，设置 1 小时过期
    await redis.incr(key)
    await redis.expire(key, 3600)


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/secondary-auth", summary="二次认证获取令牌")
async def get_secondary_auth_token(
    request: SecondaryAuthRequest,
    admin: Admin = require_permission("anon:reveal"),
    db: AsyncSession = Depends(_get_db),
) -> dict[str, Any]:
    """进行二次认证，获取临时令牌。

    管理员需要输入密码（或动态验证码）来获取访问敏感数据的临时令牌。

    Args:
        request: 认证请求
        admin: 当前管理员
        db: 数据库会话

    Returns:
        包含临时令牌的响应
    """
    import hashlib
    import time
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # 验证密码
    if not pwd_context.verify(request.password, admin.hashed_password):
        # 记录失败尝试
        logger.warning(
            "[AdminAuth] 二次认证失败，管理员: %s，IP: %s",
            admin.id,
            admin.last_login_ip,
        )
        raise AppError(
            code=ErrorCode.PASSWORD_INCORRECT,
            message="密码错误",
            status_code=401,
        )

    # 生成临时令牌
    timestamp = int(time.time())
    settings = get_settings()
    token_hash = hashlib.sha256(
        f"{admin.id}:{timestamp}:{settings.SECRET_KEY}".encode()
    ).hexdigest()[:32]
    token = f"{timestamp}:{token_hash}"

    # 记录审计日志
    log_service = AdminLogService(db)
    await log_service.log_action(
        admin_id=admin.id,
        action="secondary_auth_success",
        target_type="system",
        details={"message": "二次认证成功"},
        ip_address=admin.last_login_ip,
    )

    logger.info(
        "[AdminAuth] 二次认证成功，管理员: %s",
        admin.id,
    )

    return {
        "token": token,
        "expires_in": SECONDARY_AUTH_TTL_MINUTES * 60,
        "message": "二次认证成功，令牌有效",
    }


@router.get(
    "/{anon_id}/reveal",
    summary="反查匿名身份真实用户",
    response_model=AnonIdentityRevealResponse,
)
async def reveal_anonymous_identity(
    anon_id: str,
    reason: str,
    request: Request,
    admin: Admin = require_permission("anon:reveal"),
    x_secondary_auth: str | None = Header(None, description="二次认证令牌"),
    db: AsyncSession = Depends(_get_db),
) -> AnonIdentityRevealResponse:
    """反查匿名身份对应的真实用户（需要二次认证）。

    安全设计：
    1. 需要管理员权限 anon:reveal
    2. 需要二次认证令牌
    3. 记录敏感审计日志
    4. 频率限制（每小时最多5次）

    Args:
        anon_id: 匿名身份ID
        reason: 反查原因（必须填写）
        request: 请求对象
        admin: 当前管理员
        x_secondary_auth: 二次认证令牌
        db: 数据库会话

    Returns:
        匿名身份反查结果
    """
    from app.core.redis import get_redis

    # 1. 验证二次认证
    await verify_secondary_auth(admin, request, x_secondary_auth, db)

    # 2. 检查频率限制
    redis = get_redis()
    await check_reveal_rate_limit(admin, redis)

    # 3. 查询匿名身份
    stmt = select(AnonymousIdentity).where(
        AnonymousIdentity.id == anon_id,
        AnonymousIdentity.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    anon_identity = result.scalar_one_or_none()

    if not anon_identity:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message="匿名身份不存在",
            status_code=404,
        )

    # 4. 解密用户ID
    try:
        user_id = decrypt_data(anon_identity.encrypted_user_id)
    except Exception as e:
        logger.error(
            "[AnonIdentity] 解密用户ID失败，匿名ID: %s，错误: %s",
            anon_id, str(e)
        )
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="解密用户ID失败",
            status_code=500,
        )

    # 5. 记录敏感审计日志
    log_service = AdminLogService(db)
    await log_service.log_sensitive_action(
        admin_id=admin.id,
        action="anon_identity_reveal",
        target_type="anonymous_identity",
        target_id=anon_id,
        reason=reason,
        ip_address=request.client.host if request.client else "unknown",
    )

    logger.warning(
        "[AnonIdentity] 敏感操作：反查匿名身份，管理员: %s，匿名ID: %s，原因: %s",
        admin.id, anon_id, reason,
    )

    # 6. 返回结果
    return AnonIdentityRevealResponse(
        anon_id=anon_id,
        user_id=user_id,
        anon_nickname=anon_identity.anon_nickname,
        persona_type=anon_identity.persona_type,
        created_at=anon_identity.created_at,
        revealed_by=admin.username,
        revealed_at=datetime.now(timezone.utc),
        reveal_reason=reason,
    )


@router.get("/{anon_id}/posts", summary="获取匿名身份发布的帖子")
async def get_anon_identity_posts(
    anon_id: str,
    page: int = 1,
    page_size: int = 20,
    admin: Admin = require_permission("content:view"),
    db: AsyncSession = Depends(_get_db),
) -> dict[str, Any]:
    """获取指定匿名身份发布的所有帖子（管理后台）。

    Args:
        anon_id: 匿名身份ID
        page: 页码
        page_size: 每页数量
        admin: 当前管理员
        db: 数据库会话

    Returns:
        帖子列表
    """
    from app.models.treehole import TreeholePost

    # 查询帖子（仅通过 anon_identity_id 关联）
    stmt = (
        select(TreeholePost)
        .where(TreeholePost.anon_identity_id == anon_id)
        .order_by(TreeholePost.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    posts = result.scalars().all()

    # 统计总数
    count_stmt = select(func.count()).select_from(TreeholePost).where(
        TreeholePost.anon_identity_id == anon_id,
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    return {
        "posts": [
            {
                "id": post.id,
                "content": post.content,
                "topic_tag": post.topic_tag,
                "resonance_count": post.resonance_count,
                "comment_count": post.comment_count,
                "status": post.status,
                "created_at": post.created_at,
            }
            for post in posts
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": page * page_size < total,
        },
    }
