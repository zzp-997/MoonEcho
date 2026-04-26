<template>
  <view class="container">
    <!-- 顶部导航栏 -->
    <view class="header">
      <view class="header-title">消息</view>
      <view class="header-right">
        <view class="settings-btn" @click="handleGoSettings">
          <wd-icon name="setting" size="20px" color="var(--text-secondary)" />
        </view>
      </view>
    </view>

    <!-- 消息分类 -->
    <view class="message-tabs">
      <view
        class="tab-item"
        :class="{ active: activeTab === 'notification' }"
        @click="activeTab = 'notification'"
      >
        <text class="tab-text">通知</text>
        <view v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</view>
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'system' }"
        @click="activeTab = 'system'"
      >
        <text class="tab-text">系统</text>
      </view>
    </view>

    <!-- 通知列表 -->
    <scroll-view
      v-show="activeTab === 'notification'"
      class="scroll-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <!-- 快捷操作 -->
      <view v-if="hasUnread" class="quick-actions">
        <view class="action-btn" @click="handleMarkAllRead">
          <wd-icon name="check-circle" size="16px" color="var(--brand-primary)" />
          <text class="action-text">全部标记已读</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!isLoading && notificationList.length === 0" class="empty-state">
        <wd-icon name="message" size="64px" color="var(--text-tertiary)" />
        <text class="empty-text">暂无通知</text>
      </view>

      <!-- 通知列表 -->
      <view v-else class="notification-list">
        <view
          v-for="notification in notificationList"
          :key="notification.id"
          class="notification-item"
          :class="{ unread: !notification.is_read }"
          @click="handleNotificationClick(notification)"
        >
          <!-- 左侧未读标记 -->
          <view v-if="!notification.is_read" class="unread-dot" />

          <!-- 图标 -->
          <view class="item-icon" :class="`type-${notification.type}`">
            <wd-icon :name="getNotificationIcon(notification.type)" size="22px" />
          </view>

          <!-- 文字内容 -->
          <view class="item-text">
            <view class="item-header">
              <text class="item-title">{{ notification.title }}</text>
              <text class="item-time">{{ formatTime(notification.created_at) }}</text>
            </view>
            <text class="item-desc">{{ notification.content }}</text>
          </view>

          <!-- 右箭头 -->
          <wd-icon name="arrow-right" size="16px" color="var(--text-tertiary)" />
        </view>

        <!-- 加载更多 -->
        <view v-if="isLoadingMore" class="loading-more">
          <wd-loading size="16px" />
          <text class="loading-text">加载中...</text>
        </view>

        <!-- 没有更多 -->
        <view v-else-if="!hasMore && notificationList.length > 0" class="no-more">
          <text>已经到底了</text>
        </view>
      </view>
    </scroll-view>

    <!-- 系统消息列表 -->
    <scroll-view
      v-show="activeTab === 'system'"
      class="scroll-container"
      scroll-y
    >
      <view class="empty-state">
        <wd-icon name="info-circle" size="64px" color="var(--text-tertiary)" />
        <text class="empty-text">暂无系统消息</text>
      </view>
    </scroll-view>

    <!-- 加载遮罩 -->
    <wd-loading v-if="isLoading && !isRefreshing" class="page-loading" />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 消息页
 * 文件：src/pages/message/index.vue
 * 说明：通知和系统消息入口页面
 */
import { ref, onMounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import { useNotification } from '@/composables/useNotification'
import type { NotificationItem } from '@/api/modules/notification'
import { getNotificationJumpUrl, getNotificationIcon } from '@/api/modules/notification'
import { track, EventName } from '@/utils/tracking'
import { formatRelativeTime } from '@/utils/format'

// ==================== 组合式函数 ====================

const {
  notificationList,
  isLoading,
  isRefreshing,
  isLoadingMore,
  hasMore,
  hasUnread,
  unreadCount,
  refresh,
  loadMore,
  readNotification,
  readAllNotifications,
  startPolling,
  stopPolling
} = useNotification()

// ==================== 响应式状态 ====================

const activeTab = ref<'notification' | 'system'>('notification')

// ==================== 生命周期 ====================

onMounted(() => {
  loadNotifications()
})

onShow(() => {
  track(EventName.PAGE_VIEW, { page: 'message' })
  startPolling(30000)
})

onHide(() => {
  stopPolling()
})

// ==================== 数据加载 ====================

async function loadNotifications() {
  await refresh()
}

async function handleRefresh() {
  await refresh()
  uni.stopPullDownRefresh()
}

async function handleLoadMore() {
  if (hasMore.value && !isLoadingMore.value) {
    await loadMore()
  }
}

// ==================== 点击事件 ====================

async function handleNotificationClick(notification: NotificationItem) {
  await readNotification(notification.id)

  const jumpUrl = getNotificationJumpUrl(notification)

  if (jumpUrl) {
    // 危机干预弹窗特殊处理
    if (notification.type === 'crisis_alert') {
      uni.showModal({
        title: '温馨提示',
        content: '检测到您可能需要帮助，是否查看相关资源？',
        confirmText: '查看',
        cancelText: '暂不需要',
        success: (res) => {
          if (res.confirm) {
            uni.navigateTo({ url: jumpUrl })
          }
        }
      })
    } else {
      uni.navigateTo({ url: jumpUrl })
    }
  }

  track(EventName.NOTIFICATION_CLICK, { type: notification.type })
}

async function handleMarkAllRead() {
  await readAllNotifications()
}

function handleGoSettings() {
  uni.navigateTo({ url: '/pages/notification/settings' })
}

// ==================== 辅助函数 ====================

function formatTime(time: string): string {
  return formatRelativeTime(time)
}
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

// ==================== 头部 ====================

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 32rpx;
  padding-top: var(--status-bar-height, 44rpx);
  background-color: var(--bg-primary);
}

.header-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
}

.settings-btn {
  padding: 16rpx;
}

// ==================== 标签页 ====================

.message-tabs {
  display: flex;
  padding: 0 32rpx;
  border-bottom: 1rpx solid var(--border-primary);
}

.tab-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 24rpx 32rpx;
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  transition: color 0.2s;

  &.active {
    color: var(--text-primary);
    font-weight: 500;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 40rpx;
      height: 4rpx;
      background-color: var(--brand-primary);
      border-radius: 2rpx;
    }
  }
}

.tab-text {
  margin-right: 8rpx;
}

.badge {
  min-width: 32rpx;
  height: 32rpx;
  padding: 0 8rpx;
  font-size: var(--font-size-xs);
  line-height: 32rpx;
  text-align: center;
  color: #fff;
  background-color: var(--color-error);
  border-radius: 16rpx;
}

// ==================== 快捷操作 ====================

.quick-actions {
  display: flex;
  justify-content: flex-end;
  padding: 16rpx 32rpx;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 24rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-full);
}

.action-text {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

// ==================== 滚动容器 ====================

.scroll-container {
  flex: 1;
  height: 0;
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 160rpx 0;
}

.empty-text {
  margin-top: 24rpx;
  font-size: var(--font-size-base);
  color: var(--text-tertiary);
}

// ==================== 通知列表 ====================

.notification-list {
  padding: 0 32rpx 32rpx;
}

.notification-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 24rpx;
  margin-top: 24rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);

  &.unread {
    background-color: var(--bg-secondary);
    border-left: 4rpx solid var(--brand-primary);
  }
}

.unread-dot {
  position: absolute;
  top: 24rpx;
  left: 24rpx;
  width: 12rpx;
  height: 12rpx;
  background-color: var(--brand-primary);
  border-radius: 50%;
}

.item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  margin-right: 20rpx;
  background-color: var(--bg-tertiary);
  border-radius: 50%;

  &.type-crisis_alert,
  &.type-crisis_follow {
    background-color: var(--color-error-bg);
    color: var(--color-error);
  }

  &.type-ai_care {
    background-color: rgba(255, 181, 186, 0.15);
    color: var(--ai-xiaowen);
  }

  &.type-friend_request,
  &.type-friend_accept {
    background-color: rgba(124, 111, 224, 0.1);
    color: var(--brand-primary);
  }

  &.type-treehole_reply {
    background-color: var(--mood-calm-bg);
    color: var(--mood-calm);
  }

  &.type-square_comment,
  &.type-square_like {
    background-color: var(--color-warning-bg);
    color: var(--color-warning);
  }

  &.type-weekly_report {
    background-color: var(--mood-warm-bg);
    color: var(--mood-warm);
  }
}

.item-text {
  flex: 1;
  min-width: 0;
  margin-right: 16rpx;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.item-title {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-time {
  flex-shrink: 0;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.item-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// ==================== 加载状态 ====================

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  padding: 32rpx 0;
}

.loading-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.no-more {
  text-align: center;
  padding: 32rpx 0;
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.page-loading {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>
