<template>
  <view class="personality-page">
    <!-- 标题区域 -->
    <view class="header">
      <text class="title">选择你的 AI 朋友</text>
      <text class="subtitle">不同性格，不同陪伴方式</text>
    </view>

    <!-- 性格卡片列表 -->
    <view class="card-list">
      <view
        v-for="personality in personalities"
        :key="personality.type"
        class="personality-card"
        :class="{ 'is-selected': selectedType === personality.type }"
        @tap="handleSelect(personality.type)"
      >
        <!-- 头像 -->
        <view class="card-avatar" :class="`avatar-${personality.type}`">
          <text class="avatar-label">{{ personality.label }}</text>
        </view>

        <!-- 名称 -->
        <view class="card-name">
          <text class="name-text">{{ personality.name }}</text>
        </view>

        <!-- 简介 -->
        <view class="card-desc">
          <text class="desc-text">{{ personality.description }}</text>
        </view>

        <!-- 特点标签 -->
        <view class="card-tags">
          <view v-for="tag in personality.tags" :key="tag" class="tag">
            <text class="tag-text">{{ tag }}</text>
          </view>
        </view>

        <!-- 选中指示 -->
        <view v-if="selectedType === personality.type" class="selected-mark">
          <text class="mark-icon">✓</text>
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <!-- 跳过按钮 -->
      <view class="skip-btn" @tap="handleSkip">
        <text class="skip-text">跳过，让 AI 在对话中感知我的偏好</text>
      </view>

      <!-- 确认按钮 -->
      <view class="confirm-btn" :class="{ 'is-active': selectedType }" @tap="handleConfirm">
        <text class="confirm-text">开始对话</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - AI 性格选择页
 * 文件：src/pages/chat/personality.vue
 * 说明：注册后第2次打开 APP 时展示，三种性格卡片（小温、老黑、阿理）
 *       可随时跳过，边聊边让 AI 感知偏好
 */

import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { setStorage, getStorage } from '@/utils/storage'
import { track, EventName } from '@/utils/tracking'

// ==================== 常量 ====================

/** 是否已选择性格的存储键 */
const PERSONALITY_SELECTED_KEY = 'huisheng_personality_selected'

/** 是否为首次打开 APP 的存储键 */
const APP_OPEN_COUNT_KEY = 'huisheng_app_open_count'

/** 性格列表 */
const personalities = [
  {
    type: 'xiaowen',
    name: '小温',
    label: '温',
    description: '温柔倾听者，像姐姐一样温暖',
    tags: ['温柔', '倾听', '治愈'],
    color: '#E72F8C',
  },
  {
    type: 'laohei',
    name: '老黑',
    label: '黑',
    description: '毒舌吐槽者，像损友一样直率',
    tags: ['直率', '吐槽', '清醒'],
    color: '#78909C',
  },
  {
    type: 'ali',
    name: '阿理',
    label: '理',
    description: '理性开导者，像大哥一样可靠',
    tags: ['理性', '分析', '建议'],
    color: '#3D7EFF',
  },
]

// ==================== 响应式状态 ====================

/** 当前选中的性格类型 */
const selectedType = ref<string>('xiaowen')

/** 是否为首次选择 */
const isFirstSelect = ref(true)

// ==================== Store ====================

const chatStore = useChatStore()
const userStore = useUserStore()

// ==================== 方法 ====================

/**
 * 处理选择性格
 */
function handleSelect(type: string): void {
  selectedType.value = type

  // 追踪选择事件
  track(EventName.CHAT_PERSONALITY_SELECT, { personalityType: type })
}

/**
 * 处理跳过
 */
function handleSkip(): void {
  // 标记已展示（跳过也算）
  markAsShown()

  // 使用默认性格（小温）
  chatStore.setPersonality('xiaowen')

  // 追踪跳过事件
  track(EventName.CHAT_PERSONALITY_SKIP, {})

  // 跳转到对话页
  navigateToChat()
}

/**
 * 处理确认选择
 */
function handleConfirm(): void {
  if (!selectedType.value) return

  // 标记已选择
  markAsShown()

  // 设置性格
  chatStore.setPersonality(selectedType.value)

  // 追踪确认事件
  track(EventName.CHAT_PERSONALITY_CONFIRM, { personalityType: selectedType.value })

  // 跳转到对话页
  navigateToChat()
}

/**
 * 标记已展示性格选择页
 */
function markAsShown(): void {
  setStorage(PERSONALITY_SELECTED_KEY, true)
}

/**
 * 跳转到对话页
 */
function navigateToChat(): void {
  uni.redirectTo({
    url: '/pages/chat/index',
  })
}

/**
 * 检查是否需要展示性格选择页
 * 注册后第2次打开 APP 时展示
 */
function checkShouldShow(): void {
  // 获取打开次数
  const openCount = getStorage<number>(APP_OPEN_COUNT_KEY, 0)

  // 更新打开次数
  setStorage(APP_OPEN_COUNT_KEY, openCount + 1)

  // 检查是否已选择过性格
  const hasSelected = getStorage<boolean>(PERSONALITY_SELECTED_KEY, false)

  // 如果已选择过，直接跳转到对话页
  if (hasSelected) {
    isFirstSelect.value = false
    // 直接跳转
    uni.redirectTo({
      url: '/pages/chat/index',
    })
    return
  }

  // 如果是首次打开（注册后第一次），跳转到开场白页
  if (openCount === 0) {
    uni.redirectTo({
      url: '/pages/auth/ai-greeting',
    })
    return
  }

  // 如果是第2次打开且未选择性格，停留在当前页面
  isFirstSelect.value = openCount === 1
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 检查是否需要展示
  checkShouldShow()

  // 恢复之前的选择（如果有的话）
  const savedPersonality = chatStore.currentPersonality
  if (savedPersonality) {
    selectedType.value = savedPersonality
  }
})
</script>

<style lang="scss" scoped>
.personality-page {
  min-height: 100vh;
  background-color: #FFFFFF;
  padding: 40rpx 30rpx;
  padding-bottom: calc(60rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

// ==================== 标题区域 ====================

.header {
  text-align: center;
  margin-bottom: 40rpx;
}

.title {
  font-size: 48rpx;
  font-weight: 600;
  color: #080808;
  margin-bottom: 16rpx;
}

.subtitle {
  font-size: 28rpx;
  color: #333333;
}

// ==================== 性格卡片 ====================

.card-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  margin-bottom: 60rpx;
}

.personality-card {
  background-color: #F8F8FA;
  border-radius: 30rpx;
  padding: 30rpx;
  position: relative;
  border: 2px solid transparent;
  transition: all 0.3s ease;

  &:active {
    transform: scale(0.98);
  }

  &.is-selected {
    border-color: #01BEFF;
    box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(0,0,0,0.08);
  }
}

// ==================== 卡片头像 ====================

.card-avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 5000rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;

  &.avatar-xiaowen {
    background-color: rgba(231,47,140,0.1);
  }

  &.avatar-laohei {
    background-color: rgba(120,144,156,0.1);
  }

  &.avatar-ali {
    background-color: rgba(61,126,255,0.1);
  }
}

.avatar-label {
  font-size: 36rpx;
  font-weight: 600;
  color: #080808;
}

// ==================== 卡片内容 ====================

.card-name {
  margin-bottom: 8rpx;
}

.name-text {
  font-size: 34rpx;
  font-weight: 600;
  color: #080808;
}

.card-desc {
  margin-bottom: 16rpx;
}

.desc-text {
  font-size: 28rpx;
  color: #333333;
}

// ==================== 特点标签 ====================

.card-tags {
  display: flex;
  gap: 8rpx;
}

.tag {
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  background-color: #F4F4F5;
}

.tag-text {
  font-size: 22rpx;
  color: #838383;
}

// ==================== 选中指示 ====================

.selected-mark {
  position: absolute;
  top: 24rpx;
  right: 24rpx;
  width: 48rpx;
  height: 48rpx;
  border-radius: 5000rpx;
  background-color: #01BEFF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mark-icon {
  color: #FFFFFF;
  font-size: 30rpx;
  font-weight: 600;
}

// ==================== 底部按钮 ====================

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24rpx 30rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background-color: #FFFFFF;
}

.skip-btn {
  text-align: center;
  margin-bottom: 16rpx;

  &:active {
    opacity: 0.7;
  }
}

.skip-text {
  font-size: 26rpx;
  color: #838383;
}

.confirm-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  border-radius: 30rpx;
  background-color: #F4F4F5;

  &:active {
    opacity: 0.9;
  }

  &.is-active {
    background-color: #01BEFF;

    .confirm-text {
      color: #FFFFFF;
    }
  }
}

.confirm-text {
  font-size: 30rpx;
  font-weight: 500;
  color: #838383;
}
</style>