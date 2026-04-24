/**
 * 回声 - 对话类型定义
 * 文件：src/types/chat.d.ts
 * 说明：AI对话相关类型声明
 */

/** 消息角色 */
export type MessageRole = 'user' | 'assistant' | 'system'

/** 对话消息 */
export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  createdAt: string
  aiPersonality?: string
  isStreaming?: boolean
  emotionTag?: string
}

/** 对话会话 */
export interface ChatSession {
  id: string
  personalityType: string
  lastMessage: string
  lastMessageAt: string
  messageCount: number
  hasUnread: boolean
}

/** SSE 流式事件 */
export interface SSEEvent {
  type: 'content' | 'done' | 'error' | 'crisis_event'
  content?: string
  level?: 'yellow' | 'orange' | 'red'
  message?: string
}

/** 发送消息参数 */
export interface SendMessageParams {
  sessionId?: string
  content: string
  personalityType?: string
}
