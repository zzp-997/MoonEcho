/**
 * 回声 - 青少年模式拦截组合式函数
 * 文件：src/composables/useMinorGuard.ts
 * 说明：检查用户 is_minor 状态，对受限功能进行拦截提示
 * 受限功能：treehole（树洞）、ai_sensitive（AI敏感话题）、chat_image（图片聊天）
 */

import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

/** 受限功能类型 */
export type RestrictedFeature = 'treehole' | 'ai_sensitive' | 'chat_image'

/** 受限功能名称映射 */
const FeatureNameMap: Record<RestrictedFeature, string> = {
  treehole: '树洞',
  ai_sensitive: 'AI敏感话题',
  chat_image: '图片聊天',
}

/** 受限功能列表（用于集中校验） */
const RESTRICTED_FEATURES: RestrictedFeature[] = ['treehole', 'ai_sensitive', 'chat_image']

export function useMinorGuard() {
  const userStore = useUserStore()

  /** 当前用户是否未成年 */
  const isMinor = computed(() => {
    // 根据年龄段判断是否未成年
    const ageRange = userStore.userInfo?.ageRange
    if (ageRange === 'under_18') {
      return true
    }
    return false
  })

  /**
   * 检查功能是否被限制
   * @param feature 功能类型
   * @returns 是否被限制（true = 被限制，false = 不受限）
   */
  function isRestricted(feature: RestrictedFeature): boolean {
    return isMinor.value && RESTRICTED_FEATURES.includes(feature)
  }

  /**
   * 拦截检查 - 如果受限则显示提示
   * @param feature 功能类型
   * @returns 是否通过检查（true = 可使用，false = 被拦截）
   */
  function checkAccess(feature: RestrictedFeature): boolean {
    if (isRestricted(feature)) {
      const featureName = FeatureNameMap[feature]
      uni.showModal({
        title: '提示',
        content: '青少年模式下无法使用此功能',
        showCancel: false,
        confirmText: '我知道了',
      })
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
   * 获取所有受限功能列表
   * @returns 当前用户被限制的功能数组
   */
  function getRestrictedFeatures(): RestrictedFeature[] {
    if (!isMinor.value) return []
    return [...RESTRICTED_FEATURES]
  }

  return {
    isMinor,
    isRestricted,
    checkAccess,
    canAccess,
    getRestrictedFeatures,
  }
}
