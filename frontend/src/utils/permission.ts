/**
 * 回声 - 权限处理工具
 * 文件：src/utils/permission.ts
 * 说明：青少年模式权限拦截、页面访问权限控制
 */

import { useSettingsStore } from '@/stores/settings'
import { useUserStore } from '@/stores/user'

/** 青少年模式受限页面列表 */
const TEEN_RESTRICTED_PAGES = [
  '/pages/treehole/index',
  '/pages/square/index',
  '/pages/message/index',
]

/** 需要登录才能访问的页面列表 */
const AUTH_REQUIRED_PAGES = [
  '/pages/chat/index',
  '/pages/diary/index',
  '/pages/diary/edit',
  '/pages/mine/index',
  '/pages/message/index',
]

/**
 * 检查页面访问权限
 * @param url 目标页面路径
 * @returns 是否允许访问
 */
export function checkPagePermission(url: string): boolean {
  const settingsStore = useSettingsStore()
  const userStore = useUserStore()

  // 青少年模式检查
  if (settingsStore.isTeenMode) {
    if (TEEN_RESTRICTED_PAGES.some((page) => url.includes(page))) {
      uni.showModal({
        title: '提示',
        content: '青少年模式下无法使用此功能',
        showCancel: false,
        confirmText: '我知道了',
      })
      return false
    }
  }

  // 登录状态检查
  if (AUTH_REQUIRED_PAGES.some((page) => url.includes(page))) {
    if (!userStore.isLoggedIn) {
      uni.navigateTo({ url: '/pages/auth/login' })
      return false
    }
  }

  return true
}

/**
 * 导航到页面（带权限检查）
 */
export function navigateTo(url: string): void {
  if (checkPagePermission(url)) {
    uni.navigateTo({ url })
  }
}

/**
 * 切换到Tab页面
 */
export function switchTab(url: string): void {
  if (checkPagePermission(url)) {
    uni.switchTab({ url })
  }
}
