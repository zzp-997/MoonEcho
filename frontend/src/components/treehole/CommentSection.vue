<template>
  <view class="comment-section">
    <!-- 评论区标题 -->
    <view class="section-header">
      <text class="section-title">回声</text>
      <text class="section-hint">这里是树洞，不是建议箱</text>
    </view>

    <!-- 评论列表 -->
    <view v-if="comments.length > 0" class="comment-list">
      <view
        v-for="comment in comments"
        :key="comment.id"
        class="comment-item"
      >
        <view class="comment-content">
          <text class="comment-text">{{ comment.content }}</text>
          <text class="comment-time">{{ comment.fuzzy_time?.fuzzy_display || '' }}</text>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else class="empty-state">
      <text class="empty-text">暂无回声</text>
      <text class="empty-hint">做第一个传递温暖的人吧</text>
    </view>

    <!-- 评论输入区域 -->
    <view class="comment-input-area">
      <view class="input-wrapper">
        <input
          v-model="inputContent"
          class="comment-input"
          type="text"
          :maxlength="50"
          :placeholder="placeholder"
          placeholder-class="input-placeholder"
          @confirm="handleSubmit"
        />
        <text class="char-count">{{ inputContent.length }}/50</text>
      </view>
      <view
        class="submit-btn"
        :class="{ 'is-disabled': !canSubmit || isSubmitting }"
        @tap="handleSubmit"
      >
        <text class="submit-text">{{ isSubmitting ? '发送中' : '发送' }}</text>
      </view>
    </view>

    <!-- 提示语 -->
    <view class="section-footer">
      <text class="footer-hint">如果TA需要建议，TA会问的。</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 树洞评论区组件
 * 文件：src/components/treehole/CommentSection.vue
 * 说明：评论列表展示和评论输入，限制50字，保持树洞匿名性
 */

import { ref, computed } from 'vue'
import type { TreeholeComment } from '@/api/treehole'

// ==================== Props ====================

const props = defineProps<{
  comments: TreeholeComment[]
  postId: string
}>()

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'submit', content: string): void
}>()

// ==================== 响应式状态 ====================

/** 输入内容 */
const inputContent = ref('')

/** 是否正在提交 */
const isSubmitting = ref(false)

/** 占位符 */
const placeholder = '写点什么温暖TA...'

// ==================== 计算属性 ====================

/** 是否可以提交 */
const canSubmit = computed(() => {
  return inputContent.value.trim().length > 0 && inputContent.value.length <= 50
})

// ==================== 方法 ====================

/**
 * 处理提交评论
 */
async function handleSubmit(): Promise<void> {
  if (!canSubmit.value || isSubmitting.value) return

  const content = inputContent.value.trim()
  if (!content) return

  isSubmitting.value = true

  try {
    emit('submit', content)
    inputContent.value = ''
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.comment-section {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

// ==================== 标题 ====================

.section-header {
  display: flex;
  flex-direction: column;
  margin-bottom: var(--space-md);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.section-hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 评论列表 ====================

.comment-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.comment-item {
  display: flex;
  padding: var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.comment-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.comment-text {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  line-height: 1.5;
  word-break: break-word;
}

.comment-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg) 0;
  margin-bottom: var(--space-md);
}

.empty-text {
  font-size: var(--font-size-base);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 输入区域 ====================

.comment-input-area {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  position: relative;
}

.comment-input {
  flex: 1;
  height: 72rpx;
  padding: 0 var(--space-md);
  padding-right: 80rpx;
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.input-placeholder {
  color: var(--text-tertiary);
}

.char-count {
  position: absolute;
  right: var(--space-sm);
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 72rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-sm);

  &:active {
    opacity: 0.8;
  }

  &.is-disabled {
    background-color: var(--bg-tertiary);

    .submit-text {
      color: var(--text-tertiary);
    }
  }
}

.submit-text {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);
}

// ==================== 底部提示 ====================

.section-footer {
  display: flex;
  justify-content: center;
  padding-top: var(--space-sm);
  margin-top: var(--space-xs);
  border-top: 1px solid var(--border-primary);
}

.footer-hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  font-style: italic;
}
</style>
