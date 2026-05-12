<template>
  <!-- 危机干预弹窗 -->
  <view v-if="visible" class="crisis-dialog-overlay" @tap.stop.prevent>
    <view class="crisis-dialog" @tap.stop>
      <!-- 图标 -->
      <view class="dialog-icon">
        <view class="heart-icon-wrapper">
          <text class="heart-icon-text">♥</text>
        </view>
      </view>

      <!-- 标题 -->
      <view class="dialog-title">
        <text class="title-text">{{ title }}</text>
      </view>

      <!-- 安慰语 -->
      <view class="dialog-message">
        <text class="message-text">{{ message }}</text>
      </view>

      <!-- 热线列表 -->
      <view class="hotline-list">
        <view
          v-for="hotline in hotlines"
          :key="hotline.number"
          class="hotline-item"
          @tap="callHotline(hotline.number)"
        >
          <view class="hotline-info">
            <text class="hotline-name">{{ hotline.name }}</text>
            <text class="hotline-desc">{{ hotline.description }}</text>
          </view>
          <view class="hotline-number">
            <text class="number-text">{{ hotline.number }}</text>
            <text class="call-icon">📞</text>
          </view>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="dialog-actions">
        <view class="action-btn secondary" @tap="handleClose">
          <text class="btn-text">我知道了</text>
        </view>
        <view class="action-btn primary" @tap="handleConfirm">
          <text class="btn-text">我会寻求帮助</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 危机干预弹窗组件
 * 文件：src/components/chat/CrisisDialog.vue
 * 说明：检测到自伤关键词时显示，包含安慰语和求助热线
 */

import { computed } from 'vue'
import { CRISIS_HOTLINES } from '@/composables/useCrisis'

// ==================== Props ====================

interface Props {
  /** 是否显示弹窗 */
  visible: boolean
  /** 危机等级 */
  level?: 'medium' | 'high'
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  level: 'medium',
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 关闭弹窗 */
  (e: 'close'): void
  /** 确认会寻求帮助 */
  (e: 'confirm'): void
}>()

// ==================== 计算属性 ====================

/** 热线列表 */
const hotlines = CRISIS_HOTLINES

/** 标题文案 */
const title = computed(() => {
  return props.level === 'high' ? '我们很在乎你' : '我在乎你'
})

/** 安慰语文案 */
const message = computed(() => {
  if (props.level === 'high') {
    return '我感受到了你现在的情绪，请相信，你值得被关爱。如果你愿意，请拨打下面的热线，专业的倾听者能帮助你度过这个时刻。'
  }
  return '每个人都有困难的时候，寻求帮助是勇敢的表现。如果你愿意，可以和信任的人聊聊，或者拨打下面的热线电话。'
})

// ==================== 方法 ====================

/**
 * 拨打热线电话
 */
function callHotline(number: string): void {
  uni.makePhoneCall({
    phoneNumber: number,
    success: () => {
      // 追踪拨打成功
    },
    fail: () => {
      // 拨打失败，复制号码
      uni.setClipboardData({
        data: number,
        success: () => {
          uni.showToast({
            title: '号码已复制',
            icon: 'success',
          })
        },
      })
    },
  })
}

/**
 * 关闭弹窗
 */
function handleClose(): void {
  emit('close')
}

/**
 * 确认会寻求帮助
 */
function handleConfirm(): void {
  emit('confirm')
}
</script>

<style lang="scss" scoped>
.crisis-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-modal);
  background-color: var(--overlay-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
}

.crisis-dialog {
  width: 100%;
  max-width: 600rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-xl);
  padding: var(--space-xl) var(--space-lg);
  box-shadow: var(--shadow-lg);
}

// ==================== 图标 ====================

.dialog-icon {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-md);
}

.heart-icon-wrapper {
  width: 100rpx;
  height: 100rpx;
  border-radius: var(--radius-full);
  background-color: var(--ai-xiaowen-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.heart-icon-text {
  font-size: 48rpx;
  color: var(--ai-xiaowen);
}

// ==================== 标题与消息 ====================

.dialog-title {
  text-align: center;
  margin-bottom: var(--space-md);
}

.title-text {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.dialog-message {
  text-align: center;
  margin-bottom: var(--space-xl);
  padding: 0 var(--space-sm);
}

.message-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  line-height: 1.8;
}

// ==================== 热线列表 ====================

.hotline-list {
  margin-bottom: var(--space-xl);
}

.hotline-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-sm);

  &:last-child {
    margin-bottom: 0;
  }

  &:active {
    background-color: var(--bg-primary);
  }
}

.hotline-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.hotline-name {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.hotline-desc {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.hotline-number {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.number-text {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--brand-primary);
}

.call-icon {
  font-size: 32rpx;
}

// ==================== 操作按钮 ====================

.dialog-actions {
  display: flex;
  gap: var(--space-md);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: var(--radius-lg);

  &:active {
    opacity: 0.8;
  }

  &.primary {
    background-color: var(--brand-primary);

    .btn-text {
      color: var(--text-on-brand);
    }
  }

  &.secondary {
    background-color: var(--bg-tertiary);

    .btn-text {
      color: var(--text-secondary);
    }
  }
}

.btn-text {
  font-size: var(--font-size-md);
  font-weight: 500;
}

// ==================== 动画 ====================

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}
</style>
