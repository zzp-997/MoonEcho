/**
 * 回声 - 通知接口
 * 文件：src/api/modules/notification.ts
 * 说明：通知列表、未读数量、标记已读、通知设置等接口
 * 后端端点参考（T013-A）：
 *   GET    /api/v1/notifications              # 获取通知列表
 *   GET    /api/v1/notifications/unread-count # 获取未读数量
 *   PATCH  /api/v1/notifications/:id/read     # 标记单条已读
 *   PATCH  /api/v1/notifications/read-all     # 全部标记已读
 *   GET    /api/v1/notifications/settings     # 获取通知设置
 *   PATCH  /api/v1/notifications/settings     # 更新通知设置
 */

import { api } from '../index'
import type { Pagination } from '../types'

// ==================== 类型定义 ====================

/** 通知类型枚举 */
export type NotificationType =
  | 'ai_care'        // AI关怀提醒
  | 'crisis_alert'   // 危机干预警报
  | 'crisis_follow'  // 危机后续跟进
  | 'friend_request' // 好友请求
  | 'friend_accept'  // 好友接受
  | 'treehole_reply' // 树洞回复
  | 'square_comment' // 广场评论
  | 'square_like'    // 广场点赞
  | 'weekly_report'  // 周报生成
  | 'system'         // 系统通知
  | 'update'         // 更新通知

/** 通知项 */
export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  content: string
  payload: Record<string, any>
  is_read: boolean
  created_at: string
}

/** 通知列表响应 */
export interface NotificationListResult {
  items: NotificationItem[]
  pagination: Pagination & {
    unreadCount: number
  }
}

/** 未读数量响应 */
export interface UnreadCountResult {
  count: number
}

/** 标记已读响应 */
export interface MarkReadResult {
  success: boolean
}

/** 通知类型开关映射 */
export interface NotificationTypesEnabled {
  ai_care: boolean
  crisis_alert: boolean      // 强制开启
  crisis_follow: boolean     // 强制开启
  friend_request: boolean
  friend_accept: boolean
  treehole_reply: boolean
  square_comment: boolean
  square_like: boolean
  weekly_report: boolean
  system: boolean
  update: boolean
}

/** 通知设置 */
export interface NotificationSettings {
  push_enabled: boolean
  types_enabled: NotificationTypesEnabled
}

/** 通知设置响应 */
export interface NotificationSettingsResult {
  push_enabled: boolean
  types_enabled: NotificationTypesEnabled
}

/** 更新通知设置请求 */
export interface UpdateSettingsParams {
  push_enabled?: boolean
  types_enabled?: Partial<NotificationTypesEnabled>
}

/** 获取通知列表参数 */
export interface GetNotificationsParams {
  page?: number
  pageSize?: number
}

// ==================== API 方法 ====================

/**
 * 获取通知列表
 * @param params 分页参数
 */
export function getNotifications(params: GetNotificationsParams = {}) {
  return api.get<NotificationListResult>('/notifications', params)
}

/**
 * 获取未读数量
 */
export function getUnreadCount(config?: any) {
  return api.get<UnreadCountResult>('/notifications/unread-count', {}, config)
}

/**
 * 标记单条通知已读
 * @param id 通知ID
 */
export function markAsRead(id: string) {
  return api.patch<MarkReadResult>(`/notifications/${id}/read`)
}

/**
 * 全部标记已读
 */
export function markAllAsRead() {
  return api.patch<MarkReadResult>('/notifications/read-all')
}

/**
 * 获取通知设置
 */
export function getNotificationSettings() {
  return api.get<NotificationSettingsResult>('/notifications/settings')
}

/**
 * 更新通知设置
 * @param params 设置参数
 */
export function updateNotificationSettings(params: UpdateSettingsParams) {
  return api.patch<NotificationSettingsResult>('/notifications/settings', params)
}

// ==================== 辅助函数 ====================

/**
 * 判断通知类型是否为强制开启
 * 危机干预相关类型不允许关闭
 */
export function isForcedType(type: NotificationType): boolean {
  return type === 'crisis_alert' || type === 'crisis_follow'
}

/**
 * 获取通知类型的图标名称
 */
export function getNotificationIcon(type: NotificationType): string {
  const iconMap: Record<NotificationType, string> = {
    ai_care: 'chat',
    crisis_alert: 'warning',
    crisis_follow: 'chat',
    friend_request: 'add-friends',
    friend_accept: 'friends',
    treehole_reply: 'chat-ledger',
    square_comment: 'comment',
    square_like: 'thumb-up',
    weekly_report: 'chart',
    system: 'info-circle',
    update: 'refresh'
  }
  return iconMap[type] || 'message'
}

/**
 * 获取通知类型的中文名称
 */
export function getNotificationTypeName(type: NotificationType): string {
  const nameMap: Record<NotificationType, string> = {
    ai_care: 'AI关怀',
    crisis_alert: '危机干预',
    crisis_follow: '危机跟进',
    friend_request: '好友请求',
    friend_accept: '好友接受',
    treehole_reply: '树洞回复',
    square_comment: '广场评论',
    square_like: '广场点赞',
    weekly_report: '周报通知',
    system: '系统通知',
    update: '更新通知'
  }
  return nameMap[type] || '未知通知'
}

/**
 * 获取通知类型的跳转路径
 * @param notification 通知项
 * @returns 跳转路径，若无需跳转返回 null
 */
export function getNotificationJumpUrl(notification: NotificationItem): string | null {
  const { type, payload } = notification

  switch (type) {
    case 'ai_care':
      return '/pages/chat/index'
    case 'crisis_alert':
      // 危机干预弹窗由页面处理
      return '/pages/chat/index?crisis=true'
    case 'crisis_follow':
      return '/pages/chat/index'
    case 'friend_request':
      return '/pages/friends/request'
    case 'friend_accept':
      return '/pages/friends/index'
    case 'treehole_reply':
      return payload?.treehole_id ? `/pagesSocial/treehole/detail?id=${payload.treehole_id}` : null
    case 'square_comment':
      return payload?.post_id ? `/pagesSocial/square/detail?id=${payload.post_id}` : null
    case 'square_like':
      return payload?.post_id ? `/pagesSocial/square/detail?id=${payload.post_id}` : null
    case 'weekly_report':
      return '/pages/diary/weekly-report'
    case 'system':
    case 'update':
    default:
      return null
  }
}

export default {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  getNotificationSettings,
  updateNotificationSettings,
  isForcedType,
  getNotificationTypeName,
  getNotificationIcon,
  getNotificationJumpUrl
}
