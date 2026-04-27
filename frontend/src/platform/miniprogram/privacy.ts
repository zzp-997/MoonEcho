/**
 * 回声 - 小程序审核要点适配
 * 文件：src/platform/miniprogram/privacy.ts
 * 说明：用户隐私协议页适配、内容安全 API 接入、禁止诱导分享检查
 * 作者：Frontend Developer
 */

// ==================== 类型定义 ====================

/** 隐私协议状态 */
export interface PrivacyStatus {
  /** 是否已同意隐私协议 */
  agreed: boolean
  /** 同意时间 */
  agreedAt?: string
  /** 协议版本 */
  version?: string
}

/** 隐私协议配置 */
export interface PrivacyConfig {
  /** 协议版本 */
  version: string
  /** 协议链接 */
  privacyUrl: string
  /** 用户协议链接 */
  userAgreementUrl: string
  /** 收集的信息项 */
  collectedInfo: string[]
  /** 使用的权限列表 */
  permissions: PermissionItem[]
}

/** 权限项 */
export interface PermissionItem {
  /** 权限名称 */
  name: string
  /** 权限描述 */
  description: string
  /** 使用目的 */
  purpose: string
  /** 是否必须 */
  required: boolean
}

/** 内容安全检查结果 */
export interface ContentSecurityResult {
  /** 是否通过 */
  pass: boolean
  /** 检测类型 */
  type: 'text' | 'image' | 'audio'
  /** 风险等级 */
  riskLevel?: 'pass' | 'review' | 'reject'
  /** 风险标签 */
  labels?: string[]
  /** 建议 */
  suggestion?: string
  /** 错误信息 */
  error?: string
}

/** 分享检查结果 */
export interface ShareCheckResult {
  /** 是否合规 */
  compliant: boolean
  /** 违规原因 */
  reason?: string
  /** 建议 */
  suggestion?: string
}

/** 青少年模式状态 */
export interface MinorModeStatus {
  /** 是否开启 */
  enabled: boolean
  /** 每日使用时长限制（分钟） */
  timeLimit?: number
  /** 休息时间段 */
  restTime?: {
    start: string
    end: string
  }
  /** 内容过滤级别 */
  contentFilter?: 'strict' | 'moderate' | 'none'
}

// ==================== 常量定义 ====================

/** 当前隐私协议版本 */
const PRIVACY_VERSION = '1.0.0'

/** 隐私协议存储键 */
const PRIVACY_STORAGE_KEY = 'huisheng_privacy_agreed'

/** 青少年模式存储键 */
const MINOR_MODE_KEY = 'huisheng_minor_mode'

/** 默认隐私配置 */
const DEFAULT_PRIVACY_CONFIG: PrivacyConfig = {
  version: PRIVACY_VERSION,
  privacyUrl: '/pages/webview/index?type=privacy',
  userAgreementUrl: '/pages/webview/index?type=agreement',
  collectedInfo: [
    '微信昵称',
    '微信头像',
    '设备信息',
    '使用记录',
    '情绪日记内容',
  ],
  permissions: [
    {
      name: '相机',
      description: '用于拍摄照片上传至日记或动态',
      purpose: '记录生活，保存回忆',
      required: false,
    },
    {
      name: '相册',
      description: '用于选择照片上传至日记或动态',
      purpose: '记录生活，保存回忆',
      required: false,
    },
    {
      name: '位置',
      description: '用于在日记中记录地点信息',
      purpose: '丰富日记内容',
      required: false,
    },
  ],
}

// ==================== 平台检测 ====================

/**
 * 检测是否为微信小程序
 */
function isWeixinMiniProgram(): boolean {
  // #ifdef MP-WEIXIN
  return true
  // #endif

  // #ifndef MP-WEIXIN
  return false
  // #endif
}

// ==================== 隐私协议管理 ====================

/**
 * 隐私协议管理器
 */
export class PrivacyManager {
  private config: PrivacyConfig
  private status: PrivacyStatus | null = null

  constructor(config: PrivacyConfig = DEFAULT_PRIVACY_CONFIG) {
    this.config = config
  }

  /**
   * 初始化，加载已保存的隐私状态
   */
  async init(): Promise<void> {
    try {
      const saved = uni.getStorageSync(PRIVACY_STORAGE_KEY)
      if (saved) {
        this.status = JSON.parse(saved)
      }
    } catch (e) {
      console.warn('[PrivacyManager] 加载隐私状态失败:', e)
    }
  }

  /**
   * 检查是否已同意隐私协议
   */
  async checkAgreed(): Promise<boolean> {
    if (!this.status) {
      await this.init()
    }

    // 检查版本是否匹配
    if (this.status && this.status.version === this.config.version) {
      return this.status.agreed
    }

    return false
  }

  /**
   * 获取隐私状态
   */
  getStatus(): PrivacyStatus {
    return this.status || { agreed: false }
  }

  /**
   * 同意隐私协议
   */
  async agree(): Promise<void> {
    this.status = {
      agreed: true,
      agreedAt: new Date().toISOString(),
      version: this.config.version,
    }

    try {
      uni.setStorageSync(PRIVACY_STORAGE_KEY, JSON.stringify(this.status))
    } catch (e) {
      console.error('[PrivacyManager] 保存隐私状态失败:', e)
    }
  }

  /**
   * 撤销同意
   */
  async revoke(): Promise<void> {
    this.status = { agreed: false }
    uni.removeStorageSync(PRIVACY_STORAGE_KEY)
  }

  /**
   * 获取隐私配置
   */
  getConfig(): PrivacyConfig {
    return this.config
  }

  /**
   * 显示隐私弹窗
   * 使用微信小程序隐私弹窗组件
   */
  showPrivacyPopup(): void {
    // #ifdef MP-WEIXIN
    // 微信小程序会自动显示隐私弹窗（在 app.json 中配置）
    // 这里可以主动触发
    console.log('[PrivacyManager] 触发隐私弹窗')
    // #endif
  }

  /**
   * 跳转到隐私协议页面
   */
  navigateToPrivacy(): void {
    uni.navigateTo({
      url: this.config.privacyUrl,
    })
  }

  /**
   * 跳转到用户协议页面
   */
  navigateToUserAgreement(): void {
    uni.navigateTo({
      url: this.config.userAgreementUrl,
    })
  }
}

// ==================== 内容安全检查 ====================

/**
 * 内容安全检查器
 * 使用微信小程序内容安全 API
 */
export class ContentSecurityChecker {
  /**
   * 检查文本内容
   * @param text 要检查的文本
   * @returns 检查结果
   */
  async checkText(text: string): Promise<ContentSecurityResult> {
    // #ifdef MP-WEIXIN
    try {
      return new Promise((resolve) => {
        wx.serviceMarket.invokeService({
          service: 'wxee446d047a0f7d09', // 内容安全服务 ID
          api: 'msgSecCheck',
          data: {
            content: text,
          },
          success: (res: any) => {
            const data = res.data
            resolve({
              pass: data.errcode === 0,
              type: 'text',
              riskLevel: this.parseRiskLevel(data.errcode),
              labels: data.label,
              suggestion: data.suggestion,
            })
          },
          fail: (err: any) => {
            console.error('[ContentSecurity] 文本检查失败:', err)
            // 检查失败时拒绝通过（符合微信小程序审核要求）
            // 宁可误拦，不可漏放
            resolve({
              pass: false,
              type: 'text',
              error: '内容安全检查服务暂时不可用，请稍后重试',
            })
          },
        })
      })
    } catch (e: any) {
      console.error('[ContentSecurity] 文本检查异常:', e)
      return {
        pass: false, // 异常时拒绝通过
        type: 'text',
        error: '内容安全检查异常，请稍后重试',
      }
    }
    // #endif

    // #ifndef MP-WEIXIN
    // 非微信小程序环境，调用服务端接口
    return this.checkTextByServer(text)
    // #endif
  }

  /**
   * 检查图片内容
   * @param filePath 图片路径
   * @returns 检查结果
   */
  async checkImage(filePath: string): Promise<ContentSecurityResult> {
    // #ifdef MP-WEIXIN
    try {
      return new Promise((resolve) => {
        wx.serviceMarket.invokeService({
          service: 'wxee446d047a0f7d09',
          api: 'imgSecCheck',
          data: {
            media: {
              contentType: 'image/*',
              value: filePath,
            },
          },
          success: (res: any) => {
            const data = res.data
            resolve({
              pass: data.errcode === 0,
              type: 'image',
              riskLevel: this.parseRiskLevel(data.errcode),
              labels: data.label,
              suggestion: data.suggestion,
            })
          },
          fail: (err: any) => {
            console.error('[ContentSecurity] 图片检查失败:', err)
            resolve({
              pass: true,
              type: 'image',
              error: err.errMsg || '图片安全检查失败',
            })
          },
        })
      })
    } catch (e: any) {
      return {
        pass: true,
        type: 'image',
        error: e.message || '检查异常',
      }
    }
    // #endif

    // #ifndef MP-WEIXIN
    return this.checkImageByServer(filePath)
    // #endif
  }

  /**
   * 通过服务端检查文本
   */
  private async checkTextByServer(text: string): Promise<ContentSecurityResult> {
    try {
      // 获取用户 Token
      const token = uni.getStorageSync('token')

      const res = await new Promise<any>((resolve, reject) => {
        uni.request({
          url: `${import.meta.env.VITE_API_BASE_URL}/content-security/check-text`,
          method: 'POST',
          header: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
          },
          data: { content: text },
          success: (res) => resolve(res),
          fail: (err) => reject(err),
        })
      })

      return {
        pass: res.data?.pass !== false,
        type: 'text',
        riskLevel: res.data?.riskLevel,
        labels: res.data?.labels,
        suggestion: res.data?.suggestion,
      }
    } catch (e: any) {
      return {
        pass: false, // 服务端检查失败时拒绝通过
        type: 'text',
        error: e.message || '服务端检查失败',
      }
    }
  }

  /**
   * 通过服务端检查图片
   */
  private async checkImageByServer(filePath: string): Promise<ContentSecurityResult> {
    try {
      const res = await new Promise<any>((resolve, reject) => {
        uni.uploadFile({
          url: `${import.meta.env.VITE_API_BASE_URL}/content-security/check-image`,
          filePath,
          name: 'media',
          success: (res) => resolve(res),
          fail: (err) => reject(err),
        })
      })

      const data = JSON.parse(res.data)
      return {
        pass: data.pass !== false,
        type: 'image',
        riskLevel: data.riskLevel,
        labels: data.labels,
        suggestion: data.suggestion,
      }
    } catch (e: any) {
      return {
        pass: true,
        type: 'image',
        error: e.message || '服务端检查失败',
      }
    }
  }

  /**
   * 解析风险等级
   */
  private parseRiskLevel(errcode: number): 'pass' | 'review' | 'reject' {
    switch (errcode) {
      case 0:
        return 'pass'
      case 87014: // 内容违规
        return 'reject'
      default:
        return 'review'
    }
  }
}

// ==================== 诱导分享检查 ====================

/**
 * 分享合规检查器
 * 检查内容是否包含诱导分享的违规内容
 */
export class ShareComplianceChecker {
  /** 违规关键词列表 */
  private violationKeywords = [
    '分享必中',
    '转发有奖',
    '邀请好友得',
    '分享到群',
    '转发到群',
    '分享朋友圈',
    '不转不',
    '转发送',
    '分享送',
    '邀请送',
    '转发获',
    '分享获',
    '必得红包',
    '免费领取',
    '点击领取',
    '快抢',
    '手慢无',
    '最后一天',
    '限时秒杀',
  ]

  /** 违规行为类型 */
  private violationPatterns = [
    /分[分享享转].*[奖励礼红包]/,
    /转[发发分享].*[奖励礼红包]/,
    /邀请.*[送得获]/,
    /分享.*群/,
    /转发.*群/,
  ]

  /**
   * 检查分享内容是否合规
   * @param content 分享内容
   * @returns 检查结果
   */
  check(content: string): ShareCheckResult {
    // 检查关键词
    for (const keyword of this.violationKeywords) {
      if (content.includes(keyword)) {
        return {
          compliant: false,
          reason: `包含违规关键词: "${keyword}"`,
          suggestion: '请移除诱导分享相关内容',
        }
      }
    }

    // 检查违规模式
    for (const pattern of this.violationPatterns) {
      if (pattern.test(content)) {
        return {
          compliant: false,
          reason: `内容包含诱导分享模式`,
          suggestion: '请确保分享内容不包含诱导性描述',
        }
      }
    }

    return { compliant: true }
  }

  /**
   * 检查分享按钮点击是否合规
   * 微信小程序要求用户主动触发分享
   */
  checkShareTrigger(isUserTrigger: boolean): boolean {
    return isUserTrigger
  }

  /**
   * 过滤违规内容
   * @param content 原内容
   * @returns 过滤后的内容
   */
  filter(content: string): string {
    let filtered = content

    for (const keyword of this.violationKeywords) {
      filtered = filtered.replace(new RegExp(keyword, 'g'), '*'.repeat(keyword.length))
    }

    return filtered
  }
}

// ==================== 青少年模式管理 ====================

/**
 * 青少年模式管理器
 */
export class MinorModeManager {
  private status: MinorModeStatus | null = null

  /**
   * 初始化
   */
  async init(): Promise<void> {
    try {
      const saved = uni.getStorageSync(MINOR_MODE_KEY)
      if (saved) {
        this.status = JSON.parse(saved)
      }
    } catch (e) {
      console.warn('[MinorModeManager] 加载状态失败:', e)
    }
  }

  /**
   * 获取状态
   */
  getStatus(): MinorModeStatus {
    return this.status || { enabled: false }
  }

  /**
   * 开启青少年模式
   */
  async enable(config: Partial<MinorModeStatus> = {}): Promise<void> {
    this.status = {
      enabled: true,
      timeLimit: config.timeLimit || 40, // 默认 40 分钟
      restTime: config.restTime || { start: '22:00', end: '06:00' },
      contentFilter: config.contentFilter || 'strict',
    }

    uni.setStorageSync(MINOR_MODE_KEY, JSON.stringify(this.status))
  }

  /**
   * 关闭青少年模式
   */
  async disable(): Promise<void> {
    this.status = { enabled: false }
    uni.setStorageSync(MINOR_MODE_KEY, JSON.stringify(this.status))
  }

  /**
   * 检查当前时间是否在休息时段
   */
  isInRestTime(): boolean {
    if (!this.status?.restTime) return false

    const now = new Date()
    const currentMinutes = now.getHours() * 60 + now.getMinutes()

    const [startHour, startMin] = this.status.restTime.start.split(':').map(Number)
    const [endHour, endMin] = this.status.restTime.end.split(':').map(Number)

    const startMinutes = startHour * 60 + startMin
    const endMinutes = endHour * 60 + endMin

    if (startMinutes > endMinutes) {
      // 跨天，如 22:00 - 06:00
      return currentMinutes >= startMinutes || currentMinutes < endMinutes
    } else {
      return currentMinutes >= startMinutes && currentMinutes < endMinutes
    }
  }

  /**
   * 检查今日使用时长是否超限
   */
  checkTimeLimit(usedMinutes: number): boolean {
    if (!this.status?.timeLimit) return true
    return usedMinutes < this.status.timeLimit
  }
}

// ==================== 统一导出 ====================

let privacyManager: PrivacyManager | null = null
let contentSecurityChecker: ContentSecurityChecker | null = null
let shareComplianceChecker: ShareComplianceChecker | null = null
let minorModeManager: MinorModeManager | null = null

/**
 * 获取隐私管理器实例
 */
export async function getPrivacyManager(): Promise<PrivacyManager> {
  if (!privacyManager) {
    privacyManager = new PrivacyManager()
    await privacyManager.init()
  }
  return privacyManager
}

/**
 * 获取内容安全检查器实例
 */
export function getContentSecurityChecker(): ContentSecurityChecker {
  if (!contentSecurityChecker) {
    contentSecurityChecker = new ContentSecurityChecker()
  }
  return contentSecurityChecker
}

/**
 * 获取分享合规检查器实例
 */
export function getShareComplianceChecker(): ShareComplianceChecker {
  if (!shareComplianceChecker) {
    shareComplianceChecker = new ShareComplianceChecker()
  }
  return shareComplianceChecker
}

/**
 * 获取青少年模式管理器实例
 */
export async function getMinorModeManager(): Promise<MinorModeManager> {
  if (!minorModeManager) {
    minorModeManager = new MinorModeManager()
    await minorModeManager.init()
  }
  return minorModeManager
}

/**
 * 快捷内容安全检查
 */
export async function checkContentSecurity(text: string): Promise<boolean> {
  const checker = getContentSecurityChecker()
  const result = await checker.checkText(text)
  return result.pass
}

/**
 * 快捷分享内容检查
 */
export function checkShareContent(content: string): boolean {
  const checker = getShareComplianceChecker()
  const result = checker.check(content)
  return result.compliant
}

// ==================== 导出 ====================

export default {
  getPrivacyManager,
  getContentSecurityChecker,
  getShareComplianceChecker,
  getMinorModeManager,
  checkContentSecurity,
  checkShareContent,
  PrivacyManager,
  ContentSecurityChecker,
  ShareComplianceChecker,
  MinorModeManager,
}
