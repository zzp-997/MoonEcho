<template>
  <view class="emotion-chart">
    <!-- 视图切换 -->
    <view class="chart-tabs">
      <view
        class="tab-item"
        :class="{ 'is-active': currentView === 'line' }"
        @tap="currentView = 'line'"
      >
        <text class="tab-text">情绪曲线</text>
      </view>
      <view
        class="tab-item"
        :class="{ 'is-active': currentView === 'pie' }"
        @tap="currentView = 'pie'"
      >
        <text class="tab-text">情绪分布</text>
      </view>
    </view>

    <!-- 图表区域 -->
    <view class="chart-container">
      <!-- 情绪曲线 -->
      <view v-if="currentView === 'line'" class="line-chart">
        <!-- 图表标题 -->
        <view class="chart-header">
          <text class="chart-title">近7日情绪变化</text>
          <text class="chart-subtitle">数值越高代表情绪越好</text>
        </view>

        <!-- 折线图（使用 CSS 实现） -->
        <view class="line-chart-content">
          <!-- Y 轴标签 -->
          <view class="y-axis">
            <text v-for="label in yLabels" :key="label" class="y-label">{{ label }}</text>
          </view>

          <!-- 图表主体 -->
          <view class="chart-body">
            <!-- 网格线 -->
            <view class="grid-lines">
              <view v-for="i in 5" :key="i" class="grid-line" />
            </view>

            <!-- 数据点和连线 -->
            <view class="data-points">
              <template v-for="(point, index) in chartPoints" :key="index">
                <!-- 连线 -->
                <view
                  v-if="index < chartPoints.length - 1"
                  class="line-segment"
                  :style="getLineStyle(index)"
                />
                <!-- 数据点 -->
                <view
                  v-if="point.hasData"
                  class="data-point"
                  :style="{
                    left: `${(index / (chartPoints.length - 1)) * 100}%`,
                    bottom: `${point.position}%`,
                    backgroundColor: point.color,
                  }"
                />
                <!-- 无数据标记 -->
                <view
                  v-else
                  class="empty-point"
                  :style="{ left: `${(index / (chartPoints.length - 1)) * 100}%` }"
                >
                  <text class="empty-icon">-</text>
                </view>
              </template>
            </view>

            <!-- X 轴标签 -->
            <view class="x-axis">
              <text
                v-for="(label, index) in xLabels"
                :key="index"
                class="x-label"
              >
                {{ label }}
              </text>
            </view>
          </view>
        </view>

        <!-- 情绪图例 -->
        <view class="chart-legend">
          <view v-for="tone in emotionTones" :key="tone.tone" class="legend-item">
            <view
              class="legend-dot"
              :style="{ backgroundColor: tone.color }"
            />
            <text class="legend-text">{{ tone.meaning }}</text>
          </view>
        </view>
      </view>

      <!-- 情绪分布 -->
      <view v-else-if="currentView === 'pie'" class="pie-chart">
        <!-- 图表标题 -->
        <view class="chart-header">
          <text class="chart-title">情绪分布统计</text>
          <text class="chart-subtitle">共 {{ totalRecords }} 条记录</text>
        </view>

        <!-- 环形图（使用 CSS 实现） -->
        <view class="pie-chart-content">
          <view class="pie-container">
            <!-- 环形图 -->
            <view class="pie-ring" :style="pieRingStyle">
              <view class="pie-center">
                <text class="center-number">{{ totalRecords }}</text>
                <text class="center-label">总记录</text>
              </view>
            </view>
          </view>

          <!-- 分布列表 -->
          <view class="distribution-list">
            <view
              v-for="item in distributionItems"
              :key="item.tone"
              class="distribution-item"
            >
              <view class="item-header">
                <view
                  class="item-dot"
                  :style="{ backgroundColor: item.color }"
                />
                <text class="item-label">{{ item.meaning }}</text>
                <text class="item-count">{{ item.count }}条</text>
              </view>
              <view class="item-bar-bg">
                <view
                  class="item-bar"
                  :style="{
                    width: `${item.percentage}%`,
                    backgroundColor: item.color,
                  }"
                />
              </view>
              <text class="item-percentage">{{ item.percentage.toFixed(1) }}%</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 情绪图表组件
 * 文件：src/components/diary/EmotionChart.vue
 * 说明：包含情绪曲线（折线图）和情绪分布（环形图）两种可视化视图
 */

import { ref, computed } from 'vue'
import {
  EMOTION_TONE_META,
  EMOTION_TONE_LIST,
  type DiaryResponse,
  type EmotionTone,
} from '@/api/diary'

// ==================== Props ====================

interface Props {
  /** 日记数据列表 */
  diaries: DiaryResponse[]
  /** 统计数据 */
  stats?: {
    total_records: number
    total_days: number
    zero_record_count: number
    valid_sample_count: number
    emotion_distribution: Record<string, number>
  }
}

const props = withDefaults(defineProps<Props>(), {
  diaries: () => [],
})

// ==================== 响应式状态 ====================

/** 当前视图 */
const currentView = ref<'line' | 'pie'>('line')

// ==================== 常量 ====================

/** Y 轴标签 */
const yLabels = ['崩溃', '难过', '低落', '平静', '开心']

/** 情绪色调列表 */
const emotionTones = EMOTION_TONE_LIST.map((tone) => ({
  tone,
  color: EMOTION_TONE_META[tone].color,
  meaning: EMOTION_TONE_META[tone].meaning,
}))

/** 情绪值映射（用于折线图 Y 轴位置） */
const emotionValueMap: Record<EmotionTone, number> = {
  warm_orange: 80,
  light_green: 60,
  gray_blue: 40,
  deep_blue: 20,
  dark_purple: 10,
}

// ==================== 计算属性 ====================

/** X 轴标签（近7日） */
const xLabels = computed(() => {
  const labels: string[] = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    labels.push(`${date.getMonth() + 1}/${date.getDate()}`)
  }
  return labels
})

/** 近7日日期列表 */
const last7Days = computed(() => {
  const dates: string[] = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
  }
  return dates
})

/** 折线图数据点 */
const chartPoints = computed(() => {
  return last7Days.value.map((date) => {
    const diary = props.diaries.find((d) => d.record_date === date)
    if (diary && diary.emotion_tone) {
      return {
        hasData: true,
        position: emotionValueMap[diary.emotion_tone],
        color: EMOTION_TONE_META[diary.emotion_tone].color,
        tone: diary.emotion_tone,
      }
    }
    return {
      hasData: false,
      position: 50,
      color: 'transparent',
      tone: null,
    }
  })
})

/** 总记录数 */
const totalRecords = computed(() => {
  return props.stats?.total_records || props.diaries.length
})

/** 分布数据 */
const distributionItems = computed(() => {
  const distribution = props.stats?.emotion_distribution || {}
  const total = totalRecords.value || 1

  return EMOTION_TONE_LIST.map((tone) => {
    const count = distribution[tone] || 0
    return {
      tone,
      color: EMOTION_TONE_META[tone].color,
      meaning: EMOTION_TONE_META[tone].meaning,
      count,
      percentage: (count / total) * 100,
    }
  }).filter((item) => item.count > 0)
})

/** 环形图样式 */
const pieRingStyle = computed(() => {
  const items = distributionItems.value
  if (items.length === 0) {
    return { background: 'var(--bg-tertiary)' }
  }

  // 构建 conic-gradient
  let gradient = ''
  let currentAngle = 0

  items.forEach((item) => {
    const angle = (item.percentage / 100) * 360
    gradient += `${item.color} ${currentAngle}deg ${currentAngle + angle}deg, `
    currentAngle += angle
  })

  // 移除最后的逗号和空格
  gradient = gradient.slice(0, -2)

  return {
    background: `conic-gradient(${gradient})`,
  }
})

// ==================== 方法 ====================

/**
 * 获取连线样式
 */
function getLineStyle(index: number): Record<string, string> {
  // 边界检查：少于2个数据点时不显示连线
  if (chartPoints.value.length < 2) {
    return { display: 'none' }
  }

  const current = chartPoints.value[index]
  const next = chartPoints.value[index + 1]

  if (!current.hasData || !next.hasData) {
    return { display: 'none' }
  }

  // 计算连线的位置和角度
  const startX = (index / (chartPoints.value.length - 1)) * 100
  const endX = ((index + 1) / (chartPoints.value.length - 1)) * 100
  const startY = current.position
  const endY = next.position

  const dx = endX - startX
  const dy = endY - startY
  const length = Math.sqrt(dx * dx + dy * dy)
  const angle = Math.atan2(dy, dx) * (180 / Math.PI)

  return {
    width: `${length}%`,
    left: `${startX}%`,
    bottom: `${startY}%`,
    transform: `rotate(${angle}deg)`,
    transformOrigin: '0 0',
    backgroundColor: current.color,
  }
}
</script>

<style lang="scss" scoped>
.emotion-chart {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

// ==================== 视图切换 ====================

.chart-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 72rpx;
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
  transition: all var(--transition-fast);

  &.is-active {
    background-color: var(--brand-primary);

    .tab-text {
      color: var(--text-on-brand);
    }
  }

  &:active {
    opacity: 0.8;
  }
}

.tab-text {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
}

// ==================== 图表标题 ====================

.chart-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.chart-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.chart-subtitle {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 折线图 ====================

.line-chart-content {
  display: flex;
  gap: var(--space-sm);
  height: 400rpx;
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 48rpx;
  padding: var(--space-xs) 0;
}

.y-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  text-align: right;
}

.chart-body {
  flex: 1;
  position: relative;
}

.grid-lines {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.grid-line {
  width: 100%;
  height: 1px;
  background-color: var(--border-primary);
  opacity: 0.3;
}

.data-points {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 48rpx;
}

.data-point {
  position: absolute;
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  transform: translate(-50%, 50%);
  box-shadow: 0 0 0 4rpx var(--bg-secondary);
}

.empty-point {
  position: absolute;
  bottom: 50%;
  transform: translate(-50%, 50%);
}

.empty-icon {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.line-segment {
  position: absolute;
  height: 2px;
  transform-origin: 0 0;
  opacity: 0.6;
}

.x-axis {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 48rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.x-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 图例 ====================

.chart-legend {
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

// ==================== 环形图 ====================

.pie-chart-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
}

.pie-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 240rpx;
  height: 240rpx;
}

.pie-ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pie-center {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background-color: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.center-number {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--text-primary);
}

.center-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 分布列表 ====================

.distribution-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.distribution-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.item-header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.item-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
}

.item-label {
  flex: 1;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.item-count {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.item-bar-bg {
  height: 12rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.item-bar {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-base);
}

.item-percentage {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  text-align: right;
}
</style>