<template>
  <view class="login-page">
    <!-- 顶部装饰区域 -->
    <view class="header">
      <image class="logo" src="/static/images/logo.png" mode="aspectFit" />
      <text class="title">您好，欢迎来到回声</text>
      <text class="subtitle">深夜情绪急救站，随时陪伴</text>
    </view>

    <!-- 表单区域 -->
    <view class="form-container">
      <!-- 手机号输入 -->
      <view class="input-group">
        <wd-input
          v-model="phoneNumber"
          type="number"
          placeholder="请输入手机号"
          :maxlength="11"
          :disabled="isPhoneDisabled"
          no-border
          clearable
          @blur="validatePhone"
        >
          <template #prefix>
            <text class="input-prefix">+86</text>
          </template>
        </wd-input>
      </view>

      <!-- 验证码输入 -->
      <view class="input-group">
        <wd-input
          v-model="codeInput"
          type="number"
          placeholder="请输入验证码"
          :maxlength="6"
          no-border
          clearable
        >
          <template #suffix>
            <view
              class="code-btn"
              :class="{ disabled: !canGetCode || isCounting }"
              @tap="handleGetCode"
            >
              <text>{{ displayText }}</text>
            </view>
          </template>
        </wd-input>
      </view>

      <!-- 错误提示 -->
      <view v-if="errorMsg" class="error-tip">
        <text>{{ errorMsg }}</text>
      </view>

      <!-- 隐私政策 -->
      <view class="privacy-row">
        <wd-checkbox
          v-model="agreedPrivacy"
          shape="square"
          checked-color="var(--brand-primary)"
        />
        <text class="privacy-text">
          我已阅读并同意
          <text class="privacy-link" @tap="goToPrivacy('user')">《用户协议》</text>
          和
          <text class="privacy-link" @tap="goToPrivacy('privacy')">《隐私政策》</text>
        </text>
      </view>

      <!-- 首次登录即自动注册提示 -->
      <view class="auto-register-hint">
        <text>首次登录即自动注册</text>
      </view>

      <!-- 登录按钮 -->
      <view class="login-btn-container">
        <wd-button
          type="primary"
          block
          :disabled="!canSubmit"
          :loading="isLoading"
          @tap="handleLogin"
        >
          登录
        </wd-button>
      </view>
    </view>

    <!-- 微信登录区域（MVP阶段隐藏） -->
    <!-- #ifdef MP-WEIXIN -->
    <view v-if="WECHAT_LOGIN_ENABLED" class="wechat-section">
      <view class="divider-row">
        <view class="divider-line" />
        <text class="divider-text">其他方式</text>
        <view class="divider-line" />
      </view>
      <view class="wechat-btn" @tap="handleWechatLogin">
        <text class="wechat-icon">W</text>
        <text class="wechat-text">微信登录</text>
      </view>
    </view>
    <!-- #endif -->

    <!-- 底部提示 -->
    <view class="footer">
      <text class="footer-text">登录即代表同意相关协议</text>
    </view>

    <!-- Toast 提示 -->
    <wd-toast />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 登录页
 * 文件：src/pages/auth/login.vue
 * 说明：手机号验证码登录，支持 iOS/Android 自动读取短信验证码
 * 交互规则：
 *   - 倒计时期间手机号输入框置灰不可修改
 *   - 验证码输入框保持可编辑
 *   - 修改手机号需先清空验证码，清空后手机号恢复可编辑且倒计时重置
 *   - 倒计时结束后文案变为"重新获取"
 */

import { ref, computed, onMounted, watch } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useCountdown } from '@/composables/useCountdown'

// ==================== 常量 ====================

/** 微信登录开关（MVP阶段关闭） */
const WECHAT_LOGIN_ENABLED = false

// ==================== 响应式状态 ====================

/** 手机号 */
const phoneNumber = ref('13900139000')

/** 验证码输入值 */
const codeInput = ref('123456')

/** 是否同意隐私政策 */
const agreedPrivacy = ref(true)

/** 错误提示 */
const errorMsg = ref('')

// ==================== 组合式函数 ====================

const { isLoading, sendVerifyCode, verifyCodeLogin, goToProfile, goToHome } = useAuth()
const { isCounting, displayText, start, reset } = useCountdown(60)

// ==================== 计算属性 ====================

/** 手机号是否有效 */
const isPhoneValid = computed(() => {
  return /^1[3-9]\d{9}$/.test(phoneNumber.value)
})

/** 验证码是否有效 */
const isCodeValid = computed(() => {
  return /^\d{6}$/.test(codeInput.value)
})

/** 倒计时期间手机号禁用 */
const isPhoneDisabled = computed(() => {
  return isCounting.value
})

/** 是否可以获取验证码 */
const canGetCode = computed(() => {
  return isPhoneValid.value && !isCounting.value
})

/** 是否可以提交登录 */
const canSubmit = computed(() => {
  return isPhoneValid.value && isCodeValid.value && agreedPrivacy.value && !isLoading.value
})

// ==================== 方法 ====================

/**
 * 校验手机号
 */
function validatePhone() {
  if (phoneNumber.value && !isPhoneValid.value) {
    errorMsg.value = '请输入正确的手机号'
    return false
  }
  errorMsg.value = ''
  return true
}

/**
 * 处理获取验证码
 */
async function handleGetCode() {
  if (!canGetCode.value) return

  // 先校验手机号
  if (!validatePhone()) return

  try {
    await sendVerifyCode(phoneNumber.value)

    // 开发环境提示固定验证码
    if (import.meta.env.VITE_DEBUG === 'true') {
      uni.showModal({
        title: '开发模式提示',
        content: '当前为开发环境，验证码固定为：123456',
        showCancel: false,
        confirmText: '知道了',
      })
    }

    // 开始倒计时
    start()

    // 显示 Toast 提示
    uni.showToast({
      title: '验证码已发送',
      icon: 'success',
      duration: 2000,
    })
  } catch (error: any) {
    errorMsg.value = error.message || '验证码发送失败，请稍后重试'
  }
}

/**
 * 处理登录
 */
async function handleLogin() {
  if (!canSubmit.value) return

  try {
    errorMsg.value = ''
    const result = await verifyCodeLogin(phoneNumber.value, codeInput.value)

    if (result.success) {
      // 核心判断：资料是否完善（无论新老用户，未完善都需要先完善资料）
      if (!result.profileCompleted) {
        // 资料未完善，跳转到完善资料页
        goToProfile()
      } else {
        // 资料已完善，跳转到首页
        uni.switchTab({ url: '/pages/home/index' })
      }
    }
  } catch (error: any) {
    errorMsg.value = error.message || '登录失败，请重试'
  }
}

/**
 * 跳转协议页面
 */
function goToPrivacy(type: 'user' | 'privacy') {
  // TODO: 实现协议页面
  uni.showToast({
    title: type === 'user' ? '用户协议' : '隐私政策',
    icon: 'none',
  })
}

/**
 * 微信登录（MVP阶段预留）
 */
function handleWechatLogin() {
  uni.showToast({
    title: '微信登录暂未开放',
    icon: 'none',
  })
}

/**
 * 自动读取短信验证码
 * 使用 uni.onSMSPhoneNumberChange 监听短信验证码
 */
function setupSmsListener() {
  // #ifdef APP-PLUS
  try {
    // 监听短信验证码自动填充
    uni.onSMSPhoneNumberChange((res) => {
      if (res && res.code) {
        codeInput.value = res.code
      }
    })
  } catch (e) {
    console.warn('短信自动填充不支持', e)
  }
  // #endif
}

// ==================== 监听变化 ====================

/**
 * 核心交互规则：
 * 清空验证码时 -> 手机号恢复可编辑 + 倒计时重置
 * 倒计时期间 -> 手机号置灰不可修改（通过 isPhoneDisabled computed 控制）
 */
watch(codeInput, (newVal, oldVal) => {
  // 当验证码从有值变为空时，重置倒计时，让手机号恢复可编辑
  if (oldVal && oldVal.length > 0 && (!newVal || newVal.length === 0)) {
    if (isCounting.value) {
      reset()
    }
  }
})

// ==================== 生命周期 ====================

onMounted(() => {
  setupSmsListener()
})
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background-color: var(--bg-primary);
  padding: 0 var(--space-md);
  padding-top: 160rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

// ==================== 头部区域 ====================

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--space-xl);
}

.logo {
  width: 140rpx;
  height: 140rpx;
  margin-bottom: var(--space-md);
  border-radius: var(--radius-lg);
}

.title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
  text-align: center;
}

.subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-align: center;
}

// ==================== 表单区域 ====================

.form-container {
  width: 100%;
}

.input-group {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  padding: 0 var(--space-xs);
  overflow: hidden;
}

.input-prefix {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  margin-right: var(--space-xs);
}

.code-btn {
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--brand-primary);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;

  text {
    color: var(--text-on-brand);
    font-size: var(--font-size-xs);
    white-space: nowrap;
  }

  &.disabled {
    background-color: var(--bg-tertiary);

    text {
      color: var(--text-tertiary);
    }
  }
}

.error-tip {
  margin-bottom: var(--space-sm);

  text {
    color: var(--color-error);
    font-size: var(--font-size-xs);
  }
}

// ==================== 隐私政策 ====================

.privacy-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: var(--space-xs);
}

.privacy-text {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  margin-left: var(--space-2xs);
}

.privacy-link {
  color: var(--brand-primary);
}

// ==================== 自动注册提示 ====================

.auto-register-hint {
  margin-bottom: var(--space-md);

  text {
    font-size: var(--font-size-xs);
    color: var(--text-tertiary);
  }
}

// ==================== 登录按钮 ====================

.login-btn-container {
  margin-top: var(--space-sm);
}

// ==================== 微信登录区域 ====================

.wechat-section {
  margin-top: var(--space-xl);
}

.divider-row {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-md);
}

.divider-line {
  flex: 1;
  height: 1px;
  background-color: var(--border-primary);
}

.divider-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  padding: 0 var(--space-sm);
}

.wechat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
}

.wechat-icon {
  width: 56rpx;
  height: 56rpx;
  background-color: #07C160;
  border-radius: 50%;
  color: #FFFFFF;
  font-size: 28rpx;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wechat-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 底部 ====================

.footer {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: calc(var(--space-lg) + env(safe-area-inset-bottom));
}

.footer-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}
</style>

<style lang="scss">
// 全局样式覆盖，用于 wot-design-uni 组件样式
.login-page {
  --wd-button-primary-bg-color: var(--brand-primary);
  --wd-button-primary-border-color: var(--brand-primary);
  --wd-input-placeholder-color: var(--text-tertiary);
  --wd-input-color: var(--text-primary);
  --wd-input-disabled-color: var(--text-tertiary);
}
</style>
