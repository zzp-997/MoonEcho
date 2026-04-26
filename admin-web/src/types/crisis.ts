// 危机干预相关类型

// 危机级别
export type CrisisLevel = 'high' | 'medium' | 'low'

// 危机状态
export type CrisisStatus = 'pending' | 'intervening' | 'resolved' | 'false_positive'

// 危机事件列表项
export interface CrisisListItem {
  message_id: string
  user_id: string
  user_nickname: string | null
  level: CrisisLevel
  trigger_keywords: string[]
  status: CrisisStatus
  created_at: string
  resolved_at: string | null
  resolved_by: string | null
  intervening_admin: string | null
}

// 危机事件详情
export interface CrisisDetail extends CrisisListItem {
  user_phone: string // 脱敏
  trigger_message: string // 脱敏
  ai_response: string | null
  conversation_id: string
  user_crisis_history: CrisisHistoryStats
  resolution_notes: string | null
}

// 用户危机历史统计
export interface CrisisHistoryStats {
  total_crisis_events: number
  high_level_count: number
  medium_level_count: number
  low_level_count: number
  last_crisis_at: string | null
}

// 处理危机请求
export interface ResolveCrisisRequest {
  status: 'resolved' | 'false_positive'
  notes: string
  notify_user?: boolean
}

// 处理危机响应
export interface ResolveCrisisResponse {
  message_id: string
  status: CrisisStatus
  resolved_at: string
  notes: string
}