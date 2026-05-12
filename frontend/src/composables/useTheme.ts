/**
 * 回声 - 主题切换组合式函数
 * 文件：src/composables/useTheme.ts
 * 说明：主题切换逻辑，支持跟随系统/定时/手动三种切换方式
 * 设计风格：纯净白 · 暖橘
 */

import { ref, watch, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import type { ThemeMode } from '@/stores/settings'

export function useTheme() {
  const settingsStore = useSettingsStore()
  const isDark = ref(settingsStore.isDarkMode)

  /**
   * 应用主题到页面
   * 纯净白 · 暖橘设计系统：
   * - 暗色模式: #12111a（暖调深色）
   * - 日间模式: #FFF9F5（微暖白）
   */
  function applyTheme(dark: boolean) {
    try {
      const pageStyle = dark
        ? { backgroundColor: '#12111a' }
        : { backgroundColor: '#FFF9F5' }

      // #ifdef APP-PLUS || MP-WEIXIN
      uni.setPageStyle({
        style: pageStyle,
      })
      // #endif
      // #ifdef H5
      // H5 平台直接操作 DOM
      document.body.style.backgroundColor = dark ? '#12111a' : '#FFF9F5'
      // #endif
    } catch (e) {
      console.error('设置页面样式失败', e)
    }
  }

  function toggleTheme() {
    const themes: ThemeMode[] = ['light', 'dark', 'system', 'auto']
    const currentIndex = themes.indexOf(settingsStore.theme)
    const nextIndex = (currentIndex + 1) % themes.length
    settingsStore.setTheme(themes[nextIndex])
  }

  function setDark() {
    settingsStore.setTheme('dark')
  }

  function setLight() {
    settingsStore.setTheme('light')
  }

  function setSystem() {
    settingsStore.setTheme('system')
  }

  function setAuto() {
    settingsStore.setTheme('auto')
  }

  watch(
    () => settingsStore.isDarkMode,
    (dark) => {
      isDark.value = dark
      applyTheme(dark)
    }
  )

  onMounted(() => {
    applyTheme(isDark.value)
  })

  return {
    isDark,
    toggleTheme,
    setDark,
    setLight,
    setSystem,
    setAuto,
    applyTheme,
  }
}
