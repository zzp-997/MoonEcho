<template>
  <view class="weekly-report-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="handleBack">
        <text class="back-icon">&lt;</text>
        <text class="back-text">返回</text>
      </view>
      <view class="header-title">
        <text class="title-text">本周情绪报告</text>
      </view>
      <view class="header-actions">
        <view
          v-if="!isLoading && !isEmptyReport"
          class="action-btn"
          @tap="handleRefresh"
        >
          <text class="action-text">{{ isRefreshing ? '生成中...' : '重新生成' }}</text>
        </view>
      </view>
    </view>

    <!-- 内容区域 -->
    <scroll-view
      class="page-content"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handlePullRefresh"
    >
      <!-- 加载状态 -->
      <view v-if="isLoading" class="loading-state">
        <view class="loading-spinner" />
        <text class="loading-text">正在生成周报...</text>
      </view>

      <!-- 空周报状态 -->
      <view v-else-if="isEmptyReport" class="empty-report">
        <view class="empty-icon-wrapper">
          <text class="empty-icon">~</text>
        </view>
        <text class="empty-title">本周暂无周报</text>
        <text class="empty-message">{{ emptyReport?.message || '本周还没有记录足够的日记，无法生成周报。' }}</text>
        <view class="empty-hint">
          <text class="hint-text">记录更多日记后，AI 将为你生成专属周报</text>
        </view>
        <view class="empty-action" @tap="handleGoToRecord">
          <text class="action-btn-text">开始记录</text>
        </view>
      </view>

      <!-- 周报内容 -->
      <view v-else class="report-content">
        <!-- 动态标题 -->
        <view class="report-title-section">
          <text class="report-title">{{ report?.title || '本周情绪报告' }}</text>
          <view class="week-info">
            <text class="week-date">
              {{ formatWeekRange(report?.week_start_date, report?.week_end_date) }}
            </text>
            <text class="diary-count">{{ report?.diary_count || 0 }} 条日记</text>
          </view>
        </view>

        <!-- 情绪走势卡片 -->
        <view class="report-card story-card">
          <view class="card-header">
            <text class="card-title">情绪走势</text>
          </view>
          <view class="card-content">
            <!-- 7日情绪折线图 -->
            <view class="emotion-chart-wrapper">
              <EmotionChart
                :diaries="weekDiaries"
                :stats="weekStats"
              />
            </view>
            <!-- 故事线描述 -->
            <view v-if="report?.story_line" class="story-line">
              <text class="story-text">{{ report.story_line }}</text>
            </view>
          </view>
        </view>

        <!-- 关键词云卡片 -->
        <view class="report-card keywords-card">
          <KeywordCloud
            :keywords="report?.keywords || []"
            :max-count="8"
            :animated="true"
          />
        </view>

        <!-- 一句看见卡片 -->
        <view class="report-card insight-card">
          <view class="card-header">
            <text class="card-title">一句看见</text>
          </view>
          <view class="card-content">
            <view class="insight-wrapper">
              <text class="insight-quote">"</text>
              <text class="insight-text">{{ report?.insight || '你一直在默默撑着，却很少有人知道有多累。' }}</text>
              <text class="insight-quote">"</text>
            </view>
          </view>
        </view>

        <!-- 温和建议卡片（可折叠） -->
        <view class="report-card suggestion-card" :class="{ 'is-expanded': isSuggestionExpanded }">
          <view class="card-header" @tap="toggleSuggestion">
            <text class="card-title">温和建议</text>
            <view class="expand-toggle">
              <text class="toggle-icon">{{ isSuggestionExpanded ? '收起' : '展开' }}</text>
              <text class="toggle-arrow">{{ isSuggestionExpanded ? '^' : 'v' }}</text>
            </view>
          </view>
          <view v-if="isSuggestionExpanded" class="card-content suggestion-content">
            <text class="suggestion-text">{{ report?.suggestion || '给自己多一些喘息的时间，不必事事追求完美。' }}</text>
          </view>
        </view>

        <!-- 下周展望 -->
        <view class="outlook-section">
          <text class="outlook-text">{{ report?.outlook || '下周不一定更好，但至少不用一个人扛。' }}</text>
        </view>

        <!-- 周报来源提示 -->
        <view v-if="report?.is_cached" class="report-meta">
          <text class="meta-text">周报已于 {{ formatDateTime(report?.created_at) }} 生成</text>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 情绪周报展示页
 * 文件：src/pages/diary/weekly-report.vue
 * 说明：五段式情绪周报展示，包括动态标题、情绪走势、关键词云、一句看见、温和建议、下周展望
 */

import { ref, computed, onMounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import {
  getWeeklyReport,
  getDiaryList,
  getDiaryStats,
  isEmptyReport,
  type WeeklyReportResponse,
  type EmptyWeeklyReportResponse,
  type DiaryResponse,
} from '@/api/diary'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
import EmotionChart from '@/components/diary/EmotionChart.vue'
import KeywordCloud from '@/components/diary/KeywordCloud.vue'

// 扩展 EventName 类型以包含周报相关事件
const ReportEventName = {
  ...EventName,
  REPORT_VIEW: 'report_view',
  REPORT_REFRESH: 'report_refresh',
  REPORT_SUGGESTION_EXPAND: 'report_suggestion_expand',
  REPORT_SUGGESTION_COLLAPSE: 'report_suggestion_collapse',
}

// ==================== 响应式状态 ====================

/** 周报数据 */
const report = ref<WeeklyReportResponse | null>(null)

/** 空周报数据 */
const emptyReport = ref<EmptyWeeklyReportResponse | null>(null)

/** 本周日记列表 */
const weekDiaries = ref<DiaryResponse[]>([])

/** 本周统计 */
const weekStats = ref<{
  total_records: number
  total_days: number
  zero_record_count: number
  valid_sample_count: number
  emotion_distribution: Record<string, number>
} | null>(null)

/** 是否正在加载 */
const isLoading = ref(true)

/** 是否正在刷新 */
const isRefreshing = ref(false)

/** 是否展开温和建议 */
const isSuggestionExpanded = ref(false)

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

// ==================== 计算属性 ====================

/** 是否为空周报 */
const isEmptyReport = computed(() => {
  return emptyReport.value !== null && emptyReport.value.is_empty === true
})

// ==================== 方法 ====================

/**
 * 格式化日期范围
 */
function formatWeekRange(startDate?: string, endDate?: string): string {
  if (!startDate || !endDate) return ''

  const start = new Date(startDate)
  const end = new Date(endDate)

  const startMonth = start.getMonth() + 1
  const startDay = start.getDate()
  const endMonth = end.getMonth() + 1
  const endDay = end.getDate()

  if (startMonth === endMonth) {
    return `${startMonth}月${startDay}-${endDay}日`
  }

  return `${startMonth}月${startDay}-${endMonth}月${endDay}日`
}

/**
 * 格式化时间
 */
function formatDateTime(dateTime?: string): string {
  if (!dateTime) return ''

  const date = new Date(dateTime)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()

  return `${month}月${day}日 ${hour}:${minute < 10 ? '0' + minute : minute}`
}

/**
 * 加载周报数据
 */
async function loadReport(forceRefresh = false): Promise<void> {
  isLoading.value = true

  try {
    const result = await getWeeklyReport(forceRefresh)

    // 使用类型守卫判断是否为空周报
    if (isEmptyReport(result)) {
      emptyReport.value = result
      report.value = null
    } else {
      report.value = result
      emptyReport.value = null

      // 加载本周日记数据（用于情绪走势图）
      await loadWeekDiaries(result.week_start_date, result.week_end_date)
    }

    track(ReportEventName.REPORT_VIEW, {
      action: 'view_weekly_report',
      is_empty: isEmptyReport.value,
      diary_count: report.value?.diary_count || 0,
    })
  } catch (error) {
    console.error('加载周报失败', error)
    uni.showToast({
      title: '加载失败，请重试',
      icon: 'none',
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 加载本周日记数据
 */
async function loadWeekDiaries(startDate: string, endDate: string): Promise<void> {
  try {
    // 获取本周日记列表
    const diaryResult = await getDiaryList({
      start_date: startDate,
      end_date: endDate,
      page: 1,
      page_size: 7, // 近7天
    })
    weekDiaries.value = diaryResult.data

    // 获取统计数据（用于分布图）
    const statsResult = await getDiaryStats()
    weekStats.value = statsResult
  } catch (error) {
    console.error('加载本周日记失败', error)
  }
}

/**
 * 处理返回
 */
function handleBack(): void {
  uni.navigateBack()
}

/**
 * 处理刷新
 */
async function handleRefresh(): Promise<void> {
  if (isRefreshing.value) return

  isRefreshing.value = true

  track(ReportEventName.REPORT_REFRESH, { action: 'refresh_weekly_report' })

  try {
    await loadReport(true)
    uni.showToast({
      title: '周报已重新生成',
      icon: 'success',
    })
  } finally {
    isRefreshing.value = false
  }
}

/**
 * 处理下拉刷新
 */
async function handlePullRefresh(): Promise<void> {
  await loadReport(false)
  // scroll-view 的下拉刷新需要手动设置 refresher-triggered 为 false
  isRefreshing.value = false
}

/**
 * 切换温和建议展开状态
 */
function toggleSuggestion(): void {
  isSuggestionExpanded.value = !isSuggestionExpanded.value

  track(isSuggestionExpanded.value ? ReportEventName.REPORT_SUGGESTION_EXPAND : ReportEventName.REPORT_SUGGESTION_COLLAPSE, {
    action: isSuggestionExpanded.value ? 'expand_suggestion' : 'collapse_suggestion',
  })
}

/**
 * 处理开始记录
 */
function handleGoToRecord(): void {
  track(EventName.DIARY_CREATE, { action: 'from_empty_report' })

  uni.navigateTo({
    url: '/pages/diary/edit',
  })
}

/**
 * 获取安全区域高度
 */
function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  const bottom = systemInfo.safeAreaInsets?.bottom ?? 0
  safeAreaBottom.value = `${bottom}px`
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
  loadReport(false)
})

onShow(() => {
  trackPageEnter('weekly_report')
})

onHide(() => {
  trackPageLeave('weekly_report')
})
</script>

<style lang="scss" scoped>
.weekly-report-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
}

.header-back {
  display: flex;
  align-items: center;
  gap: var(--space-xs);

  &:active {
    opacity: 0.7;
  }
}

.back-icon {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

.back-text {
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

.header-title {
  flex: 1;
  text-align: center;
}

.title-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);

  &:active {
    opacity: 0.7;
  }
}

.action-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding: var(--space-md);
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl) 0;
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid var(--border-primary);
  border-top-color: var(--brand-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-top: var(--space-md);
}

// ==================== 空周报状态 ====================

.empty-report {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl) var(--space-md);
}

.empty-icon-wrapper {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background-color: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-lg);
}

.empty-icon {
  font-size: var(--font-size-3xl);
  color: var(--text-tertiary);
}

.empty-title {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.empty-message {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.6;
  margin-bottom: var(--space-lg);
}

.empty-hint {
  padding: var(--space-sm) 0;
}

.hint-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.empty-action {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) var(--space-xl);
  border-radius: var(--radius-lg);
  background-color: var(--brand-primary);
  margin-top: var(--space-lg);

  &:active {
    opacity: 0.9;
  }
}

.action-btn-text {
  font-size: var(--font-size-md);
  color: var(--text-on-brand);
}

// ==================== 周报内容 ====================

.report-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

// ==================== 动态标题 ====================

.report-title-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg) var(--space-md);
}

.report-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
}

.week-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: var(--space-sm);
}

.week-date {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.diary-count {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
}

// ==================== 周报卡片通用样式 ====================

.report-card {
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.card-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.card-content {
  display: flex;
  flex-direction: column;
}

// ==================== 情绪走势卡片 ====================

.story-card {
  // 情绪走势卡片特定样式
}

.emotion-chart-wrapper {
  margin-bottom: var(--space-md);
}

.story-line {
  padding: var(--space-sm) 0;
}

.story-text {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.6;
}

// ==================== 关键词云卡片 ====================

.keywords-card {
  padding: 0;
  background-color: transparent;

  .keyword-cloud {
    background-color: var(--bg-secondary);
  }
}

// ==================== 一句看见卡片 ====================

.insight-card {
  background-color: var(--bg-secondary);
}

.insight-wrapper {
  display: flex;
  align-items: flex-start;
  gap: var(--space-xs);
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.insight-quote {
  font-size: var(--font-size-xl);
  color: var(--brand-primary);
  font-weight: 300;
  line-height: 1;
}

.insight-text {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  line-height: 1.6;
  flex: 1;
}

// ==================== 温和建议卡片 ====================

.suggestion-card {
  .card-header {
    cursor: pointer;

    &:active {
      opacity: 0.8;
    }
  }
}

.expand-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.toggle-icon {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.toggle-arrow {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.suggestion-content {
  animation: fadeIn 0.3s ease-out;
}

.suggestion-text {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.6;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// ==================== 下周展望 ====================

.outlook-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg) var(--space-md);
}

.outlook-text {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.5;
}

// ==================== 周报元数据 ====================

.report-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) 0;
}

.meta-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>