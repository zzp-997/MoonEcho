<template>
  <wd-popup
    v-model="visible"
    position="bottom"
    :closeOnClickModal="true"
    @close="handleClose"
  >
    <view class="report-dialog">
      <!-- 步骤1: 选择举报类型 -->
      <view v-if="step === 1" class="step-content">
        <!-- 标题区域 -->
        <view class="dialog-header">
          <text class="dialog-title">选择举报原因</text>
          <view class="close-btn" @tap="handleClose">
            <text class="close-icon">x</text>
          </view>
        </view>

        <!-- 举报类型列表 -->
        <view class="type-list">
          <view
            v-for="option in reportTypeOptions"
            :key="option.value"
            class="type-item"
            :class="{ 'is-selected': selectedType === option.value }"
            @tap="handleSelectType(option.value)"
          >
            <view class="type-content">
              <text class="type-label">{{ option.label }}</text>
              <text v-if="option.value === ReportType.SELF_HARM" class="type-hint">
                我们会立即提供帮助
              </text>
            </view>
            <view v-if="selectedType === option.value" class="type-check">
              <text class="check-icon">v</text>
            </view>
          </view>
        </view>

        <!-- 下一步按钮 -->
        <view class="dialog-footer">
          <view
            class="next-btn"
            :class="{ 'is-disabled': !selectedType }"
            @tap="handleNextStep"
          >
            <text class="next-text">{{ hasNextStep ? '下一步' : '提交举报' }}</text>
          </view>
        </view>
      </view>

      <!-- 步骤2: 填写详细原因 -->
      <view v-else-if="step === 2" class="step-content">
        <!-- 标题区域 -->
        <view class="dialog-header">
          <view class="back-btn" @tap="handlePrevStep">
            <text class="back-icon">&lt;</text>
          </view>
          <text class="dialog-title">补充说明</text>
          <view class="close-btn" @tap="handleClose">
            <text class="close-icon">x</text>
          </view>
        </view>

        <!-- 已选类型提示 -->
        <view class="selected-type-hint">
          <text class="hint-label">举报原因：</text>
          <text class="hint-value">{{ selectedTypeLabel }}</text>
        </view>

        <!-- 详细原因输入 -->
        <view class="reason-area">
          <textarea
            v-model="reasonText"
            class="reason-input"
            :maxlength="500"
            placeholder="请描述具体情况（选填）"
            placeholder-class="reason-placeholder"
            :auto-height="false"
          />
          <text class="char-count">{{ reasonText.length }}/500</text>
        </view>

        <!-- 提交按钮 -->
        <view class="dialog-footer">
          <view
            class="submit-btn"
            :class="{ 'is-loading': isSubmitting }"
            @tap="handleSubmit"
          >
            <text class="submit-text">{{ isSubmitting ? '提交中...' : '提交举报' }}</text>
          </view>
        </view>
      </view>

      <!-- 步骤3: 提交成功 -->
      <view v-else-if="step === 3" class="step-content step-success">
        <view class="success-icon-wrapper">
          <text class="success-icon">ok</text>
        </view>
        <text class="success-title">感谢你的反馈</text>
        <text class="success-desc">我们会认真处理你的举报，并在24小时内给出结果。</text>
        <text class="success-note">你的举报信息对被举报者完全不可见，请放心。</text>
        <view class="dialog-footer">
          <view class="confirm-btn" @tap="handleClose">
            <text class="confirm-text">我知道了</text>
          </view>
        </view>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </view>
  </wd-popup>
</template>

<script setup lang="ts">
/**
 * 回声 - 统一举报弹窗组件
 * 文件：src/components/common/ReportDialog.vue
 * 说明：提供统一的举报交互流程：选择类型 -> 补充说明 -> 提交成功
 * 设计规范：参考 modules_design.md 7.7 举报处理流程
 */

import { ref, computed, watch, onMounted } from 'vue'
import {
  ReportType,
  ReportContentType,
  ReportTypeLabels,
  ReportTypeOptions,
  type ReportCreateResponse,
} from '@/api/modules/report'
import { createReport } from '@/api/modules/report'

// ==================== Types ====================

/** 举报目标信息 */
export interface ReportTarget {
  /** 举报内容类型 */
  contentType: ReportContentType
  /** 内容ID */
  contentId?: string
  /** 被举报用户ID */
  userId?: string
}

// ==================== Props ====================

const props = defineProps<{
  /** 是否显示 */
  show: boolean
  /** 举报目标 */
  target: ReportTarget | null
}>()

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'success', response: ReportCreateResponse): void
  (e: 'close'): void
}>()

// ==================== 响应式状态 ====================

/** 内部可见状态 */
const visible = ref(false)

/** 当前步骤 (1: 选择类型, 2: 补充说明, 3: 提交成功) */
const step = ref(1)

/** 选中的举报类型 */
const selectedType = ref<ReportType | null>(null)

/** 详细原因 */
const reasonText = ref('')

/** 是否正在提交 */
const isSubmitting = ref(false)

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 举报类型选项列表 */
const reportTypeOptions = ReportTypeOptions

// ==================== 计算属性 ====================

/** 选中类型的标签 */
const selectedTypeLabel = computed(() => {
  if (!selectedType.value) return ''
  return ReportTypeLabels[selectedType.value]
})

/** 是否有下一步（自杀自残类型跳过补充说明，直接提交） */
const hasNextStep = computed(() => {
  return selectedType.value !== ReportType.SELF_HARM
})

// ==================== 监听 ====================

watch(
  () => props.show,
  (newVal) => {
    visible.value = newVal
    if (newVal) {
      // 每次打开时重置状态
      resetState()
    }
  }
)

watch(visible, (newVal) => {
  emit('update:show', newVal)
  if (!newVal) {
    emit('close')
  }
})

// ==================== 方法 ====================

/**
 * 获取安全区域高度
 */
function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  const bottom = systemInfo.safeAreaInsets?.bottom ?? 0
  safeAreaBottom.value = `${bottom}px`
}

/**
 * 重置状态
 */
function resetState(): void {
  step.value = 1
  selectedType.value = null
  reasonText.value = ''
  isSubmitting.value = false
}

/**
 * 选择举报类型
 */
function handleSelectType(type: ReportType): void {
  selectedType.value = type
}

/**
 * 下一步
 */
function handleNextStep(): void {
  if (!selectedType.value) return

  // 自杀自残类型直接提交
  if (selectedType.value === ReportType.SELF_HARM) {
    handleSubmit()
    return
  }

  step.value = 2
}

/**
 * 上一步
 */
function handlePrevStep(): void {
  step.value = 1
}

/**
 * 提交举报
 */
async function handleSubmit(): Promise<void> {
  if (!selectedType.value || !props.target || isSubmitting.value) return

  isSubmitting.value = true

  try {
    const requestData: any = {
      reported_content_type: props.target.contentType,
      report_type: selectedType.value,
    }

    // 设置内容ID或用户ID
    if (props.target.contentId) {
      requestData.reported_content_id = props.target.contentId
    }
    if (props.target.userId) {
      requestData.reported_user_id = props.target.userId
    }

    // 添加详细原因
    if (reasonText.value.trim()) {
      requestData.reason = reasonText.value.trim()
    }

    const result = await createReport(requestData)

    // 显示成功页面
    step.value = 3

    emit('success', result)
  } catch (error) {
    console.error('提交举报失败', error)
    uni.showToast({
      title: '提交失败，请重试',
      icon: 'none',
    })
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 关闭弹窗
 */
function handleClose(): void {
  visible.value = false
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
})
</script>

<style lang="scss" scoped>
.report-dialog {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

// ==================== 通用标题区域 ====================

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  height: 100rpx;
  border-bottom: 1px solid var(--border-primary);
}

.dialog-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  position: absolute;
  top: 50%;
  right: var(--space-md);
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
}

.close-icon {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
}

.back-btn {
  position: absolute;
  top: 50%;
  left: var(--space-md);
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
}

.back-icon {
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

// ==================== 步骤1: 选择类型 ====================

.type-list {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  max-height: 60vh;
  overflow-y: auto;
}

.type-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  border: 2rpx solid transparent;
  transition: border-color 0.2s, background-color 0.2s;

  &:active {
    opacity: 0.9;
  }

  &.is-selected {
    border-color: var(--brand-primary);
    background-color: rgba(124, 111, 224, 0.06);
  }
}

.type-content {
  display: flex;
  flex-direction: column;
}

.type-label {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  font-weight: 500;
}

.type-hint {
  font-size: var(--font-size-xs);
  color: var(--color-warning);
  margin-top: 4rpx;
}

.type-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40rpx;
  height: 40rpx;
  background-color: var(--brand-primary);
  border-radius: 50%;
}

.check-icon {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);
}

// ==================== 步骤2: 补充说明 ====================

.selected-type-hint {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-secondary);
  margin: var(--space-md) var(--space-md) 0;
  border-radius: var(--radius-md);
}

.hint-label {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.hint-value {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
  font-weight: 500;
}

.reason-area {
  position: relative;
  margin: var(--space-md);
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.reason-input {
  width: 100%;
  height: 240rpx;
  font-size: var(--font-size-base);
  color: var(--text-primary);
  line-height: 1.6;
  background-color: transparent;
}

.reason-placeholder {
  color: var(--text-tertiary);
}

.char-count {
  display: block;
  text-align: right;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
}

// ==================== 步骤3: 提交成功 ====================

.step-success {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-2xl) var(--space-lg);
}

.success-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 120rpx;
  background-color: rgba(52, 211, 153, 0.12);
  border-radius: 50%;
  margin-bottom: var(--space-lg);
}

.success-icon {
  font-size: 48rpx;
  color: var(--color-success);
}

.success-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.success-desc {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.6;
  margin-bottom: var(--space-sm);
}

.success-note {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  text-align: center;
  line-height: 1.5;
}

// ==================== 底部按钮 ====================

.dialog-footer {
  padding: var(--space-sm) var(--space-md);
}

.next-btn,
.submit-btn,
.confirm-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }

  &.is-disabled {
    background-color: var(--bg-tertiary);

    .next-text,
    .submit-text {
      color: var(--text-tertiary);
    }
  }

  &.is-loading {
    opacity: 0.7;
    pointer-events: none;
  }
}

.next-text,
.submit-text,
.confirm-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-on-brand);
}

// ==================== 底部安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>
