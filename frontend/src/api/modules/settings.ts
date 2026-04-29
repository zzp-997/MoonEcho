/**
 * 回声 - 设置接口
 * 文件：src/api/modules/settings.ts
 * 说明：用户设置相关接口，包含AI设置、通知设置、隐私设置等
 */

import { api } from '../index'

// ==================== 类型定义 ====================

/** 用户设置数据 */
export interface UserSettings {
  // AI设置
  ai_care_enabled: boolean
  ai_personality: string
  ai_greeting_style: 'warm' | 'playful' | 'calm'

  // 通知设置
  notification_enabled: boolean
  notification_diary_reminder: boolean
  notification_friend_request: boolean
  notification_chat_message: boolean
  notification_ai_care: boolean
  quiet_hours_start: string | null // "22:00"
  quiet_hours_end: string | null // "08:00"

  // 隐私设置
  profile_visibility: 'public' | 'friends' | 'private'
  show_online_status: boolean
  show_profile_tags: boolean
  allow_friend_request: boolean

  // 同步设置
  cloud_sync_enabled: boolean
  auto_backup: boolean
}

/** 设置更新请求 */
export interface SettingsUpdateRequest {
  ai_care_enabled?: boolean
  ai_personality?: string
  ai_greeting_style?: 'warm' | 'playful' | 'calm'
  notification_enabled?: boolean
  notification_diary_reminder?: boolean
  notification_friend_request?: boolean
  notification_chat_message?: boolean
  notification_ai_care?: boolean
  quiet_hours_start?: string | null
  quiet_hours_end?: string | null
  profile_visibility?: 'public' | 'friends' | 'private'
  show_online_status?: boolean
  show_profile_tags?: boolean
  allow_friend_request?: boolean
  cloud_sync_enabled?: boolean
  auto_backup?: boolean
}

/** AI性格选项 */
export interface AIPersonalityOption {
  id: string
  name: string
  description: string
  avatar_url: string
  traits: string[]
}

/** 默认设置 */
export const DEFAULT_USER_SETTINGS: UserSettings = {
  // AI设置
  ai_care_enabled: true,
  ai_personality: 'xiaowen',
  ai_greeting_style: 'warm',

  // 通知设置
  notification_enabled: true,
  notification_diary_reminder: true,
  notification_friend_request: true,
  notification_chat_message: true,
  notification_ai_care: true,
  quiet_hours_start: '22:00',
  quiet_hours_end: '08:00',

  // 隐私设置
  profile_visibility: 'friends',
  show_online_status: true,
  show_profile_tags: true,
  allow_friend_request: true,

  // 同步设置
  cloud_sync_enabled: true,
  auto_backup: false,
}

// ==================== API 函数 ====================

/**
 * 获取用户设置
 */
export async function getUserSettings(): Promise<UserSettings> {
  try {
    return await api.get<UserSettings>('/users/me/settings')
  } catch {
    // 如果接口不存在，返回默认设置
    return { ...DEFAULT_USER_SETTINGS }
  }
}

/**
 * 更新用户设置
 * @param data 设置更新数据
 */
export async function updateUserSettings(data: SettingsUpdateRequest): Promise<UserSettings> {
  return api.patch<UserSettings>('/users/me/settings', data)
}

/**
 * 获取AI性格选项列表
 */
export async function getAIPersonalityOptions(): Promise<AIPersonalityOption[]> {
  // TODO: 从后端获取
  return [
    {
      id: 'xiaowen',
      name: '小温',
      description: '温柔细腻，善于倾听，给你温暖的陪伴',
      avatar_url: '/static/images/ai/xiaowen.png',
      traits: ['温柔', '善解人意', '耐心'],
    },
    {
      id: 'laohei',
      name: '老黑',
      description: '幽默风趣，直率坦诚，给你真诚的建议',
      avatar_url: '/static/images/ai/laohei.png',
      traits: ['幽默', '直率', '真诚'],
    },
    {
      id: 'ali',
      name: '阿离',
      description: '活泼可爱，充满好奇心，给你活力满满',
      avatar_url: '/static/images/ai/ali.png',
      traits: ['活泼', '好奇', '元气'],
    },
  ]
}

/**
 * 获取AI性格名称
 */
export function getAIPersonalityName(personalityId: string): string {
  const names: Record<string, string> = {
    xiaowen: '小温',
    laohei: '老黑',
    ali: '阿离',
  }
  return names[personalityId] || '小温'
}
