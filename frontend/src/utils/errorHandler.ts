/**
 * 回声 - 全局错误处理
 * 文件：src/utils/errorHandler.ts
 * 说明：全局错误捕获、业务错误处理、网络异常处理
 * 参考：frontend_tech.md 8.10
 */

import { ErrorCodes, getErrorMessage, isAuthError } from '@/constants/errorCodes'

/**
 * 显示Toast提示
 */
function showToast(title: string) {
  uni.showToast({
    title,
    icon: 'none',
    duration: 2000,
  })
}

/**
 * 初始化全局错误处理
 * 在 main.ts 中调用
 */
export function setupGlobalErrorHandler() {
  // Vue 全局错误处理通过 app.config.errorHandler 设置
  // 在 main.ts 中配置
}

/**
 * 统一 HTTP 错误处理
 * 在 api/index.ts 的请求拦截器中调用
 */
export function handleHttpError(statusCode: number, errorData?: any): void {
  switch (statusCode) {
    case 400:
      showToast(errorData?.message || '请求参数错误')
      break
    case 401:
      handleUnauthorized()
      break
    case 403:
      showToast('无权访问此内容')
      break
    case 404:
      showToast('请求的资源不存在')
      break
    case 429:
      showToast('请求频率过高，请稍后再试')
      break
    case 500:
    case 502:
    case 503:
      showToast('服务开小差了，请稍后重试')
      break
    default:
      showToast(`请求失败（${statusCode}）`)
  }
}

/**
 * 统一业务错误处理
 */
export function handleBusinessError(code: string, message?: string): void {
  const displayMessage = getErrorMessage(code, message)
  showToast(displayMessage)

  // 特殊错误码的额外处理
  if (isAuthError(code)) {
    handleUnauthorized()
  }
}

/**
 * 处理401未授权
 * 跳转登录页
 */
async function handleUnauthorized() {
  // Token刷新逻辑在 api/index.ts 中实现
  // 刷新失败则跳转登录页
  const { useUserStore } = await import('@/stores/user')
  const userStore = useUserStore()
  userStore.logout()
  uni.reLaunch({ url: '/pages/auth/login' })
}

/**
 * 上报错误到监控服务
 */
function reportError(errorInfo: {
  type: string
  message: string
  stack?: string | undefined
  component?: string
  info?: string
}) {
  // TODO: 接入错误监控服务
  console.error('[Error Report]', errorInfo)
}

/**
 * 显示网络断开提示条
 */
function showNetworkOfflineBar() {
  // 通过全局状态控制网络断开提示条的显示
  console.warn('[Network] 网络已断开')
}

/**
 * 隐藏网络断开提示条
 */
function hideNetworkOfflineBar() {
  console.log('[Network] 网络已恢复')
}
