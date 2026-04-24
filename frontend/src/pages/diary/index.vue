<template>
  <view class="container">
    <text class="placeholder">情绪日记</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 情绪日记页
 * 文件：src/pages/diary/index.vue
 */
import { onShow } from '@dcloudio/uni-app'
import { trackPageEnter } from '@/utils/tracking'

onShow(() => {
  trackPageEnter('diary')
})
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

.placeholder {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
}
</style>
