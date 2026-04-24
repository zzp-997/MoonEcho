/**
 * 回声 - 情绪类型定义
 * 文件：src/types/emotion.d.ts
 * 说明：情绪相关类型声明
 */

/** 情绪枚举值 */
export type EmotionType = 'warm' | 'calm' | 'low' | 'sad' | 'chaos'

/** 情绪信息 */
export interface EmotionInfo {
  /** 情绪类型 */
  type: EmotionType
  /** 情绪名称 */
  name: string
  /** 情绪描述 */
  description: string
  /** 对应色值CSS变量名 */
  colorVar: string
  /** 对应背景色CSS变量名 */
  bgColorVar: string
  /** 对应图标 */
  icon: string
  /** 情绪强度 1-5 */
  intensity?: number
}

/** 情绪映射表 */
export const EmotionMap: Record<EmotionType, EmotionInfo> = {
  warm: {
    type: 'warm',
    name: '愉悦',
    description: '充满能量、开心',
    colorVar: '--mood-warm',
    bgColorVar: '--mood-warm-bg',
    icon: 'sun',
  },
  calm: {
    type: 'calm',
    name: '平静',
    description: '平静、安稳',
    colorVar: '--mood-calm',
    bgColorVar: '--mood-calm-bg',
    icon: 'leaf',
  },
  low: {
    type: 'low',
    name: '低落',
    description: '低落、沉闷',
    colorVar: '--mood-low',
    bgColorVar: '--mood-low-bg',
    icon: 'cloud',
  },
  sad: {
    type: 'sad',
    name: '难过',
    description: '难过、忧伤',
    colorVar: '--mood-sad',
    bgColorVar: '--mood-sad-bg',
    icon: 'cloud-rain',
  },
  chaos: {
    type: 'chaos',
    name: '崩溃',
    description: '崩溃、混乱',
    colorVar: '--mood-chaos',
    bgColorVar: '--mood-chaos-bg',
    icon: 'zap',
  },
}
