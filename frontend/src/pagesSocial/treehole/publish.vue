<template>
  <view class="publish-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <wd-icon name="arrow-left" class="back-icon" />
      </view>
      <text class="header-title">发布吐槽</text>
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
      <!-- 匿名身份预览 -->
      <view class="identity-preview">
        <text class="preview-label">匿名身份</text>
        <view class="identity-card">
          <view class="avatar-wrapper">
            <view
              class="avatar-placeholder"
              :style="{ backgroundColor: previewAvatarColor }"
            >
              <wd-icon name="user" size="24px" color="#FFFFFF" />
            </view>
          </view>
          <view class="identity-info">
            <text class="nickname">{{ previewNickname }}</text>
            <text class="persona-text">{{ previewPersona }}</text>
          </view>
          <text class="hint-text">系统自动生成</text>
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

      <!-- 话题标签选择 -->
      <view class="topic-section">
        <text class="section-label">话题标签（可选）</text>
        <scroll-view class="topic-scroll" scroll-x>
          <view class="topic-list">
            <view
              v-for="topic in topics"
              :key="topic.value"
              class="topic-item"
              :class="{ 'is-active': selectedTopic === topic.value }"
              @tap="handleTopicSelect(topic.value)"
            >
              <text class="topic-text">#{{ topic.label }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- AI润色区域 -->
      <view class="ai-section">
        <view class="ai-header" @tap="handleAiRewrite">
          <wd-icon name="magic" size="20px" color="#01BEFF" />
          <text class="ai-title">AI润色</text>
          <text class="ai-hint">让表达更温暖</text>
        </view>

        <!-- AI润色预览 -->
        <view v-if="aiRewriteContent" class="ai-preview">
          <view class="preview-content">
            <text class="preview-label">润色后</text>
            <text class="preview-text">{{ aiRewriteContent }}</text>
          </view>
          <view class="preview-actions">
            <view class="action-btn" @tap="handleUseAiContent">
              <text class="action-text">使用</text>
            </view>
            <view class="action-btn secondary" @tap="handleRejectAiContent">
              <text class="action-text">保留原文</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 脱敏提醒 -->
      <view v-if="identityWarning" class="warning-section">
        <text class="warning-icon">!</text>
        <text class="warning-text">{{ identityWarning }}</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 树洞发布页
 * 文件：src/pages/treehole/publish.vue
 * 说明：匿名身份自动生成展示 + AI风格改写可选预览
 */

import { ref, computed, onMounted } from 'vue'
import {
  createTreeholePost,
  TOPIC_TAG_LABELS,
  type TopicResponse,
  type CreatePostResponse,
} from '@/api/treehole'
import { track, EventName, trackPageEnter } from '@/utils/tracking'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'

// ==================== 响应式状态 ====================

/** 输入内容 */
const content = ref('')

/** 选中的话题标签 */
const selectedTopic = ref<string | null>(null)

/** 话题列表 */
const topics = ref<TopicResponse[]>([])

/** 是否正在提交 */
const isSubmitting = ref(false)

/** AI润色内容 */
const aiRewriteContent = ref('')

/** 是否正在AI润色 */
const isAiRewriting = ref(false)

/** 脱敏提醒 */
const identityWarning = ref('')

/** 预览昵称 */
const previewNickname = ref('')

/** 预览气质标签 */
const previewPersona = ref('')

/** 预览头像颜色 */
const previewAvatarColor = ref('#E72F8C')

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 是否自动聚焦 */
const autoFocus = ref(false)

/** 占位符 */
const placeholder = '今天想吐槽什么？在这里说出来...'

/** 初始内容（从URL参数传入） */
let initialContent = ''

/** 是否触发AI润色 */
let triggerAiRewrite = false

// ==================== 计算属性 ====================

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
 * 加载话题列表
 */
function loadTopics(): void {
  topics.value = Object.entries(TOPIC_TAG_LABELS).map(([value, label]) => ({
    value,
    label,
  }))
}

/**
 * 生成预览身份
 */
function generatePreviewIdentity(): void {
  // 预设的匿名昵称词库
  const adjectives = ['迷路的', '倔强的', '温柔的', '沉默的', '深夜的', '孤独的', '安静的', '忧郁的']
  const nouns = ['信天翁', '蒲公英', '月亮', '星星', '猫', '云朵', '旅人', '听风者']

  // 基于时间戳生成稳定的随机身份
  const seed = Date.now()
  const adjIndex = seed % adjectives.length
  const nounIndex = (seed * 7) % nouns.length

  previewNickname.value = adjectives[adjIndex] + nouns[nounIndex]

  // 气质标签
  const personas = ['温柔系', '佛系', '话痨系', '毒舌系', '文艺系', '憨憨系', '社恐系', '老灵魂']
  previewPersona.value = personas[(seed * 3) % personas.length]

  // 头像颜色
  const colors = ['#FF9A5C', '#838383', '#01BEFF', '#E72F8C', '#01BEFF', '#3D7EFF', '#892FE8', '#5F7E8B']
  previewAvatarColor.value = colors[seed % colors.length]
}

/**
 * 处理话题选择
 */
function handleTopicSelect(topic: string): void {
  selectedTopic.value = selectedTopic.value === topic ? null : topic
}

/**
 * 处理AI润色
 */
async function handleAiRewrite(): Promise<void> {
  if (!content.value.trim() || isAiRewriting.value) return

  isAiRewriting.value = true

  try {
    // TODO: 调用后端AI润色API
    // 这里暂时模拟润色效果
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // 简单模拟润色：添加一些温暖的表达
    const originalContent = content.value.trim()
    aiRewriteContent.value = `${originalContent}\n\n（这只是一个模拟的润色效果，实际需要调用后端AI服务）`

    track(EventName.TREEHOLE_AI_REWRITE, { content_length: originalContent.length })
  } catch (error) {
    console.error('AI润色失败', error)
    uni.showToast({
      title: '润色失败，请重试',
      icon: 'none',
    })
  } finally {
    isAiRewriting.value = false
  }
}

/**
 * 使用AI润色内容
 */
function handleUseAiContent(): void {
  if (aiRewriteContent.value) {
    content.value = aiRewriteContent.value
    aiRewriteContent.value = ''
  }
}

/**
 * 保留原文
 */
function handleRejectAiContent(): void {
  aiRewriteContent.value = ''
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
    const result: CreatePostResponse = await createTreeholePost({
      content: publishContent,
      topic_tag: selectedTopic.value,
    })

    // 检查审核反馈
    if (result.audit_feedback) {
      uni.showModal({
        title: '温馨提示',
        content: result.audit_feedback.feedback,
        showCancel: false,
        confirmText: '我知道了',
      })

      track(EventName.TREEHOLE_CREATE_BLOCKED, {
        labels: result.audit_feedback.labels,
      })
      return
    }

    // 检查脱敏提醒
    if (result.identity_warning?.has_warning) {
      identityWarning.value = result.identity_warning.warning_message
    }

    uni.showToast({
      title: '发布成功',
      icon: 'success',
    })

    track(EventName.TREEHOLE_CREATE_SUCCESS, {
      post_id: result.post?.id,
      has_topic: !!selectedTopic.value,
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
 * 处理返回
 */
function handleBack(): void {
  if (content.value.trim()) {
    uni.showModal({
      title: '提示',
      content: '内容尚未发布，确定要退出吗？',
      confirmText: '退出',
      confirmColor: '#E83A30',
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

/**
 * 解析页面参数
 */
function parsePageParams(): void {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = (currentPage as any).options || {}

  initialContent = options.content ? decodeURIComponent(options.content) : ''
  triggerAiRewrite = options.ai_rewrite === 'true'

  if (initialContent) {
    content.value = initialContent
  }

  if (triggerAiRewrite && initialContent) {
    autoFocus.value = false
    // 延迟触发AI润色
    setTimeout(() => {
      handleAiRewrite()
    }, 500)
  } else {
    autoFocus.value = true
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
  loadTopics()
  generatePreviewIdentity()
  parsePageParams()
})

usePageVisibleRefresh({
  onVisible() {
    trackPageEnter('treehole_publish')
  }
})
</script>

<style lang="scss" scoped>
.publish-page {
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

.publish-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8rpx 24rpx;
  background: linear-gradient(135deg, #78909C, #5F7E8B);
  border-radius: 5000rpx;
  box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(120, 144, 156, 0.35);

  &:active {
    opacity: 0.8;
  }

  &.is-disabled {
    background: #F4F4F5;
    box-shadow: none;

    .publish-text {
      color: #838383;
    }
  }
}

.publish-text {
  font-size: 26rpx;
  color: #FFFFFF;
  font-weight: 500;
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
  padding: 24rpx;
}

// ==================== 匿名身份预览 ====================

.identity-preview {
  margin-bottom: 24rpx;
}

.preview-label {
  font-size: 26rpx;
  color: #838383;
  margin-bottom: 16rpx;
}

.identity-card {
  display: flex;
  align-items: center;
  padding: 16rpx 24rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.05);
}

.avatar-wrapper {
  width: 64rpx;
  height: 64rpx;
  margin-right: 16rpx;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 5000rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 28rpx;
  color: #FFFFFF;
}

.identity-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.nickname {
  font-size: 26rpx;
  font-weight: 500;
  color: #080808;
}

.persona-text {
  font-size: 22rpx;
  color: #838383;
}

.hint-text {
  font-size: 22rpx;
  color: #838383;
}

// ==================== 内容输入 ====================

.content-section {
  margin-bottom: 24rpx;
}

.content-input {
  width: 100%;
  min-height: 300rpx;
  padding: 24rpx;
  font-size: 28rpx;
  color: #080808;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.05);
  line-height: 1.6;
}

.input-placeholder {
  color: #838383;
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8rpx;
}

.char-count {
  font-size: 22rpx;
  color: #838383;
}

// ==================== 话题选择 ====================

.topic-section {
  margin-bottom: 24rpx;
}

.section-label {
  font-size: 26rpx;
  color: #838383;
  margin-bottom: 16rpx;
}

.topic-scroll {
  margin-bottom: 16rpx;
}

.topic-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.topic-item {
  display: inline-flex;
  align-items: center;
  height: 64rpx;
  padding: 0 24rpx;
  background-color: #FFFFFF;
  border-radius: 5000rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.05);

  &:active {
    opacity: 0.8;
  }

  &.is-active {
    background: linear-gradient(135deg, #78909C, #5F7E8B);
    box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(120, 144, 156, 0.35);

    .topic-text {
      color: #FFFFFF;
    }
  }
}

.topic-text {
  font-size: 26rpx;
  color: #333333;
  white-space: nowrap;
}

// ==================== AI润色区域 ====================

.ai-section {
  margin-bottom: 24rpx;
  padding: 24rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0, 0, 0, 0.05);
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 16rpx;

  &:active {
    opacity: 0.8;
  }
}

.ai-icon {
  font-size: 30rpx;
}

.ai-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #080808;
}

.ai-hint {
  font-size: 22rpx;
  color: #838383;
}

.ai-preview {
  margin-top: 24rpx;
  padding: 16rpx;
  background-color: #F4F4F5;
  border-radius: 10rpx;
}

.preview-content {
  display: flex;
  flex-direction: column;
  margin-bottom: 16rpx;
}

.preview-label {
  font-size: 22rpx;
  color: #78909C;
  margin-bottom: 8rpx;
}

.preview-text {
  font-size: 26rpx;
  color: #080808;
  line-height: 1.5;
}

.preview-actions {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  background: linear-gradient(135deg, #78909C, #5F7E8B);
  border-radius: 10rpx;

  &:active {
    opacity: 0.8;
  }

  &.secondary {
    background-color: #F8F8FA;

    .action-text {
      color: #333333;
    }
  }
}

.action-text {
  font-size: 26rpx;
  color: #FFFFFF;
}

// ==================== 脱敏提醒 ====================

.warning-section {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  padding: 24rpx;
  background-color: rgba(255, 190, 40, 0.1);
  border-radius: 20rpx;
  margin-bottom: 24rpx;
}

.warning-icon {
  font-size: 28rpx;
  color: #FFBE28;
}

.warning-text {
  flex: 1;
  font-size: 26rpx;
  color: #FFBE28;
  line-height: 1.5;
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>
