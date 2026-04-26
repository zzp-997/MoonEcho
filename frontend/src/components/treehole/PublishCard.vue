<template>
  <view class="publish-card">
    <!-- 折叠状态：引导发布 -->
    <view v-if="!isExpanded" class="card-collapsed" @tap="handleExpand">
      <view class="icon-wrapper">
        <text class="icon">🌱</text>
      </view>
      <view class="prompt-content">
        <text class="prompt-title">新来的？</text>
        <text class="prompt-hint">点击把心里话说出来</text>
      </view>
      <view class="expand-arrow">
        <text class="arrow-icon">+</text>
      </view>
    </view>

    <!-- 展开状态：发布输入 -->
    <view v-else class="card-expanded">
      <view class="expanded-header">
        <text class="header-title">匿名发布</text>
        <view class="close-btn" @tap="handleCollapse">
          <text class="close-icon">-</text>
        </view>
      </view>

      <view class="input-area">
        <textarea
          v-model="content"
          class="content-input"
          :maxlength="500"
          :placeholder="placeholder"
          placeholder-class="input-placeholder"
          :auto-height="true"
          :show-confirm-bar="false"
          :adjust-position="true"
          @input="handleInput"
        />
        <text class="char-count">{{ content.length }}/500</text>
      </view>

      <!-- 话题标签选择 -->
      <scroll-view class="topic-scroll" scroll-x>
        <view class="topic-list">
          <view
            v-for="topic in topics"
            :key="topic.value"
            class="topic-item"
            :class="{ 'is-active': selectedTopic === topic.value }"
            @tap="handleTopicSelect(topic.value)"
          >
            <text class="topic-text">#{{ topic.label }}</text>
          </view>
        </view>
      </scroll-view>

      <!-- 底部操作区 -->
      <view class="action-bar">
        <view class="left-actions">
          <view class="ai-rewrite-btn" @tap="handleAiRewrite">
            <text class="btn-icon">✨</text>
            <text class="btn-text">AI润色</text>
          </view>
        </view>
        <view class="right-actions">
          <view
            class="publish-btn"
            :class="{ 'is-disabled': !canPublish || isSubmitting }"
            @tap="handlePublish"
          >
            <text class="publish-text">{{ isSubmitting ? '发布中...' : '发布' }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 树洞新用户引导发布卡片组件
 * 文件：src/components/treehole/PublishCard.vue
 * 说明：信息流顶部引导卡片，点击就地展开输入框，降低首次发布摩擦
 */

import { ref, computed, onMounted } from 'vue'
import { TOPIC_TAG_LABELS, type TopicResponse } from '@/api/treehole'

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'publish', data: { content: string; topicTag: string | null }): void
  (e: 'ai-rewrite', content: string): void
}>()

// ==================== 响应式状态 ====================

/** 是否展开 */
const isExpanded = ref(false)

/** 输入内容 */
const content = ref('')

/** 选中的话题标签 */
const selectedTopic = ref<string | null>(null)

/** 话题列表 */
const topics = ref<TopicResponse[]>([])

/** 是否正在提交 */
const isSubmitting = ref(false)

/** 占位符 */
const placeholder = '今天想吐槽什么？'

// ==================== 计算属性 ====================

/** 是否可以发布 */
const canPublish = computed(() => {
  return content.value.trim().length > 0 && content.value.length <= 500
})

// ==================== 方法 ====================

/**
 * 加载话题列表
 */
function loadTopics(): void {
  topics.value = Object.entries(TOPIC_TAG_LABELS).map(([value, label]) => ({
    value,
    label,
  }))
}

/**
 * 处理展开
 */
function handleExpand(): void {
  isExpanded.value = true
}

/**
 * 处理折叠
 */
function handleCollapse(): void {
  isExpanded.value = false
  content.value = ''
  selectedTopic.value = null
}

/**
 * 处理输入
 */
function handleInput(): void {
  // 输入处理逻辑（如有需要）
}

/**
 * 处理话题选择
 */
function handleTopicSelect(topic: string): void {
  selectedTopic.value = selectedTopic.value === topic ? null : topic
}

/**
 * 处理AI润色
 */
function handleAiRewrite(): void {
  if (!content.value.trim()) return
  emit('ai-rewrite', content.value.trim())
}

/**
 * 处理发布
 */
async function handlePublish(): Promise<void> {
  if (!canPublish.value || isSubmitting.value) return

  const publishContent = content.value.trim()
  if (!publishContent) return

  isSubmitting.value = true

  try {
    emit('publish', {
      content: publishContent,
      topicTag: selectedTopic.value,
    })
    // 发布成功后折叠
    handleCollapse()
  } finally {
    isSubmitting.value = false
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadTopics()
})
</script>

<style lang="scss" scoped>
.publish-card {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-md);
  overflow: hidden;
}

// ==================== 折叠状态 ====================

.card-collapsed {
  display: flex;
  align-items: center;
  padding: var(--space-lg);

  &:active {
    opacity: 0.9;
  }
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  margin-right: var(--space-md);
  background-color: var(--brand-primary);
  background-color: rgba(124, 111, 224, 0.15);
  border-radius: 50%;
}

.icon {
  font-size: var(--font-size-xl);
}

.prompt-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.prompt-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.prompt-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.expand-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  background-color: var(--bg-tertiary);
  border-radius: 50%;
}

.arrow-icon {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
}

// ==================== 展开状态 ====================

.card-expanded {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
}

.expanded-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.header-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  background-color: var(--bg-tertiary);
  border-radius: 50%;

  &:active {
    opacity: 0.8;
  }
}

.close-icon {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
}

// ==================== 输入区域 ====================

.input-area {
  position: relative;
  margin-bottom: var(--space-sm);
}

.content-input {
  width: 100%;
  min-height: 200rpx;
  padding: var(--space-md);
  padding-bottom: var(--space-xl);
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  line-height: 1.6;
}

.input-placeholder {
  color: var(--text-tertiary);
}

.char-count {
  position: absolute;
  right: var(--space-sm);
  bottom: var(--space-sm);
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 话题选择 ====================

.topic-scroll {
  margin-bottom: var(--space-md);
}

.topic-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.topic-item {
  display: inline-flex;
  align-items: center;
  height: 56rpx;
  padding: 0 var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);

  &:active {
    opacity: 0.8;
  }

  &.is-active {
    background-color: var(--brand-primary);

    .topic-text {
      color: var(--text-on-brand);
    }
  }
}

.topic-text {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  white-space: nowrap;
}

// ==================== 操作栏 ====================

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.left-actions {
  display: flex;
  align-items: center;
}

.ai-rewrite-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);

  &:active {
    opacity: 0.8;
  }
}

.btn-icon {
  font-size: var(--font-size-sm);
}

.btn-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.publish-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 160rpx;
  height: 72rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }

  &.is-disabled {
    background-color: var(--bg-tertiary);

    .publish-text {
      color: var(--text-tertiary);
    }
  }
}

.publish-text {
  font-size: var(--font-size-base);
  color: var(--text-on-brand);
  font-weight: 500;
}
</style>
