/**
 * 回声 - 青少年模式拦截组合式函数
 * 文件：src/composables/useMinorGuard.ts
 * 说明：检查用户 is_minor 状态，对受限功能进行拦截提示
 * 功能增强（T016）：
 *   - 受限功能：treehole（树洞）、ai_sensitive（AI敏感话题）、chat_image（图片聊天）
 *   - 前端侧预判：青少年用户进入受限页面时直接拦截（无需等后端返回错误）
 *   - 后端 USER_UNDERAGE 错误码统一处理
 *   - 拦截后显示提示"青少年模式下无法使用此功能"并阻止页面渲染
 */

import { computed, ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import { track, EventName } from '@/utils/tracking'

// ==================== 常量 ====================

/** 受限功能类型 */
export type RestrictedFeature = 'treehole' | 'ai_sensitive' | 'chat_image' | 'dynamic_publish' | 'private_chat_image'

/** 受限页面路径 */
export const RESTRICTED_PAGES: Record<RestrictedFeature, string[]> = {
  treehole: ['/pages/treehole/index', '/pages/treehole/publish'],
  ai_sensitive: ['/pages/chat/index'],
  chat_image: ['/pages/message/index'],
  dynamic_publish: ['/pages/community/publish', '/pages/community/edit'],
  private_chat_image: ['/pages/message/index'],
}

/** 受限功能名称映射 */
const FeatureNameMap: Record<RestrictedFeature, string> = {
  treehole: '树洞',
  ai_sensitive: 'AI敏感话题',
  chat_image: '图片聊天',
  dynamic_publish: '动态发布',
  private_chat_image: '私聊图片',
}

/** 受限功能列表（用于集中校验） */
const RESTRICTED_FEATURES: RestrictedFeature[] = ['treehole', 'ai_sensitive', 'chat_image']

/** 拦截提示文案 */
const INTERCEPT_MESSAGE = '青少年模式下无法使用此功能'

/** 青少年模式时长限制配置 */
const TEEN_MODE_TIME_LIMITS = {
  /** 每日使用时长上限（分钟） */
  dailyMaxMinutes: 120,
  /** 22:00 后禁止使用 */
  nightBanHour: 22,
  /** 提前提醒时间（分钟） */
  warnBeforeMinutes: 5,
}

// ==================== 组合式函数 ====================

export function useMinorGuard() {
  const userStore = useUserStore()
  const settingsStore = useSettingsStore()

  // ==================== 响应式状态 ====================

  /** 是否正在显示拦截提示 */
  const showingInterceptDialog = ref(false)

  /** 当前拦截的功能 */
  const interceptedFeature = ref<RestrictedFeature | null>(null)

  // ==================== 计算属性 ====================

  /** 当前用户是否未成年 */
  const isMinor = computed(() => {
    // 根据年龄段判断是否未成年
    const ageRange = userStore.userInfo?.ageRange
    if (ageRange === 'under_18') {
      return true
    }
    // 如果 is_minor 标记为 true
    if (userStore.userInfo?.is_minor === true) {
      return true
    }
    return false
  })

  /** 是否启用青少年模式 */
  const isTeenModeEnabled = computed(() => {
    return settingsStore.isTeenMode || isMinor.value
  })

  /** 今日已使用时长（分钟） */
  const todayUsedMinutes = computed(() => {
    // 从 settings 中获取或计算
    return settingsStore.settings?.teenUsedMinutes || 0
  })

  /** 是否超过每日时长限制 */
  const isOverDailyLimit = computed(() => {
    if (!isTeenModeEnabled.value) return false
    return todayUsedMinutes.value >= TEEN_MODE_TIME_LIMITS.dailyMaxMinutes
  })

  /** 是否在禁止时段（22:00后） */
  const isInNightBanPeriod = computed(() => {
    if (!isTeenModeEnabled.value) return false
    const hour = new Date().getHours()
    return hour >= TEEN_MODE_TIME_LIMITS.nightBanHour
  })

  /** 是否需要显示时段提醒 */
  const needShowTimeWarning = computed(() => {
    if (!isTeenModeEnabled.value) return false
    const hour = new Date().getHours()
    const minutes = new Date().getMinutes()

    // 21:55 - 22:00 之间提醒
    if (hour === TEEN_MODE_TIME_LIMITS.nightBanHour - 1 && minutes >= 55) {
      return true
    }
    return false
  })

  // ==================== 方法 ====================

  /**
   * 检查功能是否被限制
   * @param feature 功能类型
   * @returns 是否被限制（true = 被限制，false = 不受限）
   */
  function isRestricted(feature: RestrictedFeature): boolean {
    return isTeenModeEnabled.value && RESTRICTED_FEATURES.includes(feature)
  }

  /**
   * 拦截检查 - 如果受限则显示提示
   * @param feature 功能类型
   * @returns 是否通过检查（true = 可使用，false = 被拦截）
   */
  function checkAccess(feature: RestrictedFeature): boolean {
    if (isRestricted(feature)) {
      showInterceptDialog(feature)
      return false
    }
    return true
  }

  /**
   * 静默检查（不弹提示）
   * @param feature 功能类型
   * @returns 是否通过检查
   */
  function canAccess(feature: RestrictedFeature): boolean {
    return !isRestricted(feature)
  }

  /**
   * 页面级拦截检查
   * 在受限页面的 onShow 中调用
   * @param pagePath 当前页面路径
   * @returns 是否允许访问
   */
  function pageGuard(pagePath: string): boolean {
    if (!isTeenModeEnabled.value) return true

    // 检查是否为受限页面
    for (const [feature, paths] of Object.entries(RESTRICTED_PAGES)) {
      if (paths.some(p => pagePath.includes(p))) {
        if (isRestricted(feature as RestrictedFeature)) {
          showInterceptDialog(feature as RestrictedFeature)
          return false
        }
      }
    }

    // 检查时段限制
    if (isInNightBanPeriod.value) {
      showNightBanDialog()
      return false
    }

    // 检查时长限制
    if (isOverDailyLimit.value) {
      showDailyLimitDialog()
      return false
    }

    return true
  }

  /**
   * 显示拦截提示弹窗
   */
  function showInterceptDialog(feature: RestrictedFeature): void {
    interceptedFeature.value = feature
    showingInterceptDialog.value = true

    const featureName = FeatureNameMap[feature]

    // 埋点
    track(EventName.TEEN_MODE_ENABLE, {
      action: 'intercept',
      feature: featureName,
    })

    uni.showModal({
      title: '提示',
      content: INTERCEPT_MESSAGE,
      showCancel: false,
      confirmText: '我知道了',
      success: () => {
        showingInterceptDialog.value = false
        interceptedFeature.value = null

        // 返回上一页或首页
        const pages = getCurrentPages()
        if (pages.length > 1) {
          uni.navigateBack()
        } else {
          uni.switchTab({ url: '/pages/home/index' })
        }
      },
    })
  }

  /**
   * 显示夜间禁止时段弹窗
   */
  function showNightBanDialog(): void {
    uni.showModal({
      title: '休息时间',
      content: '现在是睡觉时间了，好好休息吧。明天再来聊天！',
      showCancel: false,
      confirmText: '我知道了',
      success: () => {
        // 返回首页
        uni.switchTab({ url: '/pages/home/index' })
      },
    })
  }

  /**
   * 显示每日时长限制弹窗
   */
  function showDailyLimitDialog(): void {
    uni.showModal({
      title: '使用时长提醒',
      content: `今天已经使用${todayUsedMinutes.value}分钟了，休息一下眼睛和大脑吧。`,
      showCancel: false,
      confirmText: '我知道了',
      success: () => {
        // 返回首页
        uni.switchTab({ url: '/pages/home/index' })
      },
    })
  }

  /**
   * 显示时段临近提醒（不强制退出）
   */
  function showTimeWarning(): void {
    if (!needShowTimeWarning.value) return

    uni.showToast({
      title: `还有${TEEN_MODE_TIME_LIMITS.warnBeforeMinutes}分钟就到睡觉时间了，准备好休息吧`,
      icon: 'none',
      duration: 3000,
    })
  }

  /**
   * 获取所有受限功能列表
   * @returns 当前用户被限制的功能数组
   */
  function getRestrictedFeatures(): RestrictedFeature[] {
    if (!isTeenModeEnabled.value) return []
    return [...RESTRICTED_FEATURES]
  }

  /**
   * 处理后端 USER_UNDERAGE 错误码
   * 在请求拦截器中调用
   */
  function handleUnderageError(): void {
    showInterceptDialog('treehole')
  }

  /**
   * 更新今日使用时长
   * @param minutes 新增分钟数
   */
  function updateUsedMinutes(minutes: number): void {
    if (!settingsStore.settings) {
      console.warn('settingsStore.settings 未初始化')
      return
    }
    const total = todayUsedMinutes.value + minutes
    settingsStore.settings.teenUsedMinutes = total
    // 保存到本地
    uni.setStorageSync('huisheng_settings', JSON.stringify(settingsStore.settings))
  }

  /**
   * 重置今日使用时长（每天零点调用）
   */
  function resetDailyUsage(): void {
    if (!settingsStore.settings) {
      console.warn('settingsStore.settings 未初始化')
      return
    }
    settingsStore.settings.teenUsedMinutes = 0
    uni.setStorageSync('huisheng_settings', JSON.stringify(settingsStore.settings))
  }

  // ==================== 生命周期 ====================

  onMounted(() => {
    // 检查是否需要重置使用时长
    const lastResetDate = uni.getStorageSync('huisheng_teen_usage_reset_date')
    const today = new Date().toISOString().split('T')[0]

    if (lastResetDate !== today) {
      resetDailyUsage()
      uni.setStorageSync('huisheng_teen_usage_reset_date', today)
    }

    // 显示时段临近提醒
    showTimeWarning()
  })

  return {
    // 状态
    isMinor,
    isTeenModeEnabled,
    showingInterceptDialog,
    interceptedFeature,
    todayUsedMinutes,
    isOverDailyLimit,
    isInNightBanPeriod,
    needShowTimeWarning,

    // 方法
    isRestricted,
    checkAccess,
    canAccess,
    pageGuard,
    showInterceptDialog,
    showNightBanDialog,
    showDailyLimitDialog,
    showTimeWarning,
    getRestrictedFeatures,
    handleUnderageError,
    updateUsedMinutes,
    resetDailyUsage,
  }
}

// ==================== 导出辅助函数 ====================

/**
 * 检查页面是否需要青少年模式拦截
 * 用于页面级别的快速判断
 */
export function checkPageMinorRestriction(pagePath: string): boolean {
  const userStore = useUserStore()
  const settingsStore = useSettingsStore()

  // 检查是否为青少年模式
  const ageRange = userStore.userInfo?.ageRange
  const isMinor = ageRange === 'under_18' || userStore.userInfo?.is_minor === true
  const isTeenModeEnabled = settingsStore.isTeenMode || isMinor

  if (!isTeenModeEnabled) return true

  // 检查是否为受限页面
  for (const [feature, paths] of Object.entries(RESTRICTED_PAGES)) {
    if (paths.some(p => pagePath.includes(p))) {
      if (RESTRICTED_FEATURES.includes(feature as RestrictedFeature)) {
        return false
      }
    }
  }

  return true
}