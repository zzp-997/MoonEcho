<template>
  <view class="private-chat-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <text class="back-icon"><</text>
      </view>
      <view class="header-info" @tap="handleViewProfile">
        <image
          class="header-avatar"
          :src="friendInfo?.avatar_url || defaultAvatar"
          mode="aspectFill"
        />
        <view class="header-text">
          <text class="header-nickname">{{ friendInfo?.nickname || '聊天' }}</text>
          <text class="header-status" :class="connectionStatus">{{ connectionStatusText }}</text>
        </view>
      </view>
      <view class="more-btn" @tap="handleShowMore">
        <text class="more-icon">...</text>
      </view>
    </view>

    <!-- WebSocket 连接状态提示 -->
    <view v-if="connectionStatus === 'reconnecting'" class="connection-banner reconnecting">
      <text class="banner-text">正在重新连接...</text>
    </view>
    <view v-else-if="connectionStatus === 'error'" class="connection-banner error">
      <text class="banner-text">连接失败，点击重试</text>
    </view>

    <!-- 消息列表 -->
    <scroll-view
      class="message-list-container"
      scroll-y
      :scroll-top="scrollTop"
      :scroll-with-animation="true"
      @scrolltoupper="handleLoadMore"
    >
      <!-- 加载更多提示 -->
      <view v-if="isLoadingMore" class="loading-more">
        <wd-loading size="small" />
        <text class="loading-text">加载更多...</text>
      </view>

      <!-- 消息气泡列表 -->
      <view class="message-list">
        <PrivateMessageBubble
          v-for="(message, index) in messages"
          :key="message.id"
          :message="message"
          :is-self="message.sender_id === currentUserId"
          :show-time="shouldShowTime(index)"
          :self-avatar="currentUserAvatar"
          :other-avatar="friendInfo?.avatar_url || defaultAvatar"
          @image-tap="handleImagePreview"
        />
      </view>

      <!-- 底部占位 -->
      <view class="scroll-bottom" />
    </scroll-view>

    <!-- AI 辅助提示 -->
    <AIAssistHint
      v-if="showAIHint"
      :type="aiHintType"
      :suggestions="aiSuggestions"
      @select="handleSelectSuggestion"
      @refresh="handleRefreshSuggestions"
      @dismiss="handleDismissHint"
      @generate-topic="handleGenerateTopic"
    />

    <!-- 输入区域 -->
    <ChatInput
      :conversation-id="conversationId"
      :show-ai-hint="showAwkwardHint"
      :ai-hint-text="awkwardHintText"
      :disabled="isInRest"
      @send="handleSendMessage"
      @send-image="handleSendImage"
      @polish="handlePolish"
      @ai-hint-tap="handleAIHintTap"
      @typing="handleTyping"
    />

    <!-- 更多操作弹窗 -->
    <wd-action-sheet
      v-model="showMoreSheet"
      :actions="moreActions"
      cancelText="取消"
      @select="handleMoreAction"
    />

    <!-- 温柔退出弹窗 -->
    <GentleExit
      :visible="showExitDialog"
      :exit-phrases="exitPhrases"
      @select="handleSelectExit"
      @close="handleCloseExit"
    />

    <!-- 举报弹窗 -->
    <ReportDialog
      :show="showReportDialog"
      :target="reportTarget"
      @update:show="showReportDialog = $event"
      @success="handleReportSuccess"
    />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 私聊页面
 * 文件：src/pagesSocial/chat/private.vue
 * 说明：私聊页面，支持 WebSocket 实时消息、AI 辅助、温柔退出
 */

import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import {
  getConversationDetail,
  getMessages,
  uploadChatImage,
  markAsRead,
  compressChatImage,
  type ChatMessage,
  type Conversation,
  formatMessageTime,
} from '@/api/modules/chat'
import { useWebSocket } from '@/composables/useWebSocket'
import { useChatAssist } from '@/composables/useChatAssist'
import { useSocialEnergy } from '@/composables/useSocialEnergy'
import { track, EventName, trackPageEnter } from '@/utils/tracking'
import PrivateMessageBubble from '@/components/chat/PrivateMessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import AIAssistHint from '@/components/chat/AIAssistHint.vue'
import GentleExit from '@/components/chat/GentleExit.vue'
import ReportDialog from '@/components/common/ReportDialog.vue'
import { ReportContentType, type ReportTarget } from '@/api/modules/report'

// ==================== Props & Params ====================

/** 好友ID */
const friendId = ref('')

/** 会话ID */
const conversationId = ref('')

/** 好友昵称（从路由参数获取） */
const friendNickname = ref('')

// ==================== 响应式状态 ====================

/** 好友信息 */
const friendInfo = ref<{
  id: string
  nickname: string
  avatar_url: string | null
  online_status: string
} | null>(null)

/** 消息列表 */
const messages = ref<ChatMessage[]>([])

/** 会话信息 */
const conversation = ref<Conversation | null>(null)

/** 是否正在加载更多 */
const isLoadingMore = ref(false)

/** 是否有更多历史消息 */
const hasMore = ref(true)

/** 当前页码 */
const currentPage = ref(1)

/** 滚动位置 */
const scrollTop = ref(0)

/** 默认头像 */
const defaultAvatar = '/static/images/default-avatar.png'

// ==================== WebSocket ====================

const {
  connectionStatus,
  isConnected,
  onMessage,
  onTyping,
  connect,
  disconnect,
  sendMessage: wsSendMessage,
  sendTyping,
} = useWebSocket()

/** 连接状态文本 */
const connectionStatusText = computed(() => {
  const statusMap: Record<string, string> = {
    connecting: '连接中',
    connected: '在线',
    disconnected: '离线',
    reconnecting: '重连中',
    error: '连接失败',
  }
  return statusMap[connectionStatus.value] || '未知'
})

// ==================== 用户信息 ====================

const userStore = useUserStore()

/** 当前用户ID */
const currentUserId = computed(() => userStore.userInfo?.id || '')

/** 当前用户头像 */
const currentUserAvatar = computed(() => userStore.userInfo?.avatarUrl || defaultAvatar)

// ==================== AI 辅助 ====================

const {
  state: assistState,
  showAssistPanel,
  loadTopicSuggestions,
  loadReplySuggestions,
  selectTopic,
  selectReply,
  openExitDialog,
  recordMessageTime,
  recordInputStart,
  recordInputEnd,
  optimizePolish,
} = useChatAssist(conversationId)

/** 是否显示AI提示 */
const showAIHint = computed(() => {
  return assistState.value.showAwkwardHint || assistState.value.showReplySuggestion
})

/** AI提示类型 */
const aiHintType = computed(() => {
  return assistState.value.showAwkwardHint ? 'awkward' : 'reply'
})

/** AI建议列表 */
const aiSuggestions = computed(() => {
  return assistState.value.showAwkwardHint
    ? assistState.value.topics
    : assistState.value.replies
})

/** 是否显示冷场提示 */
const showAwkwardHint = computed(() => assistState.value.showAwkwardHint)

/** 冷场提示文本 */
const awkwardHintText = ref('AI帮我想想话题')

// ==================== 社交能量 ====================

const { isInRest, loadEnergy } = useSocialEnergy()

// ==================== 更多操作 ====================

/** 是否显示更多弹窗 */
const showMoreSheet = ref(false)

/** 更多操作列表 */
const moreActions = [
  { name: '温柔退出当前对话', value: 'exit' },
  { name: '查看对方主页', value: 'profile' },
  { name: '举报', value: 'report' },
  { name: '清空聊天记录', value: 'clear' },
]

/** 是否显示退出弹窗 */
const showExitDialog = ref(false)

/** 退出语列表 */
const exitPhrases = ref<string[]>([])

/** 举报弹窗 */
const showReportDialog = ref(false)

/** 举报目标 */
const reportTarget = ref<ReportTarget | null>(null)

// ==================== 方法 ====================

/**
 * 加载会话详情
 */
async function loadConversation(): Promise<void> {
  if (!friendId.value) return

  try {
    // 如果没有会话ID，先创建或获取会话
    if (!conversationId.value) {
      // 实际应该调用创建会话接口，这里简化处理
      const response = await getConversationDetail(friendId.value)
      conversationId.value = response.conversation.id
      friendInfo.value = response.friend
      conversation.value = response.conversation
    } else {
      const response = await getConversationDetail(conversationId.value)
      friendInfo.value = response.friend
      conversation.value = response.conversation
    }
  } catch (error) {
    console.error('加载会话失败', error)
  }
}

/**
 * 加载消息列表
 */
async function loadMessages(append = false): Promise<void> {
  if (!conversationId.value) return

  if (append && isLoadingMore.value) return
  if (!append) {
    isLoadingMore.value = false
  }

  try {
    const response = await getMessages(conversationId.value, {
      page: currentPage.value,
      page_size: 20,
    })

    if (append) {
      messages.value = [...response.messages, ...messages.value]
    } else {
      messages.value = response.messages
    }

    hasMore.value = response.pagination.has_more

    // 滚动到底部
    nextTick(() => {
      scrollToBottom()
    })

    // 标记已读
    if (messages.value.length > 0) {
      await markAsRead(conversationId.value)
    }
  } catch (error) {
    console.error('加载消息失败', error)
  }
}

/**
 * 加载更多历史消息
 */
async function handleLoadMore(): Promise<void> {
  if (!hasMore.value || isLoadingMore.value) return

  isLoadingMore.value = true
  currentPage.value++

  await loadMessages(true)
  isLoadingMore.value = false
}

/**
 * 发送消息
 */
async function handleSendMessage(content: string): Promise<void> {
  if (!content.trim() || isInRest.value) return

  // 添加到本地消息列表（乐观更新）
  const tempId = `temp_${Date.now()}`
  messages.value.push({
    id: tempId,
    conversation_id: conversationId.value,
    sender_id: currentUserId.value,
    content: content.trim(),
    message_type: 'text',
    is_read: true,
    created_at: new Date().toISOString(),
  })

  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })

  // 通过 WebSocket 发送
  wsSendMessage(conversationId.value, content.trim(), 'text')

  // 记录消息时间
  recordMessageTime()

  track(EventName.CHAT_PRIVATE_SEND, {
    message_type: 'text',
    content_length: content.length,
  })
}

/**
 * 发送图片消息
 */
async function handleSendImage(filePath: string): Promise<void> {
  if (isInRest.value) return

  try {
    // 压缩图片
    const compressedPath = await compressChatImage(filePath, 60)

    // 上传图片
    const uploadResult = await uploadChatImage(compressedPath)

    // 通过 WebSocket 发送
    wsSendMessage(conversationId.value, uploadResult.url, 'image', uploadResult.url)

    // 记录消息时间
    recordMessageTime()

    track(EventName.CHAT_PRIVATE_IMAGE_SEND)
  } catch (error) {
    console.error('发送图片失败', error)
    uni.showToast({
      title: '发送失败',
      icon: 'none',
    })
  }
}

/**
 * 语气优化
 */
async function handlePolish(content: string): Promise<void> {
  if (!content.trim()) return

  try {
    const result = await optimizePolish(content)
    // 将优化结果设置到输入框（需要通过组件 ref 调用）
    console.log('优化结果:', result)
    uni.showToast({
      title: '已优化',
      icon: 'success',
    })
  } catch (error) {
    console.error('语气优化失败', error)
    uni.showToast({
      title: '优化失败',
      icon: 'none',
    })
  }
}

/**
 * 处理输入状态
 */
function handleTyping(isTyping: boolean): void {
  if (isTyping) {
    recordInputStart()
    sendTyping(conversationId.value, true)
  } else {
    recordInputEnd()
    sendTyping(conversationId.value, false)
  }
}

/**
 * 处理AI提示点击
 */
function handleAIHintTap(): void {
  loadTopicSuggestions()
}

/**
 * 选择AI建议
 */
function handleSelectSuggestion(suggestion: string): void {
  // 将建议内容发送出去
  handleSendMessage(suggestion)
  // 关闭提示
  handleDismissHint()
}

/**
 * 刷新AI建议
 */
async function handleRefreshSuggestions(): Promise<void> {
  await loadTopicSuggestions()
}

/**
 * 关闭AI提示
 */
function handleDismissHint(): void {
  assistState.value.showAwkwardHint = false
  assistState.value.showReplySuggestion = false
}

/**
 * 生成话题
 */
async function handleGenerateTopic(): Promise<void> {
  await loadTopicSuggestions()
}

/**
 * 显示更多操作
 */
function handleShowMore(): void {
  showMoreSheet.value = true
}

/**
 * 处理更多操作
 */
function handleMoreAction(action: any): void {
  showMoreSheet.value = false

  switch (action.value) {
    case 'exit':
      openExitDialog()
      break
    case 'profile':
      uni.navigateTo({
        url: `/pages/friends/profile?userId=${friendId.value}`,
      })
      break
    case 'report':
      reportTarget.value = {
        contentType: ReportContentType.USER,
        userId: friendId.value,
      }
      showReportDialog.value = true
      break
    case 'clear':
      uni.showModal({
        title: '确认清空',
        content: '确定要清空聊天记录吗？',
        success: (res) => {
          if (res.confirm) {
            messages.value = []
          }
        },
      })
      break
  }
}

/**
 * 选择退出语
 */
function handleSelectExit(phrase: string): void {
  handleSendMessage(phrase)
  showExitDialog.value = false

  // 延迟返回
  setTimeout(() => {
    uni.navigateBack()
  }, 1000)
}

/**
 * 关闭退出弹窗
 */
function handleCloseExit(): void {
  showExitDialog.value = false
}

/**
 * 图片预览
 */
function handleImagePreview(imageUrl: string): void {
  // 获取所有图片URL
  const imageUrls = messages.value
    .filter((m) => m.message_type === 'image')
    .map((m) => m.image_url || m.content)

  uni.previewImage({
    urls: imageUrls,
    current: imageUrl,
  })
}

/**
 * 查看主页
 */
function handleViewProfile(): void {
  uni.navigateTo({
    url: `/pages/friends/profile?userId=${friendId.value}`,
  })
}

/**
 * 返回
 */
function handleBack(): void {
  uni.navigateBack()
}

/**
 * 举报成功回调
 */
function handleReportSuccess(): void {
  track(EventName.USER_REPORT, { user_id: friendId.value })
}

/**
 * 滚动到底部
 */
function scrollToBottom(): void {
  // 通过设置一个较大值触发滚动，uni-app 会自动处理边界
  scrollTop.value = scrollTop.value + 1000
}

/**
 * 判断是否显示时间
 */
function shouldShowTime(index: number): boolean {
  if (index === 0) return true

  const currentMessage = messages.value[index]
  const prevMessage = messages.value[index - 1]

  if (!currentMessage.created_at || !prevMessage.created_at) return false

  const currentTime = new Date(currentMessage.created_at).getTime()
  const prevTime = new Date(prevMessage.created_at).getTime()

  // 相隔超过5分钟显示时间
  return currentTime - prevTime > 5 * 60 * 1000
}

// ==================== WebSocket 消息处理 ====================

/** 取消消息订阅 */
let unsubscribeMessage: (() => void) | null = null
let unsubscribeTyping: (() => void) | null = null

onMounted(() => {
  // 订阅消息
  unsubscribeMessage = onMessage((message) => {
    if (message.conversation_id === conversationId.value) {
      messages.value.push({
        id: message.id,
        conversation_id: message.conversation_id,
        sender_id: message.sender_id,
        content: message.content,
        message_type: message.message_type,
        image_url: message.image_url,
        is_read: true,
        created_at: message.created_at,
      })

      // 滚动到底部
      nextTick(() => {
        scrollToBottom()
      })

      track(EventName.CHAT_PRIVATE_RECEIVE)
    }
  })

  // 订阅输入状态
  unsubscribeTyping = onTyping((data) => {
    // 显示对方正在输入状态
  })
})

onUnmounted(() => {
  // 取消订阅
  if (unsubscribeMessage) {
    unsubscribeMessage()
  }
  if (unsubscribeTyping) {
    unsubscribeTyping()
  }
})

// ==================== 生命周期 ====================

onShow(() => {
  trackPageEnter('private-chat')

  // 获取页面参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = (currentPage as any).options || {}

  friendId.value = options.friendId || ''
  conversationId.value = options.conversationId || ''
  friendNickname.value = decodeURIComponent(options.nickname || '聊天')

  // 加载数据
  loadConversation()
  loadMessages()
  loadEnergy()
})

onHide(() => {
  // 页面隐藏时，取消活跃会话
  setActiveConversation(null)
})

onUnmounted(() => {
  // 取消订阅
  if (unsubscribeMessage) {
    unsubscribeMessage()
  }
  if (unsubscribeTyping) {
    unsubscribeTyping()
  }
  // 清理活跃会话
  setActiveConversation(null)
})
</script>

<style lang="scss" scoped>
.private-chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-primary);
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-primary);
  border-bottom: 1rpx solid var(--border-primary);
}

.back-btn,
.more-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.back-icon,
.more-icon {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

.header-info {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;

  &:active {
    opacity: 0.8;
  }
}

.header-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
  margin-right: var(--space-sm);
}

.header-text {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.header-nickname {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.header-status {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);

  &.connected {
    color: var(--color-success);
  }

  &.reconnecting,
  &.connecting {
    color: var(--color-warning);
  }

  &.error,
  &.disconnected {
    color: var(--color-error);
  }
}

// ==================== 连接状态提示 ====================

.connection-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm);
  font-size: var(--font-size-xs);

  &.reconnecting {
    background-color: var(--color-warning-bg);
    color: var(--color-warning);
  }

  &.error {
    background-color: var(--color-error-bg);
    color: var(--color-error);

    &:active {
      opacity: 0.9;
    }
  }
}

// ==================== 消息列表 ====================

.message-list-container {
  flex: 1;
  overflow: hidden;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm);
  gap: var(--space-xs);
}

.loading-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.message-list {
  padding: var(--space-sm) 0;
}

.scroll-bottom {
  height: 20rpx;
}
</style>