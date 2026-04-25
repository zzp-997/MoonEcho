<template>
  <view class="container">
    <text class="placeholder">快捷入口</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 快捷入口页（[+] 按钮分流）
 * 文件：src/pages/add/index.vue
 * 说明：中间 [+] 按钮的分流页面，提供快速创建对话/日记/树洞等入口
 *       阶段一仅作占位，阶段二实现完整功能
 */
import { onShow } from '@dcloudio/uni-app'
import { trackPageEnter } from '@/utils/tracking'

onShow(() => {
  trackPageEnter('add')
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
