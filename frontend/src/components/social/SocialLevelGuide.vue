<template>
  <view class="social-level-guide">
    <!-- 当前级别 -->
    <view class="current-level">
      <view class="level-badge">
        <text class="level-num">{{ socialLevel?.current_level || 1 }}</text>
      </view>
      <view class="level-info">
        <text class="level-name">{{ socialLevel?.level_name || getSocialLevelName(1) }}</text>
        <text class="level-desc">{{ socialLevel?.description || '开始你的社交旅程' }}</text>
      </view>
    </view>

    <!-- 级别进度 -->
    <view class="level-progress">
      <view
        v-for="i in 6"
        :key="i"
        class="level-step"
        :class="{
          'is-unlocked': isLevelUnlocked(i),
          'is-current': i === (socialLevel?.current_level ?? 1)
        }"
      >
        <view class="step-dot">
          <text v-if="isLevelUnlocked(i) && i < (socialLevel?.current_level ?? 1)" class="step-check">[已解锁]</text>
          <text v-else class="step-num">{{ i }}</text>
        </view>
        <text class="step-label">L{{ i }}</text>
      </view>

      <!-- 进度连线 -->
      <view class="progress-line">
        <view
          class="progress-fill"
          :style="{ width: progressWidth }"
        />
      </view>
    </view>

    <!-- 进度描述 -->
    <view class="progress-description">
      <text class="desc-text">{{ socialLevel?.progress_description || '继续探索，解锁更多功能' }}</text>
    </view>

    <!-- 建议下一步 -->
    <view v-if="socialLevel?.next_action" class="next-action">
      <view class="action-card" @tap="handleNextAction">
        <text class="action-icon">[建议]</text>
        <text class="action-text">{{ socialLevel.next_action }}</text>
        <text class="action-arrow">></text>
      </view>
    </view>

    <!-- 行为统计 -->
    <view v-if="showStats && socialLevel?.behavior_stats" class="behavior-stats">
      <text class="stats-title">社交行为统计</text>
      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-value">{{ socialLevel.behavior_stats.browse_count }}</text>
          <text class="stat-label">浏览</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ socialLevel.behavior_stats.like_count }}</text>
          <text class="stat-label">共鸣</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ socialLevel.behavior_stats.comment_count }}</text>
          <text class="stat-label">评论</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ socialLevel.behavior_stats.follow_count }}</text>
          <text class="stat-label">关注</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ socialLevel.behavior_stats.friend_request_count }}</text>
          <text class="stat-label">好友申请</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ socialLevel.behavior_stats.chat_count }}</text>
          <text class="stat-label">私聊</text>
        </view>
      </view>
    </view>

    <!-- 级别说明列表 -->
    <view v-if="showLevelDetails" class="level-details">
      <text class="details-title">社交级别说明</text>
      <view class="details-list">
        <view
          v-for="i in 6"
          :key="i"
          class="detail-item"
          :class="{ 'is-unlocked': isLevelUnlocked(i), 'is-current': i === (socialLevel?.current_level || 1) }"
        >
          <view class="detail-header">
            <view class="detail-badge">
              <text class="detail-level">Level {{ i }}</text>
            </view>
            <text v-if="isLevelUnlocked(i)" class="detail-status unlocked">已解锁</text>
            <text v-else class="detail-status locked">未解锁</text>
          </view>
          <text class="detail-desc">{{ getSocialLevelDescription(i) }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 渐进式社交暴露引导组件
 * 文件：src/components/social/SocialLevelGuide.vue
 * 说明：展示用户的社交级别进度，引导用户逐步解锁社交功能
 */

import { computed } from 'vue'
import {
  type SocialLevelResponse,
  getSocialLevelName,
  getSocialLevelDescription,
} from '@/api/modules/user'

// ==================== Props ====================

interface Props {
  /** 社交级别数据 */
  socialLevel?: SocialLevelResponse | null
  /** 是否显示行为统计 */
  showStats?: boolean
  /** 是否显示级别详情列表 */
  showLevelDetails?: boolean
  /** 是否紧凑模式 */
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  socialLevel: null,
  showStats: false,
  showLevelDetails: false,
  compact: false,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 点击下一步行动 */
  (e: 'action', action: string): void
}>()

// ==================== 计算属性 ====================

/** 进度宽度 */
const progressWidth = computed(() => {
  const level = props.socialLevel?.current_level || 1
  return `${((level - 1) / 5) * 100}%`
})

// ==================== 方法 ====================

/**
 * 判断级别是否解锁
 */
function isLevelUnlocked(level: number): boolean {
  if (!props.socialLevel) return level === 1
  const status = props.socialLevel.unlock_status
  switch (level) {
    case 1: return status.level_1
    case 2: return status.level_2
    case 3: return status.level_3
    case 4: return status.level_4
    case 5: return status.level_5
    case 6: return status.level_6
    default: return false
  }
}

/**
 * 处理下一步行动点击
 */
function handleNextAction(): void {
  const action = props.socialLevel?.next_action
  if (action) {
    emit('action', action)
  }
}
</script>

<style lang="scss" scoped>
.social-level-guide {
  display: flex;
  flex-direction: column;
}

// ==================== 当前级别 ====================

.current-level {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background: linear-gradient(135deg, rgba(124, 111, 224, 0.2), rgba(124, 111, 224, 0.1));
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-lg);
}

.level-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  background: linear-gradient(135deg, var(--brand-primary), var(--brand-dark));
  border-radius: var(--radius-full);
  margin-right: var(--space-md);
}

.level-num {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--text-on-brand);
}

.level-info {
  display: flex;
  flex-direction: column;
}

.level-name {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.level-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 级别进度 ====================

.level-progress {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0 var(--space-xs);
  margin-bottom: var(--space-lg);
}

.level-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

.step-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  background-color: var(--bg-tertiary);
  border: 2rpx solid var(--border-primary);
  border-radius: var(--radius-full);
  transition: all 0.3s ease;

  .is-unlocked & {
    background-color: var(--brand-primary);
    border-color: var(--brand-primary);
  }

  .is-current & {
    box-shadow: 0 0 0 8rpx rgba(124, 111, 224, 0.3);
  }
}

.step-num {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);

  .is-unlocked & {
    color: var(--text-on-brand);
  }
}

.step-check {
  font-size: var(--font-size-xs);
  color: var(--text-on-brand);
}

.step-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: 8rpx;
}

.progress-line {
  position: absolute;
  top: 27rpx;
  left: var(--space-sm);
  right: var(--space-sm);
  height: 4rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
  z-index: 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--brand-primary), var(--brand-light));
  border-radius: var(--radius-full);
  transition: width 0.5s ease;
}

// ==================== 进度描述 ====================

.progress-description {
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.desc-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

// ==================== 建议下一步 ====================

.next-action {
  margin-bottom: var(--space-lg);
}

.action-card {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--color-info-bg);
  border-radius: var(--radius-md);
  border: 1rpx solid var(--color-info);

  &:active {
    opacity: 0.9;
  }
}

.action-icon {
  font-size: var(--font-size-md);
  color: var(--color-info);
  margin-right: var(--space-sm);
}

.action-text {
  flex: 1;
  font-size: var(--font-size-sm);
  color: var(--color-info);
}

.action-arrow {
  font-size: var(--font-size-md);
  color: var(--color-info);
}

// ==================== 行为统计 ====================

.behavior-stats {
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-lg);
}

.stats-title {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-md);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 级别详情 ====================

.level-details {
  margin-top: var(--space-md);
}

.details-title {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-sm);
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.detail-item {
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  opacity: 0.6;

  &.is-unlocked {
    opacity: 1;
  }

  &.is-current {
    background-color: rgba(124, 111, 224, 0.1);
    border: 1rpx solid var(--brand-primary);
  }
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.detail-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rpx 16rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);

  .is-unlocked & {
    background-color: var(--brand-primary);
  }
}

.detail-level {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);

  .is-unlocked & {
    color: var(--text-on-brand);
  }
}

.detail-status {
  font-size: var(--font-size-xs);

  &.unlocked {
    color: var(--color-success);
  }

  &.locked {
    color: var(--text-tertiary);
  }
}

.detail-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
</style>
