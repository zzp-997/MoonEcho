<template>
  <view class="weekly-report-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="handleBack">
        <wd-icon name="arrow-left" size="20px" color="#080808" />
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
          <wd-icon name="refresh" size="18px" color="#838383" />
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
          <wd-icon name="calendar" size="48px" color="#838383" />
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
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
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

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('weekly_report')
  },
  onHidden() {
    trackPageLeave('weekly_report')
  }
})
</script>

<style lang="scss" scoped>
.weekly-report-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #F8F8FA;
}

// ==================== 导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 30rpx;
  background: linear-gradient(135deg, #892FE8, #5F25E8);
}

.header-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  color: #FFFFFF;

  &:active { opacity: 0.6; }
}

.header-title {
  flex: 1;
  text-align: center;
}

.title-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);

  &:active { opacity: 0.6; }
}

// ==================== 内容区 ====================

.page-content {
  flex: 1;
  padding: 30rpx;
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid rgba(137, 47, 232, 0.2);
  border-top-color: #892FE8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 26rpx;
  color: #838383;
  margin-top: 20rpx;
}

// ==================== 空周报 ====================

.empty-report {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.empty-icon-wrapper {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(137, 47, 232, 0.1), rgba(95, 37, 232, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30rpx;
}

.empty-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #080808;
  margin-bottom: 16rpx;
}

.empty-message {
  font-size: 28rpx;
  color: #838383;
  text-align: center;
  line-height: 1.6;
  margin-bottom: 30rpx;
}

.empty-hint {
  padding: 12rpx 0;
}

.hint-text {
  font-size: 24rpx;
  color: #AAAAAA;
}

.empty-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 60rpx;
  border-radius: 5000rpx;
  background: linear-gradient(135deg, #892FE8, #5F25E8);
  box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(137, 47, 232, 0.3);
  margin-top: 20rpx;

  &:active {
    transform: scale(0.98);
    transition: transform 0.1s ease-out;
  }
}

.action-btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #FFFFFF;
}

// ==================== 周报内容 ====================

.report-content {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

// ==================== 动态标题 ====================

.report-title-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0;
}

.report-title {
  font-size: 48rpx;
  font-weight: 700;
  color: #080808;
  text-align: center;
  line-height: 1.3;
}

.week-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 16rpx;
}

.week-date {
  font-size: 26rpx;
  color: #838383;
}

.diary-count {
  font-size: 22rpx;
  color: #AAAAAA;
  margin-top: 4rpx;
}

// ==================== 周报卡片通用 ====================

.report-card {
  background-color: #FFFFFF;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.card-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #838383;
  letter-spacing: 2rpx;
}

.card-content {
  display: flex;
  flex-direction: column;
}

// ==================== 情绪走势 ====================

.emotion-chart-wrapper {
  margin-bottom: 20rpx;
}

.story-line {
  padding: 12rpx 0;
}

.story-text {
  font-size: 28rpx;
  color: #838383;
  line-height: 1.6;
}

// ==================== 关键词云 ====================

.keywords-card {
  padding: 0;
  background-color: transparent;
  box-shadow: none;
}

// ==================== 一句看见 ====================

.insight-card {
  background-color: #FFFFFF;
}

.insight-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  padding: 30rpx;
  background: linear-gradient(135deg, rgba(1, 190, 255, 0.05), rgba(61, 126, 255, 0.05));
  border-radius: 16rpx;
}

.insight-quote {
  font-size: 48rpx;
  color: #01BEFF;
  font-weight: 300;
  line-height: 1;
}

.insight-text {
  font-size: 30rpx;
  color: #080808;
  line-height: 1.6;
  flex: 1;
}

// ==================== 温和建议 ====================

.suggestion-card {
  .card-header {
    &:active { opacity: 0.8; }
  }
}

.expand-toggle {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.toggle-icon {
  font-size: 26rpx;
  color: #838383;
}

.toggle-arrow {
  font-size: 22rpx;
  color: #AAAAAA;
}

.suggestion-content {
  animation: fadeIn 0.15s ease-out;
}

.suggestion-text {
  font-size: 28rpx;
  color: #838383;
  line-height: 1.6;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

// ==================== 下周展望 ====================

.outlook-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx 0;
}

.outlook-text {
  font-size: 28rpx;
  color: #838383;
  text-align: center;
  line-height: 1.5;
}

// ==================== 元数据 ====================

.report-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 0;
}

.meta-text {
  font-size: 22rpx;
  color: #AAAAAA;
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>