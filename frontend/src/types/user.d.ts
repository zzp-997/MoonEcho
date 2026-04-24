/**
 * 回声 - 用户类型定义
 * 文件：src/types/user.d.ts
 * 说明：用户相关类型声明
 */

/** 用户信息 */
export interface UserInfo {
  id: string
  phone: string
  nickname: string
  avatarUrl?: string
  ageRange?: string
  city?: string
  occupation?: string
  interests?: string[]
  createdAt?: string
  updatedAt?: string
  is_active?: boolean
}

/** 登录请求参数 */
export interface LoginParams {
  phone: string
  code: string
}

/** 登录响应数据 */
export interface LoginResult {
  token: string
  refreshToken: string
  user: UserInfo
}

/** 注册请求参数 */
export interface RegisterParams {
  phone: string
  code: string
  nickname: string
  ageRange: string
}

/** 匿名身份 */
export interface AnonymousIdentity {
  id: string
  anonNickname: string
  anonAvatar?: string
  personalityTag?: string
  expiresAt?: string
  isActive: boolean
}
