<template>
  <view class="diary-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-title">
        <text class="title-text">情绪日记</text>
      </view>
      <view class="header-actions">
        <view class="action-btn" @tap="handleExport">
          <text class="action-icon">导出</text>
        </view>
      </view>
    </view>

    <!-- 内容区域 -->
    <scroll-view
      class="page-content"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
    >
      <!-- 快速记录卡片 -->
      <view class="quick-record-card" @tap="handleQuickRecord">
        <view class="card-content">
          <template v-if="todayDiary">
            <!-- 今天已记录 -->
            <view class="recorded-status">
              <view
                class="emotion-badge"
                :style="{ backgroundColor: getEmotionColor(todayDiary.emotion_tone) }"
              />
              <view class="record-info">
                <text class="record-title">今天已记录</text>
                <text class="record-emotion">{{ getEmotionMeaning(todayDiary.emotion_tone) }}</text>
              </view>
            </view>
            <view class="edit-hint">
              <text class="hint-text">点击查看或编辑</text>
            </view>
          </template>
          <template v-else>
            <!-- 今天未记录 -->
            <view class="unrecorded-status">
              <text class="prompt-text">记一笔今天的感受?</text>
              <text class="prompt-hint">让心情有个着落</text>
            </view>
          </template>
        </view>
        <view class="card-arrow">
          <text class="arrow-icon">&gt;</text>
        </view>
      </view>

      <!-- 周报入口卡片 -->
      <view v-if="weeklyReportSummary" class="weekly-report-card" @tap="handleWeeklyReportTap">
        <view class="report-card-content">
          <view class="report-card-header">
            <text class="report-card-title">本周情绪报告</text>
            <text class="report-card-date">{{ formatWeekDate(weeklyReportSummary.week_start_date) }}</text>
          </view>
          <view class="report-card-body">
            <text class="report-card-insight">{{ weeklyReportSummary.insight || weeklyReportSummary.title }}</text>
            <view class="report-card-keywords">
              <text
                v-for="(keyword, index) in weeklyReportSummary.keywords?.slice(0, 3)"
                :key="index"
                class="keyword-tag"
              >
                {{ keyword }}
              </text>
            </view>
          </view>
        </view>
        <view class="report-card-arrow">
          <text class="arrow-icon">&gt;</text>
        </view>
      </view>

      <!-- 统计信息 -->
      <view class="stats-section">
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

      <!-- 视图切换 -->
      <view class="view-tabs">
        <view
          class="tab-item"
          :class="{ 'is-active': currentView === 'calendar' }"
          @tap="currentView = 'calendar'"
        >
          <text class="tab-text">日历</text>
        </view>
        <view
          class="tab-item"
          :class="{ 'is-active': currentView === 'chart' }"
          @tap="currentView = 'chart'"
        >
          <text class="tab-text">图表</text>
        </view>
        <view
          class="tab-item"
          :class="{ 'is-active': currentView === 'list' }"
          @tap="currentView = 'list'"
        >
          <text class="tab-text">列表</text>
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
        <!-- 日记列表 -->
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

        <!-- 空状态 -->
        <view v-else class="empty-state">
          <text class="empty-text">暂无日记记录</text>
          <text class="empty-hint">点击上方卡片开始记录</text>
        </view>

        <!-- 加载更多 -->
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
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 情绪日记列表页
 * 文件：src/pages/diary/index.vue
 * 说明：包含日历热力图、情绪曲线、情绪分布三种可视化视图，顶部快速记录卡片，日记列表
 */

import { ref, computed, onMounted } from 'vue'
import { onShow, onHide, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
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
import DiaryCalendar from '@/components/diary/DiaryCalendar.vue'
import DiaryListItem from '@/components/diary/DiaryListItem.vue'
import EmotionChart from '@/components/diary/EmotionChart.vue'
import ExportDialog from '@/components/diary/ExportDialog.vue'

// ==================== 响应式状态 ====================

/** 日记列表 */
const diaries = ref<DiaryResponse[]>([])

/** 统计数据 */
const stats = ref<{
  total_records: number
  total_days: number
  zero_record_count: number
  valid_sample_count: number
  emotion_distribution: Record<string, number>
} | null>(null)

/** 当前视图 */
const currentView = ref<'calendar' | 'chart' | 'list'>('calendar')

/** 选中的日期 */
const selectedDate = ref<string | null>(null)

/** 是否正在刷新 */
const isRefreshing = ref(false)

/** 是否正在加载更多 */
const isLoadingMore = ref(false)

/** 是否有更多数据 */
const hasMore = ref(true)

/** 当前页码 */
const currentPage = ref(1)

/** 每页数量 */
const pageSize = 20

/** 是否显示导出对话框 */
const showExportDialog = ref(false)

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 当前日历月份 */
const currentCalendarMonth = ref({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
})

/** 周报摘要数据 */
const weeklyReportSummary = ref<{
  id: string
  week_start_date: string
  title: string | null
  insight: string | null
  keywords: string[] | null
} | null>(null)

// ==================== 计算属性 ====================

/** 今日日记 */
const todayDiary = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return diaries.value.find((d) => d.record_date === today) || null
})

/** 连续记录天数 */
const streakDays = computed(() => {
  if (diaries.value.length === 0) return 0

  const dates = [...new Set(diaries.value.map((d) => d.record_date))].sort().reverse()
  let streak = 0
  const today = new Date()

  for (let i = 0; i < dates.length; i++) {
    const checkDate = new Date(today)
    checkDate.setDate(checkDate.getDate() - i)
    const checkDateStr = checkDate.toISOString().split('T')[0]

    if (dates.includes(checkDateStr)) {
      streak++
    } else {
      break
    }
  }

  return streak
})

// ==================== 方法 ====================

/**
 * 获取情绪颜色
 */
function getEmotionColor(tone: EmotionTone | null): string {
  if (!tone) return '#808080'
  return EMOTION_TONE_META[tone].color
}

/**
 * 获取情绪含义
 */
function getEmotionMeaning(tone: EmotionTone | null): string {
  if (!tone) return '未记录'
  return EMOTION_TONE_META[tone].meaning
}

/**
 * 加载日记列表
 */
async function loadDiaries(isRefresh = false): Promise<void> {
  if (isRefresh) {
    currentPage.value = 1
    hasMore.value = true
  }

  try {
    const result = await getDiaryList({
      page: currentPage.value,
      page_size: pageSize,
    })

    if (isRefresh) {
      diaries.value = result.data
    } else {
      diaries.value = [...diaries.value, ...result.data]
    }

    hasMore.value = result.pagination.page < result.pagination.total_pages
  } catch (error) {
    console.error('加载日记列表失败', error)
    uni.showToast({
      title: '加载失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 加载统计数据
 */
async function loadStats(): Promise<void> {
  try {
    stats.value = await getDiaryStats()
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

/**
 * 加载周报摘要
 */
async function loadWeeklyReportSummary(): Promise<void> {
  try {
    const result = await getWeeklyReport(false)

    // 使用类型守卫判断，只有非空周报才显示入口卡片
    if (!isEmptyReport(result)) {
      weeklyReportSummary.value = {
        id: result.id,
        week_start_date: result.week_start_date,
        title: result.title,
        insight: result.insight,
        keywords: result.keywords,
      }
    } else {
      weeklyReportSummary.value = null
    }
  } catch (error) {
    // 静默失败，不影响主流程
    if (import.meta.env.DEV) {
      console.error('加载周报摘要失败', error)
    }
    weeklyReportSummary.value = null
  }
}

/**
 * 格式化周报日期
 */
function formatWeekDate(startDate?: string): string {
  if (!startDate) return ''

  const date = new Date(startDate)
  const month = date.getMonth() + 1
  const day = date.getDate()

  return `${month}月${day}日周报`
}

/**
 * 处理周报入口点击
 */
function handleWeeklyReportTap(): void {
  track(EventName.REPORT_VIEW, { action: 'from_diary_index' })

  uni.navigateTo({
    url: '/pages/diary/weekly-report',
  })
}

/**
 * 处理刷新
 */
async function handleRefresh(): Promise<void> {
  isRefreshing.value = true

  try {
    await Promise.all([loadDiaries(true), loadStats(), loadWeeklyReportSummary()])
  } finally {
    isRefreshing.value = false
    uni.stopPullDownRefresh()
  }
}

/**
 * 处理加载更多
 */
async function handleLoadMore(): Promise<void> {
  if (isLoadingMore.value || !hasMore.value) return

  isLoadingMore.value = true
  currentPage.value++

  try {
    await loadDiaries(false)
  } finally {
    isLoadingMore.value = false
  }
}

/**
 * 处理快速记录
 */
function handleQuickRecord(): void {
  track(EventName.DIARY_CREATE, { action: 'quick_record' })

  uni.navigateTo({
    url: '/pages/diary/edit',
  })
}

/**
 * 处理日期点击
 */
function handleDayTap(date: string, diary: DiaryResponse | null): void {
  selectedDate.value = date

  if (diary) {
    // 有日记，跳转详情
    handleDiaryTap(diary)
  } else if (date === new Date().toISOString().split('T')[0]) {
    // 今天且无日记，跳转编辑
    handleQuickRecord()
  }
}

/**
 * 处理月份切换
 */
function handleMonthChange(year: number, month: number): void {
  currentCalendarMonth.value = { year, month }
}

/**
 * 处理日记点击
 */
function handleDiaryTap(diary: DiaryResponse): void {
  track(EventName.DIARY_DETAIL_VIEW, {
    diary_id: diary.id,
    emotion_tone: diary.emotion_tone,
  })

  uni.navigateTo({
    url: `/pages/diary/edit?id=${diary.id}`,
  })
}

/**
 * 处理日记删除
 */
async function handleDiaryDelete(diary: DiaryResponse): Promise<void> {
  try {
    await deleteDiary(diary.id)

    // 从列表中移除
    diaries.value = diaries.value.filter((d) => d.id !== diary.id)

    // 更新统计
    await loadStats()

    uni.showToast({
      title: '删除成功',
      icon: 'success',
    })

    track(EventName.DIARY_DELETE, {
      diary_id: diary.id,
      emotion_tone: diary.emotion_tone,
    })
  } catch (error) {
    console.error('删除日记失败', error)
    uni.showToast({
      title: '删除失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 处理导出
 */
function handleExport(): void {
  showExportDialog.value = true

  track(EventName.DIARY_LIST_VIEW, { action: 'open_export' })
}

/**
 * 处理导出成功
 */
function handleExportSuccess(fileUrl: string, fileName: string): void {
  console.log('导出成功', fileUrl, fileName)
}

/**
 * 处理删除全部
 */
function handleDeleteAll(): void {
  uni.showModal({
    title: '确认删除全部日记',
    content: `将删除全部 ${stats.value?.total_records || 0} 条日记，删除后无法恢复。`,
    confirmText: '删除全部',
    confirmColor: '#F87171',
    cancelText: '取消',
    success: async (res) => {
      if (res.confirm) {
        try {
          uni.showLoading({ title: '删除中...' })
          await deleteAllDiaries()
          uni.hideLoading()

          // 清空数据
          diaries.value = []
          stats.value = null

          uni.showToast({
            title: '删除成功',
            icon: 'success',
          })

          track(EventName.DIARY_DELETE, { action: 'delete_all' })
        } catch (error) {
          uni.hideLoading()
          console.error('删除全部日记失败', error)
          uni.showToast({
            title: '删除失败，请重试',
            icon: 'none',
          })
        }
      }
    },
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
  loadDiaries(true)
  loadStats()
  loadWeeklyReportSummary()
})

onShow(() => {
  trackPageEnter('diary')
  // 每次显示页面时刷新数据
  loadDiaries(true)
  loadStats()
  loadWeeklyReportSummary()
})

onHide(() => {
  trackPageLeave('diary')
})

onReachBottom(() => {
  if (currentView.value === 'list') {
    handleLoadMore()
  }
})

onPullDownRefresh(() => {
  handleRefresh()
})
</script>

<style lang="scss" scoped>
.diary-page {
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

.header-title {
  flex: 1;
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

.action-icon {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding: var(--space-md);
}

// ==================== 快速记录卡片 ====================

.quick-record-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-md);

  &:active {
    opacity: 0.9;
  }
}

.card-content {
  flex: 1;
}

.recorded-status {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.emotion-badge {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
}

.record-info {
  display: flex;
  flex-direction: column;
}

.record-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.record-emotion {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.edit-hint {
  margin-top: var(--space-xs);
}

.hint-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.unrecorded-status {
  display: flex;
  flex-direction: column;
}

.prompt-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.prompt-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.card-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
}

.arrow-icon {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
}

// ==================== 周报入口卡片 ====================

.weekly-report-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-md);
  border-left: 4rpx solid var(--brand-primary);

  &:active {
    opacity: 0.9;
  }
}

.report-card-content {
  flex: 1;
}

.report-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xs);
}

.report-card-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
}

.report-card-date {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.report-card-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.report-card-insight {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.report-card-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2rpx var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.report-card-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: var(--space-sm);
}

// ==================== 统计信息 ====================

.stats-section {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-md);
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stats-value {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.stats-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
}

.stats-divider {
  width: 1px;
  height: 48rpx;
  background-color: var(--border-primary);
}

// ==================== 视图切换 ====================

.view-tabs {
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

// ==================== 日历视图 ====================

.calendar-view {
  margin-bottom: var(--space-md);
}

// ==================== 图表视图 ====================

.chart-view {
  margin-bottom: var(--space-md);
}

// ==================== 列表视图 ====================

.list-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.diary-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.list-item-wrapper {
  position: relative;
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl) 0;
}

.empty-text {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 加载更多 ====================

.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md);
}

.load-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 删除全部 ====================

.delete-all-section {
  padding: var(--space-lg);
}

.delete-all-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-error);

  &:active {
    opacity: 0.8;
  }
}

.delete-all-text {
  font-size: var(--font-size-base);
  color: var(--color-error);
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>