/**
 * 回声 - AI 对话组合式函数
 * 文件：src/composables/useChat.ts
 * 说明：对话消息发送、接收、流式输出处理
 */

import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { trackChatSend, EventName, track } from '@/utils/tracking'
import type { ChatMessage } from '@/stores/chat'

export function useChat() {
  const chatStore = useChatStore()
  const userStore = useUserStore()

  const inputMessage = ref('')
  const isSending = ref(false)

  /**
   * 发送消息
   */
  async function sendMessage(content?: string): Promise<void> {
    const messageContent = content || inputMessage.value.trim()
    if (!messageContent || isSending.value) return

    isSending.value = true
    inputMessage.value = ''

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: messageContent,
      createdAt: new Date().toISOString(),
    }
    chatStore.addMessage(userMessage)

    // 追踪发送事件
    trackChatSend({
      messageLength: messageContent.length,
      personalityType: chatStore.currentPersonality,
    })

    try {
      // 流式输出时设置生成状态
      chatStore.setGenerating(true)

      // AI 回复占位
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: '',
        createdAt: new Date().toISOString(),
        aiPersonality: chatStore.currentPersonality,
        isStreaming: true,
      }
      chatStore.addMessage(assistantMessage)

      // 实际的 SSE 流式调用将在 useStreaming.ts 中实现
      // 这里仅预留接口
    } catch (error) {
      console.error('发送消息失败', error)
      chatStore.setGenerating(false)
    } finally {
      isSending.value = false
    }
  }

  /**
   * 开始新对话
   */
  function startNewSession(personality?: string) {
    chatStore.clearMessages()
    if (personality) {
      chatStore.setPersonality(personality)
    }
    track(EventName.CHAT_NEW_SESSION, {
      personalityType: personality || chatStore.currentPersonality,
    })
  }

  /**
   * 切换AI性格
   */
  function switchPersonality(personality: string) {
    chatStore.setPersonality(personality)
    track(EventName.CHAT_PERSONALITY_SELECT, { personalityType: personality })
  }

  return {
    inputMessage,
    isSending,
    messages: chatStore.messages,
    isGenerating: chatStore.isGenerating,
    sendMessage,
    startNewSession,
    switchPersonality,
  }
}
