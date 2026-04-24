<template>
  <view class="container">
    <text class="title">回声</text>
    <text class="subtitle">深夜情绪急救站</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 首页
 * 文件：src/pages/index/index.vue
 * 说明：应用首页，引导入口
 */
import { onShow } from '@dcloudio/uni-app'
import { trackPageEnter, trackPageLeave, checkDailyActive } from '@/utils/tracking'

onShow(() => {
  trackPageEnter('index')
  checkDailyActive()
})
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--bg-primary);
  padding: var(--space-lg);
}

.title {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  color: var(--brand-primary);
  margin-bottom: var(--space-sm);
}

.subtitle {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
</style>
