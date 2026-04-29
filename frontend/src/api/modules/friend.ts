/**
 * 回声 - 好友系统 API 封装
 * 文件：src/api/modules/friend.ts
 * 说明：好友列表、好友申请、拉黑等相关 API
 */

import { api } from '../index'

// ==================== 类型定义 ====================

/** 好友在线状态 */
export type FriendOnlineStatus = 'online' | 'offline' | 'busy' | 'away'

/** 好友信息 */
export interface Friend {
  id: string
  nickname: string
  avatar_url: string | null
  online_status: FriendOnlineStatus
  last_message?: {
    content: string
    created_at: string
  }
  unread_count: number
  personality_tags?: string[]
  is_ai?: boolean
  ai_type?: string // 'xiaowen' | 'laohei' | 'ali'
  created_at: string
}

/** 好友列表响应 */
export interface FriendListResponse {
  friends: Friend[]
  total: number
}

/** 好友申请状态 */
export type RequestStatus = 'pending' | 'accepted' | 'rejected'

/** 好友申请信息 */
export interface FriendRequest {
  id: string
  requester_id: string
  requester_nickname: string
  requester_avatar_url: string | null
  greeting: string
  status: RequestStatus
  created_at: string
}

/** 好友申请列表响应 */
export interface FriendRequestListResponse {
  requests: FriendRequest[]
  total: number
  unread_count: number
}

/** 发送好友申请请求 */
export interface SendFriendRequestData {
  to_user_id: string
  greeting: string
}

/** 发送好友申请响应 */
export interface SendFriendRequestResponse {
  id: string
  status: RequestStatus
  message: string
}

/** 用户公开信息 */
export interface UserPublicProfile {
  id: string
  nickname: string
  avatar_url: string | null
  personality_tags: string[]
  bio?: string
  is_friend: boolean
  is_blocked: boolean
  has_pending_request: boolean
  recent_posts?: {
    id: string
    content: string
    created_at: string
  }[]
}

/** AI 打招呼语生成请求 */
export interface GenerateGreetingRequest {
  target_user_id: string
  context?: string
}

/** AI 打招呼语生成响应 */
export interface GenerateGreetingResponse {
  greetings: string[]
  quota_remaining: number
}

/** AI 打招呼语配额状态 */
export interface GreetingQuotaResponse {
  daily_limit: number
  used_today: number
  remaining: number
  reset_at: string
}

/** 拉黑用户信息 */
export interface BlockedUser {
  id: string
  nickname: string
  avatar_url: string | null
  blocked_at: string
}

/** 拉黑列表响应 */
export interface BlockListResponse {
  users: BlockedUser[]
  total: number
}

// ==================== API 函数 ====================

/**
 * 获取好友列表
 */
export async function getFriends(): Promise<FriendListResponse> {
  return api.get<FriendListResponse>('/friends')
}

/**
 * 删除好友
 * @param friendId 好友ID
 */
export async function deleteFriend(friendId: string): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/friends/${friendId}`)
}

/**
 * 发送好友申请
 * @param data 申请数据
 */
export async function sendFriendRequest(data: SendFriendRequestData): Promise<SendFriendRequestResponse> {
  return api.post<SendFriendRequestResponse>('/friend-requests', data)
}

/**
 * 获取收到的好友申请列表
 */
export async function getFriendRequests(): Promise<FriendRequestListResponse> {
  return api.get<FriendRequestListResponse>('/friend-requests')
}

/**
 * 同意好友申请
 * @param requestId 申请ID
 */
export async function acceptFriendRequest(requestId: string): Promise<{ accepted: boolean; friend_id: string }> {
  return api.post<{ accepted: boolean; friend_id: string }>(`/friend-requests/${requestId}/accept`)
}

/**
 * 拒绝好友申请
 * @param requestId 申请ID
 */
export async function rejectFriendRequest(requestId: string): Promise<{ rejected: boolean }> {
  return api.post<{ rejected: boolean }>(`/friend-requests/${requestId}/reject`)
}

/**
 * 获取用户公开信息
 * @param userId 用户ID
 */
export async function getUserPublicProfile(userId: string): Promise<UserPublicProfile> {
  return api.get<UserPublicProfile>(`/users/${userId}`)
}

/**
 * 拉黑用户
 * @param userId 用户ID
 */
export async function blockUser(userId: string): Promise<{ blocked: boolean }> {
  return api.post<{ blocked: boolean }>(`/users/${userId}/block`)
}

/**
 * 取消拉黑用户
 * @param userId 用户ID
 */
export async function unblockUser(userId: string): Promise<{ unblocked: boolean }> {
  return api.delete<{ unblocked: boolean }>(`/users/${userId}/block`)
}

/**
 * 获取拉黑列表
 */
export async function getBlockList(): Promise<BlockListResponse> {
  return api.get<BlockListResponse>('/blocks')
}

/**
 * AI 生成打招呼语
 * @param data 请求数据
 */
export async function generateGreeting(data: GenerateGreetingRequest): Promise<GenerateGreetingResponse> {
  return api.post<GenerateGreetingResponse>('/ai/generate-greeting', data)
}

/**
 * 获取打招呼语配额状态
 */
export async function getGreetingQuota(): Promise<GreetingQuotaResponse> {
  return api.get<GreetingQuotaResponse>('/ai/greeting-quota')
}

// ==================== 工具函数 ====================

/**
 * 获取在线状态显示文本
 */
export function getOnlineStatusText(status: FriendOnlineStatus): string {
  const statusMap: Record<FriendOnlineStatus, string> = {
    online: '在线',
    offline: '离线',
    busy: '忙碌',
    away: '离开',
  }
  return statusMap[status] || '未知'
}

/**
 * 获取在线状态颜色
 */
export function getOnlineStatusColor(status: FriendOnlineStatus): string {
  const colorMap: Record<FriendOnlineStatus, string> = {
    online: 'var(--color-success)',
    offline: 'var(--text-tertiary)',
    busy: 'var(--color-warning)',
    away: 'var(--mood-calm)',
  }
  return colorMap[status] || 'var(--text-tertiary)'
}

/**
 * 格式化最后消息时间
 */
export function formatLastMessageTime(isoString: string): string {
  if (!isoString) return ''

  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 7) return `${diffDays}天前`

    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day}`
  } catch {
    return ''
  }
}
