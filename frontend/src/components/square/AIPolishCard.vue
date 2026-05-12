<template>
  <wd-popup
    v-model="visible"
    position="bottom"
    :closeOnClickModal="true"
  >
    <view class="ai-polish-card">
      <!-- 标题区域 -->
      <view class="card-header">
        <text class="card-title">AI 文案润色</text>
        <text class="card-subtitle">让表达更温暖</text>
        <view class="close-btn" @tap="handleClose">
          <text class="close-icon">x</text>
        </view>
      </view>

      <!-- 风格选择 -->
      <view class="style-section">
        <text class="section-label">选择风格</text>
        <view class="style-list">
          <view
            v-for="(label, key) in POLISH_STYLE_LABELS"
            :key="key"
            class="style-item"
            :class="{ 'is-active': selectedStyle === key }"
            @tap="handleStyleSelect(key as PolishStyle)"
          >
            <text class="style-text">{{ label }}</text>
          </view>
        </view>
      </view>

      <!-- 内容对比区域 -->
      <view class="content-section">
        <!-- 原文 -->
        <view class="content-block">
          <text class="block-label">原文</text>
          <text class="block-text original">{{ originalContent }}</text>
        </view>

        <!-- 分隔线 -->
        <view class="divider">
          <text class="divider-text">润色后</text>
        </view>

        <!-- 润色结果 -->
        <view class="content-block polished">
          <view v-if="isLoading" class="loading-state">
            <wd-loading />
            <text class="loading-text">正在润色...</text>
          </view>
          <text v-else class="block-text">{{ polishedContent || '点击下方按钮开始润色' }}</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="action-section">
        <view
          v-if="!isLoading && polishedContent"
          class="action-btn-group"
        >
          <view class="action-btn secondary" @tap="handleKeepOriginal">
            <text class="btn-text">保留原文</text>
          </view>
          <view class="action-btn primary" @tap="handleUsePolished">
            <text class="btn-text">使用润色</text>
          </view>
          <view class="action-btn tertiary" @tap="handleRefresh">
            <text class="btn-text">再换一个</text>
          </view>
        </view>
        <view v-else-if="!isLoading" class="action-btn-group">
          <view class="action-btn primary full" @tap="handlePolish">
            <text class="btn-text">开始润色</text>
          </view>
        </view>
      </view>

      <!-- 底部提示 -->
      <view class="card-footer">
        <text class="footer-hint">润色后会保留你的原意，只是表达更温暖</text>
      </view>
    </view>
  </wd-popup>
</template>

<script setup lang="ts">
/**
 * 回声 - AI 文案润色卡片组件
 * 文件：src/components/square/AIPolishCard.vue
 * 说明：底部弹出��� AI 润色卡片，显示原文和润色版本对比
 * 设计要点：支持三种风格选择，提供保留原文/使用润色/再换一个操作
 */

import { ref, watch } from 'vue'
import { polishContent, POLISH_STYLE_LABELS, type PolishStyle } from '@/api/modules/post'

// ==================== Props ====================

const props = defineProps<{
  /** 是否显示卡片 */
  show: boolean
  /** 原文内容 */
  content: string
}>()

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'use-polished', content: string): void
  (e: 'keep-original'): void
  (e: 'close'): void
}>()

// ==================== 响应式状态 ====================

/** 内部可见状态 */
const visible = ref(false)

/** 原文内容 */
const originalContent = ref('')

/** 润色后的内容 */
const polishedContent = ref('')

/** 选中的风格 */
const selectedStyle = ref<PolishStyle>('warm')

/** 是否正在加载 */
const isLoading = ref(false)

/** 记录已尝试的次数（用于"再换一个"） */
let polishAttempts = 0

// ==================== 监听 ====================

// 监听外部 show 属性
watch(
  () => props.show,
  (newVal) => {
    visible.value = newVal
    if (newVal) {
      originalContent.value = props.content
      polishedContent.value = ''
      polishAttempts = 0
    }
  }
)

// 监听内部 visible 状态，同步到外部
watch(visible, (newVal) => {
  emit('update:show', newVal)
  if (!newVal) {
    emit('close')
  }
})

// ==================== 方法 ====================

/**
 * 处理风格选择
 */
function handleStyleSelect(style: PolishStyle): void {
  selectedStyle.value = style
  // 切换风格后清空润色结果
  polishedContent.value = ''
}

/**
 * 处理开始润色
 */
async function handlePolish(): Promise<void> {
  if (!originalContent.value.trim() || isLoading.value) return

  isLoading.value = true

  try {
    const result = await polishContent({
      content: originalContent.value,
      style: selectedStyle.value,
    })

    polishedContent.value = result.polished_content
    polishAttempts++
  } catch (error) {
    console.error('AI润色失败', error)
    uni.showToast({
      title: '润色失败，请重试',
      icon: 'none',
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 处理再换一个（重新润色）
 */
async function handleRefresh(): Promise<void> {
  if (isLoading.value) return

  isLoading.value = true

  try {
    const result = await polishContent({
      content: originalContent.value,
      style: selectedStyle.value,
    })

    polishedContent.value = result.polished_content
    polishAttempts++

    uni.showToast({
      title: '已生成新版本',
      icon: 'success',
    })
  } catch (error) {
    console.error('AI润色失败', error)
    uni.showToast({
      title: '润色失败，请重试',
      icon: 'none',
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 处理使用润色内容
 */
function handleUsePolished(): void {
  if (polishedContent.value) {
    emit('use-polished', polishedContent.value)
    handleClose()
  }
}

/**
 * 处理保留原文
 */
function handleKeepOriginal(): void {
  emit('keep-original')
  handleClose()
}

/**
 * 处理关闭
 */
function handleClose(): void {
  visible.value = false
}
</script>

<style lang="scss" scoped>
.ai-polish-card {
  display: flex;
  flex-direction: column;
  padding: var(--space-lg);
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

// ==================== 标题区域 ====================

.card-header {
  display: flex;
  flex-direction: column;
  margin-bottom: var(--space-md);
  position: relative;
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.card-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
}

.close-btn {
  position: absolute;
  top: 0;
  right: 0;
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

// ==================== 风格选择 ====================

.style-section {
  margin-bottom: var(--space-md);
}

.section-label {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-sm);
}

.style-list {
  display: flex;
  gap: var(--space-sm);
}

.style-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-primary);

  &:active {
    opacity: 0.8;
  }

  &.is-active {
    background-color: var(--brand-primary);
    border-color: var(--brand-primary);

    .style-text {
      color: var(--text-on-brand);
    }
  }
}

.style-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 内容对比区域 ====================

.content-section {
  display: flex;
  flex-direction: column;
  margin-bottom: var(--space-md);
}

.content-block {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.block-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.block-text {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  line-height: 1.6;
  word-break: break-word;
}

.original {
  opacity: 0.7;
}

.divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) 0;
}

.divider-text {
  font-size: var(--font-size-xs);
  color: var(--brand-primary);
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--brand-light);
  border-radius: var(--radius-full);
}

.polished {
  background-color: var(--brand-light);
  border: 1px solid var(--brand-light);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) 0;
}

.loading-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-top: var(--space-sm);
}

// ==================== 操作按钮 ====================

.action-section {
  margin-bottom: var(--space-md);
}

.action-btn-group {
  display: flex;
  gap: var(--space-sm);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.8;
  }

  &.primary {
    flex: 1;
    background-color: var(--brand-primary);

    .btn-text {
      color: var(--text-on-brand);
    }
  }

  &.secondary {
    flex: 1;
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-primary);

    .btn-text {
      color: var(--text-secondary);
    }
  }

  &.tertiary {
    flex: 0.8;
    background-color: var(--brand-light);

    .btn-text {
      color: var(--brand-primary);
    }
  }

  &.full {
    width: 100%;
  }
}

.btn-text {
  font-size: var(--font-size-base);
  font-weight: 500;
}

// ==================== 底部提示 ====================

.card-footer {
  display: flex;
  justify-content: center;
}

.footer-hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}
</style>