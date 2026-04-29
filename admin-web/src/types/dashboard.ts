// 数据看板相关类型

// 概览统计数据
export interface OverviewStats {
  dau: number
  wau: number
  mau: number
  new_users_today: number
  new_users_yesterday: number
  new_users_week: number
  ai_conversations_today: number
  diary_count_today: number
  active_rate: number
}

// 用户增长趋势数据
export interface UserGrowthItem {
  date: string
  new_users: number
  active_users: number
  total_users: number
}

// 用户增长查询参数
export interface UserGrowthParams {
  start_date?: string
  end_date?: string
  granularity?: 'day' | 'week' | 'month'
}

// 留存数据
export interface RetentionItem {
  date: string
  new_users: number
  day1: number
  day3: number
  day7: number
  day14: number
  day30: number
}

// 留存查询参数
export interface RetentionParams {
  start_date?: string
  end_date?: string
}

// 情绪分布数据
export interface EmotionDistribution {
  emotion: string
  count: number
  percentage: number
}

// AI 服务统计
export interface AIServiceStats {
  total_conversations: number
  avg_duration: number
  avg_messages: number
  satisfaction_rate: number
  top_intents: AIIntentItem[]
  daily_stats: AIDailyStats[]
}

export interface AIIntentItem {
  intent: string
  count: number
  percentage: number
}

export interface AIDailyStats {
  date: string
  conversations: number
  avg_duration: number
  satisfaction: number
}

// 数据看板时间范围
export type DashboardTimeRange = 'today' | 'yesterday' | 'week' | 'month' | 'custom'
