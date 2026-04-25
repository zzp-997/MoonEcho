/**
 * 回声 - 青少年模式使用时长追踪组合式函数
 * 文件：src/composables/useMinorTimer.ts
 * 说明：追踪青少年用户的使用时长，提供以下功能：
 *   1. 追踪每日使用时长并持久化到本地存储
 *   2. 使用1小时后弹窗提醒
 *   3. 21:55 弹窗提醒准备休息
 *   4. 22:00 后显示锁定页
 *   5. App 切前后台时暂停/恢复计时
 * 使用方式：在 App.vue 或入口页面中调用 useMinorTimer() 初始化
 */

import { ref, computed, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'

// ==================== 常量 ====================

/** 存储键前缀 */
const STORAGE_KEY_PREFIX = 'huisheng_minor_usage_'

/** 1小时提醒阈值（毫秒） */
const ONE_HOUR_MS = 60 * 60 * 1000

/** 21:55 提醒时间 */
const WARNING_HOUR = 21
const WARNING_MINUTE = 55

/** 22:00 锁定时间 */
const LOCK_HOUR = 22

/** 05:00 解锁时间 */
const UNLOCK_HOUR = 5

/** 计时检查间隔（毫秒） */
const TIMER_INTERVAL = 30000 // 30秒检查一次

/** 提醒标记存储键 */
const ONE_HOUR_WARNING_KEY = 'huisheng_minor_one_hour_warned_'

/** 夜间提醒标记存储键 */
const NIGHT_WARNING_KEY = 'huisheng_minor_night_warned_'

// ==================== 响应式状态 ====================

/** 今日累计使用时长（毫秒） */
const todayUsage = ref(0)

/** 是否正在计时 */
const isTracking = ref(false)

/** 定时器引用 */
let trackingTimer: ReturnType<typeof setInterval> | null = null

/** 上次活跃时间戳 */
let lastActiveTimestamp: number = 0

/** 是否已弹出1小时提醒 */
let hasOneHourWarningShown = false

/** 是否已弹出夜间提醒 */
let hasNightWarningShown = false

// ==================== 工具函数 ====================

/**
 * 获取今日日期字符串
 */
function getTodayDate(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 获取今日使用时长的存储键
 */
function getStorageKey(): string {
  return `${STORAGE_KEY_PREFIX}${getTodayDate()}`
}

/**
 * 获取1小时提醒标记的存储键
 */
function getOneHourWarningKey(): string {
  return `${ONE_HOUR_WARNING_KEY}${getTodayDate()}`
}

/**
 * 获取夜间提醒标记的存储键
 */
function getNightWarningKey(): string {
  return `${NIGHT_WARNING_KEY}${getTodayDate()}`
}

/**
 * 从本地存储恢复今日使用时长
 */
function restoreTodayUsage(): number {
  try {
    const saved = uni.getStorageSync(getStorageKey())
    if (saved) {
      return parseInt(saved, 10) || 0
    }
  } catch (e) {
    console.error('恢复青少年使用时长失败', e)
  }
  return 0
}

/**
 * 持久化今日使用时长到本地存储
 */
function persistTodayUsage(usage: number): void {
  try {
    uni.setStorageSync(getStorageKey(), String(usage))
  } catch (e) {
    console.error('持久化青少年使用时长失败', e)
  }
}

/**
 * 检查是否已弹出1小时提醒
 */
function checkOneHourWarning(): boolean {
  try {
    return uni.getStorageSync(getOneHourWarningKey()) === 'true'
  } catch {
    return false
  }
}

/**
 * 标记1小时提醒已弹出
 */
function markOneHourWarning(): void {
  try {
    uni.setStorageSync(getOneHourWarningKey(), 'true')
  } catch {
    // 静默处理
  }
}

/**
 * 检查是否已弹出夜间提醒
 */
function checkNightWarning(): boolean {
  try {
    return uni.getStorageSync(getNightWarningKey()) === 'true'
  } catch {
    return false
  }
}

/**
 * 标记夜间提醒已弹出
 */
function markNightWarning(): void {
  try {
    uni.setStorageSync(getNightWarningKey(), 'true')
  } catch {
    // 静默处理
  }
}

// ==================== 核心功能 ====================

/**
 * 检查当前是否处于锁定时段（22:00-05:00）
 */
function isLockTime(): boolean {
  const hour = new Date().getHours()
  return hour >= LOCK_HOUR || hour < UNLOCK_HOUR
}

/**
 * 检查当前是否处于夜间提醒时段（21:55-22:00）
 */
function isNightWarningTime(): boolean {
  const now = new Date()
  return now.getHours() === WARNING_HOUR && now.getMinutes() >= WARNING_MINUTE
}

/**
 * 显示1小时使用提醒
 */
function showOneHourWarning(): void {
  uni.showModal({
    title: '休息提醒',
    content: '今天已经使用60分钟了，休息一下眼睛和大脑吧',
    showCancel: false,
    confirmText: '我知道了',
  })
  markOneHourWarning()
  hasOneHourWarningShown = true
}

/**
 * 显示夜间休息提醒
 */
function showNightWarning(): void {
  uni.showModal({
    title: '准备休息',
    content: '还有5分钟就到睡觉时间了，准备好休息吧',
    showCancel: false,
    confirmText: '我知道了',
  })
  markNightWarning()
  hasNightWarningShown = true
}

/**
 * 显示锁定页
 */
function showLockPage(): void {
  uni.navigateTo({
    url: '/pages/auth/minor-lock',
    animationType: 'fade-in',
    animationDuration: 300,
  })
}

/**
 * 定时检查逻辑
 */
function performCheck(): void {
  if (!isTracking.value) return

  const now = Date.now()

  // 累加使用时长
  if (lastActiveTimestamp > 0) {
    const elapsed = now - lastActiveTimestamp
    // 防止异常的大跨度时间（如设备休眠导致），最多累加30分钟
    const safeElapsed = Math.min(elapsed, 30 * 60 * 1000)
    todayUsage.value += safeElapsed
    persistTodayUsage(todayUsage.value)
  }

  lastActiveTimestamp = now

  // 检查1小时使用提醒
  if (!hasOneHourWarningShown && !checkOneHourWarning() && todayUsage.value >= ONE_HOUR_MS) {
    showOneHourWarning()
  }

  // 检查21:55夜间提醒
  if (!hasNightWarningShown && !checkNightWarning() && isNightWarningTime()) {
    showNightWarning()
  }

  // 检查22:00锁定
  if (isLockTime()) {
    showLockPage()
    pauseTracking()
  }
}

/**
 * 开始追踪使用时长
 */
function startTracking(): void {
  const userStore = useUserStore()

  // 仅对青少年用户启用追踪
  if (!userStore.userInfo?.is_minor && userStore.userInfo?.ageRange !== 'under_18') {
    return
  }

  // 如果当前是锁定时段，直接显示锁定页
  if (isLockTime()) {
    showLockPage()
    return
  }

  isTracking.value = true

  // 恢复今日累计时长
  todayUsage.value = restoreTodayUsage()

  // 恢复提醒状态
  hasOneHourWarningShown = checkOneHourWarning()
  hasNightWarningShown = checkNightWarning()

  // 记录活跃时间
  lastActiveTimestamp = Date.now()

  // 启动定时检查
  if (!trackingTimer) {
    trackingTimer = setInterval(() => {
      performCheck()
    }, TIMER_INTERVAL)
  }

  // 立即执行一次检查
  performCheck()
}

/**
 * 暂停追踪使用时长（App 进入后台时调用）
 */
function pauseTracking(): void {
  if (!isTracking.value) return

  // 保存当前累计时长
  if (lastActiveTimestamp > 0) {
    const elapsed = Date.now() - lastActiveTimestamp
    const safeElapsed = Math.min(elapsed, 30 * 60 * 1000)
    todayUsage.value += safeElapsed
    persistTodayUsage(todayUsage.value)
  }

  lastActiveTimestamp = 0
  isTracking.value = false

  // 清除定时器
  if (trackingTimer) {
    clearInterval(trackingTimer)
    trackingTimer = null
  }
}

/**
 * 恢复追踪使用时长（App 恢复前台时调用）
 */
function resumeTracking(): void {
  const userStore = useUserStore()

  // 仅对青少年用户启用追踪
  if (!userStore.userInfo?.is_minor && userStore.userInfo?.ageRange !== 'under_18') {
    return
  }

  // 如果当前是锁定时段，显示锁定页
  if (isLockTime()) {
    showLockPage()
    return
  }

  // 重新开始追踪
  startTracking()
}

/**
 * 停止追踪并清除状态（用户退出青少年模式时调用）
 */
function stopTracking(): void {
  pauseTracking()
  todayUsage.value = 0
}

// ==================== 组合式函数导出 ====================

export function useMinorTimer() {
  // 组件卸载时清除定时器
  onUnmounted(() => {
    if (trackingTimer) {
      clearInterval(trackingTimer)
      trackingTimer = null
    }
  })

  return {
    /** 今日累计使用时长（毫秒） */
    todayUsage,
    /** 是否正在计时 */
    isTracking,
    /** 今日使用时长（格式化为 "X小时Y分钟"） */
    todayUsageFormatted: computed(() => {
      const totalMinutes = Math.floor(todayUsage.value / 60000)
      const hours = Math.floor(totalMinutes / 60)
      const minutes = totalMinutes % 60
      if (hours > 0) {
        return `${hours}小时${minutes}分钟`
      }
      return `${minutes}分钟`
    }),
    /** 开始追踪 */
    startTracking,
    /** 暂停追踪 */
    pauseTracking,
    /** 恢复追踪 */
    resumeTracking,
    /** 停止追踪 */
    stopTracking,
    /** 是否处于锁定时段 */
    isLockTime,
  }
}
