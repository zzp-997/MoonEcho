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

/** 是否启用埋点上报（可以通过环境变量禁用） */
const ENABLED = import.meta.env.VITE_ENABLE_TRACKING !== 'false'

/** 最大重试次数 */
const MAX_RETRIES = 3

/** 当前重试次数 */
let retryCount = 0

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

  // ========== 首页相关 ==========
  /** 首页访问 */
  HOME_VIEW: 'home_view',
  /** 情绪色调条点击 */
  HOME_EMOTION_BAR_TAP: 'home_emotion_bar_tap',
  /** AI对话入口点击 */
  HOME_AI_ENTRY_TAP: 'home_ai_entry_tap',
  /** 通知入口点击 */
  HOME_NOTIFICATION_TAP: 'home_notification_tap',
  /** 快捷功能点击 */
  HOME_QUICK_ACTION_TAP: 'home_quick_action_tap',
  /** 发布选择弹窗打开 */
  HOME_ACTION_SHEET_OPEN: 'home_action_sheet_open',

  // ========== AI对话相关（验证门控：日均对话轮次）==========
  /** 发送消息 */
  CHAT_SEND: 'chat_send',
  /** 接收AI回复 */
  CHAT_RECEIVE: 'chat_receive',
  /** 开始新对话 */
  CHAT_NEW_SESSION: 'chat_new_session',
  /** AI性格选择 */
  CHAT_PERSONALITY_SELECT: 'chat_personality_select',
  /** AI性格切换 */
  CHAT_PERSONALITY_SWITCH: 'chat_personality_switch',
  /** 跳过性格选择 */
  CHAT_PERSONALITY_SKIP: 'chat_personality_skip',
  /** 确认性格选择 */
  CHAT_PERSONALITY_CONFIRM: 'chat_personality_confirm',
  /** 对话消息复制 */
  CHAT_MESSAGE_COPY: 'chat_message_copy',
  /** 对话消息分享 */
  CHAT_MESSAGE_SHARE: 'chat_message_share',
  /** 对话错误 */
  CHAT_ERROR: 'chat_error',

  // ========== 危机干预相关 ==========
  /** 危机检测触发 */
  CRISIS_DETECTED: 'crisis_detected',
  /** 危机干预弹窗显示 */
  CRISIS_DIALOG_SHOW: 'crisis_dialog_show',
  /** 危机干预确认 */
  CRISIS_CONFIRM: 'crisis_confirm',
  /** 危机热线拨打 */
  CRISIS_HOTLINE_CALL: 'crisis_hotline_call',

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
  /** 导出日记 */
  DIARY_EXPORT: 'diary_export',

  // ========== 周报相关 ==========
  /** 查看周报 */
  REPORT_VIEW: 'report_view',
  /** 周报刷新 */
  REPORT_REFRESH: 'report_refresh',
  /** 查看周报历史 */
  REPORT_HISTORY_VIEW: 'report_history_view',
  /** 展开温和建议 */
  REPORT_SUGGESTION_EXPAND: 'report_suggestion_expand',
  /** 关闭温和建议 */
  REPORT_SUGGESTION_COLLAPSE: 'report_suggestion_collapse',

  // ========== 树洞/社交相关 ==========
  /** 发布树洞 */
  TREEHOLE_PUBLISH: 'treehole_publish',
  /** 查看树洞列表 */
  TREEHOLE_LIST_VIEW: 'treehole_list_view',
  /** 树洞话题筛选 */
  TREEHOLE_TOPIC_FILTER: 'treehole_topic_filter',
  /** 查看树洞帖子详情 */
  TREEHOLE_POST_VIEW: 'treehole_post_view',
  /** 创建共鸣（我懂你） */
  TREEHOLE_RESONANCE: 'treehole_resonance',
  /** 查看评论区 */
  TREEHOLE_COMMENT_VIEW: 'treehole_comment_view',
  /** 创建树洞评论 */
  TREEHOLE_COMMENT_CREATE: 'treehole_comment_create',
  /** 开始发布树洞 */
  TREEHOLE_CREATE_START: 'treehole_create_start',
  /** 发布树洞成功 */
  TREEHOLE_CREATE_SUCCESS: 'treehole_create_success',
  /** 发布树洞被拦截 */
  TREEHOLE_CREATE_BLOCKED: 'treehole_create_blocked',
  /** AI润色 */
  TREEHOLE_AI_REWRITE: 'treehole_ai_rewrite',
  /** 删除树洞帖子 */
  TREEHOLE_DELETE: 'treehole_delete',
  /** 树洞点赞 */
  TREEHOLE_LIKE: 'treehole_like',
  /** 树洞评论 */
  TREEHOLE_COMMENT: 'treehole_comment',
  /** 发布动态 */
  SQUARE_PUBLISH: 'square_publish',
  /** 查看广场 */
  SQUARE_LIST_VIEW: 'square_list_view',
  /** 查看动态详情 */
  SQUARE_POST_VIEW: 'square_post_view',
  /** 创建共鸣 */
  SQUARE_RESONANCE: 'square_resonance',
  /** 查看评论区 */
  SQUARE_COMMENT_VIEW: 'square_comment_view',
  /** 创建评论 */
  SQUARE_COMMENT_CREATE: 'square_comment_create',
  /** 开始发布动态 */
  SQUARE_CREATE_START: 'square_create_start',
  /** 发布动态成功 */
  SQUARE_CREATE_SUCCESS: 'square_create_success',
  /** 发布动态被拦截 */
  SQUARE_CREATE_BLOCKED: 'square_create_blocked',
  /** 收藏动态 */
  SQUARE_BOOKMARK: 'square_bookmark',
  /** 悄悄关注 */
  SQUARE_WHISPER_FOLLOW: 'square_whisper_follow',
  /** 匿名切换 */
  SQUARE_ANONYMOUS_TOGGLE: 'square_anonymous_toggle',
  /** 上传图片 */
  SQUARE_IMAGE_UPLOAD: 'square_image_upload',
  /** 排序方式变更 */
  SQUARE_SORT_CHANGE: 'square_sort_change',
  /** 删除动态 */
  SQUARE_DELETE: 'square_delete',
  /** 举报广场动态 */
  SQUARE_REPORT: 'square_report',

  // ========== 举报相关 ==========
  /** 举报树洞帖子 */
  TREEHOLE_REPORT: 'treehole_report',
  /** 举报树洞评论 */
  TREEHOLE_COMMENT_REPORT: 'treehole_comment_report',
  /** 举报广场评论 */
  SQUARE_COMMENT_REPORT: 'square_comment_report',
  /** 举报用户 */
  USER_REPORT: 'user_report',

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

  // ========== 通知相关 ==========
  /** 查看通知列表 */
  NOTIFICATION_LIST_VIEW: 'notification_list_view',
  /** 点击通知 */
  NOTIFICATION_CLICK: 'notification_click',
  /** 标记单条已读 */
  NOTIFICATION_MARK_READ: 'notification_mark_read',
  /** 全部标记已读 */
  NOTIFICATION_MARK_ALL_READ: 'notification_mark_all_read',
  /** 删除通知 */
  NOTIFICATION_DELETE: 'notification_delete',
  /** 查看通知设置 */
  NOTIFICATION_SETTINGS_VIEW: 'notification_settings_view',
  /** 更新通知设置 */
  NOTIFICATION_SETTINGS_CHANGE: 'notification_settings_change',

  // ========== 好友系统相关 ==========
  /** 查看好友列表 */
  FRIEND_LIST_VIEW: 'friend_list_view',
  /** 搜索好友 */
  FRIEND_SEARCH: 'friend_search',
  /** 发送好友申请 */
  FRIEND_REQUEST_SEND: 'friend_request_send',
  /** 查看好友申请列表 */
  FRIEND_REQUEST_LIST_VIEW: 'friend_request_list_view',
  /** 同意好友申请 */
  FRIEND_REQUEST_ACCEPT: 'friend_request_accept',
  /** 拒绝好友申请 */
  FRIEND_REQUEST_REJECT: 'friend_request_reject',
  /** 删除好友 */
  FRIEND_DELETE: 'friend_delete',
  /** 拉黑用户 */
  USER_BLOCK: 'user_block',
  /** 取消拉黑 */
  USER_UNBLOCK: 'user_unblock',
  /** 查看他人主页 */
  USER_PROFILE_VIEW: 'user_profile_view',
  /** AI打招呼语生成 */
  AI_GREETING_GENERATE: 'ai_greeting_generate',
  /** AI打招呼语使用 */
  AI_GREETING_USE: 'ai_greeting_use',

  // ========== 私聊相关 ==========
  /** 查看会话列表 */
  CONVERSATION_LIST_VIEW: 'conversation_list_view',
  /** 进入私聊页面 */
  CHAT_PRIVATE_ENTER: 'chat_private_enter',
  /** 发送私聊消息 */
  CHAT_PRIVATE_SEND: 'chat_private_send',
  /** 发送私聊图片 */
  CHAT_PRIVATE_IMAGE_SEND: 'chat_private_image_send',
  /** 接收私聊消息 */
  CHAT_PRIVATE_RECEIVE: 'chat_private_receive',
  /** WebSocket 连接 */
  WEBSOCKET_CONNECT: 'websocket_connect',
  /** WebSocket 断开 */
  WEBSOCKET_DISCONNECT: 'websocket_disconnect',
  /** WebSocket 重连 */
  WEBSOCKET_RECONNECT: 'websocket_reconnect',

  // ========== AI聊天辅助相关 ==========
  /** AI话题建议展示 */
  AI_TOPIC_SHOW: 'ai_topic_show',
  /** AI话题建议使用 */
  AI_TOPIC_USE: 'ai_topic_use',
  /** AI回复建议展示 */
  AI_REPLY_SHOW: 'ai_reply_show',
  /** AI回复建议使用 */
  AI_REPLY_USE: 'ai_reply_use',
  /** AI语气优化 */
  AI_POLISH_USE: 'ai_polish_use',
  /** AI温柔退出展示 */
  AI_EXIT_SHOW: 'ai_exit_show',
  /** AI温柔退出使用 */
  AI_EXIT_USE: 'ai_exit_use',

  // ========== 社交能量相关 ==========
  /** 查看社交能量 */
  SOCIAL_ENERGY_VIEW: 'social_energy_view',
  /** 社交能量休息 */
  SOCIAL_ENERGY_REST: 'social_energy_rest',

  // ========== 个人中心相关 ==========
  /** 个人中心访问 */
  MINE_VIEW: 'mine_view',
  /** 设置访问 */
  SETTINGS_VIEW: 'settings_view',
  /** 设置修改 */
  SETTING_CHANGE: 'setting_change',

  // ========== 用户登出 ==========
  /** 用户登出 */
  USER_LOGOUT: 'user_logout',
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
  if (!ENABLED || eventQueue.length === 0) return

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
        retryCount = 0
        if (DEBUG) {
          console.log('[Tracking] Flushed', eventsToSend.length, 'events')
        }
      },
      fail: (err) => {
        // 发送失败，检查重试次数
        retryCount++
        if (retryCount < MAX_RETRIES) {
          // 重新加入队列
          eventQueue = [...eventsToSend, ...eventQueue]
          if (DEBUG) {
            console.log('[Tracking] Flush failed, will retry:', err)
          }
        } else {
          // 超过重试次数，清空队列避免一直报错
          console.warn('[Tracking] Max retries reached, clearing queue')
          uni.removeStorageSync(EVENT_QUEUE_KEY)
          retryCount = 0
        }
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
  if (!ENABLED) {
    if (DEBUG) {
      console.log('[Tracking] Tracking disabled')
    }
    return
  }

  // 从本地恢复事件队列（限制队列大小避免内存问题）
  try {
    const savedQueue = uni.getStorageSync(EVENT_QUEUE_KEY)
    if (savedQueue) {
      const parsed = JSON.parse(savedQueue)
      // 只保留最近100个事件
      eventQueue = parsed.slice(-100)
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

  // 定时刷新队列（每60秒，降低频率）
  setInterval(() => {
    flushQueue()
  }, 60000)

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
