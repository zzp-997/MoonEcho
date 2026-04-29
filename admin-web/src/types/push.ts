// 推送管理相关类型

// 推送任务状态
export type PushTaskStatus = 'pending' | 'sending' | 'completed' | 'failed' | 'cancelled'

// 推送任务类型
export type PushTaskType = 'broadcast' | 'targeted' | 'scheduled'

// 推送渠道
export type PushChannel = 'app' | 'sms' | 'email' | 'all'

// 推送任务列表项
export interface PushTaskItem {
  id: string
  title: string
  content: string
  type: PushTaskType
  channel: PushChannel
  status: PushTaskStatus
  target_count: number
  sent_count: number
  success_count: number
  fail_count: number
  scheduled_at: string | null
  sent_at: string | null
  created_by: string
  created_by_name: string
  created_at: string
  updated_at: string
}

// 推送任务详情
export interface PushTaskDetail extends PushTaskItem {
  target_criteria: PushTargetCriteria | null
  extra_data: Record<string, any> | null
  remark: string | null
}

// 推送目标条件
export interface PushTargetCriteria {
  user_ids?: string[]
  age_range?: string
  city?: string
  is_minor?: boolean
  register_start?: string
  register_end?: string
  last_active_start?: string
  last_active_end?: string
  has_diary?: boolean
  tag_ids?: string[]
}

// 创建推送任务请求
export interface CreatePushTaskRequest {
  title: string
  content: string
  type: PushTaskType
  channel: PushChannel
  target_criteria?: PushTargetCriteria
  scheduled_at?: string
  extra_data?: Record<string, any>
  remark?: string
}

// 推送任务查询参数
export interface PushTaskListParams {
  page?: number
  page_size?: number
  status?: PushTaskStatus
  type?: PushTaskType
  channel?: PushChannel
  start_date?: string
  end_date?: string
  search?: string
}

// 推送任务统计
export interface PushTaskStats {
  total_tasks: number
  pending_tasks: number
  completed_tasks: number
  failed_tasks: number
  total_sent: number
  total_success: number

  // 今日统计
  today_tasks: number
  today_sent: number
  today_success: number
}

// 取消推送任务请求
export interface CancelPushTaskRequest {
  reason: string
}

// 重新发送推送任务请求
export interface RetryPushTaskRequest {
  target_user_ids?: string[]
}
