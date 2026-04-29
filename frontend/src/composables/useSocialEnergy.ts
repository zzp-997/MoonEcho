/**
 * 回声 - 社交能量组合式函数
 * 文件：src/composables/useSocialEnergy.ts
 * 说明：社交能量状态管理，支持能量可视化、活动记录、AI建议
 */

import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import {
  getSocialEnergy,
  restSocialEnergy,
  type SocialEnergy,
  type SocialActivity,
  getActivityEnergyText,
} from '@/api/modules/chat'
import { track, EventName } from '@/utils/tracking'

// ==================== 响应式状态 ====================

/** 社交能量数据 */
const energyData = ref<SocialEnergy | null>(null)

/** 是否正在加载 */
const isLoading = ref(false)

/** 是否正在休息 */
const isResting = ref(false)

/** 休息结束时间 */
const restEndTime = ref<string | null>(null)

/** 最后更新时间 */
const lastUpdateTime = ref<number>(0)

/** 缓存有效期（毫秒） */
const CACHE_DURATION = 60000 // 1分钟

// ==================== 组合式函数 ====================

export function useSocialEnergy() {
  const userStore = useUserStore()

  // ==================== 计算属性 ====================

  /** 当前能量百分比 */
  const energyPercent = computed(() => {
    if (!energyData.value) return 0
    return Math.round((energyData.value.current_energy / energyData.value.max_energy) * 100)
  })

  /** 能量条显示 */
  const energyBars = computed(() => {
    const percent = energyPercent.value
    const bars: { filled: boolean; percent: number }[] = []
    const barCount = 5
    const perBar = 20

    for (let i = 0; i < barCount; i++) {
      const barPercent = i * perBar
      bars.push({
        filled: percent > barPercent,
        percent: Math.min(100, Math.max(0, percent - barPercent)),
      })
    }

    return bars
  })

  /** 能量状态文本 */
  const energyStatusText = computed(() => {
    if (!energyData.value) return '加载中...'
    return getActivityEnergyText(energyData.value)
  })

  /** 能量颜色 */
  const energyColor = computed(() => {
    const percent = energyPercent.value
    if (percent >= 80) return 'var(--color-success)'
    if (percent >= 60) return 'var(--mood-calm)'
    if (percent >= 40) return 'var(--mood-warm)'
    if (percent >= 20) return 'var(--color-warning)'
    return 'var(--color-error)'
  })

  /** 是否正在休息（ref形式，可修改） */
  const isInRest = ref(false)

  /** 计算属性：根据结束时间判断是否在休息 */
  const isInRestByTime = computed(() => {
    if (!restEndTime.value) return false
    const endTime = new Date(restEndTime.value)
    return endTime > new Date()
  })

  /** 休息剩余时间（秒） */
  const restRemainingSeconds = computed(() => {
    if (!restEndTime.value) return 0
    const endTime = new Date(restEndTime.value)
    const remaining = Math.floor((endTime.getTime() - Date.now()) / 1000)
    return Math.max(0, remaining)
  })

  /** 最近活动列表 */
  const recentActivities = computed(() => {
    if (!energyData.value?.activities) return []
    return energyData.value.activities.slice(0, 5)
  })

  /** AI 建议 */
  const aiSuggestion = computed(() => {
    if (!energyData.value?.suggestion) return ''
    return energyData.value.suggestion
  })

  /** 是否需要刷新 */
  const needsRefresh = computed(() => {
    return Date.now() - lastUpdateTime.value > CACHE_DURATION
  })

  // ==================== 方法 ====================

  /**
   * 加载社交能量数据
   */
  async function loadEnergy(force = false): Promise<void> {
    if (!userStore.isLoggedIn) return

    if (!force && !needsRefresh.value && energyData.value) {
      return
    }

    if (isLoading.value) return

    isLoading.value = true

    try {
      const response = await getSocialEnergy()
      energyData.value = response.energy
      lastUpdateTime.value = Date.now()

      track(EventName.SOCIAL_ENERGY_VIEW, {
        energy_percent: energyPercent.value,
        activity_count: response.energy.activities.length,
      })
    } catch (error) {
      console.error('获取社交能量失败', error)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 主动休息
   * @param durationMinutes 休息时长（分钟）- 注意：当前后端不支持自定义时长
   */
  async function startRest(durationMinutes = 30): Promise<boolean> {
    if (isResting.value) return false

    isResting.value = true

    try {
      // 注意：当前 API 不支持自定义时长，后端会返回默认的休息结束时间
      const response = await restSocialEnergy()

      if (response.success) {
        restEndTime.value = response.rest_until || null
        isResting.value = false
        isInRest.value = true  // 现在 isInRest 是 ref，可以赋值

        track(EventName.SOCIAL_ENERGY_REST, {
          duration_minutes: durationMinutes,
        })

        uni.showToast({
          title: '已进入休息模式',
          icon: 'success',
        })

        return true
      }

      return false
    } catch (error) {
      console.error('开始休息失败', error)
      isResting.value = false
      return false
    }
  }

  /**
   * 格式化活动时间
   */
  function formatActivityTime(activity: SocialActivity): string {
    if (!activity.created_at) return ''

    try {
      const date = new Date(activity.created_at)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / (1000 * 60))
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`

      return '今天'
    } catch {
      return ''
    }
  }

  /**
   * 格式化休息剩余时间
   */
  function formatRestTime(seconds: number): string {
    if (seconds <= 0) return ''

    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}小时${mins}分钟`
    }

    return `${mins}分钟`
  }

  /**
   * 获取活动图标
   */
  function getActivityIcon(type: SocialActivity['type']): string {
    const iconMap: Record<SocialActivity['type'], string> = {
      message_sent: '',
      message_reply: '',
      friend_request: '',
      post_created: '',
      comment_created: '',
    }
    return iconMap[type] || ''
  }

  // ==================== 生命周期 ====================

  onMounted(() => {
    if (userStore.isLoggedIn) {
      loadEnergy()
    }
  })

  return {
    // 状态
    energyData,
    energyPercent,
    energyBars,
    energyStatusText,
    energyColor,
    isLoading,
    isResting,
    isInRest,
    isInRestByTime,
    restRemainingSeconds,
    recentActivities,
    aiSuggestion,

    // 方法
    loadEnergy,
    startRest,
    formatActivityTime,
    formatRestTime,
    getActivityIcon,
  }
}