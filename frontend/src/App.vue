<script setup lang="ts">
/**
 * 回声 - 应用入口
 * 文件：src/App.vue
 * 说明：应用生命周期管理、全局样式引入、主题初始化
 */
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import { initTracking, trackAppShow, trackAppHide } from '@/utils/tracking'

// 应用启动
onLaunch(() => {
  console.log('回声 App Launch')

  // 初始化用户状态
  const userStore = useUserStore()
  userStore.init()

  // 初始化设置
  const settingsStore = useSettingsStore()
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
  // 定时切换主题（如果配置了定时切换）
  const settingsStore = useSettingsStore()
  settingsStore.checkTeenModeExpiry()
  settingsStore.applyTheme()
})

// 应用隐藏（进入后台）
onHide(() => {
  console.log('回声 App Hide')
  trackAppHide()
})
</script>

<style lang="scss">
/* 引入全局样式 - 使用 @import 确保 Uni-app 兼容 */
@import '@/styles/variables.scss';
@import '@/styles/theme.scss';
@import '@/styles/emotions.scss';
@import '@/styles/dark.scss';
@import '@/styles/animations.scss';
@import '@/styles/common.scss';
</style>
