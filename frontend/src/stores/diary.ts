/**
 * 回声 - 日记状态管理
 * 文件：src/stores/diary.ts
 * 说明：情绪日记状态、本地缓存、同步管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 情绪日记接口 */
export interface DiaryEntry {
  id: string
  /** 日记内容 */
  content: string
  /** 情绪标签 */
  emotion: string
  /** 情绪强度 1-5 */
  intensity: number
  /** 创建日期 YYYY-MM-DD */
  date: string
  /** 创建时间 */
  createdAt: string
  /** 更新时间 */
  updatedAt: string
  /** 是否已同步 */
  synced: boolean
  /** AI评论内容 */
  aiComment?: string
}

/** 日记存储键 */
const DIARY_KEY = 'huisheng_diaries'

export const useDiaryStore = defineStore('diary', () => {
  // ==================== 状态 ====================

  /** 日记列表 */
  const diaries = ref<DiaryEntry[]>([])

  // ==================== 计算属性 ====================

  /** 今日是否已记录日记 */
  const hasTodayDiary = computed(() => {
    const today = new Date().toISOString().split('T')[0]
    return diaries.value.some((d) => d.date === today)
  })

  /** 连续记录天数 */
  const streakDays = computed(() => {
    if (diaries.value.length === 0) return 0

    const dates = [...new Set(diaries.value.map((d) => d.date))].sort().reverse()
    let streak = 0
    const today = new Date()

    for (let i = 0; i < dates.length; i++) {
      const checkDate = new Date(today)
      checkDate.setDate(checkDate.getDate() - i)
      const checkDateStr = checkDate.toISOString().split('T')[0]

      if (dates.includes(checkDateStr)) {
        streak++
      } else {
        break
      }
    }

    return streak
  })

  /** 7日连续记录率 */
  const weeklyStreakRate = computed(() => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - i)
      return date.toISOString().split('T')[0]
    })
    const recorded = last7Days.filter((d) =>
      diaries.value.some((diary) => diary.date === d)
    ).length
    return recorded / 7
  })

  // ==================== 方法 ====================

  /**
   * 初始化日记数据
   */
  function init() {
    try {
      const saved = uni.getStorageSync(DIARY_KEY)
      if (saved) {
        diaries.value = JSON.parse(saved)
      }
    } catch (e) {
      console.error('初始化日记数据失败', e)
    }
  }

  /**
   * 保存日记到本地
   */
  function saveToLocal() {
    uni.setStorageSync(DIARY_KEY, JSON.stringify(diaries.value))
  }

  /**
   * 添加日记
   */
  function addDiary(diary: DiaryEntry) {
    diaries.value.unshift(diary)
    saveToLocal()
  }

  /**
   * 更新日记
   */
  function updateDiary(id: string, updates: Partial<DiaryEntry>) {
    const index = diaries.value.findIndex((d) => d.id === id)
    if (index !== -1) {
      diaries.value[index] = { ...diaries.value[index], ...updates }
      saveToLocal()
    }
  }

  /**
   * 删除日记
   */
  function deleteDiary(id: string) {
    diaries.value = diaries.value.filter((d) => d.id !== id)
    saveToLocal()
  }

  /**
   * 获取指定日期的日记
   */
  function getDiaryByDate(date: string): DiaryEntry | undefined {
    return diaries.value.find((d) => d.date === date)
  }

  // ==================== 初始化 ====================

  init()

  return {
    // 状态
    diaries,
    // 计算属性
    hasTodayDiary,
    streakDays,
    weeklyStreakRate,
    // 方法
    addDiary,
    updateDiary,
    deleteDiary,
    getDiaryByDate,
  }
})
