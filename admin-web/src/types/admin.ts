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