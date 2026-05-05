<template>
  <view class="community-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="header-title">
        <text class="title-text">动态</text>
        <text class="title-hint">树洞 & 广场</text>
      </view>
      <view class="header-actions">
        <view class="action-btn" @tap="handleGoSquare">
          <text class="action-icon">+</text>
        </view>
      </view>
    </view>

    <!-- 功能入口卡片 -->
    <view class="entry-cards">
      <!-- 树洞入口 -->
      <view class="entry-card treehole-card" @tap="handleGoTreehole">
        <view class="card-icon treehole-icon">
          <text class="icon-text">洞</text>
        </view>
        <view class="card-content">
          <text class="card-title">树洞</text>
          <text class="card-desc">匿名吐槽，把没处说的话丢出来</text>
        </view>
        <view class="card-arrow">
          <text class="arrow-text">></text>
        </view>
      </view>

      <!-- 广场入口 -->
      <view class="entry-card square-card" @tap="handleGoSquare">
        <view class="card-icon square-icon">
          <text class="icon-text">场</text>
        </view>
        <view class="card-content">
          <text class="card-title">广场</text>
          <text class="card-desc">实名分享，看看大家在聊什么</text>
        </view>
        <view class="card-arrow">
          <text class="arrow-text">></text>
        </view>
      </view>
    </view>

    <!-- 底部提示 -->
    <view class="bottom-hint">
      <text class="hint-text">点击上方卡片进入对应功能</text>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 动态入口页（社区）
 * 文件：src/pagesSocial/community/index.vue
 * 说明：社区动态入口，整合树洞和广场功能
 *       阶段二已完成，提供两个功能入口
 */
import { onShow } from '@dcloudio/uni-app'
import { track, EventName, trackPageEnter } from '@/utils/tracking'

/**
 * 跳转到树洞页面
 */
function handleGoTreehole(): void {
  track(EventName.TREEHOLE_LIST_VIEW, { source: 'community_entry' })
  uni.navigateTo({
    url: '/pagesSocial/treehole/index',
  })
}

/**
 * 跳转到广场页面
 */
function handleGoSquare(): void {
  track(EventName.SQUARE_LIST_VIEW, { source: 'community_entry' })
  uni.navigateTo({
    url: '/pagesSocial/square/index',
  })
}

onShow(() => {
  trackPageEnter('community')
})
</script>

<style lang="scss" scoped>
.community-page {
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

.header-title {
  display: flex;
  flex-direction: column;
}

.title-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.title-hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  background-color: var(--brand-primary);
  border-radius: 50%;

  &:active {
    opacity: 0.9;
  }
}

.action-icon {
  font-size: var(--font-size-lg);
  color: var(--text-on-brand);
}

// ==================== 入口卡片 ====================

.entry-cards {
  display: flex;
  flex-direction: column;
  padding: var(--space-lg) var(--space-md);
  gap: var(--space-md);
}

.entry-card {
  display: flex;
  align-items: center;
  padding: var(--space-lg);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);

  &:active {
    opacity: 0.9;
  }
}

.card-icon {
  width: 100rpx;
  height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-md);
  border-radius: var(--radius-md);
}

.treehole-icon {
  background-color: rgba(139, 167, 196, 0.2);
}

.square-icon {
  background-color: rgba(124, 111, 224, 0.2);
}

.icon-text {
  font-size: 36rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.card-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.card-arrow {
  display: flex;
  align-items: center;
}

.arrow-text {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
}

// ==================== 底部提示 ====================

.bottom-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl) var(--space-md);
}

.hint-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}
</style>
