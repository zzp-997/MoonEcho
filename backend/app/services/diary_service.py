"""情绪日记服务模块。

核心业务逻辑层，封装以下能力：
- 日记 CRUD（含三层标签：色调/标签/文字）
- 0 字记录规则（纯色调可提交，不计入周报分析）
- 隐私同意管理（首次进入需同意）
- 同步模式管理（本地/云端）
- 日记导出（JSON/PDF）
- 批量删除
"""

from __future__ import annotations

import hmac
import io
import json
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import AppSettings
from app.core.errors import AppError
from app.core.responses import paginated_response
from app.enums.error_codes import ErrorCode
from app.models.diary import EmotionDiary
from app.models.user import User
from app.schemas.diary import (
    DiaryCreateRequest,
    DiaryDetailResponse,
    DiaryResponse,
    DiaryStatsResponse,
    DiaryUpdateRequest,
    DeleteAllResponse,
    ExportFormat,
    ExportRequest,
    ExportResponse,
    PrivacyConsentRequest,
    PrivacyConsentResponse,
    SyncMode,
    SyncSettingsResponse,
    SyncSettingsUpdateRequest,
    EMOTION_TONE_META,
)
from app.services.encryption import (
    compute_content_hash,
    encrypt_content_server_side,
    decrypt_content_server_side,
    is_encrypted_content,
    prepare_diary_for_storage,
    retrieve_diary_content,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

def _privacy_consent_key(user_id: str) -> str:
    """隐私同意状态存储 key。"""
    return f"diary:privacy:{user_id}"


def _sync_settings_key(user_id: str) -> str:
    """同步设置存储 key。"""
    return f"diary:sync:{user_id}"


def _export_task_key(task_id: str) -> str:
    """导出任务存储 key。"""
    return f"diary:export:{task_id}"


# ---------------------------------------------------------------------------
# 日记服务
# ---------------------------------------------------------------------------

class DiaryService:
    """情绪日记服务，封装所有日记相关业务逻辑。

    依赖外部注入：
    - settings: 应用配置
    - redis: Redis 客户端
    """

    def __init__(
        self,
        settings: AppSettings,
        redis: Any,
    ) -> None:
        self._settings = settings
        self._redis = redis

    # -----------------------------------------------------------------------
    # 日记 CRUD
    # -----------------------------------------------------------------------

    async def list_diaries(
        self,
        user_id: str,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        start_date: date | None = None,
        end_date: date | None = None,
        emotion_tone: str | None = None,
    ) -> dict[str, Any]:
        """获取日记列表。

        支持分页和筛选：
        - 按日期范围筛选
        - 按情绪色调筛选

        Args:
            user_id: 用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页条数
            start_date: 起始日期
            end_date: 结束日期
            emotion_tone: 情绪色调筛选

        Returns:
            分页响应字典
        """
        # 构建查询条件
        conditions = [
            EmotionDiary.user_id == user_id,
            EmotionDiary.deleted_at.is_(None),
        ]

        if start_date:
            conditions.append(EmotionDiary.record_date >= start_date)
        if end_date:
            conditions.append(EmotionDiary.record_date <= end_date)
        if emotion_tone:
            conditions.append(EmotionDiary.emotion_tone == emotion_tone)

        # 查询总数
        count_stmt = select(func.count()).where(*conditions)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(EmotionDiary)
            .where(*conditions)
            .order_by(EmotionDiary.record_date.desc(), EmotionDiary.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        diaries = result.scalars().all()

        # 获取同步模式
        sync_mode = await self._get_user_sync_mode(user_id)

        # 转换响应
        data = [
            self._convert_to_response(diary, is_cloud_sync=(sync_mode == SyncMode.CLOUD_SYNC))
            for diary in diaries
        ]

        return paginated_response(
            data=data,
            page=page,
            page_size=page_size,
            total=total,
            request_id="",  # 由路由层填充
        )

    async def create_diary(
        self,
        user_id: str,
        request: DiaryCreateRequest,
        db: AsyncSession,
    ) -> DiaryResponse:
        """创建日记。

        三层标签结构：
        - emotion_tone: 情绪色调（必选）
        - emotion_labels: 情绪标签（可选，最多3个）
        - content_text: 自由文字（可选，支持语音输入）

        0 字记录规则：
        - 纯色调记录可提交（content_text 为空）
        - 计入"已记录 N 天"统计
        - 不计入 AI 周报分析样本

        Args:
            user_id: 用户ID
            request: 创建请求
            db: 数据库会话

        Returns:
            创建的日记响应
        """
        # 验证记录日期（不能是未来日期，不能超过一年前）
        today = date.today()
        if request.record_date > today:
            raise AppError(
                code=ErrorCode.INVALID_PARAMETER,
                message="记录日期不能是未来日期",
                status_code=400,
            )
        if request.record_date < today - timedelta(days=365):
            raise AppError(
                code=ErrorCode.INVALID_PARAMETER,
                message="记录日期不能超过一年前",
                status_code=400,
            )
        # 获取同步模式
        sync_mode = await self._get_user_sync_mode(user_id)
        is_cloud_sync = sync_mode == SyncMode.CLOUD_SYNC

        # 准备存储内容
        content_text = request.content_text
        is_encrypted = request.is_encrypted
        content_hash = request.content_hash

        if content_text and not request.is_encrypted:
            # 内容未加密，根据同步模式处理
            storage_result = prepare_diary_for_storage(
                content_text,
                is_cloud_sync=is_cloud_sync,
                client_encrypted=False,
            )
            content_text = storage_result["content"]
            is_encrypted = storage_result["is_encrypted"]
            if not content_hash:
                content_hash = storage_result["content_hash"]

        # 创建日记记录
        diary = EmotionDiary(
            user_id=user_id,
            emotion_tone=request.emotion_tone.value if hasattr(request.emotion_tone, 'value') else request.emotion_tone,
            emotion_labels=request.emotion_labels,
            content_text=content_text,
            content_hash=content_hash,
            record_date=request.record_date,
            client_id=request.client_id,
            is_synced=is_cloud_sync,  # 云端同步模式下标记为已同步
        )

        db.add(diary)
        await db.commit()
        await db.refresh(diary)

        logger.info(
            "日记已创建: user_id=%s, diary_id=%s, record_date=%s, is_zero_record=%s",
            user_id,
            diary.id,
            diary.record_date,
            not request.content_text,
        )

        return self._convert_to_response(diary, is_cloud_sync=is_cloud_sync)

    async def get_diary(
        self,
        user_id: str,
        diary_id: str,
        db: AsyncSession,
    ) -> DiaryDetailResponse:
        """获取日记详情。

        Args:
            user_id: 用户ID
            diary_id: 日记ID
            db: 数据库会话

        Returns:
            日记详情响应

        Raises:
            AppError: 日记不存在或无权限访问时抛出
        """
        diary = await self._get_diary_by_id(user_id, diary_id, db)

        # 获取同步模式
        sync_mode = await self._get_user_sync_mode(user_id)
        is_cloud_sync = sync_mode == SyncMode.CLOUD_SYNC

        # 获取色调元数据
        tone_meta = None
        if diary.emotion_tone:
            tone_meta = EMOTION_TONE_META.get(diary.emotion_tone)

        # 判断是否为 0 字记录
        is_zero_record = not diary.content_text or len(diary.content_text.strip()) == 0

        return DiaryDetailResponse(
            id=diary.id,
            emotion_tone=diary.emotion_tone,
            emotion_labels=diary.emotion_labels,
            content_text=self._decrypt_content(diary, is_cloud_sync),
            record_date=diary.record_date,
            is_synced=diary.is_synced,
            is_encrypted=is_encrypted_content(diary.content_text) if diary.content_text else False,
            created_at=diary.created_at,
            updated_at=diary.updated_at,
            client_id=diary.client_id,
            content_hash=diary.content_hash,
            is_zero_record=is_zero_record,
            tone_meta=tone_meta,
        )

    async def update_diary(
        self,
        user_id: str,
        diary_id: str,
        request: DiaryUpdateRequest,
        db: AsyncSession,
    ) -> DiaryResponse:
        """更新日记。

        支持部分更新：
        - emotion_tone: 情绪色调
        - emotion_labels: 情绪标签
        - content_text: 文字内容

        Args:
            user_id: 用户ID
            diary_id: 日记ID
            request: 更新请求
            db: 数据库会话

        Returns:
            更新后的日记响应
        """
        diary = await self._get_diary_by_id(user_id, diary_id, db)

        # 获取同步模式
        sync_mode = await self._get_user_sync_mode(user_id)
        is_cloud_sync = sync_mode == SyncMode.CLOUD_SYNC

        # 更新字段
        if request.emotion_tone is not None:
            diary.emotion_tone = request.emotion_tone.value if hasattr(request.emotion_tone, 'value') else request.emotion_tone

        if request.emotion_labels is not None:
            diary.emotion_labels = request.emotion_labels

        if request.content_text is not None:
            content_text = request.content_text
            is_encrypted = request.is_encrypted

            # 验证内容哈希（如果用户提供了）
            if request.content_hash:
                computed_hash = compute_content_hash(request.content_text)
                if not hmac.compare_digest(computed_hash, request.content_hash):
                    raise AppError(
                        code=ErrorCode.VALIDATION_ERROR,
                        message="内容哈希校验失败",
                        status_code=400,
                    )

            if not request.is_encrypted:
                # 内容未加密，根据同步模式处理
                storage_result = prepare_diary_for_storage(
                    content_text,
                    is_cloud_sync=is_cloud_sync,
                    client_encrypted=False,
                )
                content_text = storage_result["content"]
                is_encrypted = storage_result["is_encrypted"]

            diary.content_text = content_text
            diary.content_hash = request.content_hash or compute_content_hash(request.content_text)

        diary.updated_at = datetime.now(timezone.utc)

        db.add(diary)
        await db.commit()
        await db.refresh(diary)

        logger.info("日记已更新: user_id=%s, diary_id=%s", user_id, diary_id)

        return self._convert_to_response(diary, is_cloud_sync=is_cloud_sync)

    async def delete_diary(
        self,
        user_id: str,
        diary_id: str,
        db: AsyncSession,
    ) -> None:
        """删除单条日记（软删除）。

        Args:
            user_id: 用户ID
            diary_id: 日记ID
            db: 数据库会话
        """
        diary = await self._get_diary_by_id(user_id, diary_id, db)

        # 软删除
        diary.deleted_at = datetime.now(timezone.utc)
        diary.updated_at = datetime.now(timezone.utc)

        db.add(diary)
        await db.commit()

        logger.info("日记已删除: user_id=%s, diary_id=%s", user_id, diary_id)

    async def delete_all_diaries(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> DeleteAllResponse:
        """删除全部日记（软删除）。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            删除结果响应
        """
        # 统计待删除数量
        count_stmt = (
            select(func.count())
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
            )
        )
        count_result = await db.execute(count_stmt)
        deleted_count = count_result.scalar() or 0

        if deleted_count == 0:
            return DeleteAllResponse(deleted_count=0, message="没有可删除的日记")

        # 批量软删除
        now = datetime.now(timezone.utc)
        stmt = (
            update(EmotionDiary)
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
            )
            .values(deleted_at=now, updated_at=now)
        )
        await db.execute(stmt)
        await db.commit()

        logger.warning("用户删除全部日记: user_id=%s, count=%d", user_id, deleted_count)

        return DeleteAllResponse(
            deleted_count=deleted_count,
            message=f"已删除 {deleted_count} 条日记",
        )

    # -----------------------------------------------------------------------
    # 隐私同意管理
    # -----------------------------------------------------------------------

    async def get_privacy_consent(
        self,
        user_id: str,
    ) -> PrivacyConsentResponse:
        """获取隐私同意状态。

        Args:
            user_id: 用户ID

        Returns:
            隐私同意状态响应
        """
        key = _privacy_consent_key(user_id)
        consent_data = await self._redis.get(key)

        if consent_data is None:
            return PrivacyConsentResponse(
                has_consented=False,
                consented_at=None,
                sync_mode=SyncMode.LOCAL_ONLY,
            )

        # 解析存储的同意数据
        if isinstance(consent_data, bytes):
            consent_data = consent_data.decode("utf-8")

        try:
            data = json.loads(consent_data)
            sync_mode = SyncMode(data.get("sync_mode", SyncMode.LOCAL_ONLY.value))
            consented_at_str = data.get("consented_at")
            consented_at = (
                datetime.fromisoformat(consented_at_str)
                if consented_at_str
                else None
            )

            return PrivacyConsentResponse(
                has_consented=True,
                consented_at=consented_at,
                sync_mode=sync_mode,
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("解析隐私同意数据失败: %s", e)
            return PrivacyConsentResponse(
                has_consented=False,
                consented_at=None,
                sync_mode=SyncMode.LOCAL_ONLY,
            )

    async def set_privacy_consent(
        self,
        user_id: str,
        request: PrivacyConsentRequest,
    ) -> PrivacyConsentResponse:
        """设置隐私同意。

        Args:
            user_id: 用户ID
            request: 同意请求

        Returns:
            更新后的隐私同意状态
        """
        key = _privacy_consent_key(user_id)
        now = datetime.now(timezone.utc)

        consent_data = {
            "sync_mode": request.sync_mode.value,
            "consented_at": now.isoformat(),
        }

        # 存储到 Redis（永久保存）
        await self._redis.set(key, json.dumps(consent_data))

        logger.info(
            "用户同意隐私声明: user_id=%s, sync_mode=%s",
            user_id,
            request.sync_mode.value,
        )

        return PrivacyConsentResponse(
            has_consented=True,
            consented_at=now,
            sync_mode=request.sync_mode,
        )

    # -----------------------------------------------------------------------
    # 同步设置管理
    # -----------------------------------------------------------------------

    async def get_sync_settings(
        self,
        user_id: str,
    ) -> SyncSettingsResponse:
        """获取同步设置。

        Args:
            user_id: 用户ID

        Returns:
            同步设置响应
        """
        # 先检查隐私同意
        privacy = await self.get_privacy_consent(user_id)
        if not privacy.has_consented:
            # 未同意隐私声明，返回默认设置
            return SyncSettingsResponse(
                sync_mode=SyncMode.LOCAL_ONLY,
                last_sync_at=None,
                sync_device_count=0,
                encryption_enabled=True,
            )

        # 获取同步设置
        key = _sync_settings_key(user_id)
        settings_data = await self._redis.get(key)

        if settings_data is None:
            # 使用隐私同意时的设置
            return SyncSettingsResponse(
                sync_mode=privacy.sync_mode,
                last_sync_at=None,
                sync_device_count=0,
                encryption_enabled=True,
            )

        if isinstance(settings_data, bytes):
            settings_data = settings_data.decode("utf-8")

        try:
            data = json.loads(settings_data)
            sync_mode = SyncMode(data.get("sync_mode", privacy.sync_mode.value))
            last_sync_at_str = data.get("last_sync_at")
            last_sync_at = (
                datetime.fromisoformat(last_sync_at_str)
                if last_sync_at_str
                else None
            )

            return SyncSettingsResponse(
                sync_mode=sync_mode,
                last_sync_at=last_sync_at,
                sync_device_count=data.get("sync_device_count", 0),
                encryption_enabled=True,
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("解析同步设置失败: %s", e)
            return SyncSettingsResponse(
                sync_mode=privacy.sync_mode,
                last_sync_at=None,
                sync_device_count=0,
                encryption_enabled=True,
            )

    async def update_sync_settings(
        self,
        user_id: str,
        request: SyncSettingsUpdateRequest,
    ) -> SyncSettingsResponse:
        """更新同步设置。

        Args:
            user_id: 用户ID
            request: 更新请求

        Returns:
            更新后的同步设置
        """
        # 检查隐私同意
        privacy = await self.get_privacy_consent(user_id)
        if not privacy.has_consented:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="请先同意隐私声明",
                status_code=403,
            )

        key = _sync_settings_key(user_id)

        # 获取现有设置
        current = await self.get_sync_settings(user_id)

        settings_data = {
            "sync_mode": request.sync_mode.value,
            "last_sync_at": current.last_sync_at.isoformat() if current.last_sync_at else None,
            "sync_device_count": current.sync_device_count,
        }

        await self._redis.set(key, json.dumps(settings_data))

        logger.info(
            "用户更新同步设置: user_id=%s, sync_mode=%s",
            user_id,
            request.sync_mode.value,
        )

        return SyncSettingsResponse(
            sync_mode=request.sync_mode,
            last_sync_at=current.last_sync_at,
            sync_device_count=current.sync_device_count,
            encryption_enabled=True,
        )

    # -----------------------------------------------------------------------
    # 日记导出
    # -----------------------------------------------------------------------

    async def export_diaries(
        self,
        user_id: str,
        request: ExportRequest,
        db: AsyncSession,
    ) -> ExportResponse:
        """导出日记。

        Args:
            user_id: 用户ID
            request: 导出请求
            db: 数据库会话

        Returns:
            导出结果响应
        """
        # 获取同步模式
        sync_mode = await self._get_user_sync_mode(user_id)
        is_cloud_sync = sync_mode == SyncMode.CLOUD_SYNC

        # 构建查询条件
        conditions = [
            EmotionDiary.user_id == user_id,
            EmotionDiary.deleted_at.is_(None),
        ]

        if request.start_date:
            conditions.append(EmotionDiary.record_date >= request.start_date)
        if request.end_date:
            conditions.append(EmotionDiary.record_date <= request.end_date)

        # 查询日记
        stmt = (
            select(EmotionDiary)
            .where(*conditions)
            .order_by(EmotionDiary.record_date.asc(), EmotionDiary.created_at.asc())
        )
        result = await db.execute(stmt)
        diaries = result.scalars().all()

        record_count = len(diaries)

        if record_count == 0:
            # 返回空导出
            task_id = str(uuid.uuid4())
            download_url = f"/api/v1/diaries/export/{task_id}/download"
            return ExportResponse(
                download_url=download_url,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                file_format=request.format.value,
                record_count=0,
            )

        # 准备导出数据
        export_data = []
        for diary in diaries:
            diary_dict = {
                "id": diary.id,
                "emotion_tone": diary.emotion_tone,
                "emotion_labels": diary.emotion_labels,
                "content_text": self._decrypt_content(diary, is_cloud_sync) if request.include_encrypted else None,
                "record_date": str(diary.record_date),
                "created_at": diary.created_at.isoformat(),
                "updated_at": diary.updated_at.isoformat(),
                "is_zero_record": not diary.content_text or len(diary.content_text.strip()) == 0,
            }

            # 添加色调元数据
            if diary.emotion_tone:
                diary_dict["tone_meta"] = EMOTION_TONE_META.get(diary.emotion_tone)

            export_data.append(diary_dict)

        # 根据格式生成文件
        task_id = str(uuid.uuid4())

        if request.format == ExportFormat.JSON:
            file_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            file_extension = "json"
        else:
            # PDF 格式 - 简化实现，实际项目应使用专门的 PDF 库
            file_content = self._generate_pdf_content(export_data)
            file_extension = "pdf"

        # 存储导出文件（临时存储到 Redis，24 小时有效）
        export_key = _export_task_key(task_id)
        await self._redis.setex(
            export_key,
            24 * 60 * 60,
            json.dumps({
                "content": file_content,
                "format": file_extension,
                "user_id": user_id,
            }),
        )

        download_url = f"/api/v1/diaries/export/{task_id}/download"

        logger.info(
            "日记导出完成: user_id=%s, format=%s, count=%d",
            user_id,
            request.format.value,
            record_count,
        )

        return ExportResponse(
            download_url=download_url,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            file_format=request.format.value,
            record_count=record_count,
        )

    # -----------------------------------------------------------------------
    # 统计相关
    # -----------------------------------------------------------------------

    async def get_stats(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> DiaryStatsResponse:
        """获取日记统计。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            统计响应
        """
        # 总记录数
        total_stmt = (
            select(func.count())
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
            )
        )
        total_result = await db.execute(total_stmt)
        total_records = total_result.scalar() or 0

        # 已记录天数（去重日期）
        days_stmt = (
            select(func.count(func.distinct(EmotionDiary.record_date)))
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
            )
        )
        days_result = await db.execute(days_stmt)
        total_days = days_result.scalar() or 0

        # 0 字记录数（内容为空）
        zero_stmt = (
            select(func.count())
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
                or_(
                    EmotionDiary.content_text.is_(None),
                    EmotionDiary.content_text == "",
                ),
            )
        )
        zero_result = await db.execute(zero_stmt)
        zero_record_count = zero_result.scalar() or 0

        # 有效样本数（用于周报分析）= 总记录数 - 0 字记录数
        valid_sample_count = total_records - zero_record_count

        # 情绪分布统计
        distribution_stmt = (
            select(
                EmotionDiary.emotion_tone,
                func.count().label("count"),
            )
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
                EmotionDiary.emotion_tone.isnot(None),
            )
            .group_by(EmotionDiary.emotion_tone)
        )
        dist_result = await db.execute(distribution_stmt)
        emotion_distribution = {
            row.emotion_tone: row.count
            for row in dist_result.all()
        }

        return DiaryStatsResponse(
            total_records=total_records,
            total_days=total_days,
            zero_record_count=zero_record_count,
            valid_sample_count=valid_sample_count,
            emotion_distribution=emotion_distribution,
        )

    # -----------------------------------------------------------------------
    # 内部方法
    # -----------------------------------------------------------------------

    async def _get_diary_by_id(
        self,
        user_id: str,
        diary_id: str,
        db: AsyncSession,
    ) -> EmotionDiary:
        """获取日记（内部方法，带权限检查）。

        Args:
            user_id: 用户ID
            diary_id: 日记ID
            db: 数据库会话

        Returns:
            日记 ORM 对象

        Raises:
            AppError: 日记不存在或无权限时抛出
        """
        stmt = (
            select(EmotionDiary)
            .where(
                EmotionDiary.id == diary_id,
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
            )
        )
        result = await db.execute(stmt)
        diary = result.scalar_one_or_none()

        if diary is None:
            raise AppError(
                code=ErrorCode.DIARY_NOT_FOUND,
                message="日记不存在或无权限访问",
                status_code=404,
            )

        return diary

    async def _get_user_sync_mode(
        self,
        user_id: str,
    ) -> SyncMode:
        """获取用户同步模式。

        Args:
            user_id: 用户ID

        Returns:
            同步模式
        """
        privacy = await self.get_privacy_consent(user_id)
        if not privacy.has_consented:
            return SyncMode.LOCAL_ONLY

        settings = await self.get_sync_settings(user_id)
        return settings.sync_mode

    def _convert_to_response(
        self,
        diary: EmotionDiary,
        *,
        is_cloud_sync: bool = False,
    ) -> DiaryResponse:
        """将 ORM 对象转换为响应模型。

        Args:
            diary: 日记 ORM 对象
            is_cloud_sync: 是否云端同步模式

        Returns:
            日记响应模型
        """
        # 判断是否为 0 字记录
        content = self._decrypt_content(diary, is_cloud_sync)
        is_zero_record = not content or len(content.strip()) == 0

        return DiaryResponse(
            id=diary.id,
            emotion_tone=diary.emotion_tone,
            emotion_labels=diary.emotion_labels,
            content_text=content,
            record_date=diary.record_date,
            is_synced=diary.is_synced,
            is_encrypted=is_encrypted_content(diary.content_text) if diary.content_text else False,
            created_at=diary.created_at,
            updated_at=diary.updated_at,
            is_zero_record=is_zero_record,
        )

    def _decrypt_content(
        self,
        diary: EmotionDiary,
        is_cloud_sync: bool,
    ) -> str | None:
        """解密日记内容。

        云端同步模式下，如果内容已加密，返回密文（需客户端解密）。
        本地模式下，使用服务端密钥解密。

        Args:
            diary: 日记 ORM 对象
            is_cloud_sync: 是否云端同步模式

        Returns:
            解密后的内容或密文
        """
        if not diary.content_text:
            return None

        if is_cloud_sync and is_encrypted_content(diary.content_text):
            # 云端同步的加密内容，返回密文（客户端解密）
            return diary.content_text

        # 本地存储的加密内容，服务端解密
        try:
            return decrypt_content_server_side(diary.content_text)
        except ValueError:
            # 解密失败，返回原内容
            return diary.content_text

    def _generate_pdf_content(
        self,
        export_data: list[dict],
    ) -> str:
        """生成 PDF 内容（简化版本）。

        实际项目应使用 reportlab 或 weasyprint 等专业库。

        Args:
            export_data: 导出数据列表

        Returns:
            PDF 文件内容（Base64 编码）
        """
        # 这里生成一个简单的文本格式
        # 实际项目应使用专业的 PDF 生成库
        lines = ["情绪日记导出", "=" * 50, ""]

        for diary in export_data:
            lines.append(f"日期: {diary.get('record_date', 'N/A')}")
            lines.append(f"情绪色调: {diary.get('emotion_tone', 'N/A')}")

            tone_meta = diary.get('tone_meta')
            if tone_meta:
                lines.append(f"色调含义: {tone_meta.get('meaning', 'N/A')}")

            labels = diary.get('emotion_labels')
            if labels:
                lines.append(f"情绪标签: {', '.join(labels)}")

            content = diary.get('content_text')
            if content:
                lines.append(f"内容: {content}")

            lines.append("-" * 30)
            lines.append("")

        # 返回文本内容（实际应为 PDF 二进制）
        return "\n".join(lines)
