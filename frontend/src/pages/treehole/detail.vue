<template>
  <view class="detail-page treehole-force-dark">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <text class="back-icon">&lt;</text>
      </view>
      <text class="header-title">详情</text>
      <view v-if="post?.is_mine" class="header-actions">
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
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 内容区域 -->
    <scroll-view v-else-if="post" class="page-content" scroll-y>
      <!-- 帖子详情 -->
      <view class="post-detail">
        <!-- 匿名身份 -->
        <view class="post-header">
          <view class="avatar-wrapper">
            <image
              v-if="post.anon_identity?.anon_avatar_url"
              class="avatar"
              :src="post.anon_identity.anon_avatar_url"
              mode="aspectFill"
            />
            <image
              v-else
              class="avatar"
              :src="generateVirtualAvatar(post.id)"
              mode="aspectFill"
            />
          </view>
          <view class="identity-info">
            <text class="nickname">{{ post.anon_identity?.anon_nickname || '匿名用户' }}</text>
            <view v-if="post.anon_identity?.persona_tag" class="persona-tag">
              <text class="tag-text">{{ post.anon_identity.persona_tag }}</text>
            </view>
          </view>
          <text class="time-text">{{ post.fuzzy_time?.fuzzy_display || '' }}</text>
        </view>

        <!-- 帖子内容 -->
        <view class="post-content">
          <text class="content-text">{{ post.content }}</text>
          <!-- 话题标签 -->
          <view v-if="post.topic_tag_label" class="topic-tag">
            <text class="topic-text">#{{ post.topic_tag_label }}</text>
          </view>
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
          <view
            class="action-item"
            :class="{ 'is-active': post.has_resonated }"
            @tap="handleResonance"
          >
            <view class="action-icon-wrapper" :class="{ 'is-active': post.has_resonated }">
              <text class="action-icon-text">{{ post.has_resonated ? '✓' : '○' }}</text>
            </view>
            <text class="action-text">我懂你</text>
            <text v-if="post.resonance_count > 0" class="action-count">{{ post.resonance_count }}</text>
          </view>
          <view class="action-item">
            <view class="action-icon-wrapper">
              <text class="action-icon-text">评</text>
            </view>
            <text class="action-text">回声</text>
            <text v-if="post.comment_count > 0" class="action-count">{{ post.comment_count }}</text>
          </view>
        </view>
      </view>

      <!-- 评论区 -->
      <CommentSection
        :comments="comments"
        :post-id="post.id"
        @submit="handleCommentSubmit"
      />

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </scroll-view>

    <!-- 错误状态 -->
    <view v-else class="error-state">
      <text class="error-text">内容不存在或已删除</text>
      <view class="retry-btn" @tap="handleBack">
        <text class="retry-text">返回</text>
      </view>
    </view>

    <!-- 更多操作弹窗 -->
    <wd-action-sheet
      v-model="showMoreActions"
      :actions="moreActions"
      cancelText="取消"
      @select="handleMoreAction"
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
 * 回声 - 树洞帖子详情页
 * 文件：src/pages/treehole/detail.vue
 * 说明：帖子详情展示，包含共鸣按钮和回声评论
 */

import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  getTreeholePostDetail,
  createResonance,
  createTreeholeComment,
  deleteTreeholePost,
  generateVirtualAvatar,
  type TreeholePost,
  type TreeholeComment,
} from '@/api/treehole'
import { track, EventName, trackPageEnter } from '@/utils/tracking'
import CommentSection from '@/components/treehole/CommentSection.vue'
import ReportDialog from '@/components/common/ReportDialog.vue'
import { ReportContentType, type ReportTarget } from '@/api/modules/report'

// ==================== 响应式状态 ====================

/** 帖子详情 */
const post = ref<TreeholePost | null>(null)

/** 评论列表 */
const comments = ref<TreeholeComment[]>([])

/** 是否正在加载 */
const isLoading = ref(true)

/** 帖子ID */
let postId = ''

/** 是否聚焦评论 */
let focusComment = false

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

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
 * 获取帖子详情
 */
async function loadPostDetail(): Promise<void> {
  if (!postId) return

  isLoading.value = true

  try {
    const result = await getTreeholePostDetail(postId)
    post.value = result.post
    comments.value = result.comments

    track(EventName.TREEHOLE_POST_VIEW, { post_id: postId })
  } catch (error) {
    console.error('加载帖子详情失败', error)
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
        title: '有人懂你',
        icon: 'success',
      })
    }

    track(EventName.TREEHOLE_RESONANCE, {
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
 * 处理评论提交
 */
async function handleCommentSubmit(content: string): Promise<void> {
  if (!post.value) return

  try {
    const result = await createTreeholeComment(post.value.id, { content })

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

    // 检查脱敏提醒
    if (result.identity_warning?.has_warning) {
      uni.showToast({
        title: result.identity_warning.warning_message,
        icon: 'none',
        duration: 3000,
      })
    }

    uni.showToast({
      title: '发送成功',
      icon: 'success',
    })

    track(EventName.TREEHOLE_COMMENT_CREATE, { post_id: post.value.id })
  } catch (error) {
    console.error('创建评论失败', error)
    uni.showToast({
      title: '发送失败，请重试',
      icon: 'none',
    })
  }
}

/**
 * 处理删除帖子
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
          await deleteTreeholePost(post.value!.id)

          uni.showToast({
            title: '删除成功',
            icon: 'success',
          })

          track(EventName.TREEHOLE_DELETE, { post_id: post.value!.id })

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
      contentType: ReportContentType.TREEHOLE_POST,
      contentId: post.value.id,
    }
    showReportDialog.value = true
  }
}

/**
 * 举报成功回调
 */
function handleReportSuccess(): void {
  track(EventName.TREEHOLE_REPORT, { post_id: post.value?.id })
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

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
  parsePageParams()
  loadPostDetail()
})

onShow(() => {
  trackPageEnter('treehole_detail')
})
</script>

<style lang="scss" scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
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
  color: var(--dark-text-primary);
}

.header-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--dark-text-primary);
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
  color: var(--dark-text-primary);
  letter-spacing: 2rpx;
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: var(--font-size-base);
  color: var(--dark-text-tertiary);
}

// ==================== 帖子详情 ====================

.post-detail {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--dark-bg-secondary);
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

.identity-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.nickname {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--dark-text-primary);
}

.persona-tag {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  margin-top: 4rpx;
  padding: 2rpx 12rpx;
  background-color: var(--dark-bg-tertiary);
  border-radius: var(--radius-full);
}

.tag-text {
  font-size: var(--font-size-xs);
  color: var(--dark-text-tertiary);
}

.time-text {
  font-size: var(--font-size-xs);
  color: var(--dark-text-tertiary);
}

// ==================== 内容 ====================

.post-content {
  display: flex;
  flex-direction: column;
}

.content-text {
  font-size: var(--font-size-base);
  color: var(--dark-text-primary);
  line-height: 1.6;
  word-break: break-word;
}

.topic-tag {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  margin-top: var(--space-sm);
  padding: 4rpx 16rpx;
  background-color: rgba(124, 111, 224, 0.15);
  border-radius: var(--radius-full);
}

.topic-text {
  font-size: var(--font-size-sm);
  color: var(--brand-light);
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
  background-color: var(--dark-bg-tertiary);
}

// ==================== 互动区域 ====================

.post-actions {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-top: var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--dark-border-primary);
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

.action-icon-wrapper {
  width: 40rpx;
  height: 40rpx;
  border-radius: var(--radius-sm);
  background-color: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 6rpx;

  &.is-active {
    background-color: rgba(248, 113, 113, 0.15);
  }
}

.action-icon-text {
  font-size: 24rpx;
  font-weight: 500;
  color: var(--text-secondary);
}

.action-text {
  font-size: var(--font-size-sm);
  color: var(--dark-text-secondary);
}

.action-count {
  font-size: var(--font-size-sm);
  color: var(--dark-text-tertiary);
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
  color: var(--dark-text-tertiary);
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

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>