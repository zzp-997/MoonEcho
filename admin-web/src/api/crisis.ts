import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  CrisisListItem,
  CrisisDetail,
  ResolveCrisisRequest,
  ResolveCrisisResponse,
  CrisisLevel,
  CrisisStatus,
} from '@/types/crisis'

// 危机事件列表查询参数
export interface CrisisListParams {
  page?: number
  page_size?: number
  level?: CrisisLevel
  status?: CrisisStatus
  user_id?: string
  start_time?: string
  end_time?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 获取危机事件列表
export function getCrisisList(params: CrisisListParams): Promise<PaginatedResponse<CrisisListItem>> {
  return request.get('/api/admin/v1/crisis/list', params)
}

// 获取危机事件详情
export function getCrisisDetail(messageId: string): Promise<CrisisDetail> {
  return request.get(`/api/admin/v1/crisis/${messageId}`)
}

// 处理危机事件
export function resolveCrisis(messageId: string, data: ResolveCrisisRequest): Promise<ResolveCrisisResponse> {
  return request.post(`/api/admin/v1/crisis/${messageId}/resolve`, data)
}

// 标记人工介入
export function markIntervention(messageId: string): Promise<{ message: string }> {
  return request.post(`/api/admin/v1/crisis/${messageId}/intervene`)
}
