/**
 * 回声 - 设置状态管理
 * 文件：src/stores/settings.ts
 * 说明：主题设置、设备标识、青少年模式等应用设置
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 主题模式 */
export type ThemeMode = 'light' | 'dark' | 'system'

/** 设置存储键 */
const SETTINGS_KEY = 'huisheng_settings'

/** 设置接口 */
export interface Settings {
  theme: ThemeMode
  deviceId: string
  appVersion: string
  teenMode: boolean
  teenModeEndTime?: string
  notificationsEnabled: boolean
  language: string
}

/** 默认设置 */
const DEFAULT_SETTINGS: Settings = {
  theme: 'dark', // 默认夜间模式
  deviceId: '',
  appVersion: '1.0.0',
  teenMode: false,
  notificationsEnabled: true,
  language: 'zh_CN',
}

export const useSettingsStore = defineStore('settings', () => {
  // ==================== 状态 ====================

  const settings = ref<Settings>({ ...DEFAULT_SETTINGS })

  // ==================== 计算属性 ====================

  /** 当前主题 */
  const theme = computed(() => settings.value.theme)

  /** 是否为青少年模式 */
  const isTeenMode = computed(() => settings.value.teenMode)

  /** 设备ID */
  const deviceId = computed(() => settings.value.deviceId)

  /** 应用版本 */
  const appVersion = computed(() => settings.value.appVersion)

  /** 是否为暗色模式 */
  const isDarkMode = computed(() => {
    if (settings.value.theme === 'system') {
      // 获取系统主题
      const systemInfo = uni.getSystemInfoSync()
      // @ts-ignore
      return systemInfo.osTheme === 'dark'
    }
    return settings.value.theme === 'dark'
  })

  // ==================== 方法 ====================

  /**
   * 初始化设置
   */
  function init() {
    try {
      const savedSettings = uni.getStorageSync(SETTINGS_KEY)
      if (savedSettings) {
        settings.value = { ...DEFAULT_SETTINGS, ...JSON.parse(savedSettings) }
      }

      // 生成设备ID
      if (!settings.value.deviceId) {
        settings.value.deviceId = generateDeviceId()
        saveSettings()
      }
    } catch (e) {
      console.error('初始化设置失败', e)
    }
  }

  /**
   * 保存设置到本地
   */
  function saveSettings() {
    uni.setStorageSync(SETTINGS_KEY, JSON.stringify(settings.value))
  }

  /**
   * 设置主题
   */
  function setTheme(newTheme: ThemeMode) {
    settings.value.theme = newTheme
    saveSettings()
    applyTheme()
  }

  /**
   * 应用主题
   */
  function applyTheme() {
    const dark = isDarkMode.value
    // 通过 CSS 变量切换主题
    // 在实际应用中，需要在页面根元素添加/移除 class
    if (dark) {
      // 移除 light class，添加 dark class
      // 具体实现在 useTheme composable 中
    } else {
      // 移除 dark class，添加 light class
    }
  }

  /**
   * 切换主题
   */
  function toggleTheme() {
    const themes: ThemeMode[] = ['light', 'dark', 'system']
    const currentIndex = themes.indexOf(settings.value.theme)
    const nextIndex = (currentIndex + 1) % themes.length
    setTheme(themes[nextIndex])
  }

  /**
   * 开启青少年模式
   */
  function enableTeenMode(duration: number = 0) {
    settings.value.teenMode = true
    if (duration > 0) {
      const endTime = new Date(Date.now() + duration * 60 * 60 * 1000)
      settings.value.teenModeEndTime = endTime.toISOString()
    }
    saveSettings()
  }

  /**
   * 关闭青少年模式
   */
  function disableTeenMode() {
    settings.value.teenMode = false
    settings.value.teenModeEndTime = undefined
    saveSettings()
  }

  /**
   * 检查青少年模式是否应该自动关闭
   */
  function checkTeenModeExpiry() {
    if (settings.value.teenMode && settings.value.teenModeEndTime) {
      const endTime = new Date(settings.value.teenModeEndTime)
      if (new Date() >= endTime) {
        disableTeenMode()
        return true
      }
    }
    return false
  }

  /**
   * 设置通知开关
   */
  function setNotificationsEnabled(enabled: boolean) {
    settings.value.notificationsEnabled = enabled
    saveSettings()
  }

  /**
   * 生成设备ID
   */
  function generateDeviceId(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < 32; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return `HS_${Date.now()}_${result}`
  }

  // ==================== 初始化 ====================

  init()

  return {
    // 状态
    settings,
    // 计算属性
    theme,
    isDarkMode,
    isTeenMode,
    deviceId,
    appVersion,
    // 方法
    setTheme,
    toggleTheme,
    applyTheme,
    enableTeenMode,
    disableTeenMode,
    checkTeenModeExpiry,
    setNotificationsEnabled,
  }
})
