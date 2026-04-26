/**
 * 回声 - SSE 流式通信组合式函数
 * 文件：src/composables/useSSE.ts
 * 说明：统一封装 SSE 流式通信，支持 App 端 onChunkReceived、H5 EventSource、小程序分段降级
 * 参考：frontend_tech.md SSE 流式输出跨端封装
 */

import { ref, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'

// ==================== 类型定义 ====================

/** SSE 事件数据 */
export interface SSEData {
  /** 内容片段 */
  content: string
  /** 是否完成 */
  done: boolean
  /** 危机等级 */
  crisis_level?: 'low' | 'medium' | 'high'
  /** 危机关键词 */
  crisis_keywords?: string[]
  /** 错误信息 */
  error?: string
}

/** SSE 回调函数 */
export interface SSECallbacks {
  /** 收到内容片段 */
  onChunk?: (content: string) => void
  /** 流式完成 */
  onComplete?: (data: SSEData) => void
  /** 发生错误 */
  onError?: (error: Error) => void
  /** 危机检测触发 */
  onCrisis?: (level: 'medium' | 'high', keywords?: string[]) => void
}

/** SSE 请求配置 */
export interface SSERequestConfig {
  /** API 地址 */
  url: string
  /** 请求体 */
  body: Record<string, any>
  /** 超时时间（毫秒） */
  timeout?: number
  /** 回调函数 */
  callbacks: SSECallbacks
}

// ==================== 平台检测 ====================

/**
 * 获取当前运行平台
 */
function getPlatform(): 'h5' | 'app' | 'mp' {
  // #ifdef H5
  return 'h5'
  // #endif

  // #ifdef APP-PLUS
  return 'app'
  // #endif

  // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
  return 'mp'
  // #endif

  // 默认返回 mp 作为降级方案
  return 'mp'
}

// ==================== SSE 请求处理 ====================

/**
 * SSE 流式通信组合式函数
 */
export function useSSE() {
  /** 是否正在流式传输 */
  const isStreaming = ref(false)

  /** 累计内容 */
  const streamedContent = ref('')

  /** 错误信息 */
  const error = ref<string | null>(null)

  /** 请求任务引用 */
  let requestTask: UniApp.RequestTask | null = null

  /** EventSource 引用（H5） */
  let eventSource: EventSource | null = null

  /** 定时器引用（小程序降级用） */
  let pollingTimer: ReturnType<typeof setInterval> | null = null

  /**
   * 解析 SSE 数据行
   */
  function parseSSELine(line: string): SSEData | null {
    if (!line.startsWith('data: ')) return null

    const dataStr = line.slice(6).trim()
    if (dataStr === '[DONE]') {
      return { content: '', done: true }
    }

    try {
      return JSON.parse(dataStr) as SSEData
    } catch {
      console.warn('[SSE] 解析数据失败:', dataStr)
      return null
    }
  }

  /**
   * 处理 SSE 数据
   */
  function handleSSEData(
    data: SSEData,
    callbacks: SSECallbacks
  ): void {
    // 处理错误
    if (data.error) {
      error.value = data.error
      callbacks.onError?.(new Error(data.error))
      return
    }

    // 处理内容片段
    if (data.content) {
      streamedContent.value += data.content
      callbacks.onChunk?.(data.content)
    }

    // 处理危机检测
    if (data.crisis_level && (data.crisis_level === 'medium' || data.crisis_level === 'high')) {
      callbacks.onCrisis?.(data.crisis_level, data.crisis_keywords)
    }

    // 处理完成
    if (data.done) {
      callbacks.onComplete?.(data)
    }
  }

  /**
   * H5 平台使用 fetch + ReadableStream
   */
  async function streamH5(config: SSERequestConfig): Promise<void> {
    const userStore = useUserStore()

    try {
      const response = await fetch(config.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
          'Accept': 'text/event-stream',  // 必须指定接受 SSE 流
        },
        body: JSON.stringify(config.body),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法获取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (isStreaming.value) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          const data = parseSSELine(line)
          if (data) {
            handleSSEData(data, config.callbacks)
          }
        }
      }

      // 处理剩余缓冲区
      if (buffer.trim()) {
        const data = parseSSELine(buffer)
        if (data) {
          handleSSEData(data, config.callbacks)
        }
      }
    } catch (e: any) {
      if (isStreaming.value) {
        error.value = e.message || '流式请求失败'
        config.callbacks.onError?.(e)
      }
    }
  }

  /**
   * App 平台使用 uni.request 的 onChunkReceived
   * 返回 Promise，等待流式传输完成
   */
  function streamApp(config: SSERequestConfig): Promise<void> {
    const userStore = useUserStore()
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

    return new Promise<void>((resolve, reject) => {
      let buffer = ''

      requestTask = uni.request({
        url: `${baseUrl}${config.url}`,
        method: 'POST',
        data: config.body,
        header: {
          'Content-Type': 'application/json',
          'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
          'Accept': 'text/event-stream',
        },
        timeout: config.timeout || 60000,
        enableChunked: true,
        success: () => {
          // 请求完成，处理剩余缓冲区
          if (buffer.trim()) {
            const data = parseSSELine(buffer)
            if (data) {
              handleSSEData(data, config.callbacks)
            }
          }
          resolve()
        },
        fail: (err) => {
          if (isStreaming.value) {
            error.value = err.errMsg || '请求失败'
            config.callbacks.onError?.(new Error(error.value))
            reject(new Error(error.value))
          } else {
            // 用户取消，正常结束
            resolve()
          }
        },
      } as any)

      // 监听数据块到达
      if (requestTask && 'onChunkReceived' in requestTask) {
        (requestTask as any).onChunkReceived((response: any) => {
          if (!isStreaming.value) return

          const arrayBuffer = response.data
          const decoder = new TextDecoder()
          buffer += decoder.decode(arrayBuffer, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.trim()) continue

            const data = parseSSELine(line)
            if (data) {
              handleSSEData(data, config.callbacks)
            }
          }
        })
      }
    })
  }

  /**
   * 小程序平台分段降级方案
   * 使用普通请求 + 模拟打字效果
   */
  async function streamMiniProgram(config: SSERequestConfig): Promise<void> {
    const userStore = useUserStore()
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

    try {
      // 先发送请求获取完整响应
      const response = await new Promise<any>((resolve, reject) => {
        uni.request({
          url: `${baseUrl}${config.url}`,
          method: 'POST',
          data: config.body,
          header: {
            'Content-Type': 'application/json',
            'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
          },
          timeout: config.timeout || 60000,
          success: (res) => resolve(res),
          fail: (err) => reject(err),
        })
      })

      if (!isStreaming.value) return

      const responseData = response.data as any

      // 检查响应状态
      if (response.statusCode !== 200 || !responseData.success) {
        throw new Error(responseData.error?.message || '请求失败')
      }

      // 获取完整内容
      const fullContent = responseData.data?.content || ''

      // 检查危机等级
      const crisisLevel = responseData.data?.crisis_level
      if (crisisLevel && (crisisLevel === 'medium' || crisisLevel === 'high')) {
        config.callbacks.onCrisis?.(crisisLevel, responseData.data?.crisis_keywords)
      }

      // 分段显示，模拟打字效果
      if (fullContent) {
        const chunkSize = 3 // 每次显示的字符数
        let currentIndex = 0

        await new Promise<void>((resolve) => {
          pollingTimer = setInterval(() => {
            if (!isStreaming.value || currentIndex >= fullContent.length) {
              if (pollingTimer) {
                clearInterval(pollingTimer)
                pollingTimer = null
              }
              resolve()
              return
            }

            const chunk = fullContent.slice(currentIndex, currentIndex + chunkSize)
            streamedContent.value += chunk
            config.callbacks.onChunk?.(chunk)
            currentIndex += chunkSize
          }, 50) // 每50ms显示一段
        })
      }

      // 完成回调
      config.callbacks.onComplete?.({
        content: fullContent,
        done: true,
        crisis_level: responseData.data?.crisis_level,
        crisis_keywords: responseData.data?.crisis_keywords,
      })
    } catch (e: any) {
      if (isStreaming.value) {
        error.value = e.message || '请求失败'
        config.callbacks.onError?.(e)
      }
    }
  }

  /**
   * 启动 SSE 流式请求
   */
  async function startStream(config: SSERequestConfig): Promise<void> {
    // 重置状态
    isStreaming.value = true
    streamedContent.value = ''
    error.value = null

    const platform = getPlatform()

    switch (platform) {
      case 'h5':
        await streamH5(config)
        break
      case 'app':
        streamApp(config)
        break
      case 'mp':
      default:
        await streamMiniProgram(config)
        break
    }
  }

  /**
   * 停止流式传输
   */
  function stopStream(): void {
    isStreaming.value = false

    // 清理 App 请求任务
    if (requestTask) {
      requestTask.abort()
      requestTask = null
    }

    // 清理 H5 EventSource
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    // 清理小程序定时器
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  /**
   * 重置状态
   */
  function reset(): void {
    stopStream()
    streamedContent.value = ''
    error.value = null
  }

  // 组件卸载时清理
  onUnmounted(() => {
    stopStream()
  })

  return {
    isStreaming,
    streamedContent,
    error,
    startStream,
    stopStream,
    reset,
    getPlatform,
  }
}
