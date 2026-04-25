/**
 * 回声 - 验证码倒计时组合式函数
 * 文件：src/composables/useCountdown.ts
 * 说明：60秒验证码倒计时，支持开始/停止/重置
 */

import { ref, computed, onUnmounted } from 'vue'

/** 倒计时默认时长（秒） */
const DEFAULT_DURATION = 60

/** 倒计时间隔（毫秒） */
const INTERVAL_MS = 1000

export function useCountdown(duration = DEFAULT_DURATION) {
  /** 剩余秒数 */
  const remaining = ref(0)

  /** 定时器 ID */
  let timer: ReturnType<typeof setInterval> | null = null

  /** 是否正在倒计时 */
  const isCounting = computed(() => remaining.value > 0)

  /** 按钮文案 */
  const buttonText = computed(() => {
    if (isCounting.value) {
      return `重新获取(${remaining.value}s)`
    }
    if (remaining.value === 0 && timer !== null) {
      // 倒计时刚结束
      return '重新获取'
    }
    return '获取验证码'
  })

  /** 是否刚完成倒计时（用于区分"重新获取"文案） */
  const hasCounted = ref(false)

  /** 完整按钮文案（包含"重新获取"逻辑） */
  const displayText = computed(() => {
    if (isCounting.value) {
      return `重新获取(${remaining.value}s)`
    }
    if (hasCounted.value) {
      return '重新获取'
    }
    return '获取验证码'
  })

  /**
   * 开始倒计时
   */
  function start() {
    stop()
    remaining.value = duration
    hasCounted.value = true

    timer = setInterval(() => {
      remaining.value--
      if (remaining.value <= 0) {
        remaining.value = 0
        stop()
      }
    }, INTERVAL_MS)
  }

  /**
   * 停止倒计时
   */
  function stop() {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  /**
   * 重置倒计时（清除状态，文案回到"获取验证码"）
   */
  function reset() {
    stop()
    remaining.value = 0
    hasCounted.value = false
  }

  // 组件卸载时清除定时器
  onUnmounted(() => {
    stop()
  })

  return {
    remaining,
    isCounting,
    displayText,
    hasCounted,
    start,
    stop,
    reset,
  }
}
