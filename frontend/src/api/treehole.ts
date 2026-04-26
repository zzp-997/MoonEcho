/**
 * 回声 - 树洞 API 封装
 * 文件：src/api/treehole.ts
 * 说明：树洞吐槽区相关 API 请求封装
 */

import { api } from './index'

// ==================== 类型定义 ====================

/** 话题标签枚举 */
export enum TopicTag {
  WORK = 'work',
  FAMILY = 'family',
  RELATIONSHIP = 'relationship',
  FRIENDS = 'friends',
  SELF = 'self',
  LIFE = 'life',
  SCHOOL = 'school',
  MONEY = 'money',
  HEALTH = 'health',
  OTHER = 'other',
}

/** 话题标签显示名称 */
export const TOPIC_TAG_LABELS: Record<string, string> = {
  [TopicTag.WORK]: '工作吐槽',
  [TopicTag.FAMILY]: '家庭关系',
  [TopicTag.RELATIONSHIP]: '情感恋爱',
  [TopicTag.FRIENDS]: '友情人际',
  [TopicTag.SELF]: '自我成长',
  [TopicTag.LIFE]: '生活琐事',
  [TopicTag.SCHOOL]: '学业压力',
  [TopicTag.MONEY]: '经济压力',
  [TopicTag.HEALTH]: '健康身心',
  [TopicTag.OTHER]: '其他',
}

/** 匿名身份 */
export interface AnonymousIdentity {
  anon_id: string
  anon_nickname: string
  persona_tag: string | null
  anon_avatar_url: string | null
}

/** 模糊时间 */
export interface FuzzyTime {
  fuzzy_display: string
}

/** 树洞帖子 */
export interface TreeholePost {
  id: string
  content: string
  topic_tag: string | null
  topic_tag_label: string | null
  image_urls: string[] | null
  anon_identity: AnonymousIdentity | null
  resonance_count: number
  comment_count: number
  fuzzy_time: FuzzyTime | null
  is_mine?: boolean
  has_resonated?: boolean
}

/** 帖子列表响应 */
export interface TreeholePostListResponse {
  data: TreeholePost[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
  topic_tags: Record<string, string> | null
}

/** 帖子详情响应 */
export interface TreeholePostDetailResponse {
  post: TreeholePost
  comments: TreeholeComment[]
}

/** 树洞评论 */
export interface TreeholeComment {
  id: string
  content: string
  is_resonance: boolean
  fuzzy_time: FuzzyTime | null
}

/** 创建帖子请求 */
export interface CreatePostRequest {
  content: string
  topic_tag?: TopicTag | string | null
  image_urls?: string[] | null
  use_ai_rewrite?: boolean
}

/** 审核反馈信息 */
export interface AuditFeedback {
  result: 'block' | 'warn'
  feedback: string
  labels: string[]
}

/** 脱敏提醒信息 */
export interface IdentityWarning {
  has_warning: boolean
  warning_message: string
  detected_types: string[]
}

/** 创建帖子响应 */
export interface CreatePostResponse {
  post: TreeholePost
  audit_feedback: AuditFeedback | null
  identity_warning: IdentityWarning | null
  trigger_care: boolean
}

/** 创建评论请求 */
export interface CreateCommentRequest {
  content: string
}

/** 创建评论响应 */
export interface CreateCommentResponse {
  comment: TreeholeComment
  audit_feedback: AuditFeedback | null
  identity_warning: IdentityWarning | null
  harassment_warning: string | null
}

/** 共鸣响应 */
export interface ResonanceResponse {
  resonance_count: number
  message: string
  already_resonated: boolean
}

/** 话题标签响应 */
export interface TopicResponse {
  value: string
  label: string
}

/** 话题标签列表响应 */
export interface TopicListResponse {
  topics: TopicResponse[]
}

/** 申诉请求 */
export interface AppealRequest {
  reason: string
}

/** 申诉响应 */
export interface AppealResponse {
  id: string
  status: 'pending' | 'approved' | 'rejected'
  message: string
}

// ==================== API 函数 ====================

/**
 * 获取树洞帖子列表
 * @param params 分页参数和筛选条件
 */
export async function getTreeholePosts(params?: {
  page?: number
  page_size?: number
  topic_tag?: string | null
}): Promise<TreeholePostListResponse> {
  return api.get<TreeholePostListResponse>('/treehole/posts', params)
}

/**
 * 获取帖子详情
 * @param postId 帖子ID
 */
export async function getTreeholePostDetail(postId: string): Promise<TreeholePostDetailResponse> {
  return api.get<TreeholePostDetailResponse>(`/treehole/posts/${postId}`)
}

/**
 * 发布树洞帖子
 * @param data 帖子内容
 */
export async function createTreeholePost(data: CreatePostRequest): Promise<CreatePostResponse> {
  return api.post<CreatePostResponse>('/treehole/posts', data)
}

/**
 * 创建共鸣（"我懂你"）
 * @param postId 帖子ID
 */
export async function createResonance(postId: string): Promise<ResonanceResponse> {
  return api.post<ResonanceResponse>(`/treehole/posts/${postId}/resonance`)
}

/**
 * 创建评论
 * @param postId 帖子ID
 * @param data 评论内容
 */
export async function createTreeholeComment(
  postId: string,
  data: CreateCommentRequest
): Promise<CreateCommentResponse> {
  return api.post<CreateCommentResponse>(`/treehole/posts/${postId}/comments`, data)
}

/**
 * 删除帖子
 * @param postId 帖子ID
 */
export async function deleteTreeholePost(postId: string): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/treehole/posts/${postId}`)
}

/**
 * 创建申诉
 * @param postId 帖子ID
 * @param data 申诉理由
 */
export async function createAppeal(postId: string, data: AppealRequest): Promise<AppealResponse> {
  return api.post<AppealResponse>(`/treehole/posts/${postId}/appeal`, data)
}

/**
 * 获取话题标签列表
 */
export async function getTopicTags(): Promise<TopicListResponse> {
  return api.get<TopicListResponse>('/treehole/topics')
}

// ==================== 工具函数 ====================

/**
 * 获取话题标签显示名称
 */
export function getTopicLabel(tag: string | null): string {
  if (!tag) return ''
  return TOPIC_TAG_LABELS[tag] || tag
}

/**
 * 生成随机虚拟头像 SVG
 * 使用不同颜色和图案组合
 */
export function generateVirtualAvatar(seed?: string): string {
  // 基于种子生成稳定的随机颜色
  const colors = [
    '#FFB5BA', // 粉色
    '#8B9DC3', // 蓝灰
    '#7CB9A0', // 绿色
    '#A89CF5', // 紫色
    '#FFB88A', // 橙色
    '#A5C0D6', // 浅蓝
    '#D4A5D9', // 淡紫
    '#8B6C9A', // 深紫
    '#6B8FC0', // 中蓝
    '#A8D9B5', // 浅绿
  ]

  // 使用种子选择颜色
  const index = seed
    ? seed.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length
    : Math.floor(Math.random() * colors.length)

  const color = colors[index]

  // 返回一个简单的 SVG 数据 URL
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
      <circle cx="24" cy="24" r="24" fill="${color}"/>
      <circle cx="24" cy="20" r="8" fill="rgba(255,255,255,0.3)"/>
      <circle cx="24" cy="36" r="10" fill="rgba(255,255,255,0.2)"/>
    </svg>
  `

  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

/**
 * 格式化模糊时间显示
 * 后端已返回 fuzzy_display，此函数仅用于后备
 */
export function formatFuzzyTime(time: string): string {
  if (!time) return ''

  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (60 * 1000))
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (minutes < 1) return '刚刚'
  if (minutes < 5) return '几分钟前'
  if (minutes < 15) return '十几分钟前'
  if (minutes < 30) return '半小时前'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 2) return '1小时前'
  if (hours < 24) return `${hours}小时前`
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  return '很久了'
}
