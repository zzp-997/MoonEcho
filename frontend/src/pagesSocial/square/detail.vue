<template>
  <view class="detail-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <text class="back-icon">&lt;</text>
      </view>
      <text class="header-title">动态详情</text>
      <view v-if="post?.author?.is_me" class="header-actions">
        <view class="action-btn" @tap="handleDelete">
          <text class="action-text">删除</text>
        </view>
      </view>
      <view v-else class="header-actions">
        <view class="action-btn" @tap="handleShowMoreActions">
          <text class="more-icon">...</text>
        </view>
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="isLoading" class="loading-state">
      <wd-loading />
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 内容区域 -->
    <scroll-view v-else-if="post" class="page-content" scroll-y>
      <!-- 动态详情 -->
      <view class="post-detail">
        <!-- 作者身份 -->
        <view class="post-header">
          <view class="avatar-wrapper">
            <image
              v-if="displayAvatar"
              class="avatar"
              :src="displayAvatar"
              mode="aspectFill"
            />
            <view
              v-else
              class="avatar-placeholder"
              :style="{ backgroundColor: anonAvatarColor }"
            >
              <text class="avatar-icon">~</text>
            </view>
          </view>
          <view class="identity-info">
            <text class="nickname">{{ displayNickname }}</text>
            <view v-if="displayPersonaTag" class="persona-tag">
              <text class="tag-text">{{ displayPersonaTag }}</text>
            </view>
          </view>
          <text class="time-text">{{ post.fuzzy_time?.fuzzy_display || '' }}</text>
        </view>

        <!-- 动态内容 -->
        <view class="post-content">
          <text class="content-text">{{ post.content }}</text>
          <!-- 图片 -->
          <view v-if="post.image_urls && post.image_urls.length > 0" class="post-images">
            <image
              v-for="(url, index) in post.image_urls"
              :key="index"
              class="post-image"
              :src="url"
              mode="aspectFill"
              @tap="handleImagePreview(index)"
            />
          </view>
        </view>

        <!-- 互动区域 -->
        <view class="post-actions">
          <!-- 共鸣 -->
          <view
            class="action-item"
            :class="{ 'is-active': post.has_resonated }"
            @tap="handleResonance"
          >
            <text class="action-icon">{{ post.has_resonated ? '共鸣' : '共鸣' }}</text>
            <text class="action-text">共鸣</text>
            <text v-if="post.resonance_count > 0" class="action-count">{{ post.resonance_count }}</text>
          </view>

          <!-- 收藏 -->
          <view
            class="action-item"
            :class="{ 'is-active': post.has_bookmarked }"
            @tap="handleBookmark"
          >
            <text class="action-icon">{{ post.has_bookmarked ? '已收藏' : '收藏' }}</text>
            <text class="action-text">收藏</text>
          </view>

          <!-- 悄悄关注（仅实名动态且非自己的动态显示） -->
          <view
            v-if="!post.is_anonymous && !post.author?.is_me && !post.has_whisper_followed"
            class="action-item follow-action"
            @tap="handleWhisperFollow"
          >
            <text class="action-icon">关注</text>
          </view>
        </view>
      </view>

      <!-- 评论区 -->
      <view class="comment-section">
        <view class="section-header">
          <text class="section-title">评论 ({{ comments.length }})</text>
        </view>

        <!-- 评论列表 -->
        <view v-if="comments.length > 0" class="comment-list">
          <view
            v-for="comment in comments"
            :key="comment.id"
            class="comment-item"
            @longpress="handleCommentLongPress(comment)"
          >
            <view class="comment-avatar-wrapper">
              <image
                v-if="comment.author_avatar_url"
                class="comment-avatar"
                :src="comment.author_avatar_url"
                mode="aspectFill"
              />
              <view v-else class="comment-avatar-placeholder">
                <text class="avatar-icon">~</text>
              </view>
            </view>
            <view class="comment-content">
              <view class="comment-header">
                <text class="comment-nickname">{{ comment.author_nickname }}</text>
                <text class="comment-time">{{ comment.fuzzy_time?.fuzzy_display || '' }}</text>
              </view>
              <!-- 回复提示 -->
              <view v-if="comment.reply_to_nickname" class="reply-hint">
                <text class="reply-text">回复 @{{ comment.reply_to_nickname }}</text>
              </view>
              <text class="comment-text">{{ comment.content }}</text>
              <!-- 回复按钮 -->
              <view class="comment-actions">
                <view class="reply-btn" @tap="handleReplyComment(comment)">
                  <text class="reply-action-text">回复</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <!-- 空状态 -->
        <view v-else class="empty-comments">
          <text class="empty-text">暂无评论</text>
          <text class="empty-hint">做第一个评论的人吧</text>
        </view>
      </view>

      <!-- 底部安全区（为输入框留空间） -->
      <view class="safe-bottom" :style="{ height: '120rpx' }" />
    </scroll-view>

    <!-- 错误状态 -->
    <view v-else class="error-state">
      <text class="error-text">内容不存在或已删除</text>
      <view class="retry-btn" @tap="handleBack">
        <text class="retry-text">返回</text>
      </view>
    </view>

    <!-- 底部评论输入框 -->
    <view v-if="post" class="comment-input-bar" :style="{ paddingBottom: safeAreaBottom }">
      <view class="input-wrapper">
        <input
          v-model="commentContent"
          class="comment-input"
          type="text"
          :maxlength="200"
          :placeholder="commentPlaceholder"
          placeholder-class="input-placeholder"
          :focus="isCommentFocus"
          @blur="handleCommentBlur"
          @confirm="handleCommentSubmit"
        />
      </view>
      <view
        class="submit-btn"
        :class="{ 'is-disabled': !canSubmitComment || isSubmittingComment }"
        @tap="handleCommentSubmit"
      >
        <text class="submit-text">{{ isSubmittingComment ? '发送中' : '发送' }}</text>
      </view>
    </view>

    <!-- 更多操作弹窗 -->
    <wd-action-sheet
      v-model="showMoreActions"
      :actions="moreActions"
      cancelText="取消"
      @select="handleMoreAction"
    />

    <!-- 评论操作弹窗 -->
    <wd-action-sheet
      v-model="showCommentActions"
      :actions="commentActions"
      cancelText="取消"
      @select="handleCommentAction"
    />

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
 * 回声 - 动态详情页
 * 文件：src/pagesSocial/square/detail.vue
 * 说明：动态详情展示，包含完整内容、评论列表（支持回复）、互动按钮
 */

import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getPostDetail,
  createResonance,
  createBookmark,
  deleteBookmark,
  createWhisperFollow,
  createComment,
  deletePost,
  type Post,
  type PostComment,
} from '@/api/modules/post'
import { track, EventName, trackPageEnter } from '@/utils/tracking'
import ReportDialog from '@/components/common/ReportDialog.vue'
import { ReportContentType, type ReportTarget } from '@/api/modules/report'

// ==================== 响应式状态 ====================

/** 动态详情 */
const post = ref<Post | null>(null)

/** 评论列表 */
const comments = ref<PostComment[]>([])

/** 是否正在加载 */
const isLoading = ref(true)

/** 动态ID */
let postId = ''

/** 是否聚焦评论 */
let focusComment = false

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 评论内容 */
const commentContent = ref('')

/** 是否正在提交评论 */
const isSubmittingComment = ref(false)

/** 是否聚焦评论输入框 */
const isCommentFocus = ref(false)

/** 回复的评论ID */
const replyToId = ref<string | null>(null)

/** 回复的评论昵称 */
const replyToNickname = ref<string | null>(null)

/** 更多操作弹窗 */
const showMoreActions = ref(false)

/** 更多操作列表 */
const moreActions = [
  { name: '举报', value: 'report' },
]

/** 举报弹窗 */
const showReportDialog = ref(false)

/** 举报目标 */
const reportTarget = ref<ReportTarget | null>(null)

/** 评论操作弹窗 */
const showCommentActions = ref(false)

/** 评论操作列表 */
const commentActions = [
  { name: '举报', value: 'report' },
]

/** 长按选中的评论 */
const selectedComment = ref<PostComment | null>(null)

// ==================== 计算属性 ====================

/** 显示的头像 */
const displayAvatar = computed(() => {
  if (!post.value) return null
  if (post.value.is_anonymous) {
    return post.value.anon_identity?.anon_avatar_url || null
  }
  return post.value.author?.avatar_url || null
})

/** 显示的昵称 */
const displayNickname = computed(() => {
  if (!post.value) return ''
  if (post.value.is_anonymous) {
    return post.value.anon_identity?.anon_nickname || '匿名用户'
  }
  return post.value.author?.nickname || '用户'
})

/** 显示的气质标签（仅匿名动态） */
const displayPersonaTag = computed(() => {
  if (!post.value) return null
  if (post.value.is_anonymous) {
    return post.value.anon_identity?.persona_tag || null
  }
  return null
})

/** 匿名头像颜色 */
const anonAvatarColor = computed(() => {
  if (!post.value) return '#A89CF5'
  const colors = [
    '#FFB5BA',
    '#8B9DC3',
    '#7CB9A0',
    '#A89CF5',
    '#FFB88A',
    '#A5C0D6',
    '#D4A5D9',
    '#8B6C9A',
  ]
  const seed = post.value.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[seed % colors.length]
})

/** 评论占位符 */
const commentPlaceholder = computed(() => {
  if (replyToNickname.value) {
    return `回复 @${replyToNickname.value}`
  }
  return '写评论...'
})

/** 是否可以提交评论 */
const canSubmitComment = computed(() => {
  return commentContent.value.trim().length > 0 && commentContent.value.length <= 200
})

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
 * 获取动态详情
 */
async function loadPostDetail(): Promise<void> {
  if (!postId) return

  isLoading.value = true

  try {
    const result = await getPostDetail(postId)
    post.value = result.post
    comments.value = result.comments

    track(EventName.SQUARE_POST_VIEW, { post_id: postId })

    // 如果需要聚焦评论
    if (focusComment) {
      setTimeout(() => {
        isCommentFocus.value = true
      }, 300)
    }
  } catch (error) {
    console.error('加载动态详情失败', error)
    post.value = null
  } finally {
    isLoading.value = false
  }
}

/**
 * 处理返回
 */
function handleBack(): void {
  uni.navigateBack()
}

/**
 * 处理共鸣
 */
async function handleResonance(): Promise<void> {
  if (!post.value) return

  try {
    const result = await createResonance(post.value.id)

    post.value = {
      ...post.value,
      resonance_count: result.resonance_count,
      has_resonated: !result.already_resonated,
    }

    if (!result.already_resonated) {
      uni.showToast({
        title: '已共鸣',
        icon: 'success',
      })
    }

    track(EventName.SQUARE_RESONANCE, {
      post_id: post.value.id,
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
 * 处理收藏
 */
async function handleBookmark(): Promise<void> {
  if (!post.value) return

  try {
    if (post.value.has_bookmarked) {
      await deleteBookmark(post.value.id)
    } else {
      await createBookmark(post.value.id)
    }

    post.value = {
      ...post.value,
      bookmark_count: post.value.has_bookmarked
        ? post.value.bookmark_count - 1
        : post.value.bookmark_count + 1,
      has_bookmarked: !post.value.has_bookmarked,
    }

    uni.showToast({
      title: post.value.has_bookmarked ? '已收藏' : '已取消收藏',
      icon: 'success',
    })

    track(EventName.SQUARE_BOOKMARK, {
      post_id: post.value.id,
      is_bookmark: post.value.has_bookmarked,
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
 * 处理悄悄关注
 */
async function handleWhisperFollow(): Promise<void> {
  if (!post.value) return

  try {
    const result = await createWhisperFollow(post.value.id)

    post.value = {
      ...post.value,
      has_whisper_followed: true,
    }

    uni.showToast({
      title: result.already_following ? '已关注' : '已悄悄关注',
      icon: 'success',
    })

    track(EventName.SQUARE_WHISPER_FOLLOW, {
      post_id: post.value.id,
      author_id: post.value.author?.id,
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
 * 处理回复评论
 */
function handleReplyComment(comment: PostComment): void {
  replyToId.value = comment.id
  replyToNickname.value = comment.author_nickname
  isCommentFocus.value = true
}

/**
 * 处理评论输入框失焦
 */
function handleCommentBlur(): void {
  // 延迟清除回复状态，让用户有时间点击其他位置
  setTimeout(() => {
    if (!isCommentFocus.value) {
      // 如果已经失焦，清除回复状态
      // replyToId.value = null
      // replyToNickname.value = null
    }
  }, 200)
}

/**
 * 处理提交评论
 */
async function handleCommentSubmit(): Promise<void> {
  if (!post.value || !canSubmitComment.value || isSubmittingComment.value) return

  const content = commentContent.value.trim()
  if (!content) return

  isSubmittingComment.value = true

  try {
    const result = await createComment(post.value.id, {
      content,
      reply_to_id: replyToId.value,
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

    // 添加新评论到列表
    if (result.comment) {
      comments.value = [result.comment, ...comments.value]
      post.value = {
        ...post.value,
        comment_count: post.value.comment_count + 1,
      }
    }

    // 清空输入
    commentContent.value = ''
    replyToId.value = null
    replyToNickname.value = null
    isCommentFocus.value = false

    uni.showToast({
      title: '发送成功',
      icon: 'success',
    })

    track(EventName.SQUARE_COMMENT_CREATE, { post_id: post.value.id })
  } catch (error) {
    console.error('创建评论失败', error)
    uni.showToast({
      title: '发送失败，请重试',
      icon: 'none',
    })
  } finally {
    isSubmittingComment.value = false
  }
}

/**
 * 处理删除动态
 */
function handleDelete(): void {
  if (!post.value) return

  uni.showModal({
    title: '确认删除',
    content: '删除后将无法恢复，确定要删除吗？',
    confirmText: '删除',
    confirmColor: '#F87171',
    cancelText: '取消',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deletePost(post.value!.id)

          uni.showToast({
            title: '删除成功',
            icon: 'success',
          })

          track(EventName.SQUARE_DELETE, { post_id: post.value!.id })

          // 返回上一页
          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        } catch (error) {
          console.error('删除失败', error)
          uni.showToast({
            title: '删除失败，请重试',
            icon: 'none',
          })
        }
      }
    },
  })
}

/**
 * 处理图片预览
 */
function handleImagePreview(index: number): void {
  if (!post.value?.image_urls) return

  uni.previewImage({
    urls: post.value.image_urls,
    current: post.value.image_urls[index],
  })
}

/**
 * 解析页面参数
 */
function parsePageParams(): void {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = (currentPage as any).options || {}

  postId = options.id || ''
  focusComment = options.focus === 'comment'
}

/**
 * 显示更多操作
 */
function handleShowMoreActions(): void {
  showMoreActions.value = true
}

/**
 * 处理更多操作
 */
function handleMoreAction(action: any): void {
  showMoreActions.value = false

  if (action.value === 'report' && post.value) {
    reportTarget.value = {
      contentType: ReportContentType.POST,
      contentId: post.value.id,
    }
    showReportDialog.value = true
  }
}

/**
 * 举报成功回调
 */
function handleReportSuccess(): void {
  track(EventName.SQUARE_REPORT, { post_id: post.value?.id })
}

/**
 * 评论长按事件
 */
function handleCommentLongPress(comment: PostComment): void {
  selectedComment.value = comment
  showCommentActions.value = true
}

/**
 * 评论操作选择
 */
function handleCommentAction(action: any): void {
  showCommentActions.value = false

  if (action.value === 'report' && selectedComment.value) {
    reportTarget.value = {
      contentType: ReportContentType.COMMENT,
      contentId: selectedComment.value.id,
    }
    showReportDialog.value = true
  }

  // 清除选中状态
  selectedComment.value = null
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
  parsePageParams()
  loadPostDetail()
})

onShow(() => {
  trackPageEnter('square_detail')
})
</script>

<style lang="scss" scoped>
.detail-page {
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
  height: 88rpx;
  padding: 0 var(--space-md);
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;

  &:active {
    opacity: 0.7;
  }
}

.back-icon {
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

.header-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-sm);

  &:active {
    opacity: 0.7;
  }
}

.action-text {
  font-size: var(--font-size-sm);
  color: var(--color-error);
}

.more-icon {
  font-size: var(--font-size-lg);
  font-weight: bold;
  color: var(--text-primary);
  letter-spacing: 2rpx;
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-top: var(--space-sm);
}

// ==================== 动态详情 ====================

.post-detail {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin: var(--space-md);
}

.post-header {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-md);
}

.avatar-wrapper {
  width: 80rpx;
  height: 80rpx;
  margin-right: var(--space-sm);
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: var(--font-size-base);
  color: rgba(255, 255, 255, 0.8);
}

.identity-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.nickname {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--text-primary);
}

.persona-tag {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  margin-top: 4rpx;
  padding: 2rpx 12rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
}

.tag-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.time-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 内容 ====================

.post-content {
  display: flex;
  flex-direction: column;
}

.content-text {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  line-height: 1.6;
  word-break: break-word;
}

.post-images {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.post-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
}

// ==================== 互动区域 ====================

.post-actions {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-top: var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-primary);
}

.action-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);

  &:active {
    opacity: 0.7;
  }

  &.is-active {
    .action-text {
      color: var(--brand-primary);
    }
  }
}

.action-icon {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}

.action-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.action-count {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.follow-action {
  .action-icon {
    color: var(--brand-primary);
  }
}

// ==================== 评论区 ====================

.comment-section {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin: 0 var(--space-md);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-md);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.comment-item {
  display: flex;
  align-items: flex-start;
}

.comment-avatar-wrapper {
  width: 64rpx;
  height: 64rpx;
  margin-right: var(--space-sm);
}

.comment-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.comment-avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--brand-primary);
}

.comment-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.comment-nickname {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.comment-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.reply-hint {
  margin-bottom: var(--space-xs);
}

.reply-text {
  font-size: var(--font-size-xs);
  color: var(--brand-primary);
}

.comment-text {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  line-height: 1.5;
  word-break: break-word;
}

.comment-actions {
  display: flex;
  margin-top: var(--space-xs);
}

.reply-btn {
  padding: var(--space-xs) 0;

  &:active {
    opacity: 0.7;
  }
}

.reply-action-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 空评论 ====================

.empty-comments {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg) 0;
}

.empty-text {
  font-size: var(--font-size-base);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
}

// ==================== 错误状态 ====================

.error-state {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.error-text {
  font-size: var(--font-size-base);
  color: var(--text-tertiary);
  margin-bottom: var(--space-md);
}

.retry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-lg);
  background-color: var(--brand-primary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.8;
  }
}

.retry-text {
  font-size: var(--font-size-base);
  color: var(--text-on-brand);
}

// ==================== 评论输入栏 ====================

.comment-input-bar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
}

.input-wrapper {
  flex: 1;
}

.comment-input {
  width: 100%;
  height: 72rpx;
  padding: 0 var(--space-md);
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
}

.input-placeholder {
  color: var(--text-tertiary);
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 72rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-full);

  &:active {
    opacity: 0.8;
  }

  &.is-disabled {
    background-color: var(--bg-tertiary);

    .submit-text {
      color: var(--text-tertiary);
    }
  }
}

.submit-text {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>