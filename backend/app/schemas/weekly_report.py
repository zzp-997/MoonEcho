"""情绪周报相关请求/响应模型。

包含周报生成、获取、缓存等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 周报响应模型
# ---------------------------------------------------------------------------

class WeeklyReportResponse(BaseSchema):
    """周报响应模型（五段式结构）。"""

    id: str = Field(..., description="周报ID")
    week_start_date: date = Field(..., description="本周起始日期（周一）")
    week_end_date: date = Field(..., description="本周结束日期（周日）")
    title: str | None = Field(None, description="动态标题，如'这周像一场漫长的周三'")
    story_line: str | None = Field(None, description="情绪故事线，叙事体描述本周情绪走势")
    keywords: list[str] | None = Field(None, description="情绪关键词列表")
    insight: str | None = Field(None, description="一句看见，提炼核心感受")
    suggestion: str | None = Field(None, description="温和建议，措辞谨慎")
    outlook: str | None = Field(None, description="下周展望，一句话收束")
    diary_count: int = Field(default=0, description="本周分析日记数量")
    created_at: datetime = Field(..., description="生成时间")

    # 状态标记
    is_empty: bool = Field(
        default=False,
        description="是否为空周报（本周无有效日记）",
    )
    is_cached: bool = Field(
        default=False,
        description="是否来自缓存",
    )


class EmptyWeeklyReportResponse(BaseSchema):
    """空周报响应模型（本周无有效日记）。"""

    week_start_date: date = Field(..., description="本周起始日期（周一）")
    week_end_date: date = Field(..., description="本周结束日期（周日）")
    is_empty: bool = Field(default=True, description="是否为空周报")
    message: str = Field(
        default="本周还没有记录足够的日记，无法生成周报。",
        description="提示信息",
    )
    diary_count: int = Field(default=0, description="本周有效日记数量")


# ---------------------------------------------------------------------------
# 周报历史响应模型
# ---------------------------------------------------------------------------

class WeeklyReportHistoryResponse(BaseSchema):
    """周报历史列表响应模型。"""

    data: list[WeeklyReportResponse] = Field(
        default_factory=list,
        description="周报列表",
    )
    pagination: dict[str, Any] = Field(..., description="分页信息")


# ---------------------------------------------------------------------------
# 周报生成请求模型
# ---------------------------------------------------------------------------

class WeeklyReportGenerateRequest(BaseSchema):
    """周报生成请求模型（内部使用）。"""

    user_id: str = Field(..., description="用户ID")
    week_start_date: date = Field(..., description="本周起始日期（周一）")
    force_refresh: bool = Field(
        default=False,
        description="是否强制重新生成",
    )