<template>
  <view class="container">
    <text class="placeholder">我的</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 个人中心页
 * 文件：src/pages/mine/index.vue
 */
import { onShow } from '@dcloudio/uni-app'
import { trackPageEnter } from '@/utils/tracking'

onShow(() => {
  trackPageEnter('mine')
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
