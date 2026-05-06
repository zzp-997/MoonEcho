<template>
  <view class="friends-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-left">
        <text class="title">好友</text>
      </view>
      <view class="header-right">
        <view class="action-btn" @tap="handleGoRequests">
          <wd-icon name="add-user" size="22px" color="var(--text-primary)" />
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
        <wd-icon name="user" size="48px" color="var(--text-muted)" custom-style="margin-bottom: var(--space-md)" />
        <text class="empty-text">还没有好友</text>
        <text class="empty-hint">去广场看看，认识新朋友吧</text>
        <view class="empty-action" @tap="handleGoSquare">
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
    <view class="requests-entry" @tap="handleGoRequests" v-if="receiveRequests.length > 0">
      <wd-icon name="add-user" size="18px" color="var(--brand-primary)" custom-style="margin-right: var(--space-sm)" />
      <text class="requests-text">{{ receiveRequests.length }}个新的好友申请</text>
      <wd-icon name="arrow-right" size="14px" color="var(--brand-primary)" />
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
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { getFriends, type Friend } from '@/api/modules/friend'
import { getConversations } from '@/api/modules/chat'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
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

onShow(() => {
  trackPageEnter('friends')
  // 刷新数据
  loadFriends()
})

</script>

<style lang="scss" scoped>
.friends-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-primary);
  border-bottom: 1rpx solid var(--border-standard);
}

.header-left {
  display: flex;
  align-items: center;
}

.title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
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
  font-size: var(--font-size-lg);
}

.unread-dot {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 16rpx;
  height: 16rpx;
  background-color: var(--color-error);
  border-radius: 50%;
}

// ==================== 社交能量 ====================

.energy-section {
  padding: var(--space-sm) var(--space-md);
}

// ==================== 搜索栏 ====================

.search-bar {
  padding: var(--space-sm) var(--space-md);
}

.search-input {
  width: 100%;
  height: 72rpx;
  padding: 0 var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.search-placeholder {
  color: var(--text-muted);
}

// ==================== 好友列表 ====================

.friend-list-container {
  flex: 1;
  padding: 0 var(--space-md);
}

.friend-group {
  margin-bottom: var(--space-md);
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) 0;
}

.group-title {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.group-count {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl) 0;
}

.empty-icon {
  font-size: 64rpx;
  margin-bottom: var(--space-md);
}

.empty-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin-bottom: var(--space-md);
}

.empty-action {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-lg);
  background-color: var(--brand-primary);
  border-radius: var(--radius-full);
}

.action-text {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg) 0;
}

.loading-text {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  margin-top: var(--space-sm);
}

// ==================== 好友申请入口 ====================

.requests-entry {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  margin: var(--space-sm) var(--space-md);
  background-color: var(--brand-light);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.requests-icon {
  font-size: var(--font-size-md);
  margin-right: var(--space-sm);
}

.requests-text {
  flex: 1;
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

.requests-arrow {

// ==================== 安全区 ====================

.safe-bottom {
  height: 100rpx;
}
</style>