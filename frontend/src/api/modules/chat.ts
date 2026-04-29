/**
 * 回声 - 对话接口
 * 文件：src/api/modules/chat.ts
 * 说明：AI对话相关接口 + 私聊消息接口
 */

import { api } from '../index'
import type { SendMessageParams } from '@/types/chat'

// ==================== AI 对话接口 ====================

/** 发送消息（SSE流式响应入口） */
export function sendMessage(params: SendMessageParams) {
  return api.post('/chat/send', params)
}

/** 获取对话历史 */
export function getChatHistory(sessionId: string, page = 1, pageSize = 50) {
  return api.get('/chat/history', { sessionId, page, pageSize })
}

/** 获取会话列表 */
export function getChatSessions() {
  return api.get('/chat/sessions')
}

/** 创建新会话 */
export function createChatSession(personalityType: string) {
  return api.post('/chat/sessions', { personalityType })
}

/** 删除会话 */
export function deleteChatSession(sessionId: string) {
  return api.delete(`/chat/sessions/${sessionId}`)
}

// ==================== 私聊类型定义 ====================

/** 会话信息 */
export interface Conversation {
  id: string
  friend_id: string
  friend_nickname: string
  friend_avatar_url: string | null
  last_message?: ChatMessage
  unread_count: number
  created_at: string
  updated_at: string
}

/** 会话列表响应 */
export interface ConversationListResponse {
  conversations: Conversation[]
  total: number
}

/** 会话详情响应 */
export interface ConversationDetailResponse {
  conversation: Conversation
  friend: {
    id: string
    nickname: string
    avatar_url: string | null
    online_status: string
  }
}

/** 聊天消息类型 */
export type ChatMessageType = 'text' | 'image'

/** 聊天消息 */
export interface ChatMessage {
  id: string
  conversation_id: string
  sender_id: string
  content: string
  message_type: ChatMessageType
  image_url?: string
  is_read: boolean
  created_at: string
  expires_at?: string
}

/** 消息列表响应 */
export interface MessageListResponse {
  messages: ChatMessage[]
  pagination: {
    page: number
    page_size: number
    total: number
    has_more: boolean
  }
}

/** 发送消息请求 */
export interface SendMessageData {
  content: string
  message_type?: ChatMessageType
  image_url?: string
}

/** 上传聊天图片响应 */
export interface UploadChatImageResponse {
  url: string
  thumbnail_url?: string
}

/** 社交能量信息 */
export interface SocialEnergy {
  current_energy: number // 0-100
  max_energy: number
  activities: SocialActivity[]
  suggestion: string
  last_rest_at?: string
}

/** 社交活动 */
export interface SocialActivity {
  id: string
  type: 'message_sent' | 'message_reply' | 'friend_request' | 'post_created' | 'comment_created'
  description: string
  energy_cost: number
  created_at: string
}

/** 社交能量响应 */
export interface SocialEnergyResponse {
  energy: SocialEnergy
}

/** AI 聊天辅助请求 */
export interface AIAssistRequest {
  context?: string
  conversation_id?: string
  message_content?: string
}

/** AI 话题建议响应 */
export interface AITopicResponse {
  topics: string[]
}

/** AI 回复建议响应 */
export interface AIReplyResponse {
  suggestions: string[]
}

/** AI 语气优化响应 */
export interface AIPolishResponse {
  original: string
  polished: string
}

/** AI 温柔退出响应 */
export interface AIExitResponse {
  exit_phrases: string[]
}

// ==================== 私聊 API 函数 ====================

/**
 * 获取会话列表
 */
export async function getConversations(): Promise<ConversationListResponse> {
  return api.get<ConversationListResponse>('/conversations')
}

/**
 * 获取会话详情
 * @param conversationId 会话ID
 */
export async function getConversationDetail(conversationId: string): Promise<ConversationDetailResponse> {
  return api.get<ConversationDetailResponse>(`/conversations/${conversationId}`)
}

/**
 * 获取历史消息
 * @param conversationId 会话ID
 * @param params 分页参数
 */
export async function getMessages(
  conversationId: string,
  params?: { page?: number; page_size?: number; before?: string }
): Promise<MessageListResponse> {
  return api.get<MessageListResponse>(`/conversations/${conversationId}/messages`, params)
}

/**
 * 标记消息已读
 * @param conversationId 会话ID
 */
export async function markAsRead(conversationId: string): Promise<{ marked: boolean }> {
  return api.post<{ marked: boolean }>(`/conversations/${conversationId}/read`)
}

/**
 * 上传聊天图片
 * @param filePath 本地文件路径
 */
export async function uploadChatImage(filePath: string): Promise<UploadChatImageResponse> {
  return api.upload<UploadChatImageResponse>('/chat/images', filePath, 'image')
}

/**
 * 获取社交能量
 */
export async function getSocialEnergy(): Promise<SocialEnergyResponse> {
  return api.get<SocialEnergyResponse>('/users/me/social-energy')
}

/**
 * 主动休息（暂停社交）
 */
export async function restSocialEnergy(): Promise<{ success: boolean; rest_until?: string }> {
  return api.post<{ success: boolean; rest_until?: string }>('/users/me/social-energy/rest')
}

/**
 * AI 话题建议（冷场时）
 * @param data 请求数据
 */
export async function getAITopics(data: AIAssistRequest): Promise<AITopicResponse> {
  return api.post<AITopicResponse>('/ai/chat-assist/topic', data)
}

/**
 * AI 回复建议
 * @param data 请求数据
 */
export async function getAIReplies(data: AIAssistRequest): Promise<AIReplyResponse> {
  return api.post<AIReplyResponse>('/ai/chat-assist/reply', data)
}

/**
 * AI 语气优化
 * @param data 请求数据
 */
export async function polishMessage(data: AIAssistRequest): Promise<AIPolishResponse> {
  return api.post<AIPolishResponse>('/ai/chat-assist/polish', data)
}

/**
 * AI 温柔退出建议
 * @param data 请求数据
 */
export async function getExitPhrases(data: AIAssistRequest): Promise<AIExitResponse> {
  return api.post<AIExitResponse>('/ai/chat-assist/exit', data)
}

// ==================== WebSocket 相关类型 ====================

/** WebSocket 连接状态 */
export type WSConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'

/** WebSocket 消息类型 */
export type WSMessageType = 'message' | 'message_ack' | 'message_read' | 'typing' | 'heartbeat' | 'error'

/** WebSocket 消息 */
export interface WSMessage {
  type: WSMessageType
  payload: any
  timestamp: number
}

/** WebSocket 发送消息 */
export interface WSSendMessage {
  type: 'message'
  payload: {
    conversation_id: string
    content: string
    message_type: ChatMessageType
    image_url?: string
    client_message_id: string
  }
}

/** WebSocket 收到消息 */
export interface WSReceivedMessage {
  type: 'message'
  payload: {
    id: string
    conversation_id: string
    sender_id: string
    content: string
    message_type: ChatMessageType
    image_url?: string
    created_at: string
    client_message_id?: string
  }
}

/** WebSocket 消息确认 */
export interface WSMessageAck {
  type: 'message_ack'
  payload: {
    client_message_id: string
    server_message_id: string
    success: boolean
    error?: string
  }
}

/** WebSocket 消息已读 */
export interface WSMessageRead {
  type: 'message_read'
  payload: {
    conversation_id: string
    reader_id: string
    read_at: string
  }
}

/** WebSocket 正在输入 */
export interface WSTyping {
  type: 'typing'
  payload: {
    conversation_id: string
    user_id: string
    is_typing: boolean
  }
}

// ==================== 工具函数 ====================

/**
 * 压缩图片
 * @param filePath 原始文件路径
 * @param quality 压缩质量 0-100
 * @returns 压缩后的临时文件路径
 */
export function compressChatImage(filePath: string, quality = 80): Promise<string> {
  return new Promise((resolve, reject) => {
    uni.compressImage({
      src: filePath,
      quality,
      success: (res) => {
        resolve(res.tempFilePath)
      },
      fail: (err) => {
        reject(err)
      },
    })
  })
}

/**
 * 格式化消息时间
 */
export function formatMessageTime(isoString: string): string {
  if (!isoString) return ''

  try {
    const date = new Date(isoString)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()

    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const timeStr = `${hours}:${minutes}`

    if (isToday) {
      return timeStr
    }

    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (date.toDateString() === yesterday.toDateString()) {
      return `昨天 ${timeStr}`
    }

    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day} ${timeStr}`
  } catch {
    return ''
  }
}

/**
 * 生成消息ID
 */
export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * 获取活动类型显示文本
 */
export function getActivityTypeText(type: SocialActivity['type']): string {
  const typeMap: Record<SocialActivity['type'], string> = {
    message_sent: '发送消息',
    message_reply: '回复消息',
    friend_request: '发送好友申请',
    post_created: '发布动态',
    comment_created: '发表评论',
  }
  return typeMap[type] || '社交活动'
}

/**
 * 获取活动能量变化描述
 */
export function getActivityEnergyText(energy: SocialEnergy): string {
  const percent = Math.round((energy.current_energy / energy.max_energy) * 100)
  if (percent >= 80) return '能量充足'
  if (percent >= 60) return '能量良好'
  if (percent >= 40) return '能量一般'
  if (percent >= 20) return '能量较低'
  return '能量不足'
}
