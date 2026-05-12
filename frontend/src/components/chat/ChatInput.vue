<template>
  <view class="chat-input-area">
    <!-- AI 辅助提示 -->
    <view v-if="showAIHint" class="ai-hint-bar">
      <view class="hint-content" @tap="handleHintTap">
        <view class="hint-icon-wrapper">
          <text class="hint-icon-text">AI</text>
        </view>
        <text class="hint-text">{{ aiHintText }}</text>
        <text class="hint-arrow">></text>
      </view>
      <view class="hint-close" @tap="handleHintClose">
        <text class="close-icon">×</text>
      </view>
    </view>

    <!-- 输入框区域 -->
    <view class="input-bar">
      <!-- 更多功能按钮 -->
      <view class="more-btn" @tap="handleMoreTap">
        <text class="more-icon">+</text>
      </view>

      <!-- 输入框 -->
      <view class="input-wrapper">
        <textarea
          class="input-field"
          :value="inputContent"
          :placeholder="placeholder"
          :maxlength="maxLength"
          :auto-height="true"
          :cursor-spacing="20"
          :show-confirm-bar="false"
          :adjust-position="true"
          :focus="inputFocus"
          @input="handleInput"
          @focus="handleFocus"
          @blur="handleBlur"
          @confirm="handleConfirm"
        />
        <!-- 语气优化按钮 -->
        <view v-if="inputContent.length > 0" class="polish-btn" @tap="handlePolish">
          <text class="polish-text">优</text>
        </view>
      </view>

      <!-- 发送按钮 -->
      <view
        class="send-btn"
        :class="{ 'is-active': canSend }"
        @tap="handleSend"
      >
        <text class="send-text">发送</text>
      </view>
    </view>

    <!-- 更多功能面板 -->
    <view v-if="showMorePanel" class="more-panel">
      <view class="panel-item" @tap="handleChooseImage">
        <view class="panel-icon-wrapper">
          <text class="panel-icon-text">图</text>
        </view>
        <text class="panel-label">图片</text>
      </view>
      <view class="panel-item" @tap="handleChooseCamera">
        <view class="panel-icon-wrapper">
          <text class="panel-icon-text">拍</text>
        </view>
        <text class="panel-label">拍照</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 私聊输入框组件
 * 文件：src/components/chat/ChatInput.vue
 * 说明：私聊输入框，支持文字输入、图片发送、AI辅助
 */

import { ref, computed, watch } from 'vue'
import { useChatAssist } from '@/composables/useChatAssist'

// ==================== Props ====================

interface Props {
  /** 会话ID */
  conversationId: string
  /** 占位文本 */
  placeholder?: string
  /** 最大长度 */
  maxLength?: number
  /** 是否显示AI提示 */
  showAIHint?: boolean
  /** AI提示文本 */
  aiHintText?: string
  /** 是否禁用 */
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '输入消息...',
  maxLength: 500,
  showAIHint: false,
  aiHintText: 'AI帮我想想话题',
  disabled: false,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 发送文字消息 */
  (e: 'send', content: string): void
  /** 发送图片消息 */
  (e: 'send-image', imageUrl: string): void
  /** 语气优化 */
  (e: 'polish', content: string): void
  /** 点击AI提示 */
  (e: 'ai-hint-tap'): void
  /** 关闭AI提示 */
  (e: 'ai-hint-close'): void
  /** 输入状态变化 */
  (e: 'typing', isTyping: boolean): void
}>()

// ==================== 响应式状态 ====================

/** 输入内容 */
const inputContent = ref('')

/** 输入框焦点 */
const inputFocus = ref(false)

/** 是否显示更多面板 */
const showMorePanel = ref(false)

// ==================== 计算属性 ====================

/** 是否可以发送 */
const canSend = computed(() => {
  return inputContent.value.trim().length > 0 && !props.disabled
})

// ==================== 方法 ====================

/**
 * 处理输入变化
 */
function handleInput(event: any): void {
  inputContent.value = event.detail.value

  // 发送输入状态
  emit('typing', true)
}

/**
 * 处理输入框聚焦
 */
function handleFocus(): void {
  inputFocus.value = true
}

/**
 * 处理输入框失焦
 */
function handleBlur(): void {
  inputFocus.value = false
  emit('typing', false)
}

/**
 * 处理确认发送
 */
function handleConfirm(): void {
  if (canSend.value) {
    handleSend()
  }
}

/**
 * 处理发送按钮点击
 */
function handleSend(): void {
  if (!canSend.value) return

  const content = inputContent.value.trim()
  emit('send', content)
  inputContent.value = ''
}

/**
 * 处理更多按钮点击
 */
function handleMoreTap(): void {
  showMorePanel.value = !showMorePanel.value
}

/**
 * 处理选择图片
 */
function handleChooseImage(): void {
  showMorePanel.value = false

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album'],
    success: (res) => {
      const tempFilePath = res.tempFilePaths[0]
      emit('send-image', tempFilePath)
    },
    fail: (err) => {
      console.error('选择图片失败', err)
    },
  })
}

/**
 * 处理拍照
 */
function handleChooseCamera(): void {
  showMorePanel.value = false

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['camera'],
    success: (res) => {
      const tempFilePath = res.tempFilePaths[0]
      emit('send-image', tempFilePath)
    },
    fail: (err) => {
      console.error('拍照失败', err)
    },
  })
}

/**
 * 处理语气优化点击
 */
async function handlePolish(): Promise<void> {
  if (!inputContent.value.trim()) return

  emit('polish', inputContent.value.trim())
}

/**
 * 处理AI提示点击
 */
function handleHintTap(): void {
  emit('ai-hint-tap')
}

/**
 * 处理关闭AI提示
 */
function handleHintClose(): void {
  emit('ai-hint-close')
}

/**
 * 设置输入内容（用于外部设置建议内容）
 */
function setInputContent(content: string): void {
  inputContent.value = content
}

/**
 * 获取输入框焦点
 */
function focusInput(): void {
  inputFocus.value = true
}

/**
 * 清除输入内容
 */
function clearInput(): void {
  inputContent.value = ''
}
</script>

<style lang="scss" scoped>
.chat-input-area {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  padding-bottom: var(--space-xs);
}

// ==================== AI 提示 ====================

.ai-hint-bar {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--brand-light);
  border-top: 1rpx solid var(--border-primary);
}

.hint-content {
  display: flex;
  align-items: center;
  flex: 1;

  &:active {
    opacity: 0.8;
  }
}

.hint-icon-wrapper {
  width: 36rpx;
  height: 36rpx;
  border-radius: var(--radius-xs);
  background-color: var(--brand-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-xs);
}

.hint-icon-text {
  font-size: 18rpx;
  font-weight: 600;
  color: var(--text-inverse);
}

.hint-text {
  font-size: var(--font-size-sm);
  color: var(--brand-light);
}

.hint-arrow {
  font-size: var(--font-size-sm);
  color: var(--brand-light);
  margin-left: var(--space-xs);
}

.hint-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40rpx;
  height: 40rpx;

  &:active {
    opacity: 0.8;
  }
}

.close-icon {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
}

// ==================== 输入栏 ====================

.input-bar {
  display: flex;
  align-items: flex-end;
  padding: var(--space-sm) var(--space-md);
  gap: var(--space-sm);
}

.more-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.more-icon {
  font-size: var(--font-size-lg);
  color: var(--text-secondary);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  flex: 1;
  min-width: 0;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-xs) var(--space-sm);
}

.input-field {
  flex: 1;
  min-width: 0;
  min-height: 64rpx;
  max-height: 200rpx;
  font-size: var(--font-size-md);
  color: var(--text-primary);
  background-color: transparent;
  line-height: 1.5;
}

.polish-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;

  &:active {
    opacity: 0.8;
  }
}

.polish-text {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--brand-primary);
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96rpx;
  height: 64rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }

  &.is-active {
    background-color: var(--brand-primary);
  }
}

.send-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.send-btn.is-active .send-text {
  color: var(--text-on-brand);
}

// ==================== 更多面板 ====================

.more-panel {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-top: 1rpx solid var(--border-primary);
}

.panel-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 120rpx;
  margin-right: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.panel-icon-wrapper {
  width: 64rpx;
  height: 64rpx;
  border-radius: var(--radius-sm);
  background-color: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-xs);
}

.panel-icon-text {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-secondary);
}

.panel-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}
</style>