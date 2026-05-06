<template>
  <view class="profile-page">
    <!-- 顶部导航 -->
    <view class="nav-bar">
      <view class="nav-back" @tap="goBack">
        <wd-icon name="arrow-left" size="20px" color="var(--text-primary)" />
      </view>
      <text class="nav-title">完善资料</text>
      <view class="nav-placeholder"></view>
    </view>

    <!-- 主要内容 -->
    <view class="content">
      <!-- 欢迎语 -->
      <view class="welcome-section">
        <text class="welcome-title">让我认识一下你 ~</text>
        <text class="welcome-subtitle">完善资料，让我更懂你</text>
      </view>

      <!-- 昵称输入 -->
      <view class="form-section">
        <text class="section-label">你的昵称</text>
        <view class="input-wrapper">
          <wd-input
            v-model="nickname"
            placeholder="你希望我怎么称呼你？"
            :maxlength="12"
            no-border
            clearable
            @input="onNicknameInput"
            @blur="validateNickname"
          />
        </view>
        <view class="nickname-hint-row">
          <text v-if="nicknameError" class="error-text">{{ nicknameError }}</text>
          <text v-else class="char-count">{{ nicknameTrimmed.length }}/12</text>
        </view>
      </view>

      <!-- 年龄段选择 -->
      <view class="form-section">
        <text class="section-label">你的年龄段</text>
        <view class="age-options">
          <view
            v-for="option in ageOptions"
            :key="option.value"
            class="age-option"
            :class="{ selected: selectedAge === option.value }"
            @tap="selectAge(option.value)"
          >
            <text class="option-text">{{ option.label }}</text>
          </view>
        </view>
      </view>

      <!-- 青少年模式提示 -->
      <view v-if="selectedAge === 'under_18'" class="minor-notice">
        <view class="notice-icon-wrap">
          <text class="notice-icon">!</text>
        </view>
        <text class="notice-text">18岁以下用户将自动开启青少年模式，部分功能受限</text>
      </view>

      <!-- 底部渐入提示 -->
      <view v-if="showBottomHint" class="bottom-hint">
        <text class="hint-text">完善资料，让我更懂你</text>
      </view>
    </view>

    <!-- 底部按钮区域 -->
    <view class="bottom-section">
      <wd-button
        type="primary"
        block
        :disabled="!canSubmit"
        :loading="isLoading"
        @tap="handleComplete"
      >
        完成并开始使用
      </wd-button>
      <view class="skip-btn" @tap="handleSkip">
        <text class="skip-text">跳过，稍后填写</text>
      </view>
    </view>

    <!-- Toast 提示 -->
    <wd-toast />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 注册引导页（完善资料）
 * 文件：src/pages/auth/profile.vue
 * 说明：新用户注册后完善昵称和年龄段
 * 功能：
 *   - 昵称输入（2-12字符实时校验）
 *   - 年龄段选择（5个选项点击即选）
 *   - 18岁以下显示青少年模式提示
 *   - "跳过，稍后填写"选项（默认昵称"小友"）
 *   - 底部渐入提示："完善资料，让我更懂你"
 *   - 注册完成后跳转AI开场白过渡页
 */

import { ref, computed, onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'

// ==================== 年龄段选项 ====================

interface AgeOption {
  label: string
  value: string
}

const ageOptions: AgeOption[] = [
  { label: '18岁以下', value: '18岁以下' },
  { label: '18-25', value: '18-25' },
  { label: '26-35', value: '26-35' },
  { label: '36-45', value: '36-45' },
  { label: '45以上', value: '45以上' },
]

// ==================== 响应式状态 ====================

/** 昵称 */
const nickname = ref('')

/** 昵称错误 */
const nicknameError = ref('')

/** 选择的年龄段 */
const selectedAge = ref('')

/** 底部渐入提示是否显示 */
const showBottomHint = ref(false)

// ==================== 组合式函数 ====================

const { isLoading, completeProfile } = useAuth()

// ==================== 计算属性 ====================

/** 昵称去除首尾空格后的长度 */
const nicknameTrimmed = computed(() => {
  return nickname.value.trim()
})

/** 昵称是否有效（2-12字符） */
const isNicknameValid = computed(() => {
  const len = nicknameTrimmed.value.length
  return len >= 2 && len <= 12
})

/** 年龄段是否已选择 */
const isAgeSelected = computed(() => {
  return selectedAge.value !== ''
})

/** 是否可以提交 */
const canSubmit = computed(() => {
  return isNicknameValid.value && isAgeSelected.value && !isLoading.value
})

// ==================== 方法 ====================

/**
 * 昵称实时输入校验
 */
function onNicknameInput() {
  const trimmed = nicknameTrimmed.value
  if (trimmed.length > 0 && trimmed.length < 2) {
    nicknameError.value = '昵称至少2个字符'
  } else if (trimmed.length > 12) {
    nicknameError.value = '昵称不能超过12个字符'
  } else if (/[<>&"']/.test(trimmed)) {
    nicknameError.value = '昵称不能包含特殊符号'
  } else {
    nicknameError.value = ''
  }
}

/**
 * 昵称失焦校验
 */
function validateNickname() {
  const trimmed = nicknameTrimmed.value
  if (trimmed.length === 0) {
    nicknameError.value = '请输入昵称'
    return false
  }
  if (trimmed.length < 2) {
    nicknameError.value = '昵称至少2个字符'
    return false
  }
  if (trimmed.length > 12) {
    nicknameError.value = '昵称不能超过12个字符'
    return false
  }
  if (/[<>&"']/.test(trimmed)) {
    nicknameError.value = '昵称不能包含特殊符号'
    return false
  }
  nicknameError.value = ''
  return true
}

/**
 * 选择年龄段
 */
function selectAge(value: string) {
  selectedAge.value = value
}

/**
 * 完成资料 - 跳转到AI开场白过渡页
 */
async function handleComplete() {
  if (!canSubmit.value) return

  // 校验昵称
  if (!validateNickname()) return

  try {
    const success = await completeProfile(nicknameTrimmed.value, selectedAge.value)

    if (success) {
      // 跳转到AI开场白过渡页
      navigateToGreeting()
    }
  } catch (error: any) {
    nicknameError.value = error.message || '保存失败，请重试'
  }
}

/**
 * 跳过，稍后填写 - 使用默认昵称"小友"
 */
async function handleSkip() {
  try {
    // 使用默认昵称和未选择的年龄段标记
    const defaultNickname = '小友'
    const defaultAge = selectedAge.value || '18岁以下'

    const success = await completeProfile(defaultNickname, defaultAge)

    if (success) {
      // 跳转到AI开场白过渡页
      navigateToGreeting()
    }
  } catch (error: any) {
    uni.showToast({
      title: '保存失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 跳转到AI开场白过渡页
 */
function navigateToGreeting() {
  // 需要传递年龄段信息，以便开场白过渡页判断是否展示青少年模式启动页
  uni.redirectTo({
    url: `/pages/auth/ai-greeting?ageRange=${selectedAge.value || 'under_18'}`,
  })
}

/**
 * 返回上一页
 */
function goBack() {
  uni.navigateBack()
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 延迟显示底部渐入提示（1.5秒后渐入）
  setTimeout(() => {
    showBottomHint.value = true
  }, 1500)
})
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background-color: var(--bg-primary);
  display: flex;
  flex-direction: column;
}

// ==================== 导航栏 ====================

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 var(--space-md);
  padding-top: env(safe-area-inset-top);
}

.nav-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.nav-placeholder {
  width: 64rpx;
}

// ==================== 内容区域 ====================

.content {
  flex: 1;
  padding: 0 var(--space-lg);
}

.welcome-section {
  margin-top: 60rpx;
  margin-bottom: 80rpx;
}

.welcome-title {
  display: block;
  font-size: 44rpx;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.welcome-subtitle {
  font-size: 28rpx;
  color: var(--text-secondary);
}

// ==================== 表单区域 ====================

.form-section {
  margin-bottom: var(--space-xl);
}

.section-label {
  display: block;
  font-size: 28rpx;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.input-wrapper {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 0 var(--space-md);
}

.nickname-hint-row {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-xs);
  min-height: 36rpx;
}

.error-text {
  display: block;
  font-size: 24rpx;
  color: var(--color-error);
}

.char-count {
  font-size: 24rpx;
  color: var(--text-muted);
  margin-left: auto;
}

// ==================== 年龄段选择 ====================

.age-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.age-option {
  flex: 0 0 calc(50% - var(--space-xs));
  height: 88rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 2rpx solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &.selected {
    background-color: var(--brand-light);
    border-color: var(--brand-primary);
  }
}

.option-text {
  font-size: 28rpx;
  color: var(--text-secondary);

  .selected & {
    color: var(--brand-primary);
    font-weight: 500;
  }
}

// ==================== 青少年模式提示 ====================

.minor-notice {
  display: flex;
  align-items: flex-start;
  background-color: var(--color-warning-bg);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-xl);
}

.notice-icon-wrap {
  width: 36rpx;
  height: 36rpx;
  background-color: var(--color-warning);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-sm);
  flex-shrink: 0;
}

.notice-icon {
  color: var(--text-on-brand);
  font-size: 24rpx;
  font-weight: bold;
}

.notice-text {
  font-size: 24rpx;
  color: var(--color-warning);
  line-height: 1.5;
  flex: 1;
}

// ==================== 底部渐入提示 ====================

.bottom-hint {
  margin-top: var(--space-lg);
  text-align: center;
  opacity: 0;
  animation: fadeInUp 0.8s ease forwards;
}

.hint-text {
  font-size: 28rpx;
  color: var(--brand-light);
  font-style: italic;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// ==================== 底部按钮区域 ====================

.bottom-section {
  padding: var(--space-lg);
  padding-bottom: calc(var(--space-lg) + env(safe-area-inset-bottom));
}

.skip-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: var(--space-md);
  padding: var(--space-sm) 0;
}

.skip-text {
  font-size: 28rpx;
  color: var(--text-muted);
}
</style>

<style lang="scss">
// 全局样式覆盖，用于 wot-design-uni 组件样式
.profile-page {
  --wd-button-primary-bg-color: var(--brand-primary);
  --wd-button-primary-border-color: var(--brand-primary);
  --wd-input-placeholder-color: var(--text-muted);
  --wd-input-color: var(--text-primary);
}
</style>
