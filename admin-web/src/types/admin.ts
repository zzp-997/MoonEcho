// 管理员相关类型

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  admin: AdminInfo
}

// 管理员信息
export interface AdminInfo {
  id: string
  username: string
  nickname: string | null
  role: 'super_admin' | 'admin' | 'operator'
  permissions: Record<string, string[]> | null
  last_login_at: string | null
  last_login_ip: string | null
  is_active: boolean
}

// 权限检查请求
export interface PermissionCheckRequest {
  permission: string
}

// 权限检查响应
export interface PermissionCheckResponse {
  has_permission: boolean
}

// ===== 管理员管理相关类型 =====

// 管理员列表项
export interface AdminListItem {
  id: string
  username: string
  nickname: string | null
  email: string | null
  role: 'super_admin' | 'admin' | 'operator'
  is_active: boolean
  last_login_at: string | null
  last_login_ip: string | null
  created_at: string
  updated_at: string
}

// 管理员详情
export interface AdminDetail extends AdminListItem {
  permissions: Record<string, string[]> | null
  remark: string | null
}

// 创建管理员请求
export interface CreateAdminRequest {
  username: string
  password: string
  nickname?: string
  email?: string
  role: 'super_admin' | 'admin' | 'operator'
  permissions?: Record<string, string[]>
  remark?: string
}

// 更新管理员请求
export interface UpdateAdminRequest {
  nickname?: string
  email?: string
  role?: 'super_admin' | 'admin' | 'operator'
  permissions?: Record<string, string[]>
  is_active?: boolean
  remark?: string
}

// 重置密码请求
export interface ResetPasswordRequest {
  new_password: string
}

// 管理员列表查询参数
export interface AdminListParams {
  page?: number
  page_size?: number
  search?: string
  role?: string
  is_active?: boolean
}

// ===== 角色相关类型 =====

// 角色信息
export interface RoleInfo {
  key: 'super_admin' | 'admin' | 'operator'
  name: string
  description: string
  user_count: number
  permissions: Record<string, string[]>
}

// 权限模块
export interface PermissionModule {
  key: string
  name: string
  actions: PermissionAction[]
}

export interface PermissionAction {
  key: string
  name: string
  description: string
}

// ===== 操作日志相关类型 =====

// 操作日志列表项
export interface AdminLogItem {
  id: string
  admin_id: string
  admin_username: string
  admin_nickname: string | null
  action: string
  module: string
  target_type: string | null
  target_id: string | null
  detail: Record<string, any> | null
  ip: string
  user_agent: string
  created_at: string
}

// 操作日志查询参数
export interface AdminLogParams {
  page?: number
  page_size?: number
  admin_id?: string
  module?: string
  action?: string
  start_date?: string
  end_date?: string
}
