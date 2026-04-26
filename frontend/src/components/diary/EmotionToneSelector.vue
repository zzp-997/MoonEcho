<template>
  <view class="emotion-tone-selector">
    <!-- 标题 -->
    <view class="selector-title">
      <text class="title-text">今天感觉怎样？</text>
    </view>

    <!-- 色调选择器 -->
    <view class="tone-list">
      <view
        v-for="tone in toneList"
        :key="tone"
        class="tone-item"
        :class="{ 'is-selected': selectedTone === tone }"
        :style="getToneStyle(tone)"
        @tap="handleSelect(tone)"
      >
        <!-- 色调圆形 -->
        <view
          class="tone-circle"
          :style="{ backgroundColor: getToneColor(tone) }"
        />
      </view>
    </view>

    <!-- 代表语显示 -->
    <view class="tone-phrase">
      <text
        class="phrase-text"
        :style="{ color: selectedTone ? getToneColor(selectedTone) : 'var(--text-tertiary)' }"
      >
        {{ currentPhrase }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 情绪色调选择器组件
 * 文件：src/components/diary/EmotionToneSelector.vue
 * 说明：5个圆形色块横向排列，未选中灰色边框，选中品牌色边框+半透明填充+放大动画
 */

import { computed } from 'vue'
import {
  EMOTION_TONE_META,
  EMOTION_TONE_LIST,
  type EmotionTone,
} from '@/api/diary'

// ==================== Props ====================

interface Props {
  /** 当前选中的色调 */
  modelValue?: EmotionTone | null
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 更新选中的色调 */
  (e: 'update:modelValue', value: EmotionTone | null): void
  /** 色调选择变化 */
  (e: 'change', value: EmotionTone): void
}>()

// ==================== 响应式状态 ====================

/** 当前选中的色调 */
const selectedTone = computed(() => props.modelValue)

/** 色调列表 */
const toneList = EMOTION_TONE_LIST

// ==================== 计算属性 ====================

/** 当前代表语文案 */
const currentPhrase = computed(() => {
  if (!selectedTone.value) {
    return '点击选择心情'
  }
  return EMOTION_TONE_META[selectedTone.value].phrase
})

// ==================== 方法 ====================

/**
 * 获取色调颜色
 */
function getToneColor(tone: EmotionTone): string {
  return EMOTION_TONE_META[tone].color
}

/**
 * 获取色调样式
 */
function getToneStyle(tone: EmotionTone): Record<string, string> {
  const isSelected = selectedTone.value === tone
  const color = getToneColor(tone)

  return {
    borderColor: isSelected ? color : 'var(--border-primary)',
    backgroundColor: isSelected ? `${color}20` : 'transparent',
    transform: isSelected ? 'scale(1.05)' : 'scale(1)',
  }
}

/**
 * 处理色调选择
 */
function handleSelect(tone: EmotionTone): void {
  const newTone = selectedTone.value === tone ? null : tone
  emit('update:modelValue', newTone)
  if (newTone) {
    emit('change', newTone)
  }
}
</script>

<style lang="scss" scoped>
.emotion-tone-selector {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-lg) var(--space-md);
}

// ==================== 标题 ====================

.selector-title {
  margin-bottom: var(--space-lg);
}

.title-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

// ==================== 色调列表 ====================

.tone-list {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  width: 100%;
}

.tone-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  border-width: 3px;
  border-style: solid;
  transition: all var(--transition-base) ease;

  &:active {
    transform: scale(0.95);
  }
}

.tone-circle {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
}

// ==================== 代表语 ====================

.tone-phrase {
  margin-top: var(--space-lg);
  min-height: 48rpx;
}

.phrase-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  transition: color var(--transition-base);
}
</style>
