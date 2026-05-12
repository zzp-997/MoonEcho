<template>
  <view class="tn-tabbar">
    <view
      v-for="(item, index) in tabItems"
      :key="item.path"
      class="tabbar-item"
      :class="{ active: activeIndex === index }"
      @tap="handleTabTap(item, index)"
    >
      <view class="tabbar-icon">
        <text :style="{ fontSize: '42rpx', color: activeIndex === index ? '#01BEFF' : '#838383' }">
          {{ item.emoji }}
        </text>
      </view>
      <text class="tabbar-label" :class="{ 'label-active': activeIndex === index }">
        {{ item.text }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface TabItem {
  path: string
  text: string
  emoji: string
}

const tabItems: TabItem[] = [
  { path: '/pages/home/index', text: '首页', emoji: '🏠' },
  { path: '/pages/diary/index', text: '日记', emoji: '📅' },
  { path: '/pagesSocial/square/index', text: '广场', emoji: '⭐' },
  { path: '/pages/mine/index', text: '我的', emoji: '👤' },
]

const activeIndex = ref(0)

function getCurrentTabIndex(): number {
  const currentPage = getCurrentPages()
  if (currentPage.length === 0) return 0
  const currentPath = '/' + currentPage[currentPage.length - 1].route
  const index = tabItems.findIndex(item => currentPath.includes(item.path.replace(/^\//, '')))
  return index >= 0 ? index : 0
}

function handleTabTap(item: TabItem, _index: number): void {
  uni.switchTab({
    url: item.path,
    fail: () => {
      uni.reLaunch({ url: item.path })
    },
  })
}

function updateActiveIndex(): void {
  activeIndex.value = getCurrentTabIndex()
}

onMounted(() => {
  updateActiveIndex()
})

uni.$on('onTabBarMidUpdate', updateActiveIndex)
</script>

<style lang="scss" scoped>
.tn-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 999;
  display: flex;
  align-items: center;
  min-height: 110rpx;
  justify-content: space-between;
  padding: 0;
  padding-bottom: env(safe-area-inset-bottom);
  background-color: #FFFFFF;
  box-shadow: 0rpx 0rpx 30rpx 0rpx rgba(0, 0, 0, 0.07);
}

.tabbar-item {
  font-size: 22rpx;
  position: relative;
  flex: 1;
  text-align: center;
  padding: 10rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;

  &:active {
    opacity: 0.7;
  }
}

.tabbar-icon {
  width: 100rpx;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: auto;
  margin: 0 auto 4rpx;
}

.tabbar-label {
  font-size: 22rpx;
  color: #838383;

  &.label-active {
    color: #01BEFF;
    font-weight: 600;
  }
}
</style>
