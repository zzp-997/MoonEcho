"""举报管理相关请求/响应模型。

包含 C 端举报提交、管理端举报管理、危机干预、内容管理等接口的 Schema 定义。
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 举报类型枚举
# ---------------------------------------------------------------------------

class ReportType(str, Enum):
    """举报类型枚举。"""
    PORN = "porn"               # 色情低俗
    AD = "ad"                   # 广告引流
    HARASSMENT = "harassment"   # 骚扰
    ABUSE = "abuse"             # 辱骂攻击
    SCAM = "scam"               # 诈骗
    SELF_HARM = "self_harm"     # 自杀自残倾向
    OTHER = "other"             # 其他


class ReportContentType(str, Enum):
    """举报内容类型枚举。"""
    POST = "post"               # 广场动态
    TREEHOLE_POST = "treehole_post"  # 树洞帖子
    COMMENT = "comment"         # 评论
    USER = "user"               # 用户


class ReportStatus(str, Enum):
    """举报状态枚举。"""
    PENDING = "pending"         # 待处理
    PROCESSING = "processing"   # 处理中
    APPROVED = "approved"       # 已通过（举报成立）
    REJECTED = "rejected"       # 已驳回（举报不成立）


class AppealStatus(str, Enum):
    """申诉状态枚举。"""
    PENDING = "pending"         # 待审核
    APPROVED = "approved"       # 申诉通过
    REJECTED = "rejected"       # 申诉驳回


# ---------------------------------------------------------------------------
# C 端举报提交
# ---------------------------------------------------------------------------

class ReportCreateRequest(BaseSchema):
    """举报提交请求模型。"""

    reported_content_type: ReportContentType = Field(
        ...,
        description="举报内容类型：post/treehole_post/comment/user",
    )
    reported_content_id: str | None = Field(
        None,
        description="举报内容ID（举报用户时可为空）",
    )
    reported_user_id: str | None = Field(
        None,
        description="被举报用户ID（可选，系统可自动关联）",
    )
    report_type: ReportType = Field(
        ...,
        description="举报分类：porn/ad/harassment/abuse/scam/self_harm/other",
    )
    reason: str | None = Field(
        None,
        max_length=500,
        description="详细原因（可选，最多500字）",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str | None) -> str | None:
        """验证举报原因，进行 XSS 防护处理。"""
        if v:
            v = v.strip()
            if not v:
                return None
            # XSS 防护：转义 HTML 特殊字符
            v = html.escape(v)
            # 移除潜在的危险字符模式
            # 防止 javascript: 协议
            v = re.sub(r'javascript\s*:', '', v, flags=re.IGNORECASE)
            # 防止 on* 事件处理器
            v = re.sub(r'on\w+\s*=', '', v, flags=re.IGNORECASE)
        return v


class ReportCreateResponse(BaseSchema):
    """举报提交响应模型。"""

    id: str = Field(..., description="举报记录ID")
    status: str = Field(..., description="举报状态")
    message: str = Field(..., description="提示信息")
    created_at: datetime = Field(..., description="创建时间")


# ---------------------------------------------------------------------------
# 管理端举报列表
# ---------------------------------------------------------------------------

class AdminReportListRequest(BaseSchema):
    """举报列表查询请求模型。"""

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")
    status: ReportStatus | None = Field(None, description="状态筛选")
    report_type: ReportType | None = Field(None, description="举报类型筛选")
    content_type: ReportContentType | None = Field(None, description="内容类型筛选")
    reporter_id: str | None = Field(None, description="举报人ID筛选")
    reported_user_id: str | None = Field(None, description="被举报人ID筛选")
    start_time: datetime | None = Field(None, description="创建时间起始")
    end_time: datetime | None = Field(None, description="创建时间截止")
    has_appeal: bool | None = Field(None, description="是否有申诉")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向：asc/desc")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """验证排序字段。"""
        allowed = ["created_at", "updated_at", "processed_at"]
        if v not in allowed:
            raise ValueError(f"排序字段必须是: {allowed}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """验证排序方向。"""
        allowed = ["asc", "desc"]
        if v not in allowed:
            raise ValueError(f"排序方向必须是: {allowed}")
        return v


class ReportContentInfo(BaseSchema):
    """被举报内容信息。"""

    id: str | None = Field(None, description="内容ID")
    type: str = Field(..., description="内容类型")
    content: str | None = Field(None, description="内容文本（脱敏处理）")
    author_id: str | None = Field(None, description="作者ID")
    author_nickname: str | None = Field(None, description="作者昵称")
    created_at: datetime | None = Field(None, description="内容创建时间")
    status: str | None = Field(None, description="内容状态")


class AdminReportListItem(BaseSchema):
    """举报列表项响应模型。"""

    id: str = Field(..., description="举报记录ID")
    reporter_id: str = Field(..., description="举报人ID")
    reporter_nickname: str | None = Field(None, description="举报人昵称")
    reported_user_id: str | None = Field(None, description="被举报人ID")
    reported_user_nickname: str | None = Field(None, description="被举报人昵称")
    reported_content_type: str = Field(..., description="被举报内容类型")
    reported_content_id: str | None = Field(None, description="被举报内容ID")
    report_type: str = Field(..., description="举报分类")
    reason: str | None = Field(None, description="举报原因")
    status: str = Field(..., description="处理状态")
    process_result: str | None = Field(None, description="处理结果")
    processed_by: str | None = Field(None, description="处理人ID")
    processed_by_name: str | None = Field(None, description="处理人姓名")
    processed_at: datetime | None = Field(None, description="处理时间")
    appeal_status: str | None = Field(None, description="申诉状态")
    created_at: datetime = Field(..., description="举报时间")
    # 同一内容举报次数（合并展示）
    same_content_report_count: int = Field(default=1, description="同一内容被举报次数")


class AdminReportDetail(BaseSchema):
    """举报详情响应模型。"""

    id: str = Field(..., description="举报记录ID")
    reporter_id: str = Field(..., description="举报人ID")
    reporter_nickname: str | None = Field(None, description="举报人昵称")
    reporter_phone: str | None = Field(None, description="举报人手机号（脱敏）")
    reported_user_id: str | None = Field(None, description="被举报人ID")
    reported_user_nickname: str | None = Field(None, description="被举报人昵称")
    reported_user_phone: str | None = Field(None, description="被举报人手机号（脱敏）")
    reported_content_type: str = Field(..., description="被举报内容类型")
    reported_content_id: str | None = Field(None, description="被举报内容ID")
    report_type: str = Field(..., description="举报分类")
    reason: str | None = Field(None, description="举报原因")
    status: str = Field(..., description="处理状态")
    process_result: str | None = Field(None, description="处理结果说明")
    processed_by: str | None = Field(None, description="处理人ID")
    processed_by_name: str | None = Field(None, description="处理人姓名")
    processed_at: datetime | None = Field(None, description="处理时间")
    appeal_status: str | None = Field(None, description="申诉状态")
    appeal_reason: str | None = Field(None, description="申诉理由")
    created_at: datetime = Field(..., description="举报时间")
    updated_at: datetime = Field(..., description="更新时间")
    # 被举报内容详情
    content_info: ReportContentInfo | None = Field(None, description="被举报内容详情")
    # 同一内容的举报列表（合并展示）
    related_reports: list[dict] = Field(default_factory=list, description="同一内容的其他举报")


# ---------------------------------------------------------------------------
# 举报处理
# ---------------------------------------------------------------------------

class AdminReportProcessRequest(BaseSchema):
    """举报处理请求模型。"""

    action: str = Field(
        ...,
        description="处理动作：approve（通过）/ reject（驳回）/ ban_user（封禁用户）",
    )
    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="处理原因",
    )
    ban_duration_days: int | None = Field(
        None,
        ge=1,
        description="封禁天数（action=ban_user 时可选，null表示永久封禁）",
    )
    hide_content: bool = Field(
        default=False,
        description="是否隐藏被举报内容",
    )
    notify_reporter: bool = Field(
        default=True,
        description="是否通知举报人",
    )
    notify_reported_user: bool = Field(
        default=False,
        description="是否通知被举报人",
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """验证处理动作。"""
        allowed = ["approve", "reject", "ban_user"]
        if v not in allowed:
            raise ValueError(f"处理动作必须是: {allowed}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """验证处理原因。"""
        v = v.strip()
        if not v:
            raise ValueError("处理原因不能为空")
        return v


class AdminReportProcessResponse(BaseSchema):
    """举报处理响应模型。"""

    id: str = Field(..., description="举报记录ID")
    status: str = Field(..., description="处理后的状态")
    action: str = Field(..., description="执行的动作")
    message: str = Field(..., description="处理结果说明")


# ---------------------------------------------------------------------------
# 申诉管理
# ---------------------------------------------------------------------------

class AdminAppealListRequest(BaseSchema):
    """申诉列表查询请求模型。"""

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")
    appeal_status: AppealStatus | None = Field(None, description="申诉状态筛选")
    start_time: datetime | None = Field(None, description="创建时间起始")
    end_time: datetime | None = Field(None, description="创建时间截止")


class AdminAppealListItem(BaseSchema):
    """申诉列表项响应模型。"""

    id: str = Field(..., description="举报记录ID")
    report_id: str = Field(..., description="举报记录ID")
    reporter_id: str = Field(..., description="举报人ID")
    reporter_nickname: str | None = Field(None, description="举报人昵称")
    reported_user_id: str | None = Field(None, description="被举报人ID")
    reported_user_nickname: str | None = Field(None, description="被举报人昵称")
    report_type: str = Field(..., description="举报分类")
    appeal_status: str | None = Field(None, description="申诉状态")
    appeal_reason: str | None = Field(None, description="申诉理由")
    created_at: datetime = Field(..., description="举报时间")


class AdminAppealReviewRequest(BaseSchema):
    """申诉审核请求模型。"""

    action: str = Field(
        ...,
        description="审核动作：approve（通过）/ reject（驳回）",
    )
    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="审核原因",
    )
    unban_user: bool = Field(
        default=False,
        description="是否解封用户（仅 action=approve 时有效）",
    )
    restore_content: bool = Field(
        default=False,
        description="是否恢复内容（仅 action=approve 时有效）",
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """验证审核动作。"""
        allowed = ["approve", "reject"]
        if v not in allowed:
            raise ValueError(f"审核动作必须是: {allowed}")
        return v


class AdminAppealReviewResponse(BaseSchema):
    """申诉审核响应模型。"""

    id: str = Field(..., description="举报记录ID")
    appeal_status: str = Field(..., description="申诉状态")
    action: str = Field(..., description="执行的动作")
    message: str = Field(..., description="审核结果说明")


# ---------------------------------------------------------------------------
# 危机干预
# ---------------------------------------------------------------------------

class CrisisLevel(str, Enum):
    """危机级别枚举。"""
    LOW = "low"           # 情绪低落
    MEDIUM = "medium"     # 自残意念
    HIGH = "high"         # 紧急信号


class CrisisStatus(str, Enum):
    """危机事件状态枚举。"""
    PENDING = "pending"           # 待处理
    INTERVENING = "intervening"   # 人工介入中
    RESOLVED = "resolved"         # 已解决
    FALSE_POSITIVE = "false_positive"  # 误报


class AdminCrisisListRequest(BaseSchema):
    """危机事件列表查询请求模型。"""

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")
    level: CrisisLevel | None = Field(None, description="危机级别筛选")
    status: CrisisStatus | None = Field(None, description="状态筛选")
    user_id: str | None = Field(None, description="用户ID筛选")
    start_time: datetime | None = Field(None, description="创建时间起始")
    end_time: datetime | None = Field(None, description="创建时间截止")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")


class AdminCrisisListItem(BaseSchema):
    """危机事件列表项响应模型。"""

    id: str = Field(..., description="消息ID")
    user_id: str = Field(..., description="用户ID")
    user_nickname: str | None = Field(None, description="用户昵称")
    user_phone: str | None = Field(None, description="用户手机号（脱敏）")
    conversation_id: str = Field(..., description="会话ID")
    ai_persona: str | None = Field(None, description="AI人设")
    level: str = Field(..., description="危机级别")
    keywords: list[str] = Field(default_factory=list, description="触发关键词")
    status: str = Field(..., description="处理状态")
    resolved_by: str | None = Field(None, description="处理人ID")
    resolved_by_name: str | None = Field(None, description="处理人姓名")
    resolved_at: datetime | None = Field(None, description="处理时间")
    created_at: datetime = Field(..., description="检测时间")


class AdminCrisisDetail(BaseSchema):
    """危机事件详情响应模型。"""

    id: str = Field(..., description="消息ID")
    user_id: str = Field(..., description="用户ID")
    user_nickname: str | None = Field(None, description="用户昵称")
    user_phone: str | None = Field(None, description="用户手机号（脱敏）")
    user_age_range: str | None = Field(None, description="用户年龄段")
    user_is_minor: bool = Field(default=False, description="是否未成年人")
    conversation_id: str = Field(..., description="会话ID")
    ai_persona: str | None = Field(None, description="AI人设")
    message_content: str | None = Field(None, description="触发消息内容（脱敏）")
    level: str = Field(..., description="危机级别")
    keywords: list[str] = Field(default_factory=list, description="触发关键词")
    ai_response: str | None = Field(None, description="AI回复内容")
    status: str = Field(..., description="处理状态")
    resolution_note: str | None = Field(None, description="处理备注")
    resolved_by: str | None = Field(None, description="处理人ID")
    resolved_by_name: str | None = Field(None, description="处理人姓名")
    resolved_at: datetime | None = Field(None, description="处理时间")
    created_at: datetime = Field(..., description="检测时间")
    # 用户历史危机事件统计
    user_crisis_history: dict = Field(default_factory=dict, description="用户危机历史统计")


class AdminCrisisResolveRequest(BaseSchema):
    """危机事件处理请求模型。"""

    status: str = Field(
        ...,
        description="处理状态：resolved/false_positive",
    )
    note: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="处理备注",
    )
    notify_user: bool = Field(
        default=False,
        description="是否联系用户（高危情况建议联系）",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """验证处理状态。"""
        allowed = ["resolved", "false_positive"]
        if v not in allowed:
            raise ValueError(f"处理状态必须是: {allowed}")
        return v


class AdminCrisisResolveResponse(BaseSchema):
    """危机事件处理响应模型。"""

    id: str = Field(..., description="消息ID")
    status: str = Field(..., description="处理状态")
    message: str = Field(..., description="处理结果说明")


# ---------------------------------------------------------------------------
# 内容管理
# ---------------------------------------------------------------------------

class ContentType(str, Enum):
    """内容类型枚举。"""
    POST = "post"               # 广场动态
    TREEHOLE_POST = "treehole_post"  # 树洞帖子


class ContentStatus(str, Enum):
    """内容状态枚举。"""
    ACTIVE = "active"           # 正常显示
    HIDDEN = "hidden"           # 已隐藏
    DELETED = "deleted"         # 已删除


class AdminContentListRequest(BaseSchema):
    """内容列表查询请求模型。"""

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")
    content_type: ContentType | None = Field(None, description="内容类型筛选")
    status: ContentStatus | None = Field(None, description="状态筛选")
    author_id: str | None = Field(None, description="作者ID筛选")
    is_recommended: bool | None = Field(None, description="是否推荐筛选")
    start_time: datetime | None = Field(None, description="创建时间起始")
    end_time: datetime | None = Field(None, description="创建时间截止")
    search: str | None = Field(None, description="内容搜索关键词")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")


class AdminContentListItem(BaseSchema):
    """内容列表项响应模型。"""

    id: str = Field(..., description="内容ID")
    content_type: str = Field(..., description="内容类型")
    content: str | None = Field(None, description="内容文本（截断）")
    author_id: str = Field(..., description="作者ID")
    author_nickname: str | None = Field(None, description="作者昵称")
    status: str = Field(..., description="内容状态")
    is_recommended: bool = Field(default=False, description="是否推荐")
    report_count: int = Field(default=0, description="被举报次数")
    like_count: int = Field(default=0, description="点赞数/共鸣数")
    comment_count: int = Field(default=0, description="评论数")
    created_at: datetime = Field(..., description="创建时间")


class AdminContentDetail(BaseSchema):
    """内容详情响应模型。"""

    id: str = Field(..., description="内容ID")
    content_type: str = Field(..., description="内容类型")
    content: str | None = Field(None, description="内容文本")
    image_urls: list[str] | None = Field(None, description="图片URL列表")
    author_id: str = Field(..., description="作者ID")
    author_nickname: str | None = Field(None, description="作者昵称")
    author_phone: str | None = Field(None, description="作者手机号（脱敏）")
    status: str = Field(..., description="内容状态")
    is_recommended: bool = Field(default=False, description="是否推荐")
    visibility: str | None = Field(None, description="可见性（广场动态）")
    topic_tag: str | None = Field(None, description="话题标签（树洞）")
    report_count: int = Field(default=0, description="被举报次数")
    like_count: int = Field(default=0, description="点赞数/共鸣数")
    comment_count: int = Field(default=0, description="评论数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminContentStatusRequest(BaseSchema):
    """内容状态修改请求模型。"""

    action: str = Field(
        ...,
        description="操作类型：hide（隐藏）/ show（显示）/ recommend（推荐）/ unrecommend（取消推荐）",
    )
    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="操作原因",
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """验证操作类型。"""
        allowed = ["hide", "show", "recommend", "unrecommend"]
        if v not in allowed:
            raise ValueError(f"操作类型必须是: {allowed}")
        return v


class AdminContentStatusResponse(BaseSchema):
    """内容状态修改响应模型。"""

    id: str = Field(..., description="内容ID")
    content_type: str = Field(..., description="内容类型")
    status: str = Field(..., description="当前状态")
    is_recommended: bool = Field(default=False, description="是否推荐")
    action: str = Field(..., description="执行的操作")
    message: str = Field(..., description="操作结果说明")
