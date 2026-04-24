<template>
  <view class="container treehole-force-dark">
    <text class="placeholder">树洞吐槽区</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 树洞页
 * 文件：src/pages/treehole/index.vue
 * 说明：树洞区始终使用夜间模式
 */
import { onShow } from '@dcloudio/uni-app'
import { trackPageEnter } from '@/utils/tracking'

onShow(() => {
  trackPageEnter('treehole')
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
