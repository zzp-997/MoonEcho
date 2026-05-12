<template>
  <view class="friends-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-left">
        <text class="title">好友</text>
      </view>
      <view class="header-right">
        <view class="action-btn" @tap="handleGoRequests">
          <text style="font-size: 40rpx; color: #FFFFFF;">➕</text>
          <view v-if="unreadRequestCount > 0" class="unread-dot" />
        </view>
      </view>
    </view>

    <!-- 社交能量卡片 -->
    <view class="energy-section">
      <SocialEnergyBar
        :show-activities="false"
        :show-rest-button="false"
      />
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <input
        class="search-input"
        v-model="searchKeyword"
        placeholder="搜索好友"
        placeholder-class="search-placeholder"
        @confirm="handleSearch"
      />
    </view>

    <!-- 好友列表 -->
    <scroll-view
      class="friend-list-container"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
    >
      <!-- AI 好友分组 -->
      <view v-if="aiFriends.length > 0" class="friend-group">
        <view class="group-header">
          <text class="group-title">AI 好友</text>
        </view>
        <FriendItem
          v-for="friend in aiFriends"
          :key="friend.id"
          :friend="friend"
          @tap="handleFriendTap"
        />
      </view>

      <!-- 真实好友分组 -->
      <view v-if="realFriends.length > 0" class="friend-group">
        <view class="group-header">
          <text class="group-title">好友</text>
          <text class="group-count">{{ realFriends.length }}人</text>
        </view>
        <FriendItem
          v-for="friend in filteredFriends"
          :key="friend.id"
          :friend="friend"
          @tap="handleFriendTap"
        />
      </view>

      <!-- 空状态 -->
      <view v-if="!isLoading && friends.length === 0" class="empty-state">
        <view class="empty-icon tn-icon-container tn-gradient-5 tn-shadow-blur">
          <text style="font-size: 60rpx;">👫</text>
        </view>
        <text class="tn-text-bold tn-text-lg tn-margin-top">还没有好友</text>
        <text class="tn-color-gray tn-margin-top-xs tn-text-sm">去广场看看，认识新朋友吧</text>
        <view class="empty-action tn-gradient-5 tn-shadow-blur" @tap="handleGoSquare">
          <text class="action-text">去广场</text>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="isLoading" class="loading-state">
        <wd-loading />
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" />
    </scroll-view>

    <!-- 好友申请入口 -->
    <view class="requests-entry tn-shadow-card" @tap="handleGoRequests" v-if="receiveRequests.length > 0">
      <text style="font-size: 36rpx;">📨</text>
      <text class="requests-text">{{ receiveRequests.length }}个新的好友申请</text>
      <text class="requests-arrow">></text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 好友列表页
 * 文件：src/pages/friends/index.vue
 * 说明：好友列表页，展示好友列表、AI好友、社交能量、搜索好友
 */

import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getFriends, type Friend } from '@/api/modules/friend'
import { getConversations } from '@/api/modules/chat'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import FriendItem from '@/components/friends/FriendItem.vue'
import SocialEnergyBar from '@/components/friends/SocialEnergyBar.vue'

// ==================== 响应式状态 ====================

/** 好友列表 */
const friends = ref<Friend[]>([])

/** 搜索关键词 */
const searchKeyword = ref('')

/** 是否正在加载 */
const isLoading = ref(false)

/** 是否正在刷新 */
const isRefreshing = ref(false)

/** 会话列表（用于显示最后消息） */
const conversations = ref<Map<string, any>>(new Map())

// ==================== 计算属性 ====================

/** AI 好友列表 */
const aiFriends = computed(() => {
  return friends.value.filter((f) => f.is_ai)
})

/** 真实好友列表 */
const realFriends = computed(() => {
  return friends.value.filter((f) => !f.is_ai)
})

/** 过滤后的好友列表 */
const filteredFriends = computed(() => {
  if (!searchKeyword.value.trim()) {
    return realFriends.value
  }

  const keyword = searchKeyword.value.trim().toLowerCase()
  return realFriends.value.filter((f) => {
    return f.nickname.toLowerCase().includes(keyword)
  })
})

/** 未读申请数量 */
const unreadRequestCount = ref(0)

/** 收到的好友申请列表 */
const receiveRequests = ref<any[]>([])

// ==================== 方法 ====================

/**
 * 加载好友列表
 */
async function loadFriends(): Promise<void> {
  if (isLoading.value) return

  isLoading.value = true

  try {
    const response = await getFriends()
    friends.value = response.friends

    // 更新未读消息数
    await loadConversations()
  } catch (error) {
    console.error('加载好友列表失败', error)
    uni.showToast({
      title: '加载失败，请重试',
      icon: 'none',
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 加载会话列表
 */
async function loadConversations(): Promise<void> {
  try {
    const response = await getConversations()
    const map = new Map<string, any>()
    response.conversations.forEach((conv) => {
      map.set(conv.friend_id, conv)
    })
    conversations.value = map

    // 更新好友的最后消息信息
    friends.value = friends.value.map((friend) => {
      const conv = map.get(friend.id)
      if (conv) {
        return {
          ...friend,
          last_message: conv.last_message,
          unread_count: conv.unread_count,
        }
      }
      return friend
    })
  } catch (error) {
    console.error('加载会话列表失败', error)
  }
}

/**
 * 处理刷新
 */
async function handleRefresh(): Promise<void> {
  isRefreshing.value = true

  try {
    await loadFriends()
  } finally {
    isRefreshing.value = false
    uni.stopPullDownRefresh()
  }
}

/**
 * 处理搜索
 */
function handleSearch(): void {
  track(EventName.FRIEND_SEARCH, {
    search_keyword: searchKeyword.value,
  })
}

/**
 * 处理好友点击
 */
function handleFriendTap(friend: Friend): void {
  track(EventName.FRIEND_LIST_VIEW, { friend_id: friend.id })

  // 跳转到私聊页面
  uni.navigateTo({
    url: `/pagesSocial/chat/private?friendId=${friend.id}&nickname=${encodeURIComponent(friend.nickname)}`,
  })
}

/**
 * 跳转到好友申请页
 */
function handleGoRequests(): void {
  uni.navigateTo({
    url: '/pages/friends/requests',
  })
}

/**
 * 跳转到广场
 */
function handleGoSquare(): void {
  uni.navigateTo({
    url: '/pagesSocial/square/index',
  })
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadFriends()
})

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('friends')
    loadFriends()
  }
})

</script>

<style lang="scss" scoped>
.friends-page {
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

.header-left {
  display: flex;
  align-items: center;
}

.title {
  font-size: 40rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.header-right {
  display: flex;
  align-items: center;
}

.action-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.action-icon {
  font-size: 34rpx;
}

.unread-dot {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 16rpx;
  height: 16rpx;
  background-color: #E83A30;
  border-radius: 50%;
}

// ==================== 社交能量 ====================

.energy-section {
  padding: 16rpx 24rpx;
}

// ==================== 搜索栏 ====================

.search-bar {
  padding: 16rpx 24rpx;
}

.search-input {
  width: 100%;
  height: 72rpx;
  padding: 0 24rpx;
  background-color: #F8F8FA;
  border-radius: 5000rpx;
  font-size: 26rpx;
  color: #080808;
}

.search-placeholder {
  color: #838383;
}

// ==================== 好友列表 ====================

.friend-list-container {
  flex: 1;
  padding: 0 24rpx;
}

.friend-group {
  margin-bottom: 24rpx;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 0;
}

.group-title {
  font-size: 26rpx;
  color: #838383;
}

.group-count {
  font-size: 22rpx;
  color: #838383;
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
  margin-bottom: 8rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: #838383;
  margin-bottom: 24rpx;
}

.empty-action {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 30rpx;
  background-color: #01BEFF;
  border-radius: 5000rpx;
}

.action-text {
  font-size: 26rpx;
  color: #FFFFFF;
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

// ==================== 好友申请入口 ====================

.requests-entry {
  display: flex;
  align-items: center;
  padding: 24rpx;
  margin: 16rpx 24rpx;
  background-color: rgba(1,190,255,0.1);
  border-radius: 20rpx;

  &:active {
    opacity: 0.9;
  }
}

.requests-icon {
  font-size: 30rpx;
  margin-right: 16rpx;
}

.requests-text {
  flex: 1;
  font-size: 26rpx;
  color: #01BEFF;
}

.requests-arrow {
  color: #838383;
}

// ==================== 安全区 ====================

.safe-bottom {
  height: 100rpx;
}
</style>