<template>
  <view class="login-page">
    <!-- 顶部背景装饰 -->
    <view class="top-bg">
      <image class="bg-img" src="https://resource.tuniaokj.com/images/login/1/login_top2.jpg" mode="aspectFill" />
      <view class="deco-circle deco-circle-1 tn-shadow-blur" />
      <view class="deco-circle deco-circle-2 tn-shadow-blur" />
    </view>

    <!-- 内容区 -->
    <view class="login-wrapper">
      <!-- 品牌区域 -->
      <view class="brand-section">
        <view class="brand-icon tn-shadow-blur">
          <text class="brand-icon-text">回</text>
        </view>
        <text class="brand-name">回声</text>
        <text class="brand-slogan">这里听得见你</text>
      </view>

      <!-- 表单卡片 -->
      <view class="form-card tn-shadow-card">
        <!-- 手机号 -->
        <view class="field-item">
          <view class="field-icon">
            <text style="font-size: 40rpx;">📱</text>
          </view>
          <view class="field-content">
            <input
              v-model="phoneNumber"
              type="number"
              placeholder="请输入手机号"
              :maxlength="11"
              :disabled="isPhoneDisabled"
              class="field-input"
              placeholder-class="field-placeholder"
            />
          </view>
          <view v-if="phoneNumber && !isPhoneDisabled" class="field-clear" @tap="clearPhone">
            <text style="font-size: 28rpx; color: #AAAAAA;">✕</text>
          </view>
        </view>

        <!-- 验证码 -->
        <view class="field-item">
          <view class="field-icon">
            <text style="font-size: 40rpx;">🔐</text>
          </view>
          <view class="field-content field-content--code">
            <input
              v-model="codeInput"
              type="number"
              placeholder="请输入验证码"
              :maxlength="6"
              class="field-input"
              placeholder-class="field-placeholder"
            />
          </view>
          <view class="code-btn" :class="{ 'is-disabled': !canGetCode || isCounting }" @tap="handleGetCode">
            <text class="code-btn-text">{{ displayText }}</text>
          </view>
        </view>

        <!-- 错误提示 -->
        <view v-if="errorMsg" class="error-row">
          <text class="error-text">{{ errorMsg }}</text>
        </view>

        <!-- 隐私协议 -->
        <view class="privacy-row">
          <view class="checkbox" :class="{ 'is-checked': agreedPrivacy }" @tap="agreedPrivacy = !agreedPrivacy">
            <text v-if="agreedPrivacy" class="checkbox-icon">✓</text>
          </view>
          <text class="privacy-text">
            我已阅读并同意
            <text class="privacy-link" @tap.stop="goToPrivacy('user')">《用户协议》</text>
            和
            <text class="privacy-link" @tap.stop="goToPrivacy('privacy')">《隐私政策》</text>
          </text>
        </view>

        <!-- 登录按钮 -->
        <view class="submit-btn" :class="{ 'is-active': canSubmit }" @tap="handleLogin">
          <wd-loading v-if="isLoading" size="18px" color="#FFFFFF" />
          <text v-else class="submit-btn-text">进 入 回 声</text>
        </view>

        <!-- 自动注册提示 -->
        <text class="auto-hint">首次登录即自动注册</text>
      </view>

      <!-- 其他登录方式 -->
      <view class="other-login">
        <text class="other-login-title">其他登录方式</text>
        <view class="other-login-icons">
          <view class="login-icon login-icon--wechat tn-shadow-blur">
            <text style="font-size: 44rpx;">💬</text>
          </view>
          <view class="login-icon login-icon--apple tn-shadow-blur">
            <text style="font-size: 44rpx;">🍎</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
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
.login-page {
  min-height: 100vh;
  background-color: #F8F7F8;
  position: relative;
  overflow: hidden;
}

// ==================== 顶部背景 ====================

.top-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 520rpx;
  overflow: hidden;

  .bg-img {
    width: 100%;
    height: 100%;
    opacity: 0.85;
  }

  .deco-circle {
    position: absolute;
    border-radius: 50%;

    &-1 {
      width: 260rpx;
      height: 260rpx;
      top: 60rpx;
      right: -60rpx;
      background: linear-gradient(135deg, rgba(231, 47, 140, 0.6), rgba(243, 96, 167, 0.4));
      box-shadow: 16rpx 16rpx 24rpx rgba(231, 47, 140, 0.3);
    }

    &-2 {
      width: 180rpx;
      height: 180rpx;
      top: 200rpx;
      left: -40rpx;
      background: linear-gradient(135deg, rgba(1, 190, 255, 0.5), rgba(61, 126, 255, 0.35));
      box-shadow: 12rpx 12rpx 20rpx rgba(1, 190, 255, 0.25);
    }
  }
}

// ==================== 内容区 ====================

.login-wrapper {
  position: relative;
  z-index: 1;
  padding: 0 30rpx;
  padding-top: 100rpx;
}

// ==================== 品牌区域 ====================

.brand-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60rpx;
}

.brand-icon {
  width: 130rpx;
  height: 130rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #E72F8C, #F360A7);
  box-shadow: 16rpx 16rpx 24rpx rgba(231, 47, 140, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28rpx;
}

.brand-icon-text {
  font-size: 54rpx;
  font-weight: 700;
  color: #FFFFFF;
}

.brand-name {
  font-size: 48rpx;
  font-weight: 700;
  color: #080808;
  margin-bottom: 12rpx;
  letter-spacing: 4rpx;
}

.brand-slogan {
  font-size: 28rpx;
  color: #838383;
  letter-spacing: 2rpx;
}

// ==================== 表单卡片 ====================

.form-card {
  margin: 0 10rpx;
  padding: 50rpx 40rpx;
  background-color: #FFFFFF;
  border-radius: 24rpx;
  box-shadow: 0rpx 0rpx 80rpx 0rpx rgba(0, 0, 0, 0.07);
}

.field-item {
  display: flex;
  align-items: center;
  height: 100rpx;
  margin-top: 30rpx;
  padding: 0 24rpx;
  border: 2rpx solid #E4E9EC;
  border-radius: 50rpx;
  background-color: #FAFBFC;
  transition: all 0.2s ease;

  &:first-child {
    margin-top: 0;
  }

  &:active {
    border-color: #01BEFF;
    background-color: #FFFFFF;
  }
}

.field-icon {
  width: 60rpx;
  font-size: 40rpx;
  color: #78909C;
  flex-shrink: 0;
}

.field-content {
  flex: 1;
  padding-left: 16rpx;

  &--code {
    flex: 0 1 55%;
  }
}

.field-input {
  width: 100%;
  height: 100rpx;
  font-size: 30rpx;
  color: #080808;
}

.field-placeholder {
  color: #AAAAAA;
}

.field-clear {
  width: 44rpx;
  height: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F4F4F5;
  border-radius: 50%;
  flex-shrink: 0;
}

// ==================== 验证码按钮 ====================

.code-btn {
  flex-shrink: 0;
  margin-left: 16rpx;
  padding: 14rpx 24rpx;
  background: linear-gradient(135deg, #01BEFF, #3D7EFF);
  border-radius: 50rpx;
  box-shadow: 8rpx 8rpx 16rpx rgba(1, 190, 255, 0.2);

  &.is-disabled {
    background: #E4E9EC;
    box-shadow: none;
  }
}

.code-btn-text {
  font-size: 26rpx;
  font-weight: 500;
  color: #FFFFFF;
  white-space: nowrap;
}

// ==================== 错误提示 ====================

.error-row {
  margin-top: 20rpx;
  padding: 16rpx 24rpx;
  background: rgba(232, 58, 48, 0.08);
  border-radius: 12rpx;
}

.error-text {
  font-size: 24rpx;
  color: #E83A30;
}

// ==================== 隐私协议 ====================

.privacy-row {
  display: flex;
  align-items: flex-start;
  margin-top: 40rpx;
}

.checkbox {
  width: 36rpx;
  height: 36rpx;
  border-radius: 8rpx;
  border: 3rpx solid #01BEFF;
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12rpx;
  margin-top: 4rpx;
  transition: all 0.15s ease;

  &.is-checked {
    background-color: #01BEFF;
    border-color: #01BEFF;
  }
}

.checkbox-icon {
  font-size: 24rpx;
  color: #FFFFFF;
  font-weight: 700;
}

.privacy-text {
  flex: 1;
  font-size: 24rpx;
  color: #838383;
  line-height: 1.6;
}

.privacy-link {
  color: #01BEFF;
}

// ==================== 登录按钮 ====================

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100rpx;
  margin-top: 50rpx;
  background: linear-gradient(135deg, #E4E9EC, #D8DDE0);
  border-radius: 50rpx;
  transition: all 0.3s ease;
  letter-spacing: 6rpx;

  &.is-active {
    background: linear-gradient(135deg, #01BEFF, #3D7EFF);
    box-shadow: 0rpx 16rpx 48rpx 0rpx rgba(1, 190, 255, 0.35);

    .submit-btn-text {
      color: #FFFFFF;
    }

    &:active {
      transform: scale(0.97);
    }
  }
}

.submit-btn-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #AAAAAA;
  letter-spacing: 8rpx;
}

// ==================== 自动注册提示 ====================

.auto-hint {
  display: block;
  margin-top: 24rpx;
  text-align: center;
  font-size: 24rpx;
  color: #AAAAAA;
}

// ==================== 其他登录方式 ====================

.other-login {
  margin-top: 80rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.other-login-title {
  font-size: 24rpx;
  color: #AAAAAA;
  margin-bottom: 30rpx;
}

.other-login-icons {
  display: flex;
  gap: 40rpx;
}

.login-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;

  &::after {
    content: ' ';
    position: absolute;
    z-index: -1;
    width: 100%;
    height: 100%;
    left: 0;
    bottom: 0;
    border-radius: inherit;
    opacity: 1;
    transform: scale(1);
    background-size: 100% 100%;
    background-image: url(https://resource.tuniaokj.com/images/cool_bg_image/icon_bg5.png);
  }

  &--wechat {
    background: linear-gradient(135deg, #2DE8BD, #24F083);
    box-shadow: 12rpx 12rpx 16rpx rgba(45, 232, 189, 0.25);
  }

  &--apple {
    background: linear-gradient(135deg, #080808, #333333);
    box-shadow: 12rpx 12rpx 16rpx rgba(0, 0, 0, 0.2);
  }
}

// ==================== 小屏适配 ====================

@media screen and (max-height: 680px) {
  .login-wrapper {
    padding-top: 60rpx;
  }

  .brand-section {
    margin-bottom: 40rpx;
  }

  .brand-icon {
    width: 100rpx;
    height: 100rpx;
  }

  .brand-icon-text {
    font-size: 44rpx;
  }

  .brand-name {
    font-size: 40rpx;
  }

  .other-login {
    margin-top: 50rpx;
  }
}
</style>
