<template>
  <view class="ai-assist-hint">
    <!-- 冷场提示 -->
    <view v-if="type === 'awkward'" class="hint-card awkward-hint">
      <view class="hint-header">
        <view class="hint-icon-wrapper">
          <text class="hint-icon-text">静</text>
        </view>
        <text class="hint-title">好像有点安静...</text>
      </view>
      <view class="hint-content">
        <text class="hint-text">不知道聊什么？让AI帮你想想话题</text>
      </view>
      <view class="hint-actions">
        <view class="action-btn primary" @tap="handleGenerateTopic">
          <text class="btn-text">AI帮我想想话题</text>
        </view>
        <view class="action-btn secondary" @tap="handleDismiss">
          <text class="btn-text">不用了</text>
        </view>
      </view>
    </view>

    <!-- 回复建议 -->
    <view v-else-if="type === 'reply'" class="hint-card reply-hint">
      <view class="hint-header">
        <view class="hint-icon-wrapper">
          <text class="hint-icon-text">!</text>
        </view>
        <text class="hint-title">试试这些回复？</text>
      </view>
      <view class="suggestions-list">
        <view
          v-for="(suggestion, index) in suggestions"
          :key="index"
          class="suggestion-item"
          @tap="handleSelectSuggestion(suggestion)"
        >
          <text class="suggestion-text">{{ suggestion }}</text>
        </view>
      </view>
      <view class="hint-footer">
        <view class="refresh-btn" @tap="handleRefresh">
          <text class="refresh-icon">↻</text>
          <text class="refresh-text">换一批</text>
        </view>
        <view class="close-btn" @tap="handleDismiss">
          <text class="close-text">关闭</text>
        </view>
      </view>
    </view>

    <!-- 话题建议 -->
    <view v-else-if="type === 'topic'" class="hint-card topic-hint">
      <view class="hint-header">
        <view class="hint-icon-wrapper">
          <text class="hint-icon-text">聊</text>
        </view>
        <text class="hint-title">可以聊聊这些话题</text>
      </view>
      <view class="suggestions-list">
        <view
          v-for="(topic, index) in suggestions"
          :key="index"
          class="suggestion-item"
          @tap="handleSelectSuggestion(topic)"
        >
          <text class="suggestion-text">{{ topic }}</text>
        </view>
      </view>
      <view class="hint-footer">
        <view class="refresh-btn" @tap="handleRefresh">
          <text class="refresh-icon">↻</text>
          <text class="refresh-text">换一批</text>
        </view>
        <view class="close-btn" @tap="handleDismiss">
          <text class="close-text">关闭</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - AI 辅助提示组件
 * 文件：src/components/chat/AIAssistHint.vue
 * 说明：AI聊天辅助提示，包括冷场提示、回复建议、话题建议
 */

import { computed } from 'vue'

// ==================== Props ====================

interface Props {
  /** 提示类型 */
  type: 'awkward' | 'reply' | 'topic'
  /** 建议列表 */
  suggestions?: string[]
  /** 是否正在加载 */
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  suggestions: () => [],
  loading: false,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 选择建议 */
  (e: 'select', suggestion: string): void
  /** 刷新建议 */
  (e: 'refresh'): void
  /** 关闭提示 */
  (e: 'dismiss'): void
  /** 生成话题 */
  (e: 'generate-topic'): void
}>()

// ==================== 方法 ====================

/**
 * 选择建议
 */
function handleSelectSuggestion(suggestion: string): void {
  emit('select', suggestion)
}

/**
 * 刷新建议
 */
function handleRefresh(): void {
  emit('refresh')
}

/**
 * 关闭提示
 */
function handleDismiss(): void {
  emit('dismiss')
}

/**
 * 生成话题
 */
function handleGenerateTopic(): void {
  emit('generate-topic')
}
</script>

<style lang="scss" scoped>
.ai-assist-hint {
  margin: var(--space-sm) var(--space-md);
}

.hint-card {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  border: 1rpx solid var(--border-primary);
}

// ==================== 头部 ====================

.hint-header {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.hint-icon {
  font-size: var(--font-size-md);
  margin-right: var(--space-xs);
}

.hint-icon-wrapper {
  width: 36rpx;
  height: 36rpx;
  border-radius: var(--radius-xs);
  background-color: var(--brand-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-xs);
}

.hint-icon-text {
  font-size: 18rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.hint-title {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  font-weight: 500;
}

// ==================== 内容 ====================

.hint-content {
  margin-bottom: var(--space-md);
}

.hint-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 建议列表 ====================

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
}

.suggestion-item {
  padding: var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);

  &:active {
    opacity: 0.9;
    background-color: var(--brand-primary);
  }
}

.suggestion-text {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  line-height: 1.5;
}

// ==================== 操作按钮 ====================

.hint-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.action-btn.primary {
  background-color: var(--brand-primary);
}

.action-btn.primary .btn-text {
  color: var(--text-on-brand);
}

.action-btn.secondary {
  background-color: var(--bg-tertiary);
}

.action-btn.secondary .btn-text {
  color: var(--text-secondary);
}

.btn-text {
  font-size: var(--font-size-sm);
}

// ==================== 底部 ====================

.hint-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.refresh-btn,
.close-btn {
  display: flex;
  align-items: center;

  &:active {
    opacity: 0.8;
  }
}

.refresh-icon {
  font-size: var(--font-size-sm);
  margin-right: 8rpx;
}

.refresh-text {
  font-size: var(--font-size-xs);
  color: var(--brand-light);
}

.close-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}
</style>