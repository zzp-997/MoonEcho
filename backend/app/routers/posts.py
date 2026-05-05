"""动态广场路由模块。

提供动态广场的 API 端点：
- GET    /api/v1/posts              获取动态列表（支持分页、筛选）
- POST   /api/v1/posts              发布动态
- GET    /api/v1/posts/:id          获取单条动态详情
- PUT    /api/v1/posts/:id          修改动态（仅限自己的）
- DELETE /api/v1/posts/:id          删除动态（仅限自己的）
- POST   /api/v1/posts/:id/like     共鸣（点赞）
- DELETE /api/v1/posts/:id/like     取消共鸣
- POST   /api/v1/posts/:id/comments 发表评论
- GET    /api/v1/posts/:id/comments 获取评论列表
- POST   /api/v1/posts/:id/favorite 收藏
- DELETE /api/v1/posts/:id/favorite 取消收藏
- POST   /api/v1/posts/:id/follow   悄悄关注（实名动态才能关注）

设计原则：
- 支持实名/匿名切换
- 匿名动态不可被关注
- 使用信息流排序算法
- 可见范围设置（public/friends/private）
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.responses import success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.schemas.post import (
    PostCommentCreateRequest,
    PostCommentListResponse,
    PostCommentResponse,
    PostCreateRequest,
    PostDetailResponse,
    PostFavoriteResponse,
    PostFollowResponse,
    PostLikeResponse,
    PostListResponse,
    PostResponse,
    PostUpdateRequest,
    PostVisibility,
)
from app.services.post_service import PostService, create_post_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _get_db_session(request: Request) -> Any:
    """从应用状态获取数据库会话工厂。"""
    return request.app.state.db_session


def _get_settings(request: Request) -> Any:
    """从应用状态获取应用配置。"""
    return request.app.state.settings


def _get_redis(request: Request) -> Any:
    """从应用状态获取 Redis 客户端。"""
    return request.app.state.redis


def _create_post_service(
    settings: Any,
    redis: Any,
) -> PostService:
    """创建动态广场服务实例。"""
    return create_post_service(
        settings=settings,
        redis=redis,
    )


# ===========================================================================
# 动态列表与发布
# ===========================================================================

@router.get(
    "",
    summary="获取动态列表",
)
async def list_posts(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    visibility: PostVisibility | None = Query(
        default=None,
        description="可见性筛选：public/friends/private",
    ),
) -> dict[str, Any]:
    """获取动态列表。

    使用信息流排序算法：
    - 排序分 = 时间新鲜度×0.4 + 互动热度×0.3 + 内容完整度×0.2 + 随机因子×0.1
    - 时间新鲜度：发布时间越近分数越高（24小时内衰减）
    - 互动热度：共鸣数×2 + 评论数×3 + 收藏数×1.5
    - 内容完整度：有图片+0.3、文字>20字+0.2
    - 随机因子：防止信息流固化

    支持可见性筛选。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.list_posts(
                current_user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
                visibility=visibility,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 获取动态列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取动态列表失败",
                status_code=500,
            )


@router.post(
    "",
    summary="发布动态",
)
async def create_post(
    body: PostCreateRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """发布动态。

    支持实名/匿名切换：
    - 默认实名发布，显示用户昵称和头像
    - 选择匿名时，使用虚拟身份（复用树洞的匿名身份机制）
    - 匿名动态不可被关注

    支持可见范围设置：
    - public: 全部公开（默认）
    - friends: 仅好友可见
    - private: 仅自己可见（私密）

    支持图片上传（最多9张）。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.create_post(
                user_id=user.id,
                request=body,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 发布动态异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="发布动态失败",
                status_code=500,
            )


# ===========================================================================
# 动态详情
# ===========================================================================

@router.get(
    "/{post_id}",
    summary="获取动态详情",
)
async def get_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """获取单条动态详情。

    包含动态信息和评论列表。
    根据可见性权限控制访问。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            post = await service.get_post(
                post_id=post_id,
                current_user_id=user.id,
                db=db,
            )

            # 获取评论列表
            comments = await service.list_comments(
                post_id=post_id,
                current_user_id=user.id,
                db=db,
                page=1,
                page_size=20,
            )

            result = PostDetailResponse(
                post=post,
                comments=comments,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 获取动态详情异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取动态详情失败",
                status_code=500,
            )


@router.put(
    "/{post_id}",
    summary="修改动态",
)
async def update_post(
    body: PostUpdateRequest,
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """修改动态（仅限自己的）。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.update_post(
                post_id=post_id,
                user_id=user.id,
                request=body,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 修改动态异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="修改动态失败",
                status_code=500,
            )


@router.delete(
    "/{post_id}",
    summary="删除动态",
)
async def delete_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """删除动态（软删除，仅限自己的）。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            await service.delete_post(
                post_id=post_id,
                user_id=user.id,
                db=db,
            )
            await db.commit()
            return success_response({"deleted": True}, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 删除动态异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="删除动态失败",
                status_code=500,
            )


# ===========================================================================
# 共鸣功能
# ===========================================================================

@router.post(
    "/{post_id}/like",
    summary="共鸣（点赞）",
)
async def like_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """共鸣（点赞）动态。

    两颗心轻触图标，替代传统点赞。
    "我懂你"而非"我认可"，被共鸣者收到"有人和你共鸣了"。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.like_post(
                post_id=post_id,
                user_id=user.id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 共鸣异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="共鸣失败",
                status_code=500,
            )


@router.delete(
    "/{post_id}/like",
    summary="取消共鸣",
)
async def unlike_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """取消共鸣。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.unlike_post(
                post_id=post_id,
                user_id=user.id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 取消共鸣异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="取消共鸣失败",
                status_code=500,
            )


# ===========================================================================
# 评论功能
# ===========================================================================

@router.get(
    "/{post_id}/comments",
    summary="获取评论列表",
)
async def list_comments(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
) -> dict[str, Any]:
    """获取动态评论列表。

    支持评论回复。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.list_comments(
                post_id=post_id,
                current_user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
            )
            pagination = {
                "page": page,
                "pageSize": page_size,
                "total": len(result),
                "hasMore": len(result) >= page_size,
            }
            response = PostCommentListResponse(
                data=result,
                pagination=pagination,
            )
            return success_response(response.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 获取评论列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取评论列表失败",
                status_code=500,
            )


@router.post(
    "/{post_id}/comments",
    summary="发表评论",
)
async def create_comment(
    body: PostCommentCreateRequest,
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """发表评论。

    支持匿名/实名切换。
    支持回复评论。
    评论最多500字。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.create_comment(
                post_id=post_id,
                user_id=user.id,
                request=body,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 发表评论异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="发表评论失败",
                status_code=500,
            )


# ===========================================================================
# 收藏功能
# ===========================================================================

@router.post(
    "/{post_id}/favorite",
    summary="收藏动态",
)
async def favorite_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """收藏动态。

    保存到个人中心，无通知。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.favorite_post(
                post_id=post_id,
                user_id=user.id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 收藏动态异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="收藏失败",
                status_code=500,
            )


@router.delete(
    "/{post_id}/favorite",
    summary="取消收藏",
)
async def unfavorite_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """取消收藏。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.unfavorite_post(
                post_id=post_id,
                user_id=user.id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 取消收藏异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="取消收藏失败",
                status_code=500,
            )


# ===========================================================================
# 悄悄关注功能
# ===========================================================================

@router.post(
    "/{post_id}/follow",
    summary="悄悄关注",
)
async def follow_author(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """悄悄关注动态作者。

    仅实名动态才能关注，匿名动态不可被关注。
    关注后对方不收到通知。
    关注者可在"我的关注"列表看到。
    被关注者的动态在信息流中优先展示。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.follow_author(
                post_id=post_id,
                user_id=user.id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 悄悄关注异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="关注失败",
                status_code=500,
            )


@router.delete(
    "/{post_id}/follow",
    summary="取消悄悄关注",
)
async def unfollow_author(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="动态ID"),
) -> dict[str, Any]:
    """取消悄悄关注。"""
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_post_service(settings, redis_client)
            result = await service.unfollow_author(
                post_id=post_id,
                user_id=user.id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Posts] 取消悄悄关注异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="取消关注失败",
                status_code=500,
            )
