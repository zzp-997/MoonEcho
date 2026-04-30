<template>
  <view class="user-profile-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <text class="back-icon">&lt;</text>
      </view>
      <text class="title">个人主页</text>
      <view class="more-btn" @tap="handleShowMoreActions">
        <text class="more-icon">[...]</text>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="isLoading" class="loading-area">
      <wd-loading />
    </view>

    <!-- 用户信息卡片 -->
    <view v-else-if="userInfo" class="user-card">
      <image
        class="user-avatar"
        :src="userInfo.avatar_url || defaultAvatar"
        mode="aspectFill"
        @tap="handleViewAvatar"
      />
      <text class="user-nickname">{{ userInfo.nickname || '回声用户' }}</text>

      <!-- AI画像标签 -->
      <view v-if="visibleTags.length > 0" class="user-tags">
        <view class="tags-header">
          <text class="tags-title">AI画像</text>
        </view>
        <view class="tags-list">
          <text
            v-for="tag in visibleTags"
            :key="tag.tag_type + tag.tag_value"
            class="user-tag"
            :class="getTagClass(tag.tag_type)"
          >{{ tag.tag_value }}</text>
        </view>
      </view>

      <!-- 无标签 -->
      <view v-else class="no-tags">
        <text class="no-tags-text">暂无公开画像标签</text>
      </view>
    </view>

    <!-- 公开动态 -->
    <view v-if="publicPosts.length > 0" class="posts-section">
      <text class="section-title">Ta的公开动态</text>
      <view class="posts-list">
        <view
          v-for="post in publicPosts"
          :key="post.post_id"
          class="post-item"
          @tap="handleViewPost(post)"
        >
          <text class="post-content">{{ post.content }}</text>
          <view v-if="post.image_urls && post.image_urls.length > 0" class="post-images">
            <image
              v-for="(url, idx) in post.image_urls.slice(0, 3)"
              :key="idx"
              class="post-image"
              :src="url"
              mode="aspectFill"
            />
          </view>
          <view class="post-meta">
            <view class="post-stats">
              <text class="stat-item">{{ post.like_count }} 共鸣</text>
              <text class="stat-item">{{ post.comment_count }} 评论</text>
            </view>
            <text class="post-time">{{ formatPostTime(post.created_at) }}</text>
          </view>
        </view>
      </view>

      <!-- 加载更多 -->
      <view v-if="hasMorePosts" class="load-more" @tap="loadMorePosts">
        <text class="load-more-text">查看更多动态</text>
      </view>
    </view>

    <!-- 无动态提示 -->
    <view v-else-if="!isLoading" class="empty-posts">
      <text class="empty-text">暂无公开动态</text>
    </view>

    <!-- 操作按钮区域 -->
    <view v-if="userInfo" class="action-area">
      <!-- 已是好友 -->
      <view v-if="isFriend" class="friend-status">
        <view class="status-badge">
          <text class="status-icon">[已好友]</text>
        </view>
        <text class="status-text">你们已是好友</text>
        <view class="chat-btn" @tap="handleStartChat">
          <text class="chat-text">发消息</text>
        </view>
      </view>

      <!-- 有待处理的申请 -->
      <view v-else-if="hasPendingRequest" class="pending-status">
        <view class="pending-btn" disabled>
          <text class="pending-text">已发送好友申请</text>
        </view>
      </view>

      <!-- 发送好友申请 -->
      <view v-else class="action-btn primary" @tap="handleSendRequest">
        <text class="btn-text">发送好友申请</text>
      </view>
    </view>

    <!-- 更多操作弹窗 -->
    <wd-action-sheet v-model="showMoreActions" title="更多操作">
      <view class="more-options">
        <view v-if="isFriend" class="more-option danger" @tap="handleDeleteFriend">
          <text class="option-icon">[删除]</text>
          <text class="option-text">删除好友</text>
        </view>
        <view v-if="!isBlocked" class="more-option" @tap="handleBlock">
          <text class="option-icon">[拉黑]</text>
          <text class="option-text">拉黑该用户</text>
        </view>
        <view v-else class="more-option" @tap="handleUnblock">
          <text class="option-icon">[取消]</text>
          <text class="option-text">取消拉黑</text>
        </view>
        <view class="more-option danger" @tap="handleReport">
          <text class="option-icon">[举报]</text>
          <text class="option-text">举报用户</text>
        </view>
      </view>
    </wd-action-sheet>

    <!-- 举报弹窗 -->
    <ReportDialog
      :show="showReportDialog"
      :target="reportTarget"
      @update:show="showReportDialog = $event"
      @success="handleReportSuccess"
    />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 查看他人主页
 * 文件：src/pages/friends/profile.vue
 * 说明：查看他人公开信息，支持加好友、拉黑等操作
 */

import { ref, computed, onMounted } from 'vue'
import {
  getUserPublicInfo,
  getUserPublicPosts,
  type UserPublicInfo,
  type PublicPostItem,
  type ProfileTagItem,
} from '@/api/modules/user'
import {
  deleteFriend,
  blockUser,
  unblockUser,
  getUserPublicProfile,
  type UserPublicProfile,
} from '@/api/modules/friend'
import { track, EventName } from '@/utils/tracking'
import ReportDialog from '@/components/common/ReportDialog.vue'
import { ReportContentType, type ReportTarget } from '@/api/modules/report'

// ==================== 响应式状态 ====================

/** 用户ID */
const userId = ref('')

/** 用户公开信息 */
const userInfo = ref<UserPublicInfo | null>(null)

/** 好友关系状态 */
const friendProfile = ref<UserPublicProfile | null>(null)

/** 公开动态列表 */
const publicPosts = ref<PublicPostItem[]>([])

/** 是否正在加载 */
const isLoading = ref(false)

/** 分页信息 */
const currentPage = ref(1)
const hasMorePosts = ref(false)

/** 默认头像 */
const defaultAvatar = '/static/images/default-avatar.png'

/** 是否是好友 */
const isFriend = ref(false)

/** 是否被拉黑 */
const isBlocked = ref(false)

/** 是否有待处理的好友申请 */
const hasPendingRequest = ref(false)

/** 更多操作弹窗 */
const showMoreActions = ref(false)

/** 举报弹窗 */
const showReportDialog = ref(false)

/** 举报目标 */
const reportTarget = ref<ReportTarget | null>(null)

// ==================== 计算属性 ====================

/** 可见的画像标签（只显示对他人可见的） */
const visibleTags = computed(() => {
  if (!userInfo.value?.profile_tags) return []
  return userInfo.value.profile_tags.filter(tag => tag.is_visible !== false)
})

// ==================== 方法 ====================

/**
 * 加载用户信息
 */
async function loadUserInfo(): Promise<void> {
  if (!userId.value) return

  isLoading.value = true

  try {
    // 并行加载用户信息和公开动态
    const [userRes, postsRes] = await Promise.all([
      getUserPublicInfo(userId.value),
      getUserPublicPosts(userId.value, 1, 5),
    ])

    userInfo.value = userRes
    publicPosts.value = postsRes.data || []
    hasMorePosts.value = postsRes.has_more || false
    currentPage.value = postsRes.page || 1

    // 获取好友状态
    try {
      const friendRes = await getUserPublicProfile(userId.value)
      friendProfile.value = friendRes
      isFriend.value = friendRes.is_friend
      isBlocked.value = friendRes.is_blocked
      hasPendingRequest.value = friendRes.has_pending_request
    } catch {
      // 忽略好友状态获取失败
    }

    track(EventName.USER_PROFILE_VIEW, { user_id: userId.value })
  } catch (error) {
    console.error('获取用户信息失败', error)
    uni.showToast({
      title: '获取信息失败',
      icon: 'none',
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 获取标签样式类
 */
function getTagClass(tagType: string): string {
  const classMap: Record<string, string> = {
    emotion_pattern: 'tag-emotion',
    social_preference: 'tag-social',
    interest: 'tag-interest',
  }
  return classMap[tagType] || ''
}

/**
 * 加载更多动态
 */
async function loadMorePosts(): Promise<void> {
  if (!userId.value || !hasMorePosts.value) return

  try {
    const nextPage = currentPage.value + 1
    const response = await getUserPublicPosts(userId.value, nextPage, 5)

    publicPosts.value.push(...response.data)
    hasMorePosts.value = response.has_more
    currentPage.value = response.page
  } catch (error) {
    console.error('加载更多动态失败', error)
  }
}

/**
 * 格式化动态时间
 */
function formatPostTime(isoString: string): string {
  if (!isoString) return ''

  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays}天前`

    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}/${day}`
  } catch {
    return ''
  }
}

/**
 * 查看头像
 */
function handleViewAvatar(): void {
  if (userInfo.value?.avatar_url) {
    uni.previewImage({
      urls: [userInfo.value.avatar_url],
    })
  }
}

/**
 * 查看动态详情
 */
function handleViewPost(post: PublicPostItem): void {
  uni.navigateTo({
    url: `/pagesSocial/square/detail?postId=${post.post_id}`,
  })
}

/**
 * 发送好友申请
 */
function handleSendRequest(): void {
  uni.navigateTo({
    url: `/pages/friends/request?userId=${userId.value}`,
  })
}

/**
 * 开始私聊
 */
function handleStartChat(): void {
  uni.navigateTo({
    url: `/pagesSocial/chat/private?userId=${userId.value}`,
  })
}

/**
 * 显示更多操作
 */
function handleShowMoreActions(): void {
  showMoreActions.value = true
}

/**
 * 删除好友
 */
async function handleDeleteFriend(): Promise<void> {
  showMoreActions.value = false

  uni.showModal({
    title: '确认删除',
    content: '确定要删除好友吗？删除后对方将无法继续和你聊天。',
    confirmColor: '#F87171',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteFriend(userId.value)

          track(EventName.FRIEND_DELETE, { friend_id: userId.value })

          uni.showToast({
            title: '已删除好友',
            icon: 'success',
          })

          isFriend.value = false
        } catch (error: any) {
          console.error('删除好友失败', error)
          uni.showToast({
            title: error.message || '操作失败',
            icon: 'none',
          })
        }
      }
    },
  })
}

/**
 * 拉黑用户
 */
async function handleBlock(): Promise<void> {
  showMoreActions.value = false

  uni.showModal({
    title: '确认拉黑',
    content: '拉黑后，对方将无法给你发送消息，也无法看到你的动态。',
    success: async (res) => {
      if (res.confirm) {
        try {
          await blockUser(userId.value)

          track(EventName.USER_BLOCK, { user_id: userId.value })

          uni.showToast({
            title: '已拉黑',
            icon: 'success',
          })

          isBlocked.value = true
        } catch (error: any) {
          console.error('拉黑用户失败', error)
          uni.showToast({
            title: error.message || '操作失败',
            icon: 'none',
          })
        }
      }
    },
  })
}

/**
 * 取消拉黑
 */
async function handleUnblock(): Promise<void> {
  showMoreActions.value = false

  try {
    await unblockUser(userId.value)

    track(EventName.USER_UNBLOCK, { user_id: userId.value })

    uni.showToast({
      title: '已取消拉黑',
      icon: 'success',
    })

    isBlocked.value = false
  } catch (error: any) {
    console.error('取消拉黑失败', error)
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

/**
 * 举报用户
 */
function handleReport(): void {
  showMoreActions.value = false

  reportTarget.value = {
    contentType: ReportContentType.USER,
    userId: userId.value,
  }
  showReportDialog.value = true
}

/**
 * 举报成功回调
 */
function handleReportSuccess(): void {
  track(EventName.USER_REPORT, { user_id: userId.value })
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 获取页面参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = (currentPage as any).options || {}

  userId.value = options.userId || ''

  if (userId.value) {
    loadUserInfo()
  }
})
</script>

<style lang="scss" scoped>
.user-profile-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
  padding-bottom: env(safe-area-inset-bottom);
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  padding-top: calc(env(safe-area-inset-top) + var(--space-md));
  background-color: var(--bg-primary);
  border-bottom: 1rpx solid var(--border-primary);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.back-icon {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

.title {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-primary);
}

.more-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.more-icon {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

// ==================== 加载状态 ====================

.loading-area {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
}

// ==================== 用户信息卡片 ====================

.user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-xl) var(--space-md);
  margin: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.user-avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
  margin-bottom: var(--space-md);
}

.user-nickname {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

// ==================== AI画像标签 ====================

.user-tags {
  width: 100%;
}

.tags-header {
  margin-bottom: var(--space-sm);
}

.tags-title {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-xs);
}

.user-tag {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background-color: var(--bg-tertiary);
  padding: 8rpx 16rpx;
  border-radius: var(--radius-full);

  &.tag-emotion {
    background-color: rgba(251, 146, 60, 0.15);
    color: #fb923c;
  }

  &.tag-social {
    background-color: rgba(96, 165, 250, 0.15);
    color: #60a5fa;
  }

  &.tag-interest {
    background-color: rgba(124, 111, 224, 0.15);
    color: var(--brand-primary);
  }
}

.no-tags {
  padding: var(--space-sm) 0;
}

.no-tags-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 公开动态 ====================

.posts-section {
  padding: var(--space-md);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.post-item {
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.post-content {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: var(--space-sm);
}

.post-images {
  display: flex;
  gap: 8rpx;
  margin-bottom: var(--space-sm);
}

.post-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: var(--radius-sm);
  background-color: var(--bg-tertiary);
}

.post-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.post-stats {
  display: flex;
  gap: var(--space-sm);
}

.stat-item {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.post-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md);
  margin-top: var(--space-sm);

  &:active {
    opacity: 0.9;
  }
}

.load-more-text {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

// ==================== 空状态 ====================

.empty-posts {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
}

.empty-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 操作按钮 ====================

.action-area {
  padding: var(--space-lg) var(--space-md);
  margin-top: auto;
}

.friend-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.status-badge {
  margin-bottom: var(--space-sm);
}

.status-icon {
  font-size: var(--font-size-xl);
  color: var(--color-success);
}

.status-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-lg);
  background-color: var(--brand-primary);
  border-radius: var(--radius-full);

  &:active {
    opacity: 0.9;
  }
}

.chat-text {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);
}

.pending-status {
  display: flex;
  justify-content: center;
}

.pending-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  width: 100%;
}

.pending-text {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.btn-text {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-on-brand);
}

// ==================== 更多操作 ====================

.more-options {
  padding: var(--space-md);
  padding-bottom: calc(env(safe-area-inset-bottom) + var(--space-md));
}

.more-option {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);

  &:active {
    background-color: var(--bg-tertiary);
  }

  &.danger .option-text {
    color: var(--color-error);
  }
}

.option-icon {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-right: var(--space-sm);
}

.option-text {
  font-size: var(--font-size-md);
  color: var(--text-primary);
}
</style>