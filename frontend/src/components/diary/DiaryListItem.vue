<template>
  <view
    class="diary-list-item"
    :class="{ 'is-swiping': isSwiping }"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
  >
    <!-- 内容区域 -->
    <view
      class="item-content"
      :style="{ transform: `translateX(${translateX}px)` }"
      @tap="handleTap"
    >
      <!-- 情绪色调条 -->
      <view
        class="emotion-bar"
        :style="{ backgroundColor: emotionColor }"
      />

      <!-- 日期和标签 -->
      <view class="item-header">
        <view class="date-area">
          <text class="date-text">{{ formattedDate }}</text>
          <text v-if="diary.is_zero_record" class="zero-badge">0字记录</text>
        </view>

        <!-- 情绪标签 -->
        <view v-if="diary.emotion_labels && diary.emotion_labels.length > 0" class="labels-area">
          <view
            v-for="label in displayLabels"
            :key="label"
            class="emotion-tag"
            :class="emotionTagClass"
          >
            <text class="tag-text">{{ label }}</text>
          </view>
          <text v-if="moreLabelsCount > 0" class="more-labels">+{{ moreLabelsCount }}</text>
        </view>
      </view>

      <!-- 内容预览 -->
      <view class="item-body">
        <text class="preview-text">
          {{ contentPreview }}
        </text>
      </view>

      <!-- 情绪色调名称 -->
      <view class="item-footer">
        <text class="emotion-text" :style="{ color: emotionColor }">
          {{ emotionMeaning }}
        </text>
        <text class="time-text">{{ formattedTime }}</text>
      </view>
    </view>

    <!-- 删除按钮（滑动显示） -->
    <view class="delete-action" :style="{ opacity: deleteActionOpacity }">
      <view class="delete-btn" @tap="handleDelete">
        <text class="delete-icon">删除</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 日记列表项组件
 * 文件：src/components/diary/DiaryListItem.vue
 * 说明：显示日期、情绪色调、标签、内容预览，支持滑动删除
 */

import { ref, computed } from 'vue'
import {
  EMOTION_TONE_META,
  type DiaryResponse,
  type EmotionTone,
} from '@/api/diary'

// ==================== Props ====================

interface Props {
  /** 日记数据 */
  diary: DiaryResponse
  /** 是否显示删除按钮 */
  showDelete?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showDelete: true,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 点击项 */
  (e: 'tap', diary: DiaryResponse): void
  /** 删除请求 */
  (e: 'delete', diary: DiaryResponse): void
}>()

// ==================== 响应式状态 ====================

/** 滑动偏移量 */
const translateX = ref(0)

/** 是否正在滑动 */
const isSwiping = ref(false)

/** 触摸开始位置 */
const touchStartX = ref(0)

/** 删除按钮宽度 */
const DELETE_WIDTH = 80

// ==================== 计算属性 ====================

/** 情绪色调颜色 */
const emotionColor = computed(() => {
  if (!props.diary.emotion_tone) return '#808080'
  return EMOTION_TONE_META[props.diary.emotion_tone].color
})

/** 情绪色调含义 */
const emotionMeaning = computed(() => {
  if (!props.diary.emotion_tone) return '未记录'
  return EMOTION_TONE_META[props.diary.emotion_tone].meaning
})

/** 情绪标签样式类 */
const emotionTagClass = computed(() => {
  if (!props.diary.emotion_tone) return ''
  const toneMap: Record<EmotionTone, string> = {
    warm_orange: 'emotion-tag--warm',
    light_green: 'emotion-tag--calm',
    gray_blue: 'emotion-tag--low',
    deep_blue: 'emotion-tag--sad',
    dark_purple: 'emotion-tag--chaos',
  }
  return toneMap[props.diary.emotion_tone]
})

/** 格式化日期 */
const formattedDate = computed(() => {
  const date = new Date(props.diary.record_date)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const weekday = weekdays[date.getDay()]
  return `${month}月${day}日 ${weekday}`
})

/** 格式化时间 */
const formattedTime = computed(() => {
  const date = new Date(props.diary.created_at)
  const hours = date.getHours()
  const minutes = date.getMinutes()
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
})

/** 显示的标签（最多2个） */
const displayLabels = computed(() => {
  if (!props.diary.emotion_labels) return []
  return props.diary.emotion_labels.slice(0, 2)
})

/** 更多标签数量 */
const moreLabelsCount = computed(() => {
  if (!props.diary.emotion_labels) return 0
  return props.diary.emotion_labels.length - 2
})

/** 内容预览（最多50字） */
const contentPreview = computed(() => {
  if (!props.diary.content_text) return '（无文字内容）'
  const text = props.diary.content_text.trim()
  if (text.length <= 50) return text
  return text.slice(0, 50) + '...'
})

/** 删除按钮透明度 */
const deleteActionOpacity = computed(() => {
  if (translateX.value < -20) {
    return Math.min(1, Math.abs(translateX.value) / DELETE_WIDTH)
  }
  return 0
})

// ==================== 方法 ====================

/**
 * 处理点击
 */
function handleTap(): void {
  // 如果正在滑动状态，不触发点击
  if (Math.abs(translateX.value) > 10) {
    resetSwipe()
    return
  }
  emit('tap', props.diary)
}

/**
 * 处理删除
 */
function handleDelete(): void {
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，确定要删除这条日记吗？',
    confirmText: '删除',
    confirmColor: '#F87171',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        emit('delete', props.diary)
      } else {
        resetSwipe()
      }
    },
  })
}

/**
 * 处理触摸开始
 */
function handleTouchStart(e: TouchEvent): void {
  touchStartX.value = e.touches[0].clientX
  isSwiping.value = true
}

/**
 * 处理触摸移动
 */
function handleTouchMove(e: TouchEvent): void {
  const currentX = e.touches[0].clientX
  const diff = currentX - touchStartX.value

  // 只允许向左滑动
  if (diff < 0) {
    translateX.value = Math.max(-DELETE_WIDTH, diff)
  } else if (translateX.value < 0) {
    // 向右滑动时，恢复位置
    translateX.value = Math.min(0, translateX.value + diff)
  }
}

/**
 * 处理触摸结束
 */
function handleTouchEnd(): void {
  isSwiping.value = false

  // 如果滑动超过一半，保持显示删除按钮
  if (translateX.value < -DELETE_WIDTH / 2) {
    translateX.value = -DELETE_WIDTH
  } else {
    resetSwipe()
  }
}

/**
 * 重置滑动状态
 */
function resetSwipe(): void {
  translateX.value = 0
}

// ==================== 暴露方法 ====================

defineExpose({
  resetSwipe,
})
</script>

<style lang="scss" scoped>
.diary-list-item {
  position: relative;
  overflow: hidden;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);

  &.is-swiping {
    transition: none;
  }
}

// ==================== 内容区域 ====================

.item-content {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  padding-left: var(--space-lg);
  transition: transform var(--transition-base);
}

.emotion-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 6rpx;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}

// ==================== 头部 ====================

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.date-area {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.date-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.zero-badge {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  padding: 2rpx 8rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-xs);
}

.labels-area {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.emotion-tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 12rpx;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);

  &--warm {
    color: var(--mood-warm);
    background-color: var(--mood-warm-bg);
  }
  &--calm {
    color: var(--mood-calm);
    background-color: var(--mood-calm-bg);
  }
  &--low {
    color: var(--mood-low);
    background-color: var(--mood-low-bg);
  }
  &--sad {
    color: var(--mood-sad);
    background-color: var(--mood-sad-bg);
  }
  &--chaos {
    color: var(--mood-chaos);
    background-color: var(--mood-chaos-bg);
  }
}

.tag-text {
  line-height: 1;
}

.more-labels {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 内容 ====================

.item-body {
  margin-bottom: var(--space-sm);
}

.preview-text {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.6;
  word-break: break-all;
}

// ==================== 底部 ====================

.item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.emotion-text {
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.time-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 删除按钮 ====================

.delete-action {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 160rpx;
  background-color: var(--color-error);
  pointer-events: none;
  transition: opacity var(--transition-fast);
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
}

.delete-icon {
  font-size: var(--font-size-md);
  color: #FFFFFF;
}
</style>