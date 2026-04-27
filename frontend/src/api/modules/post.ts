/**
 * 回声 - 动态广场 API 封装
 * 文件：src/api/modules/post.ts
 * 说明：动态广场相关 API 请求封装，包括动态 CRUD、共鸣、评论、收藏、悄悄关注、AI 文案润色
 */

import { api } from '../index'

// ==================== 类型定义 ====================

/** 动态作者信息（实名） */
export interface PostAuthor {
  id: string
  nickname: string
  avatar_url: string | null
}

/** 动态作者信息（匿名） */
export interface PostAnonIdentity {
  anon_id: string
  anon_nickname: string
  persona_tag: string | null
  anon_avatar_url: string | null
}

/** 模糊时间 */
export interface FuzzyTime {
  fuzzy_display: string
}

/** 动态帖子 */
export interface Post {
  id: string
  content: string
  image_urls: string[] | null
  is_anonymous: boolean
  author: PostAuthor | null
  anon_identity: PostAnonIdentity | null
  resonance_count: number
  comment_count: number
  bookmark_count: number
  has_resonated: boolean
  has_bookmarked: boolean
  has_whisper_followed: boolean
  fuzzy_time: FuzzyTime | null
  created_at: string
}

/** 动态列表响应 */
export interface PostListResponse {
  data: Post[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

/** 动态详情响应 */
export interface PostDetailResponse {
  post: Post
  comments: PostComment[]
}

/** 动态评论 */
export interface PostComment {
  id: string
  content: string
  author_id: string
  author_nickname: string
  author_avatar_url: string | null
  reply_to_id: string | null
  reply_to_nickname: string | null
  fuzzy_time: FuzzyTime | null
  created_at: string
}

/** 创建动态请求 */
export interface CreatePostRequest {
  content: string
  image_urls?: string[]
  is_anonymous?: boolean
}

/** 创建动态响应 */
export interface CreatePostResponse {
  post: Post
  audit_feedback: AuditFeedback | null
}

/** 审核反馈 */
export interface AuditFeedback {
  result: 'block' | 'warn'
  feedback: string
  labels: string[]
}

/** 创建评论请求 */
export interface CreateCommentRequest {
  content: string
  reply_to_id?: string | null
}

/** 创建评论响应 */
export interface CreateCommentResponse {
  comment: PostComment
  audit_feedback: AuditFeedback | null
}

/** 共鸣响应 */
export interface ResonanceResponse {
  resonance_count: number
  message: string
  already_resonated: boolean
}

/** 收藏响应 */
export interface BookmarkResponse {
  bookmark_count: number
  message: string
  already_bookmarked: boolean
}

/** 悄悄关注响应 */
export interface WhisperFollowResponse {
  message: string
  already_following: boolean
}

/** AI 润色风格 */
export type PolishStyle = 'warm' | 'humor' | 'sincere'

/** AI 润色风格标签 */
export const POLISH_STYLE_LABELS: Record<PolishStyle, string> = {
  warm: '温暖治愈风',
  humor: '轻松幽默风',
  sincere: '真诚分享风',
}

/** AI 润色请求 */
export interface PolishContentRequest {
  content: string
  style?: PolishStyle
}

/** AI 润色响应 */
export interface PolishContentResponse {
  original_content: string
  polished_content: string
  style: PolishStyle
  suggestions?: string[]
}

/** 动态筛选排序方式 */
export type PostSortBy = 'latest' | 'hot' | 'following'

/** 动态列表查询参数 */
export interface PostQueryParams {
  page?: number
  page_size?: number
  sort_by?: PostSortBy
}

// ==================== API 函数 ====================

/**
 * 获取动态列表
 * @param params 分页和筛选参数
 */
export async function getPosts(params?: PostQueryParams): Promise<PostListResponse> {
  return api.get<PostListResponse>('/posts', params)
}

/**
 * 获取动态详情
 * @param postId 动态ID
 */
export async function getPostDetail(postId: string): Promise<PostDetailResponse> {
  return api.get<PostDetailResponse>(`/posts/${postId}`)
}

/**
 * 发布动态
 * @param data 动态内容
 */
export async function createPost(data: CreatePostRequest): Promise<CreatePostResponse> {
  return api.post<CreatePostResponse>('/posts', data)
}

/**
 * 删除动态
 * @param postId 动态ID
 */
export async function deletePost(postId: string): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/posts/${postId}`)
}

/**
 * 创建共鸣
 * @param postId 动态ID
 */
export async function createResonance(postId: string): Promise<ResonanceResponse> {
  return api.post<ResonanceResponse>(`/posts/${postId}/resonance`)
}

/**
 * 创建收藏
 * @param postId 动态ID
 */
export async function createBookmark(postId: string): Promise<BookmarkResponse> {
  return api.post<BookmarkResponse>(`/posts/${postId}/bookmark`)
}

/**
 * 取消收藏
 * @param postId 动态ID
 */
export async function deleteBookmark(postId: string): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/posts/${postId}/bookmark`)
}

/**
 * 悄悄关注作者
 * @param postId 动态ID
 */
export async function createWhisperFollow(postId: string): Promise<WhisperFollowResponse> {
  return api.post<WhisperFollowResponse>(`/posts/${postId}/whisper-follow`)
}

/**
 * 取消悄悄关注
 * @param postId 动态ID
 */
export async function deleteWhisperFollow(postId: string): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/posts/${postId}/whisper-follow`)
}

/**
 * 创建评论
 * @param postId 动态ID
 * @param data 评论内容
 */
export async function createComment(
  postId: string,
  data: CreateCommentRequest
): Promise<CreateCommentResponse> {
  return api.post<CreateCommentResponse>(`/posts/${postId}/comments`, data)
}

/**
 * 删除评论
 * @param postId 动态ID
 * @param commentId 评论ID
 */
export async function deleteComment(
  postId: string,
  commentId: string
): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/posts/${postId}/comments/${commentId}`)
}

/**
 * AI 文案润色
 * @param data 润色请求
 */
export async function polishContent(data: PolishContentRequest): Promise<PolishContentResponse> {
  return api.post<PolishContentResponse>('/posts/polish', data)
}

/**
 * 上传动态图片
 * @param filePath 本地文件路径
 */
export async function uploadPostImage(filePath: string): Promise<{ url: string }> {
  return api.upload<{ url: string }>('/posts/upload-image', filePath, 'image')
}

// ==================== 工具函数 ====================

/**
 * 格式化计数
 */
export function formatPostCount(count: number): string {
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + 'w'
  }
  if (count >= 1000) {
    return (count / 1000).toFixed(1) + 'k'
  }
  return String(count)
}

/**
 * 生成匿名身份预览（仅用于发布前的 UI 预览）
 *
 * 注意：实际发布时，后端会生成真正的匿名身份并存储。
 * 此函数仅用于前端预览，不保证与后端生成的身份一致。
 *
 * 安全改进：使用 Math.random() 而非 Date.now()，避免同一毫秒内重复
 */
export function generateAnonIdentity(): { nickname: string; persona: string } {
  // 预设的匿名昵称词库
  const adjectives = [
    '迷路的',
    '倔强的',
    '温柔的',
    '沉默的',
    '深夜的',
    '孤独的',
    '安静的',
    '忧郁的',
    '月亮上的',
    '情绪',
    '星星的',
    '云朵里的',
  ]
  const nouns = [
    '信天翁',
    '蒲公英',
    '月亮',
    '星星',
    '猫',
    '云朵',
    '旅人',
    '听风者',
    '收集者',
    '收藏家',
    '漫步者',
    '追光者',
  ]

  // 使用 Math.random() 生成随机身份（比 Date.now() 更安全，避免同一毫秒内重复）
  const adjIndex = Math.floor(Math.random() * adjectives.length)
  const nounIndex = Math.floor(Math.random() * nouns.length)

  const nickname = adjectives[adjIndex] + nouns[nounIndex]

  // 气质标签
  const personas = [
    '温柔系',
    '佛系',
    '话痨系',
    '毒舌系',
    '文艺系',
    '憨憨系',
    '社恐系',
    '老灵魂',
    '野生哲学家',
    '深夜修仙党',
  ]
  const persona = personas[Math.floor(Math.random() * personas.length)]

  return { nickname, persona }
}
