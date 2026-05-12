<template>
  <view class="diary-calendar">
    <!-- 月份导航 -->
    <view class="calendar-header">
      <view class="nav-btn" @tap="handlePrevMonth">
        <text class="nav-icon">&lt;</text>
      </view>
      <view class="month-title">
        <text class="title-text">{{ currentMonthText }}</text>
        <text class="year-text">{{ currentYear }}</text>
      </view>
      <view class="nav-btn" @tap="handleNextMonth">
        <text class="nav-icon">&gt;</text>
      </view>
    </view>

    <!-- 星期标题 -->
    <view class="weekday-header">
      <view v-for="day in weekDays" :key="day" class="weekday-item">
        <text class="weekday-text">{{ day }}</text>
      </view>
    </view>

    <!-- 日期网格（支持滑动切换月份） -->
    <view
      class="calendar-grid"
      @touchstart="handleTouchStart"
      @touchend="handleTouchEnd"
    >
      <view
        v-for="(item, index) in calendarDays"
        :key="index"
        class="day-item"
        :class="{
          'is-empty': !item.date,
          'is-today': item.isToday,
          'is-selected': item.isSelected,
          'has-record': item.hasRecord,
        }"
        @tap="handleDayTap(item)"
      >
        <!-- 日期数字 -->
        <view v-if="item.date" class="day-content">
          <text class="day-number">{{ item.day }}</text>

          <!-- 有记录显示情绪色块 -->
          <view
            v-if="item.hasRecord && item.emotionTone"
            class="emotion-dot"
            :style="{ backgroundColor: getEmotionColor(item.emotionTone) }"
          />

          <!-- 今天未记录显示虚线框+问号 -->
          <view
            v-else-if="item.isToday && !item.hasRecord"
            class="empty-indicator"
          >
            <text class="question-mark">?</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 图例 -->
    <view class="calendar-legend">
      <view v-for="tone in emotionTones" :key="tone.tone" class="legend-item">
        <view
          class="legend-dot"
          :style="{ backgroundColor: tone.color }"
        />
        <text class="legend-text">{{ tone.meaning }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 日历热力图组件
 * 文件：src/components/diary/DiaryCalendar.vue
 * 说明：月视图日历，每格用情绪色调填充，支持滑动切换月份
 */

import { ref, computed, watch, onMounted } from 'vue'
import {
  EMOTION_TONE_META,
  EMOTION_TONE_LIST,
  type EmotionTone,
  type DiaryResponse,
} from '@/api/diary'

// ==================== Props ====================

interface Props {
  /** 日记数据列表 */
  diaries?: DiaryResponse[]
  /** 当前选中的日期 */
  selectedDate?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  diaries: () => [],
  selectedDate: null,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 点击日期 */
  (e: 'dayTap', date: string, diary: DiaryResponse | null): void
  /** 月份切换 */
  (e: 'monthChange', year: number, month: number): void
}>()

// ==================== 响应式状态 ====================

/** 当前显示的年份 */
const currentYear = ref(new Date().getFullYear())

/** 当前显示的月份 1-12 */
const currentMonth = ref(new Date().getMonth() + 1)

/** 触摸开始位置 */
const touchStartX = ref(0)

/** 触摸结束位置 */
const touchEndX = ref(0)

// ==================== 常量 ====================

/** 星期标题 */
const weekDays = ['日', '一', '二', '三', '四', '五', '六']

/** 情绪色调列表 */
const emotionTones = EMOTION_TONE_LIST.map((tone) => ({
  tone,
  color: EMOTION_TONE_META[tone].color,
  meaning: EMOTION_TONE_META[tone].meaning,
}))

// ==================== 计算属性 ====================

/** 当前月份文本 */
const currentMonthText = computed(() => {
  return `${currentMonth.value}月`
})

/** 日历日期数据 */
const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value

  // 获取当月第一天和最后一天
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)

  // 当月天数
  const daysInMonth = lastDay.getDate()

  // 当月第一天是星期几（0-6）
  const firstDayOfWeek = firstDay.getDay()

  // 今天
  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]

  // 构建日历数据
  const days: Array<{
    date: string | null
    day: number | null
    isToday: boolean
    isSelected: boolean
    hasRecord: boolean
    emotionTone: EmotionTone | null
    diary: DiaryResponse | null
  }> = []

  // 填充月初空白
  for (let i = 0; i < firstDayOfWeek; i++) {
    days.push({
      date: null,
      day: null,
      isToday: false,
      isSelected: false,
      hasRecord: false,
      emotionTone: null,
      diary: null,
    })
  }

  // 填充当月日期
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const diary = props.diaries.find((item) => item.record_date === dateStr) || null

    days.push({
      date: dateStr,
      day: d,
      isToday: dateStr === todayStr,
      isSelected: dateStr === props.selectedDate,
      hasRecord: !!diary,
      emotionTone: diary?.emotion_tone || null,
      diary,
    })
  }

  // 填充月末空白（补全6行）
  const remainingDays = 42 - days.length
  for (let i = 0; i < remainingDays; i++) {
    days.push({
      date: null,
      day: null,
      isToday: false,
      isSelected: false,
      hasRecord: false,
      emotionTone: null,
      diary: null,
    })
  }

  return days
})

// ==================== 方法 ====================

/**
 * 获取情绪色调颜色
 */
function getEmotionColor(tone: EmotionTone): string {
  return EMOTION_TONE_META[tone].color
}

/**
 * 处理日期点击
 */
function handleDayTap(item: typeof calendarDays.value[0]): void {
  if (!item.date) return

  emit('dayTap', item.date, item.diary)
}

/**
 * 上一月
 */
function handlePrevMonth(): void {
  if (currentMonth.value === 1) {
    currentYear.value -= 1
    currentMonth.value = 12
  } else {
    currentMonth.value -= 1
  }
  emit('monthChange', currentYear.value, currentMonth.value)
}

/**
 * 下一月
 */
function handleNextMonth(): void {
  if (currentMonth.value === 12) {
    currentYear.value += 1
    currentMonth.value = 1
  } else {
    currentMonth.value += 1
  }
  emit('monthChange', currentYear.value, currentMonth.value)
}

/**
 * 处理触摸开始
 */
function handleTouchStart(e: TouchEvent): void {
  touchStartX.value = e.touches[0].clientX
}

/**
 * 处理触摸结束
 */
function handleTouchEnd(e: TouchEvent): void {
  touchEndX.value = e.changedTouches[0].clientX
  handleSwipe()
}

/**
 * 处理滑动
 */
function handleSwipe(): void {
  const diff = touchStartX.value - touchEndX.value
  const threshold = 50

  if (diff > threshold) {
    // 向左滑动，下一月
    handleNextMonth()
  } else if (diff < -threshold) {
    // 向右滑动，上一月
    handlePrevMonth()
  }
}

/**
 * 跳转到指定月份
 */
function goToMonth(year: number, month: number): void {
  currentYear.value = year
  currentMonth.value = month
}

/**
 * 跳转到今天
 */
function goToToday(): void {
  const today = new Date()
  currentYear.value = today.getFullYear()
  currentMonth.value = today.getMonth() + 1
}

// ==================== 暴露方法 ====================

defineExpose({
  goToMonth,
  goToToday,
})

// ==================== 生命周期 ====================

onMounted(() => {
  // 触摸事件已在模板中绑定，无需额外处理
})
</script>

<style lang="scss" scoped>
.diary-calendar {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  overflow: hidden;
}

// ==================== 月份导航 ====================

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);

  &:active {
    opacity: 0.7;
  }
}

.nav-icon {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
}

.month-title {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
}

.title-text {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.year-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 星期标题 ====================

.weekday-header {
  display: flex;
  margin-bottom: var(--space-sm);
}

.weekday-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 48rpx;
}

.weekday-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 日期网格 ====================

.calendar-grid {
  display: flex;
  flex-wrap: wrap;
  user-select: none;
  width: 100%;
  overflow: hidden;
}

.day-item {
  width: 14.2857%; // 精确的 1/7，避免calc精度问题
  max-width: 14.2857%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xs);
  box-sizing: border-box;

  &.is-empty {
    pointer-events: none;
  }

  &.is-today {
    .day-number {
      color: var(--brand-primary);
      font-weight: 600;
    }
  }

  &.is-selected {
    .day-content {
      background-color: var(--brand-primary);

      .day-number {
        color: var(--text-on-brand);
      }
    }
  }

  &:active:not(.is-empty) {
    opacity: 0.7;
  }
}

.day-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  border-radius: var(--radius-md);
  transition: background-color var(--transition-fast);
}

.day-number {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  line-height: 1;
}

// ==================== 情绪色点 ====================

.emotion-dot {
  position: absolute;
  bottom: 4rpx;
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
}

// ==================== 空白指示器 ====================

.empty-indicator {
  position: absolute;
  bottom: 4rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24rpx;
  height: 24rpx;
  border: 1px dashed var(--text-tertiary);
  border-radius: var(--radius-xs);
}

.question-mark {
  font-size: 16rpx;
  color: var(--text-tertiary);
  line-height: 1;
}

// ==================== 图例 ====================

.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-primary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2xs);
}

.legend-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
}

.legend-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}
</style>
