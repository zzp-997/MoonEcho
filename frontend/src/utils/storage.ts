/**
 * 回声 - 本地存储封装
 * 文件：src/utils/storage.ts
 * 说明：统一的本地存储接口，支持键值存储和结构化数据
 */

/** 存储键名常量 */
export const StorageKeys = {
  /** 用户Token */
  TOKEN: 'huisheng_token',
  /** 刷新Token */
  REFRESH_TOKEN: 'huisheng_refresh_token',
  /** 用户信息 */
  USER_INFO: 'huisheng_user_info',
  /** 应用设置 */
  SETTINGS: 'huisheng_settings',
  /** 日记数据 */
  DIARIES: 'huisheng_diaries',
  /** 埋点事件队列 */
  EVENT_QUEUE: 'huisheng_event_queue',
  /** 最后活跃日期 */
  LAST_ACTIVE_DATE: 'huisheng_last_active_date',
  /** 主题偏好 */
  THEME_PREFERENCE: 'huisheng_theme_preference',
} as const

/**
 * 存储数据
 */
export function setStorage<T = any>(key: string, value: T): void {
  try {
    const data = typeof value === 'object' ? JSON.stringify(value) : String(value)
    uni.setStorageSync(key, data)
  } catch (e) {
    console.error(`存储数据失败 [${key}]`, e)
  }
}

/**
 * 读取数据
 */
export function getStorage<T = any>(key: string, defaultValue?: T): T | undefined {
  try {
    const data = uni.getStorageSync(key)
    if (!data) return defaultValue

    try {
      return JSON.parse(data) as T
    } catch {
      return data as T
    }
  } catch (e) {
    console.error(`读取数据失败 [${key}]`, e)
    return defaultValue
  }
}

/**
 * 删除数据
 */
export function removeStorage(key: string): void {
  try {
    uni.removeStorageSync(key)
  } catch (e) {
    console.error(`删除数据失败 [${key}]`, e)
  }
}

/**
 * 清除所有数据
 */
export function clearStorage(): void {
  try {
    uni.clearStorageSync()
  } catch (e) {
    console.error('清除存储失败', e)
  }
}
