"""管理后台认证相关请求/响应模型。

包含管理员登录、Token 刷新、管理员信息等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 角色和权限定义
# ---------------------------------------------------------------------------

# 角色枚举
ADMIN_ROLES = ["super_admin", "admin", "operator"]

# 权限节点定义
PERMISSION_NODES = {
    # 用户管理
    "user:view": "查看用户列表",
    "user:ban": "封禁/解封用户",
    "user:export": "导出用户数据",
    # 举报管理
    "report:view": "查看举报",
    "report:process": "处理举报",
    # 危机事件
    "crisis:view": "查看危机事件",
    "crisis:resolve": "介入危机事件",
    # 内容管理
    "content:view": "查看内容",
    "content:moderate": "内容审核操作",
    # 管理员管理
    "admin:view": "查看管理员",
    "admin:create": "创建管理员",
    "admin:update": "编辑管理员",
    "admin:delete": "删除管理员",
    # 日志
    "log:view": "查看操作日志",
    # 系统设置
    "settings:view": "查看系统设置",
    "settings:update": "修改系统设置",
}

# 角色-权限映射
ROLE_PERMISSIONS = {
    "super_admin": list(PERMISSION_NODES.keys()),  # 全部权限
    "admin": [
        "user:view",
        "user:ban",
        "user:export",
        "report:view",
        "report:process",
        "crisis:view",
        "crisis:resolve",
        "content:view",
        "content:moderate",
        "admin:view",
        "log:view",
        "settings:view",
    ],
    "operator": [
        "user:view",
        "report:view",
        "crisis:view",
        "content:view",
        "content:moderate",
    ],
}


# ---------------------------------------------------------------------------
# 管理员登录
# ---------------------------------------------------------------------------

class AdminLoginRequest(BaseSchema):
    """管理员登录请求模型。"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名",
        examples=["admin"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="密码",
        examples=["admin123"],
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式。"""
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码格式。"""
        v = v.strip()
        if not v:
            raise ValueError("密码不能为空")
        if len(v) < 6:
            raise ValueError("密码长度至少 6 位")
        return v


class AdminLoginResponse(BaseSchema):
    """管理员登录响应模型。"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="access_token 有效期（秒）")
    admin_id: str = Field(..., description="管理员ID")
    username: str = Field(..., description="用户名")
    nickname: str | None = Field(None, description="昵称")
    role: str = Field(..., description="角色")
    permissions: list[str] = Field(default_factory=list, description="权限列表")


# ---------------------------------------------------------------------------
# Token 刷新
# ---------------------------------------------------------------------------

class AdminRefreshTokenRequest(BaseSchema):
    """管理员刷新令牌请求模型。"""

    refresh_token: str = Field(..., description="刷新令牌")


class AdminRefreshTokenResponse(BaseSchema):
    """管理员刷新令牌响应模型。"""

    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(..., description="access_token 有效期（秒）")


# ---------------------------------------------------------------------------
# 当前管理员信息
# ---------------------------------------------------------------------------

class CurrentAdminResponse(BaseSchema):
    """当前管理员信息响应模型。"""

    id: str = Field(..., description="管理员ID")
    username: str = Field(..., description="用户名")
    nickname: str | None = Field(None, description="昵称")
    role: str = Field(..., description="角色")
    permissions: list[str] = Field(default_factory=list, description="权限列表")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    last_login_ip: str | None = Field(None, description="最后登录IP")
    created_at: datetime = Field(..., description="创建时间")


# ---------------------------------------------------------------------------
# 管理员操作日志
# ---------------------------------------------------------------------------

class AdminLogResponse(BaseSchema):
    """操作日志响应模型。"""

    id: str = Field(..., description="日志ID")
    admin_id: str = Field(..., description="管理员ID")
    admin_username: str | None = Field(None, description="管理员用户名")
    action: str = Field(..., description="操作类型")
    target_type: str | None = Field(None, description="操作对象类型")
    target_id: str | None = Field(None, description="操作对象ID")
    details: dict | None = Field(None, description="操作详情")
    ip_address: str | None = Field(None, description="操作IP")
    user_agent: str | None = Field(None, description="浏览器UA")
    created_at: datetime = Field(..., description="操作时间")


# ---------------------------------------------------------------------------
# 权限检查
# ---------------------------------------------------------------------------

class PermissionCheckRequest(BaseSchema):
    """权限检查请求模型。"""

    permission: str = Field(..., description="要检查的权限节点")


class PermissionCheckResponse(BaseSchema):
    """权限检查响应模型。"""

    has_permission: bool = Field(..., description="是否拥有该权限")
    permission: str = Field(..., description="权限节点")
    role: str = Field(..., description="当前角色")


# ---------------------------------------------------------------------------
# 用户管理
# ---------------------------------------------------------------------------

class AdminUserListRequest(BaseSchema):
    """用户列表查询请求模型。"""

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")
    search: str | None = Field(None, description="搜索关键词（昵称/手机号模糊匹配）")
    age_range: str | None = Field(None, description="年龄段筛选：18-24/25-30/31-40/40+")
    is_minor: bool | None = Field(None, description="青少年模式筛选")
    is_banned: bool | None = Field(None, description="封禁状态筛选")
    register_start: datetime | None = Field(None, description="注册时间起始")
    register_end: datetime | None = Field(None, description="注册时间截止")
    sort_by: str = Field(default="created_at", description="排序字段：created_at/last_active_at")
    sort_order: str = Field(default="desc", description="排序方向：asc/desc")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """验证排序字段。"""
        allowed = ["created_at", "last_active_at"]
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


class AdminUserListItem(BaseSchema):
    """用户列表项响应模型。"""

    id: str = Field(..., description="用户ID")
    phone: str = Field(..., description="手机号（脱敏）")
    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    age_range: str | None = Field(None, description="年龄段")
    is_minor: bool = Field(..., description="是否未成年人")
    is_banned: bool = Field(..., description="是否被封禁")
    ban_reason: str | None = Field(None, description="封禁原因")
    ban_until: datetime | None = Field(None, description="封禁结束时间")
    social_energy: float | None = Field(None, description="社交能量值")
    created_at: datetime = Field(..., description="注册时间")
    last_active_at: datetime | None = Field(None, description="最后活跃时间")


class AdminUserDetail(BaseSchema):
    """用户详情响应模型。"""

    id: str = Field(..., description="用户ID")
    phone: str = Field(..., description="手机号（脱敏）")
    nickname: str | None = Field(None, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL")
    age_range: str | None = Field(None, description="年龄段")
    city: str | None = Field(None, description="所在城市")
    occupation: str | None = Field(None, description="职业")
    is_minor: bool = Field(..., description="是否未成年人")
    guardian_phone: str | None = Field(None, description="监护人联系方式")
    is_banned: bool = Field(..., description="是否被封禁")
    ban_reason: str | None = Field(None, description="封禁原因")
    ban_until: datetime | None = Field(None, description="封禁结束时间")
    social_energy: float | None = Field(None, description="社交能量值")
    created_at: datetime = Field(..., description="注册时间")
    last_active_at: datetime | None = Field(None, description="最后活跃时间")
    notification_settings: dict | None = Field(None, description="通知偏好设置")


class AdminUserDiaryStats(BaseSchema):
    """用户日记统计响应模型。"""

    total_count: int = Field(..., description="日记总数")
    this_month_count: int = Field(..., description="本月日记数")
    emotion_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="情绪基调分布，如 {'happy': 10, 'sad': 5}",
    )
    recent_emotions: list[str] = Field(
        default_factory=list,
        description="最近7天情绪标签",
    )


class AdminUserSocialStats(BaseSchema):
    """用户社交数据响应模型。"""

    friend_count: int = Field(..., description="好友数")
    post_count: int = Field(..., description="动态数")
    treehole_count: int = Field(..., description="树洞帖子数")
    comment_count: int = Field(..., description="评论数")


class AdminBanUserRequest(BaseSchema):
    """封禁用户请求模型。"""

    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="封禁原因",
    )
    duration_days: int | None = Field(
        None,
        ge=1,
        description="封禁天数，null表示永久封禁",
    )
    notify_user: bool = Field(default=True, description="是否通知用户")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """验证封禁原因。"""
        v = v.strip()
        if not v:
            raise ValueError("封禁原因不能为空")
        return v


class AdminUnbanUserRequest(BaseSchema):
    """解封用户请求模型。"""

    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="解封原因",
    )
    notify_user: bool = Field(default=True, description="是否通知用户")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """验证解封原因。"""
        v = v.strip()
        if not v:
            raise ValueError("解封原因不能为空")
        return v


class AdminMinorModeRequest(BaseSchema):
    """青少年模式设置请求模型。"""

    is_minor: bool = Field(..., description="是否开启青少年模式")
    guardian_phone: str | None = Field(
        None,
        min_length=11,
        max_length=11,
        description="监护人手机号（开启青少年模式时必填）",
    )

    @field_validator("guardian_phone")
    @classmethod
    def validate_guardian_phone(cls, v: str | None, info) -> str | None:
        """验证监护人手机号。"""
        if info.data.get("is_minor") and not v:
            raise ValueError("开启青少年模式时必须填写监护人手机号")
        if v and not v.isdigit():
            raise ValueError("监护人手机号必须是11位数字")
        return v


# ---------------------------------------------------------------------------
# 管理员管理（CRUD）
# ---------------------------------------------------------------------------

class AdminListRequest(BaseSchema):
    """管理员列表查询请求模型。"""

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")
    search: str | None = Field(None, description="搜索关键词（用户名/昵称模糊匹配）")
    role: str | None = Field(None, description="角色筛选：super_admin/admin/operator")
    is_active: bool | None = Field(None, description="状态筛选")
    sort_by: str = Field(default="created_at", description="排序字段：created_at/last_login_at")
    sort_order: str = Field(default="desc", description="排序方向：asc/desc")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        """验证角色。"""
        if v and v not in ADMIN_ROLES:
            raise ValueError(f"角色必须是: {ADMIN_ROLES}")
        return v

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """验证排序字段。"""
        allowed = ["created_at", "last_login_at", "username"]
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


class AdminListItem(BaseSchema):
    """管理员列表项响应模型。"""

    id: str = Field(..., description="管理员ID")
    username: str = Field(..., description="用户名")
    nickname: str | None = Field(None, description="昵称")
    role: str = Field(..., description="角色")
    is_active: bool = Field(..., description="是否启用")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    last_login_ip: str | None = Field(None, description="最后登录IP")
    created_at: datetime = Field(..., description="创建时间")


class AdminDetailResponse(BaseSchema):
    """管理员详情响应模型。"""

    id: str = Field(..., description="管理员ID")
    username: str = Field(..., description="用户名")
    nickname: str | None = Field(None, description="昵称")
    role: str = Field(..., description="角色")
    permissions: list[str] = Field(default_factory=list, description="权限列表")
    is_active: bool = Field(..., description="是否启用")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    last_login_ip: str | None = Field(None, description="最后登录IP")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AdminCreateRequest(BaseSchema):
    """创建管理员请求模型。"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="密码（至少8位，包含字母和数字）",
    )
    nickname: str | None = Field(None, max_length=50, description="昵称")
    role: str = Field(
        default="operator",
        description="角色：super_admin/admin/operator",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式。"""
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度。"""
        v = v.strip()
        if not v:
            raise ValueError("密码不能为空")
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """验证角色。"""
        if v not in ADMIN_ROLES:
            raise ValueError(f"角色必须是: {ADMIN_ROLES}")
        return v


class AdminUpdateRequest(BaseSchema):
    """更新管理员请求模型。"""

    nickname: str | None = Field(None, max_length=50, description="昵称")
    role: str | None = Field(None, description="角色")
    is_active: bool | None = Field(None, description="是否启用")
    password: str | None = Field(None, min_length=8, max_length=100, description="新密码")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        """验证角色。"""
        if v and v not in ADMIN_ROLES:
            raise ValueError(f"角色必须是: {ADMIN_ROLES}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """验证密码强度。"""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("密码不能为空")
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class AdminLogListRequest(BaseSchema):
    """操作日志列表查询请求模型。"""

    page: int = Field(default=1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")
    admin_id: str | None = Field(None, description="管理员ID筛选")
    action: str | None = Field(None, description="操作类型筛选")
    target_type: str | None = Field(None, description="操作对象类型筛选")
    start_time: datetime | None = Field(None, description="开始时间")
    end_time: datetime | None = Field(None, description="结束时间")


# ---------------------------------------------------------------------------
# 角色定义
# ---------------------------------------------------------------------------

class RoleListItem(BaseSchema):
    """角色列表项响应模型。"""

    name: str = Field(..., description="角色名称")
    display_name: str = Field(..., description="角色显示名称")
    permissions: list[str] = Field(default_factory=list, description="权限列表")
    description: str | None = Field(None, description="角色描述")


class RoleListResponse(BaseSchema):
    """角色列表响应模型。"""

    roles: list[RoleListItem] = Field(default_factory=list, description="角色列表")


# ---------------------------------------------------------------------------
# 权限节点补充
# ---------------------------------------------------------------------------

# 补充管理后台阶段二的权限节点
PERMISSION_NODES.update({
    "dashboard:read": "查看数据看板",
    "admin:manage": "管理管理员账号、角色、权限",
    "push:view": "查看推送任务",
    "push:create": "创建推送任务",
})

# 更新角色权限映射
ROLE_PERMISSIONS["super_admin"] = list(PERMISSION_NODES.keys())
ROLE_PERMISSIONS["admin"].extend([
    "dashboard:read",
    "log:view",
])
ROLE_PERMISSIONS["operator"].extend([
    "dashboard:read",
])


# ---------------------------------------------------------------------------
# 角色展示名称
# ---------------------------------------------------------------------------

ROLE_DISPLAY_NAMES = {
    "super_admin": "超级管理员",
    "admin": "管理员",
    "operator": "运营人员",
}

ROLE_DESCRIPTIONS = {
    "super_admin": "拥有全部权限，包括管理员管理、系统设置等",
    "admin": "拥有大部分权限，但不能管理其他管理员",
    "operator": "基础运营权限，用于举报处理、内容审核等",
}
