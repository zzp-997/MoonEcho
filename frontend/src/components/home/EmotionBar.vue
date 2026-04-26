<template>
  <view class="emotion-bar" :class="{ 'has-record': hasRecordToday }">
    <!-- 状态文案 -->
    <view class="bar-content" @tap="handleTap">
      <view class="status-icon">
        <text class="icon-emoji">{{ statusEmoji }}</text>
      </view>
      <view class="status-text">
        <text class="main-text">{{ mainText }}</text>
        <text v-if="subText" class="sub-text">{{ subText }}</text>
      </view>
      <view class="action-hint">
        <text class="hint-text">{{ actionHint }}</text>
        <text class="arrow">></text>
      </view>
    </view>

    <!-- 情绪色调预览（已记录时显示） -->
    <view v-if="hasRecordToday && todayEmotion" class="emotion-preview">
      <view
        class="emotion-dot"
        :style="{ backgroundColor: getEmotionColor(todayEmotion) }"
      />
      <text class="emotion-name">{{ getEmotionMeaning(todayEmotion) }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 情绪色调条组件
 * 文件：src/components/home/EmotionBar.vue
 * 说明：首页顶部情绪状态条，显示今日记录状态
 * PRD 3.2 入口A — 首页轻引导
 */

import { computed } from 'vue'
import { EMOTION_TONE_META, type EmotionTone } from '@/api/diary'
import { track, EventName } from '@/utils/tracking'

// ==================== Props ====================

interface Props {
  /** 今日是否已记录 */
  hasRecordToday: boolean
  /** 今日情绪色调 */
  todayEmotion?: EmotionTone | null
  /** 连续记录天数 */
  streakDays?: number
}

const props = withDefaults(defineProps<Props>(), {
  hasRecordToday: false,
  todayEmotion: null,
  streakDays: 0,
})

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'tap'): void
}>()

// ==================== 计算属性 ====================

/** 状态表情 */
const statusEmoji = computed(() => {
  if (props.hasRecordToday) {
    if (props.streakDays >= 7) return '✨'
    if (props.streakDays >= 3) return '🌟'
    return '✓'
  }
  return '💭'
})

/** 主文案 */
const mainText = computed(() => {
  if (props.hasRecordToday) {
    if (props.streakDays >= 3) {
      return `已经连续记录${props.streakDays}天了`
    }
    return '今天已经记过了'
  }
  return '今天感觉怎么样？'
})

/** 副文案 */
const subText = computed(() => {
  if (props.hasRecordToday) {
    if (props.streakDays >= 3) {
      return '继续保持，很棒！'
    }
    return '想补充吗？'
  }
  return '记录一下今天的感受'
})

/** 操作提示 */
const actionHint = computed(() => {
  if (props.hasRecordToday) {
    return '查看'
  }
  return '记录'
})

// ==================== 方法 ====================

/**
 * 获取情绪颜色
 */
function getEmotionColor(tone: EmotionTone | null): string {
  if (!tone) return 'var(--text-tertiary)'
  return EMOTION_TONE_META[tone]?.color || 'var(--text-tertiary)'
}

/**
 * 获取情绪含义
 */
function getEmotionMeaning(tone: EmotionTone | null): string {
  if (!tone) return ''
  return EMOTION_TONE_META[tone]?.meaning || ''
}

/**
 * 处理点击
 */
function handleTap(): void {
  emit('tap')

  // 埋点
  if (props.hasRecordToday) {
    track(EventName.DIARY_DETAIL_VIEW, { action: 'from_emotion_bar' })
  } else {
    track(EventName.DIARY_CREATE, { action: 'from_emotion_bar' })
  }
}
</script>

<style lang="scss" scoped>
.emotion-bar {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin: var(--space-md);
  transition: all var(--transition-base);

  &:active {
    opacity: 0.9;
    transform: scale(0.99);
  }

  &.has-record {
    border-left: 4rpx solid var(--brand-primary);
  }
}

.bar-content {
  display: flex;
  align-items: center;
}

.status-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-sm);
}

.icon-emoji {
  font-size: 36rpx;
}

.status-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2rpx;
}

.sub-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.action-hint {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.hint-text {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

.arrow {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

.emotion-preview {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-primary);
}

.emotion-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
}

.emotion-name {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
</style>
