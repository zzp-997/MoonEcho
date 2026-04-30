/**
 * 回声 - 情绪日记接口
 * 文件：src/api/diary.ts
 * 说明：情绪日记相关接口，包括创建日记、隐私同意、同步设置等
 */

import api from './index'
import type { ApiResponse } from '../types'

// ==================== 类型定义 ====================

/** 情绪色调类型 */
export type EmotionTone = 'warm_orange' | 'light_green' | 'gray_blue' | 'deep_blue' | 'dark_purple'

/** 同步模式类型 */
export type SyncMode = 'local_only' | 'cloud_sync'

/** 情绪色调元数据 */
export interface EmotionToneMeta {
  /** 色调值 */
  tone: EmotionTone
  /** 颜色代码 */
  color: string
  /** 含义描述 */
  meaning: string
  /** 代表语 */
  phrase: string
  /** 提示语 */
  hint: string
}

/** 创建日记参数 */
export interface CreateDiaryParams {
  /** 情绪色调 */
  emotion_tone: EmotionTone
  /** 情绪标签列表，最多3个 */
  emotion_labels?: string[]
  /** 日记内容文字，最多2000字 */
  content_text?: string
  /** 记录日期 YYYY-MM-DD */
  record_date: string
  /** 客户端唯一标识 */
  client_id?: string
  /** 内容是否已加密 */
  is_encrypted?: boolean
}

/** 日记响应 */
export interface DiaryResponse {
  /** 日记ID */
  id: string
  /** 情绪色调 */
  emotion_tone: EmotionTone | null
  /** 情绪标签列表 */
  emotion_labels: string[] | null
  /** 日记内容 */
  content_text: string | null
  /** 记录日期 */
  record_date: string
  /** 是否已同步 */
  is_synced: boolean
  /** 是否加密 */
  is_encrypted: boolean
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
  /** 是否为0字记录 */
  is_zero_record: boolean
}

/** 隐私同意状态响应 */
export interface PrivacyConsentResponse {
  /** 是否已同意隐私声明 */
  has_consented: boolean
  /** 同意时间 */
  consented_at: string | null
  /** 当前同步模式 */
  sync_mode: SyncMode
}

/** 设置隐私同意参数 */
export interface PrivacyConsentRequest {
  /** 同步模式 */
  sync_mode: SyncMode
}

// ==================== 情绪色调常量 ====================

/** 情绪色调元数据映射 */
export const EMOTION_TONE_META: Record<EmotionTone, EmotionToneMeta> = {
  warm_orange: {
    tone: 'warm_orange',
    color: '#FF9A5C',
    meaning: '充满能量、开心',
    phrase: '今天还不错',
    hint: '今天什么好事发生了？',
  },
  light_green: {
    tone: 'light_green',
    color: '#8FCCA0',
    meaning: '平静、安稳',
    phrase: '还算正常',
    hint: '随便聊聊今天吧',
  },
  gray_blue: {
    tone: 'gray_blue',
    color: '#8BA7C4',
    meaning: '低落、沉闷',
    phrase: '有点堵',
    hint: '什么事让你觉得堵？',
  },
  deep_blue: {
    tone: 'deep_blue',
    color: '#4A6FA5',
    meaning: '难过、忧伤',
    phrase: '很难受',
    hint: '如果不想说具体的，说说那种感觉也行',
  },
  dark_purple: {
    tone: 'dark_purple',
    color: '#6B4C7A',
    meaning: '崩溃、混乱',
    phrase: '说不清',
    hint: '这里只有你自己，写什么都行',
  },
}

/** 情绪色调列表（按顺序） */
export const EMOTION_TONE_LIST: EmotionTone[] = [
  'warm_orange',
  'light_green',
  'gray_blue',
  'deep_blue',
  'dark_purple',
]

/** 情绪标签池 */
export const EMOTION_LABELS_POOL: Record<EmotionTone, string[]> = {
  warm_orange: ['开心', '感恩', '兴奋', '被爱', '有希望', '自豪', '释然'],
  light_green: ['平静', '放松', '专注', '安心', '满足', '无聊'],
  gray_blue: ['焦虑', '疲惫', '迷茫', '孤独', '委屈', '烦躁'],
  deep_blue: ['难过', '失望', '自责', '心疼', '想念', '害怕'],
  dark_purple: ['混乱', '麻木', '空洞', '矛盾', '崩溃', '说不清'],
}

// ==================== API 接口 ====================

/**
 * 创建日记
 * @param params 创建参数
 * @returns 日记响应
 */
export function createDiary(params: CreateDiaryParams): Promise<DiaryResponse> {
  return api.post<DiaryResponse>('/diaries', params)
}

/**
 * 获取隐私同意状态
 * @returns 隐私同意状态
 */
export function getPrivacyConsent(): Promise<PrivacyConsentResponse> {
  return api.get<PrivacyConsentResponse>('/diaries/privacy')
}

/**
 * 设置隐私同意
 * @param params 同意参数
 * @returns 隐私同意状态
 */
export function setPrivacyConsent(params: PrivacyConsentRequest): Promise<PrivacyConsentResponse> {
  return api.post<PrivacyConsentResponse>('/diaries/privacy', params)
}

/**
 * 获取日记详情
 * @param id 日记ID
 * @returns 日记详情
 */
export function getDiaryDetail(id: string): Promise<DiaryResponse> {
  return api.get<DiaryResponse>(`/diaries/${id}`)
}

/**
 * 更新日记
 * @param id 日记ID
 * @param params 更新参数
 * @returns 日记响应
 */
export function updateDiary(
  id: string,
  params: Partial<CreateDiaryParams>
): Promise<DiaryResponse> {
  return api.put<DiaryResponse>(`/diaries/${id}`, params)
}

/**
 * 删除日记
 * @param id 日记ID
 */
export function deleteDiary(id: string): Promise<void> {
  return api.delete(`/diaries/${id}`)
}

/**
 * 获取日记列表
 * @param params 查询参数
 * @returns 日记列表
 */
export function getDiaryList(params?: {
  /** 起始日期 */
  start_date?: string
  /** 结束日期 */
  end_date?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  page_size?: number
}): Promise<{
  data: DiaryResponse[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}> {
  return api.get('/diaries', params)
}

/**
 * 获取日记统计
 * @returns 统计数据
 */
export function getDiaryStats(): Promise<{
  total_records: number
  total_days: number
  zero_record_count: number
  valid_sample_count: number
  emotion_distribution: Record<string, number>
}> {
  return api.get('/diaries/stats')
}

/**
 * 删除全部日记
 */
export function deleteAllDiaries(): Promise<void> {
  return api.delete('/diaries/all')
}

/**
 * 导出日记
 * @param format 导出格式 json/pdf
 * @param params 导出参数
 * @returns 导出文件URL或数据
 */
export function exportDiaries(
  format: 'json' | 'pdf',
  params?: {
    start_date?: string
    end_date?: string
  }
): Promise<{ file_url: string; file_name: string }> {
  return api.post('/diaries/export', { format, ...params })
}

// ==================== 情绪周报相关 ====================

/** 情绪周报响应 */
export interface WeeklyReportResponse {
  /** 周报ID */
  id: string
  /** 本周起始日期（周一） */
  week_start_date: string
  /** 本周结束日期（周日） */
  week_end_date: string
  /** 动态标题，如'这周像一场漫长的周三' */
  title: string | null
  /** 情绪故事线，叙事体描述本周情绪走势 */
  story_line: string | null
  /** 情绪关键词列表 */
  keywords: string[] | null
  /** 一句看见，提炼核心感受 */
  insight: string | null
  /** 温和建议，措辞谨慎 */
  suggestion: string | null
  /** 下周展望，一句话收束 */
  outlook: string | null
  /** 本周分析日记数量 */
  diary_count: number
  /** 生成时间 */
  created_at: string
  /** 是否为空周报（本周无有效日记） */
  is_empty: boolean
  /** 是否来自缓存 */
  is_cached: boolean
}

/** 空周报响应 */
export interface EmptyWeeklyReportResponse {
  /** 本周起始日期（周一） */
  week_start_date: string
  /** 本周结束日期（周日） */
  week_end_date: string
  /** 是否为空周报 */
  is_empty: true
  /** 提示信息 */
  message: string
  /** 本周有效日记数量 */
  diary_count: number
}

/** 周报历史项 */
export interface WeeklyReportHistoryItem {
  /** 周报ID */
  id: string
  /** 本周起始日期（周一） */
  week_start_date: string
  /** 本周结束日期（周日） */
  week_end_date: string
  /** 动态标题 */
  title: string | null
  /** 一句看见 */
  insight: string | null
  /** 本周分析日记数量 */
  diary_count: number
  /** 生成时间 */
  created_at: string
}

/** 周报历史响应 */
export interface WeeklyReportHistoryResponse {
  /** 周报列表 */
  data: WeeklyReportHistoryItem[]
  /** 分页信息 */
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

/**
 * 获取本周情绪周报
 * @param forceRefresh 是否强制重新生成
 * @returns 周报响应
 */
export function getWeeklyReport(
  forceRefresh = false
): Promise<WeeklyReportResponse | EmptyWeeklyReportResponse> {
  return api.get('/diaries/report/weekly', { force_refresh: forceRefresh })
}

/**
 * 获取周报历史
 * @param params 分页参数
 * @returns 周报历史列表
 */
export function getWeeklyReportHistory(params?: {
  /** 页码 */
  page?: number
  /** 每页数量 */
  page_size?: number
}): Promise<WeeklyReportHistoryResponse> {
  return api.get('/diaries/report/history', params)
}

/**
 * 类型守卫：判断是否为空周报响应
 * @param response 周报响应
 * @returns 是否为空周报
 */
export function isEmptyReport(
  response: WeeklyReportResponse | EmptyWeeklyReportResponse
): response is EmptyWeeklyReportResponse {
  return 'is_empty' in response && response.is_empty === true
}
