<template>
  <view class="ai-tags-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <text class="back-icon">&lt;</text>
      </view>
      <text class="header-title">AI画像</text>
      <view class="placeholder" />
    </view>

    <!-- 说明区域 -->
    <view class="intro-section">
      <text class="intro-text">AI根据你的使用行为，为你生成了个性化的画像标签。你可以选择隐藏不想公开的标签。</text>
    </view>

    <!-- 加载中 -->
    <view v-if="isLoading" class="loading-area">
      <wd-loading />
    </view>

    <!-- 画像标签列表 -->
    <view v-else class="tags-container">
      <!-- 情绪模式 -->
      <view v-if="emotionTags.length > 0" class="tag-group">
        <view class="group-header">
          <text class="group-icon">[情绪]</text>
          <text class="group-title">情绪模式</text>
        </view>
        <view class="tags-list">
          <view
            v-for="(tag, index) in emotionTags"
            :key="index"
            class="tag-card"
            :class="{ 'is-hidden': !tag.is_visible }"
          >
            <view class="tag-content">
              <text class="tag-value">{{ tag.tag_value }}</text>
              <text class="tag-name">{{ tag.tag_name }}</text>
            </view>
            <view class="tag-control" @tap="handleToggleVisibility(tag)">
              <text class="control-text">{{ tag.is_visible ? '公开' : '隐藏' }}</text>
              <wd-switch :model-value="tag.is_visible" size="small" />
            </view>
          </view>
        </view>
      </view>

      <!-- 社交偏好 -->
      <view v-if="socialTags.length > 0" class="tag-group">
        <view class="group-header">
          <text class="group-icon">[社交]</text>
          <text class="group-title">社交偏好</text>
        </view>
        <view class="tags-list">
          <view
            v-for="(tag, index) in socialTags"
            :key="index"
            class="tag-card"
            :class="{ 'is-hidden': !tag.is_visible }"
          >
            <view class="tag-content">
              <text class="tag-value">{{ tag.tag_value }}</text>
              <text class="tag-name">{{ tag.tag_name }}</text>
            </view>
            <view class="tag-control" @tap="handleToggleVisibility(tag)">
              <text class="control-text">{{ tag.is_visible ? '公开' : '隐藏' }}</text>
              <wd-switch :model-value="tag.is_visible" size="small" />
            </view>
          </view>
        </view>
      </view>

      <!-- 兴趣领域 -->
      <view v-if="interestTags.length > 0" class="tag-group">
        <view class="group-header">
          <text class="group-icon">[兴趣]</text>
          <text class="group-title">兴趣领域</text>
        </view>
        <view class="tags-list">
          <view
            v-for="(tag, index) in interestTags"
            :key="index"
            class="tag-card"
            :class="{ 'is-hidden': !tag.is_visible }"
          >
            <view class="tag-content">
              <text class="tag-value">{{ tag.tag_value }}</text>
              <text class="tag-name">{{ tag.tag_name }}</text>
            </view>
            <view class="tag-control" @tap="handleToggleVisibility(tag)">
              <text class="control-text">{{ tag.is_visible ? '公开' : '隐藏' }}</text>
              <wd-switch :model-value="tag.is_visible" size="small" />
            </view>
          </view>
        </view>
      </view>

      <!-- 无标签 -->
      <view v-if="allTags.length === 0" class="empty-area">
        <view class="empty-icon">[AI]</view>
        <text class="empty-title">暂无画像数据</text>
        <text class="empty-desc">继续使用应用后，AI会为你生成个性化画像。建议：</text>
        <view class="suggestions">
          <text class="suggestion-item">记录更多日记</text>
          <text class="suggestion-item">与AI朋友互动</text>
          <text class="suggestion-item">浏览和参与动态广场</text>
        </view>
      </view>
    </view>

    <!-- 生成时间 -->
    <view v-if="generatedAt && !isLoading" class="generated-info">
      <text class="generated-text">AI画像于 {{ formatGeneratedTime(generatedAt) }} 生成</text>
    </view>

    <!-- 提示信息 -->
    <view v-if="message && !isLoading" class="message-section">
      <text class="message-text">{{ message }}</text>
    </view>

    <!-- 操作按钮 -->
    <view v-if="!isLoading && allTags.length > 0" class="action-section">
      <view class="action-btn" @tap="handleRefreshTags">
        <text class="btn-text">刷新画像</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - AI画像页面
 * 文件：src/pages/profile/ai-tags.vue
 * 说明：展示AI生成的用户画像标签，支持隐藏/公开控制
 */

import { ref, computed, onMounted } from 'vue'
import {
  getMyProfileTags,
  type AIProfileTagResponse,
  type ProfileTagItem,
} from '@/api/modules/user'
import { track, EventName } from '@/utils/tracking'

// ==================== 响应式状态 ====================

/** 所有标签 */
const allTags = ref<ProfileTagItem[]>([])

/** 生成时间 */
const generatedAt = ref<string | null>(null)

/** 提示信息 */
const message = ref<string | null>(null)

/** 是否正在加载 */
const isLoading = ref(false)

// ==================== 计算属性 ====================

/** 情绪模式标签 */
const emotionTags = computed(() => {
  return allTags.value.filter(tag => tag.tag_type === 'emotion_pattern')
})

/** 社交偏好标签 */
const socialTags = computed(() => {
  return allTags.value.filter(tag => tag.tag_type === 'social_preference')
})

/** 兴趣领域标签 */
const interestTags = computed(() => {
  return allTags.value.filter(tag => tag.tag_type === 'interest')
})

// ==================== 方法 ====================

/**
 * 加载画像标签
 */
async function loadTags(): Promise<void> {
  isLoading.value = true

  try {
    const response: AIProfileTagResponse = await getMyProfileTags()
    allTags.value = response.tags || []
    generatedAt.value = response.generated_at || null
    message.value = response.message || null

    track(EventName.PAGE_VIEW, { page: 'ai_tags' })
  } catch (error) {
    console.error('加载画像标签失败', error)
  } finally {
    isLoading.value = false
  }
}

/**
 * 切换标签可见性
 */
async function handleToggleVisibility(tag: ProfileTagItem): Promise<void> {
  tag.is_visible = !tag.is_visible

  // TODO: 调用后端API保存可见性设置
  track(EventName.SETTING_CHANGE, {
    setting: 'ai_tag_visibility',
    tag_type: tag.tag_type,
    tag_value: tag.tag_value,
    is_visible: tag.is_visible,
  })

  uni.showToast({
    title: tag.is_visible ? '已公开' : '已隐藏',
    icon: 'none',
  })
}

/**
 * 刷新画像
 */
async function handleRefreshTags(): Promise<void> {
  isLoading.value = true

  try {
    // TODO: 调用刷新画像API
    await loadTags()

    uni.showToast({
      title: '画像已更新',
      icon: 'success',
    })
  } catch (error) {
    console.error('刷新画像失败', error)
    uni.showToast({
      title: '刷新失败',
      icon: 'none',
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 格式化生成时间
 */
function formatGeneratedTime(isoString: string): string {
  if (!isoString) return ''

  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return '今天'
    } else if (diffDays === 1) {
      return '昨天'
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      const month = date.getMonth() + 1
      const day = date.getDate()
      return `${month}月${day}日`
    }
  } catch {
    return ''
  }
}

/**
 * 返回
 */
function handleBack(): void {
  uni.navigateBack()
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadTags()
})
</script>

<style lang="scss" scoped>
.ai-tags-page {
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

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-primary);
}

.placeholder {
  width: 64rpx;
}

// ==================== 说明区域 ====================

.intro-section {
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  margin: var(--space-md);
  border-radius: var(--radius-md);
}

.intro-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

// ==================== 加载状态 ====================

.loading-area {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
}

// ==================== 标签分组 ====================

.tags-container {
  flex: 1;
  padding: 0 var(--space-md);
}

.tag-group {
  margin-bottom: var(--space-lg);
}

.group-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.group-icon {
  font-size: var(--font-size-md);
  color: var(--brand-primary);
}

.group-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.tags-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.tag-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  transition: all 0.3s ease;

  &.is-hidden {
    opacity: 0.6;
    background-color: var(--bg-tertiary);
  }
}

.tag-content {
  display: flex;
  flex-direction: column;
}

.tag-value {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.tag-name {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.tag-control {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.control-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 空状态 ====================

.empty-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-2xl) var(--space-md);
}

.empty-icon {
  font-size: 80rpx;
  color: var(--brand-primary);
  margin-bottom: var(--space-md);
}

.empty-title {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.empty-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.suggestions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
}

.suggestion-item {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

// ==================== 生成信息 ====================

.generated-info {
  display: flex;
  justify-content: center;
  padding: var(--space-sm) var(--space-md);
}

.generated-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 提示信息 ====================

.message-section {
  margin: var(--space-sm) var(--space-md);
  padding: var(--space-md);
  background-color: var(--color-info-bg);
  border-radius: var(--radius-md);
}

.message-text {
  font-size: var(--font-size-sm);
  color: var(--color-info);
  line-height: 1.5;
}

// ==================== 操作按钮 ====================

.action-section {
  padding: var(--space-lg) var(--space-md);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.btn-text {
  font-size: var(--font-size-md);
  color: var(--brand-primary);
}
</style>