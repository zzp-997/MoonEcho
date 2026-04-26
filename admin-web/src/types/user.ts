// 用户管理相关类型

// 用户列表项
export interface UserListItem {
  id: string
  phone: string // 脱敏后的手机号
  nickname: string | null
  avatar_url: string | null
  age_range: string | null
  city: string | null
  occupation: string | null
  is_minor: boolean
  is_active: boolean
  is_banned: boolean
  ban_reason: string | null
  ban_expired_at: string | null
  created_at: string
  last_active_at: string | null
  social_energy: number | null
}

// 用户详情
export interface UserDetail extends UserListItem {
  notification_settings: Record<string, boolean> | null
}

// 用户日记统计
export interface UserDiaryStats {
  total_count: number
  this_month_count: number
  emotion_distribution: Record<string, number>
  recent_emotions: string[]
}

// 用户社交数据
export interface UserSocialStats {
  friend_count: number
  post_count: number
  treehole_count: number
  comment_count: number
}

// 封禁用户请求
export interface BanUserRequest {
  reason: string
  duration_days?: number | null
  notify_user?: boolean
}

// 解封用户请求
export interface UnbanUserRequest {
  reason: string
  notify_user?: boolean
}

// 青少年模式请求
export interface MinorModeRequest {
  is_minor: boolean
  guardian_phone?: string
}