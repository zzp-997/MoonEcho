<template>
  <view class="message-input-container" :style="{ paddingBottom: safeAreaBottom }">
    <!-- 工具栏 -->
    <view class="toolbar">
      <!-- 表情按钮 -->
      <view class="tool-btn" @tap="toggleEmoji">
        <text class="iconfont icon-emoji" />
      </view>

      <!-- 换人聊聊按钮 -->
      <view class="tool-btn switch-btn" @tap="handleSwitchPersonality">
        <text class="iconfont icon-switch" />
        <text class="tool-text">换人聊聊</text>
      </view>
    </view>

    <!-- 输入区域 -->
    <view class="input-area">
      <!-- 多行输入框 -->
      <textarea
        v-model="inputText"
        class="input-field"
        :placeholder="placeholder"
        placeholder-class="input-placeholder"
        :maxlength="maxLength"
        :auto-height="true"
        :show-confirm-bar="false"
        :adjust-position="true"
        :cursor-spacing="20"
        :fixed="true"
        :value="inputText"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @confirm="handleSend"
      />

      <!-- 字数统计 -->
      <view v-if="showCount" class="char-count">
        <text class="count-text" :class="{ 'is-warning': nearLimit }">
          {{ inputLength }}/{{ maxLength }}
        </text>
      </view>
    </view>

    <!-- 发送按钮 -->
    <view
      class="send-btn"
      :class="{ 'is-active': canSend, 'is-disabled': isDisabled }"
      @tap="handleSend"
    >
      <text class="send-text">发送</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 消息输入组件
 * 文件：src/components/chat/MessageInput.vue
 * 说明：自适应高度输入框，发送按钮，表情入口，换人聊聊入口
 */

import { ref, computed, watch } from 'vue'

// ==================== Props ====================

interface Props {
  /** 占位文本 */
  placeholder?: string
  /** 最大输入长度 */
  maxLength?: number
  /** 是否禁用 */
  disabled?: boolean
  /** 是否正在发送 */
  sending?: boolean
  /** 初始内容 */
  modelValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '说说你的心事...',
  maxLength: 500,
  disabled: false,
  sending: false,
  modelValue: '',
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 发送消息 */
  (e: 'send', content: string): void
  /** 输入内容变化 */
  (e: 'update:modelValue', value: string): void
  /** 切换表情面板 */
  (e: 'toggle-emoji'): void
  /** 切换 AI 性格 */
  (e: 'switch-personality'): void
  /** 输入框聚焦 */
  (e: 'focus'): void
  /** 输入框失焦 */
  (e: 'blur'): void
}>()

// ==================== 响应式状态 ====================

/** 输入文本 */
const inputText = ref(props.modelValue)

/** 是否聚焦 */
const isFocused = ref(false)

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

// ==================== 计算属性 ====================

/** 输入文本长度 */
const inputLength = computed(() => inputText.value.length)

/** 是否显示字数统计 */
const showCount = computed(() => inputLength.value > 0)

/** 是否接近字数限制 */
const nearLimit = computed(() => inputLength.value > props.maxLength * 0.8)

/** 是否可以发送 */
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && !props.disabled && !props.sending
})

/** 是否禁用状态 */
const isDisabled = computed(() => props.disabled || props.sending)

// ==================== 监听 ====================

watch(
  () => props.modelValue,
  (val) => {
    inputText.value = val
  }
)

watch(inputText, (val) => {
  emit('update:modelValue', val)
})

// ==================== 方法 ====================

/**
 * 处理输入事件
 */
function handleInput(event: any): void {
  inputText.value = event.detail.value
}

/**
 * 处理聚焦事件
 */
function handleFocus(): void {
  isFocused.value = true
  emit('focus')
}

/**
 * 处理失焦事件
 */
function handleBlur(): void {
  isFocused.value = false
  emit('blur')
}

/**
 * 处理发送
 */
function handleSend(): void {
  if (!canSend.value) return

  const content = inputText.value.trim()
  emit('send', content)
  inputText.value = ''
}

/**
 * 切换表情面板
 */
function toggleEmoji(): void {
  emit('toggle-emoji')
  // 收起键盘
  uni.hideKeyboard()
}

/**
 * 切换 AI 性格
 */
function handleSwitchPersonality(): void {
  emit('switch-personality')
}

/**
 * 获取安全区域高度
 */
function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  safeAreaBottom.value = `${systemInfo.safeAreaInsets?.bottom || 0}px`
}

// ==================== 生命周期 ====================

getSafeArea()
</script>

<style lang="scss" scoped>
.message-input-container {
  display: flex;
  align-items: flex-end;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
}

// ==================== 工具栏 ====================

.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-right: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 36rpx;

  &:active {
    background-color: var(--bg-primary);
  }
}

.switch-btn {
  width: auto;
  padding: 0 var(--space-sm);
  gap: 4rpx;
}

.tool-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 输入区域 ====================

.input-area {
  flex: 1;
  position: relative;
  min-height: 72rpx;
  max-height: 240rpx;
  margin-right: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.input-field {
  width: 100%;
  min-height: 72rpx;
  max-height: 240rpx;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-md);
  color: var(--text-primary);
  line-height: 1.5;
  box-sizing: border-box;
}

.input-placeholder {
  color: var(--text-tertiary);
}

// ==================== 字数统计 ====================

.char-count {
  position: absolute;
  right: var(--space-sm);
  bottom: -32rpx;
}

.count-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);

  &.is-warning {
    color: var(--color-warning);
  }
}

// ==================== 发送按钮 ====================

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 72rpx;
  border-radius: var(--radius-lg);
  background-color: var(--bg-tertiary);
  margin-bottom: var(--space-xs);
  transition: all var(--transition-fast);

  &:active {
    transform: scale(0.95);
  }

  &.is-active {
    background-color: var(--brand-primary);

    .send-text {
      color: var(--text-on-brand);
    }
  }

  &.is-disabled {
    opacity: 0.5;
    pointer-events: none;
  }
}

.send-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-tertiary);
}

// ==================== 图标字体（临时）====================

.iconfont {
  font-family: 'iconfont' !important;
  font-style: normal;

  // 表情图标 - 使用 Unicode 替代
  &.icon-emoji::before {
    content: '😊';
    font-family: initial;
  }

  // 切换图标
  &.icon-switch::before {
    content: '↻';
    font-family: initial;
  }
}
</style>
