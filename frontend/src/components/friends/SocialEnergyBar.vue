<template>
  <view class="social-energy-bar">
    <!-- 能量条 -->
    <view class="energy-display">
      <text class="energy-label">社交能量</text>
      <view class="energy-icons">
        <text
          v-for="(bar, index) in energyBars"
          :key="index"
          class="energy-icon"
          :class="{ 'is-filled': bar.filled }"
          :style="{ color: bar.filled ? energyColor : 'var(--text-tertiary)' }"
        >{{ bar.filled ? '⚡' : '⚪' }}</text>
      </view>
      <text class="energy-percent">{{ energyPercent }}%</text>
    </view>

    <!-- 状态描述 -->
    <view class="energy-status">
      <text class="status-text">{{ energyStatusText }}</text>
    </view>

    <!-- 最近活动（可展开） -->
    <view v-if="showActivities && recentActivities.length > 0" class="activities-area">
      <text class="activities-title">最近社交活动</text>
      <view class="activities-list">
        <view
          v-for="activity in recentActivities"
          :key="activity.id"
          class="activity-item"
        >
          <text class="activity-desc">{{ activity.description }}</text>
          <text class="activity-time">{{ formatActivityTime(activity) }}</text>
        </view>
      </view>
    </view>

    <!-- AI 建议 -->
    <view v-if="aiSuggestion" class="ai-suggestion">
      <text class="suggestion-text">{{ aiSuggestion }}</text>
    </view>

    <!-- 操作按钮 -->
    <view v-if="showRestButton" class="action-area">
      <view class="rest-btn" @tap="handleRest">
        <text class="rest-icon">😴</text>
        <text class="rest-text">我想休息一会</text>
      </view>
    </view>

    <!-- 休息状态提示 -->
    <view v-if="isInRest" class="rest-status">
      <text class="rest-status-text">正在休息中...</text>
      <text class="rest-remaining">{{ formatRestTime(restRemainingSeconds) }}</text>
      <text class="rest-hint">暂时无法发送消息</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 社交能量条组件
 * 文件：src/components/friends/SocialEnergyBar.vue
 * 说明：社交能量可视化，显示能量条、活动记录、AI建议
 */

import { computed } from 'vue'
import { useSocialEnergy } from '@/composables/useSocialEnergy'
import type { SocialActivity } from '@/api/modules/chat'

// ==================== Props ====================

interface Props {
  /** 是否显示活动列表 */
  showActivities?: boolean
  /** 是否显示休息按钮 */
  showRestButton?: boolean
  /** 是否显示AI建议 */
  showSuggestion?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActivities: false,
  showRestButton: true,
  showSuggestion: true,
})

// ==================== Emits ====================

const emit = defineEmits<{
  /** 点击休息按钮 */
  (e: 'rest'): void
}>()

// ==================== 组合式函数 ====================

const {
  energyPercent,
  energyBars,
  energyStatusText,
  energyColor,
  isInRest,
  restRemainingSeconds,
  recentActivities,
  aiSuggestion,
  loadEnergy,
  startRest,
  formatActivityTime,
  formatRestTime,
} = useSocialEnergy()

// ==================== 方法 ====================

/**
 * 处理休息按钮点击
 */
async function handleRest(): Promise<void> {
  const success = await startRest()
  if (success) {
    emit('rest')
  }
}
</script>

<style lang="scss" scoped>
.social-energy-bar {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
}

// ==================== 能量显示 ====================

.energy-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.energy-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.energy-icons {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.energy-icon {
  font-size: var(--font-size-md);

  &.is-filled {
    animation: energyPulse 1.5s ease-in-out infinite;
  }
}

@keyframes energyPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.energy-percent {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
  font-weight: 500;
}

// ==================== 状态描述 ====================

.energy-status {
  margin-bottom: var(--space-sm);
}

.status-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 活动列表 ====================

.activities-area {
  margin-bottom: var(--space-md);
  padding: var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.activities-title {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.activity-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.activity-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== AI 建议 ====================

.ai-suggestion {
  margin-bottom: var(--space-md);
  padding: var(--space-sm);
  background-color: var(--brand-light);
  border-radius: var(--radius-sm);
}

.suggestion-text {
  font-size: var(--font-size-sm);
  color: var(--brand-light);
  line-height: 1.5;
}

// ==================== 操作按钮 ====================

.action-area {
  display: flex;
  align-items: center;
  justify-content: center;
}

.rest-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);

  &:active {
    opacity: 0.9;
  }
}

.rest-icon {
  font-size: var(--font-size-md);
}

.rest-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

// ==================== 休息状态 ====================

.rest-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--mood-calm-bg);
  border-radius: var(--radius-sm);
}

.rest-status-text {
  font-size: var(--font-size-md);
  color: var(--mood-calm);
  font-weight: 500;
  margin-bottom: 8rpx;
}

.rest-remaining {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: 8rpx;
}

.rest-hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}
</style>