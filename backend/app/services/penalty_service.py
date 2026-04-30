"""处罚梯度服务。

实现 modules_design.md 7.4 规定的处罚梯度机制：

处罚梯度表：
| 违规程度 | 首次 | 二次 | 三次 |
|---------|------|------|------|
| 轻微（消息过频） | 速率限制+警告 | 禁用24小时 | 禁用7天 |
| 中等（诱导引流） | 禁用24小时+警告 | 禁用7天 | 永久封禁 |
| 严重（性骚扰/PUA） | 永久封禁 | 永久封禁+设备标记 | 同左 |

功能：
- 记录违规行为
- 计算处罚梯度（根据违规次数和程度）
- 执行处罚（更新用户状态）
- 支持申诉处理
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.penalty import (
    DeviceBan,
    PenaltyRecord,
    PenaltyType,
    PENALTY_DURATION_HOURS,
    PENALTY_GRADIENT,
    ViolationSeverity,
    ViolationType,
)
from ..models.user import User

logger = logging.getLogger(__name__)


class PenaltyService:
    """处罚梯度服务。

    提供处罚记录、梯度计算、处罚执行和申诉处理等功能。

    使用示例：
        service = PenaltyService(db)

        # 记录违规并自动处罚
        result = await service.record_violation(
            user_id=user_id,
            violation_type=ViolationType.PROMOTION_DETECTED,
            evidence={"message_id": "xxx", "content": "..."},
        )
    """

    def __init__(self, db: AsyncSession) -> None:
        """初始化处罚服务。

        Args:
            db: 数据库会话
        """
        self._db = db

    async def get_violation_count(
        self,
        user_id: str,
        violation_type: ViolationType,
    ) -> int:
        """获取用户特定违规类型的累计次数。

        Args:
            user_id: 用户ID
            violation_type: 违规类型

        Returns:
            累计违规次数（包含已过期但未删除的记录）
        """
        stmt = select(func.count(PenaltyRecord.id)).where(
            and_(
                PenaltyRecord.user_id == user_id,
                PenaltyRecord.violation_type == violation_type.value,
            )
        )
        result = await self._db.execute(stmt)
        count = result.scalar() or 0
        return count

    async def get_active_penalty(
        self,
        user_id: str,
    ) -> PenaltyRecord | None:
        """获取用户当前生效的处罚。

        Args:
            user_id: 用户ID

        Returns:
            当前生效的处罚记录，如果没有则返回 None
        """
        now = datetime.now(timezone.utc)
        stmt = select(PenaltyRecord).where(
            and_(
                PenaltyRecord.user_id == user_id,
                PenaltyRecord.is_active == True,
                PenaltyRecord.expires_at.is_(None) | (PenaltyRecord.expires_at > now),
            )
        ).order_by(PenaltyRecord.created_at.desc()).limit(1)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    def _determine_severity(
        self,
        violation_type: ViolationType,
    ) -> ViolationSeverity:
        """根据违规类型确定违规程度。

        Args:
            violation_type: 违规类型

        Returns:
            违规程度
        """
        # 轻微违规类型
        minor_types = [
            ViolationType.MESSAGE_RATE_EXCEEDED,
            ViolationType.FRIEND_REQUEST_EXCEEDED,
            ViolationType.COMMENT_RATE_EXCEEDED,
        ]

        # 中等违规类型
        moderate_types = [
            ViolationType.PROMOTION_DETECTED,
            ViolationType.CONTACT_INFO_INDUCED,
            ViolationType.FAKE_CONTENT,
        ]

        # 严重违规类型
        severe_types = [
            ViolationType.SEXUAL_HARASSMENT,
            ViolationType.PUA_BEHAVIOR,
            ViolationType.FRAUD_ATTEMPT,
            ViolationType.VIOLENCE_THREAT,
        ]

        if violation_type in minor_types:
            return ViolationSeverity.MINOR
        elif violation_type in moderate_types:
            return ViolationSeverity.MODERATE
        elif violation_type in severe_types:
            return ViolationSeverity.SEVERE
        else:
            # 默认为中等
            return ViolationSeverity.MODERATE

    def _calculate_penalty(
        self,
        severity: ViolationSeverity,
        violation_count: int,
    ) -> PenaltyType:
        """根据违规程度和次数计算处罚类型。

        Args:
            severity: 违规程度
            violation_count: 累计违规次数

        Returns:
            处罚类型
        """
        gradient = PENALTY_GRADIENT.get(severity, {})
        # 超过3次按3次处理
        count = min(violation_count, 3)
        return gradient.get(count, PenaltyType.BAN_PERMANENT)

    def _calculate_expiry(
        self,
        penalty_type: PenaltyType,
    ) -> datetime | None:
        """计算处罚结束时间。

        Args:
            penalty_type: 处罚类型

        Returns:
            处罚结束时间，永久处罚返回 None
        """
        hours = PENALTY_DURATION_HOURS.get(penalty_type)
        if hours is None:
            return None
        return datetime.now(timezone.utc) + timedelta(hours=hours)

    async def record_violation(
        self,
        user_id: str,
        violation_type: ViolationType,
        reason: str | None = None,
        evidence: dict[str, Any] | None = None,
        auto_execute: bool = True,
    ) -> dict[str, Any]:
        """记录违规行为并自动计算处罚。

        Args:
            user_id: 用户ID
            violation_type: 违规类型
            reason: 违规原因描述
            evidence: 证据（如消息ID、内容等）
            auto_execute: 是否自动执行处罚

        Returns:
            处理结果，包含处罚记录和处罚类型信息
        """
        # 1. 确定违规程度
        severity = self._determine_severity(violation_type)

        # 2. 获取累计违规次数（包含本次）
        current_count = await self.get_violation_count(user_id, violation_type)
        new_count = current_count + 1

        # 3. 计算处罚类型
        penalty_type = self._calculate_penalty(severity, new_count)

        # 4. 计算处罚结束时间
        expires_at = self._calculate_expiry(penalty_type)

        # 5. 创建处罚记录
        record = PenaltyRecord(
            user_id=user_id,
            violation_type=violation_type.value,
            violation_severity=severity.value,
            penalty_type=penalty_type.value,
            penalty_count=new_count,
            reason=reason or f"检测到违规行为: {violation_type.value}",
            evidence=json.dumps(evidence) if evidence else None,
            expires_at=expires_at,
            is_active=True,
        )

        self._db.add(record)
        await self._db.flush()

        logger.warning(
            "[PenaltyService] 记录违规，用户: %s, 类型: %s, 累计次数: %d, "
            "处罚类型: %s, 结束时间: %s",
            user_id, violation_type.value, new_count,
            penalty_type.value, expires_at or "永久",
        )

        result = {
            "record_id": record.id,
            "violation_type": violation_type.value,
            "violation_severity": severity.value,
            "penalty_count": new_count,
            "penalty_type": penalty_type.value,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_permanent": expires_at is None,
        }

        # 6. 自动执行处罚
        if auto_execute:
            execution_result = await self._execute_penalty(
                user_id, penalty_type, expires_at
            )
            result["execution"] = execution_result

        return result

    async def _execute_penalty(
        self,
        user_id: str,
        penalty_type: PenaltyType,
        expires_at: datetime | None,
    ) -> dict[str, Any]:
        """执行处罚（更新用户状态）。

        Args:
            user_id: 用户ID
            penalty_type: 处罚类型
            expires_at: 处罚结束时间

        Returns:
            执行结果
        """
        # 查询用户
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            logger.error("[PenaltyService] 用户不存在: %s", user_id)
            return {"success": False, "error": "用户不存在"}

        # 根据处罚类型更新用户状态
        is_ban = penalty_type in [
            PenaltyType.BAN_24H,
            PenaltyType.BAN_7D,
            PenaltyType.BAN_PERMANENT,
            PenaltyType.BAN_PERMANENT_DEVICE,
        ]

        if is_ban:
            user.is_banned = True
            user.ban_until = expires_at
            user.ban_reason = f"处罚类型: {penalty_type.value}"

            logger.warning(
                "[PenaltyService] 执行封禁，用户: %s, 类型: %s, "
                "结束时间: %s",
                user_id, penalty_type.value, expires_at or "永久",
            )

        # 对于设备标记类型的处罚，需要额外处理
        if penalty_type == PenaltyType.BAN_PERMANENT_DEVICE:
            # TODO: 获取用户设备指纹并记录到 device_bans 表
            # 需要从用户登录日志或请求中获取设备指纹
            logger.warning(
                "[PenaltyService] 需要设备标记，用户: %s（待获取设备指纹）",
                user_id
            )

        await self._db.flush()

        return {
            "success": True,
            "is_banned": is_ban,
            "ban_until": expires_at.isoformat() if expires_at else None,
        }

    async def expire_penalty(
        self,
        user_id: str,
    ) -> bool:
        """检查并过期已结束的处罚。

        Args:
            user_id: 用户ID

        Returns:
            是否有过处罚被过期
        """
        now = datetime.now(timezone.utc)

        # 更新处罚记录状态
        stmt = select(PenaltyRecord).where(
            and_(
                PenaltyRecord.user_id == user_id,
                PenaltyRecord.is_active == True,
                PenaltyRecord.expires_at <= now,
                PenaltyRecord.expires_at.is_not(None),
            )
        )
        result = await self._db.execute(stmt)
        expired_records = result.scalars().all()

        for record in expired_records:
            record.is_active = False
            logger.info(
                "[PenaltyService] 处罚过期，用户: %s, 处罚ID: %s",
                user_id, record.id
            )

        # 更新用户封禁状态
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()

        if user and user.is_banned and user.ban_until:
            if user.ban_until <= now:
                user.is_banned = False
                user.ban_until = None
                user.ban_reason = None
                logger.info(
                    "[PenaltyService] 用户封禁解除，用户: %s",
                    user_id
                )

        await self._db.flush()

        return len(expired_records) > 0

    async def submit_appeal(
        self,
        penalty_id: str,
        user_id: str,
        appeal_reason: str,
    ) -> dict[str, Any]:
        """提交申诉。

        Args:
            penalty_id: 处罚记录ID
            user_id: 用户ID
            appeal_reason: 申诉理由

        Returns:
            申诉结果
        """
        stmt = select(PenaltyRecord).where(
            and_(
                PenaltyRecord.id == penalty_id,
                PenaltyRecord.user_id == user_id,
            )
        )
        result = await self._db.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            return {"success": False, "error": "处罚记录不存在"}

        if record.appeal_status is not None:
            return {"success": False, "error": "已提交申诉"}

        record.appeal_status = "pending"
        record.appeal_reason = appeal_reason

        await self._db.flush()

        logger.info(
            "[PenaltyService] 提交申诉，处罚ID: %s, 用户: %s",
            penalty_id, user_id
        )

        return {
            "success": True,
            "appeal_status": "pending",
            "message": "申诉已提交，等待审核",
        }

    async def review_appeal(
        self,
        penalty_id: str,
        admin_id: str,
        approved: bool,
        review_note: str | None = None,
    ) -> dict[str, Any]:
        """审核申诉。

        Args:
            penalty_id: 处罚记录ID
            admin_id: 管理员ID
            approved: 是否通过申诉
            review_note: 审核备注

        Returns:
            审核结果
        """
        stmt = select(PenaltyRecord).where(PenaltyRecord.id == penalty_id)
        result = await self._db.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            return {"success": False, "error": "处罚记录不存在"}

        if record.appeal_status != "pending":
            return {"success": False, "error": "申诉状态不正确"}

        # 更新申诉状态
        record.appeal_status = "approved" if approved else "rejected"
        record.reviewed_by = admin_id
        record.reviewed_at = datetime.now(timezone.utc)

        # 如果申诉通过，解除处罚
        if approved:
            record.is_active = False

            # 更新用户封禁状态
            stmt = select(User).where(User.id == record.user_id)
            result = await self._db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.is_banned = False
                user.ban_until = None
                user.ban_reason = None

            logger.info(
                "[PenaltyService] 申诉通过，处罚解除，处罚ID: %s, 用户: %s",
                penalty_id, record.user_id
            )
        else:
            logger.info(
                "[PenaltyService] 申诉驳回，处罚ID: %s, 用户: %s",
                penalty_id, record.user_id
            )

        await self._db.flush()

        return {
            "success": True,
            "appeal_approved": approved,
            "penalty_revoked": approved,
        }

    async def check_device_banned(
        self,
        device_fingerprint: str,
    ) -> bool:
        """检查设备是否被封禁。

        Args:
            device_fingerprint: 设备指纹

        Returns:
            是否被封禁
        """
        stmt = select(DeviceBan).where(
            DeviceBan.device_fingerprint == device_fingerprint
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_device_ban(
        self,
        device_fingerprint: str,
        user_id: str,
        ban_reason: str,
        penalty_id: str | None = None,
    ) -> DeviceBan:
        """添加设备封禁。

        Args:
            device_fingerprint: 设备指纹
            user_id: 用户ID
            ban_reason: 封禁原因
            penalty_id: 关联的处罚记录ID

        Returns:
            设备封禁记录
        """
        device_ban = DeviceBan(
            device_fingerprint=device_fingerprint,
            user_id=user_id,
            ban_reason=ban_reason,
            related_penalty_id=penalty_id,
        )

        self._db.add(device_ban)
        await self._db.flush()

        logger.warning(
            "[PenaltyService] 设备封禁，指纹: %s, 用户: %s",
            device_fingerprint, user_id
        )

        return device_ban