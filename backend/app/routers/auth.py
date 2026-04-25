"""认证路由模块。

提供用户认证相关的 API 端点：
- POST /api/v1/auth/send-code        发送验证码
- POST /api/v1/auth/verify-code      验证码登录/注册
- POST /api/v1/auth/complete-profile 完善资料（昵称+年龄段）
- POST /api/v1/auth/refresh-token    刷新 Token
- DELETE /api/v1/auth/logout         登出
- GET  /api/v1/auth/me               获取当前用户信息
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.middleware.auth import CurrentUser
from app.models.user import User
from app.schemas.auth import (
    CompleteProfileRequest,
    RefreshTokenRequest,
    SendCodeRequest,
    VerifyCodeRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# 依赖注入：获取认证服务和数据库会话
# ---------------------------------------------------------------------------

def _get_auth_service(request: Request) -> Any:
    """从应用状态获取认证服务。"""
    return request.app.state.auth_service


def _get_db(request: Request) -> Any:
    """从请求状态获取数据库会话。"""
    # 数据库会话在中间件或依赖注入中创建
    # 此处通过 request.state 获取
    return request.state.db


# ---------------------------------------------------------------------------
# POST /api/v1/auth/send-code — 发送验证码
# ---------------------------------------------------------------------------

@router.post("/send-code", summary="发送验证码")
async def send_code(
    body: SendCodeRequest,
    request: Request,
    auth_service: Any = Depends(_get_auth_service),
) -> dict[str, Any]:
    """发送短信验证码。

    - 60 秒内同一手机号不能重复发送
    - 验证码有效期 5 分钟
    - 开发环境固定验证码 123456
    """
    request_id = getattr(request.state, "request_id", "")
    result = await auth_service.send_code(body.phone)
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/verify-code — 验证码登录/注册
# ---------------------------------------------------------------------------

@router.post("/verify-code", summary="验证码登录/注册")
async def verify_code(
    body: VerifyCodeRequest,
    request: Request,
    auth_service: Any = Depends(_get_auth_service),
) -> dict[str, Any]:
    """验证码登录或注册。

    - 验证码正确且用户已存在 → 登录，返回 Token
    - 验证码正确且用户不存在 → 自动注册，返回 Token（is_new_user=True）
    - 新用户需后续调用 complete-profile 完善资料
    - 登录失败 5 次/15 分钟后锁定
    """
    request_id = getattr(request.state, "request_id", "")
    db: AsyncSession = request.app.state.db_session()
    try:
        result = await auth_service.verify_code(body, db)
        return success_response(result, request_id)
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# POST /api/v1/auth/complete-profile — 完善资料
# ---------------------------------------------------------------------------

@router.post("/complete-profile", summary="完善资料")
async def complete_profile(
    body: CompleteProfileRequest,
    user: CurrentUser,
    request: Request,
    auth_service: Any = Depends(_get_auth_service),
) -> dict[str, Any]:
    """完善用户资料（昵称 + 年龄段）。

    - 年龄段选项：18岁以下/18-25/26-35/36-45/45以上
    - 18岁以下自动标记 is_minor=True（青少年模式）
    - 完善后重新签发 Token（载荷包含 is_minor/age_range）
    - 需要登录（Bearer Token）
    """
    request_id = getattr(request.state, "request_id", "")
    db: AsyncSession = request.app.state.db_session()
    try:
        result = await auth_service.complete_profile(user, body, db)
        return success_response(result, request_id)
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh-token — 刷新 Token
# ---------------------------------------------------------------------------

@router.post("/refresh-token", summary="刷新Token")
async def refresh_token(
    body: RefreshTokenRequest,
    request: Request,
    auth_service: Any = Depends(_get_auth_service),
) -> dict[str, Any]:
    """刷新 JWT Token。

    - 使用 refresh_token 获取新的 token 对
    - refresh_token 有效期 7 天
    - 新的 access_token 有效期 15 分钟
    """
    request_id = getattr(request.state, "request_id", "")
    result = await auth_service.refresh_token(body)
    return success_response(result, request_id)


# ---------------------------------------------------------------------------
# DELETE /api/v1/auth/logout — 登出
# ---------------------------------------------------------------------------

@router.delete("/logout", summary="登出")
async def logout(
    user: CurrentUser,
    request: Request,
    auth_service: Any = Depends(_get_auth_service),
) -> dict[str, Any]:
    """用户登出。

    - 将当前 access_token 加入黑名单
    - 黑名单有效期为 Token 剩余有效期
    - 需要登录（Bearer Token）
    """
    request_id = getattr(request.state, "request_id", "")
    access_token = getattr(request.state, "access_token", "")
    await auth_service.logout(user.id, access_token)
    return success_response({"message": "登出成功"}, request_id)


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me — 获取当前用户信息
# ---------------------------------------------------------------------------

@router.get("/me", summary="获取当前用户信息")
async def get_me(
    user: CurrentUser,
    request: Request,
    auth_service: Any = Depends(_get_auth_service),
) -> dict[str, Any]:
    """获取当前登录用户信息。

    - 返回用户基本信息（手机号脱敏）
    - 返回是否已完善资料
    - 返回是否为未成年人
    - 需要登录（Bearer Token）
    """
    request_id = getattr(request.state, "request_id", "")
    result = await auth_service.get_current_user_info(user)
    return success_response(result, request_id)
