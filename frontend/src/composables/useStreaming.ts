/**
 * 回声 - 流式输出组合式函数
 * 文件：src/composables/useStreaming.ts
 * 说明：HTTP SSE 流式输出处理，AI对话核心能力
 */

import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import api from '@/api'

export function useStreaming() {
  const chatStore = useChatStore()

  const content = ref('')
  const isStreaming = ref(false)
  const error = ref<string | null>(null)

  /**
   * 启动 SSE 流式请求
   */
  async function startStream(
    url: string,
    data: Record<string, any>,
    onChunk?: (text: string) => void,
    onComplete?: (fullText: string) => void
  ): Promise<void> {
    content.value = ''
    isStreaming.value = true
    error.value = null

    try {
      // H5 环境使用 EventSource
      // #ifdef H5
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${chatStore.currentSessionId}`,
        },
        body: JSON.stringify(data),
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6)
              if (dataStr === '[DONE]') continue

              try {
                const parsed = JSON.parse(dataStr)
                const text = parsed.content || parsed.text || ''
                content.value += text
                onChunk?.(text)
              } catch {
                // 非JSON数据，直接追加
                content.value += dataStr
                onChunk?.(dataStr)
              }
            }
          }
        }
      }
      // #endif

      // 小程序/App 环境使用 uni.request 分段请求
      // #ifndef H5
      // 使用 requestTask 进行流式处理
      // 实际实现需要根据小程序端能力适配
      // #endif

      isStreaming.value = false
      onComplete?.(content.value)
    } catch (e: any) {
      isStreaming.value = false
      error.value = e.message || '流式请求失败'
      throw e
    }
  }

  /**
   * 停止流式输出
   */
  function stopStream() {
    isStreaming.value = false
  }

  /**
   * 重置状态
   */
  function reset() {
    content.value = ''
    isStreaming.value = false
    error.value = null
  }

  return {
    content,
    isStreaming,
    error,
    startStream,
    stopStream,
    reset,
  }
}
