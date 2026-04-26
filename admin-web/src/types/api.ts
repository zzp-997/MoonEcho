// API 响应通用类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  meta?: {
    timestamp: string
    requestId: string
  }
  error?: {
    code: string
    message: string
    details?: Record<string, any>
  }
}

// 分页响应
export interface PaginatedResponse<T = any> {
  success: boolean
  data: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
    hasMore: boolean
  }
  meta?: {
    timestamp: string
    requestId: string
  }
}

// 分页请求参数
export interface PaginationParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}