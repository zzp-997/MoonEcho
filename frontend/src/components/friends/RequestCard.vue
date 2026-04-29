<template>
  <view class="request-card">
    <!-- 用户信息 -->
    <view class="user-info" @tap="handleViewProfile">
      <image
        class="avatar"
        :src="request.requester_avatar_url || defaultAvatar"
        mode="aspectFill"
      />
      <view class="info">
        <text class="nickname">{{ request.requester_nickname }}</text>
        <text class="time">{{ formatTime(request.created_at) }}</text>
      </view>
    </view>

    <!-- 打招呼语 -->
    <view class="greeting-area">
      <text class="greeting-text">{{ request.greeting }}</text>
    </view>

    <!-- 操作按钮 -->
    <view class="actions">
      <view v-if="request.status === 'pending'" class="action-buttons">
        <view class="btn btn-ignore" @tap="handleIgnore">
          <text class="btn-text">忽略</text>
        </view>
        <view class="btn btn-accept" @tap="handleAccept">
          <text class="btn-text">同意</text>
        </view>
      </view>
      <view v-else class="status-tag">
        <text class="status-text" :class="statusClass">{{ statusText }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 好友申请卡片组件
 * 文件：src/components/friends/RequestCard.vue
 * 说明：好友申请卡片，显示申请人信息、打招呼语、操作按钮
 */

import { computed } from 'vue'
import type { FriendRequest } from '@/api/modules/friend'

// ==================== Props ====================

interface Props {
  /** 申请信息 */
  request: FriendRequest
  /** 默认头像 */
  defaultAvatar?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultAvatar: '/static/images/default-avatar.png',
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 查看主页 */
  (e: 'view-profile', request: FriendRequest): void
  /** 同意申请 */
  (e: 'accept', request: FriendRequest): void
  /** 忽略申请 */
  (e: 'ignore', request: FriendRequest): void
}>()

// ==================== 计算属性 ====================

/** 状态文本 */
const statusText = computed(() => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    accepted: '已同意',
    rejected: '已忽略',
  }
  return statusMap[props.request.status] || '未知'
})

/** 状态样式类 */
const statusClass = computed(() => {
  return `status-${props.request.status}`
})

// ==================== 方法 ====================

/**
 * 格式化时间
 */
function formatTime(isoString: string): string {
  if (!isoString) return ''

  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 7) return `${diffDays}天前`

    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day}`
  } catch {
    return ''
  }
}

/**
 * 查看主页
 */
function handleViewProfile(): void {
  emit('view-profile', props.request)
}

/**
 * 同意申请
 */
function handleAccept(): void {
  emit('accept', props.request)
}

/**
 * 忽略申请
 */
function handleIgnore(): void {
  emit('ignore', props.request)
}
</script>

<style lang="scss" scoped>
.request-card {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
}

// ==================== 用户信息 ====================

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-sm);

  &:active {
    opacity: 0.8;
  }
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
  margin-right: var(--space-md);
}

.info {
  display: flex;
  flex-direction: column;
}

.nickname {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 打招呼语 ====================

.greeting-area {
  margin-bottom: var(--space-md);
  padding: var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.greeting-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

// ==================== 操作按钮 ====================

.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius-full);

  &:active {
    opacity: 0.9;
  }
}

.btn-ignore {
  background-color: var(--bg-tertiary);
  border: 1rpx solid var(--border-primary);
}

.btn-accept {
  background-color: var(--brand-primary);
}

.btn-text {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.btn-accept .btn-text {
  color: var(--text-on-brand);
}

.status-tag {
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
}

.status-text {
  font-size: var(--font-size-sm);

  &.status-pending {
    color: var(--mood-warm);
  }

  &.status-accepted {
    color: var(--color-success);
  }

  &.status-rejected {
    color: var(--text-tertiary);
  }
}
</style>