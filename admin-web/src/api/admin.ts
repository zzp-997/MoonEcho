import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  AdminListItem,
  AdminDetail,
  CreateAdminRequest,
  UpdateAdminRequest,
  ResetPasswordRequest,
  AdminListParams,
  RoleInfo,
  AdminLogItem,
  AdminLogParams,
} from '@/types/admin'

// ===== 管理员管理 =====

// 获取管理员列表
export function getAdminList(params?: AdminListParams): Promise<PaginatedResponse<AdminListItem>> {
  return request.get('/api/admin/v1/admins', params)
}

// 获取管理员详情
export function getAdminDetail(adminId: string): Promise<AdminDetail> {
  return request.get(`/api/admin/v1/admins/${adminId}`)
}

// 创建管理员
export function createAdmin(data: CreateAdminRequest): Promise<AdminDetail> {
  return request.post('/api/admin/v1/admins', data)
}

// 更新管理员
export function updateAdmin(adminId: string, data: UpdateAdminRequest): Promise<AdminDetail> {
  return request.patch(`/api/admin/v1/admins/${adminId}`, data)
}

// 删除管理员
export function deleteAdmin(adminId: string): Promise<void> {
  return request.delete(`/api/admin/v1/admins/${adminId}`)
}

// 重置管理员密码
export function resetAdminPassword(adminId: string, data: ResetPasswordRequest): Promise<void> {
  return request.post(`/api/admin/v1/admins/${adminId}/reset-password`, data)
}

// ===== 角色管理 =====

// 获取角色列表
export function getRoleList(): Promise<RoleInfo[]> {
  return request.get('/api/admin/v1/admins/roles')
}

// ===== 操作日志 =====

// 获取操作日志列表
export function getAdminLogs(params?: AdminLogParams): Promise<PaginatedResponse<AdminLogItem>> {
  return request.get('/api/admin/v1/admins/logs', params)
}
