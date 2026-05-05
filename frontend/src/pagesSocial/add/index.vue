<template>
  <view class="add-page">
    <!-- 遮罩层 -->
    <view class="overlay" @tap="handleClose" />

    <!-- 操作菜单 -->
    <view class="action-sheet">
      <view class="sheet-header">
        <text class="sheet-title">选择发布类型</text>
      </view>
      <view class="sheet-options">
        <!-- 发布树洞 -->
        <view class="sheet-option" @tap="handlePublishTreehole">
          <view class="option-icon-wrapper treehole-option">
            <text class="option-icon-text">洞</text>
          </view>
          <view class="option-content">
            <text class="option-title">发布树洞吐槽</text>
            <text class="option-desc">匿名宣泄，获得共鸣</text>
          </view>
        </view>
        <!-- 发布动态 -->
        <view class="sheet-option" @tap="handlePublishSquare">
          <view class="option-icon-wrapper square-option">
            <text class="option-icon-text">动</text>
          </view>
          <view class="option-content">
            <text class="option-title">发布动态</text>
            <text class="option-desc">实名分享，连接好友</text>
          </view>
        </view>
        <!-- 记录日记 -->
        <view class="sheet-option" @tap="handleRecordDiary">
          <view class="option-icon-wrapper diary-option">
            <text class="option-icon-text">记</text>
          </view>
          <view class="option-content">
            <text class="option-title">记录情绪日记</text>
            <text class="option-desc">写下今天的心情</text>
          </view>
        </view>
      </view>
      <view class="sheet-cancel" @tap="handleClose">
        <text class="cancel-text">取消</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 快捷入口页（[+] 按钮分流）
 * 文件：src/pagesSocial/add/index.vue
 * 说明：中间 [+] 按钮的分流页面，提供快速创建树洞/动态/日记入口
 */
import { onShow, onBackPress } from '@dcloudio/uni-app'
import { track, EventName, trackPageEnter } from '@/utils/tracking'

/**
 * 关闭页面
 */
function handleClose(): void {
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/home/index' })
    },
  })
}

/**
 * 发布树洞
 */
function handlePublishTreehole(): void {
  track(EventName.TREEHOLE_CREATE_START, { source: 'add_shortcut' })
  uni.redirectTo({
    url: '/pagesSocial/treehole/publish',
  })
}

/**
 * 发布动态
 */
function handlePublishSquare(): void {
  track(EventName.SQUARE_CREATE_START, { source: 'add_shortcut' })
  uni.redirectTo({
    url: '/pagesSocial/square/publish',
  })
}

/**
 * 记录日记
 */
function handleRecordDiary(): void {
  track(EventName.DIARY_CREATE, { source: 'add_shortcut' })
  uni.redirectTo({
    url: '/pages/diary/edit',
  })
}

onShow(() => {
  trackPageEnter('add')
})

// 物理返回键也关闭页面
onBackPress(() => {
  handleClose()
  return true
})
</script>

<style lang="scss" scoped>
.add-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
}

.action-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-primary);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding-bottom: env(safe-area-inset-bottom);
}

.sheet-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-primary);
}

.sheet-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.sheet-options {
  display: flex;
  flex-direction: column;
}

.sheet-option {
  display: flex;
  align-items: center;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-primary);

  &:active {
    background-color: var(--bg-secondary);
  }
}

.option-icon-wrapper {
  width: 80rpx;
  height: 80rpx;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-md);
}

.treehole-option {
  background-color: rgba(139, 167, 196, 0.2);
}

.square-option {
  background-color: rgba(124, 111, 224, 0.2);
}

.diary-option {
  background-color: rgba(255, 154, 92, 0.2);
}

.option-icon-text {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.option-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.option-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.sheet-cancel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);

  &:active {
    background-color: var(--bg-secondary);
  }
}

.cancel-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
</style>
