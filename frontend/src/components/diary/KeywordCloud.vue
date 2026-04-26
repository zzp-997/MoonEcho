<template>
  <view class="keyword-cloud">
    <!-- 关键词云标题 -->
    <view class="cloud-header">
      <text class="cloud-title">本周关键词</text>
    </view>

    <!-- 关键词云内容 -->
    <view class="cloud-content">
      <view
        v-for="(keyword, index) in processedKeywords"
        :key="index"
        class="keyword-item"
        :style="keyword.style"
        @tap="handleKeywordTap(keyword)"
      >
        <text class="keyword-text">{{ keyword.text }}</text>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-if="keywords.length === 0" class="empty-cloud">
      <text class="empty-text">暂无关键词数据</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 关键词云组件
 * 文件：src/components/diary/KeywordCloud.vue
 * 说明：纯 CSS 实现关键词云可视化，字体大小根据词频变化
 */

import { computed } from 'vue'
import { track, EventName } from '@/utils/tracking'

// ==================== Props ====================

interface KeywordItem {
  /** 关键词文本 */
  text: string
  /** 词频/权重（可选） */
  weight?: number
  /** 情绪色调（可选） */
  tone?: string
}

interface Props {
  /** 关键词列表 */
  keywords: string[] | KeywordItem[]
  /** 最大显示数量 */
  maxCount?: number
  /** 是否显示动画 */
  animated?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  keywords: () => [],
  maxCount: 8,
  animated: true,
})

// ==================== 情绪色调颜色映射 ====================

const toneColorMap: Record<string, string> = {
  warm_orange: 'var(--mood-warm)',
  light_green: 'var(--mood-calm)',
  gray_blue: 'var(--mood-low)',
  deep_blue: 'var(--mood-sad)',
  dark_purple: 'var(--mood-chaos)',
}

// ==================== 计算属性 ====================

/**
 * 处理后的关键词列表
 * 包含样式计算（字体大小、颜色等）
 */
const processedKeywords = computed(() => {
  // 限制显示数量
  const limitedKeywords = props.keywords.slice(0, props.maxCount)

  // 标准化关键词数据
  const normalizedKeywords = limitedKeywords.map((kw) => {
    if (typeof kw === 'string') {
      return { text: kw, weight: 1, tone: undefined }
    }
    return {
      text: kw.text,
      weight: kw.weight || 1,
      tone: kw.tone || undefined,
    }
  })

  // 计算权重范围
  const weights = normalizedKeywords.map((kw) => kw.weight)
  const minWeight = Math.min(...weights)
  const maxWeight = Math.max(...weights)
  const weightRange = maxWeight - minWeight || 1

  // 为每个关键词生成样式
  return normalizedKeywords.map((kw, index) => {
    // 计算字体大小（基于权重）
    // 最小字体 14px，最大字体 22px
    const normalizedWeight = (kw.weight - minWeight) / weightRange
    const fontSize = 14 + normalizedWeight * 8

    // 确定颜色
    const color = kw.tone && toneColorMap[kw.tone]
      ? toneColorMap[kw.tone]
      : 'var(--text-primary)'

    // 动画延迟
    const animationDelay = props.animated ? index * 0.05 : 0

    return {
      text: kw.text,
      weight: kw.weight,
      tone: kw.tone,
      style: {
        fontSize: `${fontSize}px`,
        color,
        animationDelay: `${animationDelay}s`,
      },
    }
  })
})

// ==================== 方法 ====================

/**
 * 处理关键词点击
 */
function handleKeywordTap(keyword: { text: string; weight?: number; tone?: string | null }) {
  track(EventName.DIARY_LIST_VIEW, {
    action: 'keyword_tap',
    keyword: keyword.text,
    tone: keyword.tone,
  })

  // 可以扩展为跳转到相关日记列表
  console.log('关键词点击:', keyword.text)
}
</script>

<style lang="scss" scoped>
.keyword-cloud {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

// ==================== 标题 ====================

.cloud-header {
  margin-bottom: var(--space-md);
}

.cloud-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

// ==================== 关键词云内容 ====================

.cloud-content {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
  justify-content: center;
  min-height: 60rpx;
}

.keyword-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);

  &:active {
    opacity: 0.7;
    transform: scale(0.95);
  }

  // 入场动画
  animation: fadeInScale 0.3s ease-out forwards;
  opacity: 0;
}

.keyword-text {
  font-weight: 500;
  line-height: 1.2;
}

// ==================== 入场动画 ====================

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

// ==================== 空状态 ====================

.empty-cloud {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) 0;
}

.empty-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}
</style>