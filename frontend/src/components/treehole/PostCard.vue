<template>
  <view class="post-card" @tap="handleTap">
    <!-- 匿名身份区域 -->
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
      <view class="post-meta">
        <text class="time-text">{{ post.fuzzy_time?.fuzzy_display || '' }}</text>
      </view>
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
          v-for="(url, index) in post.image_urls.slice(0, 3)"
          :key="index"
          class="post-image"
          :src="url"
          mode="aspectFill"
          @tap.stop="handleImageTap(index)"
        />
      </view>
    </view>

    <!-- 互动区域 -->
    <view class="post-actions">
      <view class="action-item" :class="{ 'is-active': post.has_resonated }" @tap.stop="handleResonance">
        <view class="action-icon-wrapper" :class="{ 'is-active': post.has_resonated }">
          <text class="action-icon-text">{{ post.has_resonated ? '✓' : '○' }}</text>
        </view>
        <text class="action-text">我懂你</text>
        <text v-if="post.resonance_count > 0" class="action-count">{{ formatCount(post.resonance_count) }}</text>
      </view>
      <view class="action-item" @tap.stop="handleComment">
        <view class="action-icon-wrapper">
          <text class="action-icon-text">评</text>
        </view>
        <text class="action-text">回声</text>
        <text v-if="post.comment_count > 0" class="action-count">{{ formatCount(post.comment_count) }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 树洞帖子卡片组件
 * 文件：src/components/treehole/PostCard.vue
 * 说明：用于信息流和列表中的帖子展示，包含匿名身份、内容、互动按钮
 */

import type { TreeholePost } from '@/api/treehole'
import { generateVirtualAvatar } from '@/api/treehole'

// ==================== Props ====================

const { post } = defineProps<{
  post: TreeholePost
}>()

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'tap', post: TreeholePost): void
  (e: 'resonance', post: TreeholePost): void
  (e: 'comment', post: TreeholePost): void
  (e: 'image-tap', index: number): void
}>()

// ==================== 方法 ====================

/**
 * 格式化计数
 */
function formatCount(count: number): string {
  if (count >= 1000) {
    return (count / 1000).toFixed(1) + 'k'
  }
  return String(count)
}

/**
 * 处理卡片点击
 */
function handleTap(): void {
  emit('tap', post)
}

/**
 * 处理共鸣点击
 */
function handleResonance(): void {
  emit('resonance', post)
}

/**
 * 处理评论点击
 */
function handleComment(): void {
  emit('comment', post)
}

/**
 * 处理图片点击
 */
function handleImageTap(index: number): void {
  emit('image-tap', index)
}
</script>

<style lang="scss" scoped>
.post-card {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-sm);

  &:active {
    opacity: 0.95;
  }
}

// ==================== 头部 ====================

.post-header {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-sm);
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

.post-meta {
  display: flex;
  align-items: center;
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

.topic-tag {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  margin-top: var(--space-sm);
  padding: 4rpx 16rpx;
  background-color: var(--brand-light);
  border-radius: var(--radius-full);
}

.topic-text {
  font-size: var(--font-size-sm);
  color: var(--brand-light);
}

.post-images {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
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
    background-color: var(--color-error);
  }
}

.action-icon-text {
  font-size: 24rpx;
  font-weight: 500;
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
</style>
