<template>
  <view class="profile-page">
    <!-- 顶部导航 -->
    <view class="nav-bar">
      <view class="nav-back" @tap="goBack">
        <wd-icon name="arrow-left" size="20px" color="#080808" />
      </view>
      <text class="nav-title">完善资料</text>
      <view class="nav-spacer" />
    </view>

    <!-- 内容 -->
    <view class="content">
      <!-- 欢迎 -->
      <view class="intro">
        <text class="intro-title">让我认识一下你</text>
        <text class="intro-sub">这些信息帮我更好地陪伴你</text>
      </view>

      <!-- 昵称 -->
      <view class="field-group">
        <text class="field-label">昵称</text>
        <view class="nickname-field" :class="{ focused: nicknameFocused }">
          <input
            v-model="nickname"
            placeholder="你想让我怎么称呼你"
            :maxlength="12"
            class="nickname-input"
            placeholder-class="field-placeholder"
            @input="onNicknameInput"
            @blur="validateNickname"
            @focus="nicknameFocused = true"
          />
          <text class="char-count" :class="{ error: !!nicknameError }">{{ nicknameTrimmed.length }}/12</text>
        </view>
        <text v-if="nicknameError" class="field-error">{{ nicknameError }}</text>
      </view>

      <!-- 年龄段 -->
      <view class="field-group">
        <text class="field-label">年龄段</text>
        <view class="age-chips">
          <view
            v-for="option in ageOptions"
            :key="option.value"
            class="age-chip"
            :class="{ selected: selectedAge === option.value }"
            @tap="selectAge(option.value)"
          >
            <text class="chip-text">{{ option.label }}</text>
          </view>
        </view>
      </view>

      <!-- 青少年模式提示 -->
      <view v-if="selectedAge === '18岁以下'" class="minor-notice">
        <text class="minor-text">18岁以下用户将自动开启青少年模式，部分功能受限</text>
      </view>
    </view>

    <!-- 底部操作 -->
    <view class="bottom-area">
      <view
        class="complete-btn"
        :class="{ active: canSubmit }"
        @tap="handleComplete"
      >
        <wd-loading v-if="isLoading" size="16px" color="#FFFFFF" />
        <text v-else class="complete-btn-text">开始使用</text>
      </view>
      <view class="skip-action" @tap="handleSkip">
        <text class="skip-text">跳过，稍后再说</text>
      </view>
    </view>

    <wd-toast />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

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

const nickname = ref('')
const nicknameError = ref('')
const nicknameFocused = ref(false)
const selectedAge = ref('')

const { isLoading, completeProfile } = useAuth()

const nicknameTrimmed = computed(() => nickname.value.trim())

const isNicknameValid = computed(() => {
  const len = nicknameTrimmed.value.length
  return len >= 2 && len <= 12
})

const canSubmit = computed(() => {
  return isNicknameValid.value && selectedAge.value !== '' && !isLoading.value
})

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

function validateNickname() {
  nicknameFocused.value = false
  const trimmed = nicknameTrimmed.value
  if (trimmed.length === 0) {
    nicknameError.value = '请输入昵称'
    return false
  }
  if (trimmed.length < 2) {
    nicknameError.value = '昵称至少2个字符'
    return false
  }
  if (/[<>&"']/.test(trimmed)) {
    nicknameError.value = '昵称不能包含特殊符号'
    return false
  }
  nicknameError.value = ''
  return true
}

function selectAge(value: string) {
  selectedAge.value = value
}

async function handleComplete() {
  if (!canSubmit.value) return
  if (!validateNickname()) return

  try {
    const success = await completeProfile(nicknameTrimmed.value, selectedAge.value)
    if (success) {
      navigateToGreeting()
    }
  } catch (error: any) {
    nicknameError.value = error.message || '保存失败，请重试'
  }
}

async function handleSkip() {
  try {
    const defaultNickname = '小友'
    const defaultAge = selectedAge.value || '18岁以下'
    const success = await completeProfile(defaultNickname, defaultAge)
    if (success) {
      navigateToGreeting()
    }
  } catch (error: any) {
    uni.showToast({ title: '保存失败，请重试', icon: 'none' })
  }
}

function navigateToGreeting() {
  uni.redirectTo({
    url: `/pages/auth/ai-greeting?ageRange=${selectedAge.value || 'under_18'}`,
  })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
}

// ==================== 导航栏 ====================

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 24rpx;
  padding-top: env(safe-area-inset-top);
  border-bottom: 1px solid #F4F4F5;
}

.nav-back {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #080808;
}

.nav-spacer {
  width: 32px;
}

// ==================== 内容 ====================

.content {
  flex: 1;
  padding: 30rpx;
}

.intro {
  margin-bottom: 40rpx;
}

.intro-title {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: #080808;
  margin-bottom: 6rpx;
}

.intro-sub {
  font-size: 26rpx;
  color: #838383;
}

// ==================== 表单字段 ====================

.field-group {
  margin-bottom: 40rpx;
}

.field-label {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: #333333;
  margin-bottom: 16rpx;
}

.field-placeholder {
  color: #838383;
}

// ==================== 昵称输入 ====================

.nickname-field {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #E0E0E0;
  padding: 16rpx 0;
  transition: border-color 0.15s ease-out;

  &.focused {
    border-color: #080808;
  }
}

.nickname-input {
  flex: 1;
  font-size: 28rpx;
  color: #080808;
  background: transparent;
  border: none;
  outline: none;
}

.char-count {
  font-size: 22rpx;
  color: #838383;
  flex-shrink: 0;
  margin-left: 8rpx;

  &.error {
    color: #E83A30;
  }
}

.field-error {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #E83A30;
}

// ==================== 年龄段 Chips ====================

.age-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.age-chip {
  padding: 8rpx 24rpx;
  border-radius: 10rpx;
  border: 1px solid #E0E0E0;
  background-color: transparent;
  transition: all 0.15s ease-out;

  &.selected {
    border-color: #080808;
    background-color: rgba(1,190,255,0.1);
  }
}

.chip-text {
  font-size: 26rpx;
  color: #333333;

  .selected & {
    color: #080808;
    font-weight: 500;
  }
}

// ==================== 青少年提示 ====================

.minor-notice {
  padding: 16rpx 24rpx;
  border-radius: 10rpx;
  border: 1px solid #F4F4F5;
  background-color: #F8F8FA;
}

.minor-text {
  font-size: 22rpx;
  color: #333333;
  line-height: 1.5;
}

// ==================== 底部 ====================

.bottom-area {
  padding: 30rpx;
  padding-bottom: calc(30rpx + env(safe-area-inset-bottom));
}

.complete-btn {
  width: 100%;
  height: 48px;
  border-radius: 10rpx;
  background-color: #F4F4F5;
  color: #AAAAAA;
  font-size: 28rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease-out, color 0.15s ease-out;

  &.active {
    background-color: #01BEFF;
    color: #FFFFFF;

    &:active {
      background-color: #01B0E8;
      transform: scale(0.98);
      transition: transform 0.1s ease-out;
    }
  }
}

.complete-btn-text {
  font-size: 28rpx;
  font-weight: 500;
  color: inherit;
  letter-spacing: 1px;
}

.skip-action {
  display: flex;
  justify-content: center;
  margin-top: 24rpx;
  padding: 16rpx 0;
}

.skip-text {
  font-size: 26rpx;
  color: #838383;
}
</style>
