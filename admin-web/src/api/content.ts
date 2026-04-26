import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  ContentListItem,
  ContentDetail,
  ContentStatusRequest,
  ContentStatusResponse,
  AdminContentType,
  ContentStatus,
} from '@/types/content'

// 内容列表查询参数
export interface ContentListParams {
  page?: number
  page_size?: number
  content_type?: AdminContentType
  status?: ContentStatus
  author_id?: string
  is_recommended?: boolean
  start_time?: string
  end_time?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 获取内容列表
export function getContentList(params: ContentListParams): Promise<PaginatedResponse<ContentListItem>> {
  return request.get('/api/admin/v1/contents', params)
}

// 获取内容详情
export function getContentDetail(contentType: AdminContentType, contentId: string): Promise<ContentDetail> {
  return request.get(`/api/admin/v1/contents/${contentType}/${contentId}`)
}

// 修改内容状态
export function updateContentStatus(
  contentType: AdminContentType,
  contentId: string,
  data: ContentStatusRequest
): Promise<ContentStatusResponse> {
  return request.patch(`/api/admin/v1/contents/${contentType}/${contentId}/status`, data)
}
