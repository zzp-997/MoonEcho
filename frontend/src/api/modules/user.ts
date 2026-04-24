/**
 * 回声 - 用户接口
 * 文件：src/api/modules/user.ts
 * 说明：用户信息相关接口
 */

import api from '../index'
import type { UserInfo } from '@/types/user'

/** 获取用户信息 */
export function getUserInfo() {
  return api.get<UserInfo>('/user/info')
}

/** 更新用户信息 */
export function updateUserInfo(data: Partial<UserInfo>) {
  return api.put('/user/info', data)
}

/** 上传头像 */
export function uploadAvatar(filePath: string) {
  return api.upload<string>('/user/avatar', filePath)
}

/** 获取匿名身份列表 */
export function getAnonymousIdentities() {
  return api.get('/user/anonymous-identities')
}
