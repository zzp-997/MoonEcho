/**
 * 回声 - 小程序平台适配模块
 * 文件：src/platform/miniprogram/index.ts
 * 说明：统一导出小程序平台适配相关功能
 * 作者：Frontend Developer
 */

// ==================== 推送降级 ====================

export {
  // 类型
  type PushMessage,
  type PushConfig,
  type PushPermissionStatus,
  type SubscribeResult,
  type SubscribeTemplate,
  PushMessageType,
  // 类
  MiniProgramPushAdapter,
  AppPushAdapter,
  // 工厂函数
  createPushAdapter,
  getPush,
  quickSubscribe,
  isPushSupported,
} from './push'

// ==================== 审核要点适配 ====================

export {
  // 类型
  type PrivacyStatus,
  type PrivacyConfig,
  type PermissionItem,
  type ContentSecurityResult,
  type ShareCheckResult,
  type MinorModeStatus,
  // 类
  PrivacyManager,
  ContentSecurityChecker,
  ShareComplianceChecker,
  MinorModeManager,
  // 工厂函数
  getPrivacyManager,
  getContentSecurityChecker,
  getShareComplianceChecker,
  getMinorModeManager,
  checkContentSecurity,
  checkShareContent,
} from './privacy'

// ==================== 平台检测工具 ====================

/**
 * 检测是否为微信小程序环境
 */
export function isWeixinMiniProgram(): boolean {
  // #ifdef MP-WEIXIN
  return true
  // #endif

  // #ifndef MP-WEIXIN
  return false
  // #endif
}

/**
 * 检测是否为小程序环境
 */
export function isMiniProgram(): boolean {
  // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
  return true
  // #endif

  // #ifndef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
  return false
  // #endif
}

/**
 * 获取当前运行平台
 */
export function getCurrentPlatform(): 'h5' | 'app' | 'mp-weixin' | 'mp-alipay' | 'mp-other' {
  // #ifdef H5
  return 'h5'
  // #endif

  // #ifdef APP-PLUS
  return 'app'
  // #endif

  // #ifdef MP-WEIXIN
  return 'mp-weixin'
  // #endif

  // #ifdef MP-ALIPAY
  return 'mp-alipay'
  // #endif

  // #ifdef MP-BAIDU || MP-TOUTIAO || MP-QQ
  return 'mp-other'
  // #endif

  return 'h5'
}

/**
 * 获取小程序系统信息
 */
export function getMPSystemInfo(): UniApp.GetSystemInfoSyncRes | null {
  try {
    // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
    return uni.getSystemInfoSync()
    // #endif

    // #ifndef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
    return null
    // #endif
  } catch {
    return null
  }
}

/**
 * 获取小程序菜单按钮信息（用于自定义导航栏）
 */
export function getMenuButtonInfo(): { top: number; height: number; right: number } | null {
  // #ifdef MP-WEIXIN
  try {
    const menuButton = wx.getMenuButtonBoundingClientRect()
    return {
      top: menuButton.top,
      height: menuButton.height,
      right: menuButton.right,
    }
  } catch {
    return null
  }
  // #endif

  // #ifndef MP-WEIXIN
  return null
  // #endif
}

/**
 * 检查小程序版本更新
 */
export function checkUpdate(): void {
  // #ifdef MP-WEIXIN
  if (wx.canIUse('getUpdateManager')) {
    const updateManager = wx.getUpdateManager()

    updateManager.onCheckForUpdate((res) => {
      console.log('[MP] 检查更新:', res.hasUpdate ? '有新版本' : '已是最新')
    })

    updateManager.onUpdateReady(() => {
      wx.showModal({
        title: '更新提示',
        content: '新版本已经准备好，是否重启应用？',
        success: (res) => {
          if (res.confirm) {
            updateManager.applyUpdate()
          }
        },
      })
    })

    updateManager.onUpdateFailed(() => {
      console.warn('[MP] 新版本下载失败')
    })
  }
  // #endif
}

/**
 * 小程序性能监控
 */
export function reportPerformance(metric: string, value: number): void {
  // #ifdef MP-WEIXIN
  try {
    wx.reportPerformance?.(1000, value, metric)
  } catch {
    // 忽略错误
  }
  // #endif
}

// ==================== 默认导出 ====================

export default {
  isWeixinMiniProgram,
  isMiniProgram,
  getCurrentPlatform,
  getMPSystemInfo,
  getMenuButtonInfo,
  checkUpdate,
  reportPerformance,
}
