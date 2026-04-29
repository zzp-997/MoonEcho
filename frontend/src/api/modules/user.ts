/**
 * 回声 - 用户接口
 * 文件：src/api/modules/user.ts
 * 说明：用户信息相关接口，包含个人中心、设置、社交能量等功能
 */

import { api } from '../index'

// ==================== 类型定义 ====================

/** 用户详细信息 */
export interface UserDetail {
  id: string
  phone: string
  nickname: string | null
  avatar_url: string | null
  age_range: string | null
  city: string | null
  occupation: string | null
  is_minor: boolean
  social_energy: number | null
  created_at: string
  tags: UserTag[]
}

/** 用户标签 */
export interface UserTag {
  id: string
  tag_key: string
  tag_value: string
  created_at: string
}

/** 用户更新请求 */
export interface UserUpdateRequest {
  nickname?: string
  avatar_url?: string
  city?: string
  occupation?: string
}

/** 用户标签创建请求 */
export interface UserTagCreateRequest {
  tag_key?: string
  tag_value: string
}

/** 用户标签列表响应 */
export interface UserTagsResponse {
  tags: UserTag[]
  total: number
}

/** AI画像标签项 */
export interface ProfileTagItem {
  tag_type: 'emotion_pattern' | 'social_preference' | 'interest'
  tag_name: string
  tag_value: string
  is_visible: boolean
}

/** AI画像标签响应 */
export interface AIProfileTagResponse {
  tags: ProfileTagItem[]
  generated_at: string | null
  message: string | null
}

/** 社交能量响应 */
export interface SocialEnergyResponse {
  energy: number
  percentage: string
  status: string
  can_rest: boolean
  rest_cooldown_remaining: number
  updated_at: string | null
}

/** 主动休息响应 */
export interface RestResponse {
  old_energy: number
  new_energy: number
  change: number
  message: string
  cooldown_until: number
}

/** 社交暴露级别解锁状态 */
export interface SocialLevelUnlockStatus {
  level_1: boolean
  level_2: boolean
  level_3: boolean
  level_4: boolean
  level_5: boolean
  level_6: boolean
}

/** 行为统计数据 */
export interface BehaviorStats {
  browse_count: number
  like_count: number
  comment_count: number
  follow_count: number
  friend_request_count: number
  chat_count: number
}

/** 渐进式社交暴露级别响应 */
export interface SocialLevelResponse {
  current_level: number
  level_name: string
  description: string
  progress_description: string
  unlock_status: SocialLevelUnlockStatus
  next_action: string | null
  behavior_stats: BehaviorStats
}

/** 用户公开信息（查看他人） */
export interface UserPublicInfo {
  user_id: string
  nickname: string | null
  avatar_url: string | null
  profile_tags: ProfileTagItem[]
}

/** 公开动态项 */
export interface PublicPostItem {
  post_id: string
  content: string
  image_urls: string[] | null
  like_count: number
  comment_count: number
  created_at: string
}

/** 公开动态列表响应 */
export interface PublicPostsResponse {
  data: PublicPostItem[]
  page: number
  page_size: number
  total: number
  has_more: boolean
}

// ==================== API 函数 ====================

/**
 * 获取自己的用户信息
 */
export async function getMyProfile(): Promise<UserDetail> {
  return api.get<UserDetail>('/users/me')
}

/**
 * 更新自己的资料
 * @param data 更新数据
 */
export async function updateMyProfile(data: UserUpdateRequest): Promise<UserDetail> {
  return api.patch<UserDetail>('/users/me', data)
}

/**
 * 获取我的兴趣标签
 */
export async function getMyTags(): Promise<UserTagsResponse> {
  return api.get<UserTagsResponse>('/users/me/tags')
}

/**
 * 添加兴趣标签
 * @param data 标签数据
 */
export async function addMyTag(data: UserTagCreateRequest): Promise<UserTag> {
  return api.post<UserTag>('/users/me/tags', data)
}

/**
 * 删除兴趣标签
 * @param tagId 标签ID
 */
export async function deleteMyTag(tagId: string): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/users/me/tags/${tagId}`)
}

/**
 * 获取AI画像标签
 */
export async function getMyProfileTags(): Promise<AIProfileTagResponse> {
  return api.get<AIProfileTagResponse>('/users/me/profile-tags')
}

/**
 * 获取社交能量
 */
export async function getSocialEnergy(): Promise<SocialEnergyResponse> {
  return api.get<SocialEnergyResponse>('/users/me/social-energy')
}

/**
 * 主动休息恢复能量
 */
export async function restSocialEnergy(): Promise<RestResponse> {
  return api.post<RestResponse>('/users/me/social-energy/rest')
}

/**
 * 获取渐进式社交暴露级别
 */
export async function getSocialLevel(): Promise<SocialLevelResponse> {
  return api.get<SocialLevelResponse>('/users/me/social-level')
}

/**
 * 查看他人公开信息
 * @param userId 用户ID
 */
export async function getUserPublicInfo(userId: string): Promise<UserPublicInfo> {
  return api.get<UserPublicInfo>(`/users/${userId}`)
}

/**
 * 获取他人公开动态列表
 * @param userId 用户ID
 * @param page 页码
 * @param pageSize 每页数量
 */
export async function getUserPublicPosts(
  userId: string,
  page = 1,
  pageSize = 5
): Promise<PublicPostsResponse> {
  return api.get<PublicPostsResponse>(`/users/${userId}/public-posts`, { page, page_size: pageSize })
}

// ==================== 兼容旧接口（逐步迁移后可删除） ====================

/** 获取用户信息（兼容旧接口） */
export function getUserInfo() {
  return getMyProfile()
}

/** 更新用户信息（兼容旧接口） */
export function updateUserInfo(data: Partial<UserDetail>) {
  return updateMyProfile({
    nickname: data.nickname ?? undefined,
    avatar_url: data.avatar_url ?? undefined,
    city: data.city ?? undefined,
    occupation: data.occupation ?? undefined,
  })
}

/** 上传头像 */
export function uploadAvatar(filePath: string) {
  return api.upload<string>('/user/avatar', filePath)
}

/** 获取匿名身份列表 */
export function getAnonymousIdentities() {
  return api.get('/user/anonymous-identities')
}

// ==================== 工具函数 ====================

/**
 * 获取社交级别名称
 */
export function getSocialLevelName(level: number): string {
  const names: Record<number, string> = {
    1: '观察者',
    2: '探索者',
    3: '参与者',
    4: '关注者',
    5: '连接者',
    6: '交流者',
  }
  return names[level] || '未知'
}

/**
 * 获取社交级别描述
 */
export function getSocialLevelDescription(level: number): string {
  const descriptions: Record<number, string> = {
    1: '浏览动态广场（零社交压力）',
    2: '点共鸣/点赞（最小社交动作）',
    3: '评论互动（轻度社交）',
    4: '悄悄关注（单向关注）',
    5: '发送好友申请（双向连接）',
    6: '私聊（深度社交）',
  }
  return descriptions[level] || '未知级别'
}

/**
 * 获取能量状态颜色
 */
export function getEnergyColor(energy: number): string {
  if (energy >= 80) return 'var(--color-success)'
  if (energy >= 60) return 'var(--mood-calm)'
  if (energy >= 40) return 'var(--mood-warm)'
  if (energy >= 20) return 'var(--color-warning)'
  return 'var(--color-error)'
}

/**
 * 获取能量状态文本
 */
export function getEnergyStatusText(energy: number): string {
  if (energy >= 80) return '能量充足'
  if (energy >= 60) return '能量良好'
  if (energy >= 40) return '能量一般'
  if (energy >= 20) return '能量较低'
  return '能量不足'
}

/**
 * 获取画像标签类型名称
 */
export function getProfileTagTypeName(tagType: ProfileTagItem['tag_type']): string {
  const names: Record<ProfileTagItem['tag_type'], string> = {
    emotion_pattern: '情绪模式',
    social_preference: '社交偏好',
    interest: '兴趣领域',
  }
  return names[tagType] || '未知'
}
