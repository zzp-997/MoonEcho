"""树洞路由模块。

提供树洞吐槽区的 API 端点：
- GET    /api/v1/treehole/posts          树洞帖子列表
- POST   /api/v1/treehole/posts          发布树洞帖子
- GET    /api/v1/treehole/posts/:id      帖子详情
- POST   /api/v1/treehole/posts/:id/resonance  创建共鸣（"我懂你"）
- POST   /api/v1/treehole/posts/:id/comments   创建评论
- DELETE /api/v1/treehole/posts/:id      删除帖子
- POST   /api/v1/treehole/posts/:id/appeal     审核结果申诉

设计原则：
- 强制匿名发布，自动生成虚拟身份
- 内容审核集成（自伤允许发布触发关怀、人身攻击拦截）
- 审核拦截时返回温和反馈文案
- 发布前脱敏提醒（可识别信息检测）
- 骚扰频率控制
- 发布时间随机化（0-15分钟随机延迟显示）
- 模糊时间显示（不显示精确时间）
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
from app.schemas.treehole import (
    AuditAppealCreateRequest,
    AuditAppealCreateResponse,
    ResonanceResponse,
    TOPIC_TAG_LABELS,
    TreeholeCommentCreateRequest,
    TreeholeCommentCreateResponse,
    TreeholeCommentResponse,
    TreeholePostCreateRequest,
    TreeholePostCreateResponse,
    TreeholePostDetailResponse,
    TreeholePostListResponse,
    TreeholePostResponse,
)
from app.services.treehole_service import TreeholeService, create_treehole_service
from app.services.treehole_care import TreeholeCareService, create_treehole_care_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/treehole", tags=["treehole"])


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


def _create_treehole_service(
    settings: Any,
    redis: Any,
) -> TreeholeService:
    """创建树洞服务实例。"""
    content_audit_provider = getattr(settings, "content_audit_provider", "treehole")
    return create_treehole_service(
        settings=settings,
        redis=redis,
        content_audit_provider=content_audit_provider,
    )


def _create_treehole_care_service(
    settings: Any,
    redis: Any,
) -> TreeholeCareService:
    """创建树洞关怀服务实例。"""
    ai_provider = getattr(settings, "ai_provider", "mock")
    zhipu_api_key = getattr(settings, "zhipu_api_key", "")
    return create_treehole_care_service(
        settings=settings,
        redis=redis,
        ai_provider=ai_provider,
        zhipu_api_key=zhipu_api_key,
    )


# ===========================================================================
# 树洞帖子列表与发布
# ===========================================================================

@router.get(
    "/posts",
    summary="获取树洞帖子列表",
    response_model=TreeholePostListResponse,
)
async def list_posts(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    topic_tag: str | None = Query(default=None, description="话题标签筛选"),
) -> dict[str, Any]:
    """获取树洞帖子列表。

    使用温度排序算法：
    - 温度分 = 时间衰减 × 0.4 + 共鸣权重 × 0.3 + 评论权重 × 0.2 + 随机因子 × 0.1
    - 低谷时段（2-5点）调整权重：降低新鲜度权重，提升共鸣数权重
    - 新发布帖子获得曝光加成
    - 7天后不进默认信息流

    支持话题标签筛选。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_treehole_service(settings, redis_client)
            result = await service.list_posts(
                db=db,
                current_user_id=user.id,
                page=page,
                page_size=page_size,
                topic_tag=topic_tag,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Treehole] 获取帖子列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取帖子列表失败",
                status_code=500,
            )


@router.post(
    "/posts",
    summary="发布树洞帖子",
    response_model=TreeholePostCreateResponse,
)
async def create_post(
    body: TreeholePostCreateRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """发布树洞帖子。

    仅支持匿名发布：
    - 自动生成虚拟身份（虚拟昵称 + 气质标签）
    - AI 生成小图标替代头像

    内容审核策略（TreeholeContentAudit）：
    - 自伤内容：允许发布，触发关怀流程
    - 人身攻击：拦截，返回温和反馈文案
    - 广告引流/色情/暴力：拦截

    发布前脱敏提醒：
    - 检测可识别信息（手机号、微信号等）
    - 建议性提醒，不强制阻止

    发布时间随机化：
    - 显示时间加入0-15分钟随机延迟
    - 不显示精确时间，使用模糊表达
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_treehole_service(settings, redis_client)
            result = await service.create_post(
                user_id=user.id,
                request=body,
                db=db,
            )

            # 如果触发关怀，异步启动关怀流程
            if result.trigger_care and result.post.id:
                post_id = result.post.id
                care_service = _create_treehole_care_service(settings, redis_client)
                # 异步触发，不阻塞响应
                await care_service.on_post_created(user.id, post_id, db)
                logger.info(
                    "[Treehole] 触发关怀流程，帖子: %s，用户: %s",
                    post_id, user.id
                )

            # 审核不通过时也提交事务（不创建帖子，但返回反馈）
            # 只有帖子创建成功时才提交
            if result.post.id:
                await db.commit()

            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Treehole] 发布帖子异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="发布帖子失败",
                status_code=500,
            )


# ===========================================================================
# 帖子详情
# ===========================================================================

@router.get(
    "/posts/{post_id}",
    summary="获取帖子详情",
    response_model=TreeholePostDetailResponse,
)
async def get_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="帖子ID"),
) -> dict[str, Any]:
    """获取树洞帖子详情。

    包含帖子信息和评论列表。
    评论不显示发布者身份信息（保持匿名性）。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_treehole_service(settings, redis_client)
            result = await service.get_post(
                post_id=post_id,
                db=db,
                current_user_id=user.id,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Treehole] 获取帖子详情异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取帖子详情失败",
                status_code=500,
            )


# ===========================================================================
# 共鸣功能
# ===========================================================================

@router.post(
    "/posts/{post_id}/resonance",
    summary="创建共鸣（我懂你）",
    response_model=ResonanceResponse,
)
async def create_resonance(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="帖子ID"),
) -> dict[str, Any]:
    """创建共鸣（"我懂你"按钮）。

    最低门槛的互动方式：
    - 点击即表示"我懂你"
    - 不暴露共鸣者身份
    - 共鸣数显示在帖子上

    用户获得共鸣后，AI在下次对话时会提及"有人懂你诶"。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_treehole_service(settings, redis_client)
            result = await service.create_resonance(
                user_id=user.id,
                post_id=post_id,
                db=db,
            )

            # 如果是新共鸣（不是已共鸣），通知关怀服务
            if not result.already_resonated:
                care_service = _create_treehole_care_service(settings, redis_client)
                await care_service.on_resonance_received(user.id, post_id, db)

            # 提交事务
            await db.commit()

            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Treehole] 创建共鸣异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="创建共鸣失败",
                status_code=500,
            )


# ===========================================================================
# 评论功能
# ===========================================================================

@router.post(
    "/posts/{post_id}/comments",
    summary="创建评论",
    response_model=TreeholeCommentCreateResponse,
)
async def create_comment(
    body: TreeholeCommentCreateRequest,
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="帖子ID"),
) -> dict[str, Any]:
    """创建树洞评论。

    评论设计：
    - 限50字，保持轻量
    - 不支持回复评论（树洞不是讨论区）
    - 不显示评论者身份

    T017-B 增强：
    - 审核拦截时返回温和反馈文案
    - 发布前脱敏提醒（可识别信息检测）
    - 骚扰频率控制

    提示语："这里是树洞，不是建议箱。如果TA需要建议，TA会问的。"
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_treehole_service(settings, redis_client)
            result = await service.create_comment(
                user_id=user.id,
                post_id=post_id,
                request=body,
                db=db,
            )
            # 审核不通过时不创建评论，但仍返回反馈
            if result.comment.id:
                await db.commit()

            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Treehole] 创建评论异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="创建评论失败",
                status_code=500,
            )


# ===========================================================================
# 删除功能
# ===========================================================================

@router.delete(
    "/posts/{post_id}",
    summary="删除帖子",
)
async def delete_post(
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="帖子ID"),
) -> dict[str, Any]:
    """删除树洞帖子（软删除）。

    只能删除自己发布的帖子。
    已删除的帖子不会在列表中显示。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_treehole_service(settings, redis_client)
            await service.delete_post(
                user_id=user.id,
                post_id=post_id,
                db=db,
            )
            # 提交事务
            await db.commit()
            return success_response({"deleted": True}, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Treehole] 删除帖子异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="删除帖子失败",
                status_code=500,
            )


# ===========================================================================
# 误判申诉
# ===========================================================================

@router.post(
    "/posts/{post_id}/appeal",
    summary="审核结果申诉",
    response_model=AuditAppealCreateResponse,
)
async def create_appeal(
    body: AuditAppealCreateRequest,
    user: CurrentUser,
    request: Request,
    post_id: str = Path(..., description="帖子ID"),
) -> dict[str, Any]:
    """对审核结果发起申诉。

    被拦截/删除后可申诉，人工复核。
    只有帖子作者可以发起申诉。

    申诉流程：
    1. 用户提交申诉理由
    2. 系统创建申诉记录（复用 reports 表，type 为 audit_appeal）
    3. 管理员审核申诉
    4. 审核通过后恢复内容/解冻功能
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_treehole_service(settings, redis_client)
            result = await service.create_appeal(
                user_id=user.id,
                post_id=post_id,
                reason=body.reason,
                db=db,
            )
            # 提交事务
            await db.commit()

            response = AuditAppealCreateResponse(
                id=result["id"],
                status=result["status"],
                message=result["message"],
            )

            return success_response(response.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Treehole] 创建申诉异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="创建申诉失败",
                status_code=500,
            )


# ===========================================================================
# 话题标签
# ===========================================================================

@router.get(
    "/topics",
    summary="获取话题标签列表",
)
async def list_topics(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取可用的话题标签列表。

    返回话题标签及其显示名称。
    """
    request_id = getattr(request.state, "request_id", "")

    return success_response({
        "topics": [
            {"value": value, "label": label}
            for value, label in TOPIC_TAG_LABELS.items()
        ]
    }, request_id)
