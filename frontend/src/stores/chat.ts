/**
 * 回声 - 对话状态管理
 * 文件：src/stores/chat.ts
 * 说明：AI对话历史、对话状态、流式消息管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 对话消息接口 */
export interface ChatMessage {
  id: string
  /** 角色：user / assistant */
  role: 'user' | 'assistant'
  /** 消息内容 */
  content: string
  /** 创建时间 */
  createdAt: string
  /** AI角色标识 */
  aiPersonality?: string
  /** 是否正在流式输出 */
  isStreaming?: boolean
  /** 情绪标签 */
  emotionTag?: string
}

/** 对话会话接口 */
export interface ChatSession {
  id: string
  /** AI性格类型 */
  personalityType: string
  /** 最后一条消息 */
  lastMessage: string
  /** 最后消息时间 */
  lastMessageAt: string
  /** 消息数量 */
  messageCount: number
  /** 是否有未读 */
  hasUnread: boolean
}

export const useChatStore = defineStore('chat', () => {
  // ==================== 状态 ====================

  /** 当前会话ID */
  const currentSessionId = ref<string | null>(null)
  /** 当前会话消息列表 */
  const messages = ref<ChatMessage[]>([])
  /** 是否正在生成回复 */
  const isGenerating = ref(false)
  /** AI性格类型 */
  const currentPersonality = ref<string>('xiaowen')
  /** 会话列表 */
  const sessions = ref<ChatSession[]>([])

  // ==================== 计算属性 ====================

  /** 当前会话消息数量 */
  const messageCount = computed(() => messages.value.length)

  /** 今日对话轮次 */
  const todayChatRounds = computed(() => {
    const today = new Date().toDateString()
    return messages.value.filter(
      (m) => new Date(m.createdAt).toDateString() === today && m.role === 'user'
    ).length
  })

  // ==================== 方法 ====================

  /**
   * 添加消息
   */
  function addMessage(message: ChatMessage) {
    messages.value.push(message)
  }

  /**
   * 更新消息内容（流式输出用）
   */
  function updateMessage(messageId: string, content: string) {
    const msg = messages.value.find((m) => m.id === messageId)
    if (msg) {
      msg.content = content
    }
  }

  /**
   * 标记消息流式输出完成
   */
  function finishStreaming(messageId: string) {
    const msg = messages.value.find((m) => m.id === messageId)
    if (msg) {
      msg.isStreaming = false
    }
    isGenerating.value = false
  }

  /**
   * 设置生成状态
   */
  function setGenerating(generating: boolean) {
    isGenerating.value = generating
  }

  /**
   * 清空当前会话消息
   */
  function clearMessages() {
    messages.value = []
  }

  /**
   * 设置当前AI性格
   */
  function setPersonality(personality: string) {
    currentPersonality.value = personality
  }

  return {
    // 状态
    currentSessionId,
    messages,
    isGenerating,
    currentPersonality,
    sessions,
    // 计算属性
    messageCount,
    todayChatRounds,
    // 方法
    addMessage,
    updateMessage,
    finishStreaming,
    setGenerating,
    clearMessages,
    setPersonality,
  }
})
