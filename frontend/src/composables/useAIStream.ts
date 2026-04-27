/**
 * 回声 - AI 流式输出跨端封装
 * 文件：src/composables/useAIStream.ts
 * 说明：统一封装 AI 流式输出，支持 App 端原生 SSE、H5 EventSource、小程序分段降级
 * 作者：Frontend Developer
 */

import { ref, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'

// ==================== 类型定义 ====================

/** 流式数据结构 */
export interface StreamData {
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
  /** 消息ID */
  message_id?: string
  /** 创建时间 */
  created_at?: string
}

/** 流式回调函数 */
export interface StreamCallbacks {
  /** 收到内容片段 */
  onChunk?: (content: string, accumulated: string) => void
  /** 流式完成 */
  onComplete?: (data: StreamData) => void
  /** 发生错误 */
  onError?: (error: Error) => void
  /** 危机检测触发 */
  onCrisis?: (level: 'medium' | 'high', keywords?: string[]) => void
  /** 开始流式传输 */
  onStart?: () => void
}

/** 流式请求配置 */
export interface StreamRequestConfig {
  /** API 路径 */
  url: string
  /** 请求体 */
  body: Record<string, any>
  /** 超时时间（毫秒），默认 60000 */
  timeout?: number
  /** 回调函数 */
  callbacks: StreamCallbacks
  /** 分段显示间隔（毫秒），小程序降级时使用，默认 50 */
  chunkInterval?: number
  /** 分段字符数，小程序降级时使用，默认 3 */
  chunkSize?: number
}

/** 平台类型 */
export type Platform = 'h5' | 'app' | 'mp-weixin' | 'mp-alipay' | 'mp'

// ==================== 平台检测 ====================

/**
 * 获取当前运行平台
 * @returns 平台类型
 */
export function getPlatform(): Platform {
  // #ifdef H5
  return 'h5'
  // #endif

  // #ifdef APP-PLUS
  return 'app'
  // #endif

  // #ifdef MP-WEIXIN
  return 'mp-weixin'
  // #endif

  // #ifdef MP-ALIPAY
  return 'mp-alipay'
  // #endif

  // #ifdef MP-BAIDU || MP-TOUTIAO || MP-QQ
  return 'mp'
  // #endif

  // 默认返回 mp 作为降级方案
  return 'mp'
}

/**
 * 检测是否为小程序环境
 * @returns 是否为小程序环境
 */
export function isMiniProgram(): boolean {
  const platform = getPlatform()
  return platform.startsWith('mp') || platform === 'mp-weixin' || platform === 'mp-alipay'
}

/**
 * 检测是否支持原生 SSE
 * @returns 是否支持原生 SSE
 */
export function supportsNativeSSE(): boolean {
  // App 端和 H5 支持原生 SSE
  // 小程序不支持，需要降级
  return !isMiniProgram()
}

// ==================== SSE 数据解析 ====================

/**
 * 解析 SSE 数据行
 * @param line SSE 数据行
 * @returns 解析后的数据或 null
 */
function parseSSELine(line: string): StreamData | null {
  if (!line.startsWith('data: ')) return null

  const dataStr = line.slice(6).trim()
  if (dataStr === '[DONE]') {
    return { content: '', done: true }
  }

  try {
    return JSON.parse(dataStr) as StreamData
  } catch {
    console.warn('[useAIStream] 解析数据失败:', dataStr)
    return null
  }
}

// ==================== 组合式函数 ====================

/**
 * AI 流式输出组合式函数
 *
 * @example
 * ```typescript
 * const {
 *   isStreaming,
 *   streamedContent,
 *   startStream,
 *   stopStream
 * } = useAIStream()
 *
 * await startStream({
 *   url: '/chat/stream',
 *   body: { message: '你好' },
 *   callbacks: {
 *     onChunk: (chunk, accumulated) => {
 *       console.log('收到片段:', chunk)
 *     },
 *     onComplete: (data) => {
 *       console.log('完成:', data)
 *     },
 *     onError: (error) => {
 *       console.error('错误:', error)
 *     }
 *   }
 * })
 * ```
 */
export function useAIStream() {
  // ==================== 状态 ====================

  /** 是否正在流式传输 */
  const isStreaming = ref(false)

  /** 累计内容 */
  const streamedContent = ref('')

  /** 错误信息 */
  const error = ref<string | null>(null)

  /** 当前平台 */
  const platform = ref<Platform>(getPlatform())

  /** 请求任务引用（App 端） */
  let requestTask: UniApp.RequestTask | null = null

  /** EventSource 引用（H5） */
  let eventSource: EventSource | null = null

  /** 定时器引用（小程序降级用） */
  let pollingTimer: ReturnType<typeof setInterval> | null = null

  /** AbortController 引用（H5 fetch） */
  let abortController: AbortController | null = null

  // ==================== H5 平台实现 ====================

  /**
   * H5 平台使用 fetch + ReadableStream
   */
  async function streamH5(config: StreamRequestConfig): Promise<void> {
    const userStore = useUserStore()
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

    abortController = new AbortController()

    try {
      const response = await fetch(`${baseUrl}${config.url}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(config.body),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法获取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      // 触发开始回调
      config.callbacks.onStart?.()

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
            handleStreamData(data, config.callbacks)
          }
        }
      }

      // 处理剩余缓冲区
      if (buffer.trim()) {
        const data = parseSSELine(buffer)
        if (data) {
          handleStreamData(data, config.callbacks)
        }
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        // 用户取消，正常结束
        return
      }
      if (isStreaming.value) {
        error.value = e.message || '流式请求失败'
        config.callbacks.onError?.(e)
      }
    }
  }

  // ==================== App 平台实现 ====================

  /**
   * App 平台使用 uni.request 的 onChunkReceived
   */
  function streamApp(config: StreamRequestConfig): Promise<void> {
    const userStore = useUserStore()
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

    return new Promise<void>((resolve, reject) => {
      let buffer = ''

      // 触发开始回调
      config.callbacks.onStart?.()

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
              handleStreamData(data, config.callbacks)
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
              handleStreamData(data, config.callbacks)
            }
          }
        })
      }
    })
  }

  // ==================== 小程序平台降级实现 ====================

  /**
   * 小程序平台分段降级方案
   * 使用普通请求获取完整响应 + 模拟打字效果
   */
  async function streamMiniProgram(config: StreamRequestConfig): Promise<void> {
    const userStore = useUserStore()
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

    try {
      // 触发开始回调
      config.callbacks.onStart?.()

      // #ifdef MP-WEIXIN
      // 微信小程序尝试使用 enableChunked（部分版本支持）
      const canUseChunked = checkWeixinChunkedSupport()
      if (canUseChunked) {
        await streamWeixinMP(config, baseUrl, userStore.token)
        return
      }
      // #endif

      // 降级方案：普通请求 + 分段显示
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
        await simulateTyping(fullContent, config)
      }

      // 完成回调
      config.callbacks.onComplete?.({
        content: fullContent,
        done: true,
        message_id: responseData.data?.message_id,
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
   * 模拟打字效果
   */
  async function simulateTyping(
    fullContent: string,
    config: StreamRequestConfig
  ): Promise<void> {
    const chunkSize = config.chunkSize || 3
    const interval = config.chunkInterval || 50
    let currentIndex = 0

    return new Promise<void>((resolve) => {
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
        config.callbacks.onChunk?.(chunk, streamedContent.value)
        currentIndex += chunkSize
      }, interval)
    })
  }

  /**
   * 微信小程序尝试使用 chunked 传输（实验性）
   */
  // #ifdef MP-WEIXIN
  async function streamWeixinMP(
    config: StreamRequestConfig,
    baseUrl: string,
    token: string | null
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      let buffer = ''

      const task = uni.request({
        url: `${baseUrl}${config.url}`,
        method: 'POST',
        data: config.body,
        header: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          'Accept': 'text/event-stream',
        },
        timeout: config.timeout || 60000,
        enableChunked: true,
        success: () => {
          if (buffer.trim()) {
            const data = parseSSELine(buffer)
            if (data) {
              handleStreamData(data, config.callbacks)
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
            resolve()
          }
        },
      } as any)

      // 微信小程序的 chunked 支持（实验性）
      if (task && 'onChunkReceived' in task) {
        (task as any).onChunkReceived((response: any) => {
          if (!isStreaming.value) return

          try {
            const arrayBuffer = response.data
            const decoder = new TextDecoder()
            buffer += decoder.decode(arrayBuffer, { stream: true })

            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (!line.trim()) continue
              const data = parseSSELine(line)
              if (data) {
                handleStreamData(data, config.callbacks)
              }
            }
          } catch (e) {
            console.warn('[useAIStream] 微信小程序 chunked 处理异常:', e)
          }
        })
      }

      requestTask = task
    })
  }

  /**
   * 检查微信小程序是否支持 enableChunked
   */
  function checkWeixinChunkedSupport(): boolean {
    try {
      // 检查基础库版本，enableChunked 需要 2.20.0 以上
      // @ts-ignore
      const systemInfo = uni.getSystemInfoSync()
      const SDKVersion = systemInfo.SDKVersion || '0.0.0'
      const [major, minor] = SDKVersion.split('.').map(Number)
      return major > 2 || (major === 2 && minor >= 20)
    } catch {
      return false
    }
  }
  // #endif

  // ==================== 数据处理 ====================

  /**
   * 处理流式数据
   */
  function handleStreamData(data: StreamData, callbacks: StreamCallbacks): void {
    // 处理错误
    if (data.error) {
      error.value = data.error
      callbacks.onError?.(new Error(data.error))
      return
    }

    // 处理内容片段
    if (data.content) {
      streamedContent.value += data.content
      callbacks.onChunk?.(data.content, streamedContent.value)
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

  // ==================== 公开方法 ====================

  /**
   * 启动流式请求
   */
  async function startStream(config: StreamRequestConfig): Promise<void> {
    // 重置状态
    isStreaming.value = true
    streamedContent.value = ''
    error.value = null

    const currentPlatform = getPlatform()

    switch (currentPlatform) {
      case 'h5':
        await streamH5(config)
        break
      case 'app':
        await streamApp(config)
        break
      case 'mp-weixin':
      case 'mp-alipay':
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

    // 清理 H5 AbortController
    if (abortController) {
      abortController.abort()
      abortController = null
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
    // 状态
    isStreaming,
    streamedContent,
    error,
    platform,
    // 方法
    startStream,
    stopStream,
    reset,
    // 工具函数
    getPlatform,
    isMiniProgram,
    supportsNativeSSE,
  }
}

// ==================== 导出 ====================

export default useAIStream
