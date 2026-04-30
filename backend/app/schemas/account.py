"""账户注销相关请求/响应模型。

包含账户注销请求、注销进度响应、注销完成响应等 Schema 定义。

安全设计：
- 注销需要用户二次确认
- 支持选择是否备份数据
- 注销进度实时反馈
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 注销请求
# ---------------------------------------------------------------------------

class AccountDeletionRequest(BaseSchema):
    """账户注销请求模型。

    用户发起注销请求时需填写。

    Attributes:
        reason: 注销原因（可选）
        confirm_password: 确认密码（可选，增强安全性）
        export_data: 是否需要导出数据备份
    """

    reason: str | None = Field(
        default=None,
        max_length=200,
        description="注销原因（可选）",
        examples=["不再使用"],
    )
    confirm_password: str | None = Field(
        default=None,
        description="确认密码（可选，增强安全性）",
    )
    export_data: bool = Field(
        default=False,
        description="是否需要导出数据备份",
    )


# ---------------------------------------------------------------------------
# 注销进度响应
# ---------------------------------------------------------------------------

class DeletionProgressItem(BaseSchema):
    """注销进度单项。

    表示单个数据类型的处理进度。

    Attributes:
        data_type: 数据类型名称
        status: 处理状态
        count: 处理数量
        message: 处理消息
    """

    data_type: str = Field(..., description="数据类型：users/posts/diaries 等")
    status: str = Field(
        ...,
        description="处理状态：pending/processing/completed/skipped",
    )
    count: int = Field(default=0, description="已处理数量")
    message: str | None = Field(default=None, description="处理消息")


class DeletionProgressResponse(BaseSchema):
    """注销进度响应模型。

    用于向用户反馈注销处理进度。

    Attributes:
        total_steps: 总步骤数
        completed_steps: 已完成步骤数
        current_step: 当前步骤名称
        progress_items: 各数据类型处理进度
        estimated_remaining_seconds: 预估剩余时间（秒）
        started_at: 开始时间
        is_completed: 是否已完成
    """

    total_steps: int = Field(..., description="总步骤数")
    completed_steps: int = Field(default=0, description="已完成步骤数")
    current_step: str | None = Field(default=None, description="当前步骤名称")
    progress_items: list[DeletionProgressItem] = Field(
        default_factory=list,
        description="各数据类型处理进度",
    )
    estimated_remaining_seconds: int | None = Field(
        default=None,
        description="预估剩余时间（秒）",
    )
    started_at: datetime | None = Field(default=None, description="开始时间")
    is_completed: bool = Field(default=False, description="是否已完成")


# ---------------------------------------------------------------------------
# 注销完成响应
# ---------------------------------------------------------------------------

class AccountDeletionResponse(BaseSchema):
    """账户注销完成响应模型。

    注销完成后返回的最终结果。

    Attributes:
        success: 是否成功
        message: 结果消息
        deleted_at: 注销完成时间
        data_export_url: 数据导出链接（如果用户选择了导出）
        export_expires_at: 导出链接过期时间（下载后失效）
        deletion_summary: 注销数据摘要
    """

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="结果消息")
    deleted_at: datetime | None = Field(default=None, description="注销完成时间")
    data_export_url: str | None = Field(
        default=None,
        description="数据导出链接（如果用户选择了导出）",
    )
    export_expires_at: datetime | None = Field(
        default=None,
        description="导出链接过期时间（24小时后失效）",
    )
    deletion_summary: dict[str, int] | None = Field(
        default=None,
        description="注销数据摘要：各类型删除数量",
    )


# ---------------------------------------------------------------------------
# 注销预检查响应
# ---------------------------------------------------------------------------

class DeletionPreCheckResponse(BaseSchema):
    """注销预检查响应模型。

    在用户发起注销前展示，提醒用户注销的影响。

    Attributes:
        can_delete: 是否可以注销（有未处理的好友申请等时可能不允许）
        warnings: 警告信息列表
        data_summary: 用户数据摘要
        irreversible_warning: 不可逆操作警告
    """

    can_delete: bool = Field(..., description="是否可以注销")
    warnings: list[str] = Field(
        default_factory=list,
        description="警告信息列表",
    )
    data_summary: dict[str, int] = Field(
        default_factory=dict,
        description="用户数据摘要：各类型数据数量",
    )
    irreversible_warning: str = Field(
        default="账户注销后，您的所有数据将被永久删除或匿名化处理，此操作不可恢复。",
        description="不可逆操作警告",
    )


# ---------------------------------------------------------------------------
# 数据导出响应
# ---------------------------------------------------------------------------

class DataExportRequest(BaseSchema):
    """数据导出请求模型。

    用户在注销前申请导出数据备份。

    Attributes:
        include_diaries: 是否包含情绪日记
        include_posts: 是否包含动态广场帖子
        include_treehole: 是否包含树洞内容
        include_ai_conversations: 是否包含AI对话记录
        include_friends: 是否包含好友关系
    """

    include_diaries: bool = Field(default=True, description="是否包含情绪日记")
    include_posts: bool = Field(default=True, description="是否包含动态广场帖子")
    include_treehole: bool = Field(default=True, description="是否包含树洞内容")
    include_ai_conversations: bool = Field(default=True, description="是否包含AI对话记录")
    include_friends: bool = Field(default=True, description="是否包含好友关系")


class DataExportResponse(BaseSchema):
    """数据导出响应模型。

    Attributes:
        export_url: 导出文件下载链接
        expires_at: 链接过期时间
        file_size: 文件大小（字节）
        format: 导出格式
    """

    export_url: str = Field(..., description="导出文件下载链接")
    expires_at: datetime = Field(..., description="链接过期时间（24小时后）")
    file_size: int | None = Field(default=None, description="文件大小（字节）")
    format: str = Field(default="json", description="导出格式：json/csv")