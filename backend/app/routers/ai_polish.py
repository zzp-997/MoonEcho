"""AI 文案润色路由模块。

提供动态广场发布前的 AI 文案润色 API：
- POST /api/v1/ai/polish   AI 文案润色

功能特点：
- 多种风格可选（温暖治愈、轻松幽默、真诚分享）
- 生成 2 个版本供用户选择
- 每用户每分钟限制 5 次请求
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request

from app.core.errors import AppError
from app.core.responses import success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.schemas.ai_polish import PolishRequest, PolishResponse, PolishStyle
from app.services.ai_polish import (
    AIPolishService,
    check_rate_limit,
    create_polish_service,
    increment_rate_limit,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai-polish"])


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _get_settings(request: Request) -> Any:
    """从应用状态获取应用配置。"""
    return request.app.state.settings


def _get_redis(request: Request) -> Any:
    """从应用状态获取 Redis 客户端。"""
    return request.app.state.redis


def _create_polish_service(settings: Any) -> AIPolishService:
    """创建 AI 润色服务实例。

    Args:
        settings: 应用配置

    Returns:
        AIPolishService 实例
    """
    # 从配置获取 API Key
    api_key = getattr(settings, "zhipu_api_key", "")
    return create_polish_service(api_key=api_key)


# ---------------------------------------------------------------------------
# POST /api/v1/ai/polish — AI 文案润色
# ---------------------------------------------------------------------------

@router.post("/polish", summary="AI文案润色")
async def polish(
    body: PolishRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """AI 文案润色接口。

    为用户提供动态发布前的文案润色服务：
    - 保留原意和情感基调
    - 不改变核心内容
    - 字数不超过原文的 1.5 倍
    - 提供 2 个版本供选择

    频率限制：每用户每分钟最多 5 次

    Args:
        body: 润色请求体
        user: 当前用户
        request: FastAPI 请求对象

    Returns:
        润色结果，包含原文和 2 个润色版本

    Raises:
        AppError: 内容过长、频率超限或 AI 服务不可用时抛出
    """
    request_id = getattr(request.state, "request_id", "")

    # 获取 Redis 客户端和配置
    redis_client = _get_redis(request)
    settings = _get_settings(request)

    # 检查频率限制
    allowed, remaining = await check_rate_limit(redis_client, str(user.id))
    if not allowed:
        logger.warning(
            "[AIPolish] 用户 %s 润色请求频率超限",
            user.id
        )
        raise AppError(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="润色请求过于频繁，请稍后再试（每分钟最多 5 次）",
            status_code=429,
        )

    # 创建润色服务
    service = _create_polish_service(settings)

    try:
        # 执行润色
        result = await service.polish(
            content=body.content,
            style=body.style,
        )

        # 增加请求计数
        await increment_rate_limit(redis_client, str(user.id))

        logger.info(
            "[AIPolish] 用户 %s 润色成功，风格: %s，剩余次数: %d",
            user.id,
            body.style.value,
            remaining
        )

        return success_response(result, request_id)

    except AppError:
        raise
    except Exception as e:
        logger.error("[AIPolish] 润色异常: %s", str(e))
        raise AppError(
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            message="AI 服务暂时不可用，请稍后重试",
            status_code=503,
        )