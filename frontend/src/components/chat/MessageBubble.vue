<template>
  <view
    class="message-bubble"
    :class="[
      `message-${message.role}`,
      { 'is-streaming': message.isStreaming }
    ]"
  >
    <!-- AI 头像 -->
    <view v-if="message.role === 'assistant'" class="avatar-area">
      <image
        class="avatar"
        :src="avatarSrc"
        mode="aspectFill"
      />
    </view>

    <!-- 消息内容 -->
    <view class="content-area">
      <!-- AI 名称标签 -->
      <view v-if="message.role === 'assistant'" class="name-tag">
        <text class="name-text">{{ personalityName }}</text>
      </view>

      <!-- 消息气泡 -->
      <view class="bubble" :class="bubbleClass">
        <text class="bubble-text" :user-select="message.role === 'assistant'">
          {{ displayContent }}
        </text>

        <!-- 打字指示器（流式输出时显示） -->
        <view v-if="message.isStreaming" class="typing-indicator">
          <view class="typing-dot" />
          <view class="typing-dot" />
          <view class="typing-dot" />
        </view>
      </view>

      <!-- 时间戳 -->
      <view v-if="showTime" class="time-area">
        <text class="time-text">{{ formatTime(message.createdAt) }}</text>
      </view>
    </view>

    <!-- 用户头像（可选） -->
    <view v-if="message.role === 'user' && showUserAvatar" class="avatar-area user-avatar">
      <image
        class="avatar"
        :src="userAvatar"
        mode="aspectFill"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 消息气泡组件
 * 文件：src/components/chat/MessageBubble.vue
 * 说明：支持用户和 AI 消息显示，流式输出打字指示器效果
 */

import { computed } from 'vue'
import type { ChatMessage } from '@/stores/chat'

// ==================== Props ====================

interface Props {
  /** 消息对象 */
  message: ChatMessage
  /** 是否显示时间 */
  showTime?: boolean
  /** 是否显示用户头像 */
  showUserAvatar?: boolean
  /** 用户头像URL */
  userAvatar?: string
}

const props = withDefaults(defineProps<Props>(), {
  showTime: true,
  showUserAvatar: false,
  userAvatar: '/static/images/default-avatar.png',
})

// ==================== 计算属性 ====================

/** AI 性格名称映射 */
const personalityNames: Record<string, string> = {
  xiaowen: '小温',
  laohei: '老黑',
  ali: '阿理',
}

/** AI 性格头像映射 */
const personalityAvatars: Record<string, string> = {
  xiaowen: '/static/images/ai-xiaowen.png',
  laohei: '/static/images/ai-laohei.png',
  ali: '/static/images/ai-ali.png',
}

/** 显示的 AI 名称 */
const personalityName = computed(() => {
  if (props.message.role !== 'assistant') return ''
  const type = props.message.aiPersonality || 'xiaowen'
  return personalityNames[type] || '小温'
})

/** AI 头像地址 */
const avatarSrc = computed(() => {
  if (props.message.role !== 'assistant') return ''
  const type = props.message.aiPersonality || 'xiaowen'
  return personalityAvatars[type] || personalityAvatars.xiaowen
})

/** 显示的内容 */
const displayContent = computed(() => {
  return props.message.content || ''
})

/** 气泡样式类 */
const bubbleClass = computed(() => {
  const classes: string[] = []

  // 用户消息使用品牌色背景
  if (props.message.role === 'user') {
    classes.push('bubble-user')
  } else {
    classes.push('bubble-ai')

    // 根据 AI 性格添加特定样式
    const type = props.message.aiPersonality || 'xiaowen'
    classes.push(`bubble-${type}`)
  }

  return classes
})

// ==================== 方法 ====================

/**
 * 格式化时间显示
 */
function formatTime(isoString: string): string {
  if (!isoString) return ''

  try {
    const date = new Date(isoString)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()

    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const timeStr = `${hours}:${minutes}`

    if (isToday) {
      return timeStr
    }

    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day} ${timeStr}`
  } catch {
    return ''
  }
}
</script>

<style lang="scss" scoped>
.message-bubble {
  display: flex;
  align-items: flex-start;
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-xs);

  &.message-user {
    flex-direction: row-reverse;
  }

  &.is-streaming {
    .bubble {
      // 流式输出时添加呼吸效果
      animation: breathe 1.5s ease-in-out infinite;
    }
  }
}

// ==================== 头像区域 ====================

.avatar-area {
  flex-shrink: 0;
  width: 80rpx;
  height: 80rpx;
  margin-top: 8rpx;

  &.user-avatar {
    margin-left: var(--space-sm);
  }
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
}

// ==================== 内容区域 ====================

.content-area {
  flex: 1;
  min-width: 0;
  max-width: 80%;
}

.name-tag {
  margin-bottom: 8rpx;

  .message-user & {
    text-align: right;
  }
}

.name-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 气泡样式 ====================

.bubble {
  display: inline-flex;
  flex-direction: column;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-lg);
  word-break: break-word;
  position: relative;

  .message-user & {
    margin-left: auto;
    border-bottom-right-radius: var(--radius-xs);
  }

  .message-assistant & {
    border-bottom-left-radius: var(--radius-xs);
  }
}

.bubble-text {
  font-size: var(--font-size-md);
  line-height: 1.6;
  white-space: pre-wrap;
}

// 用户气泡
.bubble-user {
  background-color: var(--brand-primary);
  color: var(--text-on-brand);
}

// AI 气泡 - 默认
.bubble-ai {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

// AI 气泡 - 小温（温柔粉色）
.bubble-xiaowen {
  background-color: var(--ai-xiaowen-bg);
}

// AI 气泡 - 老黑（冷静蓝色）
.bubble-laohei {
  background-color: var(--ai-laohei-bg);
}

// AI 气泡 - 阿理（可靠绿色）
.bubble-ali {
  background-color: var(--ai-ali-bg);
}

// ==================== 时间显示 ====================

.time-area {
  margin-top: 8rpx;

  .message-user & {
    text-align: right;
  }
}

.time-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 打字指示器 ====================

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6rpx;
  margin-top: 8rpx;
  padding-left: 8rpx;
}

.typing-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background-color: var(--text-tertiary);
  animation: typingBounce 1.4s ease-in-out infinite;

  &:nth-child(1) {
    animation-delay: 0s;
  }

  &:nth-child(2) {
    animation-delay: 0.2s;
  }

  &:nth-child(3) {
    animation-delay: 0.4s;
  }
}

// ==================== 动画 ====================

@keyframes typingBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-8rpx);
    opacity: 1;
  }
}

@keyframes breathe {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.85;
  }
}
</style>
