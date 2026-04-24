/**
 * 回声 - 认证组合式函数
 * 文件：src/composables/useAuth.ts
 * 说明：登录、注册、Token管理等认证相关逻辑
 */

import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import api from '@/api'
import { ErrorCodes, isTeenModeError } from '@/constants/errorCodes'
import { track, EventName } from '@/utils/tracking'

export function useAuth() {
  const userStore = useUserStore()
  const settingsStore = useSettingsStore()

  const isLoading = ref(false)
  const errorMessage = ref('')

  /**
   * 发送验证码
   */
  async function sendVerifyCode(phone: string): Promise<boolean> {
    isLoading.value = true
    errorMessage.value = ''

    try {
      await api.post('/auth/send-code', { phone }, { requireAuth: false })
      return true
    } catch (error: any) {
      errorMessage.value = error.message || '验证码发送失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 验证码登录
   */
  async function loginWithCode(phone: string, code: string): Promise<boolean> {
    isLoading.value = true
    errorMessage.value = ''

    try {
      const data = await api.post<{
        token: string
        refreshToken: string
        user: any
      }>('/auth/login', { phone, code }, { requireAuth: false })

      // 保存 Token 和用户信息
      userStore.setToken(data.token, data.refreshToken)
      userStore.setUserInfo(data.user)

      // 追踪登录事件
      track(EventName.USER_LOGIN, { method: 'phone_code' })

      return true
    } catch (error: any) {
      errorMessage.value = error.message || '登录失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 登出
   */
  function logout() {
    track(EventName.USER_LOGOUT)
    userStore.logout()
    uni.reLaunch({ url: '/pages/auth/login' })
  }

  /**
   * 检查登录状态
   */
  function checkAuth(): boolean {
    if (!userStore.isLoggedIn) {
      uni.navigateTo({ url: '/pages/auth/login' })
      return false
    }
    return true
  }

  return {
    isLoading,
    errorMessage,
    sendVerifyCode,
    loginWithCode,
    logout,
    checkAuth,
  }
}
