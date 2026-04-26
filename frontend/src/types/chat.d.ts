/**
 * 回声 - 对话类型定义
 * 文件：src/types/chat.d.ts
 * 说明：AI对话相关类型���明
 */

/** 消息角色 */
export type MessageRole = 'user' | 'assistant' | 'system'

/** AI 性格类型 */
export type PersonalityType = 'xiaowen' | 'laohei' | 'ali'

/** 危机等级 */
export type CrisisLevel = 'low' | 'medium' | 'high'

/** 对话消息 */
export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  createdAt: string
  aiPersonality?: PersonalityType
  isStreaming?: boolean
  emotionTag?: string
  crisisLevel?: CrisisLevel
}

/** 对话会话 */
export interface ChatSession {
  id: string
  personalityType: PersonalityType
  lastMessage: string
  lastMessageAt: string
  messageCount: number
  hasUnread: boolean
}

/** SSE 流式事件 */
export interface SSEEvent {
  type: 'content' | 'done' | 'error' | 'crisis_event'
  content?: string
  level?: CrisisLevel
  crisisKeywords?: string[]
  message?: string
}

/** 发送消息参数 */
export interface SendMessageParams {
  conversationId?: string
  content: string
  personalityType?: PersonalityType
}

/** SSE 数据响应 */
export interface SSEData {
  content: string
  done: boolean
  crisis_level?: CrisisLevel
  crisis_keywords?: string[]
  error?: string
}
