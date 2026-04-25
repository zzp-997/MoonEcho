/**
 * 回声 - 数据埋点工具
 * 文件：src/utils/tracking.ts
 * 说明：事件上报封装，为阶段一验证门控提供数据采集能力
 * 验证指标：7日留存、日均对话轮次、日记连续记录率、NPS
 * 参考：prod_v2.md 阶段一验证门控
 */

import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'

// ==================== 配置 ====================

/** 埋点上报地址 */
const TRACKING_URL = import.meta.env.VITE_TRACKING_URL || '/api/v1/analytics/events'

/** 是否开启调试模式 */
const DEBUG = import.meta.env.VITE_DEBUG === 'true'

/** 本地缓存键 */
const EVENT_QUEUE_KEY = 'huisheng_event_queue'

// ==================== 事件类型定义 ====================

/** 事件名称枚举 */
export const EventName = {
  // ========== 用户生命周期 ==========
  /** 应用启动 */
  APP_LAUNCH: 'app_launch',
  /** 应用进入前台 */
  APP_SHOW: 'app_show',
  /** 应用进入后台 */
  APP_HIDE: 'app_hide',
  /** 用户注册完成 */
  USER_REGISTER: 'user_register',
  /** 用户登录 */
  USER_LOGIN: 'user_login',
  /** 用户登出 */
  USER_LOGOUT: 'user_logout',

  // ========== 留存相关（验证门控：7日留存）==========
  /** 每日首次打开 */
  DAILY_ACTIVE: 'daily_active',
  /** 用户返回（次日/7日） */
  USER_RETURN: 'user_return',

  // ========== AI对话相关（验证门控：日均对话轮次）==========
  /** 发送消息 */
  CHAT_SEND: 'chat_send',
  /** 接收AI回复 */
  CHAT_RECEIVE: 'chat_receive',
  /** 开始新对话 */
  CHAT_NEW_SESSION: 'chat_new_session',
  /** AI性格选择 */
  CHAT_PERSONALITY_SELECT: 'chat_personality_select',
  /** 对话消息复制 */
  CHAT_MESSAGE_COPY: 'chat_message_copy',
  /** 对话消息分享 */
  CHAT_MESSAGE_SHARE: 'chat_message_share',

  // ========== 日记相关（验证门控：日记连续记录率）==========
  /** 记录日记 */
  DIARY_CREATE: 'diary_create',
  /** 编辑日记 */
  DIARY_EDIT: 'diary_edit',
  /** 删除日记 */
  DIARY_DELETE: 'diary_delete',
  /** 查看日记列表 */
  DIARY_LIST_VIEW: 'diary_list_view',
  /** 查看日记详情 */
  DIARY_DETAIL_VIEW: 'diary_detail_view',
  /** 日记连续记录里程碑 */
  DIARY_STREAK_MILESTONE: 'diary_streak_milestone',

  // ========== 树洞/社交相关 ==========
  /** 发布树洞 */
  TREEHOLE_PUBLISH: 'treehole_publish',
  /** 查看树洞列表 */
  TREEHOLE_LIST_VIEW: 'treehole_list_view',
  /** 树洞点赞 */
  TREEHOLE_LIKE: 'treehole_like',
  /** 树洞评论 */
  TREEHOLE_COMMENT: 'treehole_comment',
  /** 发布动态 */
  SQUARE_PUBLISH: 'square_publish',
  /** 查看广场 */
  SQUARE_LIST_VIEW: 'square_list_view',

  // ========== NPS相关（验证门控：NPS）==========
  /** 显示NPS问卷 */
  NPS_SHOW: 'nps_show',
  /** 提交NPS评分 */
  NPS_SUBMIT: 'nps_submit',
  /** 关闭NPS问卷 */
  NPS_CLOSE: 'nps_close',

  // ========== 页面访问 ==========
  /** 页面访问 */
  PAGE_VIEW: 'page_view',
  /** 页面停留时长 */
  PAGE_DURATION: 'page_duration',

  // ========== 功能使用 ==========
  /** 主题切换 */
  THEME_CHANGE: 'theme_change',
  /** 青少年模式开启 */
  TEEN_MODE_ENABLE: 'teen_mode_enable',
  /** 设置修改 */
  SETTINGS_CHANGE: 'settings_change',
} as const

export type EventNameType = (typeof EventName)[keyof typeof EventName]

/** 事件属性接口 */
export interface EventProperties {
  [key: string]: string | number | boolean | undefined
}

/** 事件数据结构 */
export interface TrackingEvent {
  name: EventNameType
  properties?: EventProperties
  timestamp: number
  userId?: string
  deviceId: string
  sessionId: string
  platform: string
  appVersion: string
}

// ==================== 核心功能 ====================

/** 事件队列 */
let eventQueue: TrackingEvent[] = []

/** 会话ID */
let sessionId: string = generateSessionId()

/** 页面进入时间记录 */
const pageEnterTimes: Map<string, number> = new Map()

/**
 * 生成会话ID
 */
function generateSessionId(): string {
  return `sid_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * 获取平台信息
 */
function getPlatform(): string {
  // #ifdef H5
  return 'h5'
  // #endif
  // #ifdef MP-WEIXIN
  return 'mp-weixin'
  // #endif
  // #ifdef APP-PLUS
  return 'app'
  // #endif
  return 'unknown'
}

/**
 * 创建事件对象
 */
function createEvent(name: EventNameType, properties?: EventProperties): TrackingEvent {
  const userStore = useUserStore()
  const settingsStore = useSettingsStore()

  return {
    name,
    properties,
    timestamp: Date.now(),
    userId: userStore.userInfo?.id,
    deviceId: settingsStore.deviceId,
    sessionId,
    platform: getPlatform(),
    appVersion: settingsStore.appVersion,
  }
}

/**
 * 添加事件到队列
 */
function enqueueEvent(event: TrackingEvent) {
  eventQueue.push(event)

  // 缓存到本地
  try {
    uni.setStorageSync(EVENT_QUEUE_KEY, JSON.stringify(eventQueue))
  } catch (e) {
    console.error('缓存事件队列失败', e)
  }

  // 调试模式打印
  if (DEBUG) {
    console.log('[Tracking] Event:', event.name, event.properties)
  }
}

/**
 * 发送事件队列
 */
async function flushQueue(): Promise<void> {
  if (eventQueue.length === 0) return

  const eventsToSend = [...eventQueue]
  eventQueue = []

  try {
    // 批量发送事件
    uni.request({
      url: TRACKING_URL,
      method: 'POST',
      data: { events: eventsToSend },
      header: { 'Content-Type': 'application/json' },
      success: () => {
        // 发送成功，清除本地缓存
        uni.removeStorageSync(EVENT_QUEUE_KEY)
        if (DEBUG) {
          console.log('[Tracking] Flushed', eventsToSend.length, 'events')
        }
      },
      fail: (err) => {
        // 发送失败，重新加入队列
        eventQueue = [...eventsToSend, ...eventQueue]
        console.error('[Tracking] Flush failed:', err)
      },
    })
  } catch (e) {
    console.error('[Tracking] Flush error:', e)
    eventQueue = [...eventsToSend, ...eventQueue]
  }
}

/**
 * 初始化埋点系统
 */
export function initTracking() {
  // 从本地恢复事件队列
  try {
    const savedQueue = uni.getStorageSync(EVENT_QUEUE_KEY)
    if (savedQueue) {
      eventQueue = JSON.parse(savedQueue)
    }
  } catch (e) {
    console.error('恢复事件队列失败', e)
  }

  // 应用生命周期事件
  // #ifdef APP-PLUS
  plus.globalEvent.addEventListener('plusready', () => {
    track(EventName.APP_LAUNCH)
    checkDailyActive()
  })
  // #endif

  // 定时刷新队列（每30秒）
  setInterval(() => {
    flushQueue()
  }, 30000)

  // 页面切换时刷新
  // uni.onAppHide 和 uni.onAppShow 需要在 App.vue 中处理
}

/**
 * 追踪事件
 * @param name 事件名称
 * @param properties 事件属性
 */
export function track(name: EventNameType, properties?: EventProperties) {
  const event = createEvent(name, properties)
  enqueueEvent(event)

  // 立即发送关键事件
  const immediateEvents: EventNameType[] = [
    EventName.USER_REGISTER,
    EventName.USER_LOGIN,
    EventName.NPS_SUBMIT,
  ]
  if (immediateEvents.includes(name)) {
    flushQueue()
  }
}

/**
 * 检查并记录每日活跃
 * 验证门控：7日留存
 */
export function checkDailyActive() {
  const today = new Date().toISOString().split('T')[0]
  const lastActiveDate = uni.getStorageSync('huisheng_last_active_date')

  if (lastActiveDate !== today) {
    // 每日首次打开
    track(EventName.DAILY_ACTIVE, { date: today })

    // 检查用户返回（次日留存、7日留存）
    if (lastActiveDate) {
      const lastDate = new Date(lastActiveDate)
      const todayDate = new Date(today)
      const daysDiff = Math.floor((todayDate.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24))

      if (daysDiff === 1) {
        track(EventName.USER_RETURN, { type: 'day1' })
      } else if (daysDiff === 7) {
        track(EventName.USER_RETURN, { type: 'day7' })
      }
    }

    uni.setStorageSync('huisheng_last_active_date', today)
  }
}

/**
 * 页面进入追踪
 */
export function trackPageEnter(pageName: string) {
  pageEnterTimes.set(pageName, Date.now())
  track(EventName.PAGE_VIEW, { page: pageName })
}

/**
 * 页面离开追踪（计算停留时长）
 */
export function trackPageLeave(pageName: string) {
  const enterTime = pageEnterTimes.get(pageName)
  if (enterTime) {
    const duration = Math.floor((Date.now() - enterTime) / 1000)
    track(EventName.PAGE_DURATION, { page: pageName, duration })
    pageEnterTimes.delete(pageName)
  }
}

/**
 * 应用显示（从后台恢复）
 */
export function trackAppShow() {
  sessionId = generateSessionId()
  track(EventName.APP_SHOW)
  checkDailyActive()
}

/**
 * 应用隐藏（进入后台）
 */
export function trackAppHide() {
  track(EventName.APP_HIDE)
  flushQueue()
}

// ==================== 便捷方法 ====================

/**
 * 追踪对话消息发送
 */
export function trackChatSend(properties: { messageLength: number; personalityType: string }) {
  track(EventName.CHAT_SEND, properties)
}

/**
 * 追踪日记创建
 */
export function trackDiaryCreate(properties: { emotion: string; intensity: number; hasContent: boolean }) {
  track(EventName.DIARY_CREATE, properties)
}

/**
 * 追踪NPS提交
 */
export function trackNPSSubmit(properties: { score: number; feedback?: string }) {
  track(EventName.NPS_SUBMIT, properties)
}

/**
 * 追踪日记连续记录里程碑
 */
export function trackDiaryStreak(streakDays: number) {
  // 里程碑：3天、7天、14天、30天
  const milestones = [3, 7, 14, 30]
  if (milestones.includes(streakDays)) {
    track(EventName.DIARY_STREAK_MILESTONE, { streak_days: streakDays })
  }
}

// 导出默认对象
export default {
  init: initTracking,
  track,
  trackPageEnter,
  trackPageLeave,
  trackAppShow,
  trackAppHide,
  checkDailyActive,
  flush: flushQueue,
  EventName,
}
