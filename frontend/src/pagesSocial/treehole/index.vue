<template>
  <view class="treehole-page treehole-force-dark">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-title">
        <text class="title-text">树洞</text>
        <text class="title-hint">把没处说的话丢出来</text>
      </view>
      <view class="header-actions">
        <view class="action-btn" @tap="handleGoPublish">
          <text class="action-icon">+</text>
        </view>
      </view>
    </view>

    <!-- 话题标签筛选 -->
    <TopicFilter
      :selected-tag="selectedTopic"
      @change="handleTopicChange"
    />

    <!-- 内容区域 -->
    <scroll-view
      class="page-content"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
      @scrolltolower="handleLoadMore"
    >
      <!-- 新用户引导发布卡片 -->
      <PublishCard
        @publish="handleQuickPublish"
        @ai-rewrite="handleAiRewrite"
      />

      <!-- 帖子列表 -->
      <view v-if="posts.length > 0" class="post-list">
        <PostCard
          v-for="post in posts"
          :key="post.id"
          :post="post"
          @tap="handlePostTap"
          @resonance="handleResonance"
          @comment="handleCommentTap"
        />
      </view>

      <!-- 空状态 -->
      <view v-else-if="!isLoading" class="empty-state">
        <text class="empty-icon">~</text>
        <text class="empty-text">树洞里空空的</text>
        <text class="empty-hint">做第一个说话的人吧</text>
      </view>

      <!-- 加载状态 -->
      <view v-if="isLoading" class="loading-state">
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
 * 回声 - 树洞信息流主页
 * 文件：src/pages/treehole/index.vue
 * 说明：树洞吐槽区信息流，话题标签筛选 + 帖子列表 + 新用户引导卡片
 * 设计要点：强制暗色主题，不显示精确时间，AI生成小图标替代头像
 */

import { ref, onMounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import {
  getTreeholePosts,
  createTreeholePost,
  createResonance as createResonanceApi,
  type TreeholePost,
  type CreatePostResponse,
} from '@/api/treehole'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
import TopicFilter from '@/components/treehole/TopicFilter.vue'
import PostCard from '@/components/treehole/PostCard.vue'
import PublishCard from '@/components/treehole/PublishCard.vue'

// ==================== 响应式状态 ====================

/** 帖子列表 */
const posts = ref<TreeholePost[]>([])

/** 当前选中话题 */
const selectedTopic = ref<string | null>(null)

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
 * 加载帖子列表
 */
async function loadPosts(isRefresh = false): Promise<void> {
  if (isLoading.value) return

  if (isRefresh) {
    currentPage.value = 1
    hasMore.value = true
  }

  isLoading.value = true

  try {
    const result = await getTreeholePosts({
      page: currentPage.value,
      page_size: pageSize,
      topic_tag: selectedTopic.value,
    })

    if (isRefresh) {
      posts.value = result.data
    } else {
      posts.value = [...posts.value, ...result.data]
    }

    hasMore.value = result.pagination.page < result.pagination.total_pages
  } catch (error) {
    console.error('加载帖子列表失败', error)
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
 * 处理话题变更
 */
function handleTopicChange(topic: string | null): void {
  selectedTopic.value = topic
  loadPosts(true)

  track(EventName.TREEHOLE_TOPIC_FILTER, { topic: topic || 'all' })
}

/**
 * 处理帖子点击
 */
function handlePostTap(post: TreeholePost): void {
  track(EventName.TREEHOLE_POST_VIEW, { post_id: post.id })

  uni.navigateTo({
    url: `/pages/treehole/detail?id=${post.id}`,
  })
}

/**
 * 处理共鸣点击
 */
async function handleResonance(post: TreeholePost): Promise<void> {
  try {
    const result = await createResonanceApi(post.id)

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
        title: '有人懂你',
        icon: 'success',
      })
    }

    track(EventName.TREEHOLE_RESONANCE, {
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
function handleCommentTap(post: TreeholePost): void {
  track(EventName.TREEHOLE_COMMENT_VIEW, { post_id: post.id })

  uni.navigateTo({
    url: `/pages/treehole/detail?id=${post.id}&focus=comment`,
  })
}

/**
 * 处理发布页面跳转
 */
function handleGoPublish(): void {
  track(EventName.TREEHOLE_CREATE_START, { source: 'header_btn' })

  uni.navigateTo({
    url: '/pages/treehole/publish',
  })
}

/**
 * 处理快速发布
 */
async function handleQuickPublish(data: { content: string; topicTag: string | null }): Promise<void> {
  try {
    const result: CreatePostResponse = await createTreeholePost({
      content: data.content,
      topic_tag: data.topicTag,
    })

    // 检查审核反馈
    if (result.audit_feedback) {
      uni.showModal({
        title: '温馨提示',
        content: result.audit_feedback.feedback,
        showCancel: false,
        confirmText: '我知道了',
      })
      return
    }

    // 检查脱敏提醒
    if (result.identity_warning?.has_warning) {
      uni.showToast({
        title: result.identity_warning.warning_message,
        icon: 'none',
        duration: 3000,
      })
    }

    // 将新帖子添加到列表顶部
    if (result.post) {
      posts.value = [result.post, ...posts.value]
    }

    uni.showToast({
      title: '发布成功',
      icon: 'success',
    })

    track(EventName.TREEHOLE_CREATE_SUCCESS, {
      post_id: result.post?.id,
      has_topic: !!data.topicTag,
    })
  } catch (error) {
    console.error('发布失败', error)
    uni.showToast({
      title: '发布失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 处理AI润色
 */
function handleAiRewrite(content: string): void {
  // 跳转到发布页面并传递内容
  uni.navigateTo({
    url: `/pages/treehole/publish?content=${encodeURIComponent(content)}&ai_rewrite=true`,
  })
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
  loadPosts(true)
})

onShow(() => {
  trackPageEnter('treehole')
  // 每次显示页面时刷新数据
  loadPosts(true)
})

onHide(() => {
  trackPageLeave('treehole')
})
</script>

<style lang="scss" scoped>
.treehole-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  // 强制使用暗色主题
  background-color: var(--dark-bg-primary);
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: var(--dark-bg-primary);
  border-bottom: 1px solid var(--dark-border-primary);
}

.header-title {
  display: flex;
  flex-direction: column;
}

.title-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--dark-text-primary);
}

.title-hint {
  font-size: var(--font-size-xs);
  color: var(--dark-text-tertiary);
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

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding: 0 var(--space-md);
}

// ==================== 帖子列表 ====================

.post-list {
  display: flex;
  flex-direction: column;
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
  color: var(--dark-text-tertiary);
}

.empty-text {
  font-size: var(--font-size-md);
  color: var(--dark-text-secondary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--dark-text-tertiary);
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg) 0;
}

.loading-text {
  font-size: var(--font-size-sm);
  color: var(--dark-text-tertiary);
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
  color: var(--dark-text-tertiary);
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
  color: var(--dark-text-tertiary);
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>
