"""管理员认证中间件。

提供管理员 JWT Token 校验和身份注入能力：
- get_current_admin: 依赖注入，从 Token 中获取当前管理员 ORM 对象
- get_current_admin_payload: 依赖注入，仅验证 Token 返回载荷（不查询数据库）
- require_permission: 权限校验装饰器

安全说明：
- get_client_ip 函数实现了可信代理验证，防止 IP 伪造攻击
- 生产环境必须配置 TRUSTED_PROXY_IPS 环境变量
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.admin import Admin
from app.schemas.admin import ROLE_PERMISSIONS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Authorization Header 提取
# ---------------------------------------------------------------------------

async def _get_admin_authorization_token(
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
            message="请先登录管理后台",
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
# 获取服务实例
# ---------------------------------------------------------------------------

async def _get_admin_auth_service(request: Request) -> Any:
    """从应用状态获取管理员认证服务实例。"""
    return request.app.state.admin_auth_service


async def _get_db_session(request: Request) -> AsyncSession:
    """从应用状态获取数据库会话。"""
    async_session_factory = request.app.state.async_session_factory
    async with async_session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Token 验证与管理员加载
# ---------------------------------------------------------------------------

async def get_current_admin_payload(
    request: Request,
    token: str = Depends(_get_admin_authorization_token),
    auth_service: Any = Depends(_get_admin_auth_service),
) -> dict[str, Any]:
    """验证 Token 并返回载荷（不查询数据库）。

    适用于只需要验证身份但不需要管理员详细信息的场景。

    Args:
        request: FastAPI 请求对象
        token: JWT Token
        auth_service: 管理员认证服务

    Returns:
        Token 载荷字典

    Raises:
        AppError: Token 无效时抛出
    """
    payload = await auth_service.verify_access_token(token)
    return payload


async def get_current_admin(
    request: Request,
    token: str = Depends(_get_admin_authorization_token),
    auth_service: Any = Depends(_get_admin_auth_service),
    db: AsyncSession = Depends(_get_db_session),
) -> Admin:
    """验证 Token 并返回管理员 ORM 对象。

    适用于需要操作管理员数据的场景。

    Args:
        request: FastAPI 请求对象
        token: JWT Token
        auth_service: 管理员认证服务
        db: 数据库会话

    Returns:
        Admin ORM 对象

    Raises:
        AppError: Token 无效或管理员不存在时抛出
    """
    # 验证 Token
    payload = await auth_service.verify_access_token(token)
    admin_id = payload.get("sub")

    # 查询管理员
    stmt = select(Admin).where(
        Admin.id == admin_id,
        Admin.is_active == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if admin is None:
        raise AppError(
            code=ErrorCode.ADMIN_AUTH_FAILED,
            message="管理员不存在或已被禁用",
            status_code=404,
        )

    # 将 token 存储在 request.state 中，便于后续登出使用
    request.state.admin_access_token = token

    return admin


# ---------------------------------------------------------------------------
# 权限校验装饰器
# ---------------------------------------------------------------------------

def require_permission(permission: str):
    """权限校验依赖注入装饰器。

    校验当前管理员是否拥有指定权限节点。

    Args:
        permission: 权限节点，如 "user:ban", "report:process"

    Returns:
        Depends 包装的权限检查函数

    Raises:
        AppError: 权限不足时抛出
    """

    async def check_permission(
        admin: Admin = Depends(get_current_admin),
    ) -> Admin:
        """检查管理员权限。"""
        # 获取角色权限列表
        role_permissions = ROLE_PERMISSIONS.get(admin.role, [])

        if permission not in role_permissions:
            raise AppError(
                code=ErrorCode.ADMIN_PERMISSION_DENIED,
                message=f"您没有 '{permission}' 权限，请联系管理员",
                status_code=403,
            )

        return admin

    return Depends(check_permission)


def require_role(role: str | list[str]):
    """角色校验依赖注入装饰器。

    校验当前管理员是否拥有指定角色。

    Args:
        role: 角色名称或角色列表，如 "super_admin" 或 ["super_admin", "admin"]

    Returns:
        Depends 包装的角色检查函数

    Raises:
        AppError: 角色不匹配时抛出
    """
    allowed_roles = [role] if isinstance(role, str) else role

    async def check_role(
        admin: Admin = Depends(get_current_admin),
    ) -> Admin:
        """检查管理员角色。"""
        if admin.role not in allowed_roles:
            raise AppError(
                code=ErrorCode.ADMIN_PERMISSION_DENIED,
                message=f"此操作需要特定角色权限",
                status_code=403,
            )

        return admin

    return Depends(check_role)


# ---------------------------------------------------------------------------
# 可信代理配置（防止 IP 伪造攻击）
# ---------------------------------------------------------------------------

import os

# 从环境变量读取可信代理 IP 列表
# 格式：逗号分隔的 IP 地址或 CIDR，例如 "10.0.0.1,10.0.0.2,192.168.1.0/24"
_TRUSTED_PROXY_IPS_ENV = "TRUSTED_PROXY_IPS"
_TRUSTED_PROXY_IPS: set[str] | None = None
_TRUSTED_PROXY_CIDRS: list[str] = []


def _load_trusted_proxies() -> tuple[set[str], list[str]]:
    """加载可信代理 IP 配置。

    Returns:
        (可信 IP 集合, CIDR 列表)

    Raises:
        RuntimeError: 生产环境未配置可信代理时抛出
    """
    from app.core.config import _environment_name

    env_value = os.getenv(_TRUSTED_PROXY_IPS_ENV, "")
    env = _environment_name()

    if not env_value:
        if env == "production":
            raise RuntimeError(
                "生产环境必须配置 TRUSTED_PROXY_IPS 环境变量！"
                "请配置负载均衡器/反向代理的内网 IP 地址（逗号分隔）。"
                "示例：TRUSTED_PROXY_IPS=10.0.0.1,10.0.0.2,192.168.1.0/24"
            )
        # 开发/测试环境允许不配置，直接信任 X-Forwarded-For
        logger.warning(
            "未配置 TRUSTED_PROXY_IPS，将直接信任 X-Forwarded-For 头。"
            "生产环境务必配置可信代理 IP 列表，防止 IP 伪造攻击！"
        )
        return set(), []

    # 解析配置
    ips: set[str] = set()
    cidrs: list[str] = []

    for item in env_value.split(","):
        item = item.strip()
        if not item:
            continue
        if "/" in item:
            # CIDR 格式
            cidrs.append(item)
        else:
            # 单个 IP
            ips.add(item)

    logger.info("已加载可信代理配置: IPs=%s, CIDRs=%s", ips, cidrs)
    return ips, cidrs


def _is_trusted_proxy(ip: str) -> bool:
    """检查 IP 是否为可信代理。

    Args:
        ip: 代理 IP 地址

    Returns:
        True 如果是可信代理
    """
    global _TRUSTED_PROXY_IPS, _TRUSTED_PROXY_CIDRS

    # 延迟加载配置
    if _TRUSTED_PROXY_IPS is None:
        _TRUSTED_PROXY_IPS, _TRUSTED_PROXY_CIDRS = _load_trusted_proxies()

    # 检查是否在可信 IP 集合中
    if ip in _TRUSTED_PROXY_IPS:
        return True

    # 检查是否在可信 CIDR 范围内
    for cidr in _TRUSTED_PROXY_CIDRS:
        try:
            import ipaddress
            network = ipaddress.ip_network(cidr, strict=False)
            addr = ipaddress.ip_address(ip)
            if addr in network:
                return True
        except ValueError:
            logger.warning("无效的 CIDR 配置: %s", cidr)
            continue

    return False


# ---------------------------------------------------------------------------
# 客户端信息提取
# ---------------------------------------------------------------------------

async def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP 地址。

    实现可信代理验证，防止 IP 伪造攻击：
    1. 检查请求是否来自可信代理（通过 TRUSTED_PROXY_IPS 配置）
    2. 如果来自可信代理，从 X-Forwarded-For 中提取真实客户端 IP
    3. 如果不是可信代理，直接使用连接 IP（防止伪造）

    Args:
        request: FastAPI 请求对象

    Returns:
        客户端 IP 地址

    Raises:
        RuntimeError: 生产环境未配置可信代理时抛出（在 _is_trusted_proxy 中）
    """
    # 获取直接连接的 IP（可能是代理或客户端）
    direct_ip = request.client.host if request.client else None

    if direct_ip is None:
        return "unknown"

    # 检查直接连接方是否为可信代理
    if _is_trusted_proxy(direct_ip):
        # 来自可信代理，从 X-Forwarded-For 提取真实客户端 IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 格式: client, proxy1, proxy2
            # 从右向左遍历，找到第一个不可信的 IP 即为真实客户端
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            for ip in reversed(ips):
                if not _is_trusted_proxy(ip):
                    return ip
            # 所有 IP 都是可信代理，取最左边的（原始客户端）
            return ips[0] if ips else direct_ip

        # 尝试 X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    # 不是可信代理，直接使用连接 IP（防止伪造）
    # 任何 X-Forwarded-For 头都不可信，可能是攻击者伪造
    return direct_ip


async def get_user_agent(request: Request) -> str:
    """获取客户端 User-Agent。

    Args:
        request: FastAPI 请求对象

    Returns:
        User-Agent 字符串
    """
    return request.headers.get("User-Agent", "unknown")


# ---------------------------------------------------------------------------
# 类型别名，方便使用
# ---------------------------------------------------------------------------

# 当前管理员载荷（不含数据库查询）
CurrentAdminPayload = Annotated[dict[str, Any], Depends(get_current_admin_payload)]

# 当前管理员（ORM 对象）
CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]

# 客户端 IP
ClientIP = Annotated[str, Depends(get_client_ip)]

# User-Agent
UserAgent = Annotated[str, Depends(get_user_agent)]