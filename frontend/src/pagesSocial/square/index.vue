<template>
  <view class="square-page">
    <!-- 离线提示 -->
    <view v-if="isOffline" class="offline-banner" @tap="handleRetry">
      <text style="font-size: 36rpx;">⚠️</text>
      <text class="offline-text">网络已断开</text>
      <text class="offline-retry">点击重试</text>
    </view>

    <!-- 顶部导航栏 — 图鸟风格 -->
    <view class="page-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="header-title-area">
        <text class="header-title">动态广场</text>
        <text class="header-hint">看看大家在分享什么</text>
      </view>
      <view class="header-actions">
        <view class="publish-btn tn-shadow-blur tn-gradient-13" @tap="handleGoPublish">
          <text class="publish-btn-text">✏️ 发布</text>
        </view>
      </view>
    </view>

    <!-- 筛选条 — 图鸟胶囊风格 -->
    <view class="filter-bar">
      <view class="filter-scroll">
        <view
          class="filter-item"
          :class="{ 'is-active': sortBy === 'latest' }"
          @tap="handleSortChange('latest')"
        >
          <text class="filter-text">🔥 最新</text>
        </view>
        <view
          class="filter-item"
          :class="{ 'is-active': sortBy === 'hot' }"
          @tap="handleSortChange('hot')"
        >
          <text class="filter-text">⭐ 最热</text>
        </view>
        <view
          class="filter-item"
          :class="{ 'is-active': sortBy === 'following' }"
          @tap="handleSortChange('following')"
        >
          <text class="filter-text">👀 关注</text>
        </view>
      </view>
    </view>

    <!-- 内容区域 -->
    <scroll-view
      class="page-content"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <!-- 动态列表 -->
      <view v-if="posts.length > 0" class="post-list">
        <PostCard
          v-for="post in posts"
          :key="post.id"
          :post="post"
          @tap="handlePostTap"
          @resonance="handleResonance"
          @comment="handleCommentTap"
          @bookmark="handleBookmark"
          @whisper-follow="handleWhisperFollow"
          @image-tap="handleImagePreview(post, $event)"
        />
      </view>

      <!-- 空状态 -->
      <view v-else-if="!isLoading" class="empty-state">
        <view class="empty-icon tn-icon-container tn-gradient-13 tn-shadow-blur">
          <text style="font-size: 60rpx;">🌟</text>
        </view>
        <text class="tn-text-bold tn-text-lg tn-margin-top">广场空空的</text>
        <text class="tn-color-gray tn-margin-top-xs tn-text-sm">发布一条动态吧</text>
      </view>

      <!-- 加载状态 -->
      <view v-if="isLoading" class="loading-state">
        <view class="loading-spinner tn-gradient-1" />
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 加载更多 -->
      <view v-if="hasMore && !isLoading && posts.length > 0" class="load-more">
        <text class="load-text">上拉加载更多</text>
      </view>

      <!-- 没有更多 -->
      <view v-if="!hasMore && posts.length > 0" class="no-more">
        <text class="no-more-text">已经到底了</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </scroll-view>

    <!-- 自定义TabBar -->
    <CustomTabBar />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getPosts,
  createResonance,
  createBookmark,
  deleteBookmark,
  createWhisperFollow,
  deleteWhisperFollow,
  type Post,
  type PostSortBy,
} from '@/api/modules/post'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import PostCard from '@/components/square/PostCard.vue'
import CustomTabBar from '@/components/common/CustomTabBar.vue'

const posts = ref<Post[]>([])
const sortBy = ref<PostSortBy>('latest')
const isRefreshing = ref(false)
const isLoading = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = 20
const safeAreaBottom = ref('0px')
const isOffline = ref(false)

const statusBarHeight = ref(0)
const sysInfo = uni.getSystemInfoSync()
statusBarHeight.value = sysInfo.statusBarHeight || 0

function checkNetworkStatus(): void {
  uni.getNetworkType({
    success: (res) => { isOffline.value = res.networkType === 'none' },
    fail: () => { isOffline.value = false },
  })
}

function handleRetry(): void {
  checkNetworkStatus()
  if (!isOffline.value) loadPosts(true)
}

function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  const bottom = systemInfo.safeAreaInsets?.bottom ?? 0
  safeAreaBottom.value = `${bottom}px`
}

async function loadPosts(isRefresh = false): Promise<void> {
  if (isLoading.value) return
  if (isRefresh) { currentPage.value = 1; hasMore.value = true }
  isLoading.value = true
  try {
    const result = await getPosts({ page: currentPage.value, page_size: pageSize, sort_by: sortBy.value })
    if (isRefresh) posts.value = result.data
    else posts.value = [...posts.value, ...result.data]
    hasMore.value = result.pagination.page < result.pagination.total_pages
  } catch (error) {
    console.error('加载动态列表失败', error)
    uni.showToast({ title: '加载失败，请重试', icon: 'none' })
  } finally { isLoading.value = false }
}

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  try { await loadPosts(true) } finally { isRefreshing.value = false; uni.stopPullDownRefresh() }
}

async function handleLoadMore(): Promise<void> {
  if (isLoading.value || !hasMore.value) return
  currentPage.value++
  await loadPosts(false)
}

function handleSortChange(sort: PostSortBy): void {
  sortBy.value = sort
  loadPosts(true)
  track(EventName.SQUARE_SORT_CHANGE, { sort_by: sort })
}

function handlePostTap(post: Post): void {
  track(EventName.SQUARE_POST_VIEW, { post_id: post.id })
  uni.navigateTo({ url: `/pagesSocial/square/detail?id=${post.id}` })
}

async function handleResonance(post: Post): Promise<void> {
  try {
    const result = await createResonance(post.id)
    const index = posts.value.findIndex((p) => p.id === post.id)
    if (index !== -1) {
      posts.value[index] = { ...posts.value[index], resonance_count: result.resonance_count, has_resonated: !result.already_resonated }
    }
    if (!result.already_resonated) uni.showToast({ title: '已共鸣', icon: 'success' })
    track(EventName.SQUARE_RESONANCE, { post_id: post.id, already_resonated: result.already_resonated })
  } catch { uni.showToast({ title: '操作失败，请重试', icon: 'none' }) }
}

function handleCommentTap(post: Post): void {
  track(EventName.SQUARE_COMMENT_VIEW, { post_id: post.id })
  uni.navigateTo({ url: `/pagesSocial/square/detail?id=${post.id}&focus=comment` })
}

async function handleBookmark(post: Post): Promise<void> {
  try {
    if (post.has_bookmarked) await deleteBookmark(post.id)
    else await createBookmark(post.id)
    const index = posts.value.findIndex((p) => p.id === post.id)
    if (index !== -1) {
      const newCount = post.has_bookmarked ? posts.value[index].bookmark_count - 1 : posts.value[index].bookmark_count + 1
      posts.value[index] = { ...posts.value[index], bookmark_count: Math.max(0, newCount), has_bookmarked: !post.has_bookmarked }
    }
    uni.showToast({ title: post.has_bookmarked ? '已取消收藏' : '已收藏', icon: 'success' })
    track(EventName.SQUARE_BOOKMARK, { post_id: post.id, is_bookmark: !post.has_bookmarked })
  } catch { uni.showToast({ title: '操作失败，请重试', icon: 'none' }) }
}

async function handleWhisperFollow(post: Post): Promise<void> {
  try {
    const result = await createWhisperFollow(post.id)
    const index = posts.value.findIndex((p) => p.id === post.id)
    if (index !== -1) posts.value[index] = { ...posts.value[index], has_whisper_followed: true }
    uni.showToast({ title: result.already_following ? '已关注' : '已悄悄关注', icon: 'success' })
    track(EventName.SQUARE_WHISPER_FOLLOW, { post_id: post.id, author_id: post.author?.id })
  } catch { uni.showToast({ title: '操作失败，请重试', icon: 'none' }) }
}

function handleImagePreview(post: Post, index: number): void {
  if (!post.image_urls) return
  uni.previewImage({ urls: post.image_urls, current: post.image_urls[index] })
}

function handleGoPublish(): void {
  track(EventName.SQUARE_CREATE_START, { source: 'header_btn' })
  uni.navigateTo({ url: '/pagesSocial/square/publish' })
}

let networkStatusCallback: UniApp.Callback<any> | null = null

onMounted(() => {
  getSafeArea()
  networkStatusCallback = uni.onNetworkStatusChange((res) => {
    isOffline.value = !res.isConnected
    if (res.isConnected && posts.value.length === 0) loadPosts(true)
  })
  checkNetworkStatus()
  loadPosts(true)
})

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('square')
    checkNetworkStatus()
    try { uni.setStorageSync('recent_active_module', 'square') } catch {}
    loadPosts(true)
  },
  onHidden() { trackPageLeave('square') }
})
</script>

<style lang="scss" scoped>
.square-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #FFFFFF;
}

// ==================== 离线提示 ====================

.offline-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 20rpx 30rpx;
  background-color: rgba(255, 190, 40, 0.1);
}

.offline-text {
  font-size: 26rpx;
  color: #FFBE28;
}

.offline-retry {
  font-size: 26rpx;
  color: #FFBE28;
  text-decoration: underline;
}

// ==================== 导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 30rpx;
  background-color: #FFFFFF;
}

.header-title-area {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #080808;
}

.header-hint {
  font-size: 22rpx;
  color: #838383;
  margin-top: 2rpx;
}

.header-actions {
  display: flex;
  align-items: center;
}

.publish-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12rpx 28rpx;
  border-radius: 5000rpx;
}

.publish-btn-text {
  color: #FFFFFF;
  font-size: 24rpx;
  font-weight: 600;
}

// ==================== 筛选条 ====================

.filter-bar {
  padding: 12rpx 30rpx;
  background-color: #FFFFFF;
}

.filter-scroll {
  display: flex;
  gap: 16rpx;
}

.filter-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12rpx 28rpx;
  border-radius: 5000rpx;
  background-color: #F4F4F5;

  &:active {
    opacity: 0.8;
  }

  &.is-active {
    background: linear-gradient(45deg, #FBDA61, #F3683A);
    box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(243, 104, 58, 0.3);

    .filter-text {
      color: #FFFFFF;
      font-weight: 600;
    }
  }
}

.filter-text {
  font-size: 26rpx;
  color: #838383;
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding: 0 30rpx;
  box-sizing: border-box;
}

.post-list {
  display: flex;
  flex-direction: column;
  margin-top: 16rpx;
  gap: 20rpx;
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 0;
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  animation: tn-spin 1s linear infinite;
}

@keyframes tn-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 26rpx;
  color: #838383;
  margin-top: 16rpx;
}

// ==================== 加载更多 ====================

.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx 0;
}

.load-text {
  font-size: 26rpx;
  color: #838383;
}

.no-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx 0;
}

.no-more-text {
  font-size: 26rpx;
  color: #AAAAAA;
}

.safe-bottom {
  background-color: transparent;
}
</style>
