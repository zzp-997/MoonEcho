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
              <wd-icon name="user" size="24px" color="var(--text-inverse)" />
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
          <wd-icon name="magic" size="20px" color="var(--brand-primary)" />
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
import { onShow } from '@dcloudio/uni-app'
import {
  createTreeholePost,
  TOPIC_TAG_LABELS,
  type TopicResponse,
  type CreatePostResponse,
} from '@/api/treehole'
import { track, EventName, trackPageEnter } from '@/utils/tracking'

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
const previewAvatarColor = ref('#A89CF5')

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
  const colors = ['#FFB5BA', '#8B9DC3', '#7CB9A0', '#A89CF5', '#FFB88A', '#A5C0D6', '#D4A5D9', '#8B6C9A']
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

onShow(() => {
  trackPageEnter('treehole_publish')
})
</script>

<style lang="scss" scoped>
.publish-page {
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
    background-color: var(--dark-bg-tertiary);

    .publish-text {
      color: var(--dark-text-tertiary);
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

// ==================== 匿名身份预览 ====================

.identity-preview {
  margin-bottom: var(--space-md);
}

.preview-label {
  font-size: var(--font-size-sm);
  color: var(--dark-text-tertiary);
  margin-bottom: var(--space-sm);
}

.identity-card {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background-color: var(--dark-bg-secondary);
  border-radius: var(--radius-md);
}

.avatar-wrapper {
  width: 64rpx;
  height: 64rpx;
  margin-right: var(--space-sm);
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
}

.nickname {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--dark-text-primary);
}

.persona-text {
  font-size: var(--font-size-xs);
  color: var(--dark-text-tertiary);
}

.hint-text {
  font-size: var(--font-size-xs);
  color: var(--dark-text-tertiary);
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
  color: var(--dark-text-primary);
  background-color: var(--dark-bg-secondary);
  border-radius: var(--radius-md);
  line-height: 1.6;
}

.input-placeholder {
  color: var(--dark-text-tertiary);
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-xs);
}

.char-count {
  font-size: var(--font-size-xs);
  color: var(--dark-text-tertiary);
}

// ==================== 话题选择 ====================

.topic-section {
  margin-bottom: var(--space-md);
}

.section-label {
  font-size: var(--font-size-sm);
  color: var(--dark-text-tertiary);
  margin-bottom: var(--space-sm);
}

.topic-scroll {
  margin-bottom: var(--space-sm);
}

.topic-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.topic-item {
  display: inline-flex;
  align-items: center;
  height: 64rpx;
  padding: 0 var(--space-md);
  background-color: var(--dark-bg-secondary);
  border-radius: var(--radius-full);

  &:active {
    opacity: 0.8;
  }

  &.is-active {
    background-color: var(--brand-primary);

    .topic-text {
      color: var(--text-on-brand);
    }
  }
}

.topic-text {
  font-size: var(--font-size-sm);
  color: var(--dark-text-secondary);
  white-space: nowrap;
}

// ==================== AI润色区域 ====================

.ai-section {
  margin-bottom: var(--space-md);
  padding: var(--space-md);
  background-color: var(--dark-bg-secondary);
  border-radius: var(--radius-md);
}

.ai-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);

  &:active {
    opacity: 0.8;
  }
}

.ai-icon {
  font-size: var(--font-size-md);
}

.ai-title {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--dark-text-primary);
}

.ai-hint {
  font-size: var(--font-size-xs);
  color: var(--dark-text-tertiary);
}

.ai-preview {
  margin-top: var(--space-md);
  padding: var(--space-sm);
  background-color: var(--dark-bg-tertiary);
  border-radius: var(--radius-sm);
}

.preview-content {
  display: flex;
  flex-direction: column;
  margin-bottom: var(--space-sm);
}

.preview-label {
  font-size: var(--font-size-xs);
  color: var(--brand-light);
  margin-bottom: var(--space-xs);
}

.preview-text {
  font-size: var(--font-size-sm);
  color: var(--dark-text-primary);
  line-height: 1.5;
}

.preview-actions {
  display: flex;
  gap: var(--space-sm);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-sm);

  &:active {
    opacity: 0.8;
  }

  &.secondary {
    background-color: var(--dark-bg-secondary);

    .action-text {
      color: var(--dark-text-secondary);
    }
  }
}

.action-text {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);
}

// ==================== 脱敏提醒 ====================

.warning-section {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-md);
  background-color: rgba(251, 191, 36, 0.1);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.warning-icon {
  font-size: var(--font-size-base);
  color: var(--color-warning);
}

.warning-text {
  flex: 1;
  font-size: var(--font-size-sm);
  color: var(--color-warning);
  line-height: 1.5;
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>
