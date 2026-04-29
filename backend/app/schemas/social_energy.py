"""社交能量相关的 Pydantic Schema 定义。

提供社交能量查询和操作的请求/响应模型。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 能量状态响应
# ---------------------------------------------------------------------------

class SocialEnergyResponse(BaseSchema):
    """社交能量状态响应模型。"""

    energy: float = Field(..., ge=0, le=100, description="当前能量值（0-100）")
    percentage: str = Field(..., description="百分比显示，如 '50%'")
    status: str = Field(..., description="状态描述")
    can_rest: bool = Field(..., description="是否可以主动休息")
    rest_cooldown_remaining: int = Field(0, ge=0, description="休息冷却剩余秒数")
    updated_at: str | None = Field(None, description="最后更新时间")


# ---------------------------------------------------------------------------
# 主动休息请求/响应
# ---------------------------------------------------------------------------

class RestRequest(BaseSchema):
    """主动休息请求模型（空请求，仅用于文档）。"""

    pass


class RestResponse(BaseSchema):
    """主动休息响应模型。"""

    old_energy: float = Field(..., description="休息前能量值")
    new_energy: float = Field(..., description="休息后能量值")
    change: float = Field(..., description="能量变化量")
    message: str = Field(..., description="提示消息")
    cooldown_until: float = Field(..., description="冷却结束时间戳")
