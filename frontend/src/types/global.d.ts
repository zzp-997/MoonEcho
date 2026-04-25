/**
 * 回声 - 全局类型定义
 * 文件：src/types/global.d.ts
 * 说明：全局 TypeScript 类型声明
 */

/// <reference types="vite/client" />

/** Vite 环境变量类型声明 */
interface ImportMetaEnv {
  /** API 基础地址 */
  readonly VITE_API_BASE_URL?: string
  /** 埋点上报地址 */
  readonly VITE_TRACKING_URL?: string
  /** 调试模式开关 */
  readonly VITE_DEBUG?: string
  /** 应用版本号 */
  readonly VITE_APP_VERSION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/** 通用分页参数 */
export interface PageParams {
  page?: number
  pageSize?: number
}

/** 通用分页响应 */
export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

/** 情绪类型 */
export type EmotionType = 'warm' | 'calm' | 'low' | 'sad' | 'chaos'

/** AI 性格类型 */
export type AIPersonality = 'xiaowen' | 'laohei' | 'ali'

/** 主题模式 */
export type ThemeMode = 'light' | 'dark' | 'system'

/** 性别 */
export type Gender = 'male' | 'female' | 'other' | 'unknown'

/** 年龄段 */
export type AgeRange = 'under_18' | '18_25' | '26_35' | '36_45' | 'above_45'

/** 通用 ID 类型 */
export type ID = string

/** 时间戳类型 */
export type Timestamp = number

/** ISO 日期字符串 */
export type ISODate = string
