/**
 * 回声 - 认证接口
 * 文件：src/api/modules/auth.ts
 * 说明：登录、注册、验证码等认证相关接口
 */

import api from '../index'
import type { LoginParams, LoginResult, RegisterParams } from '@/types/user'

/** 发送验证码 */
export function sendVerifyCode(phone: string) {
  return api.post('/auth/send-code', { phone }, { requireAuth: false })
}

/** 验证码登录 */
export function loginWithCode(params: LoginParams) {
  return api.post<LoginResult>('/auth/login', params, { requireAuth: false })
}

/** 注册 */
export function register(params: RegisterParams) {
  return api.post<LoginResult>('/auth/register', params, { requireAuth: false })
}

/** 刷新Token */
export function refreshToken(refreshToken: string) {
  return api.post<{ token: string; refreshToken: string }>(
    '/auth/refresh',
    { refreshToken },
    { requireAuth: false }
  )
}
