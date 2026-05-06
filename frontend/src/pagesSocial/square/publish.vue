<template>
  <view class="publish-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <wd-icon name="arrow-left" size="20px" color="var(--text-primary)" />
      </view>
      <text class="header-title">发布动态</text>
      <view class="header-actions">
        <view
          class="publish-btn"
          :class="{ 'is-disabled': !canPublish || isSubmitting }"
          @tap="handlePublish"
        >
          <text class="publish-text">{{ isSubmitting ? '发布中' : '发布' }}</text>
        </view>
      </view>
    </view>

    <!-- 内容区域 -->
    <scroll-view class="page-content" scroll-y>
      <!-- 身份预览 -->
      <view class="identity-section">
        <view v-if="!isAnonymous" class="identity-card real-name">
          <view class="avatar-wrapper">
            <image
              v-if="userAvatar"
              class="avatar"
              :src="userAvatar"
              mode="aspectFill"
            />
            <view v-else class="avatar-placeholder">
              <wd-icon name="user" size="24px" color="var(--text-muted)" />
            </view>
          </view>
          <view class="identity-info">
            <text class="nickname">{{ userNickname }}</text>
            <text class="identity-type">实名发布</text>
          </view>
        </view>
        <view v-else class="identity-card anonymous">
          <view class="avatar-wrapper">
            <view
              class="avatar-placeholder"
              :style="{ backgroundColor: anonAvatarColor }"
            >
              <wd-icon name="user" size="24px" color="var(--text-inverse)" />
            </view>
          </view>
          <view class="identity-info">
            <text class="nickname">{{ anonNickname }}</text>
            <text class="persona-text">{{ anonPersona }}</text>
          </view>
          <text class="hint-text">匿名身份</text>
        </view>
      </view>

      <!-- 内容输入 -->
      <view class="content-section">
        <textarea
          v-model="content"
          class="content-input"
          :maxlength="500"
          :placeholder="placeholder"
          placeholder-class="input-placeholder"
          :auto-height="true"
          :show-confirm-bar="false"
          :adjust-position="true"
          :focus="autoFocus"
        />
        <view class="input-footer">
          <text class="char-count">{{ content.length }}/500</text>
        </view>
      </view>

      <!-- 图片上传区域 -->
      <view class="image-section">
        <text class="section-label">图片（最多9张）</text>
        <view class="image-grid">
          <view
            v-for="(url, index) in imageUrls"
            :key="index"
            class="image-item"
          >
            <image class="preview-image" :src="url" mode="aspectFill" />
            <view class="remove-btn" @tap="handleRemoveImage(index)">
              <text class="remove-icon">x</text>
            </view>
          </view>
          <view
            v-if="imageUrls.length < 9"
            class="image-add-btn"
            @tap="handleAddImage"
          >
            <text class="add-icon">+</text>
            <text class="add-text">添加图片</text>
          </view>
        </view>
        <!-- 失败图片重试提示 -->
        <view v-if="failedImages.length > 0" class="failed-images-tip">
          <text class="failed-text">{{ failedImages.length }}张图片上传失败</text>
          <view
            class="retry-btn"
            :class="{ 'is-loading': isRetryingImages }"
            @tap="handleRetryFailedImages"
          >
            <text class="retry-text">{{ isRetryingImages ? '重试中...' : '重试' }}</text>
          </view>
        </view>
      </view>

      <!-- 底部工具栏 -->
      <view class="toolbar">
        <view class="tool-left">
          <!-- 图片按钮 -->
          <view class="tool-btn" @tap="handleAddImage">
            <text class="tool-icon">图片</text>
          </view>
          <!-- AI润色按钮 -->
          <view
            class="tool-btn"
            :class="{ 'is-disabled': !content.trim() }"
            @tap="handleOpenPolish"
          >
            <text class="tool-icon">AI润色</text>
          </view>
        </view>
        <view class="tool-right">
          <!-- 匿名切换 -->
          <view class="anonymous-toggle" @tap="handleToggleAnonymous">
            <view class="toggle-switch" :class="{ 'is-active': isAnonymous }">
              <view class="toggle-dot" />
            </view>
            <text class="toggle-label">{{ isAnonymous ? '匿名' : '实名' }}</text>
          </view>
        </view>
      </view>

      <!-- 匿名提示 -->
      <view v-if="isAnonymous" class="anonymous-hint">
        <text class="hint-icon">!</text>
        <text class="hint-text">匿名发布后无法被关注</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </scroll-view>

    <!-- AI润色卡片 -->
    <AIPolishCard
      v-model:show="showPolishCard"
      :content="content"
      @use-polished="handleUsePolished"
      @keep-original="handleKeepOriginal"
    />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 动态发布页
 * 文件：src/pagesSocial/square/publish.vue
 * 说明：动态发布页面，支持内容输入、图片上传、AI润色、匿名切换
 * 设计要点：默认实名发布，可切换匿名，匿名时显示随机虚拟身份
 */

import { ref, computed, onMounted } from 'vue'
import { onShow, onBackPress } from '@dcloudio/uni-app'
import {
  createPost,
  uploadPostImage,
  generateAnonIdentity,
  type CreatePostResponse,
} from '@/api/modules/post'
import { track, EventName, trackPageEnter } from '@/utils/tracking'
import { useUserStore } from '@/stores/user'
import AIPolishCard from '@/components/square/AIPolishCard.vue'

// ==================== 响应式状态 ====================

/** 输入内容 */
const content = ref('')

/** 图片URL列表 */
const imageUrls = ref<string[]>([])

/** 失败的图片路径列表（用于重试） */
const failedImages = ref<string[]>([])

/** 是否匿名发布 */
const isAnonymous = ref(false)

/** 匿名昵称 */
const anonNickname = ref('')

/** 匿名气质标签 */
const anonPersona = ref('')

/** 匿名头像颜色 */
const anonAvatarColor = ref('#A89CF5')

/** 是否正在提交 */
const isSubmitting = ref(false)

/** 是否正在上传图片 */
const isUploadingImage = ref(false)

/** 是否正在重试失败的图片 */
const isRetryingImages = ref(false)

/** 是否显示AI润色卡片 */
const showPolishCard = ref(false)

/** 是否自动聚焦 */
const autoFocus = ref(true)

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 占位符 */
const placeholder = '分享此刻的心情...'

// ==================== Store ====================

const userStore = useUserStore()

// ==================== 计算属性 ====================

/** 用户昵称 */
const userNickname = computed(() => userStore.displayName)

/** 用户头像 */
const userAvatar = computed(() => userStore.userInfo?.avatarUrl || null)

/** 是否可以发布 */
const canPublish = computed(() => {
  return content.value.trim().length > 0 && content.value.length <= 500
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
 * 生成匿名身份
 */
function generateAnonIdentityPreview(): void {
  const { nickname, persona } = generateAnonIdentity()
  anonNickname.value = nickname
  anonPersona.value = persona

  // 头像颜色
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
  const seed = Date.now()
  anonAvatarColor.value = colors[seed % colors.length]
}

/**
 * 处理添加图片
 */
async function handleAddImage(): Promise<void> {
  if (isUploadingImage.value || imageUrls.value.length >= 9) return

  try {
    const result = await new Promise<string[]>((resolve, reject) => {
      uni.chooseImage({
        count: 9 - imageUrls.value.length,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => resolve(res.tempFilePaths),
        fail: (err) => reject(err),
      })
    })

    isUploadingImage.value = true

    // 上传图片，记录失败的图片
    const newFailedImages: string[] = []
    for (const filePath of result) {
      try {
        const uploadResult = await uploadPostImage(filePath)
        imageUrls.value.push(uploadResult.url)
      } catch (error) {
        console.error('上传图片失败', error)
        newFailedImages.push(filePath)
      }
    }

    // 记录失败的图片
    if (newFailedImages.length > 0) {
      failedImages.value.push(...newFailedImages)
      uni.showToast({
        title: `${newFailedImages.length}张图片上传失败`,
        icon: 'none',
      })
    }

    track(EventName.SQUARE_IMAGE_UPLOAD, { count: result.length })
  } catch (error) {
    console.error('选择图片失败', error)
  } finally {
    isUploadingImage.value = false
  }
}

/**
 * 处理移除图片
 */
function handleRemoveImage(index: number): void {
  imageUrls.value.splice(index, 1)
}

/**
 * 重试上传失败的图片
 */
async function handleRetryFailedImages(): Promise<void> {
  if (failedImages.value.length === 0 || isRetryingImages.value) {
    return
  }

  isRetryingImages.value = true

  const retryImages = [...failedImages.value]
  failedImages.value = [] // 清空失败列表

  let successCount = 0
  let failCount = 0

  for (const filePath of retryImages) {
    try {
      const uploadResult = await uploadPostImage(filePath)
      imageUrls.value.push(uploadResult.url)
      successCount++
    } catch (error) {
      console.error('重试上传图片失败', error)
      failedImages.value.push(filePath) // 重新加入失败列表
      failCount++
    }
  }

  isRetryingImages.value = false

  // 提示结果
  if (successCount > 0 && failCount === 0) {
    uni.showToast({
      title: `${successCount}张图片上传成功`,
      icon: 'success',
    })
  } else if (successCount > 0 && failCount > 0) {
    uni.showToast({
      title: `${successCount}张成功，${failCount}张失败`,
      icon: 'none',
    })
  } else if (failCount > 0) {
    uni.showToast({
      title: '重试失败，请稍后再试',
      icon: 'none',
    })
  }
}

/**
 * 处理打开AI润色卡片
 */
function handleOpenPolish(): void {
  if (!content.value.trim()) {
    uni.showToast({
      title: '请先输入内容',
      icon: 'none',
    })
    return
  }
  showPolishCard.value = true
}

/**
 * 处理使用润色内容
 */
function handleUsePolished(polishedContent: string): void {
  content.value = polishedContent
  showPolishCard.value = false

  uni.showToast({
    title: '已应用润色内容',
    icon: 'success',
  })
}

/**
 * 处理保留原文
 */
function handleKeepOriginal(): void {
  showPolishCard.value = false
}

/**
 * 处理匿名切换
 */
function handleToggleAnonymous(): void {
  if (!isAnonymous.value) {
    // 切换到匿名，先确认
    uni.showModal({
      title: '匿名发布',
      content: '匿名发布后无法被关注，确定要匿名发布吗？',
      confirmText: '确定',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          isAnonymous.value = true
          track(EventName.SQUARE_ANONYMOUS_TOGGLE, { is_anonymous: true })
        }
      },
    })
  } else {
    isAnonymous.value = false
    track(EventName.SQUARE_ANONYMOUS_TOGGLE, { is_anonymous: false })
  }
}

/**
 * 处理发布
 */
async function handlePublish(): Promise<void> {
  if (!canPublish.value || isSubmitting.value) return

  const publishContent = content.value.trim()
  if (!publishContent) return

  isSubmitting.value = true

  try {
    const result: CreatePostResponse = await createPost({
      content: publishContent,
      image_urls: imageUrls.value.length > 0 ? imageUrls.value : undefined,
      is_anonymous: isAnonymous.value,
    })

    // 检查审核反馈
    if (result.audit_feedback) {
      uni.showModal({
        title: '温馨提示',
        content: result.audit_feedback.feedback,
        showCancel: false,
        confirmText: '我知道了',
      })

      track(EventName.SQUARE_CREATE_BLOCKED, {
        labels: result.audit_feedback.labels,
      })
      return
    }

    uni.showToast({
      title: '发布成功',
      icon: 'success',
    })

    track(EventName.SQUARE_CREATE_SUCCESS, {
      post_id: result.post?.id,
      is_anonymous: isAnonymous.value,
      has_images: imageUrls.value.length > 0,
    })

    // 返回上一页
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (error) {
    console.error('发布失败', error)
    uni.showToast({
      title: '发布失败，请重试',
      icon: 'none',
    })
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 处理返回（自定义返回按钮）
 */
function handleBack(): void {
  if (content.value.trim() || imageUrls.value.length > 0) {
    uni.showModal({
      title: '提示',
      content: '内容尚未发布，确定要退出吗？',
      confirmText: '退出',
      confirmColor: '#F87171',
      cancelText: '继续编辑',
      success: (res) => {
        if (res.confirm) {
          uni.navigateBack()
        }
      },
    })
  } else {
    uni.navigateBack()
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
  generateAnonIdentityPreview()
})

onShow(() => {
  trackPageEnter('square_publish')
})

/**
 * 拦截物理返回键（Android）和右滑返回（iOS）
 * 返回 true 阻止默认返回行为，返回 false 允许返回
 */
onBackPress(() => {
  // 如果有内容未发布，显示确认弹窗
  if (content.value.trim() || imageUrls.value.length > 0) {
    uni.showModal({
      title: '提示',
      content: '内容尚未发布，确定要退出吗？',
      confirmText: '退出',
      confirmColor: '#F87171',
      cancelText: '继续编辑',
      success: (res) => {
        if (res.confirm) {
          // 用户确认退出，执行返回
          uni.navigateBack()
        }
        // 用户取消，不做任何操作，留在当前页
      },
    })
    // 阻止默认返回行为，让用户通过弹窗选择
    return true
  }
  // 没有内容，允许正常返回
  return false
})
</script>

<style lang="scss" scoped>
.publish-page {
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

.publish-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-md);
  background-color: var(--brand-primary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.8;
  }

  &.is-disabled {
    background-color: var(--bg-tertiary);

    .publish-text {
      color: var(--text-tertiary);
    }
  }
}

.publish-text {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);
  font-weight: 500;
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding: var(--space-md);
}

// ==================== 身份预览 ====================

.identity-section {
  margin-bottom: var(--space-md);
}

.identity-card {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.avatar-wrapper {
  width: 64rpx;
  height: 64rpx;
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
  background-color: var(--brand-primary);
}

.avatar-icon {
  font-size: var(--font-size-base);
  color: rgba(255, 255, 255, 0.8);
}

.identity-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.nickname {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.identity-type {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.persona-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.hint-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 内容输入 ====================

.content-section {
  margin-bottom: var(--space-md);
}

.content-input {
  width: 100%;
  min-height: 300rpx;
  padding: var(--space-md);
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  line-height: 1.6;
}

.input-placeholder {
  color: var(--text-tertiary);
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-xs);
}

.char-count {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 图片上传 ====================

.image-section {
  margin-bottom: var(--space-md);
}

.section-label {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-sm);
}

.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.image-item {
  position: relative;
  width: 200rpx;
  height: 200rpx;
}

.preview-image {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);
}

.remove-btn {
  position: absolute;
  top: -16rpx;
  right: -16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40rpx;
  height: 40rpx;
  background-color: var(--color-error);
  border-radius: 50%;
}

.remove-icon {
  font-size: var(--font-size-sm);
  color: #fff;
}

.image-add-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 200rpx;
  height: 200rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-primary);

  &:active {
    opacity: 0.8;
  }
}

.add-icon {
  font-size: var(--font-size-xl);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.add-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// 失败图片重试提示
.failed-images-tip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background-color: var(--color-warning-bg);
  border-radius: var(--radius-md);
}

.failed-text {
  font-size: var(--font-size-sm);
  color: var(--color-warning);
}

.retry-btn {
  padding: 8rpx 20rpx;
  background-color: var(--color-warning);
  border-radius: var(--radius-sm);

  &.is-loading {
    opacity: 0.6;
  }
}

.retry-text {
  font-size: var(--font-size-sm);
  color: var(--text-inverse);
}

// ==================== 工具栏 ====================

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.tool-left {
  display: flex;
  gap: var(--space-md);
}

.tool-btn {
  display: flex;
  align-items: center;
  padding: var(--space-xs) var(--space-sm);

  &:active {
    opacity: 0.8;
  }

  &.is-disabled {
    opacity: 0.5;
  }
}

.tool-icon {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.tool-right {
  display: flex;
  align-items: center;
}

.anonymous-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-sm);

  &:active {
    opacity: 0.8;
  }
}

.toggle-switch {
  display: flex;
  align-items: center;
  width: 80rpx;
  height: 48rpx;
  padding: 4rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
  transition: background-color 0.2s;

  &.is-active {
    background-color: var(--brand-primary);
    justify-content: flex-end;
  }
}

.toggle-dot {
  width: 40rpx;
  height: 40rpx;
  background-color: #fff;
  border-radius: 50%;
}

.toggle-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 匿名提示 ====================

.anonymous-hint {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background-color: rgba(251, 191, 36, 0.1);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.hint-icon {
  font-size: var(--font-size-base);
  color: var(--color-warning);
}

.hint-text {
  font-size: var(--font-size-sm);
  color: var(--color-warning);
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>