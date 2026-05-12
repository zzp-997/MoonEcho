<template>
  <view class="greeting-page">
    <!-- AI 开场白 -->
    <view class="greeting-body">
      <text class="greeting-text">{{ greetingMessage }}</text>
      <view v-if="showGuide" class="guide-line">
        <text class="guide-text">让我们一起开始</text>
      </view>
    </view>

    <!-- 跳过 -->
    <view class="skip-action" @tap="handleSkip">
      <text class="skip-text">跳过</text>
    </view>

    <!-- 底部进度线 -->
    <view class="progress-track">
      <view class="progress-fill" :style="{ width: progressPercent + '%' }" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'

const AUTO_REDIRECT_DELAY = 3000
const PROGRESS_DURATION = 3000
const PROGRESS_INTERVAL = 50

const showGuide = ref(false)
const progressPercent = ref(0)
const ageRange = ref('')

let autoRedirectTimer: ReturnType<typeof setTimeout> | null = null
let guideTimer: ReturnType<typeof setTimeout> | null = null
let progressTimer: ReturnType<typeof setInterval> | null = null

const greetingMessage = computed(() => {
  const hour = new Date().getHours()

  if (hour >= 23 || hour < 2) {
    return '这么晚还没睡，是不是心里有事？我在听。'
  } else if (hour >= 2 && hour < 5) {
    return '你也睡不着吗？这个时间醒着的人，大多心里装着点事。'
  } else if (hour >= 5 && hour < 7) {
    return '早安。醒这么早，是没睡好还是有什么心事？'
  } else {
    return '嗨，随时随地，我都在。'
  }
})

function handleSkip() {
  navigateToNext()
}

function navigateToNext() {
  clearAllTimers()

  const userStore = useUserStore()
  const isMinor = userStore.userInfo?.is_minor || ageRange.value === 'under_18'

  if (isMinor) {
    uni.redirectTo({ url: '/pages/auth/minor-notice' })
  } else {
    uni.switchTab({ url: '/pages/home/index' })
  }
}

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

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  if (currentPage?.options?.ageRange) {
    ageRange.value = currentPage.options.ageRange
  }

  guideTimer = setTimeout(() => {
    showGuide.value = true
  }, 1000)

  startProgress()

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
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 0 40rpx;
  box-sizing: border-box;
}

// ==================== 开场白 ====================

.greeting-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.greeting-text {
  font-size: 20px;
  font-weight: 500;
  color: #080808;
  line-height: 1.8;
  letter-spacing: 0.5px;
}

.guide-line {
  margin-top: 40rpx;
  opacity: 0;
  animation: fadeIn 0.6s ease-out forwards;
}

.guide-text {
  font-size: 26rpx;
  color: #838383;
  letter-spacing: 2px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

// ==================== 跳过 ====================

.skip-action {
  position: absolute;
  top: calc(env(safe-area-inset-top) + 16px);
  right: 30rpx;
  padding: 8rpx;
}

.skip-text {
  font-size: 26rpx;
  color: #838383;
}

// ==================== 进度线 ====================

.progress-track {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #F4F4F5;
}

.progress-fill {
  height: 100%;
  background-color: #333333;
  transition: width 0.05s linear;
}
</style>
