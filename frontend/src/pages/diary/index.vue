<template>
  <view class="diary-page">
    <!-- 顶部导航栏 — 图鸟风格 -->
    <view class="page-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="header-left">
        <text class="header-title">情绪日记</text>
      </view>
      <view class="header-right">
        <view class="action-btn tn-shadow-blur tn-gradient-9" @tap="handleExport">
          <text class="action-btn-text">导出</text>
        </view>
      </view>
    </view>

    <!-- 内容区域 -->
    <scroll-view
      class="page-content"
      scroll-y
      :scroll-x="false"
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
    >
      <!-- 快速记录卡片 — 渐变背景 -->
      <view class="quick-record-card tn-shadow-card" @tap="handleQuickRecord">
        <view class="card-body">
          <template v-if="todayDiary">
            <view class="recorded-status">
              <view class="emotion-dot tn-shadow-blur" :style="{ backgroundColor: getEmotionColor(todayDiary.emotion_tone) }" />
              <view class="record-info">
                <text class="record-title">今天已记录</text>
                <text class="record-emotion">{{ getEmotionMeaning(todayDiary.emotion_tone) }}</text>
              </view>
            </view>
            <view class="record-action">
              <text class="action-go tn-gradient-6">查看</text>
            </view>
          </template>
          <template v-else>
            <view class="unrecorded-status">
              <view class="prompt-icon tn-icon-container tn-gradient-1 tn-shadow-blur">
                <text style="font-size: 48rpx;">✏️</text>
              </view>
              <view class="prompt-info">
                <text class="prompt-text">记一笔今天的感受</text>
                <text class="prompt-hint">让心情有个着落</text>
              </view>
            </view>
            <view class="record-action">
              <text class="action-go tn-gradient-5">记录</text>
            </view>
          </template>
        </view>
      </view>

      <!-- 周报入口卡片 — 彩色阴影 -->
      <view v-if="weeklyReportSummary" class="weekly-report-card tn-shadow-card" @tap="handleWeeklyReportTap">
        <view class="report-body">
          <view class="report-header">
            <view class="report-icon tn-icon-container tn-gradient-15 tn-shadow-blur">
              <text style="font-size: 36rpx;">📊</text>
            </view>
            <view class="report-meta">
              <text class="report-title">本周情绪报告</text>
              <text class="report-date">{{ formatWeekDate(weeklyReportSummary.week_start_date) }}</text>
            </view>
          </view>
          <text class="report-insight">{{ weeklyReportSummary.insight || weeklyReportSummary.title }}</text>
          <view class="report-keywords">
            <text
              v-for="(keyword, index) in weeklyReportSummary.keywords?.slice(0, 3)"
              :key="index"
              class="keyword-tag tn-color-purple"
            >
              {{ keyword }}
            </text>
          </view>
        </view>
      </view>

      <!-- 统计信息 — 渐变背景 -->
      <view class="stats-section tn-shadow-blur">
        <view class="stats-item">
          <text class="stats-value">{{ stats?.total_records || 0 }}</text>
          <text class="stats-label">总记录</text>
        </view>
        <view class="stats-divider" />
        <view class="stats-item">
          <text class="stats-value">{{ stats?.total_days || 0 }}</text>
          <text class="stats-label">记录天数</text>
        </view>
        <view class="stats-divider" />
        <view class="stats-item">
          <text class="stats-value">{{ streakDays }}</text>
          <text class="stats-label">连续天</text>
        </view>
      </view>

      <!-- 视图切换 — 图鸟胶囊风格 -->
      <view class="view-tabs">
        <view
          class="tab-item"
          :class="{ 'is-active': currentView === 'calendar' }"
          @tap="currentView = 'calendar'"
        >
          <text class="tab-text">📅 日历</text>
        </view>
        <view
          class="tab-item"
          :class="{ 'is-active': currentView === 'chart' }"
          @tap="currentView = 'chart'"
        >
          <text class="tab-text">📈 图表</text>
        </view>
        <view
          class="tab-item"
          :class="{ 'is-active': currentView === 'list' }"
          @tap="currentView = 'list'"
        >
          <text class="tab-text">📋 列表</text>
        </view>
      </view>

      <!-- 日历视图 -->
      <view v-if="currentView === 'calendar'" class="calendar-view">
        <DiaryCalendar
          :diaries="diaries"
          :selected-date="selectedDate"
          @day-tap="handleDayTap"
          @month-change="handleMonthChange"
        />
      </view>

      <!-- 图表视图 -->
      <view v-else-if="currentView === 'chart'" class="chart-view">
        <EmotionChart
          :diaries="diaries"
          :stats="stats"
        />
      </view>

      <!-- 列表视图 -->
      <view v-else-if="currentView === 'list'" class="list-view">
        <view v-if="diaries.length > 0" class="diary-list">
          <view
            v-for="diary in diaries"
            :key="diary.id"
            class="list-item-wrapper"
          >
            <DiaryListItem
              :diary="diary"
              @tap="handleDiaryTap"
              @delete="handleDiaryDelete"
            />
          </view>
        </view>

        <view v-else class="empty-state">
          <view class="empty-icon tn-icon-container tn-gradient-6 tn-shadow-blur">
            <text style="font-size: 60rpx;">📝</text>
          </view>
          <text class="tn-text-bold tn-text-lg tn-margin-top">暂无日记记录</text>
          <text class="tn-color-gray tn-margin-top-xs tn-text-sm">点击上方卡片开始记录</text>
        </view>

        <view v-if="hasMore" class="load-more" @tap="handleLoadMore">
          <text class="load-text">{{ isLoadingMore ? '加载中...' : '加载更多' }}</text>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </scroll-view>

    <!-- 导出对话框 -->
    <ExportDialog
      v-model:visible="showExportDialog"
      :diaries="diaries"
      :total-count="stats?.total_records || 0"
      @export-success="handleExportSuccess"
    />

    <!-- 底部留白 -->
    <view class="page-bottom-space" />

    <!-- 自定义TabBar -->
    <CustomTabBar />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import {
  getDiaryList,
  getDiaryStats,
  deleteDiary,
  deleteAllDiaries,
  getWeeklyReport,
  isEmptyReport,
  EMOTION_TONE_META,
  type DiaryResponse,
  type EmotionTone,
  type WeeklyReportResponse,
  type EmptyWeeklyReportResponse,
} from '@/api/diary'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import DiaryCalendar from '@/components/diary/DiaryCalendar.vue'
import DiaryListItem from '@/components/diary/DiaryListItem.vue'
import EmotionChart from '@/components/diary/EmotionChart.vue'
import ExportDialog from '@/components/diary/ExportDialog.vue'
import CustomTabBar from '@/components/common/CustomTabBar.vue'

const diaries = ref<DiaryResponse[]>([])

const stats = ref<{
  total_records: number
  total_days: number
  zero_record_count: number
  valid_sample_count: number
  emotion_distribution: Record<string, number>
} | null>(null)

const currentView = ref<'calendar' | 'chart' | 'list'>('calendar')
const selectedDate = ref<string | null>(null)
const isRefreshing = ref(false)
const isLoadingMore = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = 20
const showExportDialog = ref(false)
const safeAreaBottom = ref('0px')

const statusBarHeight = ref(0)
const sysInfo = uni.getSystemInfoSync()
statusBarHeight.value = sysInfo.statusBarHeight || 0

const currentCalendarMonth = ref({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
})

const weeklyReportSummary = ref<{
  id: string
  week_start_date: string
  title: string | null
  insight: string | null
  keywords: string[] | null
} | null>(null)

const todayDiary = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return diaries.value.find((d) => d.record_date === today) || null
})

const streakDays = computed(() => {
  if (diaries.value.length === 0) return 0
  const dates = [...new Set(diaries.value.map((d) => d.record_date))].sort().reverse()
  let streak = 0
  const today = new Date()
  for (let i = 0; i < dates.length; i++) {
    const checkDate = new Date(today)
    checkDate.setDate(checkDate.getDate() - i)
    const checkDateStr = checkDate.toISOString().split('T')[0]
    if (dates.includes(checkDateStr)) streak++
    else break
  }
  return streak
})

function getEmotionColor(tone: EmotionTone | null): string {
  if (!tone) return '#AAAAAA'
  return EMOTION_TONE_META[tone].color
}

function getEmotionMeaning(tone: EmotionTone | null): string {
  if (!tone) return '未记录'
  return EMOTION_TONE_META[tone].meaning
}

async function loadDiaries(isRefresh = false): Promise<void> {
  if (isRefresh) {
    currentPage.value = 1
    hasMore.value = true
  }
  try {
    const result = await getDiaryList({ page: currentPage.value, page_size: pageSize })
    if (isRefresh) diaries.value = result.data
    else diaries.value = [...diaries.value, ...result.data]
    hasMore.value = result.pagination.hasMore
  } catch (error) {
    console.error('加载日记列表失败', error)
    uni.showToast({ title: '加载失败，请重试', icon: 'none' })
  }
}

async function loadStats(): Promise<void> {
  try { stats.value = await getDiaryStats() } catch (error) { console.error('加载统计数据失败', error) }
}

async function loadWeeklyReportSummary(): Promise<void> {
  try {
    const result = await getWeeklyReport(false)
    if (!isEmptyReport(result)) {
      weeklyReportSummary.value = { id: result.id, week_start_date: result.week_start_date, title: result.title, insight: result.insight, keywords: result.keywords }
    } else {
      weeklyReportSummary.value = null
    }
  } catch {
    weeklyReportSummary.value = null
  }
}

function formatWeekDate(startDate?: string): string {
  if (!startDate) return ''
  const date = new Date(startDate)
  return `${date.getMonth() + 1}月${date.getDate()}日周报`
}

function handleWeeklyReportTap(): void {
  track(EventName.REPORT_VIEW, { action: 'from_diary_index' })
  uni.navigateTo({ url: '/pages/diary/weekly-report' })
}

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  try { await Promise.all([loadDiaries(true), loadStats(), loadWeeklyReportSummary()]) }
  finally { isRefreshing.value = false; uni.stopPullDownRefresh() }
}

async function handleLoadMore(): Promise<void> {
  if (isLoadingMore.value || !hasMore.value) return
  isLoadingMore.value = true
  currentPage.value++
  try { await loadDiaries(false) } finally { isLoadingMore.value = false }
}

function handleQuickRecord(): void {
  track(EventName.DIARY_CREATE, { action: 'quick_record' })
  uni.navigateTo({ url: '/pages/diary/edit' })
}

function handleDayTap(date: string, diary: DiaryResponse | null): void {
  selectedDate.value = date
  if (diary) handleDiaryTap(diary)
  else if (date === new Date().toISOString().split('T')[0]) handleQuickRecord()
}

function handleMonthChange(year: number, month: number): void {
  currentCalendarMonth.value = { year, month }
}

function handleDiaryTap(diary: DiaryResponse): void {
  track(EventName.DIARY_DETAIL_VIEW, { diary_id: diary.id, emotion_tone: diary.emotion_tone })
  uni.navigateTo({ url: `/pages/diary/edit?id=${diary.id}` })
}

async function handleDiaryDelete(diary: DiaryResponse): Promise<void> {
  try {
    await deleteDiary(diary.id)
    diaries.value = diaries.value.filter((d) => d.id !== diary.id)
    await loadStats()
    uni.showToast({ title: '删除成功', icon: 'success' })
    track(EventName.DIARY_DELETE, { diary_id: diary.id, emotion_tone: diary.emotion_tone })
  } catch (error) {
    console.error('删除日记失败', error)
    uni.showToast({ title: '删除失败，请重试', icon: 'none' })
  }
}

function handleExport(): void {
  showExportDialog.value = true
  track(EventName.DIARY_LIST_VIEW, { action: 'open_export' })
}

function handleExportSuccess(fileUrl: string, fileName: string): void {
  console.log('导出成功', fileUrl, fileName)
}

function handleDeleteAll(): void {
  uni.showModal({
    title: '确认删除全部日记',
    content: `将删除全部 ${stats.value?.total_records || 0} 条日记，删除后无法恢复。`,
    confirmText: '删除全部',
    confirmColor: '#E83A30',
    cancelText: '取消',
    success: async (res) => {
      if (res.confirm) {
        try {
          uni.showLoading({ title: '删除中...' })
          await deleteAllDiaries()
          uni.hideLoading()
          diaries.value = []
          stats.value = null
          uni.showToast({ title: '删除成功', icon: 'success' })
          track(EventName.DIARY_DELETE, { action: 'delete_all' })
        } catch (error) {
          uni.hideLoading()
          uni.showToast({ title: '删除失败，请重试', icon: 'none' })
        }
      }
    },
  })
}

function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  const bottom = systemInfo.safeAreaInsets?.bottom ?? 0
  safeAreaBottom.value = `${bottom}px`
}

onMounted(() => {
  getSafeArea()
  loadDiaries(true)
  loadStats()
  loadWeeklyReportSummary()
})

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('diary')
    loadDiaries(true)
    loadStats()
    loadWeeklyReportSummary()
  },
  onHidden() { trackPageLeave('diary') }
})

onReachBottom(() => { if (currentView.value === 'list') handleLoadMore() })
onPullDownRefresh(() => { handleRefresh() })
</script>

<style lang="scss" scoped>
.diary-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #FFFFFF;
  overflow-x: hidden;
}

// ==================== 导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 30rpx;
  background-color: #FFFFFF;
}

.header-left {
  flex: 1;
}

.header-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #080808;
}

.header-right {
  display: flex;
  align-items: center;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10rpx 28rpx;
  border-radius: 5000rpx;
}

.action-btn-text {
  color: #FFFFFF;
  font-size: 24rpx;
  font-weight: 600;
}

// ==================== 内容区 ====================

.page-content {
  flex: 1;
  padding: 20rpx 30rpx;
  overflow-x: hidden;
  box-sizing: border-box;
}

// ==================== 快速记录卡片 ====================

.quick-record-card {
  padding: 30rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  margin-bottom: 24rpx;

  &:active {
    transform: scale(0.98);
    transition: transform 0.3s ease;
  }
}

.card-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.recorded-status {
  display: flex;
  align-items: center;
  gap: 16rpx;
  flex: 1;
}

.emotion-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.record-info {
  display: flex;
  flex-direction: column;
}

.record-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #080808;
}

.record-emotion {
  font-size: 24rpx;
  color: #838383;
  margin-top: 4rpx;
}

.unrecorded-status {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
}

.prompt-info {
  display: flex;
  flex-direction: column;
}

.prompt-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #080808;
}

.prompt-hint {
  font-size: 24rpx;
  color: #838383;
  margin-top: 4rpx;
}

.record-action {
  flex-shrink: 0;
}

.action-go {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12rpx 32rpx;
  border-radius: 5000rpx;
  color: #FFFFFF;
  font-weight: 600;
  font-size: 24rpx;
}

// ==================== 周报入口卡片 ====================

.weekly-report-card {
  padding: 30rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  margin-bottom: 24rpx;

  &:active {
    transform: scale(0.98);
    transition: transform 0.3s ease;
  }
}

.report-body {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.report-header {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.report-meta {
  display: flex;
  flex-direction: column;
}

.report-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #080808;
}

.report-date {
  font-size: 22rpx;
  color: #838383;
  margin-top: 4rpx;
}

.report-insight {
  font-size: 28rpx;
  color: #080808;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.report-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6rpx 20rpx;
  border-radius: 5000rpx;
  font-size: 22rpx;
  background-color: rgba(137, 47, 232, 0.1);
}

// ==================== 统计信息 ====================

.stats-section {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 30rpx;
  background: linear-gradient(45deg, #01BEFF, #31C9E8);
  border-radius: 20rpx;
  margin-bottom: 30rpx;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stats-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #FFFFFF;
}

.stats-label {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4rpx;
}

.stats-divider {
  width: 2rpx;
  height: 50rpx;
  background-color: rgba(255, 255, 255, 0.3);
}

// ==================== 视图切换 ====================

.view-tabs {
  display: flex;
  gap: 12rpx;
  margin-bottom: 24rpx;
  background-color: #F4F4F5;
  border-radius: 5000rpx;
  padding: 6rpx;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 68rpx;
  border-radius: 5000rpx;

  &.is-active {
    background-color: #FFFFFF;
    box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.08);
  }

  &:active {
    opacity: 0.8;
  }
}

.tab-text {
  font-size: 26rpx;
  color: #838383;

  .is-active & {
    color: #080808;
    font-weight: 600;
  }
}

// ==================== 日历/图表/列表视图 ====================

.calendar-view,
.chart-view {
  margin-bottom: 24rpx;
}

.list-view {
  display: flex;
  flex-direction: column;
}

.diary-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.list-item-wrapper {
  position: relative;
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
}

// ==================== 加载更多 ====================

.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx;
}

.load-text {
  font-size: 26rpx;
  color: #838383;
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}

.page-bottom-space {
  min-height: 100rpx;
  height: calc(120rpx + env(safe-area-inset-bottom) / 2);
}
</style>
