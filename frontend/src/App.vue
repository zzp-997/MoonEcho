<script setup lang="ts">
/**
 * 回声 - 应用入口
 * 文件：src/App.vue
 * 说明：应用生命周期管理、全局样式引入、主题初始化、全局路由守卫
 * 功能增强（T016）：全局路由守卫初始化
 */
import { computed } from 'vue'
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import { initTracking, trackAppShow, trackAppHide } from '@/utils/tracking'
import { useAuth, globalAuthGuard } from '@/composables/useAuth'

// 初始化 store 引用（避免重复创建）
const userStore = useUserStore()
const settingsStore = useSettingsStore()
const { initAuth, incrementAppOpenCount } = useAuth()

// 是否为暗色模式（用于 wd-config-provider）
const isDark = computed(() => settingsStore.isDarkMode)

// 应用启动
onLaunch(() => {
  console.log('回声 App Launch')

  // 初始化认证状态（包含路由守卫初始化）
  initAuth()

  // 初始化用户状态
  userStore.init()

  // 初始化设置
  settingsStore.applyTheme()

  // 检查青少年模式过期
  settingsStore.checkTeenModeExpiry()

  // 初始化埋点系统
  initTracking()
})

// 应用显示（从后台恢复）
onShow(() => {
  console.log('回声 App Show')
  trackAppShow()

  // 全局路由守卫检查
  globalAuthGuard()

  // 增加 APP 打开次数
  incrementAppOpenCount()

  // 恢复时重新应用主题（支持定时切换）
  settingsStore.applyTheme()
})

// 应用隐藏（进入后台）
onHide(() => {
  console.log('回声 App Hide')
  trackAppHide()
})
</script>

<template>
  <wd-config-provider :theme="isDark ? 'dark' : 'light'">
    <view class="app-container">
      <slot />
    </view>
  </wd-config-provider>
</template>

<style lang="scss">
/* 引入全局样式 - 使用 @import 确保 Uni-app 兼容 */
@import '@/styles/variables.scss';
@import '@/styles/theme.scss';
@import '@/styles/emotions.scss';
@import '@/styles/dark.scss';
@import '@/styles/animations.scss';
@import '@/styles/common.scss';

.app-container {
  width: 100%;
  min-height: 100vh;
}
</style>
