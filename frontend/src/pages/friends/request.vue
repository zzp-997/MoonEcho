<template>
  <view class="friend-request-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <wd-icon name="arrow-left" class="back-icon" />
      </view>
      <text class="title">发送好友申请</text>
      <view class="placeholder" />
    </view>

    <!-- 对方信息 -->
    <view class="user-info-card">
      <image
        class="user-avatar"
        :src="targetUser?.avatar_url || defaultAvatar"
        mode="aspectFill"
      />
      <view class="user-info">
        <text class="user-nickname">{{ targetUser?.nickname || '用户' }}</text>
        <view v-if="targetUser?.personality_tags && targetUser.personality_tags.length > 0" class="user-tags">
          <text
            v-for="tag in targetUser.personality_tags.slice(0, 3)"
            :key="tag"
            class="user-tag"
          >{{ tag }}</text>
        </view>
      </view>
    </view>

    <!-- 打招呼语输入 -->
    <view class="greeting-section">
      <text class="section-title">打个招呼吧</text>
      <textarea
        class="greeting-input"
        v-model="greetingContent"
        placeholder="写一句打动对方的话..."
        placeholder-class="input-placeholder"
        :maxlength="100"
        :auto-height="true"
      />
      <text class="char-count">{{ greetingContent.length }}/100</text>
    </view>

    <!-- AI 帮我想想 -->
    <view class="ai-assist-section">
      <view class="ai-btn" :class="{ 'is-loading': isGenerating }" @tap="handleGenerateGreeting">
        <view v-if="!isGenerating" class="ai-icon-wrapper">
          <text class="ai-icon-text">AI</text>
        </view>
        <wd-loading v-else size="small" />
        <text class="ai-text">{{ isGenerating ? 'AI正在想...' : 'AI帮我想想' }}</text>
      </view>
      <text v-if="quotaRemaining !== null" class="ai-quota">今日剩余{{ quotaRemaining }}次</text>
    </view>

    <!-- AI 生成的问候语建议 -->
    <view v-if="aiGreetings.length > 0" class="greeting-suggestions">
      <text class="suggestions-title">AI为你准备了这些</text>
      <view class="suggestions-list">
        <view
          v-for="(greeting, index) in aiGreetings"
          :key="index"
          class="suggestion-item"
          @tap="handleSelectGreeting(greeting)"
        >
          <text class="suggestion-text">{{ greeting }}</text>
        </view>
      </view>
    </view>

    <!-- 发送按钮 -->
    <view class="action-area">
      <view class="send-btn" :class="{ 'is-disabled': !canSend || isSending }" @tap="handleSend">
        <text class="send-text">{{ isSending ? '发送中...' : '发送申请' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 好友申请页
 * 文件：src/pages/friends/request.vue
 * 说明：发送好友申请，支持AI生成打招呼语
 */

import { ref, computed, onMounted } from 'vue'
import { sendFriendRequest, generateGreeting, getGreetingQuota, getUserPublicProfile, type UserPublicProfile } from '@/api/modules/friend'
import { track, EventName } from '@/utils/tracking'

// ==================== 响应式状态 ====================

/** 目标用户ID */
const targetUserId = ref('')

/** 目标用户信息 */
const targetUser = ref<UserPublicProfile | null>(null)

/** 打招呼语内容 */
const greetingContent = ref('')

/** AI 生成的问候语列表 */
const aiGreetings = ref<string[]>([])

/** 是否正在生成 */
const isGenerating = ref(false)

/** 是否正在发送 */
const isSending = ref(false)

/** 配额剩余次数 */
const quotaRemaining = ref<number | null>(null)

/** 默认头像 */
const defaultAvatar = '/static/images/default-avatar.png'

// ==================== 计算属性 ====================

/** 是否可以发送 */
const canSend = computed(() => {
  return targetUserId.value && greetingContent.value.trim().length >= 5
})

// ==================== 方法 ====================

/**
 * 加载用户信息
 */
async function loadUserInfo(): Promise<void> {
  if (!targetUserId.value) return

  try {
    const response = await getUserPublicProfile(targetUserId.value)
    targetUser.value = response
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

/**
 * 获取配额状态
 */
async function loadQuota(): Promise<void> {
  try {
    const response = await getGreetingQuota()
    quotaRemaining.value = response.remaining
  } catch (error) {
    console.error('获取配额失败', error)
  }
}

/**
 * AI 生成问候语
 */
async function handleGenerateGreeting(): Promise<void> {
  if (isGenerating.value) return
  if (quotaRemaining.value !== null && quotaRemaining.value <= 0) {
    uni.showToast({
      title: '今日次数已用完',
      icon: 'none',
    })
    return
  }

  isGenerating.value = true

  try {
    const response = await generateGreeting({
      target_user_id: targetUserId.value,
      context: targetUser.value?.bio,
    })

    aiGreetings.value = response.greetings
    quotaRemaining.value = response.quota_remaining

    track(EventName.AI_GREETING_GENERATE)
  } catch (error) {
    console.error('生成问候语失败', error)
    uni.showToast({
      title: '生成失败，请重试',
      icon: 'none',
    })
  } finally {
    isGenerating.value = false
  }
}

/**
 * 选择AI问候语
 */
function handleSelectGreeting(greeting: string): void {
  greetingContent.value = greeting
  track(EventName.AI_GREETING_USE)
}

/**
 * 发送好友申请
 */
async function handleSend(): Promise<void> {
  if (!canSend.value || isSending.value) return

  isSending.value = true

  try {
    await sendFriendRequest({
      to_user_id: targetUserId.value,
      greeting: greetingContent.value.trim(),
    })

    track(EventName.FRIEND_REQUEST_SEND, {
      greeting_length: greetingContent.value.length,
      used_ai: aiGreetings.value.includes(greetingContent.value),
    })

    uni.showToast({
      title: '申请已发送',
      icon: 'success',
    })

    // 返回上一页
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (error: any) {
    console.error('发送好友申请失败', error)
    uni.showToast({
      title: error.message || '发送失败',
      icon: 'none',
    })
  } finally {
    isSending.value = false
  }
}

/**
 * 返回
 */
function handleBack(): void {
  uni.navigateBack()
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 获取页面参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = (currentPage as any).options || {}

  targetUserId.value = options.userId || ''

  if (targetUserId.value) {
    loadUserInfo()
    loadQuota()
  }
})
</script>

<style lang="scss" scoped>
.friend-request-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #F8F8FA;
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  padding-top: calc(env(safe-area-inset-top) + 24rpx);
  background: linear-gradient(135deg, #E72F8C, #F360A7);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.back-icon {
  font-size: 34rpx;
  color: #FFFFFF;
}

.title {
  font-size: 34rpx;
  font-weight: 500;
  color: #FFFFFF;
}

.placeholder {
  width: 64rpx;
}

// ==================== 用户信息卡片 ====================

.user-info-card {
  display: flex;
  align-items: center;
  padding: 30rpx 24rpx;
  margin: 24rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0,0,0,0.05);
}

.user-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 5000rpx;
  background-color: #F4F4F5;
  margin-right: 24rpx;
}

.user-info {
  flex: 1;
}

.user-nickname {
  font-size: 34rpx;
  font-weight: 500;
  color: #080808;
  margin-bottom: 8rpx;
}

.user-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.user-tag {
  font-size: 22rpx;
  color: #838383;
  background-color: #F4F4F5;
  padding: 4rpx 12rpx;
  border-radius: 10rpx;
}

// ==================== 打招呼语输入 ====================

.greeting-section {
  padding: 24rpx;
  margin: 16rpx 24rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0,0,0,0.05);
}

.section-title {
  font-size: 26rpx;
  color: #838383;
  margin-bottom: 16rpx;
}

.greeting-input {
  width: 100%;
  min-height: 120rpx;
  padding: 16rpx;
  background-color: #F4F4F5;
  border-radius: 20rpx;
  font-size: 30rpx;
  color: #080808;
  line-height: 1.6;
}

.input-placeholder {
  color: #838383;
}

.char-count {
  display: block;
  text-align: right;
  font-size: 22rpx;
  color: #838383;
  margin-top: 8rpx;
}

// ==================== AI 辅助 ====================

.ai-assist-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 24rpx;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 16rpx 24rpx;
  background-color: rgba(1,190,255,0.1);
  border-radius: 5000rpx;

  &:active {
    opacity: 0.9;
  }

  &.is-loading {
    opacity: 0.7;
  }
}

.ai-icon-wrapper {
  width: 32rpx;
  height: 32rpx;
  border-radius: 10rpx;
  background-color: #01BEFF;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 6rpx;
}

.ai-icon-text {
  font-size: 16rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.ai-text {
  font-size: 26rpx;
  color: #01BEFF;
}

.ai-quota {
  font-size: 22rpx;
  color: #838383;
}

// ==================== AI 建议 ====================

.greeting-suggestions {
  padding: 16rpx 24rpx;
}

.suggestions-title {
  font-size: 26rpx;
  color: #838383;
  margin-bottom: 16rpx;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.suggestion-item {
  padding: 16rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  border: 1rpx solid #F4F4F5;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0,0,0,0.05);

  &:active {
    opacity: 0.9;
    border-color: #01BEFF;
  }
}

.suggestion-text {
  font-size: 26rpx;
  color: #080808;
  line-height: 1.5;
}

// ==================== 发送按钮 ====================

.action-area {
  padding: 30rpx 24rpx;
  margin-top: auto;
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  background: linear-gradient(135deg, #01BEFF, #0AA8E8);
  border-radius: 5000rpx;

  &:active {
    opacity: 0.9;
  }

  &.is-disabled {
    background: #F4F4F5;
  }
}

.send-text {
  font-size: 30rpx;
  font-weight: 500;
  color: #FFFFFF;
}

.send-btn.is-disabled .send-text {
  color: #838383;
}
</style>