/**
 * 回声 - 认证组合式函数
 * 文件：src/composables/useAuth.ts
 * 说明：登录、注册、Token管理等认证相关逻辑
 * 适配后端接口（T005）：
 *   POST /api/v1/auth/send-code       # 发送验证码
 *   POST /api/v1/auth/verify-code     # 验证码登录/注册（返回 is_new_user）
 *   POST /api/v1/auth/complete-profile # 完善资料（昵称+年龄段）
 *   POST /api/v1/auth/refresh-token   # 刷新token
 */

import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import api from '@/api'
import { getErrorMessage } from '@/constants/errorCodes'
import { track, EventName } from '@/utils/tracking'

/** 验证码登录响应类型 */
interface VerifyCodeResponse {
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

/** 完善资料响应类型 */
interface CompleteProfileResponse {
  id: string
  phone: string
  nickname: string
  avatarUrl?: string
  ageRange: string
  is_minor: boolean
}

export function useAuth() {
  const userStore = useUserStore()
  const settingsStore = useSettingsStore()

  const isLoading = ref(false)
  const errorMessage = ref('')

  /**
   * 发送验证码
   * @param phone 手机号
   * @returns 是否发送成功
   */
  async function sendVerifyCode(phone: string): Promise<boolean> {
    isLoading.value = true
    errorMessage.value = ''

    try {
      await api.post('/auth/send-code', { phone }, { requireAuth: false })
      return true
    } catch (error: any) {
      errorMessage.value = error.message || '验证码发送失败'
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 验证码登录/注册
   * @param phone 手机号
   * @param code 验证码
   * @returns 返回 { success, isNewUser } 表示是否为新用户
   */
  async function verifyCodeLogin(phone: string, code: string): Promise<{ success: boolean; isNewUser: boolean }> {
    isLoading.value = true
    errorMessage.value = ''

    try {
      const data = await api.post<VerifyCodeResponse>('/auth/verify-code', { phone, code }, { requireAuth: false })

      // 保存 Token
      userStore.setToken(data.token, data.refreshToken)

      // 保存用户基本信息
      userStore.setUserInfo({
        id: data.user.id,
        phone: data.user.phone,
        nickname: data.user.nickname || '',
        avatarUrl: data.user.avatarUrl,
        ageRange: data.user.ageRange,
        is_minor: data.user.is_minor,
      })

      // 追踪登录事件
      if (data.is_new_user) {
        track(EventName.USER_REGISTER, { method: 'phone_code' })
      } else {
        track(EventName.USER_LOGIN, { method: 'phone_code' })
      }

      return { success: true, isNewUser: data.is_new_user }
    } catch (error: any) {
      errorMessage.value = error.message || '验证失败'
      return { success: false, isNewUser: false }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 完善个人资料
   * @param nickname 昵称
   * @param ageRange 年龄段
   * @returns 是否成功
   */
  async function completeProfile(nickname: string, ageRange: string): Promise<boolean> {
    isLoading.value = true
    errorMessage.value = ''

    try {
      const data = await api.post<CompleteProfileResponse>('/auth/complete-profile', { nickname, ageRange }, { requireAuth: true })

      // 更新用户信息
      userStore.updateUserInfo({
        nickname: data.nickname,
        ageRange: data.ageRange,
        is_minor: data.is_minor,
      })

      // 追踪注册完成事件
      track(EventName.USER_REGISTER, { method: 'complete_profile', has_nickname: true })

      return true
    } catch (error: any) {
      errorMessage.value = error.message || '保存失败'
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
   * @param redirect 是否跳转登录页
   * @returns 是否已登录
   */
  function checkAuth(redirect = true): boolean {
    if (!userStore.isLoggedIn) {
      if (redirect) {
        uni.navigateTo({ url: '/pages/auth/login' })
      }
      return false
    }
    return true
  }

  /**
   * 跳转到登录页
   */
  function goToLogin() {
    uni.navigateTo({ url: '/pages/auth/login' })
  }

  /**
   * 跳转到完善资料页
   */
  function goToProfile() {
    uni.navigateTo({ url: '/pages/auth/profile' })
  }

  /**
   * 跳转到首页
   */
  function goToHome() {
    uni.switchTab({ url: '/pages/chat/index' })
  }

  return {
    isLoading,
    errorMessage,
    sendVerifyCode,
    verifyCodeLogin,
    completeProfile,
    logout,
    checkAuth,
    goToLogin,
    goToProfile,
    goToHome,
  }
}
