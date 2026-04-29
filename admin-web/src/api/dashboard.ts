import { request } from '@/utils/request'
import type {
  OverviewStats,
  UserGrowthItem,
  UserGrowthParams,
  RetentionItem,
  RetentionParams,
  EmotionDistribution,
  AIServiceStats,
} from '@/types/dashboard'

// 获取概览统计数据
export function getOverviewStats(): Promise<OverviewStats> {
  return request.get('/api/admin/v1/dashboard/overview')
}

// 获取用户增长趋势
export function getUserGrowth(params?: UserGrowthParams): Promise<UserGrowthItem[]> {
  return request.get('/api/admin/v1/dashboard/users', params)
}

// 获取留存数据
export function getRetention(params?: RetentionParams): Promise<RetentionItem[]> {
  return request.get('/api/admin/v1/dashboard/retention', params)
}

// 获取情绪分布
export function getEmotionDistribution(): Promise<EmotionDistribution[]> {
  return request.get('/api/admin/v1/dashboard/emotion')
}

// 获取 AI 服务统计
export function getAIServiceStats(): Promise<AIServiceStats> {
  return request.get('/api/admin/v1/dashboard/ai')
}
