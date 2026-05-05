/**
 * 回声 - 认证组合式函数
 * 文件：src/composables/useAuth.ts
 * 说明：登录、注册、Token管理、路由守卫等认证相关逻辑
 * 功能增强（T016）：
 *   - JWT 登录状态管理（token 刷新、过期自动跳转登录页）
 *   - 未登录不可访问需认证页面
 *   - 首次打开 vs 二次打开区分（注册后第2次打开展示性格选择页）
 */

import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import api from '@/api'
import { getErrorMessage } from '@/constants/errorCodes'
import { track, EventName } from '@/utils/tracking'
import { getStorage, setStorage, removeStorage } from '@/utils/storage'

// ==================== 常量 ====================

/** APP 打开次数存储键 */
const APP_OPEN_COUNT_KEY = 'huisheng_app_open_count'

/** 性格选择页已展示标记存储键 */
const PERSONALITY_SHOWN_KEY = 'huisheng_personality_shown'

/** 首次注册完成标记存储键 */
const FIRST_REGISTER_COMPLETE_KEY = 'huisheng_first_register_complete'

/** 需要认证的页面路径列表 */
const AUTH_REQUIRED_PAGES = [
  '/pages/chat/index',
  '/pages/diary/index',
  '/pages/diary/edit',
  '/pages/diary/weekly-report',
  '/pages/treehole/index',
  '/pages/community/index',
  '/pages/mine/index',
  '/pages/home/index',
  '/pages/notification/list',
  '/pages/notification/settings',
  '/pages/message/index',
]

/** 公开页面（无需登录） */
const PUBLIC_PAGES = [
  '/pages/auth/login',
  '/pages/auth/profile',
  '/pages/auth/ai-greeting',
  '/pages/auth/minor-notice',
  '/pages/auth/minor-lock',
  '/pages/index/index',
]

// ==================== 类型定义 ====================

/** 验证码登录响应类型（与后端 VerifyCodeResponse 对齐） */
interface VerifyCodeResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  is_new_user: boolean
  profile_completed: boolean
}

/** 完善资料响应类型（与后端 CompleteProfileResponse 对齐） */
interface CompleteProfileResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

/** 路由守卫选项 */
interface RouteGuardOptions {
  /** 是否跳转登录页 */
  redirectToLogin?: boolean
  /** 是否检查性格选择 */
  checkPersonality?: boolean
}

// ==================== 响应式状态 ====================

/** 是否正在加载 */
const isLoading = ref(false)

/** 错误消息 */
const errorMessage = ref('')

/** App 打开次数 */
const appOpenCount = ref(0)

/** 是否首次注册完成 */
const isFirstRegisterComplete = ref(false)

/** 性格选择页是否已展示 */
const isPersonalityShown = ref(false)

// ==================== 组合式函数 ====================

export function useAuth() {
  const userStore = useUserStore()
  const settingsStore = useSettingsStore()

  // ==================== 计算属性 ====================

  /** 是否已登录 */
  const isLoggedIn = computed(() => userStore.isLoggedIn)

  /** 是否为新用户（首次注册后） */
  const isNewUser = computed(() => {
    return isFirstRegisterComplete.value && !isPersonalityShown.value
  })

  /** 是否需要展示性格选择页 */
  const needShowPersonality = computed(() => {
    // 注册后第2次打开 APP 时展示
    if (!isFirstRegisterComplete.value) return false
    if (isPersonalityShown.value) return false
    return appOpenCount.value === 2
  })

  // ==================== 初始化方法 ====================

  /**
   * 初始化认证状态
   * 在 App.vue onLaunch 中调用
   */
  function initAuth(): void {
    // 恢复用户状态
    userStore.init()

    // 读取 APP 打开次数
    appOpenCount.value = getStorage<number>(APP_OPEN_COUNT_KEY, 0) || 0

    // 读取首次注册标记
    isFirstRegisterComplete.value = getStorage<boolean>(FIRST_REGISTER_COMPLETE_KEY, false) || false

    // 读取性格选择页展示标记
    isPersonalityShown.value = getStorage<boolean>(PERSONALITY_SHOWN_KEY, false) || false

    // 检查 Token 是否过期
    if (userStore.token) {
      checkTokenExpiry()
    }
  }

  /**
   * 检查 Token 是否过期
   */
  function checkTokenExpiry(): void {
    try {
      const token = userStore.token
      if (!token) return

      // JWT Token 解析（简单解析 payload）
      const payload = parseJwtPayload(token)
      if (!payload) return

      const now = Math.floor(Date.now() / 1000)
      const exp = payload.exp

      // Token 已过期
      if (exp && now >= exp) {
        handleTokenExpired()
      }
    } catch (error) {
      console.error('检查 Token 过期失败', error)
    }
  }

  /**
   * 解析 JWT Payload（使用模块级函数）
   */
  function parseJwtPayload(token: string): Record<string, unknown> | null {
    return parseJwtPayloadSimple(token)
  }

  /**
   * 处理 Token 过期
   */
  async function handleTokenExpired(): Promise<void> {
    const refreshToken = userStore.refreshTokenValue

    if (refreshToken) {
      // 尝试刷新 Token
      const success = await refreshAccessToken()
      if (!success) {
        // 刷新失败，跳转登录页
        goToLogin()
      }
    } else {
      // 没有 refreshToken，跳转登录页
      goToLogin()
    }
  }

  /**
   * 刷新 Access Token
   */
  async function refreshAccessToken(): Promise<boolean> {
    try {
      const refreshToken = userStore.refreshTokenValue
      if (!refreshToken) return false

      const data = await api.post<{ access_token: string; refresh_token: string }>(
        '/auth/refresh-token',
        { refresh_token: refreshToken },
        { requireAuth: false, silent: true }
      )

      userStore.setToken(data.access_token, data.refresh_token)
      return true
    } catch (error) {
      console.error('刷新 Token 失败', error)
      return false
    }
  }

  // ==================== 登录相关方法 ====================

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
   * @returns 返回 { success, isNewUser, profileCompleted } 表示是否为新用户及资料是否完善
   */
  async function verifyCodeLogin(phone: string, code: string): Promise<{ success: boolean; isNewUser: boolean; profileCompleted: boolean }> {
    isLoading.value = true
    errorMessage.value = ''

    try {
      const data = await api.post<VerifyCodeResponse>('/auth/verify-code', { phone, code }, { requireAuth: false })

      // 保存 Token（后端返回 access_token / refresh_token）
      userStore.setToken(data.access_token, data.refresh_token)

      // 验证码登录后获取用户信息（后端 verify-code 不返回 user 对象）
      try {
        const userInfo = await api.get<{ id: string; phone: string; nickname: string | null; avatar_url: string | null; age_range: string | null; is_minor: boolean }>('/auth/me', {}, { requireAuth: true })
        userStore.setUserInfo({
          id: userInfo.id,
          phone: userInfo.phone,
          nickname: userInfo.nickname || '',
          avatarUrl: userInfo.avatar_url,
          ageRange: userInfo.age_range,
          is_minor: userInfo.is_minor,
        })
      } catch {
        // 获取用户信息失败不影响登录流程
      }

      // 追踪登录事件
      if (data.is_new_user) {
        track(EventName.USER_REGISTER, { method: 'phone_code' })
        // 标记首次注册完成
        setStorage(FIRST_REGISTER_COMPLETE_KEY, true)
        isFirstRegisterComplete.value = true
      } else {
        track(EventName.USER_LOGIN, { method: 'phone_code' })
      }

      return { success: true, isNewUser: data.is_new_user, profileCompleted: data.profile_completed }
    } catch (error: any) {
      errorMessage.value = error.message || '验证失败'
      return { success: false, isNewUser: false, profileCompleted: false }
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
      const data = await api.post<CompleteProfileResponse>('/auth/complete-profile', { nickname, age_range: ageRange }, { requireAuth: true })

      // 更新 Token（完善资料后后端重新签发）
      userStore.setToken(data.access_token, data.refresh_token)

      // 重新获取用户信息
      try {
        const userInfo = await api.get<{ id: string; phone: string; nickname: string | null; avatar_url: string | null; age_range: string | null; is_minor: boolean }>('/auth/me', {}, { requireAuth: true })
        userStore.updateUserInfo({
          nickname: userInfo.nickname || '',
          ageRange: userInfo.age_range,
          is_minor: userInfo.is_minor,
        })
      } catch {
        // 获取用户信息失败不影响流程
      }

      // 追踪注册完成事件
      track(EventName.USER_REGISTER, { method: 'complete_profile', has_nickname: true })

      // 标记首次注册完成
      setStorage(FIRST_REGISTER_COMPLETE_KEY, true)
      isFirstRegisterComplete.value = true

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
  function logout(): void {
    track(EventName.USER_LOGOUT)

    // 清除用户状态
    userStore.logout()

    // 清除首次注册标记
    removeStorage(FIRST_REGISTER_COMPLETE_KEY)
    isFirstRegisterComplete.value = false

    // 重置打开次数
    removeStorage(APP_OPEN_COUNT_KEY)
    appOpenCount.value = 0

    // 跳转登录页
    uni.reLaunch({ url: '/pages/auth/login' })
  }

  // ==================== 路由守卫方法 ====================

  /**
   * 检查登录状态
   * @param redirect 是否跳转登录页
   * @returns 是否已登录
   */
  function checkAuth(redirect = true): boolean {
    if (!userStore.isLoggedIn) {
      if (redirect) {
        goToLogin()
      }
      return false
    }
    return true
  }

  /**
   * 页面访问守卫
   * 在页面 onShow 中调用，检查登录状态和路由权限
   * @param pagePath 当前页面路径
   * @param options 守卫选项
   * @returns 是否允许访问
   */
  function pageGuard(pagePath: string, options: RouteGuardOptions = {}): boolean {
    const { redirectToLogin = true, checkPersonality = true } = options

    // 检查是否为公开页面
    if (PUBLIC_PAGES.some(p => pagePath.includes(p))) {
      return true
    }

    // 检查是否需要认证
    const needAuth = AUTH_REQUIRED_PAGES.some(p => pagePath.includes(p))

    if (needAuth && !userStore.isLoggedIn) {
      if (redirectToLogin) {
        goToLogin()
      }
      return false
    }

    // 检查是否需要展示性格选择页
    if (checkPersonality && needShowPersonality.value) {
      uni.redirectTo({ url: '/pages/chat/personality' })
      return false
    }

    return true
  }

  /**
   * 增加 APP 打开次数
   */
  function incrementAppOpenCount(): void {
    appOpenCount.value++
    setStorage(APP_OPEN_COUNT_KEY, appOpenCount.value)
  }

  /**
   * 标记性格选择页已展示
   */
  function markPersonalityShown(): void {
    isPersonalityShown.value = true
    setStorage(PERSONALITY_SHOWN_KEY, true)
  }

  // ==================== 导航方法 ====================

  /**
   * 跳转到登录页
   */
  function goToLogin(): void {
    uni.reLaunch({ url: '/pages/auth/login' })
  }

  /**
   * 跳转到完善资料页
   */
  function goToProfile(): void {
    uni.navigateTo({ url: '/pages/auth/profile' })
  }

  /**
   * 跳转到首页
   */
  function goToHome(): void {
    uni.switchTab({ url: '/pages/home/index' })
  }

  /**
   * 跳转到性格选择页
   */
  function goToPersonality(): void {
    uni.navigateTo({ url: '/pages/chat/personality' })
  }

  return {
    // 状态
    isLoading,
    errorMessage,
    isLoggedIn,
    isNewUser,
    needShowPersonality,
    appOpenCount,

    // 初始化方法
    initAuth,
    checkTokenExpiry,
    refreshAccessToken,

    // 登录相关
    sendVerifyCode,
    verifyCodeLogin,
    completeProfile,
    logout,

    // 路由守卫
    checkAuth,
    pageGuard,
    incrementAppOpenCount,
    markPersonalityShown,

    // 导航方法
    goToLogin,
    goToProfile,
    goToHome,
    goToPersonality,
  }
}

// ==================== 导出单例方法（用于非组件中使用） ====================

/**
 * 全局路由守卫
 * 在 App.vue 的 onShow 中调用
 */
export function globalAuthGuard(): void {
  const userStore = useUserStore()

  // 如果未登录，不做处理（由页面级守卫处理）
  if (!userStore.isLoggedIn) return

  // 检查 Token 过期
  const token = userStore.token
  if (token) {
    try {
      const payload = parseJwtPayloadSimple(token)
      if (payload?.exp) {
        const now = Math.floor(Date.now() / 1000)
        if (now >= payload.exp) {
          // Token 已过期，尝试刷新
          const settingsStore = useSettingsStore()
          // 这里不直接刷新，交给请求拦截器处理
        }
      }
    } catch (error) {
      console.error('全局守卫检查失败', error)
    }
  }
}

/**
 * 解析 JWT Payload（可在模块级别使用）
 */
function parseJwtPayloadSimple(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split('.')[1]
    if (!base64Url) return null

    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )

    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}
