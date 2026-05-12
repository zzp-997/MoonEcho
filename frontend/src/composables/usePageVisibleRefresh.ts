/**
 * 回声 - 页面可见性刷新 Hook
 * 文件：src/composables/usePageVisibleRefresh.ts
 * 说明：替代 onShow/onHide，H5 模式下避免标签页切换时重复刷新
 *
 * H5 模式：用 visibilitychange 事件 + 隐藏时间阈值判断
 *   - 页面隐藏超过阈值再恢复时，触发 onVisible
 *   - 短时间切换标签页不触发
 * 非 H5 模式：直接映射到 uni-app 的 onShow/onHide
 */

import { onMounted, onUnmounted } from 'vue'
// #ifndef H5
import { onShow, onHide } from '@dcloudio/uni-app'
// #endif

/** 默认隐藏时间阈值（毫秒），超过此时间才视为"从后台恢复" */
const DEFAULT_THRESHOLD = 30000

/**
 * 页面可见性刷新 Hook
 * @param options.onVisible 页面变为可见时的回调（替代 onShow 中的数据加载逻辑）
 * @param options.onHidden 页面变为不可见时的回调（替代 onHide 中的清理逻辑）
 * @param options.threshold 隐藏时间阈值（毫秒），默认 30000（30秒）
 */
export function usePageVisibleRefresh(options: {
  onVisible?: () => void
  onHidden?: () => void
  threshold?: number
}) {
  const { onVisible, onHidden, threshold = DEFAULT_THRESHOLD } = options

  // #ifdef H5
  let hiddenTime = 0

  function handleVisibilityChange() {
    if (document.hidden) {
      hiddenTime = Date.now()
    } else {
      // 隐藏超过阈值才视为"从后台恢复"，触发清理+刷新
      // 短时间切换标签页不触发，避免无意义的接口请求
      if (hiddenTime > 0 && Date.now() - hiddenTime > threshold) {
        onHidden?.()
        onVisible?.()
      }
    }
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
  })

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })
  // #endif

  // #ifndef H5
  onShow(() => {
    onVisible?.()
  })

  onHide(() => {
    onHidden?.()
  })
  // #endif
}
