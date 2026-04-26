import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  UserListItem,
  UserDetail,
  UserDiaryStats,
  UserSocialStats,
  BanUserRequest,
  UnbanUserRequest,
  MinorModeRequest,
} from '@/types/user'

// 用户列表查询参数
export interface UserListParams {
  page?: number
  page_size?: number
  search?: string
  age_range?: string
  is_minor?: boolean
  is_banned?: boolean
  register_start?: string
  register_end?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 获取用户列表
export function getUserList(params: UserListParams): Promise<PaginatedResponse<UserListItem>> {
  return request.get('/api/admin/v1/users', params)
}

// 获取用户详情
export function getUserDetail(userId: string): Promise<UserDetail> {
  return request.get(`/api/admin/v1/users/${userId}`)
}

// 封禁用户
export function banUser(userId: string, data: BanUserRequest): Promise<UserDetail> {
  return request.post(`/api/admin/v1/users/${userId}/ban`, data)
}

// 解封用户
export function unbanUser(userId: string, data: UnbanUserRequest): Promise<UserDetail> {
  return request.post(`/api/admin/v1/users/${userId}/unban`, data)
}

// 获取用户日记统计
export function getUserDiaryStats(userId: string): Promise<UserDiaryStats> {
  return request.get(`/api/admin/v1/users/${userId}/diaries`)
}

// 获取用户社交数据
export function getUserSocialStats(userId: string): Promise<UserSocialStats> {
  return request.get(`/api/admin/v1/users/${userId}/social`)
}

// 设置青少年模式
export function setMinorMode(userId: string, data: MinorModeRequest): Promise<UserDetail> {
  return request.put(`/api/admin/v1/users/${userId}/minor`, data)
}
