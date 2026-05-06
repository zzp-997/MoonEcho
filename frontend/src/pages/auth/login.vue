<template>
  <view class="login-page">
    <!-- 背景装饰 -->
    <view class="bg-decor">
      <view class="bg-circle bg-circle-1" />
      <view class="bg-circle bg-circle-2" />
    </view>

    <!-- 内容区 - flex 垂直居中 -->
    <view class="login-content">
      <!-- Logo 区域 -->
      <view class="logo-section">
        <image class="logo" src="/static/images/logo.png" mode="aspectFit" />
        <text class="brand-name">回声</text>
        <text class="brand-slogan">深夜情绪急救站，随时陪伴</text>
      </view>

      <!-- 表单卡片 -->
      <view class="form-card">
        <text class="welcome-text">您好，欢迎回来</text>

        <!-- 手机号输入 -->
        <view class="input-group">
          <view class="input-label">手机号</view>
          <view class="input-wrapper" :class="{ focused: phoneFocused }">
            <text class="input-prefix">+86</text>
            <input
              v-model="phoneNumber"
              type="number"
              placeholder="请输入手机号"
              :maxlength="11"
              :disabled="isPhoneDisabled"
              class="input-field"
              placeholder-class="input-placeholder"
              @focus="phoneFocused = true"
              @blur="phoneFocused = false; validatePhone()"
            />
            <view v-if="phoneNumber && !isPhoneDisabled" class="clear-btn" @tap="clearPhone">
              <wd-icon name="close" size="14px" color="var(--text-muted)" />
            </view>
          </view>
        </view>

        <!-- 验证码输入 -->
        <view class="input-group">
          <view class="input-label">验证码</view>
          <view class="input-wrapper code-wrapper" :class="{ focused: codeFocused }">
            <input
              v-model="codeInput"
              type="number"
              placeholder="请输入验证码"
              :maxlength="6"
              class="input-field"
              placeholder-class="input-placeholder"
              @focus="codeFocused = true"
              @blur="codeFocused = false"
            />
            <view
              class="code-btn"
              :class="{ disabled: !canGetCode || isCounting }"
              @tap="handleGetCode"
            >
              <text>{{ displayText }}</text>
            </view>
          </view>
        </view>

        <!-- 错误提示 -->
        <view v-if="errorMsg" class="error-tip">
          <wd-icon name="close-outline" size="14px" color="var(--color-error)" />
          <text class="error-text">{{ errorMsg }}</text>
        </view>

        <!-- 隐私政策 -->
        <view class="privacy-row">
          <view
            class="checkbox-wrapper"
            :class="{ checked: agreedPrivacy }"
            @tap="agreedPrivacy = !agreedPrivacy"
          >
            <wd-icon v-if="agreedPrivacy" name="check" size="12px" color="#ffffff" />
          </view>
          <text class="privacy-text">
            我已阅读并同意
            <text class="privacy-link" @tap.stop="goToPrivacy('user')">《用户协议》</text>
            和
            <text class="privacy-link" @tap.stop="goToPrivacy('privacy')">《隐私政策》</text>
          </text>
        </view>

        <!-- 自动注册提示 -->
        <view class="auto-register-hint">
          <text>首次登录即自动注册</text>
        </view>

        <!-- 登录按钮 -->
        <view
          class="login-btn"
          :class="{ active: canSubmit }"
          @tap="handleLogin"
        >
          <wd-loading v-if="isLoading" size="18px" color="#ffffff" />
          <text v-else class="login-btn-text">登录</text>
        </view>
      </view>
    </view>

    <!-- 底部 -->
    <view class="footer safe-area-bottom">
      <text class="footer-text">登录即代表同意相关协议</text>
    </view>

    <wd-toast />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 登录页
 * 设计风格：纯净白 · 暖橘
 */

import { ref, computed, onMounted, watch } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useCountdown } from '@/composables/useCountdown'

const { isLoading, sendVerifyCode, verifyCodeLogin, goToProfile } = useAuth()
const { isCounting, displayText, start, reset } = useCountdown(60)

const phoneNumber = ref('13900139000')
const codeInput = ref('123456')
const agreedPrivacy = ref(true)
const errorMsg = ref('')
const phoneFocused = ref(false)
const codeFocused = ref(false)

const isPhoneValid = computed(() => /^1[3-9]\d{9}$/.test(phoneNumber.value))
const isCodeValid = computed(() => /^\d{6}$/.test(codeInput.value))
const isPhoneDisabled = computed(() => isCounting.value)
const canGetCode = computed(() => isPhoneValid.value && !isCounting.value)
const canSubmit = computed(() => isPhoneValid.value && isCodeValid.value && agreedPrivacy.value && !isLoading.value)

function clearPhone() {
  phoneNumber.value = ''
  codeInput.value = ''
  if (isCounting.value) reset()
}

function validatePhone() {
  if (phoneNumber.value && !isPhoneValid.value) {
    errorMsg.value = '请输入正确的手机号'
    return false
  }
  errorMsg.value = ''
  return true
}

async function handleGetCode() {
  if (!canGetCode.value) return
  if (!validatePhone()) return

  try {
    await sendVerifyCode(phoneNumber.value)
    if (import.meta.env.VITE_DEBUG === 'true') {
      uni.showModal({
        title: '开发模式提示',
        content: '当前为开发环境，验证码固定为：123456',
        showCancel: false,
        confirmText: '知道了',
      })
    }
    start()
    uni.showToast({ title: '验证码已发送', icon: 'success', duration: 2000 })
  } catch (error: any) {
    errorMsg.value = error.message || '验证码发送失败，请稍后重试'
  }
}

async function handleLogin() {
  if (!canSubmit.value) return
  try {
    errorMsg.value = ''
    const result = await verifyCodeLogin(phoneNumber.value, codeInput.value)
    if (result.success) {
      if (!result.profileCompleted) {
        goToProfile()
      } else {
        uni.switchTab({ url: '/pages/home/index' })
      }
    }
  } catch (error: any) {
    errorMsg.value = error.message || '登录失败，请重试'
  }
}

function goToPrivacy(type: 'user' | 'privacy') {
  uni.showToast({ title: type === 'user' ? '用户协议' : '隐私政策', icon: 'none' })
}

function setupSmsListener() {
  // #ifdef APP-PLUS
  try {
    uni.onSMSPhoneNumberChange((res) => {
      if (res?.code) codeInput.value = res.code
    })
  } catch (e) {
    console.warn('短信自动填充不支持', e)
  }
  // #endif
}

watch(codeInput, (newVal, oldVal) => {
  if (oldVal && oldVal.length > 0 && (!newVal || newVal.length === 0) && isCounting.value) {
    reset()
  }
})

onMounted(() => {
  setupSmsListener()
})
</script>

<style lang="scss" scoped>
// ==================== 页面容器 - 暖橘渐变背景 ====================

.login-page {
  position: relative;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(165deg, #FFF5ED 0%, #FFE8D6 40%, #FFDCC4 100%);
}

// ==================== 背景装饰圆 ====================

.bg-decor {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.35;
}

.bg-circle-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(255, 154, 92, 0.3), transparent 70%);
  top: -80px;
  right: -60px;
}

.bg-circle-2 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(255, 154, 92, 0.2), transparent 70%);
  bottom: 60px;
  left: -40px;
}

// ==================== 内容区 - 一屏居中 ====================

.login-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--space-lg);
  padding-top: env(safe-area-inset-top);
  padding-bottom: calc(60px + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

// ==================== Logo 区域 ====================

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--space-xl);
}

.logo {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  box-shadow: 0 4px 16px rgba(255, 154, 92, 0.25);
}

.brand-name {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: #2d2a26;
  margin-bottom: 4px;
  letter-spacing: -0.5px;
}

.brand-slogan {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-regular);
  color: #8a7a6a;
}

// ==================== 表单卡片 - 白色浮层 ====================

.form-card {
  width: 100%;
  max-width: 380px;
  background-color: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--space-lg) var(--space-lg) var(--space-md);
  box-shadow: 0 4px 24px rgba(180, 120, 60, 0.1), 0 1px 4px rgba(0, 0, 0, 0.04);
}

.welcome-text {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-lg);
  display: block;
}

// ==================== 输入框组 ====================

.input-group {
  margin-bottom: var(--space-md);
}

.input-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.input-wrapper {
  display: flex;
  align-items: center;
  background-color: var(--bg-secondary);
  border: 1.5px solid var(--border-standard);
  border-radius: var(--radius-sm);
  padding: 0 var(--space-sm);
  height: 46px;
  transition: all 0.2s ease;

  &.focused {
    border-color: var(--brand-primary);
    box-shadow: 0 0 0 3px rgba(255, 154, 92, 0.12);
    background-color: var(--bg-elevated);
  }
}

.code-wrapper {
  padding-right: var(--space-2xs);
}

.input-prefix {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
  margin-right: var(--space-xs);
  flex-shrink: 0;
}

.input-field {
  flex: 1;
  height: 100%;
  color: var(--text-primary);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-regular);
  background: transparent;
  border: none;
  outline: none;
}

.input-placeholder {
  color: var(--text-muted);
}

.clear-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

// ==================== 验证码按钮 ====================

.code-btn {
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--brand-primary);
  border-radius: var(--radius-sm);
  color: #ffffff;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
  flex-shrink: 0;
  margin-left: var(--space-xs);
  transition: all 0.2s ease;

  &:active {
    background-color: var(--brand-hover);
    transform: scale(0.97);
  }

  &.disabled {
    background-color: var(--bg-tertiary);
    color: var(--text-disabled);

    &:active {
      transform: none;
      background-color: var(--bg-tertiary);
    }
  }
}

// ==================== 错误提示 ====================

.error-tip {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
  margin-bottom: var(--space-sm);
}

.error-text {
  font-size: var(--font-size-xs);
  color: var(--color-error);
}

// ==================== 隐私政策 ====================

.privacy-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: var(--space-xs);
}

.checkbox-wrapper {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 1.5px solid var(--border-interactive);
  background-color: var(--bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: var(--space-xs);
  margin-top: 2px;
  transition: all 0.2s ease;

  &.checked {
    background-color: var(--brand-primary);
    border-color: var(--brand-primary);
  }
}

.privacy-text {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  line-height: 1.6;
  flex: 1;
}

.privacy-link {
  color: var(--brand-primary);

  &:active {
    opacity: 0.7;
  }
}

// ==================== 自动注册提示 ====================

.auto-register-hint {
  margin-bottom: var(--space-md);

  text {
    font-size: var(--font-size-xs);
    color: var(--text-disabled);
  }
}

// ==================== 登录按钮 ====================

.login-btn {
  width: 100%;
  height: 46px;
  border-radius: var(--radius-sm);
  background-color: var(--bg-tertiary);
  color: var(--text-disabled);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &.active {
    background-color: var(--brand-primary);
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(255, 154, 92, 0.3);

    &:active {
      background-color: var(--brand-hover);
      transform: scale(0.98);
    }
  }
}

.login-btn-text {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: inherit;
}

// ==================== 底部 ====================

.footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  padding-bottom: env(safe-area-inset-bottom);
}

.footer-text {
  font-size: var(--font-size-xs);
  color: rgba(100, 80, 60, 0.4);
}

// ==================== 响应式 - 小屏适配 ====================

@media screen and (max-height: 680px) {
  .login-content {
    justify-content: flex-start;
    padding-top: calc(40px + env(safe-area-inset-top));
  }

  .logo-section {
    margin-bottom: var(--space-md);
  }

  .logo {
    width: 44px;
    height: 44px;
    margin-bottom: var(--space-xs);
  }

  .brand-name {
    font-size: var(--font-size-xl);
  }

  .brand-slogan {
    font-size: var(--font-size-xs);
  }

  .form-card {
    padding: var(--space-md);
  }

  .welcome-text {
    font-size: var(--font-size-lg);
    margin-bottom: var(--space-md);
  }

  .input-group {
    margin-bottom: var(--space-sm);
  }
}

@media screen and (max-width: 375px) {
  .form-card {
    padding: var(--space-md);
  }
}
</style>
