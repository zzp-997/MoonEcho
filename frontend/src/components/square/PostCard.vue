<template>
  <view class="post-card" @tap="handleTap">
    <!-- 作者身份区域 -->
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
          <wd-icon name="user" size="20px" color="var(--text-inverse)" />
        </view>
      </view>
      <view class="identity-info">
        <text class="nickname">{{ displayNickname }}</text>
        <view v-if="displayPersonaTag" class="persona-tag">
          <text class="tag-text">{{ displayPersonaTag }}</text>
        </view>
      </view>
      <view class="post-meta">
        <text class="time-text">{{ post.fuzzy_time?.fuzzy_display || '' }}</text>
      </view>
    </view>

    <!-- 动态内容 -->
    <view class="post-content">
      <text class="content-text">{{ post.content }}</text>
      <!-- 图片 -->
      <view v-if="post.image_urls && post.image_urls.length > 0" class="post-images">
        <image
          v-for="(url, index) in post.image_urls.slice(0, 9)"
          :key="index"
          class="post-image"
          :class="{ 'is-single': post.image_urls?.length === 1 }"
          :src="url"
          mode="aspectFill"
          @tap.stop="handleImageTap(index)"
        />
      </view>
    </view>

    <!-- 互动区域 -->
    <view class="post-actions">
      <!-- 共鸣按钮 -->
      <view
        class="action-item"
        :class="{ 'is-active': post.has_resonated }"
        @tap.stop="handleResonance"
      >
        <text class="action-icon">{{ post.has_resonated ? '共鸣' : '共鸣' }}</text>
        <text v-if="post.resonance_count > 0" class="action-count">
          {{ formatCount(post.resonance_count) }}
        </text>
      </view>

      <!-- 评论按钮 -->
      <view class="action-item" @tap.stop="handleComment">
        <text class="action-icon">评论</text>
        <text v-if="post.comment_count > 0" class="action-count">
          {{ formatCount(post.comment_count) }}
        </text>
      </view>

      <!-- 收藏按钮 -->
      <view
        class="action-item"
        :class="{ 'is-active': post.has_bookmarked }"
        @tap.stop="handleBookmark"
      >
        <text class="action-icon">{{ post.has_bookmarked ? '已收藏' : '收藏' }}</text>
      </view>

      <!-- 关注按钮（仅实名动态显示） -->
      <view
        v-if="!post.is_anonymous && !post.author?.is_me && !post.has_whisper_followed"
        class="action-item follow-action"
        @tap.stop="handleWhisperFollow"
      >
        <text class="action-icon">关注</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 动态广场卡片组件
 * 文件：src/components/square/PostCard.vue
 * 说明：用于动态广场信息流中的帖子展示，支持实名/匿名展示
 * 设计要点：实名动态显示用户头像昵称，匿名动态显示随机虚拟身份
 */

import { computed } from 'vue'
import type { Post } from '@/api/modules/post'
import { formatPostCount } from '@/api/modules/post'

// ==================== Props ====================

const props = defineProps<{
  post: Post
}>()

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'tap', post: Post): void
  (e: 'resonance', post: Post): void
  (e: 'comment', post: Post): void
  (e: 'bookmark', post: Post): void
  (e: 'whisper-follow', post: Post): void
  (e: 'image-tap', index: number): void
}>()

// ==================== 响应式状态 ====================

// ==================== 计算属性 ====================

/** 显示的头像 */
const displayAvatar = computed(() => {
  if (props.post.is_anonymous) {
    return props.post.anon_identity?.anon_avatar_url || null
  }
  return props.post.author?.avatar_url || null
})

/** 显示的昵称 */
const displayNickname = computed(() => {
  if (props.post.is_anonymous) {
    return props.post.anon_identity?.anon_nickname || '匿名用户'
  }
  return props.post.author?.nickname || '用户'
})

/** 显示的气质标签（仅匿名动态） */
const displayPersonaTag = computed(() => {
  if (props.post.is_anonymous) {
    return props.post.anon_identity?.persona_tag || null
  }
  return null
})

/** 匿名头像颜色（无头像时使用） */
const anonAvatarColor = computed(() => {
  // 基于动态ID生成稳定的颜色
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
  const seed = props.post.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[seed % colors.length]
})

// ==================== 方法 ====================

/**
 * 格式化计数
 */
function formatCount(count: number): string {
  return formatPostCount(count)
}

/**
 * 处理卡片点击
 */
function handleTap(): void {
  emit('tap', props.post)
}

/**
 * 处理共鸣点击
 */
function handleResonance(): void {
  emit('resonance', props.post)
}

/**
 * 处理评论点击
 */
function handleComment(): void {
  emit('comment', props.post)
}

/**
 * 处理收藏点击
 */
function handleBookmark(): void {
  emit('bookmark', props.post)
}

/**
 * 处理悄悄关注点击
 */
function handleWhisperFollow(): void {
  emit('whisper-follow', props.post)
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

.post-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
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
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.post-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: var(--radius-md);
  background-color: var(--bg-tertiary);

  &.is-single {
    width: 400rpx;
    height: 300rpx;
  }
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
    .action-icon {
      color: var(--brand-primary);
    }
  }
}

.action-icon {
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
</style>