/**
 * 回声 - 危机干预组合式函数
 * 文件：src/composables/useCrisis.ts
 * 说明：处理危机干预 UI 逻辑，检测 crisis_level 并触发弹窗
 * 参考：PRD.md 模块2 - AI 陪伴好友 - 危机干预机制
 */

import { ref, computed } from 'vue'

// ==================== 常量定义 ====================

/** 求助热线列表 */
export const CRISIS_HOTLINES = [
  {
    name: '希望24热线',
    number: '400-161-9995',
    description: '24小时心理援助热线',
  },
  {
    name: '北京心理危机研究与干预中心',
    number: '010-82951332',
    description: '北京市心理援助热线',
  },
  {
    name: '全国心理援助热线',
    number: '400-161-9995',
    description: '全国心理援助服务',
  },
] as const

/** 危机等级枚举 */
export type CrisisLevel = 'low' | 'medium' | 'high'

/** 安慰语模板 */
const COMFORT_MESSAGES: Record<CrisisLevel, string> = {
  low: '我感受到了你的情绪，记住，任何时候都有人在乎你。',
  medium: '我注意到你似乎正在经历一些困难。请记住，寻求帮助是勇敢的表现。如果你愿意，可以和信任的人聊聊，或者拨打下面的热线电话。',
  high: '我非常关心你现在的状态。如果你正在经历艰难时刻，请一定要寻求帮助。你值得被关爱，专业的帮助一定能让你感受到更好。',
}

// ==================== 组合式函数 ====================

/**
 * 危机干预组合式函数
 */
export function useCrisis() {
  /** 是否显示危机干预弹窗 */
  const showDialog = ref(false)

  /** 当前危机等级 */
  const crisisLevel = ref<CrisisLevel | null>(null)

  /** 触发危机的关键词 */
  const crisisKeywords = ref<string[]>([])

  /** 是否已经显示过（同一会话内） */
  const hasShownInSession = ref(false)

  /** 当前安慰语 */
  const comfortMessage = computed(() => {
    if (!crisisLevel.value) return ''
    return COMFORT_MESSAGES[crisisLevel.value]
  })

  /** 是否为高危等级 */
  const isHighRisk = computed(() => crisisLevel.value === 'high')

  /**
   * 处理危机检测
   * @param level 危机等级
   * @param keywords 触发关键词
   */
  function handleCrisis(level: CrisisLevel, keywords?: string[]): void {
    // 只处理 medium 和 high 等级
    if (level === 'low') {
      return
    }

    // 同一会话内不重复显示
    if (hasShownInSession.value) {
      return
    }

    crisisLevel.value = level
    crisisKeywords.value = keywords || []
    showDialog.value = true
    hasShownInSession.value = true

    // 追踪事件
    trackCrisisEvent(level, keywords)
  }

  /**
   * 关闭弹窗
   */
  function closeDialog(): void {
    showDialog.value = false
  }

  /**
   * 确认已联系帮助
   */
  function confirmGetHelp(): void {
    showDialog.value = false
    // 可以在这里添加后续逻辑，如推荐其他资源
  }

  /**
   * 拨打热线电话
   */
  function callHotline(number: string): void {
    uni.makePhoneCall({
      phoneNumber: number,
      success: () => {
        trackCrisisEvent('hotline_called', [number])
      },
      fail: (err) => {
        console.error('拨打电话失败', err)
        // 对于 H5 等不支持拨打的平台，复制号码
        uni.setClipboardData({
          data: number,
          success: () => {
            uni.showToast({
              title: '号码已复制',
              icon: 'success',
            })
          },
        })
      },
    })
  }

  /**
   * 复制热线号码
   */
  function copyHotline(number: string): void {
    uni.setClipboardData({
      data: number,
      success: () => {
        uni.showToast({
          title: '号码已复制',
          icon: 'success',
        })
      },
    })
  }

  /**
   * 重置会话状态
   * 在开始新对话时调用
   */
  function resetSession(): void {
    showDialog.value = false
    crisisLevel.value = null
    crisisKeywords.value = []
    hasShownInSession.value = false
  }

  /**
   * 追踪危机事件
   */
  function trackCrisisEvent(level: string, keywords?: string[]): void {
    try {
      // 集成埋点系统
      console.log('[Crisis]', '检测到危机事件', {
        level,
        keywords,
        timestamp: new Date().toISOString(),
      })
    } catch (e) {
      console.error('[Crisis] 追踪事件失败', e)
    }
  }

  return {
    // 状态
    showDialog,
    crisisLevel,
    crisisKeywords,
    comfortMessage,
    isHighRisk,
    hasShownInSession,
    // 方法
    handleCrisis,
    closeDialog,
    confirmGetHelp,
    callHotline,
    copyHotline,
    resetSession,
    // 常量
    CRISIS_HOTLINES,
  }
}
