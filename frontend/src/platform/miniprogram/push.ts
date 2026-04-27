/**
 * 回声 - 小程序推送降级
 * 文件：src/platform/miniprogram/push.ts
 * 说明：统一推送接口，App 端使用极光推送，小程序使用模板消息
 * 作者：Frontend Developer
 */

// ==================== 类型定义 ====================

/** 推送消息类型 */
export interface PushMessage {
  /** 消息标题 */
  title: string
  /** 消息内容 */
  content: string
  /** 消息类型 */
  type: PushMessageType
  /** 额外数据 */
  payload?: Record<string, any>
  /** 跳转页面 */
  page?: string
  /** 跳转参数 */
  params?: Record<string, string>
}

/** 推送消息类型枚举 */
export enum PushMessageType {
  /** AI 回复通知 */
  AI_REPLY = 'ai_reply',
  /** 日记提醒 */
  DIARY_REMINDER = 'diary_reminder',
  /** 周报生成 */
  WEEKLY_REPORT = 'weekly_report',
  /** 好友动态 */
  FRIEND_ACTIVITY = 'friend_activity',
  /** 树洞回复 */
  TREEHOLE_REPLY = 'treehole_reply',
  /** 系统通知 */
  SYSTEM = 'system',
}

/** 推送配置 */
export interface PushConfig {
  /** 极光推送 AppKey（App 端） */
  jpushAppKey?: string
  /** 小程序模板 ID 映射 */
  templateIds?: Record<PushMessageType, string>
}

/** 推送权限状态 */
export interface PushPermissionStatus {
  /** 是否已授权 */
  authorized: boolean
  /** 是否为小程序环境 */
  isMiniProgram: boolean
  /** 是否需要用户主动触发 */
  requiresUserTrigger: boolean
}

/** 推送订阅结果 */
export interface SubscribeResult {
  /** 是否成功 */
  success: boolean
  /** 模板 ID */
  templateId?: string
  /** 错误信息 */
  error?: string
}

/** 订阅消息模板 */
export interface SubscribeTemplate {
  /** 模板 ID */
  id: string
  /** 模板标题 */
  title: string
  /** 模板内容 */
  content: string
  /** 模板示例 */
  example: string
}

// ==================== 平台检测 ====================

/**
 * 检测是否为小程序环境
 */
function isMiniProgram(): boolean {
  // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
  return true
  // #endif

  // #ifndef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
  return false
  // #endif
}

// ==================== 默认配置 ====================

const DEFAULT_TEMPLATE_IDS: Record<PushMessageType, string> = {
  [PushMessageType.AI_REPLY]: '', // 需要在后台配置
  [PushMessageType.DIARY_REMINDER]: '',
  [PushMessageType.WEEKLY_REPORT]: '',
  [PushMessageType.FRIEND_ACTIVITY]: '',
  [PushMessageType.TREEHOLE_REPLY]: '',
  [PushMessageType.SYSTEM]: '',
}

// ==================== 推送适配器接口 ====================

/**
 * 推送适配器接口
 */
export interface PushAdapter {
  /** 初始化推送服务 */
  init(): Promise<void>
  /** 检查推送权限 */
  checkPermission(): Promise<PushPermissionStatus>
  /** 请求推送权限 */
  requestPermission(): Promise<boolean>
  /** 订阅消息 */
  subscribe(messageTypes: PushMessageType[]): Promise<SubscribeResult[]>
  /** 取消订阅 */
  unsubscribe(messageTypes: PushMessageType[]): Promise<void>
  /** 本地通知（仅 App 端） */
  localNotify(message: PushMessage): Promise<void>
  /** 获取设备注册 ID */
  getRegistrationId(): Promise<string | null>
}

// ==================== 小程序推送适配器 ====================

/**
 * 小程序推送适配器
 * 使用微信小程序订阅消息
 *
 * 注意：小程序模板消息有以下限制：
 * 1. 需要用户主动触发订阅
 * 2. 每次订阅只能发送一次消息
 * 3. 需要在小程序后台配置模板
 */
export class MiniProgramPushAdapter implements PushAdapter {
  private templateIds: Record<PushMessageType, string>
  private subscribedTemplates: Set<string> = new Set()

  constructor(config: PushConfig = {}) {
    this.templateIds = config.templateIds || DEFAULT_TEMPLATE_IDS
  }

  /**
   * 初始化推送服务
   */
  async init(): Promise<void> {
    console.log('[MiniProgramPush] 推送服务初始化')

    // #ifdef MP-WEIXIN
    // 微信小程序：检查是否有未读消息
    this.checkUnreadMessages()
    // #endif
  }

  /**
   * 检查推送权限
   */
  async checkPermission(): Promise<PushPermissionStatus> {
    return {
      authorized: this.subscribedTemplates.size > 0,
      isMiniProgram: true,
      requiresUserTrigger: true, // 小程序需要用户主动触发订阅
    }
  }

  /**
   * 请求推送权限
   * 注意：小程序需要在用户点击时调用
   */
  async requestPermission(): Promise<boolean> {
    // #ifdef MP-WEIXIN
    try {
      // 请求订阅消息授权
      const templateIds = Object.values(this.templateIds).filter(Boolean)
      if (templateIds.length === 0) {
        console.warn('[MiniProgramPush] 未配置模板 ID')
        return false
      }

      return new Promise((resolve) => {
        wx.requestSubscribeMessage({
          tmplIds: templateIds,
          success: (res) => {
            console.log('[MiniProgramPush] 订阅结果:', res)
            for (const templateId of templateIds) {
              if (res[templateId] === 'accept') {
                this.subscribedTemplates.add(templateId)
              }
            }
            resolve(this.subscribedTemplates.size > 0)
          },
          fail: (err) => {
            console.error('[MiniProgramPush] 订阅失败:', err)
            resolve(false)
          },
        })
      })
    } catch (e) {
      console.error('[MiniProgramPush] 请求权限异常:', e)
      return false
    }
    // #endif

    // #ifndef MP-WEIXIN
    return false
    // #endif
  }

  /**
   * 订阅消息
   */
  async subscribe(messageTypes: PushMessageType[]): Promise<SubscribeResult[]> {
    const results: SubscribeResult[] = []

    // #ifdef MP-WEIXIN
    const templateIds = messageTypes
      .map((type) => this.templateIds[type])
      .filter(Boolean)

    if (templateIds.length === 0) {
      return messageTypes.map((type) => ({
        success: false,
        templateId: this.templateIds[type],
        error: '未配置模板 ID',
      }))
    }

    return new Promise((resolve) => {
      wx.requestSubscribeMessage({
        tmplIds: templateIds,
        success: (res) => {
          const results: SubscribeResult[] = []
          for (const type of messageTypes) {
            const templateId = this.templateIds[type]
            const status = res[templateId]
            const success = status === 'accept'
            if (success) {
              this.subscribedTemplates.add(templateId)
            }
            results.push({
              success,
              templateId,
              error: success ? undefined : `用户${status === 'reject' ? '拒绝' : '取消'}`,
            })
          }
          resolve(results)
        },
        fail: (err) => {
          resolve(
            messageTypes.map((type) => ({
              success: false,
              templateId: this.templateIds[type],
              error: err.errMsg || '订阅失败',
            }))
          )
        },
      })
    })
    // #endif

    // #ifndef MP-WEIXIN
    return messageTypes.map((type) => ({
      success: false,
      error: '仅支持微信小程序',
    }))
    // #endif
  }

  /**
   * 取消订阅
   * 注意：小程序不支持取消订阅，订阅状态由用户控制
   */
  async unsubscribe(messageTypes: PushMessageType[]): Promise<void> {
    for (const type of messageTypes) {
      const templateId = this.templateIds[type]
      this.subscribedTemplates.delete(templateId)
    }
  }

  /**
   * 本地通知
   * 小程序不支持本地通知，使用页面内提示替代
   */
  async localNotify(message: PushMessage): Promise<void> {
    console.log('[MiniProgramPush] 本地通知（降级为页面提示）:', message)

    // 小程序降级方案：使用页面内弹窗或 Toast
    uni.showToast({
      title: message.title,
      icon: 'none',
      duration: 3000,
    })
  }

  /**
   * 获取设备注册 ID
   * 小程序返回 null
   */
  async getRegistrationId(): Promise<string | null> {
    return null
  }

  /**
   * 检查未读消息
   */
  private checkUnreadMessages(): void {
    // #ifdef MP-WEIXIN
    // 可以通过 API 检查服务器是否有未读消息
    // 在用户进入应用时主动拉取
    console.log('[MiniProgramPush] 检查未读消息')
    // #endif
  }

  /**
   * 获取可用的模板列表
   */
  async getAvailableTemplates(): Promise<SubscribeTemplate[]> {
    // #ifdef MP-WEIXIN
    return new Promise((resolve) => {
      wx.getSetting({
        withSubscriptions: true,
        success: (res) => {
          console.log('[MiniProgramPush] 订阅设置:', res)
          // 返回已订阅的模板信息
          resolve([])
        },
        fail: () => resolve([]),
      })
    })
    // #endif

    // #ifndef MP-WEIXIN
    return []
    // #endif
  }
}

// ==================== App 推送适配器（预留） ====================

/**
 * App 端推送适配器
 * 使用极光推送
 *
 * 注意：需要在 manifest.json 中配置极光推送
 */
export class AppPushAdapter implements PushAdapter {
  private jpushAppKey?: string
  private registrationId: string | null = null

  constructor(config: PushConfig = {}) {
    this.jpushAppKey = config.jpushAppKey
  }

  /**
   * 初始化推送服务
   */
  async init(): Promise<void> {
    // #ifdef APP-PLUS
    console.log('[AppPush] 初始化极光推送')

    // 这里需要集成极光推送插件
    // 示例代码：
    // const jpush = uni.requireNativePlugin('JG-JPush')
    // jpush.init()

    // 获取注册 ID
    // jpush.getRegistrationID((result) => {
    //   this.registrationId = result.registrationID
    // })
    // #endif
  }

  /**
   * 检查推送权限
   */
  async checkPermission(): Promise<PushPermissionStatus> {
    return {
      authorized: true, // App 端默认已授权
      isMiniProgram: false,
      requiresUserTrigger: false,
    }
  }

  /**
   * 请求推送权限
   */
  async requestPermission(): Promise<boolean> {
    // #ifdef APP-PLUS
    // App 端权限通常在安装时已获取
    return true
    // #endif

    // #ifndef APP-PLUS
    return false
    // #endif
  }

  /**
   * 订阅消息
   * App 端通过极光推送标签实现
   */
  async subscribe(messageTypes: PushMessageType[]): Promise<SubscribeResult[]> {
    // #ifdef APP-PLUS
    // 设置极光推送标签
    // const jpush = uni.requireNativePlugin('JG-JPush')
    // jpush.setTags({ sequence: 1, tags: messageTypes })

    return messageTypes.map((type) => ({
      success: true,
      templateId: type,
    }))
    // #endif

    // #ifndef APP-PLUS
    return messageTypes.map((type) => ({
      success: false,
      error: '仅支持 App 端',
    }))
    // #endif
  }

  /**
   * 取消订阅
   */
  async unsubscribe(messageTypes: PushMessageType[]): Promise<void> {
    // #ifdef APP-PLUS
    // const jpush = uni.requireNativePlugin('JG-JPush')
    // jpush.deleteTags({ sequence: 1, tags: messageTypes })
    // #endif
  }

  /**
   * 本地通知
   */
  async localNotify(message: PushMessage): Promise<void> {
    // #ifdef APP-PLUS
    // 使用极光推送本地通知
    // const jpush = uni.requireNativePlugin('JG-JPush')
    // jpush.addLocalNotification({
    //   messageID: Date.now().toString(),
    //   title: message.title,
    //   content: message.content,
    //   extras: message.payload,
    // })
    // #endif
  }

  /**
   * 获取设备注册 ID
   */
  async getRegistrationId(): Promise<string | null> {
    return this.registrationId
  }
}

// ==================== 统一推送接口 ====================

let pushAdapter: PushAdapter | null = null

/**
 * 创建平台适配的推送实例
 */
export function createPushAdapter(config?: PushConfig): PushAdapter {
  // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ
  return new MiniProgramPushAdapter(config)
  // #endif

  // #ifdef APP-PLUS
  return new AppPushAdapter(config)
  // #endif

  // #ifdef H5
  // H5 不支持推送，返回空实现
  return {
    init: async () => {},
    checkPermission: async () => ({ authorized: false, isMiniProgram: false, requiresUserTrigger: false }),
    requestPermission: async () => false,
    subscribe: async () => [],
    unsubscribe: async () => {},
    localNotify: async () => {},
    getRegistrationId: async () => null,
  }
  // #endif
}

/**
 * 获取推送实例
 */
export async function getPush(): Promise<PushAdapter> {
  if (!pushAdapter) {
    pushAdapter = createPushAdapter()
    await pushAdapter.init()
  }
  return pushAdapter
}

/**
 * 快捷订阅消息
 * 适用于小程序中用户点击后的场景
 */
export async function quickSubscribe(types: PushMessageType[]): Promise<SubscribeResult[]> {
  const push = await getPush()
  return push.subscribe(types)
}

/**
 * 检查是否支持推送
 */
export function isPushSupported(): boolean {
  // #ifdef MP-WEIXIN || APP-PLUS
  return true
  // #endif

  // #ifndef MP-WEIXIN || APP-PLUS
  return false
  // #endif
}

// ==================== 导出 ====================

export default {
  createPushAdapter,
  getPush,
  quickSubscribe,
  isPushSupported,
  PushMessageType,
  MiniProgramPushAdapter,
  AppPushAdapter,
}
