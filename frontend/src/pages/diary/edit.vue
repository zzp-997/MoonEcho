<template>
  <view class="diary-edit-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="handleBack">
        <text class="back-icon">←</text>
      </view>
      <view class="header-title">
        <text class="title-text">记录心情</text>
      </view>
      <view class="header-action" />
    </view>

    <!-- 内容区域 -->
    <scroll-view class="page-content" scroll-y>
      <!-- 情绪色调选择器 -->
      <EmotionToneSelector
        v-model="selectedTone"
        @change="handleToneChange"
      />

      <!-- 情绪标签选择器 -->
      <EmotionLabelPicker
        v-if="selectedTone"
        :tone="selectedTone"
        :labels="currentLabelsPool"
        v-model="selectedLabels"
      />

      <!-- 文字输入区 -->
      <view class="content-input-area">
        <!-- 提示语 -->
        <view class="input-hint" :style="{ color: currentToneColor }">
          <text class="hint-text">{{ currentHint }}</text>
        </view>

        <!-- 输入框 -->
        <view class="input-wrapper">
          <textarea
            v-model="contentText"
            class="content-textarea"
            :placeholder="inputPlaceholder"
            placeholder-class="textarea-placeholder"
            :maxlength="2000"
            :auto-height="true"
            :show-confirm-bar="false"
            :adjust-position="true"
            :cursor-spacing="20"
            @input="handleInput"
            @focus="handleFocus"
            @blur="handleBlur"
          />

          <!-- 字数统计 -->
          <view v-if="contentLength > 0" class="char-counter">
            <text class="counter-text" :class="{ 'is-warning': isOverLong, 'is-max': isMaxLength }">
              {{ contentLength }}/2000
            </text>
          </view>
        </view>

        <!-- 语音输入按钮（功能开发中，暂时隐藏） -->
        <!-- <view class="voice-input-btn" @tap="toggleRecording">
          <view class="voice-icon" :class="{ 'is-recording': isRecording }">
            <text class="icon-mic">🎤</text>
          </view>
          <text class="voice-text">{{ isRecording ? `${recordingDuration}s` : '语音输入' }}</text>
        </view> -->

        <!-- 内容提示 -->
        <view v-if="isEmptyContent && selectedTone" class="content-tip">
          <text class="tip-text">写点什么让记录更有意义</text>
        </view>

        <view v-if="isOverLong" class="content-tip is-overlong">
          <text class="tip-text">要不要发给AI朋友聊聊</text>
        </view>
      </view>

      <!-- 底部留白 -->
      <view class="page-bottom-space" />
    </scroll-view>

    <!-- 提交按钮 -->
    <view class="submit-area" :style="{ paddingBottom: safeAreaBottom }">
      <view
        class="submit-btn"
        :class="{ 'is-active': canSubmit, 'is-loading': isSubmitting }"
        @tap="handleSubmit"
      >
        <text class="btn-text">{{ isSubmitting ? '保存中...' : '完成记录' }}</text>
      </view>
    </view>

    <!-- 隐私声明弹窗 -->
    <PrivacyConsentDialog
      :visible="showPrivacyDialog"
      :default-sync-mode="syncMode"
      @confirm="handlePrivacyConfirm"
    />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 日记编辑页
 * 文件：src/pages/diary/edit.vue
 * 说明：情绪日记编辑页面，包含色调选择、标签选择、文字输入
 */

import { ref, computed, onMounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import {
  useDiary,
  useVoiceInput,
  type EmotionTone,
  type SyncMode,
} from '@/composables/useDiary'
import { trackPageEnter, trackPageLeave, EventName } from '@/utils/tracking'
import EmotionToneSelector from '@/components/diary/EmotionToneSelector.vue'
import EmotionLabelPicker from '@/components/diary/EmotionLabelPicker.vue'
import PrivacyConsentDialog from '@/components/diary/PrivacyConsentDialog.vue'

// ==================== 组合式函数 ====================

const {
  // 状态
  selectedTone,
  selectedLabels,
  contentText,
  isSubmitting,
  showPrivacyDialog,
  syncMode,
  // 计算属性
  currentToneColor,
  currentHint,
  currentLabelsPool,
  contentLength,
  canSubmit,
  isEmptyContent,
  isOverLong,
  isMaxLength,
  // 方法
  selectTone,
  toggleLabel,
  handlePrivacyConsent,
  submitDiary,
  initDiaryEditor,
} = useDiary()

const {
  isRecording,
  recordingDuration,
  toggleRecording,
} = useVoiceInput()

// ==================== 本地状态 ====================

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 是否聚焦 */
const isFocused = ref(false)

// ==================== 计算属性 ====================

/** 输入框占位符 */
const inputPlaceholder = computed(() => {
  if (!selectedTone.value) {
    return '先选择一下心情吧...'
  }
  return currentHint.value
})

// ==================== 方法 ====================

/**
 * 处理色调变化（由 EmotionToneSelector 触发）
 * 注意：标签清空逻辑已在 useDiary.selectTone 中处理
 */
function handleToneChange(_tone: EmotionTone): void {
  // 无需手动清空标签，selectTone 已处理
}

/**
 * 处理输入事件
 */
function handleInput(event: any): void {
  contentText.value = event.detail.value
}

/**
 * 处理聚焦事件
 */
function handleFocus(): void {
  isFocused.value = true
}

/**
 * 处理失焦事件
 */
function handleBlur(): void {
  isFocused.value = false
}

/**
 * 处理隐私确认
 */
async function handlePrivacyConfirm(mode: SyncMode): Promise<void> {
  const success = await handlePrivacyConsent(mode)
  if (success) {
    // 确认成功后，如果用户已经选择了色调，继续提交
    if (selectedTone.value) {
      submitDiary()
    }
  }
}

/**
 * 处理提交
 */
async function handleSubmit(): Promise<void> {
  if (!canSubmit.value) {
    if (!selectedTone.value) {
      uni.showToast({
        title: '请先选择情绪色调',
        icon: 'none',
      })
    }
    return
  }

  const success = await submitDiary()
  if (success) {
    // 提交成功，返回上一页
    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  }
}

/**
 * 处理返回
 */
function handleBack(): void {
  // 如果有内容，提示用户是否保存
  if (selectedTone.value || contentText.value.trim()) {
    uni.showModal({
      title: '提示',
      content: '当前内容未保存，确定要离开吗？',
      confirmText: '离开',
      cancelText: '继续编辑',
      success: (res) => {
        if (res.confirm) {
          uni.navigateBack()
        }
      },
    })
  } else {
    uni.navigateBack()
  }
}

/**
 * 获取安全区域高度
 */
function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  // 兼容不同平台的安全区域获取
  const bottom = systemInfo.safeAreaInsets?.bottom ?? 0
  safeAreaBottom.value = `${bottom}px`
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
  initDiaryEditor()
})

onShow(() => {
  trackPageEnter('diary_edit')
})

onHide(() => {
  trackPageLeave('diary_edit')
})
</script>

<style lang="scss" scoped>
.diary-edit-page {
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
  justify-content: center;
  width: 64rpx;
  height: 64rpx;

  &:active {
    opacity: 0.6;
  }
}

.back-icon {
  font-size: 40rpx;
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

.header-action {
  width: 64rpx;
  height: 64rpx;
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding-top: var(--space-sm);
}

.page-bottom-space {
  height: var(--space-xl);
}

// ==================== 文字输入区 ====================

.content-input-area {
  padding: var(--space-md);
}

.input-hint {
  margin-bottom: var(--space-md);
}

.hint-text {
  font-size: var(--font-size-md);
  font-weight: 500;
}

.input-wrapper {
  position: relative;
  min-height: 200rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.content-textarea {
  width: 100%;
  min-height: 200rpx;
  max-height: 600rpx;
  font-size: var(--font-size-md);
  color: var(--text-primary);
  line-height: 1.8;
  background-color: transparent;
}

.textarea-placeholder {
  color: var(--text-tertiary);
}

.char-counter {
  position: absolute;
  right: var(--space-sm);
  bottom: var(--space-sm);
}

.counter-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);

  &.is-warning {
    color: var(--color-warning);
  }

  &.is-max {
    color: var(--color-error);
  }
}

// ==================== 语音输入按钮 ====================

.voice-input-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: var(--space-md) 0;
}

.voice-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
  transition: all var(--transition-fast);

  &.is-recording {
    background-color: var(--brand-primary);
    animation: recordingPulse 1s ease-in-out infinite;
  }
}

.icon-mic {
  font-size: 28rpx;
}

.voice-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

@keyframes recordingPulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

// ==================== 内容提示 ====================

.content-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) 0;
}

.tip-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.content-tip.is-overlong {
  .tip-text {
    color: var(--color-warning);
  }
}

// ==================== 提交按钮 ====================

.submit-area {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border-primary);
}

.submit-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: var(--radius-lg);
  background-color: var(--bg-tertiary);
  transition: all var(--transition-fast);

  &:active {
    transform: scale(0.98);
  }

  &.is-active {
    background-color: var(--brand-primary);

    .btn-text {
      color: var(--text-on-brand);
    }
  }

  &.is-loading {
    opacity: 0.7;
    pointer-events: none;
  }
}

.btn-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-tertiary);
}
</style>