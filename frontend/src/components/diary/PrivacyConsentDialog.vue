
<template>
  <!-- 隐私声明弹窗 -->
  <view v-if="visible" class="privacy-dialog-overlay" @tap.stop.prevent>
    <view class="privacy-dialog" @tap.stop>
      <!-- 图标 -->
      <view class="dialog-icon">
        <text class="icon-lock">🔒</text>
      </view>

      <!-- 标题 -->
      <view class="dialog-title">
        <text class="title-text">你的日记是私密的</text>
      </view>

      <!-- 说明 -->
      <view class="dialog-message">
        <text class="message-text">
          你的情绪日记只有你自己能看到。我们绝不会在未经你允许的情况下，向任何人展示你的日记内容。
        </text>
      </view>

      <!-- 分隔线 -->
      <view class="dialog-divider" />

      <!-- 同步选项 -->
      <view class="sync-options">
        <!-- 仅本设备 -->
        <view
          class="sync-option"
          :class="{ 'is-selected': localSyncMode === 'local_only' }"
          @tap="selectSyncMode('local_only')"
        >
          <view class="option-icon">
            <text class="icon-device">📱</text>
          </view>
          <view class="option-content">
            <text class="option-title">仅存本设备</text>
            <text class="option-desc">日记仅保存在当前设备</text>
          </view>
          <view class="option-check">
            <view
              v-if="localSyncMode === 'local_only'"
              class="check-dot is-active"
            >
              <text class="check-icon">✓</text>
            </view>
            <view v-else class="check-dot" />
          </view>
        </view>

        <!-- 云端同步 -->
        <view
          class="sync-option"
          :class="{ 'is-selected': localSyncMode === 'cloud_sync' }"
          @tap="selectSyncMode('cloud_sync')"
        >
          <view class="option-icon">
            <text class="icon-cloud-text">云</text>
          </view>
          <view class="option-content">
            <text class="option-title">开启云端同步</text>
            <text class="option-desc">换设备也能看到日记</text>
          </view>
          <view class="option-check">
            <view
              v-if="localSyncMode === 'cloud_sync'"
              class="check-dot is-active"
            >
              <text class="check-icon">✓</text>
            </view>
            <view v-else class="check-dot" />
          </view>
        </view>
      </view>

      <!-- 确认按钮 -->
      <view class="dialog-actions">
        <view class="confirm-btn" @tap="handleConfirm">
          <text class="btn-text">我明白了</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 隐私声明弹窗组件
 * 文件：src/components/diary/PrivacyConsentDialog.vue
 * 说明：首次进入日记页时显示，说明隐私政策并选择同步模式
 */

import { ref, watch } from 'vue'
import type { SyncMode } from '@/api/diary'

// ==================== Props ====================

interface Props {
  /** 是否显示弹窗 */
  visible: boolean
  /** 默认同步模式 */
  defaultSyncMode?: SyncMode
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  defaultSyncMode: 'local_only',
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 关闭弹窗 */
  (e: 'close'): void
  /** 确认同意，传递同步模式 */
  (e: 'confirm', mode: SyncMode): void
}>()

// ==================== 响应式状态 ====================

/** 本地同步模式状态 */
const localSyncMode = ref<SyncMode>(props.defaultSyncMode)

// ==================== 监听 ====================

watch(
  () => props.defaultSyncMode,
  (mode) => {
    localSyncMode.value = mode
  }
)

// ==================== 方法 ====================

/**
 * 选择同步模式
 */
function selectSyncMode(mode: SyncMode): void {
  localSyncMode.value = mode
}

/**
 * 确认同意
 */
function handleConfirm(): void {
  emit('confirm', localSyncMode.value)
}
</script>

<style lang="scss" scoped>
.privacy-dialog-overlay {
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

.privacy-dialog {
  width: 100%;
  max-width: 640rpx;
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

.icon-lock {
  font-size: 80rpx;
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
  margin-bottom: var(--space-lg);
  padding: 0 var(--space-sm);
}

.message-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  line-height: 1.8;
}

// ==================== 分隔线 ====================

.dialog-divider {
  height: 1px;
  background-color: var(--border-primary);
  margin-bottom: var(--space-lg);
}

// ==================== 同步选项 ====================

.sync-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.sync-option {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  border: 2px solid transparent;
  transition: all var(--transition-fast) ease;

  &:active {
    background-color: var(--bg-primary);
  }

  &.is-selected {
    border-color: var(--brand-primary);
    background-color: var(--brand-light);
  }
}

.option-icon {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-right: var(--space-md);
}

.icon-device,
.icon-cloud-text {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-secondary);
}

.option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.option-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.option-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.option-check {
  display: flex;
  align-items: center;
  justify-content: center;
}

.check-dot {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 2px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: center;

  &.is-active {
    background-color: var(--brand-primary);
    border-color: var(--brand-primary);
  }
}

.check-icon {
  font-size: 24rpx;
  color: var(--text-on-brand);
  font-weight: bold;
}

// ==================== 确认按钮 ====================

.dialog-actions {
  display: flex;
  gap: var(--space-md);
}

.confirm-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: var(--radius-lg);
  background-color: var(--brand-primary);

  &:active {
    opacity: 0.8;
  }
}

.btn-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-on-brand);
}
</style>
