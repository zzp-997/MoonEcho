<template>
  <view class="container">
    <!-- 顶部导航栏 -->
    <view class="header">
      <view class="header-left" @click="handleBack">
        <wd-icon name="arrow-left" size="20px" color="var(--text-primary)" />
      </view>
      <view class="header-title">通知</view>
      <view class="header-right">
        <text
          v-if="hasUnread"
          class="mark-all-btn"
          @click="handleMarkAllRead"
        >
          全部已读
        </text>
        <wd-icon
          name="setting"
          size="20px"
          color="var(--text-secondary)"
          custom-class="settings-icon"
          @click="handleGoSettings"
        />
      </view>
    </view>

    <!-- 通知列表 -->
    <scroll-view
      class="scroll-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <!-- 空状态 -->
      <view v-if="!isLoading && notificationList.length === 0" class="empty-state">
        <wd-icon name="message" size="64px" color="var(--text-muted)" />
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
          @touchstart="handleTouchStart($event, notification.id)"
          @touchmove="handleTouchMove($event, notification.id)"
          @touchend="handleTouchEnd(notification.id)"
        >
          <!-- 左侧未读标记 -->
          <view v-if="!notification.is_read" class="unread-dot" />

          <!-- 内容区域 -->
          <view class="item-content" :style="{ transform: `translateX(${swipeOffset[notification.id] || 0}px)` }">
            <!-- 图标 -->
            <view class="item-icon" :class="`type-${notification.type}`">
              <wd-icon :name="getNotificationIcon(notification.type)" size="24px" />
            </view>

            <!-- 文字内容 -->
            <view class="item-text">
              <view class="item-header">
                <text class="item-title">{{ notification.title }}</text>
                <text class="item-time">{{ formatTime(notification.created_at) }}</text>
              </view>
              <text class="item-desc">{{ notification.content }}</text>
            </view>
          </view>

          <!-- 删除按钮 -->
          <view
            class="delete-btn"
            :style="{ opacity: (swipeOffset[notification.id] || 0) < -30 ? 1 : 0 }"
            @click.stop="handleDelete(notification.id)"
          >
            <wd-icon name="delete" size="20px" color="#fff" />
          </view>
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

    <!-- 加载遮罩 -->
    <wd-loading v-if="isLoading && !isRefreshing" class="page-loading" />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 通知列表页
 * 文件：src/pages/notification/list.vue
 * 说明：展示通知列表，支持下拉刷新、上拉加载、左滑删除、点击跳转
 */
import { ref, reactive, onMounted } from 'vue'
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
  refresh,
  loadMore,
  readNotification,
  readAllNotifications,
  deleteNotification,
  startPolling,
  stopPolling
} = useNotification()

// ==================== 响应式状态 ====================

/** 左滑偏移量 */
const swipeOffset = reactive<Record<string, number>>({})

/** 触摸起始位置 */
const touchStartX = ref(0)

/** 当前滑动的通知ID */
const currentSwipeId = ref<string | null>(null)

// ==================== 生命周期 ====================

onMounted(() => {
  loadNotifications()
})

onShow(() => {
  track(EventName.PAGE_VIEW, { page: 'notification_list' })
  // 开始轮询未读数量
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
  // 标记已读
  await readNotification(notification.id)

  // 重置滑动状态
  delete swipeOffset[notification.id]

  // 获取跳转路径
  const jumpUrl = getNotificationJumpUrl(notification)

  // 跳转处理
  if (jumpUrl) {
    // 危机干预弹窗特殊处理
    if (notification.type === 'crisis_alert' && notification.payload?.crisis) {
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

  // 追踪点击
  track(EventName.PAGE_VIEW, {
    page: 'notification_detail',
    type: notification.type
  })
}

async function handleMarkAllRead() {
  await readAllNotifications()
}

function handleGoSettings() {
  uni.navigateTo({ url: '/pages/notification/settings' })
}

function handleBack() {
  uni.navigateBack()
}

// ==================== 左滑删除 ====================

function handleTouchStart(e: TouchEvent, id: string) {
  touchStartX.value = e.touches[0].clientX
  currentSwipeId.value = id
}

function handleTouchMove(e: TouchEvent, id: string) {
  const moveX = e.touches[0].clientX
  const diff = moveX - touchStartX.value

  // 只允许左滑（负值）
  if (diff < 0) {
    swipeOffset[id] = Math.max(diff, -80)
  } else {
    // 右滑恢复
    swipeOffset[id] = 0
  }
}

function handleTouchEnd(id: string) {
  // 滑动超过一半，显示删除按钮
  if ((swipeOffset[id] || 0) < -40) {
    swipeOffset[id] = -80
  } else {
    swipeOffset[id] = 0
  }
  currentSwipeId.value = null
}

function handleDelete(id: string) {
  deleteNotification(id)
  delete swipeOffset[id]
  uni.showToast({
    title: '已删除',
    icon: 'success',
    duration: 1500
  })
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
  border-bottom: 1rpx solid var(--border-standard);
}

.header-left {
  display: flex;
  align-items: center;
  width: 80rpx;
  height: 88rpx;
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.mark-all-btn {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

.settings-icon {
  padding: 16rpx;
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
  color: var(--text-muted);
}

// ==================== 通知列表 ====================

.notification-list {
  padding: 24rpx 32rpx;
}

.notification-item {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  overflow: hidden;

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

.item-content {
  display: flex;
  flex: 1;
  padding: 24rpx;
  transition: transform 0.15s ease;
}

.item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  margin-right: 24rpx;
  background-color: var(--bg-tertiary);
  border-radius: 50%;

  &.type-crisis_alert,
  &.type-crisis_follow {
    background-color: var(--color-error-bg);
    color: var(--color-error);
  }

  &.type-ai_care {
    background-color: var(--ai-xiaowen-bg);
    color: var(--ai-xiaowen);
  }

  &.type-friend_request,
  &.type-friend_accept {
    background-color: var(--brand-light);
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
  margin-left: 16rpx;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.item-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// ==================== 删除按钮 ====================

.delete-btn {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 100%;
  background-color: var(--color-error);
  opacity: 0;
  transition: opacity 0.15s ease;
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
  color: var(--text-muted);
}

.no-more {
  text-align: center;
  padding: 32rpx 0;
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.page-loading {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>
