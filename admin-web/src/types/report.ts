// 举报管理相关类型

// 举报类型
export type ReportType = 'porn' | 'ad' | 'harassment' | 'abuse' | 'scam' | 'self_harm' | 'other'

// 内容类型
export type ContentType = 'post' | 'treehole_post' | 'comment' | 'user'

// 举报状态
export type ReportStatus = 'pending' | 'processing' | 'approved' | 'rejected'

// 举报列表项
export interface ReportListItem {
  id: string
  report_type: ReportType
  content_type: ContentType
  content_id: string
  reporter_id: string
  reporter_nickname: string | null
  reported_user_id: string | null
  reported_user_nickname: string | null
  reason: string
  status: ReportStatus
  created_at: string
  processed_at: string | null
  processed_by: string | null
  process_result: string | null
  has_appeal: boolean
}

// 举报详情
export interface ReportDetail extends ReportListItem {
  content_preview: string
  content_images: string[] | null
  reporter_phone: string // 脱敏
  reported_user_phone: string | null // 脱敏
  other_reports: ReportListItem[] // 同一内容的其他举报
  process_history: ProcessHistoryItem[]
  appeal_info: AppealInfo | null
}

// 处理历史项
export interface ProcessHistoryItem {
  admin_id: string
  admin_nickname: string
  action: string
  result: string
  created_at: string
}

// 申诉信息
export interface AppealInfo {
  appeal_reason: string
  appeal_status: 'pending' | 'approved' | 'rejected'
  appeal_created_at: string
  appeal_reviewed_at: string | null
  appeal_reviewed_by: string | null
}

// 处理举报请求
export interface ProcessReportRequest {
  action: 'approve' | 'reject' | 'ban_user'
  reason: string
  hide_content?: boolean
  ban_duration_days?: number
  notify_reporter?: boolean
  notify_reported_user?: boolean
}

// 处理举报响应
export interface ProcessReportResponse {
  report_id: string
  status: ReportStatus
  processed_at: string
  result: string
  content_hidden?: boolean
  user_banned?: boolean
}

// 申诉列表项
export interface AppealListItem {
  report_id: string
  appeal_reason: string
  appeal_status: 'pending' | 'approved' | 'rejected'
  appeal_created_at: string
  reporter_nickname: string | null
  reported_user_nickname: string | null
}

// 审核申诉请求
export interface ReviewAppealRequest {
  action: 'approve' | 'reject'
  reason: string
  unban_user?: boolean
  restore_content?: boolean
}

// 审核申诉响应
export interface ReviewAppealResponse {
  report_id: string
  appeal_status: string
  user_unbanned?: boolean
  content_restored?: boolean
}