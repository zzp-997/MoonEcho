"""社交能量服务模块。

管理用户社交能量值，包括：
- 能量消耗与恢复计算
- 能量状态查询
- 主动休息恢复能量
- 能量变化事件触发

社交能量计算规则：
- 发送消息：-5%
- 接收消息并回复：-3%
- 发起好友申请：-10%
- 发布动态并收到互动：+10%
- 收到共鸣/点赞：+5%
- AI朋友对话：+15%

边界规则：
- 能量范围：0% - 100%
- 降到0%时：提示"社交能量耗尽，建议休息"，但不强制限制操作
- 达到100%时：不再增加，显示"社交能量满满"
- 每日重置：凌晨0点恢复至50%基准值（定时任务实现）
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 能量变化值（百分比）
ENERGY_CHANGE_SEND_MESSAGE = Decimal("-5")      # 发送消息：-5%
ENERGY_CHANGE_REPLY_MESSAGE = Decimal("-3")    # 接收消息并回复：-3%
ENERGY_CHANGE_FRIEND_REQUEST = Decimal("-10") # 发起好友申请：-10%
ENERGY_CHANGE_POST_INTERACTION = Decimal("10") # 发布动态并收到互动：+10%
ENERGY_CHANGE_RECEIVE_RESONATE = Decimal("5") # 收到共鸣/点赞：+5%
ENERGY_CHANGE_AI_CHAT = Decimal("15")          # AI朋友对话：+15%

# 能量边界值
ENERGY_MIN = Decimal("0")    # 最小值：0%
ENERGY_MAX = Decimal("100")  # 最大值：100%
ENERGY_DEFAULT = Decimal("50")  # 默认/重置值：50%

# 主动休息恢复量
ENERGY_REST_RECOVERY = Decimal("20")  # 主动休息恢复：+20%

# 休息冷却时间（秒）
REST_COOLDOWN_SECONDS = 3600  # 1小时冷却

# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

def _rest_cooldown_key(user_id: str) -> str:
    """主动休息冷却 Redis 键。"""
    return f"social_energy:rest_cooldown:{user_id}"


# ---------------------------------------------------------------------------
# 社交能量服务类
# ---------------------------------------------------------------------------

class SocialEnergyService:
    """社交能量服务。

    提供社交能量的查询、变更和恢复功能。

    使用示例：
        service = SocialEnergyService(redis_client)
        energy = await service.get_energy(user_id, db)
        await service.consume_energy(user_id, "send_message", db)
    """

    def __init__(self, redis: Any) -> None:
        """初始化社交能量服务。

        Args:
            redis: Redis 客户端（用于冷却时间管理）
        """
        self._redis = redis
        logger.info("[SocialEnergyService] 初始化完成")

    # =========================================================================
    # 能量查询
    # =========================================================================

    async def get_energy(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """获取用户当前社交能量值。

        如果用户没有初始化过能量值，则初始化为默认值 50%。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            能量信息字典，包含：
            - energy: 当前能量值（Decimal）
            - percentage: 百分比显示（如 "50%"）
            - status: 状态描述
            - can_rest: 是否可以主动休息
            - rest_cooldown_remaining: 休息冷却剩余秒数（0表示无冷却）
        """
        # 查询用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 初始化能量值（如果为空）
        if user.social_energy is None:
            user.social_energy = ENERGY_DEFAULT
            user.social_energy_updated_at = datetime.now(timezone.utc)
            await db.flush()

        energy = user.social_energy

        # 检查是否可以主动休息
        can_rest, cooldown_remaining = await self._check_rest_cooldown(user_id)

        # 计算状态描述
        status = self._get_energy_status(energy)

        return {
            "energy": float(energy),
            "percentage": f"{int(energy)}%",
            "status": status,
            "can_rest": can_rest,
            "rest_cooldown_remaining": cooldown_remaining,
            "updated_at": user.social_energy_updated_at.isoformat() if user.social_energy_updated_at else None,
        }

    # =========================================================================
    # 能量消耗
    # =========================================================================

    async def consume_energy(
        self,
        user_id: str,
        action: str,
        db: AsyncSession,
        amount: Decimal | None = None,
    ) -> dict[str, Any]:
        """消耗用户社交能量。

        根据操作类型消耗对应的能量值。如果能量不足，记录警告但不阻止操作。

        Args:
            user_id: 用户ID
            action: 操作类型（send_message/reply_message/friend_request）
            db: 数据库会话
            amount: 自定义消耗量（可选，覆盖默认值）

        Returns:
            消耗结果，包含：
            - old_energy: 消耗前能量值
            - new_energy: 消耗后能量值
            - change: 变化量
            - is_depleted: 是否已耗尽
        """
        # 获取能量变化值
        if amount is not None:
            change = amount
        else:
            change = self._get_energy_change(action)

        # 查询用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 初始化能量值（如果为空）
        if user.social_energy is None:
            user.social_energy = ENERGY_DEFAULT

        old_energy = user.social_energy
        new_energy = self._clamp_energy(old_energy + change)

        # 更新能量值
        user.social_energy = new_energy
        user.social_energy_updated_at = datetime.now(timezone.utc)

        logger.info(
            "[SocialEnergyService] 能量消耗: user_id=%s, action=%s, old=%s, new=%s, change=%s",
            user_id, action, old_energy, new_energy, change,
        )

        # 检查是否耗尽
        is_depleted = new_energy <= ENERGY_MIN

        return {
            "old_energy": float(old_energy),
            "new_energy": float(new_energy),
            "change": float(change),
            "is_depleted": is_depleted,
        }

    # =========================================================================
    # 能量恢复
    # =========================================================================

    async def recover_energy(
        self,
        user_id: str,
        action: str,
        db: AsyncSession,
        amount: Decimal | None = None,
    ) -> dict[str, Any]:
        """恢复用户社交能量。

        根据操作类型恢复对应的能量值。如果能量已满，不再增加。

        Args:
            user_id: 用户ID
            action: 操作类型（post_interaction/receive_resonate/ai_chat）
            db: 数据库会话
            amount: 自定义恢复量（可选，覆盖默认值）

        Returns:
            恢复结果，包含：
            - old_energy: 恢复前能量值
            - new_energy: 恢复后能量值
            - change: 变化量
            - is_full: 是否已满
        """
        # 获取能量变化值
        if amount is not None:
            change = amount
        else:
            change = self._get_energy_change(action)

        # 查询用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                status_code=404,
            )

        # 初始化能量值（如果为空）
        if user.social_energy is None:
            user.social_energy = ENERGY_DEFAULT

        old_energy = user.social_energy
        new_energy = self._clamp_energy(old_energy + change)

        # 更新能量值
        user.social_energy = new_energy
        user.social_energy_updated_at = datetime.now(timezone.utc)

        logger.info(
            "[SocialEnergyService] 能量恢复: user_id=%s, action=%s, old=%s, new=%s, change=%s",
            user_id, action, old_energy, new_energy, change,
        )

        # 检查是否已满
        is_full = new_energy >= ENERGY_MAX

        return {
            "old_energy": float(old_energy),
            "new_energy": float(new_energy),
            "change": float(change),
            "is_full": is_full,
        }

    async def rest_and_recover(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """主动休息恢复能量。

        用户主动点击休息按钮后恢复能量。有冷却时间限制（1小时一次）。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            恢复结果，包含：
            - old_energy: 恢复前能量值
            - new_energy: 恢复后能量值
            - change: 变化量
            - message: 提示消息
            - cooldown_until: 下次可休息时间

        Raises:
            AppError: 冷却期内无法休息
        """
        # 检查冷却时间
        can_rest, cooldown_remaining = await self._check_rest_cooldown(user_id)
        if not can_rest:
            raise AppError(
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message=f"休息冷却中，请在 {cooldown_remaining} 秒后再试",
                status_code=429,
            )

        # 执行恢复
        result = await self.recover_energy(
            user_id=user_id,
            action="rest",
            db=db,
            amount=ENERGY_REST_RECOVERY,
        )

        # 设置冷却时间
        await self._set_rest_cooldown(user_id)

        result["message"] = "休息了一会，感觉好多了~"
        result["cooldown_until"] = datetime.now(timezone.utc).timestamp() + REST_COOLDOWN_SECONDS

        logger.info(
            "[SocialEnergyService] 主动休息恢复: user_id=%s, old=%s, new=%s",
            user_id, result["old_energy"], result["new_energy"],
        )

        return result

    # =========================================================================
    # 内部辅助方法
    # =========================================================================

    def _get_energy_change(self, action: str) -> Decimal:
        """根据操作类型获取能量变化值。

        Args:
            action: 操作类型

        Returns:
            能量变化值（正数为恢复，负数为消耗）
        """
        action_map = {
            "send_message": ENERGY_CHANGE_SEND_MESSAGE,
            "reply_message": ENERGY_CHANGE_REPLY_MESSAGE,
            "friend_request": ENERGY_CHANGE_FRIEND_REQUEST,
            "post_interaction": ENERGY_CHANGE_POST_INTERACTION,
            "receive_resonate": ENERGY_CHANGE_RECEIVE_RESONATE,
            "ai_chat": ENERGY_CHANGE_AI_CHAT,
            "rest": ENERGY_REST_RECOVERY,
        }
        return action_map.get(action, Decimal("0"))

    def _clamp_energy(self, energy: Decimal) -> Decimal:
        """将能量值限制在有效范围内。

        Args:
            energy: 原始能量值

        Returns:
            限制后的能量值
        """
        if energy < ENERGY_MIN:
            return ENERGY_MIN
        if energy > ENERGY_MAX:
            return ENERGY_MAX
        return energy

    def _get_energy_status(self, energy: Decimal) -> str:
        """根据能量值获取状态描述。

        Args:
            energy: 能量值

        Returns:
            状态描述字符串
        """
        if energy <= ENERGY_MIN:
            return "社交能量耗尽，建议休息"
        elif energy >= ENERGY_MAX:
            return "社交能量满满"
        elif energy <= Decimal("20"):
            return "社交能量较低，注意休息"
        elif energy >= Decimal("80"):
            return "社交能量充足"
        else:
            return "正常"

    async def _check_rest_cooldown(self, user_id: str) -> tuple[bool, int]:
        """检查主动休息冷却时间。

        Args:
            user_id: 用户ID

        Returns:
            (是否可以休息, 冷却剩余秒数)
        """
        key = _rest_cooldown_key(user_id)
        try:
            ttl = await self._redis.ttl(key)
            # ttl > 0 表示存在冷却中
            if ttl > 0:
                return False, ttl
            return True, 0
        except Exception as e:
            logger.warning("[SocialEnergyService] 检查冷却时间失败: %s", str(e))
            # Redis 失败时允许操作
            return True, 0

    async def _set_rest_cooldown(self, user_id: str) -> None:
        """设置主动休息冷却时间。

        Args:
            user_id: 用户ID
        """
        key = _rest_cooldown_key(user_id)
        try:
            await self._redis.setex(key, REST_COOLDOWN_SECONDS, "1")
        except Exception as e:
            logger.warning("[SocialEnergyService] 设置冷却时间失败: %s", str(e))


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_social_energy_service(redis: Any) -> SocialEnergyService:
    """创建社交能量服务实例。

    Args:
        redis: Redis 客户端

    Returns:
        SocialEnergyService 实例
    """
    return SocialEnergyService(redis=redis)
