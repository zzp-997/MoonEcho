"""账户注销路由模块。

提供账户注销相关的 API 端点：
- POST   /api/v1/users/me/delete                发起账户注销
- GET    /api/v1/users/me/delete/pre-check     注销预检查
- GET    /api/v1/users/me/delete/progress      查询注销进度
- POST   /api/v1/users/me/export                导出用户数据

安全设计：
- 所有接口需要用户认证
- 注销前进行预检查和警告确认
- 注销过程中实时反馈进度
- 注销完成后使所有 Token 失效
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request

from app.core.errors import AppError
from app.core.responses import success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.schemas.account import (
    AccountDeletionRequest,
    AccountDeletionResponse,
    DataExportRequest,
    DataExportResponse,
    DeletionPreCheckResponse,
)
from app.services.account_deletion import create_account_deletion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users/me", tags=["account-deletion"])


# ---------------------------------------------------------------------------
# 依赖注入辅助函数
# ---------------------------------------------------------------------------

def _get_db_session(request: Request) -> Any:
    """从应用状态获取数据库会话工厂。"""
    return request.app.state.db_session


def _get_redis(request: Request) -> Any:
    """从应用状态获取 Redis 客户端。"""
    return request.app.state.redis


def _get_auth_service(request: Request) -> Any:
    """从应用状态获取认证服务。"""
    return request.app.state.auth_service


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/delete/pre-check — 注销预检查
# ---------------------------------------------------------------------------

@router.get(
    "/delete/pre-check",
    summary="账户注销预检查",
)
async def pre_check_deletion(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """账户注销预检查。

    在用户发起注销前展示：
    - 是否可以注销
    - 警告信息
    - 数据摘要
    - 不可逆操作提醒

    Returns:
        DeletionPreCheckResponse: 预检查结果
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = create_account_deletion_service(redis_client)
            result = await service.pre_check(user.id, db)
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[AccountDeletion] 预检查异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="预检查失败，请稍后重试",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/users/me/delete — 发起账户注销
# ---------------------------------------------------------------------------

@router.post(
    "/delete",
    summary="发起账户注销",
)
async def delete_account(
    user: CurrentUser,
    request: Request,
    deletion_request: AccountDeletionRequest,
) -> dict[str, Any]:
    """发起账户注销。

    执行完整的账户注销流程：
    1. 检查是否可以注销
    2. 删除/匿名化所有用户数据
    3. 使所有 Token 失效
    4. 记录注销日志

    注意：此操作不可逆！

    Args:
        deletion_request: 注销请求参数

    Returns:
        AccountDeletionResponse: 注销结果
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    redis_client = _get_redis(request)
    auth_service = _get_auth_service(request)

    # 获取当前 token（用于注销后使其失效）
    access_token = getattr(request.state, "access_token", "")

    async with session_factory() as db:
        try:
            service = create_account_deletion_service(redis_client)
            result = await service.execute_deletion(
                user_id=user.id,
                reason=deletion_request.reason,
                export_data=deletion_request.export_data,
                auth_service=auth_service,
                access_token=access_token,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[AccountDeletion] 注销异常: %s", str(e))
            raise AppError(
                code=ErrorCode.ACCOUNT_DELETION_FAILED,
                message="账户注销失败，请稍后重试",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/users/me/export — 导出用户数据
# ---------------------------------------------------------------------------

@router.post(
    "/export",
    summary="导出用户数据",
)
async def export_user_data(
    user: CurrentUser,
    request: Request,
    export_request: DataExportRequest,
) -> dict[str, Any]:
    """导出用户数据。

    生成用户数据备份文件，供用户下载。
    导出链接24小时后过期。

    Args:
        export_request: 导出请求参数

    Returns:
        DataExportResponse: 导出结果
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = create_account_deletion_service(redis_client)
            result = await service.export_user_data(
                user_id=user.id,
                db=db,
                include_diaries=export_request.include_diaries,
                include_posts=export_request.include_posts,
                include_treehole=export_request.include_treehole,
                include_ai_conversations=export_request.include_ai_conversations,
                include_friends=export_request.include_friends,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[AccountDeletion] 数据导出异常: %s", str(e))
            raise AppError(
                code=ErrorCode.DATA_EXPORT_FAILED,
                message="数据导出失败，请稍后重试",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/users/me/export/{export_id} — 下载导出文件
# ---------------------------------------------------------------------------

@router.get(
    "/export/{export_id}",
    summary="下载导出数据",
)
async def download_exported_data(
    user: CurrentUser,
    request: Request,
    export_id: str,
) -> dict[str, Any]:
    """下载导出的数据文件。

    通过导出ID下载之前生成的数据备份文件。
    链接24小时后过期。

    Args:
        export_id: 导出文件ID

    Returns:
        导出的JSON数据
    """
    request_id = getattr(request.state, "request_id", "")
    redis_client = _get_redis(request)

    try:
        export_storage_key = f"export:file:{export_id}"
        export_data = await redis_client.get(export_storage_key)

        if not export_data:
            raise AppError(
                code=ErrorCode.FILE_NOT_FOUND,
                message="导出文件不存在或已过期",
                status_code=404,
            )

        # 解码数据
        if isinstance(export_data, bytes):
            export_data = export_data.decode("utf-8")

        # 返回原始数据
        return success_response(
            {"data": "导出文件内容已准备好，请在应用中下载", "export_id": export_id},
            request_id,
        )

    except AppError:
        raise
    except Exception as e:
        logger.error("[AccountDeletion] 下载导出数据异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="下载失败，请稍后重试",
            status_code=500,
        )