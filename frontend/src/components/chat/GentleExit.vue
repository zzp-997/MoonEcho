<template>
  <view v-if="visible" class="gentle-exit-overlay" @tap="handleOverlayTap">
    <view class="exit-dialog" @tap.stop>
      <!-- 标题 -->
      <view class="dialog-header">
        <text class="dialog-title">温柔退出</text>
        <text class="dialog-subtitle">选择一个合适的方式结束对话吧</text>
      </view>

      <!-- 退出语列表 -->
      <view class="exit-list">
        <view
          v-for="(phrase, index) in exitPhrases"
          :key="index"
          class="exit-item"
          @tap="handleSelectPhrase(phrase)"
        >
          <text class="exit-text">{{ phrase }}</text>
          <text class="select-icon">✓</text>
        </view>
      </view>

      <!-- 自定义输入 -->
      <view class="custom-input">
        <textarea
          class="input-field"
          v-model="customPhrase"
          placeholder="或者自己写一句..."
          :maxlength="100"
          :auto-height="true"
        />
      </view>

      <!-- 操作按钮 -->
      <view class="dialog-actions">
        <view class="action-btn cancel" @tap="handleCancel">
          <text class="btn-text">取消</text>
        </view>
        <view class="action-btn confirm" @tap="handleConfirm">
          <text class="btn-text">使用这句话退出</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 温柔退出组件
 * 文件：src/components/chat/GentleExit.vue
 * 说明：AI辅助温柔退出对话，提供优雅的结束语建议
 */

import { ref, watch } from 'vue'

// ==================== Props ====================

interface Props {
  /** 是否显示 */
  visible: boolean
  /** 退出语建议列表 */
  exitPhrases?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  exitPhrases: () => [],
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 选择退出语 */
  (e: 'select', phrase: string): void
  /** 关闭弹窗 */
  (e: 'close'): void
}>()

// ==================== 响应式状态 ====================

/** 自定义退出语 */
const customPhrase = ref('')

/** 选中的退出语 */
const selectedPhrase = ref<string | null>(null)

// ==================== 监听器 ====================

watch(
  () => props.visible,
  (newVal) => {
    if (!newVal) {
      // 关闭时重置状态
      customPhrase.value = ''
      selectedPhrase.value = null
    }
  }
)

// ==================== 方法 ====================

/**
 * 选择退出语
 */
function handleSelectPhrase(phrase: string): void {
  selectedPhrase.value = phrase
  customPhrase.value = phrase
}

/**
 * 取消
 */
function handleCancel(): void {
  emit('close')
}

/**
 * 确认使用
 */
function handleConfirm(): void {
  const phrase = customPhrase.value.trim() || selectedPhrase.value
  if (phrase) {
    emit('select', phrase)
  }
}

/**
 * 点击遮罩层
 */
function handleOverlayTap(): void {
  emit('close')
}
</script>

<style lang="scss" scoped>
.gentle-exit-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--overlay-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.exit-dialog {
  width: 90%;
  max-width: 640rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

// ==================== 标题 ====================

.dialog-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-lg) var(--space-md) var(--space-md);
  border-bottom: 1rpx solid var(--border-primary);
}

.dialog-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.dialog-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 退出语列表 ====================

.exit-list {
  padding: var(--space-md);
}

.exit-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-xs);

  &:active {
    opacity: 0.9;
  }

  &.selected {
    background-color: var(--brand-light);
  }
}

.exit-text {
  flex: 1;
  font-size: var(--font-size-md);
  color: var(--text-primary);
  line-height: 1.5;
}

.select-icon {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
  margin-left: var(--space-sm);
}

// ==================== 自定义输入 ====================

.custom-input {
  padding: 0 var(--space-md) var(--space-md);
}

.input-field {
  width: 100%;
  min-height: 80rpx;
  padding: var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

// ==================== 操作按钮 ====================

.dialog-actions {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  border-top: 1rpx solid var(--border-primary);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.action-btn.cancel {
  background-color: var(--bg-tertiary);
  margin-right: var(--space-sm);
}

.action-btn.cancel .btn-text {
  color: var(--text-secondary);
}

.action-btn.confirm {
  background-color: var(--brand-primary);
}

.action-btn.confirm .btn-text {
  color: var(--text-on-brand);
}

.btn-text {
  font-size: var(--font-size-sm);
  font-weight: 500;
}
</style>