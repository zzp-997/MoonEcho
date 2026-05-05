"""用户相关路由模块。

提供用户个人相关的 API 端点：
- GET  /api/v1/users/me                  获取自己的用户信息
- PATCH /api/v1/users/me                  更新自己的资料
- GET  /api/v1/users/me/tags             获取我的兴趣标签
- POST /api/v1/users/me/tags             添加兴趣标签
- DELETE /api/v1/users/me/tags/:tag_id   删除兴趣标签
- GET  /api/v1/users/me/profile-tags     获取AI画像标签
- GET  /api/v1/users/me/social-energy    获取当前社交能量
- POST /api/v1/users/me/social-energy/rest 主动休息恢复能量
- GET  /api/v1/users/me/social-level     渐进式社交暴露级别

- GET  /api/v1/users/:id                 查看他人公开信息
- GET  /api/v1/users/:id/public-posts    他人的公开动态列表
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.responses import paginated_response, success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.schemas.social_energy import RestResponse, SocialEnergyResponse
from app.schemas.user import (
    AIProfileTagResponse,
    PublicPostsResponse,
    SocialLevelResponse,
    UserDetailResponse,
    UserPublicInfo,
    UserTagCreateRequest,
    UserTagResponse,
    UserTagsResponse,
    UserUpdateRequest,
)
from app.services.ai_profile import create_ai_profile_service
from app.services.social_energy import create_social_energy_service
from app.services.social_level import create_social_level_service
from app.services.user_service import create_user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _get_db_session(request: Request) -> Any:
    """从应用状态获取数据库会话工厂。"""
    return request.app.state.db_session


def _get_redis(request: Request) -> Any:
    """从应用状态获取 Redis 客户端。"""
    return request.app.state.redis


# ---------------------------------------------------------------------------
# GET /api/v1/users/me — 获取自己的用户信息
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    summary="获取自己的用户信息",
)
async def get_my_profile(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取当前用户的详细信息，包括基本资料和兴趣标签。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_user_service()
            result = await service.get_my_profile(user.id, db)
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 获取用户信息异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取用户信息失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me — 更新自己的资料
# ---------------------------------------------------------------------------

@router.patch(
    "/me",
    summary="更新自己的资料",
)
async def update_my_profile(
    user: CurrentUser,
    request: Request,
    update_data: UserUpdateRequest,
) -> dict[str, Any]:
    """更新当前用户的资料（昵称、头像、城市、职业）。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_user_service()
            result = await service.update_profile(user.id, update_data, db)
            await db.commit()
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 更新用户资料异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="更新用户资料失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/tags — 获取我的兴趣标签
# ---------------------------------------------------------------------------

@router.get(
    "/me/tags",
    summary="获取我的兴趣标签",
)
async def get_my_tags(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取当前用户的兴趣标签列表。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_user_service()
            result = await service.get_my_tags(user.id, db)
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 获取兴趣标签异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取兴趣标签失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/users/me/tags — 添加兴趣标签
# ---------------------------------------------------------------------------

@router.post(
    "/me/tags",
    summary="添加兴趣标签",
)
async def add_my_tag(
    user: CurrentUser,
    request: Request,
    tag_data: UserTagCreateRequest,
) -> dict[str, Any]:
    """添加兴趣标签（最多10个）。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_user_service()
            result = await service.add_tag(user.id, tag_data, db)
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 添加兴趣标签异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="添加兴趣标签失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/me/tags/:tag_id — 删除兴趣标签
# ---------------------------------------------------------------------------

@router.delete(
    "/me/tags/{tag_id}",
    summary="删除兴趣标签",
)
async def delete_my_tag(
    user: CurrentUser,
    request: Request,
    tag_id: str = Path(..., description="标签ID"),
) -> dict[str, Any]:
    """删除指定的兴趣标签。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_user_service()
            result = await service.delete_tag(user.id, tag_id, db)
            await db.commit()
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 删除兴趣标签异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="删除兴趣标签失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/profile-tags — 获取AI画像标签
# ---------------------------------------------------------------------------

@router.get(
    "/me/profile-tags",
    summary="获取AI画像标签",
)
async def get_my_profile_tags(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取AI基于用户行为生成的画像标签。

    包括情绪模式、社交偏好、兴趣领域等。
    用户可选择隐藏部分标签。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            user_service = create_user_service()
            profile_service = create_ai_profile_service(redis_client)
            result = await user_service.get_profile_tags(
                user.id, profile_service, db
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 获取AI画像标签异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取AI画像标签失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/social-energy — 获取社交能量
# ---------------------------------------------------------------------------

@router.get(
    "/me/social-energy",
    summary="获取社交能量",
)
async def get_social_energy(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取当前用户的社交能量状态。

    返回：
    - energy: 当前能量值（0-100）
    - percentage: 百分比显示
    - status: 状态描述
    - can_rest: 是否可以主动休息
    - rest_cooldown_remaining: 休息冷却剩余秒数
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = create_social_energy_service(redis_client)
            result = await service.get_energy(user.id, db)
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[SocialEnergy] 获取社交能量异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取社交能量失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/users/me/social-energy/rest — 主动休息
# ---------------------------------------------------------------------------

@router.post(
    "/me/social-energy/rest",
    summary="主动休息恢复能量",
)
async def rest_and_recover(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """主动休息恢复社交能量。

    用户点击"休息一下"按钮后恢复 20% 能量。
    有冷却时间限制（1小时一次）。

    返回：
    - old_energy: 休息前能量值
    - new_energy: 休息后能量值
    - change: 能量变化量
    - message: 提示消息（如"休息了一会，感觉好多了~"）
    - cooldown_until: 下次可休息时间戳
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = create_social_energy_service(redis_client)
            result = await service.rest_and_recover(user.id, db)
            await db.commit()  # 提交事务
            return success_response(result, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[SocialEnergy] 主动休息异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="休息恢复失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/social-level — 渐进式社交暴露级别
# ---------------------------------------------------------------------------

@router.get(
    "/me/social-level",
    summary="获取渐进式社交暴露级别",
)
async def get_social_level(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取用户当前的渐进式社交暴露级别。

    六级渐进式社交暴露：
    - Level 1：浏览动态广场（零社交压力）
    - Level 2：点共鸣/点赞（最小社交动作）
    - Level 3：评论互动（轻度社交）
    - Level 4：悄悄关注（单向关注）
    - Level 5：发送好友申请（双向连接）
    - Level 6：私聊（深度社交）

    返回：
    - current_level: 当前级别（1-6）
    - progress_description: 进度描述
    - unlock_status: 各级别解锁状态
    - next_action: 建议下一步行动
    - behavior_stats: 行为统计数据
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            user_service = create_user_service()
            social_level_service = create_social_level_service()
            result = await user_service.get_social_level(
                user.id, social_level_service, db
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 获取社交暴露级别异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取社交暴露级别失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/users/:id — 查看他人公开信息
# ---------------------------------------------------------------------------

@router.get(
    "/{user_id}",
    summary="查看他人公开信息",
)
async def get_user_public_info(
    user: CurrentUser,
    request: Request,
    user_id: str = Path(..., description="目标用户ID"),
) -> dict[str, Any]:
    """查看他人的公开信息。

    返回对方的公开信息（昵称/头像/画像标签）。
    用于好友申请时展示对方信息和个人主页查看他人信息。

    隐私保护：
    - 不返回私密数据
    - 被拉黑时返回403
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            user_service = create_user_service()
            profile_service = create_ai_profile_service(redis_client)
            result = await user_service.get_user_public_info(
                user.id, user_id, profile_service, db
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 获取他人公开信息异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取用户公开信息失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/users/:id/public-posts — 他人的公开动态列表
# ---------------------------------------------------------------------------

@router.get(
    "/{user_id}/public-posts",
    summary="获取他人公开动态列表",
)
async def get_user_public_posts(
    user: CurrentUser,
    request: Request,
    user_id: str = Path(..., description="目标用户ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=5, ge=1, le=5, description="每页数量，最多5"),
) -> dict[str, Any]:
    """获取他人的公开动态列表。

    返回对方的最近公开动态（分页，最多5条）。
    用于好友申请时展示"Ta的公开动态"。

    隐私保护：
    - 仅返回公开动态（visibility='public'）
    - 不返回匿名动态
    - 被拉黑时返回403
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)

    async with session_factory() as db:
        try:
            service = create_user_service()
            result = await service.get_user_public_posts(
                user.id, user_id, db, page, page_size
            )
            return paginated_response(
                data=[item.model_dump() for item in result.data],
                page=result.page,
                page_size=result.page_size,
                total=result.total,
                request_id=request_id,
            )
        except AppError:
            raise
        except Exception as e:
            logger.error("[Users] 获取他人公开动态异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取公开动态失败",
                status_code=500,
            )
