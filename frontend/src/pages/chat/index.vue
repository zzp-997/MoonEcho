<template>
  <view class="chat-page">
    <!-- 导航栏 — 图鸟风格渐变 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-back" @tap="handleBack">
        <text style="font-size: 36rpx;">←</text>
      </view>
      <view class="nav-center">
        <view class="nav-avatar tn-shadow-blur" :style="{ background: personalityGradient }">
          <text class="nav-avatar-text">{{ currentPersonalityLabel }}</text>
        </view>
        <text class="nav-title">{{ currentPersonalityName }}</text>
      </view>
      <view class="nav-action" @tap="handleSwitchPersonality">
        <text style="font-size: 36rpx;">🔄</text>
      </view>
    </view>

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

      <!-- 空状态提示 — 图鸟风格 -->
      <view v-if="messages.length === 0 && !isGenerating" class="empty-state">
        <view class="empty-avatar tn-shadow-blur" :style="{ background: personalityGradient }">
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
        <view class="generating-avatar tn-shadow-blur" :style="{ background: personalityGradient }">
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

    <!-- 性格切换弹窗 — 图鸟风格 -->
    <view v-if="showPersonalityPicker" class="personality-picker-overlay" @tap="closePersonalityPicker">
      <view class="personality-picker" @tap.stop>
        <text class="picker-title">选择新的 AI 朋友</text>
        <view class="picker-options">
          <view
            v-for="p in personalityOptions"
            :key="p.type"
            class="picker-option"
            :class="{ 'is-current': currentPersonality === p.type }"
            @tap="selectPersonality(p.type)"
          >
            <view class="option-avatar tn-shadow-blur" :style="{ background: getGradient(p.type) }">
              <text class="option-avatar-text">{{ p.label }}</text>
            </view>
            <view class="option-info">
              <text class="option-name">{{ p.name }}</text>
            </view>
            <view v-if="currentPersonality === p.type" class="current-mark tn-gradient-1">
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
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { useSSE, type SSEData } from '@/composables/useSSE'
import { useCrisis } from '@/composables/useCrisis'
import { getGreeting } from '@/api/chat'
import { trackPageEnter, track, EventName } from '@/utils/tracking'
import { getStorage, setStorage } from '@/utils/storage'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
import CrisisDialog from '@/components/chat/CrisisDialog.vue'
import type { ChatMessage } from '@/stores/chat'

const PERSONALITY_SHOWN_KEY = 'huisheng_personality_shown'
const APP_OPEN_COUNT_KEY = 'huisheng_app_open_count'

const personalityOptions = [
  { type: 'xiaowen', name: '小温', label: '温' },
  { type: 'laohei', name: '老黑', label: '黑' },
  { type: 'ali', name: '阿理', label: '理' },
]

const chatStore = useChatStore()
const userStore = useUserStore()

const {
  isStreaming,
  streamedContent: streamingContent,
  startStream,
  stopStream,
} = useSSE()

const {
  showDialog: showCrisisDialog,
  crisisLevel,
  handleCrisis,
  closeDialog,
  resetSession,
} = useCrisis()

const inputMessage = ref('')
const scrollTop = ref(0)
const isLoadingMore = ref(false)
const greetingMessage = ref('')
const showPersonalityPicker = ref(false)
const streamingMessageId = ref<string | null>(null)

const statusBarHeight = ref(0)
const sysInfo = uni.getSystemInfoSync()
statusBarHeight.value = sysInfo.statusBarHeight || 0

const messages = computed(() => chatStore.messages)
const currentPersonality = computed(() => chatStore.currentPersonality)
const isGenerating = computed(() => chatStore.isGenerating || isStreaming.value)
const userAvatar = computed(() => userStore.userInfo?.avatarUrl || '/static/images/default-avatar.png')

const currentPersonalityName = computed(() => {
  const option = personalityOptions.find((p) => p.type === currentPersonality.value)
  return option?.name || '小温'
})

const currentPersonalityLabel = computed(() => {
  const option = personalityOptions.find((p) => p.type === currentPersonality.value)
  return option?.label || '温'
})

const personalityGradient = computed(() => {
  return getGradient(currentPersonality.value)
})

const streamingMessage = computed<ChatMessage>(() => ({
  id: streamingMessageId.value || `stream_${Date.now()}`,
  role: 'assistant',
  content: streamingContent.value,
  createdAt: new Date().toISOString(),
  aiPersonality: currentPersonality.value,
  isStreaming: isStreaming.value,
}))

function getGradient(type: string): string {
  const map: Record<string, string> = {
    xiaowen: 'linear-gradient(135deg, #E72F8C, #F360A7)',
    laohei: 'linear-gradient(135deg, #78909C, #5F7E8B)',
    ali: 'linear-gradient(135deg, #3D7EFF, #01BEFF)',
  }
  return map[type] || map.xiaowen
}

function generateGreeting(): string {
  const hour = new Date().getHours()
  if (hour >= 23 || hour < 2) return '嗨，这么晚还没睡，是不是心里有事？我在听。'
  if (hour >= 2 && hour < 5) return '…你也睡不着吗？这个时间醒着的人，大多心里装着点事。想说说吗？'
  if (hour >= 5 && hour < 7) return '早安。醒这么早，是没睡好还是有什么心事？'
  return '嗨，随时随地，我都在。'
}

async function handleSend(content: string): Promise<void> {
  if (!content.trim() || isGenerating.value) return
  if (messages.value.length === 0) resetSession()

  const userMessage: ChatMessage = {
    id: `msg_${Date.now()}_user`,
    role: 'user',
    content: content.trim(),
    createdAt: new Date().toISOString(),
  }
  chatStore.addMessage(userMessage)
  inputMessage.value = ''
  scrollToBottom()

  track(EventName.CHAT_SEND, { messageLength: content.length, personalityType: currentPersonality.value })
  chatStore.setGenerating(true)
  streamingMessageId.value = `msg_${Date.now()}_assistant`

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
        onChunk: () => { scrollToBottom() },
        onComplete: (data: SSEData) => {
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
          if (data.crisis_level && data.crisis_level !== 'low') handleCrisis(data.crisis_level, data.crisis_keywords)
          track(EventName.CHAT_RECEIVE, { responseLength: (data.content || '').length, personalityType: currentPersonality.value })
        },
        onError: (error: Error) => {
          uni.showToast({ title: 'AI 服务暂时不可用', icon: 'none' })
          chatStore.setGenerating(false)
          track(EventName.CHAT_ERROR, { error: error.message })
        },
        onCrisis: (level, keywords) => { handleCrisis(level, keywords) },
      },
    })
  } catch {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
    chatStore.setGenerating(false)
  }
}

function handleSwitchPersonality(): void { showPersonalityPicker.value = true }
function handleBack(): void { uni.navigateBack() }
function closePersonalityPicker(): void { showPersonalityPicker.value = false }

function selectPersonality(type: string): void {
  if (type === currentPersonality.value) { closePersonalityPicker(); return }
  chatStore.setPersonality(type)
  closePersonalityPicker()
  track(EventName.CHAT_PERSONALITY_SWITCH, { personalityType: type })
  uni.showToast({ title: `已切换为${personalityOptions.find((p) => p.type === type)?.name}`, icon: 'none' })
  greetingMessage.value = generateGreeting()
}

function handleCrisisClose(): void { closeDialog() }
function handleCrisisConfirm(): void { closeDialog(); track(EventName.CRISIS_CONFIRM, {}) }

function scrollToBottom(): void {
  nextTick(() => { scrollTop.value = 999999 })
}

function shouldShowTime(index: number): boolean {
  if (index === 0) return true
  const currentMsg = messages.value[index]
  const prevMsg = messages.value[index - 1]
  const diffMinutes = (new Date(currentMsg.createdAt).getTime() - new Date(prevMsg.createdAt).getTime()) / (1000 * 60)
  return diffMinutes >= 5
}

async function handleLoadMore(): Promise<void> {
  if (isLoadingMore.value || !chatStore.currentSessionId) return
  isLoadingMore.value = true
  try { /* loadHistoryMessages() */ } finally { isLoadingMore.value = false }
}

async function checkPersonalitySelect(): void {
  const hasShown = getStorage<boolean>(PERSONALITY_SHOWN_KEY, false)
  if (!hasShown) {
    const openCount = getStorage<number>(APP_OPEN_COUNT_KEY, 0)
    if (openCount === 1) uni.redirectTo({ url: '/pages/chat/personality' })
  }
}

async function initGreeting(): void {
  if (messages.value.length === 0) {
    greetingMessage.value = generateGreeting()
    try {
      const response = await getGreeting(currentPersonality.value as any)
      if (response.content) greetingMessage.value = response.content
    } catch {}
  }
}

watch(isGenerating, (val) => { if (val) scrollToBottom() })
watch(messages, () => { scrollToBottom() }, { deep: true })

onMounted(() => { initGreeting() })

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('chat')
    const openCount = getStorage<number>(APP_OPEN_COUNT_KEY, 0)
    setStorage(APP_OPEN_COUNT_KEY, openCount + 1)
    checkPersonalitySelect()
    scrollToBottom()
  }
})
</script>

<style lang="scss" scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #FFFFFF;
}

// ==================== 导航栏 ====================

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 30rpx;
  background: linear-gradient(135deg, #01BEFF, #3D7EFF);
}

.nav-back,
.nav-action {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;

  &:active { opacity: 0.8; }
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.nav-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-avatar-text {
  font-size: 24rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.nav-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #FFFFFF;
}

// ==================== 消息列表 ====================

.message-list {
  flex: 1;
  padding-top: 16rpx;
}

.list-bottom-space {
  height: 20rpx;
}

.loading-indicator {
  display: flex;
  justify-content: center;
  padding: 20rpx;
}

.loading-text {
  font-size: 24rpx;
  color: #838383;
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 30rpx;
  padding-top: 200rpx;
}

.empty-avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30rpx;
}

.avatar-label {
  font-size: 56rpx;
  font-weight: 700;
  color: #FFFFFF;
}

.empty-content {
  text-align: center;
  margin-bottom: 30rpx;
}

.empty-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #080808;
  margin-bottom: 12rpx;
}

.empty-message {
  font-size: 28rpx;
  color: #838383;
  line-height: 1.8;
}

.empty-guide {
  margin-top: 20rpx;
}

.guide-text {
  font-size: 24rpx;
  color: #AAAAAA;
}

// ==================== 生成中指示器 ====================

.generating-indicator {
  display: flex;
  align-items: flex-start;
  padding: 16rpx 30rpx;
}

.generating-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.generating-bubble {
  background-color: #FFFFFF;
  padding: 20rpx 28rpx;
  border-radius: 20rpx;
  border-bottom-left-radius: 6rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.06);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.typing-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background-color: #01BEFF;
  animation: typingBounce 1.4s ease-in-out infinite;

  &:nth-child(1) { animation-delay: 0s; }
  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
}

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-8rpx); opacity: 1; }
}

// ==================== 消息包装 ====================

.message-wrapper {
  padding: 8rpx 30rpx;
}

// ==================== 性格切换弹窗 ====================

.personality-picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.personality-picker {
  width: 100%;
  background-color: #FFFFFF;
  border-radius: 30rpx 30rpx 0 0;
  padding: 40rpx 30rpx;
  padding-bottom: calc(40rpx + env(safe-area-inset-bottom));
}

.picker-title {
  display: block;
  text-align: center;
  font-size: 34rpx;
  font-weight: 700;
  color: #080808;
  margin-bottom: 30rpx;
}

.picker-options {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.picker-option {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background-color: #FFFFFF;
  border: 2rpx solid #F4F4F5;
  border-radius: 20rpx;

  &:active { border-color: #01BEFF; }

  &.is-current {
    border-color: #01BEFF;
    background: linear-gradient(135deg, rgba(1, 190, 255, 0.05), rgba(61, 126, 255, 0.05));
  }
}

.option-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}

.option-avatar-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.option-info {
  flex: 1;
}

.option-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #080808;
}

.current-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6rpx 16rpx;
  border-radius: 5000rpx;
}

.mark-text {
  font-size: 22rpx;
  color: #FFFFFF;
  font-weight: 600;
}

.picker-close {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  background-color: #F4F4F5;
  border-radius: 5000rpx;

  &:active { opacity: 0.8; }
}

.close-text {
  font-size: 30rpx;
  color: #838383;
  font-weight: 500;
}
</style>
