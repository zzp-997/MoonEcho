/**
 * 回声 - AI 聊天辅助组合式函数
 * 文件：src/composables/useChatAssist.ts
 * 说明：AI话题建议、回复建议、语气优化、温柔退出
 */

import { ref, computed, watch, onMounted, onUnmounted, type Ref } from 'vue'
import {
  getAITopics,
  getAIReplies,
  polishMessage,
  getExitPhrases,
  type AIAssistRequest,
} from '@/api/modules/chat'
import { track, EventName } from '@/utils/tracking'

// ==================== 配置 ====================

/** 冷场检测时间（毫秒）- 10分钟 */
const AWKWARD_SILENCE_DURATION = 10 * 60 * 1000

/** 回复建议显示等待时间（毫秒）- 1分钟 */
const REPLY_SUGGESTION_DELAY = 60 * 1000

/** 建议缓存有效期（毫秒）- 5分钟 */
const SUGGESTION_CACHE_DURATION = 5 * 60 * 1000

// ==================== 类型定义 ====================

/** 辅助状态 */
interface AssistState {
  /** 是否显示冷场提示 */
  showAwkwardHint: boolean
  /** 是否显示回复建议 */
  showReplySuggestion: boolean
  /** 话题建议列表 */
  topics: string[]
  /** 回复建议列表 */
  replies: string[]
  /** 温柔退出建议列表 */
  exitPhrases: string[]
  /** 是否正在加载 */
  isLoading: boolean
  /** 最后一条消息时间 */
  lastMessageTime: number | null
  /** 用户开始输入时间 */
  inputStartTime: number | null
}

// ==================== 组合式函数 ====================

export function useChatAssist(conversationId: Ref<string> | string) {
  // 将参数转换为 ref
  const conversationIdRef = typeof conversationId === 'string' ? ref(conversationId) : conversationId

  // ==================== 响应式状态 ====================

  const state = ref<AssistState>({
    showAwkwardHint: false,
    showReplySuggestion: false,
    topics: [],
    replies: [],
    exitPhrases: [],
    isLoading: false,
    lastMessageTime: null,
    inputStartTime: null,
  })

  /** 是否显示AI辅助面板 */
  const showAssistPanel = ref(false)

  /** 当前选中的建议 */
  const selectedSuggestion = ref<string | null>(null)

  /** 语气优化输入内容 */
  const polishInput = ref('')

  /** 语气优化结果 */
  const polishResult = ref('')

  /** 是否正在优化 */
  const isPolishing = ref(false)

  /** 是否显示温柔退出弹窗 */
  const showExitDialog = ref(false)

  /** 定时器ID */
  let awkwardTimer: ReturnType<typeof setTimeout> | null = null
  let replyTimer: ReturnType<typeof setTimeout> | null = null

  /** 建议缓存时间戳 */
  let topicsCacheTime = 0
  let repliesCacheTime = 0

  // ==================== 计算属性 ====================

  /** 是否有话题建议 */
  const hasTopics = computed(() => state.value.topics.length > 0)

  /** 是否有回复建议 */
  const hasReplies = computed(() => state.value.replies.length > 0)

  /** 是否有退出建议 */
  const hasExitPhrases = computed(() => state.value.exitPhrases.length > 0)

  /** 是否显示冷场提示 */
  const shouldShowAwkwardHint = computed(() => {
    return state.value.showAwkwardHint && !state.value.showReplySuggestion
  })

  // ==================== 方法 ====================

  /**
   * 记录消息时间
   */
  function recordMessageTime(): void {
    state.value.lastMessageTime = Date.now()
    state.value.showAwkwardHint = false
    state.value.showReplySuggestion = false
    clearTimers()
    scheduleAwkwardCheck()
  }

  /**
   * 记录输入开始时间
   */
  function recordInputStart(): void {
    state.value.inputStartTime = Date.now()
    clearReplyTimer()
    state.value.showReplySuggestion = false
  }

  /**
   * 记录输入结束
   */
  function recordInputEnd(): void {
    if (state.value.inputStartTime) {
      // 用户开始输入后1分钟未发送，显示回复建议
      const elapsed = Date.now() - state.value.inputStartTime
      if (elapsed < REPLY_SUGGESTION_DELAY) {
        replyTimer = setTimeout(() => {
          if (!state.value.inputStartTime) return
          loadReplySuggestions()
          state.value.showReplySuggestion = true
          track(EventName.AI_REPLY_SHOW)
        }, REPLY_SUGGESTION_DELAY - elapsed)
      }
    }
    state.value.inputStartTime = null
  }

  /**
   * 安排冷场检测
   */
  function scheduleAwkwardCheck(): void {
    clearAwkwardTimer()
    awkwardTimer = setTimeout(() => {
      state.value.showAwkwardHint = true
      track(EventName.AI_TOPIC_SHOW)
    }, AWKWARD_SILENCE_DURATION)
  }

  /**
   * 清除定时器
   */
  function clearTimers(): void {
    clearAwkwardTimer()
    clearReplyTimer()
  }

  function clearAwkwardTimer(): void {
    if (awkwardTimer) {
      clearTimeout(awkwardTimer)
      awkwardTimer = null
    }
  }

  function clearReplyTimer(): void {
    if (replyTimer) {
      clearTimeout(replyTimer)
      replyTimer = null
    }
  }

  /**
   * 加载话题建议
   */
  async function loadTopicSuggestions(context?: string): Promise<void> {
    // 检查缓存
    if (
      state.value.topics.length > 0 &&
      Date.now() - topicsCacheTime < SUGGESTION_CACHE_DURATION
    ) {
      return
    }

    state.value.isLoading = true

    try {
      const response = await getAITopics({
        conversation_id: conversationIdRef.value,
        context,
      })

      state.value.topics = response.topics
      topicsCacheTime = Date.now()
    } catch (error) {
      console.error('获取话题建议失败', error)
      // 使用默认话题
      state.value.topics = [
        '最近有什么有趣的事情吗？',
        '你最近心情怎么样？',
        '有什么想分享的吗？',
      ]
    } finally {
      state.value.isLoading = false
    }
  }

  /**
   * 加载回复建议
   */
  async function loadReplySuggestions(context?: string): Promise<void> {
    // 检查缓存
    if (
      state.value.replies.length > 0 &&
      Date.now() - repliesCacheTime < SUGGESTION_CACHE_DURATION
    ) {
      return
    }

    state.value.isLoading = true

    try {
      const response = await getAIReplies({
        conversation_id: conversationIdRef.value,
        context,
      })

      state.value.replies = response.suggestions
      repliesCacheTime = Date.now()
    } catch (error) {
      console.error('获取回复建议失败', error)
      // 使用默认回复
      state.value.replies = [
        '嗯嗯，我明白你的意思~',
        '这确实挺有意思的',
        '那你后来怎么样了？',
      ]
    } finally {
      state.value.isLoading = false
    }
  }

  /**
   * 选择话题建议
   */
  function selectTopic(topic: string): void {
    selectedSuggestion.value = topic
    showAssistPanel.value = false
    state.value.showAwkwardHint = false

    track(EventName.AI_TOPIC_USE, { topic })
  }

  /**
   * 选择回复建议
   */
  function selectReply(reply: string): void {
    selectedSuggestion.value = reply
    showAssistPanel.value = false
    state.value.showReplySuggestion = false

    track(EventName.AI_REPLY_USE, { reply })
  }

  /**
   * 语气优化
   */
  async function optimizePolish(content: string): Promise<string> {
    if (!content.trim()) return ''

    isPolishing.value = true
    polishInput.value = content

    try {
      const response = await polishMessage({
        message_content: content,
        conversation_id: conversationIdRef.value,
      })

      polishResult.value = response.polished

      track(EventName.AI_POLISH_USE, {
        original_length: content.length,
        polished_length: response.polished.length,
      })

      return response.polished
    } catch (error) {
      console.error('语气优化失败', error)
      return content
    } finally {
      isPolishing.value = false
    }
  }

  /**
   * 加载温柔退出建议
   */
  async function loadExitPhrases(context?: string): Promise<void> {
    state.value.isLoading = true

    try {
      const response = await getExitPhrases({
        conversation_id: conversationIdRef.value,
        context,
      })

      state.value.exitPhrases = response.exit_phrases
    } catch (error) {
      console.error('获取温柔退出建议失败', error)
      // 使用默认退出语
      state.value.exitPhrases = [
        '我先去忙一会，晚点再聊~',
        '今天有点累了，改天再聊吧',
        '时间不早了，早点休息哦',
      ]
    } finally {
      state.value.isLoading = false
    }
  }

  /**
   * 打开温柔退出弹窗
   */
  async function openExitDialog(): Promise<void> {
    showExitDialog.value = true
    await loadExitPhrases()
    track(EventName.AI_EXIT_SHOW)
  }

  /**
   * 选择退出建议
   */
  function selectExit(phrase: string): void {
    selectedSuggestion.value = phrase
    showExitDialog.value = false

    track(EventName.AI_EXIT_USE, { phrase })
  }

  /**
   * 关闭辅助面板
   */
  function closeAssistPanel(): void {
    showAssistPanel.value = false
  }

  /**
   * 刷新建议
   */
  async function refreshSuggestions(): Promise<void> {
    topicsCacheTime = 0
    repliesCacheTime = 0
    await Promise.all([loadTopicSuggestions(), loadReplySuggestions()])
  }

  // ==================== 监听器 ====================

  // 监听会话ID变化，重置状态
  watch(
    conversationIdRef,
    () => {
      state.value = {
        showAwkwardHint: false,
        showReplySuggestion: false,
        topics: [],
        replies: [],
        exitPhrases: [],
        isLoading: false,
        lastMessageTime: null,
        inputStartTime: null,
      }
      clearTimers()
    }
  )

  // ==================== 生命周期 ====================

  onMounted(() => {
    // 开始检测冷场
    scheduleAwkwardCheck()
  })

  onUnmounted(() => {
    clearTimers()
  })

  return {
    // 状态
    state,
    showAssistPanel,
    selectedSuggestion,
    polishInput,
    polishResult,
    isPolishing,
    showExitDialog,

    // 计算属性
    hasTopics,
    hasReplies,
    hasExitPhrases,
    shouldShowAwkwardHint,

    // 方法
    recordMessageTime,
    recordInputStart,
    recordInputEnd,
    loadTopicSuggestions,
    loadReplySuggestions,
    selectTopic,
    selectReply,
    optimizePolish,
    openExitDialog,
    selectExit,
    closeAssistPanel,
    refreshSuggestions,
  }
}

// ==================== 工具函数 ====================

/**
 * 检测文本情感倾向
 */
export function detectEmotion(text: string): 'positive' | 'neutral' | 'negative' {
  const positiveKeywords = ['开心', '高兴', '喜欢', '谢谢', '太棒了', '哈哈']
  const negativeKeywords = ['难过', '不开心', '烦', '讨厌', '无聊', '累']

  const lowerText = text.toLowerCase()

  if (positiveKeywords.some((k) => lowerText.includes(k))) {
    return 'positive'
  }
  if (negativeKeywords.some((k) => lowerText.includes(k))) {
    return 'negative'
  }
  return 'neutral'
}

/**
 * 生成问候语建议
 */
export function generateGreetingSuggestions(): string[] {
  return [
    '你好呀~ 很高兴认识你',
    '嗨~ 看到你发的内容很有共鸣',
    '你好，我们可以交个朋友吗？',
  ]
}
