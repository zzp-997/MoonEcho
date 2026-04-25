<template>
  <view class="greeting-page">
    <!-- AI 开场白内容 -->
    <view class="greeting-content">
      <!-- 品牌Logo -->
      <image class="greeting-logo" src="/static/images/logo.png" mode="aspectFit" />

      <!-- 按时间段动态变化的开场白 -->
      <view class="greeting-text-area">
        <text class="greeting-text">{{ greetingMessage }}</text>
      </view>

      <!-- 渐入的引导文字 -->
      <view v-if="showGuide" class="guide-area">
        <text class="guide-text">让我们一起开始吧</text>
      </view>
    </view>

    <!-- 跳过按钮 -->
    <view class="skip-area" @tap="handleSkip">
      <text class="skip-text">跳过</text>
    </view>

    <!-- 进度指示 -->
    <view class="progress-bar">
      <view class="progress-fill" :style="{ width: progressWidth }" />
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - AI 开场白过渡页
 * 文件：src/pages/auth/ai-greeting.vue
 * 说明：注册完成后展示 AI 开场白，按时段动态变化
 *       3秒后自动跳转到首页/AI对话页，或用户点击跳过
 *       若为18岁以下用户，跳转前先展示青少年模式启动页
 * 开场白按时段变化：
 *   23:00-02:00 深夜："嗨，这么晚还没睡，是不是心里有事？我在听。"
 *   02:00-05:00 极深夜："…你也睡不着吗？这个时间醒着的人，大多心里装着点事。想说说吗？"
 *   05:00-07:00 清晨："早安。醒这么早，是没睡好还是有什么心事？"
 *   其他时间："嗨，随时随地，我都在。"
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'

// ==================== 常量 ====================

/** 自动跳转延迟（毫秒） */
const AUTO_REDIRECT_DELAY = 3000

/** 进度条动画总时长（毫秒） */
const PROGRESS_DURATION = 3000

/** 进度条更新间隔（毫秒） */
const PROGRESS_INTERVAL = 50

// ==================== 响应式状态 ====================

/** 是否显示引导文字 */
const showGuide = ref(false)

/** 进度条宽度百分比 */
const progressPercent = ref(0)

/** 定时器引用 */
let autoRedirectTimer: ReturnType<typeof setTimeout> | null = null
let guideTimer: ReturnType<typeof setTimeout> | null = null
let progressTimer: ReturnType<typeof setInterval> | null = null

/** 接收的年龄段参数 */
const ageRange = ref('')

// ==================== 计算属性 ====================

/** 进度条宽度 */
const progressWidth = computed(() => {
  return `${progressPercent.value}%`
})

/** 根据当前时间生成开场白 */
const greetingMessage = computed(() => {
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
})

// ==================== 方法 ====================

/**
 * 处理跳过
 */
function handleSkip() {
  navigateToNext()
}

/**
 * 导航到下一个页面
 * 18岁以下用户先展示青少年模式启动页，其他直接进首页
 */
function navigateToNext() {
  // 清除所有定时器
  clearAllTimers()

  const userStore = useUserStore()
  const isMinor = userStore.userInfo?.is_minor || ageRange.value === 'under_18'

  if (isMinor) {
    // 18岁以下用户先展示青少年模式启动页
    uni.redirectTo({
      url: '/pages/auth/minor-notice',
    })
  } else {
    // 其他用户直接进首页
    uni.switchTab({
      url: '/pages/chat/index',
    })
  }
}

/**
 * 启动进度条动画
 */
function startProgress() {
  const step = (PROGRESS_INTERVAL / PROGRESS_DURATION) * 100
  progressTimer = setInterval(() => {
    progressPercent.value = Math.min(progressPercent.value + step, 100)
    if (progressPercent.value >= 100) {
      if (progressTimer) {
        clearInterval(progressTimer)
        progressTimer = null
      }
    }
  }, PROGRESS_INTERVAL)
}

/**
 * 清除所有定时器
 */
function clearAllTimers() {
  if (autoRedirectTimer) {
    clearTimeout(autoRedirectTimer)
    autoRedirectTimer = null
  }
  if (guideTimer) {
    clearTimeout(guideTimer)
    guideTimer = null
  }
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 获取页面参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  if (currentPage?.options?.ageRange) {
    ageRange.value = currentPage.options.ageRange
  }

  // 1秒后显示引导文字
  guideTimer = setTimeout(() => {
    showGuide.value = true
  }, 1000)

  // 启动进度条
  startProgress()

  // 3秒后自动跳转
  autoRedirectTimer = setTimeout(() => {
    navigateToNext()
  }, AUTO_REDIRECT_DELAY)
})

onUnmounted(() => {
  clearAllTimers()
})
</script>

<style lang="scss" scoped>
.greeting-page {
  min-height: 100vh;
  background-color: var(--bg-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 0 var(--space-lg);
  box-sizing: border-box;
}

// ==================== 开场白内容 ====================

.greeting-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  justify-content: center;
  width: 100%;
}

.greeting-logo {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: var(--space-2xl);
  opacity: 0.9;
}

.greeting-text-area {
  margin-bottom: var(--space-lg);
  padding: 0 var(--space-md);
}

.greeting-text {
  font-size: 36rpx;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.8;
  text-align: center;
  letter-spacing: 1px;
}

// ==================== 引导文字 ====================

.guide-area {
  margin-top: var(--space-xl);
  opacity: 0;
  animation: fadeIn 0.8s ease forwards;
}

.guide-text {
  font-size: 28rpx;
  color: var(--text-secondary);
  letter-spacing: 2px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

// ==================== 跳过按钮 ====================

.skip-area {
  position: absolute;
  top: calc(env(safe-area-inset-top) + 40rpx);
  right: var(--space-lg);
  padding: var(--space-sm) var(--space-md);
}

.skip-text {
  font-size: 28rpx;
  color: var(--text-tertiary);
}

// ==================== 进度条 ====================

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 6rpx;
  background-color: var(--bg-tertiary);
}

.progress-fill {
  height: 100%;
  background-color: var(--brand-primary);
  transition: width 50ms linear;
}
</style>
