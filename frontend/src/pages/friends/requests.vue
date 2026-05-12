<template>
  <view class="friend-requests-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <wd-icon name="arrow-left" class="back-icon" />
      </view>
      <text class="title">好友申请</text>
      <view class="placeholder" />
    </view>

    <!-- 申请列表 -->
    <scroll-view
      class="requests-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
    >
      <!-- 空状态 -->
      <view v-if="!isLoading && requests.length === 0" class="empty-state">
        <wd-icon name="add-user" class="empty-icon" />
        <text class="empty-text">暂无好友申请</text>
      </view>

      <!-- 申请列表 -->
      <view v-else class="requests-list">
        <RequestCard
          v-for="request in requests"
          :key="request.id"
          :request="request"
          @view-profile="handleViewProfile"
          @accept="handleAccept"
          @ignore="handleIgnore"
        />
      </view>

      <!-- 加载状态 -->
      <view v-if="isLoading" class="loading-state">
        <wd-loading />
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 好友申请通知页
 * 文件：src/pages/friends/requests.vue
 * 说明：收到的好友申请列表，支持同意/忽略操作
 */

import { ref, onMounted } from 'vue'
import {
  getFriendRequests,
  acceptFriendRequest,
  rejectFriendRequest,
  type FriendRequest,
} from '@/api/modules/friend'
import { track, EventName, trackPageEnter } from '@/utils/tracking'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import RequestCard from '@/components/friends/RequestCard.vue'

// ==================== 响应式状态 ====================

/** 申请列表 */
const requests = ref<FriendRequest[]>([])

/** 是否正在加载 */
const isLoading = ref(false)

/** 是否正在刷新 */
const isRefreshing = ref(false)

// ==================== 方法 ====================

/**
 * 加载申请列表
 */
async function loadRequests(): Promise<void> {
  if (isLoading.value) return

  isLoading.value = true

  try {
    const response = await getFriendRequests()
    requests.value = response.requests
  } catch (error) {
    console.error('加载好友申请失败', error)
    uni.showToast({
      title: '加载失败，请重试',
      icon: 'none',
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 处理刷新
 */
async function handleRefresh(): Promise<void> {
  isRefreshing.value = true

  try {
    await loadRequests()
  } finally {
    isRefreshing.value = false
    uni.stopPullDownRefresh()
  }
}

/**
 * 查看主页
 */
function handleViewProfile(request: FriendRequest): void {
  track(EventName.USER_PROFILE_VIEW, { user_id: request.requester_id })

  uni.navigateTo({
    url: `/pages/friends/profile?userId=${request.requester_id}`,
  })
}

/**
 * 同意申请
 */
async function handleAccept(request: FriendRequest): Promise<void> {
  try {
    await acceptFriendRequest(request.id)

    // 更新本地状态
    const index = requests.value.findIndex((r) => r.id === request.id)
    if (index !== -1) {
      requests.value[index] = {
        ...requests.value[index],
        status: 'accepted',
      }
    }

    track(EventName.FRIEND_REQUEST_ACCEPT, { request_id: request.id })

    uni.showToast({
      title: '已添加好友',
      icon: 'success',
    })
  } catch (error: any) {
    console.error('同意好友申请失败', error)
    uni.showToast({
      title: error.message || '操作失败',
      icon: 'none',
    })
  }
}

/**
 * 忽略申请
 */
async function handleIgnore(request: FriendRequest): Promise<void> {
  try {
    await rejectFriendRequest(request.id)

    // 更新本地状态
    const index = requests.value.findIndex((r) => r.id === request.id)
    if (index !== -1) {
      requests.value[index] = {
        ...requests.value[index],
        status: 'rejected',
      }
    }

    track(EventName.FRIEND_REQUEST_REJECT, { request_id: request.id })

    uni.showToast({
      title: '已忽略',
      icon: 'none',
    })
  } catch (error: any) {
    console.error('忽略好友申请失败', error)
    uni.showToast({
      title: error.message || '操作失败',
      icon: 'none',
    })
  }
}

/**
 * 返回
 */
function handleBack(): void {
  uni.navigateBack()
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadRequests()
})

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('friend-requests')
  }
})
</script>

<style lang="scss" scoped>
.friend-requests-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #F8F8FA;
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  padding-top: calc(env(safe-area-inset-top) + 24rpx);
  background: linear-gradient(135deg, #E72F8C, #F360A7);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.back-icon {
  font-size: 34rpx;
  color: #FFFFFF;
}

.title {
  font-size: 34rpx;
  font-weight: 500;
  color: #FFFFFF;
}

.placeholder {
  width: 64rpx;
}

// ==================== 申请列表 ====================

.requests-container {
  flex: 1;
  padding: 24rpx;
}

.requests-list {
  display: flex;
  flex-direction: column;
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 0;
}

.empty-icon {
  font-size: 64rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 30rpx;
  color: #333333;
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30rpx 0;
}

.loading-text {
  font-size: 26rpx;
  color: #838383;
  margin-top: 16rpx;
}

// ==================== 安全区 ====================

.safe-bottom {
  height: 100rpx;
}
</style>