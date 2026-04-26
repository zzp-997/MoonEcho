// 内容管理相关类型

// 内容类型
export type AdminContentType = 'post' | 'treehole_post'

// 内容状态
export type ContentStatus = 'active' | 'hidden' | 'deleted'

// 内容列表项
export interface ContentListItem {
  id: string
  content_type: AdminContentType
  content_preview: string
  author_id: string | null
  author_nickname: string | null
  author_phone: string | null // 脱敏
  status: ContentStatus
  image_urls: string[] | null
  topic_tag: string | null
  like_count: number | null
  comment_count: number | null
  resonance_count: number | null // 树洞专属
  is_anonymous: boolean | null // 动态专属
  created_at: string
  deleted_at: string | null
  is_recommended: boolean
  report_count: number
}

// 内容详情
export interface ContentDetail extends ContentListItem {
  content: string
}

// 内容状态修改请求
export interface ContentStatusRequest {
  action: 'hide' | 'show' | 'recommend' | 'unrecommend'
  reason?: string
}

// 内容状态修改响应
export interface ContentStatusResponse {
  content_id: string
  content_type: AdminContentType
  status: ContentStatus
  is_recommended: boolean
  updated_at: string
}