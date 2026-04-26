import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  ReportListItem,
  ReportDetail,
  ProcessReportRequest,
  ProcessReportResponse,
  AppealListItem,
  ReviewAppealRequest,
  ReviewAppealResponse,
  ReportType,
  ContentType,
  ReportStatus,
} from '@/types/report'

// 举报列表查询参数
export interface ReportListParams {
  page?: number
  page_size?: number
  status?: ReportStatus
  report_type?: ReportType
  content_type?: ContentType
  reporter_id?: string
  reported_user_id?: string
  start_time?: string
  end_time?: string
  has_appeal?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 申诉列表查询参数
export interface AppealListParams {
  page?: number
  page_size?: number
  appeal_status?: 'pending' | 'approved' | 'rejected'
  start_time?: string
  end_time?: string
}

// 获取举报列表
export function getReportList(params: ReportListParams): Promise<PaginatedResponse<ReportListItem>> {
  return request.get('/api/admin/v1/reports', params)
}

// 获取举报详情
export function getReportDetail(reportId: string): Promise<ReportDetail> {
  return request.get(`/api/admin/v1/reports/${reportId}`)
}

// 处理举报
export function processReport(reportId: string, data: ProcessReportRequest): Promise<ProcessReportResponse> {
  return request.post(`/api/admin/v1/reports/${reportId}/process`, data)
}

// 获取申诉列表
export function getAppealList(params: AppealListParams): Promise<PaginatedResponse<AppealListItem>> {
  return request.get('/api/admin/v1/reports/appeals', params)
}

// 审核申诉
export function reviewAppeal(reportId: string, data: ReviewAppealRequest): Promise<ReviewAppealResponse> {
  return request.post(`/api/admin/v1/reports/appeals/${reportId}/review`, data)
}
