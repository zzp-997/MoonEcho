import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAdminStore } from '@/stores/admin'
import router from '@/router'
import type { ApiResponse } from '@/types/api'

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const adminStore = useAdminStore()
    const token = adminStore.token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('[Request Error]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { data } = response
    if (data.success) {
      return response
    }
    // 业务错误
    const errorMessage = data.error?.message || '请求失败'
    ElMessage.error(errorMessage)
    return Promise.reject(new Error(errorMessage))
  },
  async (error: AxiosError<ApiResponse>) => {
    const { response, config } = error
    if (response) {
      const { status, data } = response
      switch (status) {
        case 401:
          // Token 过期，尝试刷新 Token
          const adminStore = useAdminStore()
          // 如果不是刷新 Token 的请求本身失败，则尝试刷新
          if (!config.url?.includes('/auth/refresh')) {
            const refreshed = await adminStore.refreshAccessToken()
            if (refreshed) {
              // 刷新成功，重新发起原请求
              const newToken = adminStore.token
              config.headers.Authorization = `Bearer ${newToken}`
              return service.request(config)
            }
          }
          // 刷新失败或刷新请求本身失败，登出用户
          ElMessage.error('登录已过期，请重新登录')
          adminStore.clearAuth()
          router.push('/login')
          break
        case 403:
          ElMessage.error('没有权限执行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data?.error?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

// 封装请求方法
export const request = {
  get<T>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, { params, ...config }).then((res) => res.data.data)
  },
  post<T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config).then((res) => res.data.data)
  },
  put<T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config).then((res) => res.data.data)
  },
  patch<T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.patch(url, data, config).then((res) => res.data.data)
  },
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config).then((res) => res.data.data)
  },
}

export default service
