<template>
  <view class="detail-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <wd-icon name="arrow-left" class="back-icon" />
      </view>
      <text class="header-title">详情</text>
      <view v-if="post?.is_mine" class="header-actions">
        <view class="action-btn" @tap="handleDelete">
          <text class="action-text">删除</text>
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
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 树洞帖子详情页
 * 文件：src/pages/treehole/detail.vue
 * 说明：帖子详情展示，包含共鸣按钮和回声评论
 */

import { ref, onMounted } from 'vue'
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
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import CommentSection from '@/components/treehole/CommentSection.vue'

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
    confirmColor: '#E83A30',
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

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('treehole_detail')
  }
})
</script>

<style lang="scss" scoped>
.detail-page {
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
  height: 88rpx;
  padding: 0 24rpx;
  background: linear-gradient(135deg, #78909C, #5F7E8B);
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
  font-size: 40rpx;
  color: #FFFFFF;
}

.header-title {
  font-size: 30rpx;
  font-weight: 500;
  color: #FFFFFF;
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8rpx 16rpx;

  &:active {
    opacity: 0.7;
  }
}

.action-text {
  font-size: 26rpx;
  color: #E83A30;
}

// ==================== 加载状态 ====================

.loading-state {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 28rpx;
  color: #838383;
}

// ==================== 帖子详情 ====================

.post-detail {
  display: flex;
  flex-direction: column;
  padding: 24rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.05);
  margin: 24rpx;
}

.post-header {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.avatar-wrapper {
  width: 80rpx;
  height: 80rpx;
  margin-right: 16rpx;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 5000rpx;
}

.identity-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.nickname {
  font-size: 28rpx;
  font-weight: 500;
  color: #080808;
}

.persona-tag {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  margin-top: 4rpx;
  padding: 2rpx 12rpx;
  background-color: #F4F4F5;
  border-radius: 5000rpx;
}

.tag-text {
  font-size: 22rpx;
  color: #838383;
}

.time-text {
  font-size: 22rpx;
  color: #838383;
}

// ==================== 内容 ====================

.post-content {
  display: flex;
  flex-direction: column;
}

.content-text {
  font-size: 28rpx;
  color: #080808;
  line-height: 1.6;
  word-break: break-word;
}

.topic-tag {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  margin-top: 16rpx;
  padding: 4rpx 16rpx;
  background-color: rgba(1, 190, 255, 0.1);
  border-radius: 5000rpx;
}

.topic-text {
  font-size: 26rpx;
  color: #01BEFF;
}

.post-images {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 24rpx;
}

.post-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: 20rpx;
  background-color: #F4F4F5;
}

// ==================== 互动区域 ====================

.post-actions {
  display: flex;
  align-items: center;
  gap: 30rpx;
  margin-top: 24rpx;
  padding-top: 16rpx;
  border-top: 2rpx solid #F4F4F5;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8rpx;

  &:active {
    opacity: 0.7;
  }

  &.is-active {
    .action-text {
      color: #01BEFF;
    }
  }
}

.action-icon-wrapper {
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  background-color: #F4F4F5;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 6rpx;

  &.is-active {
    background-color: #E83A30;
  }
}

.action-icon-text {
  font-size: 24rpx;
  font-weight: 500;
  color: #333333;
}

.action-text {
  font-size: 26rpx;
  color: #333333;
}

.action-count {
  font-size: 26rpx;
  color: #838383;
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
  font-size: 28rpx;
  color: #838383;
  margin-bottom: 24rpx;
}

.retry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 30rpx;
  background: linear-gradient(135deg, #78909C, #5F7E8B);
  border-radius: 5000rpx;
  box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(120, 144, 156, 0.35);

  &:active {
    opacity: 0.8;
  }
}

.retry-text {
  font-size: 28rpx;
  color: #FFFFFF;
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>