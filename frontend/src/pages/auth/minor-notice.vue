<template>
  <view class="minor-notice-page">
    <!-- 顶部区域 -->
    <view class="header">
      <view class="shield-icon-wrap">
        <text class="shield-icon">S</text>
      </view>
      <text class="header-title">青少年模式</text>
      <text class="header-subtitle">为未成年人提供更安全的使用环境</text>
    </view>

    <!-- 受限功能说明 -->
    <view class="section">
      <text class="section-title">功能限制说明</text>
      <view class="info-list">
        <view class="info-item">
          <view class="info-dot" />
          <text class="info-text">树洞内容受限，仅展示适龄内容</text>
        </view>
        <view class="info-item">
          <view class="info-dot" />
          <text class="info-text">AI对话将过滤敏感话题，确保对话安全</text>
        </view>
        <view class="info-item">
          <view class="info-dot" />
          <text class="info-text">禁止私聊发送图片</text>
        </view>
      </view>
    </view>

    <!-- 使用时长限制说明 -->
    <view class="section">
      <text class="section-title">使用时长限制</text>
      <view class="info-list">
        <view class="info-item">
          <view class="info-dot dot-warning" />
          <text class="info-text">22:00 后禁止使用，保护你的睡眠</text>
        </view>
        <view class="info-item">
          <view class="info-dot dot-warning" />
          <text class="info-text">每小时会温馨提醒你休息</text>
        </view>
        <view class="info-item">
          <view class="info-dot dot-warning" />
          <text class="info-text">21:55 提前5分钟提醒你准备休息</text>
        </view>
      </view>
    </view>

    <!-- 温馨提示 -->
    <view class="warm-tip">
      <text class="warm-tip-text">我们希望你健康快乐地成长，这些限制是为了保护你</text>
    </view>

    <!-- 确认按钮 -->
    <view class="bottom-section">
      <wd-button
        type="primary"
        block
        @tap="handleConfirm"
      >
        我已知悉
      </wd-button>
    </view>

    <!-- Toast 提示 -->
    <wd-toast />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 青少年模式启动页
 * 文件：src/pages/auth/minor-notice.vue
 * 说明：18岁以下用户首次进入后展示，告知受限功能和使用时长限制
 *       用户点击"我已知悉"后跳转到首页
 */

import { useSettingsStore } from '@/stores/settings'

// ==================== 组合式函数 ====================

const settingsStore = useSettingsStore()

// ==================== 方法 ====================

/**
 * 确认已知悉 - 开启青少年模式并跳转到首页
 */
function handleConfirm() {
  // 开启青少年模式
  settingsStore.enableTeenMode()

  // 记录已阅读青少年模式通知
  uni.setStorageSync('huisheng_minor_notice_shown', true)

  // 跳转到首页
  uni.switchTab({
    url: '/pages/home/index',
  })
}
</script>

<style lang="scss" scoped>
.minor-notice-page {
  min-height: 100vh;
  background-color: #FFFFFF;
  padding: 0 30rpx;
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
  margin-bottom: 60rpx;
}

.shield-icon-wrap {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background-color: rgba(255,190,40,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.shield-icon {
  font-size: 56rpx;
  color: #FFBE28;
  font-weight: bold;
}

.header-title {
  font-size: 40rpx;
  font-weight: 600;
  color: #080808;
  margin-bottom: 8rpx;
}

.header-subtitle {
  font-size: 26rpx;
  color: #333333;
}

// ==================== 说明区域 ====================

.section {
  margin-bottom: 40rpx;
}

.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: 500;
  color: #080808;
  margin-bottom: 24rpx;
}

.info-list {
  background-color: #F8F8FA;
  border-radius: 30rpx;
  padding: 24rpx;
}

.info-item {
  display: flex;
  align-items: flex-start;
  padding: 16rpx 0;

  &:not(:last-child) {
    border-bottom: 1px solid #E0E0E0;
    padding-bottom: 24rpx;
    margin-bottom: 0;
  }
}

.info-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background-color: #01BEFF;
  margin-top: 8rpx;
  margin-right: 16rpx;
  flex-shrink: 0;

  &.dot-warning {
    background-color: #FFBE28;
  }
}

.info-text {
  font-size: 28rpx;
  color: #333333;
  line-height: 1.6;
  flex: 1;
}

// ==================== 温馨提示 ====================

.warm-tip {
  background-color: rgba(1,190,255,0.1);
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 60rpx;
}

.warm-tip-text {
  font-size: 26rpx;
  color: #01BEFF;
  line-height: 1.6;
  text-align: center;
}

// ==================== 底部按钮 ====================

.bottom-section {
  margin-top: auto;
  padding-bottom: calc(30rpx + env(safe-area-inset-bottom));
}
</style>

<style lang="scss">
// 全局样式覆盖，用于 wot-design-uni 组件样式
.minor-notice-page {
  --wd-button-primary-bg-color: #01BEFF;
  --wd-button-primary-border-color: #01BEFF;
}
</style>
