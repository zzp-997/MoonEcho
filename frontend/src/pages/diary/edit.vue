<template>
  <view class="diary-edit-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-back" @tap="handleBack">
        <wd-icon name="arrow-left" class="back-icon" />
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
import {
  useDiary,
  useVoiceInput,
  type EmotionTone,
  type SyncMode,
} from '@/composables/useDiary'
import { trackPageEnter, trackPageLeave, EventName } from '@/utils/tracking'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
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

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('diary_edit')
  },
  onHidden() {
    trackPageLeave('diary_edit')
  }
})
</script>

<style lang="scss" scoped>
.diary-edit-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #FFFFFF;
}

// ==================== 导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 30rpx;
  background: linear-gradient(135deg, #01BEFF, #3D7EFF);
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

.back-icon {
  font-size: 40rpx;
  color: #FFFFFF;
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

.header-action {
  width: 64rpx;
}

// ==================== 内容区 ====================

.page-content {
  flex: 1;
  padding-top: 20rpx;
}

.page-bottom-space {
  height: 40rpx;
}

// ==================== 文字输入区 ====================

.content-input-area {
  padding: 30rpx;
}

.input-hint {
  margin-bottom: 24rpx;
}

.hint-text {
  font-size: 34rpx;
  font-weight: 600;
}

.input-wrapper {
  position: relative;
  min-height: 240rpx;
  background-color: #F8F8FA;
  border-radius: 20rpx;
  padding: 24rpx;
  box-shadow: inset 0rpx 2rpx 8rpx 0rpx rgba(0, 0, 0, 0.04);
}

.content-textarea {
  width: 100%;
  min-height: 240rpx;
  max-height: 720rpx;
  font-size: 30rpx;
  color: #080808;
  line-height: 1.8;
  background-color: transparent;
}

.textarea-placeholder {
  color: #AAAAAA;
}

.char-counter {
  position: absolute;
  right: 20rpx;
  bottom: 20rpx;
}

.counter-text {
  font-size: 22rpx;
  color: #838383;

  &.is-warning { color: #FFBE28; }
  &.is-max { color: #E83A30; }
}

// ==================== 语音输入 ====================

.voice-input-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 24rpx 0;
}

.voice-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background-color: #F4F4F5;

  &.is-recording {
    background: linear-gradient(45deg, #01BEFF, #3D7EFF);
    animation: recordingPulse 1s ease-in-out infinite;
  }
}

.icon-mic {
  font-size: 28rpx;
}

.voice-text {
  font-size: 26rpx;
  color: #838383;
}

@keyframes recordingPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

// ==================== 内容提示 ====================

.content-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 0;
}

.tip-text {
  font-size: 26rpx;
  color: #838383;
}

.content-tip.is-overlong {
  .tip-text { color: #FFBE28; }
}

// ==================== 提交按钮 ====================

.submit-area {
  display: flex;
  align-items: center;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background-color: #FFFFFF;
}

.submit-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: 5000rpx;
  background-color: #F4F4F5;

  &.is-active {
    background: linear-gradient(135deg, #01BEFF, #3D7EFF);
    box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(1, 190, 255, 0.35);

    .btn-text { color: #FFFFFF; }

    &:active {
      transform: scale(0.98);
      transition: transform 0.1s ease-out;
    }
  }

  &.is-loading {
    opacity: 0.7;
    pointer-events: none;
  }
}

.btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #AAAAAA;
}
</style>