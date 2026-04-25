/**
 * 回声 - 主题切换组合式函数
 * 文件：src/composables/useTheme.ts
 * 说明：主题切换逻辑，支持跟随系统/定时/手动三种切换方式
 */

import { ref, watch, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import type { ThemeMode } from '@/stores/settings'

export function useTheme() {
  const settingsStore = useSettingsStore()
  const isDark = ref(settingsStore.isDarkMode)

  /**
   * 应用主题到页面
   * 注意：uni.setPageStyle 在部分平台不支持 CSS 变量
   * 此处使用实际颜色值，颜色来源与 variables.scss 中的 CSS 变量定义一致：
   * --bg-primary: 暗色 #121212, 亮色 #F5F5F7
   */
  function applyTheme(dark: boolean) {
    // 设置页面背景色（颜色值与 variables.scss --bg-primary 对应）
    try {
      const pageStyle = dark
        ? { backgroundColor: '#121212' }
        : { backgroundColor: '#F5F5F7' }

      uni.setPageStyle({
        style: pageStyle,
      })
    } catch (e) {
      console.error('设置页面样式失败', e)
    }
  }

  /**
   * 切换主题
   */
  function toggleTheme() {
    const themes: ThemeMode[] = ['light', 'dark', 'system']
    const currentIndex = themes.indexOf(settingsStore.theme)
    const nextIndex = (currentIndex + 1) % themes.length
    settingsStore.setTheme(themes[nextIndex])
  }

  /**
   * 设置为暗色模式
   */
  function setDark() {
    settingsStore.setTheme('dark')
  }

  /**
   * 设置为亮色模式
   */
  function setLight() {
    settingsStore.setTheme('light')
  }

  /**
   * 设置跟随系统
   */
  function setSystem() {
    settingsStore.setTheme('system')
  }

  // 监听主题变化
  watch(
    () => settingsStore.isDarkMode,
    (dark) => {
      isDark.value = dark
      applyTheme(dark)
    }
  )

  // 初始化时应用主题
  onMounted(() => {
    applyTheme(isDark.value)
  })

  return {
    isDark,
    toggleTheme,
    setDark,
    setLight,
    setSystem,
    applyTheme,
  }
}
