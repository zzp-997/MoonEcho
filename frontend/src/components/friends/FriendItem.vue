<template>
  <view class="friend-item" @tap="handleTap">
    <!-- 头像区域 -->
    <view class="avatar-area">
      <image
        class="avatar"
        :src="friend.avatar_url || defaultAvatar"
        mode="aspectFill"
      />
      <!-- AI 标识 -->
      <view v-if="friend.is_ai" class="ai-badge">
        <text class="ai-text">AI</text>
      </view>
      <!-- 在线状态 -->
      <view
        v-if="!friend.is_ai"
        class="online-dot"
        :class="{ 'is-online': friend.online_status === 'online' }"
        :style="{ backgroundColor: onlineStatusColor }"
      />
    </view>

    <!-- 信息区域 -->
    <view class="info-area">
      <!-- 昵称 -->
      <view class="nickname-row">
        <text class="nickname">{{ friend.nickname }}</text>
        <!-- 画像标签 -->
        <view v-if="friend.personality_tags && friend.personality_tags.length > 0" class="tags">
          <text
            v-for="tag in friend.personality_tags.slice(0, 2)"
            :key="tag"
            class="tag"
          >{{ tag }}</text>
        </view>
      </view>

      <!-- 最后消息 -->
      <view v-if="friend.last_message" class="last-message">
        <text class="message-content">{{ friend.last_message.content }}</text>
        <text class="message-time">{{ formatTime(friend.last_message.created_at) }}</text>
      </view>
      <view v-else class="last-message">
        <text class="message-content empty">暂无消息</text>
      </view>
    </view>

    <!-- 未读数量 -->
    <view v-if="friend.unread_count > 0" class="unread-badge">
      <text class="unread-count">{{ formatUnreadCount(friend.unread_count) }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 好友列表项组件
 * 文件：src/components/friends/FriendItem.vue
 * 说明：好友列表项，显示头像、昵称、在线状态、最后消息、未读数
 */

import { computed } from 'vue'
import type { Friend, FriendOnlineStatus } from '@/api/modules/friend'
import { formatLastMessageTime, getOnlineStatusColor } from '@/api/modules/friend'

// ==================== Props ====================

interface Props {
  /** 好友信息 */
  friend: Friend
  /** 默认头像 */
  defaultAvatar?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultAvatar: '/static/images/default-avatar.png',
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 点击好友 */
  (e: 'tap', friend: Friend): void
}>()

// ==================== 计算属性 ====================

/** 在线状态颜色 */
const onlineStatusColor = computed(() => {
  return getOnlineStatusColor(props.friend.online_status)
})

// ==================== 方法 ====================

/**
 * 格式化时间
 */
function formatTime(isoString: string): string {
  return formatLastMessageTime(isoString)
}

/**
 * 格式化未读数量
 */
function formatUnreadCount(count: number): string {
  if (count > 99) return '99+'
  return String(count)
}

/**
 * 处理点击
 */
function handleTap(): void {
  emit('tap', props.friend)
}
</script>

<style lang="scss" scoped>
.friend-item {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-xs);

  &:active {
    opacity: 0.9;
  }
}

// ==================== 头像区域 ====================

.avatar-area {
  position: relative;
  flex-shrink: 0;
  width: 96rpx;
  height: 96rpx;
  margin-right: var(--space-md);
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
}

.ai-badge {
  position: absolute;
  bottom: -4rpx;
  right: -4rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36rpx;
  height: 36rpx;
  background-color: var(--brand-primary);
  border-radius: 50%;
}

.ai-text {
  font-size: var(--font-size-xs);
  color: var(--text-on-brand);
  font-weight: 600;
}

.online-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  border: 2rpx solid var(--bg-secondary);

  &.is-online {
    animation: pulse 2s ease-in-out infinite;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

// ==================== 信息区域 ====================

.info-area {
  flex: 1;
  min-width: 0;
}

.nickname-row {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.nickname {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-right: var(--space-xs);
}

.tags {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.tag {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  background-color: var(--bg-tertiary);
  padding: 4rpx 12rpx;
  border-radius: var(--radius-xs);
}

.last-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.message-content {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: var(--space-xs);

  &.empty {
    color: var(--text-tertiary);
  }
}

.message-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

// ==================== 未读数量 ====================

.unread-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40rpx;
  height: 40rpx;
  background-color: var(--color-error);
  border-radius: var(--radius-full);
  padding: 4rpx 8rpx;
}

.unread-count {
  font-size: var(--font-size-xs);
  color: var(--text-on-brand);
  font-weight: 600;
}
</style>