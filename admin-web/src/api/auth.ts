import { request } from '@/utils/request'
import type {
  LoginRequest,
  LoginResponse,
  AdminInfo,
  PermissionCheckRequest,
  PermissionCheckResponse,
} from '@/types/admin'

// 管理员登录
export function login(data: LoginRequest): Promise<LoginResponse> {
  return request.post('/api/admin/v1/auth/login', data)
}

// 刷新 Token
export function refreshToken(refreshToken: string): Promise<LoginResponse> {
  return request.post('/api/admin/v1/auth/refresh', { refresh_token: refreshToken })
}

// 登出
export function logout(): Promise<{ message: string }> {
  return request.post('/api/admin/v1/auth/logout')
}

// 获取当前管理员信息
export function getAdminInfo(): Promise<AdminInfo> {
  return request.get('/api/admin/v1/auth/me')
}

// 权限检查
export function checkPermission(data: PermissionCheckRequest): Promise<PermissionCheckResponse> {
  return request.post('/api/admin/v1/auth/check-permission', data)
}
