/**
 * 回声 - 用户状态管理
 * 文件：src/stores/user.ts
 * 说明：用户登录状态、Token管理、用户信息存储
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 用户信息接口 */
export interface UserInfo {
  id: string
  phone: string
  nickname: string
  avatarUrl?: string
  ageRange?: string
  city?: string
  occupation?: string
  createdAt?: string
}

/** Token 存储键 */
const TOKEN_KEY = 'huisheng_token'
const REFRESH_TOKEN_KEY = 'huisheng_refresh_token'
const USER_INFO_KEY = 'huisheng_user_info'

export const useUserStore = defineStore('user', () => {
  // ==================== 状态 ====================

  /** Token */
  const token = ref<string | null>(null)
  /** 刷新Token */
  const refreshTokenValue = ref<string | null>(null)
  /** 用户信息 */
  const userInfo = ref<UserInfo | null>(null)

  // ==================== 计算属性 ====================

  /** 是否已登录 */
  const isLoggedIn = computed(() => !!token.value)

  /** 用户昵称（优先用户设置，否则显示默认） */
  const displayName = computed(() => userInfo.value?.nickname || '用户')

  /** 手机号脱敏显示 */
  const maskedPhone = computed(() => {
    const phone = userInfo.value?.phone
    if (!phone) return ''
    return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
  })

  // ==================== 方法 ====================

  /**
   * 初始化用户状态（从本地存储恢复）
   */
  function init() {
    try {
      const savedToken = uni.getStorageSync(TOKEN_KEY)
      const savedRefreshToken = uni.getStorageSync(REFRESH_TOKEN_KEY)
      const savedUserInfo = uni.getStorageSync(USER_INFO_KEY)

      if (savedToken) {
        token.value = savedToken
      }
      if (savedRefreshToken) {
        refreshTokenValue.value = savedRefreshToken
      }
      if (savedUserInfo) {
        userInfo.value = JSON.parse(savedUserInfo)
      }
    } catch (e) {
      console.error('初始化用户状态失败', e)
    }
  }

  /**
   * 设置Token
   */
  function setToken(newToken: string, newRefreshToken?: string) {
    token.value = newToken
    uni.setStorageSync(TOKEN_KEY, newToken)

    if (newRefreshToken) {
      refreshTokenValue.value = newRefreshToken
      uni.setStorageSync(REFRESH_TOKEN_KEY, newRefreshToken)
    }
  }

  /**
   * 设置用户信息
   */
  function setUserInfo(info: UserInfo) {
    userInfo.value = info
    uni.setStorageSync(USER_INFO_KEY, JSON.stringify(info))
  }

  /**
   * 更新用户信息（部分更新）
   */
  function updateUserInfo(info: Partial<UserInfo>) {
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, ...info }
      uni.setStorageSync(USER_INFO_KEY, JSON.stringify(userInfo.value))
    }
  }

  /**
   * 清除Token
   */
  function clearToken() {
    token.value = null
    refreshTokenValue.value = null
    uni.removeStorageSync(TOKEN_KEY)
    uni.removeStorageSync(REFRESH_TOKEN_KEY)
  }

  /**
   * 登出
   */
  function logout() {
    clearToken()
    userInfo.value = null
    uni.removeStorageSync(USER_INFO_KEY)
  }

  /**
   * 刷新Token
   * @returns 是否刷新成功
   */
  async function refreshToken(): Promise<boolean> {
    // 实际刷新逻辑在 api/index.ts 中实现
    // 这里仅作为接口暴露
    return false
  }

  // ==================== 初始化 ====================

  init()

  return {
    // 状态
    token,
    refreshTokenValue,
    userInfo,
    // 计算属性
    isLoggedIn,
    displayName,
    maskedPhone,
    // 方法
    setToken,
    setUserInfo,
    updateUserInfo,
    clearToken,
    logout,
    refreshToken,
    init,
  }
})
