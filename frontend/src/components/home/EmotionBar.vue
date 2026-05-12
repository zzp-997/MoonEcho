<template>
  <view class="emotion-bar tn-shadow-card" @tap="handleTap">
    <view class="bar-row">
      <view class="bar-left">
        <view
          v-if="hasRecordToday && todayEmotion"
          class="emotion-dot"
          :style="{ backgroundColor: getEmotionColor(todayEmotion) }"
        />
        <text class="main-text">{{ mainText }}</text>
      </view>
      <view class="action-btn tn-gradient-6 tn-shadow-indigo">{{ actionHint }} ▸</view>
    </view>
    <text v-if="subText" class="sub-text">{{ subText }}</text>
    <!-- 底部渐变装饰条 -->
    <view class="bar-decoration" />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { EMOTION_TONE_META, type EmotionTone } from '@/api/diary'
import { track, EventName } from '@/utils/tracking'

interface Props {
  hasRecordToday: boolean
  todayEmotion?: EmotionTone | null
  streakDays?: number
}

const props = withDefaults(defineProps<Props>(), {
  hasRecordToday: false,
  todayEmotion: null,
  streakDays: 0,
})

const emit = defineEmits<{
  (e: 'tap'): void
}>()

const mainText = computed(() => {
  if (props.hasRecordToday) {
    if (props.streakDays >= 3) return `连续记录${props.streakDays}天`
    return '今天已记录'
  }
  return '今天感觉怎么样'
})

const subText = computed(() => {
  if (props.hasRecordToday && props.todayEmotion) return getEmotionMeaning(props.todayEmotion)
  if (!props.hasRecordToday) return '写点什么吧'
  return ''
})

const actionHint = computed(() => props.hasRecordToday ? '查看' : '记录')

function getEmotionColor(tone: EmotionTone | null): string {
  if (!tone) return '#AAAAAA'
  return EMOTION_TONE_META[tone]?.color || '#AAAAAA'
}

function getEmotionMeaning(tone: EmotionTone | null): string {
  if (!tone) return ''
  return EMOTION_TONE_META[tone]?.meaning || ''
}

function handleTap(): void {
  emit('tap')
  if (props.hasRecordToday) track(EventName.DIARY_DETAIL_VIEW, { action: 'from_emotion_bar' })
  else track(EventName.DIARY_CREATE, { action: 'from_emotion_bar' })
}
</script>

<style lang="scss" scoped>
.emotion-bar {
  padding: 24rpx 30rpx;
  background-color: #FFFFFF;
  position: relative;
  overflow: hidden;

  &:active {
    opacity: 0.85;
    transform: scale(0.98);
  }
}

.bar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bar-left {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.emotion-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.main-text {
  font-size: 30rpx;
  font-weight: 500;
  color: var(--color-black, #080808);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8rpx 24rpx;
  border-radius: 5000rpx;
  color: #FFFFFF;
  font-weight: 600;
  font-size: 22rpx;
}

.sub-text {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: var(--color-gray, #838383);
}

// 底部渐变装饰条
.bar-decoration {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 6rpx;
  background-image: linear-gradient(90deg, #209CFF, #68E0CF);
  border-radius: 0 0 15rpx 15rpx;
}
</style>
