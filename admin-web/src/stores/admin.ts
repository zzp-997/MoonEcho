import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, logout, getAdminInfo, refreshToken } from '@/api/auth'
import type { AdminInfo, LoginRequest } from '@/types/admin'
import router from '@/router'

// Token 过期时间存储
const TOKEN_EXPIRES_KEY = 'admin_token_expires'

export const useAdminStore = defineStore('admin', () => {
  // 状态
  const token = ref<string>(localStorage.getItem('admin_token') || '')
  const refreshTokenValue = ref<string>(localStorage.getItem('admin_refresh_token') || '')
  const tokenExpiresAt = ref<number>(parseInt(localStorage.getItem(TOKEN_EXPIRES_KEY) || '0'))
  const adminInfo = ref<AdminInfo | null>(null)
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => adminInfo.value?.username || '')
  const nickname = computed(() => adminInfo.value?.nickname || adminInfo.value?.username || '')
  const role = computed(() => adminInfo.value?.role || '')
  const permissions = computed(() => adminInfo.value?.permissions || {})

  // 检查 Token 是否过期
  function isTokenExpired(): boolean {
    if (!tokenExpiresAt.value) return true
    // 提前 5 分钟判断过期，给刷新留出时间
    return Date.now() >= tokenExpiresAt.value - 5 * 60 * 1000
  }

  // 方法
  async function loginAction(data: LoginRequest) {
    loading.value = true
    try {
      const result = await login(data)
      token.value = result.access_token
      refreshTokenValue.value = result.refresh_token
      adminInfo.value = result.admin
      // 计算 Token 过期时间
      const expiresAt = Date.now() + result.expires_in * 1000
      tokenExpiresAt.value = expiresAt
      localStorage.setItem('admin_token', result.access_token)
      localStorage.setItem('admin_refresh_token', result.refresh_token)
      localStorage.setItem(TOKEN_EXPIRES_KEY, expiresAt.toString())
      return true
    } catch (error) {
      console.error('登录失败', error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function logoutAction() {
    try {
      await logout()
    } catch (error) {
      console.error('登出失败', error)
    }
    clearAuth()
    router.push('/login')
  }

  function clearAuth() {
    token.value = ''
    refreshTokenValue.value = ''
    tokenExpiresAt.value = 0
    adminInfo.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_refresh_token')
    localStorage.removeItem(TOKEN_EXPIRES_KEY)
  }

  async function fetchAdminInfo() {
    if (!token.value) return null
    try {
      const result = await getAdminInfo()
      adminInfo.value = result
      return result
    } catch (error) {
      console.error('获取管理员信息失败', error)
      clearAuth()
      return null
    }
  }

  async function refreshAccessToken() {
    if (!refreshTokenValue.value) {
      clearAuth()
      return false
    }
    try {
      const result = await refreshToken(refreshTokenValue.value)
      token.value = result.access_token
      refreshTokenValue.value = result.refresh_token
      // 计算 Token 过期时间
      const expiresAt = Date.now() + result.expires_in * 1000
      tokenExpiresAt.value = expiresAt
      localStorage.setItem('admin_token', result.access_token)
      localStorage.setItem('admin_refresh_token', result.refresh_token)
      localStorage.setItem(TOKEN_EXPIRES_KEY, expiresAt.toString())
      return true
    } catch (error) {
      console.error('刷新 Token 失败', error)
      clearAuth()
      return false
    }
  }

  // 权限检查方法
  function hasPermission(permission: string): boolean {
    if (!adminInfo.value) return false
    // super_admin 拥有所有权限
    if (adminInfo.value.role === 'super_admin') return true
    // 解析权限字符串，如 'user:view'
    const [resource, action] = permission.split(':')
    if (!resource || !action) return false
    // 检查是否有该权限
    const resourcePermissions = adminInfo.value.permissions?.[resource] || []
    return resourcePermissions.includes(action) || resourcePermissions.includes('*')
  }

  return {
    token,
    refreshTokenValue,
    tokenExpiresAt,
    adminInfo,
    loading,
    isLoggedIn,
    username,
    nickname,
    role,
    permissions,
    isTokenExpired,
    loginAction,
    logoutAction,
    clearAuth,
    fetchAdminInfo,
    refreshAccessToken,
    hasPermission,
  }
})