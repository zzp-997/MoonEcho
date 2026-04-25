<template>
  <view class="minor-lock-page">
    <!-- 深色背景全屏遮罩 -->
    <view class="lock-content">
      <!-- 月亮图标 -->
      <view class="moon-icon-wrap">
        <text class="moon-icon">M</text>
      </view>

      <!-- 主要文案 -->
      <text class="lock-title">该休息了</text>
      <text class="lock-subtitle">明天再来吧~</text>

      <!-- 安慰语 -->
      <view class="comfort-area">
        <text class="comfort-text">{{ comfortMessage }}</text>
      </view>

      <!-- 当前时间 -->
      <view class="time-display">
        <text class="current-time">{{ currentTime }}</text>
        <text class="time-hint">05:00 自动解锁</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 青少年模式锁定页
 * 文件：src/pages/auth/minor-lock.vue
 * 说明：22:00-05:00 期间显示，全屏遮罩
 *       深色背景，中央显示"该休息了"文案 + 安慰语 + 当前时间
 *       无跳过按钮，到05:00自动解锁
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'

// ==================== 响应式状态 ====================

/** 当前时间字符串 */
const currentTime = ref('')

/** 时间更新定时器 */
let timeTimer: ReturnType<typeof setInterval> | null = null

/** 解锁定时器 */
let unlockTimer: ReturnType<typeof setInterval> | null = null

// ==================== 计算属性 ====================

/** 安慰语（随机选取） */
const comfortMessage = computed(() => {
  const messages = [
    '好梦，明天又是新的一天',
    '今晚的事，明天再想也不迟',
    '好好休息，我在这里等你回来',
    '睡觉是最好的治愈，晚安',
    '夜深了，让心事也休息吧',
  ]
  // 使用当前分钟数作为简单的随机种子，避免每次重新渲染变化
  const index = new Date().getMinutes() % messages.length
  return messages[index]
})

// ==================== 方法 ====================

/**
 * 更新当前时间显示
 */
function updateCurrentTime() {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  currentTime.value = `${hours}:${minutes}`
}

/**
 * 检查是否已到解锁时间（05:00）
 */
function checkUnlock() {
  const hour = new Date().getHours()
  const minute = new Date().getMinutes()

  // 05:00 及之后自动解锁
  if (hour >= 5 && hour < 22) {
    // 已过锁定时段，跳转到首页
    uni.switchTab({
      url: '/pages/chat/index',
    })
  }
}

/**
 * 清除所有定时器
 */
function clearAllTimers() {
  if (timeTimer) {
    clearInterval(timeTimer)
    timeTimer = null
  }
  if (unlockTimer) {
    clearInterval(unlockTimer)
    unlockTimer = null
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 初始化时间
  updateCurrentTime()

  // 每秒更新时间
  timeTimer = setInterval(() => {
    updateCurrentTime()
  }, 1000)

  // 每分钟检查是否到了解锁时间
  unlockTimer = setInterval(() => {
    checkUnlock()
  }, 60000)
})

onUnmounted(() => {
  clearAllTimers()
})
</script>

<style lang="scss" scoped>
.minor-lock-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #0A0A0A;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lock-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 var(--space-lg);
}

// ==================== 月亮图标 ====================

.moon-icon-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background-color: rgba(251, 191, 36, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-2xl);
}

.moon-icon {
  font-size: 80rpx;
  color: var(--color-warning);
  font-weight: bold;
}

// ==================== 主要文案 ====================

.lock-title {
  font-size: 52rpx;
  font-weight: 600;
  color: #F5F5F5;
  margin-bottom: var(--space-sm);
}

.lock-subtitle {
  font-size: 32rpx;
  color: #B3B3B3;
  margin-bottom: var(--space-2xl);
}

// ==================== 安慰语 ====================

.comfort-area {
  margin-bottom: var(--space-2xl);
  padding: 0 var(--space-md);
}

.comfort-text {
  font-size: 28rpx;
  color: #808080;
  line-height: 1.8;
  text-align: center;
  font-style: italic;
}

// ==================== 时间显示 ====================

.time-display {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.current-time {
  font-size: 80rpx;
  font-weight: 300;
  color: #B3B3B3;
  letter-spacing: 4px;
  margin-bottom: var(--space-sm);
}

.time-hint {
  font-size: 24rpx;
  color: #808080;
}
</style>
