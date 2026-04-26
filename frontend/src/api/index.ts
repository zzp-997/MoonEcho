/**
 * 回声 - 请求封装基类
 * 文件：src/api/index.ts
 * 说明：基于 uni.request 的统一请求封装，支持拦截器、错误码处理、Token自动刷新
 * 参考：frontend_tech.md 3.3 | tech_architecture.md 第三章
 */

import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import { ErrorCodes, getErrorMessage, isAuthError, isTeenModeError } from '@/constants/errorCodes'
import type { ApiResponse, RequestConfig } from './types'

// ==================== 配置 ====================

/** API 基础地址 */
const BASE_URL: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

/** 默认超时时间 */
const DEFAULT_TIMEOUT = 30000

/** 是否正在刷新Token */
let isRefreshing = false

/** Token刷新期间等待队列 */
let pendingRequests: Array<(token: string) => void> = []

// ==================== 工具函数 ====================

/**
 * 显示Toast提示
 */
function showToast(title: string, icon: UniApp.ShowToastOptions['icon'] = 'none') {
  uni.showToast({
    title,
    icon,
    duration: 2000,
  })
}

/**
 * 显示loading
 */
function showLoading(title = '加载中...') {
  uni.showLoading({ title, mask: true })
}

/**
 * 隐藏loading
 */
function hideLoading() {
  uni.hideLoading()
}

// ==================== Token 刷新逻辑 ====================

/**
 * 尝试刷新Token
 * @returns 新Token或null
 */
async function tryRefreshToken(): Promise<string | null> {
  if (isRefreshing) {
    // 已在刷新中，等待结果
    return new Promise((resolve) => {
      pendingRequests.push((token: string) => {
        resolve(token)
      })
    })
  }

  isRefreshing = true
  try {
    const userStore = useUserStore()
    const refreshToken = userStore.refreshTokenValue
    if (!refreshToken) {
      return null
    }

    const res = await new Promise<ApiResponse<{ token: string; refreshToken: string }>>(
      (resolve, reject) => {
        uni.request({
          url: `${BASE_URL}/auth/refresh`,
          method: 'POST',
          data: { refreshToken },
          header: { 'Content-Type': 'application/json' },
          success: (result) => resolve(result.data as ApiResponse),
          fail: (err) => reject(err),
        })
      }
    )

    if (res.success && res.data) {
      const newToken = res.data.token
      userStore.setToken(newToken, res.data.refreshToken)

      // 处理等待队列
      pendingRequests.forEach((cb) => cb(newToken))
      pendingRequests = []

      return newToken
    }

    return null
  } catch {
    return null
  } finally {
    isRefreshing = false
  }
}

/**
 * Token刷新失败处理 - 跳转登录页
 */
function handleAuthExpired() {
  const userStore = useUserStore()
  userStore.logout()
  uni.reLaunch({ url: '/pages/auth/login' })
}

// ==================== 青少年模式拦截 ====================

/**
 * 青少年模式错误处理
 * 显示提示并阻止页面渲染
 * 返回上一页或首页
 */
function handleTeenModeError() {
  uni.showModal({
    title: '提示',
    content: '青少年模式下无法使用此功能',
    showCancel: false,
    confirmText: '我知道了',
    success: () => {
      // 返回上一页或首页
      const pages = getCurrentPages()
      if (pages.length > 1) {
        uni.navigateBack()
      } else {
        uni.switchTab({ url: '/pages/home/index' })
      }
    },
  })
}

// ==================== 核心请求函数 ====================

/**
 * 统一请求封装
 * @param options 请求配置
 * @returns Promise<T>
 */
function request<T = any>(
  url: string,
  method: UniApp.RequestOptions['method'] = 'GET',
  data?: any,
  config: RequestConfig = {}
): Promise<T> {
  const {
    showLoading: showLoadingFlag = false,
    loadingText = '加载中...',
    silent = false,
    headers = {},
    timeout = DEFAULT_TIMEOUT,
    requireAuth = true,
  } = config

  // 显示loading
  if (showLoadingFlag) {
    showLoading(loadingText)
  }

  return new Promise<T>((resolve, reject) => {
    const userStore = useUserStore()
    const settingsStore = useSettingsStore()

    // 构建请求头
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    }

    // 添加认证头
    if (requireAuth && userStore.token) {
      requestHeaders['Authorization'] = `Bearer ${userStore.token}`
    }

    // 添加设备标识
    if (settingsStore.deviceId) {
      requestHeaders['X-Device-Id'] = settingsStore.deviceId
    }

    // 添加版本信息
    requestHeaders['X-App-Version'] = settingsStore.appVersion || '1.0.0'

    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: requestHeaders,
      timeout,
      success: async (res) => {
        if (showLoadingFlag) {
          hideLoading()
        }

        const statusCode = res.statusCode

        // HTTP 200 - 检查业务响应
        if (statusCode === 200) {
          const responseData = res.data as ApiResponse<T>
          if (responseData.success) {
            resolve(responseData.data as T)
          } else {
            // 业务错误处理
            const errorCode = responseData.error?.code || 'UNKNOWN'
            const errorMessage = responseData.error?.message

            if (!silent) {
              // 青少年模式拦截
              if (isTeenModeError(errorCode)) {
                handleTeenModeError()
              } else if (isAuthError(errorCode)) {
                // 认证错误处理
                const newToken = await tryRefreshToken()
                if (newToken) {
                  // Token刷新成功，重试原始请求
                  requestHeaders['Authorization'] = `Bearer ${newToken}`
                  try {
                    const retryResult = await new Promise<T>((retryResolve, retryReject) => {
                      uni.request({
                        url: `${BASE_URL}${url}`,
                        method,
                        data,
                        header: requestHeaders,
                        timeout,
                        success: (retryRes) => {
                          const retryData = retryRes.data as ApiResponse<T>
                          if (retryData.success) {
                            retryResolve(retryData.data as T)
                          } else {
                            retryReject(new Error(retryData.error?.message || '请求失败'))
                          }
                        },
                        fail: retryReject,
                      })
                    })
                    resolve(retryResult)
                  } catch (retryErr) {
                    handleAuthExpired()
                    reject(retryErr)
                  }
                } else {
                  handleAuthExpired()
                  reject(new Error(getErrorMessage(errorCode)))
                }
              } else {
                // 普通业务错误 - 显示Toast
                showToast(getErrorMessage(errorCode, errorMessage))
              }
            }

            reject(new Error(errorMessage || getErrorMessage(errorCode)))
          }
        } else if (statusCode === 401) {
          // HTTP 401 - Token失效
          if (!silent) {
            const newToken = await tryRefreshToken()
            if (newToken) {
              requestHeaders['Authorization'] = `Bearer ${newToken}`
              try {
                const retryResult = await new Promise<T>((retryResolve, retryReject) => {
                  uni.request({
                    url: `${BASE_URL}${url}`,
                    method,
                    data,
                    header: requestHeaders,
                    timeout,
                    success: (retryRes) => {
                      const retryData = retryRes.data as ApiResponse<T>
                      if (retryData.success) {
                        retryResolve(retryData.data as T)
                      } else {
                        retryReject(new Error(retryData.error?.message || '请求失败'))
                      }
                    },
                    fail: retryReject,
                  })
                })
                resolve(retryResult)
              } catch {
                handleAuthExpired()
                reject(new Error('请先登录'))
              }
            } else {
              handleAuthExpired()
              reject(new Error('请先登录'))
            }
          }
        } else if (statusCode === 403) {
          if (!silent) {
            showToast('无权访问此内容')
          }
          reject(new Error('无权访问'))
        } else if (statusCode === 404) {
          if (!silent) {
            showToast('请求的资源不存在')
          }
          reject(new Error('资源不存在'))
        } else if (statusCode === 429) {
          if (!silent) {
            showToast('请求频率过高，请稍后再试')
          }
          reject(new Error('请求频率过高'))
        } else if (statusCode >= 500) {
          if (!silent) {
            showToast('服务开小差了，请稍后重试')
          }
          reject(new Error('服务器错误'))
        } else {
          if (!silent) {
            showToast(`请求失败（${statusCode}）`)
          }
          reject(new Error(`请求失败: ${statusCode}`))
        }
      },
      fail: (err) => {
        if (showLoadingFlag) {
          hideLoading()
        }
        if (!silent) {
          showToast('网络请求失败')
        }
        reject(err)
      },
    })
  })
}

// ==================== 快捷方法 ====================

export const api = {
  /** GET 请求 */
  get<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return request<T>(url, 'GET', data, config)
  },

  /** POST 请求 */
  post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return request<T>(url, 'POST', data, config)
  },

  /** PUT 请求 */
  put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return request<T>(url, 'PUT', data, config)
  },

  /** PATCH 请求 */
  patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return request<T>(url, 'PATCH', data, config)
  },

  /** DELETE 请求 */
  delete<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return request<T>(url, 'DELETE', data, config)
  },

  /** 上传文件 */
  upload<T = any>(url: string, filePath: string, name = 'file', formData?: Record<string, any>): Promise<T> {
    return new Promise((resolve, reject) => {
      const userStore = useUserStore()

      uni.uploadFile({
        url: `${BASE_URL}${url}`,
        filePath,
        name,
        formData,
        header: {
          'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
        },
        success: (res) => {
          if (res.statusCode === 200) {
            const data = JSON.parse(res.data) as ApiResponse<T>
            if (data.success) {
              resolve(data.data as T)
            } else {
              showToast(getErrorMessage(data.error?.code || 'UNKNOWN', data.error?.message))
              reject(new Error(data.error?.message))
            }
          } else {
            showToast('上传失败')
            reject(new Error('上传失败'))
          }
        },
        fail: (err) => {
          showToast('网络请求失败')
          reject(err)
        },
      })
    })
  },
}

export default api
