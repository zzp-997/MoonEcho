/**
 * 回声 - WebSocket 连接管理
 * 文件：src/composables/useWebSocket.ts
 * 说明：私聊 WebSocket 连接管理，支持心跳、断线重连、消息确认
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import {
  type WSConnectionStatus,
  type WSMessage,
  type WSSendMessage,
  type WSReceivedMessage,
  type WSMessageAck,
  type ChatMessageType,
  generateMessageId,
} from '@/api/modules/chat'
import { track, EventName } from '@/utils/tracking'

// ==================== 配置 ====================

/** WebSocket 基础地址 */
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws/chat'

/** 心跳间隔（毫秒） */
const HEARTBEAT_INTERVAL = 30000

/** 重连延迟配置（毫秒）- 指数退避 */
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000]

/** 消息确认超时时间（毫秒） */
const ACK_TIMEOUT = 10000

// ==================== 类型定义 ====================

/** 消息状态 */
interface MessageState {
  clientMessageId: string
  status: 'pending' | 'sent' | 'failed'
  retryCount: number
  timer?: ReturnType<typeof setTimeout>
}

/** 消息处理器 */
type MessageHandler = (message: WSReceivedMessage['payload']) => void

/** 输入状态处理器 */
type TypingHandler = (data: { conversationId: string; userId: string; isTyping: boolean }) => void

/** 已读状态处理器 */
type ReadHandler = (data: { conversationId: string; readerId: string; readAt: string }) => void

// ==================== 全局状态 ====================

/** WebSocket 实例 */
let wsInstance: UniApp.SocketTask | null = null

/** 连接状态 */
const connectionStatus = ref<WSConnectionStatus>('disconnected')

/** 重连索引 */
let reconnectIndex = 0

/** 重连定时器 */
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

/** 心跳定时器 */
let heartbeatTimer: ReturnType<typeof setInterval> | null = null

/** 待确认消息 Map */
const pendingMessages = new Map<string, MessageState>()

/** 消息处理器列表 */
const messageHandlers: MessageHandler[] = []

/** 输入状态处理器列表 */
const typingHandlers: TypingHandler[] = []

/** 已读状态处理器列表 */
const readHandlers: ReadHandler[] = []

/** 当前会话ID（用于标记当前活跃会话） */
const activeConversationId = ref<string | null>(null)

// ==================== 组合式函数 ====================

export function useWebSocket() {
  const userStore = useUserStore()

  // ==================== 计算属性 ====================

  /** 是否已连接 */
  const isConnected = computed(() => connectionStatus.value === 'connected')

  /** 是否正在连接 */
  const isConnecting = computed(() => connectionStatus.value === 'connecting')

  /** 是否正在重连 */
  const isReconnecting = computed(() => connectionStatus.value === 'reconnecting')

  /** 连接状态文本 */
  const statusText = computed(() => {
    const statusMap: Record<WSConnectionStatus, string> = {
      connecting: '连接中...',
      connected: '已连接',
      disconnected: '未连接',
      reconnecting: '重新连接中...',
      error: '连接错误',
    }
    return statusMap[connectionStatus.value]
  })

  // ==================== 核心方法 ====================

  /**
   * 连接 WebSocket
   */
  function connect(): void {
    if (wsInstance && connectionStatus.value === 'connected') {
      return
    }

    const token = userStore.token
    if (!token) {
      console.error('[WebSocket] 未找到 Token，无法连接')
      connectionStatus.value = 'error'
      return
    }

    connectionStatus.value = 'connecting'

    const url = `${WS_BASE_URL}?token=${token}`

    wsInstance = uni.connectSocket({
      url,
      success: () => {
        console.log('[WebSocket] 连接请求已发送')
        track(EventName.WEBSOCKET_CONNECT)
      },
      fail: (err) => {
        console.error('[WebSocket] 连接失败', err)
        connectionStatus.value = 'error'
        scheduleReconnect()
      },
    })

    // 监听连接打开
    wsInstance.onOpen(() => {
      console.log('[WebSocket] 连接已建立')
      connectionStatus.value = 'connected'
      reconnectIndex = 0
      startHeartbeat()

      // 重发待确认消息
      resendPendingMessages()
    })

    // 监听消息
    wsInstance.onMessage((res) => {
      handleRawMessage(res.data)
    })

    // 监听错误
    wsInstance.onError((err) => {
      console.error('[WebSocket] 连接错误', err)
      connectionStatus.value = 'error'
      track(EventName.WEBSOCKET_DISCONNECT, { reason: 'error' })
    })

    // 监听关闭
    wsInstance.onClose((res) => {
      console.log('[WebSocket] 连接关闭', res.code, res.reason)
      connectionStatus.value = 'disconnected'
      stopHeartbeat()
      track(EventName.WEBSOCKET_DISCONNECT, { reason: 'close', code: res.code })

      // 非正常关闭时尝试重连
      if (res.code !== 1000) {
        scheduleReconnect()
      }
    })
  }

  /**
   * 断开连接
   */
  function disconnect(): void {
    stopHeartbeat()
    clearReconnectTimer()

    if (wsInstance) {
      wsInstance.close({
        code: 1000,
        reason: 'User disconnect',
      })
      wsInstance = null
    }

    connectionStatus.value = 'disconnected'
    pendingMessages.clear()
  }

  /**
   * 发送消息
   */
  function sendMessage(
    conversationId: string,
    content: string,
    messageType: ChatMessageType = 'text',
    imageUrl?: string
  ): string {
    const clientMessageId = generateMessageId()

    const message: WSSendMessage = {
      type: 'message',
      payload: {
        conversation_id: conversationId,
        content,
        message_type: messageType,
        image_url: imageUrl,
        client_message_id: clientMessageId,
      },
    }

    // 添加到待确认队列
    pendingMessages.set(clientMessageId, {
      clientMessageId,
      status: 'pending',
      retryCount: 0,
    })

    // 设置确认超时
    const state = pendingMessages.get(clientMessageId)!
    state.timer = setTimeout(() => {
      handleAckTimeout(clientMessageId)
    }, ACK_TIMEOUT)

    // 发送消息
    sendRawMessage(message)

    track(EventName.CHAT_PRIVATE_SEND, {
      message_type: messageType,
      has_image: !!imageUrl,
    })

    return clientMessageId
  }

  /**
   * 发送原始消息
   */
  function sendRawMessage(message: WSMessage): boolean {
    if (!wsInstance || connectionStatus.value !== 'connected') {
      console.error('[WebSocket] 未连接，无法发送消息')
      return false
    }

    try {
      wsInstance.send({
        data: JSON.stringify(message),
        success: () => {
          console.log('[WebSocket] 消息发送成功', message.type)
        },
        fail: (err) => {
          console.error('[WebSocket] 消息发送失败', err)
        },
      })
      return true
    } catch (err) {
      console.error('[WebSocket] 发送消息异常', err)
      return false
    }
  }

  /**
   * 发送心跳
   */
  function sendHeartbeat(): void {
    sendRawMessage({
      type: 'heartbeat',
      payload: {},
      timestamp: Date.now(),
    })
  }

  /**
   * 发送输入状态
   */
  function sendTyping(conversationId: string, isTyping: boolean): void {
    sendRawMessage({
      type: 'typing',
      payload: {
        conversation_id: conversationId,
        is_typing: isTyping,
      },
      timestamp: Date.now(),
    })
  }

  /**
   * 设置当前活跃会话
   */
  function setActiveConversation(conversationId: string | null): void {
    activeConversationId.value = conversationId
  }

  // ==================== 消息处理 ====================

  /**
   * 处理原始消息
   */
  function handleRawMessage(data: string | ArrayBuffer): void {
    try {
      const message = JSON.parse(data as string) as WSMessage

      switch (message.type) {
        case 'message':
          handleChatMessage(message as WSReceivedMessage)
          break
        case 'message_ack':
          handleMessageAck(message as WSMessageAck)
          break
        case 'message_read':
          handleMessageRead(message as WSMessage['payload'])
          break
        case 'typing':
          handleTyping(message as WSMessage['payload'])
          break
        case 'heartbeat':
          // 心跳响应，无需处理
          break
        case 'error':
          console.error('[WebSocket] 服务器错误', message.payload)
          break
        default:
          console.log('[WebSocket] 未知消息类型', message.type)
      }
    } catch (err) {
      console.error('[WebSocket] 消息解析失败', err)
    }
  }

  /**
   * 处理聊天消息
   */
  function handleChatMessage(message: WSReceivedMessage): void {
    track(EventName.CHAT_PRIVATE_RECEIVE)

    // 通知所有消息处理器
    messageHandlers.forEach((handler) => {
      handler(message.payload)
    })
  }

  /**
   * 处理消息确认
   */
  function handleMessageAck(ack: WSMessageAck): void {
    const state = pendingMessages.get(ack.payload.client_message_id)
    if (!state) return

    // 清除超时定时器
    if (state.timer) {
      clearTimeout(state.timer)
    }

    // 移除待确认消息
    pendingMessages.delete(ack.payload.client_message_id)

    if (!ack.payload.success) {
      console.error('[WebSocket] 消息确认失败', ack.payload.error)
    }
  }

  /**
   * 处理已读状态
   */
  function handleMessageRead(payload: any): void {
    readHandlers.forEach((handler) => {
      handler({
        conversationId: payload.conversation_id,
        readerId: payload.reader_id,
        readAt: payload.read_at,
      })
    })
  }

  /**
   * 处理输入状态
   */
  function handleTyping(payload: any): void {
    typingHandlers.forEach((handler) => {
      handler({
        conversationId: payload.conversation_id,
        userId: payload.user_id,
        isTyping: payload.is_typing,
      })
    })
  }

  /**
   * 处理确认超时
   */
  function handleAckTimeout(clientMessageId: string): void {
    const state = pendingMessages.get(clientMessageId)
    if (!state) return

    state.retryCount++

    if (state.retryCount >= 3) {
      // 重试次数过多，标记为失败
      state.status = 'failed'
      console.error('[WebSocket] 消息确认超时，重试次数过多', clientMessageId)
      pendingMessages.delete(clientMessageId)
      return
    }

    // 重新发送
    // 注意：这里需要重新构建消息，因为原始消息内容没有保存
    // 实际实现中应该在 pendingMessages 中保存完整消息
    state.timer = setTimeout(() => {
      handleAckTimeout(clientMessageId)
    }, ACK_TIMEOUT)
  }

  // ==================== 重连逻辑 ====================

  /**
   * 安排重连
   */
  function scheduleReconnect(): void {
    if (reconnectTimer) return

    if (reconnectIndex >= RECONNECT_DELAYS.length) {
      reconnectIndex = RECONNECT_DELAYS.length - 1
    }

    const delay = RECONNECT_DELAYS[reconnectIndex]
    console.log(`[WebSocket] ${delay}ms 后尝试重连...`)

    connectionStatus.value = 'reconnecting'

    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      reconnectIndex++
      track(EventName.WEBSOCKET_RECONNECT, { attempt: reconnectIndex })
      connect()
    }, delay)
  }

  /**
   * 清除重连定时器
   */
  function clearReconnectTimer(): void {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    reconnectIndex = 0
  }

  /**
   * 重发待确认消息
   */
  function resendPendingMessages(): void {
    // 实际实现中应该重发所有 pending 状态的消息
    console.log('[WebSocket] 重发待确认消息', pendingMessages.size)
  }

  // ==================== 心跳逻辑 ====================

  /**
   * 开始心跳
   */
  function startHeartbeat(): void {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      sendHeartbeat()
    }, HEARTBEAT_INTERVAL)
  }

  /**
   * 停止心跳
   */
  function stopHeartbeat(): void {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  // ==================== 事件订阅 ====================

  /**
   * 订阅消息
   */
  function onMessage(handler: MessageHandler): () => void {
    messageHandlers.push(handler)
    return () => {
      const index = messageHandlers.indexOf(handler)
      if (index !== -1) {
        messageHandlers.splice(index, 1)
      }
    }
  }

  /**
   * 订阅输入状态
   */
  function onTyping(handler: TypingHandler): () => void {
    typingHandlers.push(handler)
    return () => {
      const index = typingHandlers.indexOf(handler)
      if (index !== -1) {
        typingHandlers.splice(index, 1)
      }
    }
  }

  /**
   * 订阅已读状态
   */
  function onRead(handler: ReadHandler): () => void {
    readHandlers.push(handler)
    return () => {
      const index = readHandlers.indexOf(handler)
      if (index !== -1) {
        readHandlers.splice(index, 1)
      }
    }
  }

  // ==================== 生命周期 ====================

  onMounted(() => {
    // 自动连接
    if (userStore.isLoggedIn) {
      connect()
    }
  })

  onUnmounted(() => {
    // 注意：不要在组件卸载时断开连接，因为可能其他组件也在使用
    // 可以根据实际需求调整
  })

  return {
    // 状态
    connectionStatus,
    isConnected,
    isConnecting,
    isReconnecting,
    statusText,
    activeConversationId,

    // 方法
    connect,
    disconnect,
    sendMessage,
    sendTyping,
    setActiveConversation,

    // 事件订阅
    onMessage,
    onTyping,
    onRead,
  }
}

// ==================== 全局单例方法 ====================

/**
 * 获取连接状态（非响应式）
 */
export function getWSConnectionStatus(): WSConnectionStatus {
  return connectionStatus.value
}

/**
 * 全局连接 WebSocket
 */
export function connectWebSocket(): void {
  const userStore = useUserStore()
  if (userStore.isLoggedIn && connectionStatus.value !== 'connected') {
    // 使用组合式函数中的 connect 方法
    // 这里简化处理，实际应该在组合式函数中导出
  }
}

/**
 * 全局断开 WebSocket
 */
export function disconnectWebSocket(): void {
  if (wsInstance) {
    wsInstance.close({
      code: 1000,
      reason: 'Global disconnect',
    })
    wsInstance = null
  }
  connectionStatus.value = 'disconnected'
}
