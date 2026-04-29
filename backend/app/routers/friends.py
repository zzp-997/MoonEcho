"""好友系统路由模块。

提供好友申请和好友管理的 API 端点：
- GET    /api/v1/friends                    好友列表
- POST   /api/v1/friend-requests            发送好友申请
- GET    /api/v1/friend-requests            收到的好友申请列表
- POST   /api/v1/friend-requests/:id/accept 同意好友申请
- POST   /api/v1/friend-requests/:id/reject 忽略好友申请
- DELETE /api/v1/friends/:id                删除好友
- POST   /api/v1/users/:id/block            拉黑用户
- DELETE /api/v1/users/:id/block            取消拉黑
- GET    /api/v1/blocks                     拉黑列表
- POST   /api/v1/ai-friends/:id             添加官方AI好友

设计原则：
- 好友申请需打招呼语，可由AI协助生成
- 双向同意机制：忽略不通知，降低社交压力
- 7天过期机制，过期后24小时冷却期
- 同一用户30天最多3次申请
- 官方AI账号添加后自动建立好友关系
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
from app.schemas.friend import (
    AcceptFriendRequestRequest,
    BlockListResponse,
    BlockUserRequest,
    BlockUserResponse,
    CooldownCheckResponse,
    DeleteFriendResponse,
    FriendListResponse,
    FriendRequestListResponse,
    HandleFriendRequestResponse,
    SendFriendRequestRequest,
    SendFriendRequestResponse,
)
from app.services.friend_service import FriendService, create_friend_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["friends"])


# ---------------------------------------------------------------------------
# 依赖注入
# ---------------------------------------------------------------------------

def _get_db_session(request: Request) -> Any:
    """从应用状态获取数据库会话工厂。"""
    return request.app.state.db_session


def _create_friend_service() -> FriendService:
    """创建好友服务实例。"""
    return create_friend_service()


# ===========================================================================
# 好友列表
# ===========================================================================

@router.get(
    "/friends",
    summary="获取好友列表",
)
async def list_friends(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
) -> dict[str, Any]:
    """获取好友列表。

    包含好友基本信息和会话状态，按最后消息时间排序。
    官方AI账号会在好友列表中显示（is_official_ai=true）。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.list_friends(
                user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 获取好友列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取好友列表失败",
                status_code=500,
            )


# ===========================================================================
# 好友申请
# ===========================================================================

@router.post(
    "/friend-requests",
    summary="发送好友申请",
)
async def send_friend_request(
    body: SendFriendRequestRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """发送好友申请。

    业务规则：
    - 必须附带打招呼语（可由AI协助生成）
    - 不能向自己发送申请
    - 不能向已拉黑你的用户发送申请
    - 不能向自己已拉黑的用户发送申请
    - 已是好友则不能发送
    - 过期后需等待24小时冷却期
    - 同一用户30天内最多3次申请

    响应包含：
    - 申请ID
    - 过期时间（7天后）
    - 提示消息
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.send_friend_request(
                user_id=user.id,
                request=body,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 发送好友申请异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="发送好友申请失败",
                status_code=500,
            )


@router.get(
    "/friend-requests",
    summary="获取好友申请列表",
)
async def list_friend_requests(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
) -> dict[str, Any]:
    """获取收到的好友申请列表。

    自动标记过期的申请，按时间倒序排列，pending 状态优先显示。

    响应包含：
    - 申请列表（发送者信息、打招呼语、状态、过期时间）
    - 待处理数量
    - 分页信息
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.list_friend_requests(
                user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 获取好友申请列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取好友申请列表失败",
                status_code=500,
            )


@router.post(
    "/friend-requests/{request_id}/accept",
    summary="同意好友申请",
)
async def accept_friend_request(
    user: CurrentUser,
    request: Request,
    request_id: str = Path(..., description="好友申请ID"),
    body: AcceptFriendRequestRequest | None = None,
) -> dict[str, Any]:
    """同意好友申请。

    业务规则：
    - 同意后自动建立好友关系和创建会话
    - 发送者收到通知："XX已通过你的好友申请，去打个招呼吧~"
    - 可以附带回复打招呼（可选）

    响应包含：
    - 会话ID（用于跳转到聊天）
    - 提示消息
    """
    request_id_str = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.accept_friend_request(
                user_id=user.id,
                request_id=request_id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id_str)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 同意好友申请异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="同意好友申请失败",
                status_code=500,
            )


@router.post(
    "/friend-requests/{request_id}/reject",
    summary="忽略好友申请",
)
async def reject_friend_request(
    user: CurrentUser,
    request: Request,
    request_id: str = Path(..., description="好友申请ID"),
) -> dict[str, Any]:
    """忽略好友申请。

    业务规则：
    - 忽略后发送者不收到通知（降低社交压力）
    - 申请状态变为 rejected

    响应包含：
    - 提示消息
    """
    request_id_str = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.reject_friend_request(
                user_id=user.id,
                request_id=request_id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id_str)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 忽略好友申请异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="忽略好友申请失败",
                status_code=500,
            )


# ===========================================================================
# 删除好友
# ===========================================================================

@router.delete(
    "/friends/{friend_id}",
    summary="删除好友",
)
async def delete_friend(
    user: CurrentUser,
    request: Request,
    friend_id: str = Path(..., description="好友用户ID"),
) -> dict[str, Any]:
    """删除好友。

    业务规则：
    - 对方不会收到通知
    - 聊天记录保留但无法继续发送消息
    - 删除后可以重新发送好友申请
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.delete_friend(
                user_id=user.id,
                friend_user_id=friend_id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 删除好友异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="删除好友失败",
                status_code=500,
            )


# ===========================================================================
# 拉黑用户
# ===========================================================================

@router.post(
    "/users/{user_id}/block",
    summary="拉黑用户",
)
async def block_user(
    current_user: CurrentUser,
    request: Request,
    user_id: str = Path(..., description="被拉黑用户ID"),
    body: BlockUserRequest | None = None,
) -> dict[str, Any]:
    """拉黑用户。

    业务规则：
    - 拉黑后对方无法查看你的动态和主页
    - 拉黑后对方无法发送好友申请
    - 聊天记录从双方的聊天列表中消失
    - 自动删除好友关系（如果存在）
    - 可以填写拉黑原因（可选）
    """
    request_id_str = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    reason = body.reason if body else None

    async with session_factory() as db:
        try:
            result = await service.block_user(
                user_id=current_user.id,
                blocked_user_id=user_id,
                reason=reason,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id_str)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 拉黑用户异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="拉黑用户失败",
                status_code=500,
            )


@router.delete(
    "/users/{user_id}/block",
    summary="取消拉黑",
)
async def unblock_user(
    current_user: CurrentUser,
    request: Request,
    user_id: str = Path(..., description="被拉黑用户ID"),
) -> dict[str, Any]:
    """取消拉黑用户。

    取消拉黑后，对方可以重新查看你的动态和主页，可以发送好友申请。
    """
    request_id_str = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.unblock_user(
                user_id=current_user.id,
                blocked_user_id=user_id,
                db=db,
            )
            await db.commit()
            return success_response(result, request_id_str)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 取消拉黑异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="取消拉黑失败",
                status_code=500,
            )


@router.get(
    "/blocks",
    summary="获取拉黑列表",
)
async def list_blocked_users(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
) -> dict[str, Any]:
    """获取拉黑列表。

    显示已拉黑的用户信息，按拉黑时间倒序排列。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.list_blocked_users(
                user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 获取拉黑列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取拉黑列表失败",
                status_code=500,
            )


# ===========================================================================
# 官方AI好友
# ===========================================================================

@router.post(
    "/ai-friends/{ai_user_id}",
    summary="添加官方AI好友",
)
async def add_ai_friend(
    user: CurrentUser,
    request: Request,
    ai_user_id: str = Path(..., description="官方AI账号用户ID"),
) -> dict[str, Any]:
    """添加官方AI账号为好友。

    官方AI账号（小温/老黑/阿理）添加后自动建立好友关系，
    无需申请流程，可直接开始聊天。

    AI账号ID：
    - ai000001-0000-0000-0000-000000000001（小温）
    - ai000002-0000-0000-0000-000000000002（老黑）
    - ai000003-0000-0000-0000-000000000003（阿理）
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.add_official_ai_friend(
                user_id=user.id,
                ai_user_id=ai_user_id,
                db=db,
            )
            await db.commit()
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 添加AI好友异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="添加AI好友失败",
                status_code=500,
            )


# ===========================================================================
# 冷却期检查
# ===========================================================================

@router.get(
    "/friend-requests/cooldown/{target_user_id}",
    summary="检查好友申请冷却期",
)
async def check_cooldown(
    user: CurrentUser,
    request: Request,
    target_user_id: str = Path(..., description="目标用户ID"),
) -> dict[str, Any]:
    """检查是否可以向目标用户发送好友申请。

    用于前端在发送申请前检查：
    - 是否在冷却期内
    - 30天内已发送申请次数

    响应包含：
    - can_send: 是否可以发送
    - cooldown_until: 冷却期结束时间（如果不能发送）
    - request_count_in_30_days: 30天内已发送次数
    - message: 提示消息
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    service = _create_friend_service()

    async with session_factory() as db:
        try:
            result = await service.check_cooldown(
                user_id=user.id,
                target_user_id=target_user_id,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Friends] 检查冷却期异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="检查冷却期失败",
                status_code=500,
            )