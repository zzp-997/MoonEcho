/**
 * 回声 - API 响应类型定义
 * 文件：src/api/types/index.ts
 * 说明：与后端 tech_architecture.md 统一响应格式保持一致
 */

/** API 统一响应格式 */
export interface ApiResponse<T = any> {
  /** 是否成功 */
  success: boolean
  /** 响应数据 */
  data?: T
  /** 错误信息 */
  error?: ApiError
  /** 分页信息 */
  pagination?: Pagination
  /** 元数据 */
  meta?: ApiMeta
}

/** API 错误信息 */
export interface ApiError {
  /** 错误码（语义化） */
  code: string
  /** 错误消息 */
  message: string
  /** 错误详情 */
  details?: any
}

/** 分页信息 */
export interface Pagination {
  /** 当前页码 */
  page: number
  /** 每页数量 */
  pageSize: number
  /** 总数 */
  total: number
  /** 是否有更多 */
  hasMore: boolean
}

/** API 元数据 */
export interface ApiMeta {
  /** 时间戳 */
  timestamp: string
  /** 请求ID */
  requestId: string
}

/** 请求配置 */
export interface RequestConfig {
  /** 是否显示loading */
  showLoading?: boolean
  /** loading文案 */
  loadingText?: string
  /** 是否静默处理错误（不显示Toast） */
  silent?: boolean
  /** 自定义请求头 */
  headers?: Record<string, string>
  /** 超时时间(ms) */
  timeout?: number
  /** 是否需要认证 */
  requireAuth?: boolean
}

/** 分页请求参数 */
export interface PageParams {
  page?: number
  pageSize?: number
}
