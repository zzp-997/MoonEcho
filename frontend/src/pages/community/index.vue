<template>
  <view class="container">
    <text class="placeholder">动态</text>
    <text class="hint">阶段二功能：树洞 & 广场</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 动态页（社区）
 * 文件：src/pages/community/index.vue
 * 说明：社区动态入口，阶段二整合树洞和广场功能
 *       阶段一仅作占位页面
 */
import { onShow } from '@dcloudio/uni-app'
import { trackPageEnter } from '@/utils/tracking'

onShow(() => {
  trackPageEnter('community')
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
}

.placeholder {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
  margin-bottom: var(--space-xs);
}

.hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}
</style>
