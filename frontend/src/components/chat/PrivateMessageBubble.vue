<template>
  <view
    class="message-bubble"
    :class="[
      `message-${isSelf ? 'self' : 'other'}`,
      { 'has-image': message.message_type === 'image' }
    ]"
  >
    <!-- 头像（对方消息显示） -->
    <view v-if="!isSelf" class="avatar-area">
      <image
        class="avatar"
        :src="otherAvatar"
        mode="aspectFill"
      />
    </view>

    <!-- 消息内容 -->
    <view class="content-area">
      <!-- 消息气泡 -->
      <view class="bubble">
        <!-- 文字消息 -->
        <text v-if="message.message_type === 'text'" class="bubble-text" user-select>
          {{ message.content }}
        </text>

        <!-- 图片消息 -->
        <view v-else-if="message.message_type === 'image'" class="bubble-image" @tap="handleImageTap">
          <image
            class="chat-image"
            :src="message.image_url || message.content"
            mode="widthFix"
            :lazy-load="true"
          />
        </view>

        <!-- 发送状态指示器 -->
        <view v-if="isSelf && showStatus" class="status-indicator">
          <text v-if="sendingStatus === 'sending'" class="status-text sending">发送中...</text>
          <text v-else-if="sendingStatus === 'failed'" class="status-text failed">发送失败</text>
        </view>
      </view>

      <!-- 时间戳 -->
      <view v-if="showTime" class="time-area">
        <text class="time-text">{{ formatTime(message.created_at) }}</text>
      </view>
    </view>

    <!-- 头像（自己消息显示） -->
    <view v-if="isSelf" class="avatar-area">
      <image
        class="avatar"
        :src="selfAvatar"
        mode="aspectFill"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 私聊消息气泡组件
 * 文件：src/components/chat/PrivateMessageBubble.vue
 * 说明：私聊消息气泡，支持文字和图片消息
 */

import { computed } from 'vue'
import type { ChatMessage } from '@/api/modules/chat'
import { formatMessageTime } from '@/api/modules/chat'

// ==================== Props ====================

interface Props {
  /** 消息对象 */
  message: ChatMessage
  /** 是否是自己发送的消息 */
  isSelf: boolean
  /** 是否显示时间 */
  showTime?: boolean
  /** 是否显示发送状态 */
  showStatus?: boolean
  /** 发送状态 */
  sendingStatus?: 'sending' | 'sent' | 'failed'
  /** 自己头像 */
  selfAvatar?: string
  /** 对方头像 */
  otherAvatar?: string
}

const props = withDefaults(defineProps<Props>(), {
  showTime: true,
  showStatus: false,
  sendingStatus: 'sent',
  selfAvatar: '/static/images/default-avatar.png',
  otherAvatar: '/static/images/default-avatar.png',
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 点击图片 */
  (e: 'image-tap', imageUrl: string): void
}>()

// ==================== 方法 ====================

/**
 * 格式化时间
 */
function formatTime(isoString: string): string {
  return formatMessageTime(isoString)
}

/**
 * 处理图片点击
 */
function handleImageTap(): void {
  const imageUrl = props.message.image_url || props.message.content
  if (imageUrl) {
    emit('image-tap', imageUrl)
  }
}
</script>

<style lang="scss" scoped>
.message-bubble {
  display: flex;
  align-items: flex-start;
  padding: var(--space-xs) var(--space-md);
  margin-bottom: var(--space-xs);

  &.message-self {
    flex-direction: row-reverse;

    .content-area {
      align-items: flex-end;
    }

    .bubble {
      background-color: var(--brand-primary);
      border-bottom-right-radius: var(--radius-xs);
    }

    .bubble-text {
      color: var(--text-on-brand);
    }
  }

  &.message-other {
    .bubble {
      background-color: var(--bg-secondary);
      border-bottom-left-radius: var(--radius-xs);
    }

    .bubble-text {
      color: var(--text-primary);
    }
  }
}

// ==================== 头像区域 ====================

.avatar-area {
  flex-shrink: 0;
  width: 64rpx;
  height: 64rpx;
  margin-top: 4rpx;
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
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

// ==================== 气泡样式 ====================

.bubble {
  display: inline-flex;
  flex-direction: column;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-lg);
  word-break: break-word;
  position: relative;
}

.bubble-text {
  font-size: var(--font-size-md);
  line-height: 1.6;
  white-space: pre-wrap;
}

// ==================== 图片消息 ====================

.bubble-image {
  display: block;
  max-width: 400rpx;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.chat-image {
  width: 100%;
  display: block;

  &:active {
    opacity: 0.9;
  }
}

// ==================== 发送状态 ====================

.status-indicator {
  margin-top: 8rpx;
}

.status-text {
  font-size: var(--font-size-xs);

  &.sending {
    color: var(--text-tertiary);
  }

  &.failed {
    color: var(--color-error);
  }
}

// ==================== 时间显示 ====================

.time-area {
  margin-top: 8rpx;
}

.time-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}
</style>