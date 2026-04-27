/**
 * 回声 - 平台适配模块
 * 文件：src/platform/index.ts
 * 说明：统一导出平台适配相关功能
 * 作者：Frontend Developer
 */

// ==================== 小程序平台适配 ====================

export * from './miniprogram'

// ==================== 存储适配 ====================

export {
  // 类型
  type StorageAdapter,
  type StructuredStorageAdapter,
  type DiaryStorageItem,
  type StorageConfig,
  StorageType,
  // 类
  MiniProgramStorageAdapter,
  MiniProgramDiaryAdapter,
  // 工厂函数
  createStorageAdapter,
  createDiaryStorageAdapter,
  getStorage,
  getDiaryStorage,
  saveData,
  loadData,
  removeData,
} from './mp-storage'

// ==================== 平台能力检测 ====================

/**
 * 检测当前平台是否支持某项能力
 * @param capability 能力名称
 * @returns 是否支持
 */
export function checkCapability(
  capability: 'sse' | 'sqlite' | 'push' | 'camera' | 'location' | 'bluetooth'
): boolean {
  switch (capability) {
    case 'sse':
      // App 和 H5 支持 SSE，小程序需要降级
      // #ifdef APP-PLUS || H5
      return true
      // #endif
      // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
      return false
      // #endif
      return false

    case 'sqlite':
      // 只有 App 端支持 SQLite
      // #ifdef APP-PLUS
      return true
      // #endif
      return false

    case 'push':
      // App 和微信小程序支持推送
      // #ifdef APP-PLUS || MP-WEIXIN
      return true
      // #endif
      return false

    case 'camera':
      // 所有平台都支持相机
      return true

    case 'location':
      // 所有平台都支持定位
      return true

    case 'bluetooth':
      // App 和部分小程序支持蓝牙
      // #ifdef APP-PLUS || MP-WEIXIN
      return true
      // #endif
      return false

    default:
      return false
  }
}

/**
 * 获取平台限制信息
 */
export function getPlatformLimits(): {
  /** 主包大小限制（MB） */
  mainPackageSize: number
  /** 总包大小限制（MB） */
  totalPackageSize: number
  /** 本地存储限制（MB） */
  localStorageSize: number
  /** 是否支持分包 */
  supportsSubPackages: boolean
} {
  // #ifdef MP-WEIXIN
  return {
    mainPackageSize: 2, // 微信小程序主包 2MB
    totalPackageSize: 20, // 总包 20MB
    localStorageSize: 10, // 本地存储 10MB
    supportsSubPackages: true,
  }
  // #endif

  // #ifdef APP-PLUS
  return {
    mainPackageSize: Infinity,
    totalPackageSize: Infinity,
    localStorageSize: Infinity,
    supportsSubPackages: false,
  }
  // #endif

  // #ifdef H5
  return {
    mainPackageSize: Infinity,
    totalPackageSize: Infinity,
    localStorageSize: 5, // LocalStorage 通常 5MB
    supportsSubPackages: false,
  }
  // #endif

  // 默认值
  return {
    mainPackageSize: 2,
    totalPackageSize: 20,
    localStorageSize: 10,
    supportsSubPackages: true,
  }
}

/**
 * 获取平台特性描述
 */
export function getPlatformFeatures(): {
  /** 平台名称 */
  name: string
  /** 是否支持 SSE 流式输出 */
  supportsSSE: boolean
  /** 是否支持原生推送 */
  supportsNativePush: boolean
  /** 是否支持结构化存储 */
  supportsStructuredStorage: boolean
  /** 需要审核 */
  requiresReview: boolean
  /** 需要隐私协议 */
  requiresPrivacyAgreement: boolean
} {
  // #ifdef MP-WEIXIN
  return {
    name: '微信小程序',
    supportsSSE: false,
    supportsNativePush: true,
    supportsStructuredStorage: false,
    requiresReview: true,
    requiresPrivacyAgreement: true,
  }
  // #endif

  // #ifdef MP-ALIPAY
  return {
    name: '支付宝小程序',
    supportsSSE: false,
    supportsNativePush: false,
    supportsStructuredStorage: false,
    requiresReview: true,
    requiresPrivacyAgreement: true,
  }
  // #endif

  // #ifdef APP-PLUS
  return {
    name: 'App',
    supportsSSE: true,
    supportsNativePush: true,
    supportsStructuredStorage: true,
    requiresReview: false,
    requiresPrivacyAgreement: true,
  }
  // #endif

  // #ifdef H5
  return {
    name: 'H5',
    supportsSSE: true,
    supportsNativePush: false,
    supportsStructuredStorage: false,
    requiresReview: false,
    requiresPrivacyAgreement: true,
  }
  // #endif

  // 默认值
  return {
    name: '未知平台',
    supportsSSE: false,
    supportsNativePush: false,
    supportsStructuredStorage: false,
    requiresReview: false,
    requiresPrivacyAgreement: false,
  }
}

// ==================== 默认导出 ====================

export default {
  checkCapability,
  getPlatformLimits,
  getPlatformFeatures,
}
