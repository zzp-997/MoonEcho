<template>
  <view class="container">
    <text class="placeholder">动态广场</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 动态广场页
 * 文件：src/pages/square/index.vue
 */
import { onShow } from '@dcloudio/uni-app'
import { trackPageEnter } from '@/utils/tracking'

onShow(() => {
  trackPageEnter('square')
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
