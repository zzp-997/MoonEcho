/**
 * 回声 - AI 对话接口
 * 文件：src/api/chat.ts
 * 说明：AI 对话相关接口，包括同步对话、SSE 流式对话、对话列表、开场白等
 */

import api from './index'
import type { ApiResponse, Pagination } from '../types'

// ==================== 类型定义 ====================

/** AI 性格类型 */
export type PersonalityType = 'xiaowen' | 'laohei' | 'ali'

/** 对话消息 */
export interface ChatMessage {
  id: string
  /** 角色 */
  role: 'user' | 'assistant'
  /** 消息内容 */
  content: string
  /** 创建时间 */
  createdAt: string
  /** AI 性格 */
  personalityType?: PersonalityType
  /** 情绪标签 */
  emotionTag?: string
  /** 危机等级 */
  crisisLevel?: 'low' | 'medium' | 'high'
}

/** 对话会话 */
export interface ChatConversation {
  id: string
  /** AI 性格类型 */
  personalityType: PersonalityType
  /** 最后一条消息 */
  lastMessage: string
  /** 最后消息时间 */
  lastMessageAt: string
  /** 消息数量 */
  messageCount: number
  /** 是否有未读 */
  hasUnread: boolean
  /** 创建时间 */
  createdAt: string
}

/** 发送消息参数 */
export interface SendMessageParams {
  /** 会话ID（可选，不传则创建新会话） */
  conversationId?: string
  /** 消息内容 */
  content: string
  /** AI 性格类型（可选） */
  personalityType?: PersonalityType
}

/** 发送消息响应 */
export interface SendMessageResponse {
  /** 会话ID */
  conversationId: string
  /** 消息ID */
  messageId: string
  /** AI 回复内容 */
  content: string
  /** 危机等级 */
  crisisLevel?: 'low' | 'medium' | 'high'
  /** 危机关键词 */
  crisisKeywords?: string[]
  /** 情绪标签 */
  emotionTag?: string
}

/** 获取对话历史参数 */
export interface GetHistoryParams {
  /** 会话ID */
  conversationId: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  pageSize?: number
}

/** 获取对话历史响应 */
export interface GetHistoryResponse {
  /** 消息列表 */
  messages: ChatMessage[]
  /** 分页信息 */
  pagination: Pagination
}

/** 获取开场白响应 */
export interface GreetingResponse {
  /** 开场白内容 */
  content: string
  /** AI 性格类型 */
  personalityType: PersonalityType
}

/** AI 性格信息 */
export interface PersonalityInfo {
  /** 性格标识 */
  type: PersonalityType
  /** 显示名称 */
  name: string
  /** 简介 */
  description: string
  /** 头像URL */
  avatarUrl: string
  /** 特点标签 */
  tags: string[]
}

// ==================== API 接口 ====================

/**
 * 发送消息（同步模式）
 * @param params 发送参数
 * @returns 消息响应
 */
export function sendMessage(params: SendMessageParams): Promise<SendMessageResponse> {
  return api.post<SendMessageResponse>('/ai/chat', params)
}

/**
 * 获取 SSE 流式对话地址
 * @param params 发送参数
 * @returns 流式对话 URL（供 SSE 使用）
 */
export function getStreamUrl(): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  return `${baseUrl}/ai/chat/stream`
}

/**
 * 获取对话历史
 * @param params 查询参数
 * @returns 历史消息列表
 */
export function getChatHistory(params: GetHistoryParams): Promise<GetHistoryResponse> {
  return api.get<GetHistoryResponse>('/ai/conversations/history', params)
}

/**
 * 获取对话会话列表
 * @returns 会话列表
 */
export function getConversations(): Promise<ChatConversation[]> {
  return api.get<ChatConversation[]>('/ai/conversations')
}

/**
 * 创建新会话
 * @param personalityType AI 性格类型
 * @returns 新会话信息
 */
export function createConversation(personalityType: PersonalityType): Promise<ChatConversation> {
  return api.post<ChatConversation>('/ai/conversations', { personalityType })
}

/**
 * 删除会话
 * @param conversationId 会话ID
 */
export function deleteConversation(conversationId: string): Promise<void> {
  return api.delete(`/ai/conversations/${conversationId}`)
}

/**
 * 获取 AI 开场白
 * @param personalityType AI 性格类型（可选，默认小温）
 * @returns 开场白内容
 */
export function getGreeting(personalityType?: PersonalityType): Promise<GreetingResponse> {
  return api.post<GreetingResponse>('/ai/greeting', { personalityType })
}

/**
 * 获取 AI 性格列表
 * @returns 性格列表
 */
export function getPersonalities(): Promise<PersonalityInfo[]> {
  return api.get<PersonalityInfo[]>('/ai/personalities')
}

/**
 * 切换会话的 AI 性格
 * @param conversationId 会话ID
 * @param personalityType 新的 AI 性格
 */
export function switchPersonality(
  conversationId: string,
  personalityType: PersonalityType
): Promise<void> {
  return api.put(`/ai/conversations/${conversationId}/personality`, { personalityType })
}

/**
 * 获取用户对话统计
 * @returns 统计信息
 */
export function getChatStats(): Promise<{
  totalRounds: number
  todayRounds: number
  favoritePersonality: PersonalityType | null
  lastChatAt: string | null
}> {
  return api.get('/ai/chat/stats')
}
