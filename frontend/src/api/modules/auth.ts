/**
 * 回声 - 认证接口
 * 文件：src/api/modules/auth.ts
 * 说明：登录、注册、验证码、完善资料等认证相关接口
 * 后端端点参考（T005）：
 *   POST /api/v1/auth/send-code       # 发送验证码
 *   POST /api/v1/auth/verify-code     # 验证码登录/注册（返回 is_new_user）
 *   POST /api/v1/auth/complete-profile # 完善资料（昵称+年龄段）
 *   POST /api/v1/auth/refresh-token   # 刷新token
 */

import api from '../index'

// ==================== 类型定义 ====================

/** 发送验证码请求参数 */
export interface SendCodeParams {
  phone: string
}

/** 发送验证码响应 */
export interface SendCodeResult {
  success: boolean
  message?: string
}

/** 验证码登录/注册请求参数 */
export interface VerifyCodeParams {
  phone: string
  code: string
}

/** 验证码登录/注册响应 */
export interface VerifyCodeResult {
  token: string
  refreshToken: string
  is_new_user: boolean
  user: {
    id: string
    phone: string
    nickname?: string
    avatarUrl?: string
    ageRange?: string
    is_minor?: boolean
  }
}

/** 完善资料请求参数 */
export interface CompleteProfileParams {
  nickname: string
  ageRange: string
}

/** 完善资料响应 */
export interface CompleteProfileResult {
  id: string
  phone: string
  nickname: string
  avatarUrl?: string
  ageRange: string
  is_minor: boolean
}

/** 刷新 Token 请求参数 */
export interface RefreshTokenParams {
  refreshToken: string
}

/** 刷新 Token 响应 */
export interface RefreshTokenResult {
  token: string
  refreshToken: string
}

// ==================== API 方法 ====================

/** 发送验证码 */
export function sendVerifyCode(params: SendCodeParams) {
  return api.post<SendCodeResult>('/auth/send-code', params, { requireAuth: false })
}

/** 验证码登录/注册 */
export function verifyCode(params: VerifyCodeParams) {
  return api.post<VerifyCodeResult>('/auth/verify-code', params, { requireAuth: false })
}

/** 完善个人资料 */
export function completeProfile(params: CompleteProfileParams) {
  return api.post<CompleteProfileResult>('/auth/complete-profile', params, { requireAuth: true })
}

/** 刷新 Token */
export function refreshToken(params: RefreshTokenParams) {
  return api.post<RefreshTokenResult>('/auth/refresh-token', params, { requireAuth: false })
}
