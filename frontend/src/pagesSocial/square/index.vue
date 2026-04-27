<template>
  <view class="square-page">
    <!-- 离线提示 -->
    <view v-if="isOffline" class="offline-banner" @tap="handleRetry">
      <text class="offline-icon">⚠</text>
      <text class="offline-text">网络已断开</text>
      <text class="offline-retry">点击重试</text>
    </view>

    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-title">
        <text class="title-text">动态广场</text>
        <text class="title-hint">看看大家在分享什么</text>
      </view>
      <view class="header-actions">
        <view class="action-btn" @tap="handleGoPublish">
          <text class="action-icon">+</text>
        </view>
      </view>
    </view>

    <!-- 筛选条 -->
    <view class="filter-bar">
      <view
        class="filter-item"
        :class="{ 'is-active': sortBy === 'latest' }"
        @tap="handleSortChange('latest')"
      >
        <text class="filter-text">最新</text>
      </view>
      <view
        class="filter-item"
        :class="{ 'is-active': sortBy === 'hot' }"
        @tap="handleSortChange('hot')"
      >
        <text class="filter-text">最热</text>
      </view>
      <view
        class="filter-item"
        :class="{ 'is-active': sortBy === 'following' }"
        @tap="handleSortChange('following')"
      >
        <text class="filter-text">关注</text>
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
        <text class="empty-icon">~</text>
        <text class="empty-text">广场空空的</text>
        <text class="empty-hint">发布一条动态吧</text>
      </view>

      <!-- 加载状态 -->
      <view v-if="isLoading" class="loading-state">
        <wd-loading />
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
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 动态广场信息流主页
 * 文件：src/pagesSocial/square/index.vue
 * 说明：动态广场信息流，顶部筛选条（最新/最热/关注）+ 动态卡片列表
 * 设计要点：支持下拉刷新、上拉加载，实名/匿名动态混合展示
 */

import { ref, onMounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
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
import PostCard from '@/components/square/PostCard.vue'

// ==================== 响应式状态 ====================

/** 动态列表 */
const posts = ref<Post[]>([])

/** 当前排序方式 */
const sortBy = ref<PostSortBy>('latest')

/** 是否正在刷新 */
const isRefreshing = ref(false)

/** 是否正在加载 */
const isLoading = ref(false)

/** 是否有更多数据 */
const hasMore = ref(true)

/** 当前页码 */
const currentPage = ref(1)

/** 每页数量 */
const pageSize = 20

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 是否离线 */
const isOffline = ref(false)

// ==================== 网络状态检测 ====================

/**
 * 检查网络状态
 */
function checkNetworkStatus(): void {
  uni.getNetworkType({
    success: (res) => {
      // networkType 可能为 'wifi', '2g', '3g', '4g', '5g', 'unknown', 'none'
      isOffline.value = res.networkType === 'none'
    },
    fail: () => {
      // 检测失败时假设有网络
      isOffline.value = false
    },
  })
}

/**
 * 处理重试点击
 */
function handleRetry(): void {
  checkNetworkStatus()
  if (!isOffline.value) {
    loadPosts(true)
  }
}

// ==================== 方法 ====================

/**
 * 获取安全区域高度
 */
function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  const bottom = systemInfo.safeAreaInsets?.bottom ?? 0
  safeAreaBottom.value = `${bottom}px`
}

/**
 * 加载动态列表
 */
async function loadPosts(isRefresh = false): Promise<void> {
  if (isLoading.value) return

  if (isRefresh) {
    currentPage.value = 1
    hasMore.value = true
  }

  isLoading.value = true

  try {
    const result = await getPosts({
      page: currentPage.value,
      page_size: pageSize,
      sort_by: sortBy.value,
    })

    if (isRefresh) {
      posts.value = result.data
    } else {
      posts.value = [...posts.value, ...result.data]
    }

    hasMore.value = result.pagination.page < result.pagination.total_pages
  } catch (error) {
    console.error('加载动态列表失败', error)
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
    await loadPosts(true)
  } finally {
    isRefreshing.value = false
    uni.stopPullDownRefresh()
  }
}

/**
 * 处理加载更多
 */
async function handleLoadMore(): Promise<void> {
  if (isLoading.value || !hasMore.value) return

  currentPage.value++
  await loadPosts(false)
}

/**
 * 处理排序方式变更
 */
function handleSortChange(sort: PostSortBy): void {
  sortBy.value = sort
  loadPosts(true)

  track(EventName.SQUARE_SORT_CHANGE, { sort_by: sort })
}

/**
 * 处理动态点击
 */
function handlePostTap(post: Post): void {
  track(EventName.SQUARE_POST_VIEW, { post_id: post.id })

  uni.navigateTo({
    url: `/pagesSocial/square/detail?id=${post.id}`,
  })
}

/**
 * 处理共鸣点击
 */
async function handleResonance(post: Post): Promise<void> {
  try {
    const result = await createResonance(post.id)

    // 更新本地状态
    const index = posts.value.findIndex((p) => p.id === post.id)
    if (index !== -1) {
      posts.value[index] = {
        ...posts.value[index],
        resonance_count: result.resonance_count,
        has_resonated: !result.already_resonated,
      }
    }

    if (!result.already_resonated) {
      uni.showToast({
        title: '已共鸣',
        icon: 'success',
      })
    }

    track(EventName.SQUARE_RESONANCE, {
      post_id: post.id,
      already_resonated: result.already_resonated,
    })
  } catch (error) {
    console.error('创建共鸣失败', error)
    uni.showToast({
      title: '操作失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 处理评论点击
 */
function handleCommentTap(post: Post): void {
  track(EventName.SQUARE_COMMENT_VIEW, { post_id: post.id })

  uni.navigateTo({
    url: `/pagesSocial/square/detail?id=${post.id}&focus=comment`,
  })
}

/**
 * 处理收藏点击
 */
async function handleBookmark(post: Post): Promise<void> {
  try {
    if (post.has_bookmarked) {
      await deleteBookmark(post.id)
    } else {
      const result = await createBookmark(post.id)
    }

    // 更新本地状态
    const index = posts.value.findIndex((p) => p.id === post.id)
    if (index !== -1) {
      const newBookmarkCount = post.has_bookmarked
        ? posts.value[index].bookmark_count - 1
        : posts.value[index].bookmark_count + 1
      posts.value[index] = {
        ...posts.value[index],
        bookmark_count: Math.max(0, newBookmarkCount),
        has_bookmarked: !post.has_bookmarked,
      }
    }

    uni.showToast({
      title: post.has_bookmarked ? '已取消收藏' : '已收藏',
      icon: 'success',
    })

    track(EventName.SQUARE_BOOKMARK, {
      post_id: post.id,
      is_bookmark: !post.has_bookmarked,
    })
  } catch (error) {
    console.error('收藏操作失败', error)
    uni.showToast({
      title: '操作失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 处理悄悄关注点击
 */
async function handleWhisperFollow(post: Post): Promise<void> {
  try {
    const result = await createWhisperFollow(post.id)

    // 更新本地状态
    const index = posts.value.findIndex((p) => p.id === post.id)
    if (index !== -1) {
      posts.value[index] = {
        ...posts.value[index],
        has_whisper_followed: true,
      }
    }

    uni.showToast({
      title: result.already_following ? '已关注' : '已悄悄关注',
      icon: 'success',
    })

    track(EventName.SQUARE_WHISPER_FOLLOW, {
      post_id: post.id,
      author_id: post.author?.id,
    })
  } catch (error) {
    console.error('悄悄关注失败', error)
    uni.showToast({
      title: '操作失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 处理图片预览
 */
function handleImagePreview(post: Post, index: number): void {
  if (!post.image_urls) return

  uni.previewImage({
    urls: post.image_urls,
    current: post.image_urls[index],
  })
}

/**
 * 处理发布页面跳转
 */
function handleGoPublish(): void {
  track(EventName.SQUARE_CREATE_START, { source: 'header_btn' })

  uni.navigateTo({
    url: '/pagesSocial/square/publish',
  })
}

// ==================== 生命周期 ====================

// 网络状态变化回调引用
let networkStatusCallback: UniApp.Callback<any> | null = null

onMounted(() => {
  getSafeArea()
  // 检查网络状态
  checkNetworkStatus()
  // 监听网络状态变化
  networkStatusCallback = uni.onNetworkStatusChange((res) => {
    isOffline.value = !res.isConnected
    // 网络恢复时自动刷新
    if (res.isConnected && posts.value.length === 0) {
      loadPosts(true)
    }
  })
  loadPosts(true)
})

onShow(() => {
  trackPageEnter('square')
  // 检查网络状态
  checkNetworkStatus()
  // 记录最近活跃模块（用于智能高亮）
  try {
    uni.setStorageSync('recent_active_module', 'square')
  } catch (e) {
    console.error('保存最近活跃模块失败', e)
  }
  // 每次显示页面时刷新数据
  loadPosts(true)
})

onHide(() => {
  trackPageLeave('square')
})
</script>

<style lang="scss" scoped>
.square-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

// ==================== 离线提示 ====================

.offline-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 20rpx var(--space-md);
  background-color: #FEF3C7;
  border-bottom: 1px solid #FCD34D;
}

.offline-icon {
  font-size: 28rpx;
  color: #D97706;
}

.offline-text {
  font-size: 26rpx;
  color: #92400E;
}

.offline-retry {
  font-size: 26rpx;
  color: #D97706;
  text-decoration: underline;
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
}

.header-title {
  display: flex;
  flex-direction: column;
}

.title-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.title-hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  background-color: var(--brand-primary);
  border-radius: 50%;

  &:active {
    opacity: 0.9;
  }
}

.action-icon {
  font-size: var(--font-size-lg);
  color: var(--text-on-brand);
}

// ==================== 筛选条 ====================

.filter-bar {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-secondary);
}

.filter-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-md);
  margin-right: var(--space-sm);

  &:active {
    opacity: 0.8;
  }

  &.is-active {
    background-color: var(--brand-primary);
    border-radius: var(--radius-full);

    .filter-text {
      color: var(--text-on-brand);
    }
  }
}

.filter-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding: 0 var(--space-md);
}

// ==================== 动态列表 ====================

.post-list {
  display: flex;
  flex-direction: column;
  margin-top: var(--space-sm);
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
  color: var(--text-tertiary);
}

.empty-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
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
  color: var(--text-tertiary);
  margin-top: var(--space-sm);
}

// ==================== 加载更多 ====================

.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) 0;
}

.load-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 没有更多 ====================

.no-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) 0;
}

.no-more-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>