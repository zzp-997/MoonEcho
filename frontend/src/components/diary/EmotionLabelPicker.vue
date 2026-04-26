<template>
  <view v-if="visible" class="emotion-label-picker">
    <!-- 标题 -->
    <view class="picker-header">
      <text class="header-text">选几个词形容一下</text>
      <text class="header-hint">最多3个</text>
    </view>

    <!-- 标签池 -->
    <view class="label-grid">
      <view
        v-for="label in labels"
        :key="label"
        class="label-item"
        :class="{ 'is-selected': isSelected(label) }"
        :style="getLabelStyle(label)"
        @tap="handleToggle(label)"
      >
        <text class="label-text" :style="getTextStyle(label)">{{ label }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 情绪标签选择器组件
 * 文件：src/components/diary/EmotionLabelPicker.vue
 * 说明：根据选中色调显示对应标签池，最多选3个，选中态高亮
 */

import { computed } from 'vue'
import { EMOTION_TONE_META, EMOTION_LABELS_POOL, type EmotionTone } from '@/api/diary'

// ==================== Props ====================

interface Props {
  /** 当前色调 */
  tone: EmotionTone | null
  /** 当前选中的标签列表 */
  modelValue?: string[]
  /** 可选标签列表（不传则使用默认标签池） */
  labels?: string[]
  /** 是否显示 */
  visible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  tone: null,
  modelValue: () => [],
  labels: () => [],
  visible: true,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 更新选中的标签 */
  (e: 'update:modelValue', value: string[]): void
}>()

// ==================== 计算属性 ====================

/** 标签列表 */
const labels = computed(() => {
  // 如果传入了自定义标签列表，使用自定义列表
  if (props.labels.length > 0) {
    return props.labels
  }
  // 否则根据当前色调从标签池获取
  if (props.tone) {
    return EMOTION_LABELS_POOL[props.tone] || []
  }
  return []
})

/** 当前色调颜色 */
const toneColor = computed(() => {
  if (!props.tone) return 'var(--brand-primary)'
  return EMOTION_TONE_META[props.tone].color
})

// ==================== 方法 ====================

/**
 * 判断标签是否选中
 */
function isSelected(label: string): boolean {
  return props.modelValue.includes(label)
}

/**
 * 获取标签样式
 */
function getLabelStyle(label: string): Record<string, string> {
  const selected = isSelected(label)
  return {
    backgroundColor: selected ? `${toneColor.value}20` : 'var(--bg-tertiary)',
    borderColor: selected ? toneColor.value : 'transparent',
  }
}

/**
 * 获取文字样式
 */
function getTextStyle(label: string): Record<string, string> {
  const selected = isSelected(label)
  return {
    color: selected ? toneColor.value : 'var(--text-secondary)',
  }
}

/**
 * 切换标签选择
 */
function handleToggle(label: string): void {
  const currentLabels = [...props.modelValue]
  const index = currentLabels.indexOf(label)

  if (index > -1) {
    // 取消选择
    currentLabels.splice(index, 1)
  } else {
    // 添加选择（最多3个）
    if (currentLabels.length < 3) {
      currentLabels.push(label)
    } else {
      // 已选满，不做任何操作（由 composable 层处理提示）
      return
    }
  }

  emit('update:modelValue', currentLabels)
}
</script>

<style lang="scss" scoped>
.emotion-label-picker {
  padding: var(--space-md);
}

// ==================== 标题 ====================

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.header-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.header-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 标签网格 ====================

.label-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.label-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  padding: 0 var(--space-md);
  border-radius: var(--radius-full);
  border-width: 2px;
  border-style: solid;
  transition: all var(--transition-fast) ease;

  &:active {
    transform: scale(0.95);
  }
}

.label-text {
  font-size: var(--font-size-sm);
  transition: color var(--transition-fast);
}
</style>
