"""情绪日记路由模块。

提供情绪日记相关的 API 端点：
- GET    /api/v1/diaries                      获取日记列表
- POST   /api/v1/diaries                      创建日记
- GET    /api/v1/diaries/privacy              获取隐私同意状态
- POST   /api/v1/diaries/privacy              设置隐私同意
- GET    /api/v1/diaries/sync-settings        获取同步设置
- PUT    /api/v1/diaries/sync-settings        更新同步设置
- GET    /api/v1/diaries/stats                获取日记统计
- GET    /api/v1/diaries/report/weekly        获取本周情绪周报
- GET    /api/v1/diaries/report/history        获取周报历史
- POST   /api/v1/diaries/export                导出日记
- GET    /api/v1/diaries/export/{task_id}/download  下载导出文件
- DELETE /api/v1/diaries/all                  删除全部日记
- GET    /api/v1/diaries/{diary_id}           获取日记详情
- PUT    /api/v1/diaries/{diary_id}           更新日记
- DELETE /api/v1/diaries/{diary_id}           删除单条日记

注意：静态路径路由必须定义在动态路径/{diary_id}之前，避免路径匹配错误。
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

import hmac
from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.responses import success_response
from app.enums.error_codes import ErrorCode
from app.middleware.auth import CurrentUser
from app.schemas.diary import (
    DiaryCreateRequest,
    DiaryDetailResponse,
    DiaryListResponse,
    DiaryResponse,
    DiaryStatsResponse,
    DiaryUpdateRequest,
    DeleteAllResponse,
    ExportRequest,
    ExportResponse,
    PrivacyConsentRequest,
    PrivacyConsentResponse,
    SyncSettingsResponse,
    SyncSettingsUpdateRequest,
)
from app.schemas.weekly_report import (
    WeeklyReportResponse,
    EmptyWeeklyReportResponse,
    WeeklyReportHistoryResponse,
)
from app.services.diary_service import DiaryService
from app.services.weekly_report_service import WeeklyReportService
from app.services.encryption import compute_content_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diaries", tags=["diaries"])


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


def _create_diary_service(
    settings: Any,
    redis_client: Any,
) -> DiaryService:
    """创建日记服务实例。

    Args:
        settings: 应用配置
        redis_client: Redis 客户端

    Returns:
        DiaryService 实例
    """
    return DiaryService(
        settings=settings,
        redis=redis_client,
    )


def _create_weekly_report_service(
    settings: Any,
    redis_client: Any,
) -> WeeklyReportService:
    """创建周报服务实例。"""
    return WeeklyReportService(
        settings=settings,
        redis=redis_client,
        ai_provider=settings.ai_provider,
        zhipu_api_key=settings.zhipu_api_key,
    )


# ---------------------------------------------------------------------------
# 删除全部确认请求
# ---------------------------------------------------------------------------

class DeleteAllConfirmRequest(BaseModel):
    """删除全部日记确认请求。"""
    confirm: bool = Field(
        ...,
        description="确认删除，必须为 true",
    )


# ===========================================================================
# 以下为静态路径路由（必须在动态路径之前定义）
# ===========================================================================

# ---------------------------------------------------------------------------
# GET /api/v1/diaries — 获取日记列表
# ---------------------------------------------------------------------------

@router.get("", summary="获取日记列表", response_model=DiaryListResponse)
async def list_diaries(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=50, description="每页数量"),
    start_date: date | None = Query(default=None, description="起始日期"),
    end_date: date | None = Query(default=None, description="结束日期"),
    emotion_tone: str | None = Query(default=None, description="情绪色调筛选"),
) -> dict[str, Any]:
    """获取用户的日记列表。

    - 支持按日期范围筛选
    - 支持按情绪色调筛选
    - 按记录日期倒序排列
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            result = await service.list_diaries(
                user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
                start_date=start_date,
                end_date=end_date,
                emotion_tone=emotion_tone,
            )
            result["request_id"] = request_id
            return result
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 获取日记列表异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取日记列表失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/diaries — 创建日记
# ---------------------------------------------------------------------------

@router.post("", summary="创建日记")
async def create_diary(
    body: DiaryCreateRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """创建情绪日记。

    三层标签结构：
    - emotion_tone: 情绪色调（必选）
    - emotion_labels: 情绪标签（可选，最多3个）
    - content_text: 自由文字（可选，支持语音输入）

    0 字记录规则：
    - 纯色调记录可提交（content_text 为空）
    - 计入"已记录 N 天"统计
    - 不计入 AI 周报分析样本
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            result = await service.create_diary(
                user_id=user.id,
                request=body,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 创建日记异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="创建日记失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/diaries/privacy — 获取隐私同意状态
# ---------------------------------------------------------------------------

@router.get(
    "/privacy",
    summary="获取隐私同意状态",
)
async def get_privacy_consent(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取用户隐私同意状态。

    首次进入日记页面时调用。
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = _create_diary_service(settings, redis_client)
        result = await service.get_privacy_consent(user_id=user.id)
        return success_response(result.model_dump(), request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[Diaries] 获取隐私同意状态异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="获取隐私同意状态失败",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# POST /api/v1/diaries/privacy — 设置隐私同意
# ---------------------------------------------------------------------------

@router.post(
    "/privacy",
    summary="设置隐私同意",
)
async def set_privacy_consent(
    body: PrivacyConsentRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """同意隐私声明并选择同步模式。

    同步模式：
    - local_only: 仅存储在本地设备
    - cloud_sync: 开启云端同步（端到端加密）
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = _create_diary_service(settings, redis_client)
        result = await service.set_privacy_consent(
            user_id=user.id,
            request=body,
        )
        return success_response(result.model_dump(), request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[Diaries] 设置隐私同意异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="设置隐私同意失败",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# GET /api/v1/diaries/sync-settings — 获取同步设置
# ---------------------------------------------------------------------------

@router.get(
    "/sync-settings",
    summary="获取同步设置",
)
async def get_sync_settings(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取用户同步设置。

    包含同步模式、上次同步时间、已同步设备数等。
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = _create_diary_service(settings, redis_client)
        result = await service.get_sync_settings(user_id=user.id)
        return success_response(result.model_dump(), request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[Diaries] 获取同步设置异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="获取同步设置失败",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# PUT /api/v1/diaries/sync-settings — 更新同步设置
# ---------------------------------------------------------------------------

@router.put(
    "/sync-settings",
    summary="更新同步设置",
)
async def update_sync_settings(
    body: SyncSettingsUpdateRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """更新用户同步设置。

    切换同步模式（本地/云端）。
    """
    request_id = getattr(request.state, "request_id", "")

    settings = _get_settings(request)
    redis_client = _get_redis(request)

    try:
        service = _create_diary_service(settings, redis_client)
        result = await service.update_sync_settings(
            user_id=user.id,
            request=body,
        )
        return success_response(result.model_dump(), request_id)
    except AppError:
        raise
    except Exception as e:
        logger.error("[Diaries] 更新同步设置异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="更新同步设置失败",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# GET /api/v1/diaries/stats — 获取日记统计
# ---------------------------------------------------------------------------

@router.get(
    "/stats",
    summary="获取日记统计",
)
async def get_diary_stats(
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """获取用户日记统计。

    包含：
    - 总记录数
    - 已记录天数
    - 0 字记录数
    - 有效样本数
    - 情绪分布
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            result = await service.get_stats(
                user_id=user.id,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 获取日记统计异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取日记统计失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/diaries/report/weekly — 获取本周情绪周报
# ---------------------------------------------------------------------------

@router.get(
    "/report/weekly",
    summary="获取本周情绪周报",
)
async def get_weekly_report(
    user: CurrentUser,
    request: Request,
    force_refresh: bool = Query(
        default=False,
        description="是否强制重新生成",
    ),
) -> dict[str, Any]:
    """获取本周情绪周报。

    五段式周报结构：
    1. 动态标题 - 概括本周情绪特点
    2. 情绪故事线 - 叙事体描述情绪走势
    3. 关键词云 - 从日记中提取的高频词
    4. 一句看见 - 提炼核心感受
    5. 温和建议 - 支持性建议
    6. 下周展望 - 一句话收束

    注意：0 字记录不计入周报分析。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_weekly_report_service(settings, redis_client)
            result = await service.get_or_generate_weekly_report(
                user_id=user.id,
                db=db,
                force_refresh=force_refresh,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 获取周报异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取周报失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/diaries/report/history — 获取周报历史
# ---------------------------------------------------------------------------

@router.get(
    "/report/history",
    summary="获取周报历史",
)
async def get_report_history(
    user: CurrentUser,
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> dict[str, Any]:
    """获取用户的周报历史。

    按周倒序排列，支持分页。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_weekly_report_service(settings, redis_client)
            result = await service.get_report_history(
                user_id=user.id,
                db=db,
                page=page,
                page_size=page_size,
            )
            result["request_id"] = request_id
            return result
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 获取周报历史异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取周报历史失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# POST /api/v1/diaries/export — 导出日记
# ---------------------------------------------------------------------------

@router.post(
    "/export",
    summary="导出日记",
)
async def export_diaries(
    body: ExportRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """导出日记。

    支持格式：JSON、PDF
    导出文件24小时内有效。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            result = await service.export_diaries(
                user_id=user.id,
                request=body,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 导出日记异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="导出日记失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# GET /api/v1/diaries/export/{task_id}/download — 下载导出文件
# ---------------------------------------------------------------------------

@router.get("/export/{task_id}/download", summary="下载导出文件")
async def download_export(
    user: CurrentUser,
    request: Request,
    task_id: str = Path(..., description="导出任务ID"),
) -> dict[str, Any]:
    """下载导出的日记文件。

    文件下载链接24小时内有效。
    """
    request_id = getattr(request.state, "request_id", "")

    redis_client = _get_redis(request)

    try:
        # 从 Redis 获取导出文件数据
        export_key = f"diary:export:{task_id}"
        export_data = await redis_client.get(export_key)

        if export_data is None:
            raise AppError(
                code=ErrorCode.FILE_NOT_FOUND,
                message="导出文件已过期或不存在",
                status_code=404,
            )

        if isinstance(export_data, bytes):
            export_data = export_data.decode("utf-8")

        data = json.loads(export_data)

        # 验证用户身份
        if data.get("user_id") != user.id:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权限访问此文件",
                status_code=403,
            )

        return success_response({
            "content": data.get("content"),
            "format": data.get("format"),
        }, request_id)
    except AppError:
        raise
    except json.JSONDecodeError as e:
        logger.error("[Diaries] 解析导出数据异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="导出文件数据损坏",
            status_code=500,
        )
    except Exception as e:
        logger.error("[Diaries] 下载导出文件异常: %s", str(e))
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="下载导出文件失败",
            status_code=500,
        )


# ---------------------------------------------------------------------------
# DELETE /api/v1/diaries/all — 删除全部日记
# ---------------------------------------------------------------------------

@router.delete("/all", summary="删除全部日记", response_model=DeleteAllResponse)
async def delete_all_diaries(
    body: DeleteAllConfirmRequest,
    user: CurrentUser,
    request: Request,
) -> dict[str, Any]:
    """删除用户全部日记（软删除）。

    危险操作，需要确认参数 confirm=true。
    """
    request_id = getattr(request.state, "request_id", "")

    # 确认删除
    if not body.confirm:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="请确认删除操作（confirm=true）",
            status_code=400,
        )

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            result = await service.delete_all_diaries(
                user_id=user.id,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 删除全部日记异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="删除全部日记失败",
                status_code=500,
            )


# ===========================================================================
# 以下为动态路径路由（必须在静态路径之后定义）
# ===========================================================================

# ---------------------------------------------------------------------------
# GET /api/v1/diaries/{diary_id} — 获取日记详情
# ---------------------------------------------------------------------------

@router.get(
    "/{diary_id}",
    summary="获取日记详情",
)
async def get_diary(
    user: CurrentUser,
    request: Request,
    diary_id: str = Path(..., description="日记ID"),
) -> dict[str, Any]:
    """获取单条日记详情。

    包含色调元数据（颜色、含义、代表语）。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            result = await service.get_diary(
                user_id=user.id,
                diary_id=diary_id,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 获取日记详情异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="获取日记详情失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# PUT /api/v1/diaries/{diary_id} — 更新日记
# ---------------------------------------------------------------------------

@router.put(
    "/{diary_id}",
    summary="更新日记",
)
async def update_diary(
    body: DiaryUpdateRequest,
    user: CurrentUser,
    request: Request,
    diary_id: str = Path(..., description="日记ID"),
) -> dict[str, Any]:
    """更新情绪日记。

    支持部分更新：
    - emotion_tone: 情绪色调
    - emotion_labels: 情绪标签
    - content_text: 文字内容
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            result = await service.update_diary(
                user_id=user.id,
                diary_id=diary_id,
                request=body,
                db=db,
            )
            return success_response(result.model_dump(), request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 更新日记异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="更新日记失败",
                status_code=500,
            )


# ---------------------------------------------------------------------------
# DELETE /api/v1/diaries/{diary_id} — 删除单条日记
# ---------------------------------------------------------------------------

@router.delete("/{diary_id}", summary="删除单条日记")
async def delete_diary(
    user: CurrentUser,
    request: Request,
    diary_id: str = Path(..., description="日记ID"),
) -> dict[str, Any]:
    """删除单条日记（软删除）。

    已删除的日记不会在列表中显示。
    """
    request_id = getattr(request.state, "request_id", "")

    session_factory = _get_db_session(request)
    settings = _get_settings(request)
    redis_client = _get_redis(request)

    async with session_factory() as db:
        try:
            service = _create_diary_service(settings, redis_client)
            await service.delete_diary(
                user_id=user.id,
                diary_id=diary_id,
                db=db,
            )
            return success_response({"deleted": True}, request_id)
        except AppError:
            raise
        except Exception as e:
            logger.error("[Diaries] 删除日记异常: %s", str(e))
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="删除日记失败",
                status_code=500,
            )
