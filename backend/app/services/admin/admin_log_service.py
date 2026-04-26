"""管理员操作日志服务模块。

提供审计日志的记录和查询能力：
- 记录所有管理员操作
- 支持按管理员、操作类型筛选
- 日志永存，不可删除
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin, AdminLog
from app.schemas.admin import AdminLogResponse
from app.schemas.base import PaginatedResponse

logger = logging.getLogger(__name__)


# Redis Key 定义
def _log_queue_key() -> str:
    """日志写入队列 key（异步写入）。"""
    return "admin:log:queue"


class AdminLogService:
    """管理员操作日志服务。

    依赖外部注入：
    - redis: Redis 客户端
    """

    def __init__(self, redis: Any) -> None:
        self._redis = redis

    async def log_action(
        self,
        admin_id: str | None,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """记录管理员操作日志。

        Args:
            admin_id: 管理员ID（登录失败时可能为 None）
            action: 操作类型
            target_type: 操作对象类型
            target_id: 操作对象ID
            details: 操作详情
            ip_address: 客户端IP
            user_agent: 客户端UA

        Returns:
            日志ID
        """
        log_id = uuid4().hex

        # 构造日志数据（存入 Redis 队列，异步写入数据库）
        log_data = {
            "id": log_id,
            "admin_id": admin_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # 先存入 Redis 队列（快速返回）
            await self._redis.lpush(_log_queue_key(), json.dumps(log_data))
        except Exception as e:
            logger.error("写入操作日志到 Redis 失败: %s, 将直接返回 log_id", e)
            # Redis 不可用时的降级策略：返回 log_id，由调用方决定是否同步写入
            # 注意：这种情况下日志可能丢失，建议在关键场景使用 log_action_sync

        return log_id

    async def flush_logs_to_db(self, db: AsyncSession, batch_size: int = 100) -> int:
        """将 Redis 队列中的日志批量写入数据库。

        建议在后台任务中定时调用。

        Args:
            db: 数据库会话
            batch_size: 每批次写入条数

        Returns:
            写入的日志条数
        """
        count = 0
        try:
            for _ in range(batch_size):
                data = await self._redis.rpop(_log_queue_key())
                if data is None:
                    break

                log_data = json.loads(data)
                log = AdminLog(
                    id=log_data["id"],
                    admin_id=log_data.get("admin_id"),
                    action=log_data["action"],
                    target_type=log_data.get("target_type"),
                    target_id=log_data.get("target_id"),
                    details=log_data.get("details"),
                    ip_address=log_data.get("ip_address"),
                    user_agent=log_data.get("user_agent"),
                    created_at=datetime.fromisoformat(log_data["created_at"]),
                )
                db.add(log)
                count += 1

            if count > 0:
                await db.commit()

        except Exception as e:
            logger.error("批量写入操作日志失败: %s", e)
            await db.rollback()

        return count

    async def log_action_sync(
        self,
        db: AsyncSession,
        admin_id: str | None,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        auto_commit: bool = True,
    ) -> str:
        """同步记录管理员操作日志（直接写入数据库）。

        用于关键操作的审计日志记录。

        Args:
            db: 数据库会话
            admin_id: 管理员ID
            action: 操作类型
            target_type: 操作对象类型
            target_id: 操作对象ID
            details: 操作详情
            ip_address: 客户端IP
            user_agent: 客户端UA
            auto_commit: 是否自动提交事务（默认 True）
                - True: 单独提交日志事务
                - False: 不提交，由调用方在完成其他操作后统一提交

        Returns:
            日志ID
        """
        log_id = uuid4().hex
        log = AdminLog(
            id=log_id,
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)

        if auto_commit:
            await db.commit()

        logger.debug("记录操作日志: action=%s, admin_id=%s", action, admin_id)
        return log_id

    async def get_logs(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        admin_id: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> PaginatedResponse[AdminLogResponse]:
        """查询操作日志列表。

        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页条数
            admin_id: 按管理员ID筛选
            action: 按操作类型筛选
            target_type: 按目标类型筛选
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            分页日志列表
        """
        # 构建查询条件
        stmt = select(AdminLog)

        if admin_id:
            stmt = stmt.where(AdminLog.admin_id == admin_id)
        if action:
            stmt = stmt.where(AdminLog.action == action)
        if target_type:
            stmt = stmt.where(AdminLog.target_type == target_type)
        if start_time:
            stmt = stmt.where(AdminLog.created_at >= start_time)
        if end_time:
            stmt = stmt.where(AdminLog.created_at <= end_time)

        # 统计总数（使用 count 函数优化性能）
        count_stmt = select(func.count()).select_from(AdminLog)
        if admin_id:
            count_stmt = count_stmt.where(AdminLog.admin_id == admin_id)
        if action:
            count_stmt = count_stmt.where(AdminLog.action == action)
        if target_type:
            count_stmt = count_stmt.where(AdminLog.target_type == target_type)
        if start_time:
            count_stmt = count_stmt.where(AdminLog.created_at >= start_time)
        if end_time:
            count_stmt = count_stmt.where(AdminLog.created_at <= end_time)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页查询（使用 join 一次性获取管理员用户名）
        stmt = stmt.order_by(desc(AdminLog.created_at))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        # 使用 joinoptions 确保关联加载
        stmt = stmt.join(Admin, AdminLog.admin_id == Admin.id, isouter=True)
        # 同时选择 AdminLog 和 Admin.username
        stmt = stmt.add_columns(Admin.username)

        result = await db.execute(stmt)
        rows = result.all()

        # 转换为响应模型
        data = []
        for row in rows:
            log = row[0]  # AdminLog 对象
            admin_username = row[1]  # Admin.username

            data.append(AdminLogResponse(
                id=log.id,
                admin_id=log.admin_id or "",
                admin_username=admin_username,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            ))

        return PaginatedResponse.create(
            data=data,
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_log_by_id(
        self,
        db: AsyncSession,
        log_id: str,
    ) -> AdminLogResponse | None:
        """获取单条日志详情。

        Args:
            db: 数据库会话
            log_id: 日志ID

        Returns:
            日志详情，不存在返回 None
        """
        stmt = select(AdminLog).where(AdminLog.id == log_id)
        result = await db.execute(stmt)
        log = result.scalar_one_or_none()

        if log is None:
            return None

        # 查询关联的管理员用户名
        admin_stmt = select(Admin.username).where(Admin.id == log.admin_id)
        admin_result = await db.execute(admin_stmt)
        admin_username = admin_result.scalar_one_or_none()

        return AdminLogResponse(
            id=log.id,
            admin_id=log.admin_id or "",
            admin_username=admin_username,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )
