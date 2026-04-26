<template>
  <scroll-view class="topic-filter" scroll-x :scroll-left="scrollLeft" scroll-with-animation>
    <view class="filter-content">
      <!-- 全部选项 -->
      <view
        class="filter-item"
        :class="{ 'is-active': !selectedTag }"
        @tap="handleSelect(null)"
      >
        <text class="filter-text">全部</text>
      </view>
      <!-- 话题标签列表 -->
      <view
        v-for="topic in topics"
        :key="topic.value"
        class="filter-item"
        :class="{ 'is-active': selectedTag === topic.value }"
        @tap="handleSelect(topic.value)"
      >
        <text class="filter-text">#{{ topic.label }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
/**
 * 回声 - 树洞话题标签筛选组件
 * 文件：src/components/treehole/TopicFilter.vue
 * 说明：水平滚动的话题标签筛选条，支持选择话题进行内容筛选
 */

import { ref, watch, onMounted } from 'vue'
import { getTopicTags, TOPIC_TAG_LABELS, type TopicResponse } from '@/api/treehole'

// ==================== Props ====================

const props = defineProps<{
  selectedTag?: string | null
}>()

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'change', tag: string | null): void
}>()

// ==================== 响应式状态 ====================

/** 话题列表 */
const topics = ref<TopicResponse[]>([])

/** 滚动位置 */
const scrollLeft = ref(0)

// ==================== 方法 ====================

/**
 * 加载话题标签列表
 */
async function loadTopics(): Promise<void> {
  try {
    // 先使用本地预设的标签
    topics.value = Object.entries(TOPIC_TAG_LABELS).map(([value, label]) => ({
      value,
      label,
    }))
  } catch (error) {
    console.error('加载话题标签失败', error)
    // 使用本地预设的标签作为后备
    topics.value = Object.entries(TOPIC_TAG_LABELS).map(([value, label]) => ({
      value,
      label,
    }))
  }
}

/**
 * 处理话题选择
 */
function handleSelect(tag: string | null): void {
  emit('change', tag)
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadTopics()
})
</script>

<style lang="scss" scoped>
.topic-filter {
  width: 100%;
  white-space: nowrap;
  padding: var(--space-sm) 0;
  margin-bottom: var(--space-sm);
}

.filter-content {
  display: inline-flex;
  gap: var(--space-sm);
  padding: 0 var(--space-md);
}

.filter-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  padding: 0 var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);

  &:active {
    opacity: 0.8;
  }

  &.is-active {
    background-color: var(--brand-primary);

    .filter-text {
      color: var(--text-on-brand);
    }
  }
}

.filter-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  white-space: nowrap;
}
</style>
