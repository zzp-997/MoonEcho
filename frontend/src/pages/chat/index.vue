<template>
  <view class="chat-page">
    <!-- 消息列表区域 -->
    <scroll-view
      class="message-list"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
      :scroll-anchoring="true"
      @scrolltoupper="handleLoadMore"
    >
      <!-- 加载更多指示器 -->
      <view v-if="isLoadingMore" class="loading-indicator">
        <text class="loading-text">加载更多消息...</text>
      </view>

      <!-- 空状态提示 -->
      <view v-if="messages.length === 0 && !isGenerating" class="empty-state">
        <view class="empty-avatar">
          <text class="avatar-label">{{ currentPersonalityLabel }}</text>
        </view>
        <view class="empty-content">
          <text class="empty-title">{{ currentPersonalityName }}</text>
          <text class="empty-message">{{ greetingMessage }}</text>
        </view>
        <view class="empty-guide">
          <text class="guide-text">点击下方输入框开始对话</text>
        </view>
      </view>

      <!-- 消息列表 -->
      <view v-for="(message, index) in messages" :key="message.id" class="message-wrapper">
        <MessageBubble
          :message="message"
          :show-time="shouldShowTime(index)"
          :show-user-avatar="true"
          :user-avatar="userAvatar"
        />
      </view>

      <!-- AI 正在生成提示 -->
      <view v-if="isGenerating && !streamingContent" class="generating-indicator">
        <view class="generating-avatar">
          <text class="avatar-label">{{ currentPersonalityLabel }}</text>
        </view>
        <view class="generating-bubble">
          <view class="typing-indicator">
            <view class="typing-dot" />
            <view class="typing-dot" />
            <view class="typing-dot" />
          </view>
        </view>
      </view>

      <!-- 流式输出的 AI 消息 -->
      <view v-if="streamingContent && isStreaming" class="message-wrapper">
        <MessageBubble
          :message="streamingMessage"
          :show-time="false"
        />
      </view>

      <!-- 底部留白 -->
      <view class="list-bottom-space" />
    </scroll-view>

    <!-- 输入区域 -->
    <MessageInput
      v-model="inputMessage"
      :disabled="isGenerating"
      :sending="isGenerating"
      @send="handleSend"
      @switch-personality="handleSwitchPersonality"
    />

    <!-- 危机干预弹窗 -->
    <CrisisDialog
      :visible="showCrisisDialog"
      :level="crisisLevel"
      @close="handleCrisisClose"
      @confirm="handleCrisisConfirm"
    />

    <!-- 性格切换弹窗 -->
    <view v-if="showPersonalityPicker" class="personality-picker-overlay" @tap="closePersonalityPicker">
      <view class="personality-picker" @tap.stop>
        <view class="picker-title">
          <text class="title-text">选择新的 AI 朋友</text>
        </view>
        <view class="picker-options">
          <view
            v-for="p in personalityOptions"
            :key="p.type"
            class="picker-option"
            :class="{ 'is-current': currentPersonality === p.type }"
            @tap="selectPersonality(p.type)"
          >
            <text class="option-label">{{ p.label }}</text>
            <text class="option-name">{{ p.name }}</text>
            <view v-if="currentPersonality === p.type" class="current-mark">
              <text class="mark-text">当前</text>
            </view>
          </view>
        </view>
        <view class="picker-close" @tap="closePersonalityPicker">
          <text class="close-text">取消</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - AI 对话主页面
 * 文件：src/pages/chat/index.vue
 * 说明：AI 对话页面（消息列表 + 输入框），SSE 流式显示，
 *       换人聊聊入口，危机干预弹窗，开场白按时间段展示
 */

import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { useSSE, type SSEData } from '@/composables/useSSE'
import { useCrisis } from '@/composables/useCrisis'
import { getGreeting } from '@/api/chat'
import { trackPageEnter, track, EventName } from '@/utils/tracking'
import { getStorage, setStorage } from '@/utils/storage'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
import CrisisDialog from '@/components/chat/CrisisDialog.vue'
import type { ChatMessage } from '@/stores/chat'

// ==================== 常量 ====================

/** 是否展示性格选择页的存储键 */
const PERSONALITY_SHOWN_KEY = 'huisheng_personality_shown'

/** APP 打开次数存储键 */
const APP_OPEN_COUNT_KEY = 'huisheng_app_open_count'

/** 性格选项 */
const personalityOptions = [
  { type: 'xiaowen', name: '小温', label: '温' },
  { type: 'laohei', name: '老黑', label: '黑' },
  { type: 'ali', name: '阿理', label: '理' },
]

// ==================== Store ====================

const chatStore = useChatStore()
const userStore = useUserStore()

// ==================== SSE 流式通信 ====================

const {
  isStreaming,
  streamedContent: streamingContent,
  startStream,
  stopStream,
} = useSSE()

// ==================== 危机干预 ====================

const {
  showDialog: showCrisisDialog,
  crisisLevel,
  handleCrisis,
  closeDialog,
  resetSession,
} = useCrisis()

// ==================== 响应式状态 ====================

/** 输入消息 */
const inputMessage = ref('')

/** 滚动位置 */
const scrollTop = ref(0)

/** 是否正在加载更多 */
const isLoadingMore = ref(false)

/** 开场白消息 */
const greetingMessage = ref('')

/** 是否显示性格切换弹窗 */
const showPersonalityPicker = ref(false)

/** 流式消息 ID */
const streamingMessageId = ref<string | null>(null)

// ==================== 计算属性 ====================

/** 消息列表 */
const messages = computed(() => chatStore.messages)

/** 当前 AI 性格类型 */
const currentPersonality = computed(() => chatStore.currentPersonality)

/** 是否正在生成回复 */
const isGenerating = computed(() => chatStore.isGenerating || isStreaming.value)

/** 用户头像 */
const userAvatar = computed(() => userStore.userInfo?.avatarUrl || '/static/images/default-avatar.png')

/** 当前 AI 性格名称 */
const currentPersonalityName = computed(() => {
  const option = personalityOptions.find((p) => p.type === currentPersonality.value)
  return option?.name || '小温'
})

/** 当前 AI 性格标识 */
const currentPersonalityLabel = computed(() => {
  const option = personalityOptions.find((p) => p.type === currentPersonality.value)
  return option?.label || '温'
})

/** 流式输出的临时消息 */
const streamingMessage = computed<ChatMessage>(() => ({
  id: streamingMessageId.value || `stream_${Date.now()}`,
  role: 'assistant',
  content: streamingContent.value,
  createdAt: new Date().toISOString(),
  aiPersonality: currentPersonality.value,
  isStreaming: isStreaming.value,
}))

// ==================== 方法 ====================

/**
 * 生成按时间段的开场白
 */
function generateGreeting(): string {
  const hour = new Date().getHours()

  if (hour >= 23 || hour < 2) {
    // 23:00-02:00 深夜
    return '嗨，这么晚还没睡，是不是心里有事？我在听。'
  } else if (hour >= 2 && hour < 5) {
    // 02:00-05:00 极深夜
    return '…你也睡不着吗？这个时间醒着的人，大多心里装着点事。想说说吗？'
  } else if (hour >= 5 && hour < 7) {
    // 05:00-07:00 清晨
    return '早安。醒这么早，是没睡好还是有什么心事？'
  } else {
    // 其他时间
    return '嗨，随时随地，我都在。'
  }
}

/**
 * 处理发送消息
 */
async function handleSend(content: string): Promise<void> {
  if (!content.trim() || isGenerating.value) return

  // 重置危机干预状态（新会话）
  if (messages.value.length === 0) {
    resetSession()
  }

  // 添加用户消息
  const userMessage: ChatMessage = {
    id: `msg_${Date.now()}_user`,
    role: 'user',
    content: content.trim(),
    createdAt: new Date().toISOString(),
  }
  chatStore.addMessage(userMessage)

  // 清空输入
  inputMessage.value = ''

  // 滚动到底部
  scrollToBottom()

  // 追踪发送事件
  track(EventName.CHAT_SEND, {
    messageLength: content.length,
    personalityType: currentPersonality.value,
  })

  // 设置生成状态
  chatStore.setGenerating(true)

  // 生成 AI 消息占位 ID
  streamingMessageId.value = `msg_${Date.now()}_assistant`

  // 启动 SSE 流式请求
  try {
    const streamUrl = '/ai/chat/stream'
    await startStream({
      url: streamUrl,
      body: {
        content: content.trim(),
        personalityType: currentPersonality.value,
        conversationId: chatStore.currentSessionId,
      },
      callbacks: {
        onChunk: (chunk: string) => {
          // 每次收到内容片段，滚动到底部
          scrollToBottom()
        },
        onComplete: (data: SSEData) => {
          // 流式完成，添加完整消息（检查避免重复添加）
          const existingMsg = chatStore.messages.find(m => m.id === streamingMessageId.value)
          if (!existingMsg) {
            const assistantMessage: ChatMessage = {
              id: streamingMessageId.value!,
              role: 'assistant',
              content: data.content || streamingContent.value,
              createdAt: new Date().toISOString(),
              aiPersonality: currentPersonality.value,
              isStreaming: false,
            }
            chatStore.addMessage(assistantMessage)
          }
          chatStore.finishStreaming(streamingMessageId.value!)

          // 处理危机检测
          if (data.crisis_level && data.crisis_level !== 'low') {
            handleCrisis(data.crisis_level, data.crisis_keywords)
          }

          // 追踪完成事件
          track(EventName.CHAT_RECEIVE, {
            responseLength: assistantMessage.content.length,
            personalityType: currentPersonality.value,
          })
        },
        onError: (error: Error) => {
          // 显示错误提示
          uni.showToast({
            title: 'AI 服务暂时不可用',
            icon: 'none',
          })
          chatStore.setGenerating(false)

          // 追踪错误事件
          track(EventName.CHAT_ERROR, { error: error.message })
        },
        onCrisis: (level, keywords) => {
          // 处理危机干预
          handleCrisis(level, keywords)
        },
      },
    })
  } catch (error: any) {
    console.error('发送消息失败', error)
    uni.showToast({
      title: '发送失败，请重试',
      icon: 'none',
    })
    chatStore.setGenerating(false)
  }
}

/**
 * 处理切换 AI 性格
 */
function handleSwitchPersonality(): void {
  showPersonalityPicker.value = true
}

/**
 * 关闭性格切换弹窗
 */
function closePersonalityPicker(): void {
  showPersonalityPicker.value = false
}

/**
 * 选择新的 AI 性格
 */
function selectPersonality(type: string): void {
  if (type === currentPersonality.value) {
    closePersonalityPicker()
    return
  }

  // 切换性格
  chatStore.setPersonality(type)
  closePersonalityPicker()

  // 追踪切换事件
  track(EventName.CHAT_PERSONALITY_SWITCH, { personalityType: type })

  // 显示提示
  uni.showToast({
    title: `已切换为${personalityOptions.find((p) => p.type === type)?.name}`,
    icon: 'none',
  })

  // 更新开场白
  greetingMessage.value = generateGreeting()
}

/**
 * 处理危机干预弹窗关闭
 */
function handleCrisisClose(): void {
  closeDialog()
}

/**
 * 处理危机干预确认
 */
function handleCrisisConfirm(): void {
  closeDialog()
  // 追踪确认事件
  track(EventName.CRISIS_CONFIRM, {})
}

/**
 * 滚动到底部
 */
function scrollToBottom(): void {
  nextTick(() => {
    scrollTop.value = 999999
  })
}

/**
 * 判断是否显示时间
 */
function shouldShowTime(index: number): boolean {
  if (index === 0) return true

  const currentMsg = messages.value[index]
  const prevMsg = messages.value[index - 1]

  // 如果两条消息间隔超过 5 分钟，显示时间
  const currentTime = new Date(currentMsg.createdAt).getTime()
  const prevTime = new Date(prevMsg.createdAt).getTime()
  const diffMinutes = (currentTime - prevTime) / (1000 * 60)

  return diffMinutes >= 5
}

/**
 * 加载更多历史消息
 */
async function handleLoadMore(): Promise<void> {
  if (isLoadingMore.value || !chatStore.currentSessionId) return

  isLoadingMore.value = true

  try {
    // 这里可以调用 API 加载历史消息
    // await loadHistoryMessages()
  } catch (error) {
    console.error('加载历史消息失败', error)
  } finally {
    isLoadingMore.value = false
  }
}

/**
 * 检查是否需要展示性格选择页
 * 注册后第2次打开 APP 时展示
 */
async function checkPersonalitySelect(): void {
  const hasShown = getStorage<boolean>(PERSONALITY_SHOWN_KEY, false)

  if (!hasShown) {
    const openCount = getStorage<number>(APP_OPEN_COUNT_KEY, 0)

    // 如果是第2次打开（openCount === 1），跳转到性格选择页
    if (openCount === 1) {
      uni.redirectTo({
        url: '/pages/chat/personality',
      })
    }
  }
}

/**
 * 初始化开场白
 */
async function initGreeting(): void {
  // 如果没有消息，显示开场白
  if (messages.value.length === 0) {
    greetingMessage.value = generateGreeting()

    // 尝试从后端获取开场白（可选）
    try {
      const response = await getGreeting(currentPersonality.value as any)
      if (response.content) {
        greetingMessage.value = response.content
      }
    } catch {
      // 使用本地生成的时间段开场白
    }
  }
}

// ==================== 监听 ====================

watch(isGenerating, (val) => {
  if (val) {
    scrollToBottom()
  }
})

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// ==================== 生命周期 ====================

onMounted(() => {
  // 初始化开场白
  initGreeting()
})

onShow(() => {
  // 追踪页面进入
  trackPageEnter('chat')

  // 更新 APP 打开次数
  const openCount = getStorage<number>(APP_OPEN_COUNT_KEY, 0)
  setStorage(APP_OPEN_COUNT_KEY, openCount + 1)

  // 检查是否需要展示性格选择页
  checkPersonalitySelect()

  // 滚动到底部
  scrollToBottom()
})
</script>

<style lang="scss" scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

// ==================== 消息列表 ====================

.message-list {
  flex: 1;
  padding-top: var(--space-sm);
}

.list-bottom-space {
  height: var(--space-md);
}

// ==================== 加载指示器 ====================

.loading-indicator {
  display: flex;
  justify-content: center;
  padding: var(--space-md);
}

.loading-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  padding-top: 160rpx;
}

.empty-avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: var(--radius-full);
  background-color: var(--ai-xiaowen-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-lg);
}

.avatar-label {
  font-size: 48rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-content {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.empty-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.empty-message {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  line-height: 1.8;
}

.empty-guide {
  margin-top: var(--space-md);
}

.guide-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 生成中指示器 ====================

.generating-indicator {
  display: flex;
  align-items: flex-start;
  padding: var(--space-sm) var(--space-md);
}

.generating-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: var(--radius-full);
  background-color: var(--ai-xiaowen-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-sm);
}

.generating-bubble {
  background-color: var(--bg-secondary);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-lg);
  border-bottom-left-radius: var(--radius-xs);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.typing-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background-color: var(--text-tertiary);
  animation: typingBounce 1.4s ease-in-out infinite;

  &:nth-child(1) {
    animation-delay: 0s;
  }

  &:nth-child(2) {
    animation-delay: 0.2s;
  }

  &:nth-child(3) {
    animation-delay: 0.4s;
  }
}

@keyframes typingBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-8rpx);
    opacity: 1;
  }
}

// ==================== 消息包装 ====================

.message-wrapper {
  padding: var(--space-xs) var(--space-md);
}

// ==================== 性格切换弹窗 ====================

.personality-picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-modal);
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.personality-picker {
  width: 100%;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: var(--space-lg);
  padding-bottom: calc(var(--space-lg) + env(safe-area-inset-bottom));
}

.picker-title {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.title-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.picker-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.picker-option {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  border: 2px solid transparent;

  &:active {
    background-color: var(--bg-primary);
  }

  &.is-current {
    border-color: var(--brand-primary);
  }
}

.option-label {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
  margin-right: var(--space-sm);
}

.option-name {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.current-mark {
  margin-left: auto;
  padding: 4rpx 12rpx;
  border-radius: var(--radius-sm);
  background-color: var(--brand-primary);
}

.mark-text {
  font-size: var(--font-size-xs);
  color: var(--text-on-brand);
}

.picker-close {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);

  &:active {
    opacity: 0.8;
  }
}

.close-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
</style>