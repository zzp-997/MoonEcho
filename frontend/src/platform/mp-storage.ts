/**
 * 回声 - 小程序存储适配
 * 文件：src/platform/mp-storage.ts
 * 说明：统一存储接口，App 端使用 SQLite，小程序使用 uni.setStorageSync
 * 作者：Frontend Developer
 */

// ==================== 类型定义 ====================

/** 存储适配器接口 */
export interface StorageAdapter {
  /** 初始化存储 */
  init(): Promise<void>
  /** 保存数据 */
  set<T>(key: string, value: T): Promise<void>
  /** 获取数据 */
  get<T>(key: string, defaultValue?: T): Promise<T | undefined>
  /** 删除数据 */
  remove(key: string): Promise<void>
  /** 清除所有数据 */
  clear(): Promise<void>
  /** 获取所有键 */
  keys(): Promise<string[]>
  /** 获取存储大小（字节） */
  getSize(): Promise<number>
}

/** 结构化存存储接口（用于日记等需要查询的数据） */
export interface StructuredStorageAdapter extends StorageAdapter {
  /** 开始事务 */
  beginTransaction(): Promise<void>
  /** 提交事务 */
  commit(): Promise<void>
  /** 回滚事务 */
  rollback(): Promise<void>
  /** 执行查询 */
  query<T>(sql: string, params?: any[]): Promise<T[]>
  /** 执行更新 */
  execute(sql: string, params?: any[]): Promise<void>
}

/** 日记数据接口 */
export interface DiaryStorageItem {
  id: string
  content: string
  emotion: string
  intensity: number
  date: string
  createdAt: string
  updatedAt: string
  synced: boolean
  aiComment?: string
}

/** 存储配置 */
export interface StorageConfig {
  /** 存储前缀 */
  prefix: string
  /** 最大存储大小（字节），仅小程序有效 */
  maxSize?: number
}

// ==================== 默认配置 ====================

const DEFAULT_CONFIG: StorageConfig = {
  prefix: 'huisheng_',
  maxSize: 10 * 1024 * 1024, // 10MB
}

// ==================== 小程序存储适配器 ====================

/**
 * 小程序键值存储适配器
 * 使用 uni.setStorageSync 实现
 */
export class MiniProgramStorageAdapter implements StorageAdapter {
  private prefix: string
  private initialized = false

  constructor(config: StorageConfig = DEFAULT_CONFIG) {
    this.prefix = config.prefix
  }

  /**
   * 初始化存储
   */
  async init(): Promise<void> {
    if (this.initialized) return
    this.initialized = true
    console.log('[MiniProgramStorage] 存储初始化完成')
  }

  /**
   * 生成完整键名
   */
  private getFullKey(key: string): string {
    return `${this.prefix}${key}`
  }

  /**
   * 保存数据
   */
  async set<T>(key: string, value: T): Promise<void> {
    try {
      const fullKey = this.getFullKey(key)
      const data = typeof value === 'object' ? JSON.stringify(value) : String(value)
      uni.setStorageSync(fullKey, data)
    } catch (e) {
      console.error(`[MiniProgramStorage] 保存数据失败 [${key}]`, e)
      throw e
    }
  }

  /**
   * 获取数据
   */
  async get<T>(key: string, defaultValue?: T): Promise<T | undefined> {
    try {
      const fullKey = this.getFullKey(key)
      const data = uni.getStorageSync(fullKey)
      if (!data) return defaultValue

      try {
        return JSON.parse(data) as T
      } catch {
        return data as T
      }
    } catch (e) {
      console.error(`[MiniProgramStorage] 获取数据失败 [${key}]`, e)
      return defaultValue
    }
  }

  /**
   * 删除数据
   */
  async remove(key: string): Promise<void> {
    try {
      const fullKey = this.getFullKey(key)
      uni.removeStorageSync(fullKey)
    } catch (e) {
      console.error(`[MiniProgramStorage] 删除数据失败 [${key}]`, e)
      throw e
    }
  }

  /**
   * 清除所有数据（仅清除带前缀的）
   */
  async clear(): Promise<void> {
    try {
      // 使用管理接口清除所有数据
      // #ifdef MP-WEIXIN
      const res = uni.getStorageInfoSync()
      for (const key of res.keys) {
        if (key.startsWith(this.prefix)) {
          uni.removeStorageSync(key)
        }
      }
      // #endif

      // #ifndef MP-WEIXIN
      // 其他平台保守清理已知的键
      uni.clearStorageSync()
      // #endif
    } catch (e) {
      console.error('[MiniProgramStorage] 清除存储失败', e)
      throw e
    }
  }

  /**
   * 获取所有键
   */
  async keys(): Promise<string[]> {
    try {
      // #ifdef MP-WEIXIN
      const res = uni.getStorageInfoSync()
      return res.keys
        .filter((key: string) => key.startsWith(this.prefix))
        .map((key: string) => key.slice(this.prefix.length))
      // #endif

      // #ifndef MP-WEIXIN
      const res = uni.getStorageInfoSync()
      return (res as any).keys || []
      // #endif
    } catch (e) {
      console.error('[MiniProgramStorage] 获取键列表失败', e)
      return []
    }
  }

  /**
   * 获取存储大小
   */
  async getSize(): Promise<number> {
    try {
      const res = uni.getStorageInfoSync()
      return (res as any).currentSize || 0
    } catch {
      return 0
    }
  }
}

// ==================== 日记存储适配器 ====================

/**
 * 小程序日记存储适配器
 * 实现简单的增删改查，无结构化查询能力
 */
export class MiniProgramDiaryAdapter extends MiniProgramStorageAdapter {
  private diaryKey = 'diaries'

  constructor(config: StorageConfig = DEFAULT_CONFIG) {
    super(config)
  }

  /**
   * 获取所有日记
   */
  async getAllDiaries(): Promise<DiaryStorageItem[]> {
    const diaries = await this.get<DiaryStorageItem[]>(this.diaryKey, [])
    return diaries || []
  }

  /**
   * 保存所有日记
   */
  private async saveAllDiaries(diaries: DiaryStorageItem[]): Promise<void> {
    await this.set(this.diaryKey, diaries)
  }

  /**
   * 添加日记
   */
  async addDiary(diary: DiaryStorageItem): Promise<void> {
    const diaries = await this.getAllDiaries()
    diaries.unshift(diary)
    await this.saveAllDiaries(diaries)
  }

  /**
   * 更新日记
   */
  async updateDiary(id: string, updates: Partial<DiaryStorageItem>): Promise<void> {
    const diaries = await this.getAllDiaries()
    const index = diaries.findIndex((d) => d.id === id)
    if (index !== -1) {
      diaries[index] = { ...diaries[index], ...updates }
      await this.saveAllDiaries(diaries)
    }
  }

  /**
   * 删除日记
   */
  async deleteDiary(id: string): Promise<void> {
    const diaries = await this.getAllDiaries()
    const filtered = diaries.filter((d) => d.id !== id)
    await this.saveAllDiaries(filtered)
  }

  /**
   * 根据日期获取日记
   */
  async getDiaryByDate(date: string): Promise<DiaryStorageItem | undefined> {
    const diaries = await this.getAllDiaries()
    return diaries.find((d) => d.date === date)
  }

  /**
   * 根据日期范围获取日记
   */
  async getDiariesByDateRange(startDate: string, endDate: string): Promise<DiaryStorageItem[]> {
    const diaries = await this.getAllDiaries()
    return diaries.filter((d) => d.date >= startDate && d.date <= endDate)
  }

  /**
   * 获取未同步的日记
   */
  async getUnsyncedDiaries(): Promise<DiaryStorageItem[]> {
    const diaries = await this.getAllDiaries()
    return diaries.filter((d) => !d.synced)
  }

  /**
   * 标记日记为已同步
   */
  async markDiarySynced(id: string): Promise<void> {
    await this.updateDiary(id, { synced: true })
  }
}

// ==================== 统一存储接口 ====================

/** 存储类型枚举 */
export enum StorageType {
  /** 用户Token */
  TOKEN = 'token',
  /** 刷新Token */
  REFRESH_TOKEN = 'refresh_token',
  /** 用户信息 */
  USER_INFO = 'user_info',
  /** 应用设置 */
  SETTINGS = 'settings',
  /** 日记数据 */
  DIARIES = 'diaries',
  /** 埋点事件队列 */
  EVENT_QUEUE = 'event_queue',
  /** 最后活跃日期 */
  LAST_ACTIVE_DATE = 'last_active_date',
  /** 主题偏好 */
  THEME_PREFERENCE = 'theme_preference',
  /** 搜索历史 */
  SEARCH_HISTORY = 'search_history',
  /** 缓存数据 */
  CACHE = 'cache',
}

/**
 * 创建平台适配的存储实例
 */
export function createStorageAdapter(config?: StorageConfig): StorageAdapter {
  // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
  return new MiniProgramStorageAdapter(config)
  // #endif

  // #ifdef APP-PLUS
  // App 端可以扩展为 SQLite 适配器
  // return new SQLiteStorageAdapter(config)
  return new MiniProgramStorageAdapter(config) // 暂时降级使用键值存储
  // #endif

  // #ifdef H5
  return new MiniProgramStorageAdapter(config)
  // #endif
}

/**
 * 创建日记存储实例
 */
export function createDiaryStorageAdapter(config?: StorageConfig): MiniProgramDiaryAdapter {
  return new MiniProgramDiaryAdapter(config)
}

// ==================== 便捷方法 ====================

// 默认存储实例
let defaultStorage: StorageAdapter | null = null
let defaultDiaryStorage: MiniProgramDiaryAdapter | null = null

/**
 * 获取默认存储实例
 */
export async function getStorage(): Promise<StorageAdapter> {
  if (!defaultStorage) {
    defaultStorage = createStorageAdapter()
    await defaultStorage.init()
  }
  return defaultStorage
}

/**
 * 获取日记存储实例
 */
export async function getDiaryStorage(): Promise<MiniProgramDiaryAdapter> {
  if (!defaultDiaryStorage) {
    defaultDiaryStorage = createDiaryStorageAdapter()
    await defaultDiaryStorage.init()
  }
  return defaultDiaryStorage
}

/**
 * 快捷保存数据
 */
export async function saveData<T>(key: StorageType | string, value: T): Promise<void> {
  const storage = await getStorage()
  await storage.set(key, value)
}

/**
 * 快捷读取数据
 */
export async function loadData<T>(key: StorageType | string, defaultValue?: T): Promise<T | undefined> {
  const storage = await getStorage()
  return storage.get(key, defaultValue)
}

/**
 * 快捷删除数据
 */
export async function removeData(key: StorageType | string): Promise<void> {
  const storage = await getStorage()
  await storage.remove(key)
}

// ==================== 导出 ====================

export default {
  createStorageAdapter,
  createDiaryStorageAdapter,
  getStorage,
  getDiaryStorage,
  saveData,
  loadData,
  removeData,
  StorageType,
  MiniProgramStorageAdapter,
  MiniProgramDiaryAdapter,
}
