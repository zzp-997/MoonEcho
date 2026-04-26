<template>
  <view v-if="visible" class="export-dialog-overlay" @tap.self="handleClose">
    <view class="export-dialog">
      <!-- 标题 -->
      <view class="dialog-header">
        <text class="dialog-title">导出日记</text>
        <view class="close-btn" @tap="handleClose">
          <text class="close-icon">X</text>
        </view>
      </view>

      <!-- 内容 -->
      <view class="dialog-body">
        <!-- 导出格式 -->
        <view class="option-section">
          <text class="section-title">导出格式</text>
          <view class="format-options">
            <view
              class="format-item"
              :class="{ 'is-selected': selectedFormat === 'json' }"
              @tap="selectedFormat = 'json'"
            >
              <text class="format-label">JSON</text>
              <text class="format-desc">结构化数据，适合备份</text>
            </view>
            <view
              class="format-item"
              :class="{ 'is-selected': selectedFormat === 'pdf' }"
              @tap="selectedFormat = 'pdf'"
            >
              <text class="format-label">PDF</text>
              <text class="format-desc">精美排版，适合分享</text>
            </view>
          </view>
        </view>

        <!-- 导出范围 -->
        <view class="option-section">
          <text class="section-title">导出范围</text>
          <view class="range-options">
            <view
              class="range-item"
              :class="{ 'is-selected': selectedRange === 'all' }"
              @tap="selectedRange = 'all'"
            >
              <text class="range-label">全部日记</text>
              <text class="range-count">{{ totalCount }}条</text>
            </view>
            <view
              class="range-item"
              :class="{ 'is-selected': selectedRange === 'month' }"
              @tap="selectedRange = 'month'"
            >
              <text class="range-label">本月日记</text>
              <text class="range-count">{{ monthCount }}条</text>
            </view>
            <view
              v-if="weekCount > 0"
              class="range-item"
              :class="{ 'is-selected': selectedRange === 'week' }"
              @tap="selectedRange = 'week'"
            >
              <text class="range-label">本周日记</text>
              <text class="range-count">{{ weekCount }}条</text>
            </view>
          </view>
        </view>

        <!-- 自定义日期范围 -->
        <view v-if="selectedRange === 'custom'" class="custom-range">
          <view class="date-input" @tap="handleSelectStartDate">
            <text class="date-label">开始日期</text>
            <text class="date-value">{{ startDate || '请选择' }}</text>
          </view>
          <text class="date-separator">至</text>
          <view class="date-input" @tap="handleSelectEndDate">
            <text class="date-label">结束日期</text>
            <text class="date-value">{{ endDate || '请选择' }}</text>
          </view>
        </view>
      </view>

      <!-- 底部 -->
      <view class="dialog-footer">
        <view class="cancel-btn" @tap="handleClose">
          <text class="btn-text">取消</text>
        </view>
        <view
          class="confirm-btn"
          :class="{ 'is-loading': isExporting }"
          @tap="handleExport"
        >
          <text class="btn-text">{{ isExporting ? '导出中...' : '确认导出' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 导出对话框组件
 * 文件：src/components/diary/ExportDialog.vue
 * 说明：支持JSON/PDF格式导出，包含导出范围选择
 */

import { ref, computed, watch } from 'vue'
import { exportDiaries, type DiaryResponse } from '@/api/diary'
import { track, EventName } from '@/utils/tracking'

// ==================== Props ====================

interface Props {
  /** 是否显示对话框 */
  visible: boolean
  /** 日记列表 */
  diaries?: DiaryResponse[]
  /** 总记录数 */
  totalCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  diaries: () => [],
  totalCount: 0,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 更新可见状态 */
  (e: 'update:visible', value: boolean): void
  /** 导出成功 */
  (e: 'exportSuccess', fileUrl: string, fileName: string): void
  /** 导出失败 */
  (e: 'exportError', error: Error): void
}>()

// ==================== 响应式状态 ====================

/** 选中的格式 */
const selectedFormat = ref<'json' | 'pdf'>('json')

/** 选中的范围 */
const selectedRange = ref<'all' | 'month' | 'week' | 'custom'>('all')

/** 自定义开始日期 */
const startDate = ref('')

/** 自定义结束日期 */
const endDate = ref('')

/** 是否正在导出 */
const isExporting = ref(false)

// ==================== 计算属性 ====================

/** 本月日记数量 */
const monthCount = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  return props.diaries.filter((d) => {
    const date = new Date(d.record_date)
    return date >= firstDay && date <= lastDay
  }).length
})

/** 本周日记数量 */
const weekCount = computed(() => {
  const now = new Date()
  // 周日 getDay() 返回 0，需要转换为 7 来正确计算本周起始
  const dayOfWeek = now.getDay() || 7
  const weekStart = new Date(now)
  // 本周一作为一周开始
  weekStart.setDate(now.getDate() - dayOfWeek + 1)
  weekStart.setHours(0, 0, 0, 0)

  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekStart.getDate() + 6)
  weekEnd.setHours(23, 59, 59, 999)

  return props.diaries.filter((d) => {
    const date = new Date(d.record_date)
    return date >= weekStart && date <= weekEnd
  }).length
})

// ==================== 方法 ====================

/**
 * 关闭对话框
 */
function handleClose(): void {
  emit('update:visible', false)
}

/**
 * 选择开始日期
 */
function handleSelectStartDate(): void {
  // 使用 uni-app 的日期选择器（picker 组件）
  // 由于这里需要动态选择，改用默认值
  const today = new Date()
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
  startDate.value = thirtyDaysAgo.toISOString().split('T')[0]

  // 提示用户实际选择需要使用 picker 组件
  uni.showToast({
    title: '请在实际项目中使用 picker 组件',
    icon: 'none',
  })
}

/**
 * 选择结束日期
 */
function handleSelectEndDate(): void {
  const today = new Date()
  endDate.value = today.toISOString().split('T')[0]

  uni.showToast({
    title: '请在实际项目中使用 picker 组件',
    icon: 'none',
  })
}

/**
 * 获取导出日期范围
 */
function getExportDateRange(): { start_date?: string; end_date?: string } {
  const now = new Date()

  switch (selectedRange.value) {
    case 'all':
      return {}
    case 'month': {
      const year = now.getFullYear()
      const month = now.getMonth()
      const firstDay = new Date(year, month, 1)
      const lastDay = new Date(year, month + 1, 0)
      return {
        start_date: firstDay.toISOString().split('T')[0],
        end_date: lastDay.toISOString().split('T')[0],
      }
    }
    case 'week': {
      // 周日 getDay() 返回 0，需要转换为 7 来正确计算本周起始
      const dayOfWeek = now.getDay() || 7
      const weekStart = new Date(now)
      // 本周一作为一周开始
      weekStart.setDate(now.getDate() - dayOfWeek + 1)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekStart.getDate() + 6)
      return {
        start_date: weekStart.toISOString().split('T')[0],
        end_date: weekEnd.toISOString().split('T')[0],
      }
    }
    case 'custom':
      return {
        start_date: startDate.value || undefined,
        end_date: endDate.value || undefined,
      }
    default:
      return {}
  }
}

/**
 * 执行导出
 */
async function handleExport(): Promise<void> {
  if (isExporting.value) return

  isExporting.value = true

  try {
    const dateRange = getExportDateRange()
    const result = await exportDiaries(selectedFormat.value, dateRange)

    // 追踪导出事件
    track(EventName.DIARY_EXPORT, {
      format: selectedFormat.value,
      range: selectedRange.value,
    })

    // 显示成功提示
    uni.showToast({
      title: '导出成功',
      icon: 'success',
    })

    // 触发成功事件
    emit('exportSuccess', result.file_url, result.file_name)

    // 关闭对话框
    handleClose()

    // 下载文件
    handleDownload(result.file_url, result.file_name)
  } catch (error) {
    console.error('导出失败', error)
    uni.showToast({
      title: '导出失败，请重试',
      icon: 'none',
    })
    emit('exportError', error as Error)
  } finally {
    isExporting.value = false
  }
}

/**
 * 处理下载
 */
function handleDownload(fileUrl: string, fileName: string): void {
  // #ifdef H5
  // H5 端直接打开链接下载
  const link = document.createElement('a')
  link.href = fileUrl
  link.download = fileName
  link.click()
  // #endif

  // #ifdef APP-PLUS
  // APP 端使用原生下载
  plus.runtime.openURL(fileUrl)
  // #endif

  // #ifdef MP-WEIXIN
  // 小程序端使用下载 API
  uni.downloadFile({
    url: fileUrl,
    success: (res) => {
      if (res.statusCode === 200) {
        uni.saveFile({
          tempFilePath: res.tempFilePath,
          success: () => {
            uni.showToast({ title: '已保存到本地', icon: 'success' })
          },
        })
      }
    },
  })
  // #endif
}

// ==================== 监听 ====================

// 重置状态
watch(
  () => props.visible,
  (newVal) => {
    if (!newVal) {
      // 关闭时重置
      selectedFormat.value = 'json'
      selectedRange.value = 'all'
      startDate.value = ''
      endDate.value = ''
      isExporting.value = false
    }
  }
)
</script>

<style lang="scss" scoped>
.export-dialog-overlay {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal-backdrop);
}

.export-dialog {
  width: 90%;
  max-width: 600rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

// ==================== 标题 ====================

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border-primary);
}

.dialog-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.7;
  }
}

.close-icon {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
}

// ==================== 内容 ====================

.dialog-body {
  padding: var(--space-lg);
}

.option-section {
  margin-bottom: var(--space-lg);

  &:last-child {
    margin-bottom: 0;
  }
}

.section-title {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

// ==================== 格式选项 ====================

.format-options {
  display: flex;
  gap: var(--space-sm);
}

.format-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  border-radius: var(--radius-md);
  border: 2px solid var(--border-primary);
  transition: all var(--transition-fast);

  &.is-selected {
    border-color: var(--brand-primary);
    background-color: rgba(124, 111, 224, 0.1);
  }

  &:active {
    opacity: 0.8;
  }
}

.format-label {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.format-desc {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 范围选项 ====================

.range-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.range-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  border-radius: var(--radius-md);
  border: 2px solid var(--border-primary);
  transition: all var(--transition-fast);

  &.is-selected {
    border-color: var(--brand-primary);
    background-color: rgba(124, 111, 224, 0.1);
  }

  &:active {
    opacity: 0.8;
  }
}

.range-label {
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

.range-count {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 自定义日期 ====================

.custom-range {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.date-input {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
}

.date-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.date-value {
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

.date-separator {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 底部 ====================

.dialog-footer {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--border-primary);
}

.cancel-btn,
.confirm-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);

  &:active {
    opacity: 0.8;
  }
}

.cancel-btn {
  background-color: var(--bg-tertiary);
}

.confirm-btn {
  background-color: var(--brand-primary);

  &.is-loading {
    opacity: 0.7;
    pointer-events: none;
  }
}

.btn-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-secondary);
}

.confirm-btn .btn-text {
  color: var(--text-on-brand);
}
</style>