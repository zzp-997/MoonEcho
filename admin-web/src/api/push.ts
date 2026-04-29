import { request } from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  PushTaskItem,
  PushTaskDetail,
  CreatePushTaskRequest,
  PushTaskListParams,
  PushTaskStats,
  CancelPushTaskRequest,
  RetryPushTaskRequest,
} from '@/types/push'

// 获取推送任务列表
export function getPushTaskList(params?: PushTaskListParams): Promise<PaginatedResponse<PushTaskItem>> {
  return request.get('/api/admin/v1/push/tasks', params)
}

// 获取推送任务详情
export function getPushTaskDetail(taskId: string): Promise<PushTaskDetail> {
  return request.get(`/api/admin/v1/push/tasks/${taskId}`)
}

// 创建推送任务
export function createPushTask(data: CreatePushTaskRequest): Promise<PushTaskDetail> {
  return request.post('/api/admin/v1/push/tasks', data)
}

// 取消推送任务
export function cancelPushTask(taskId: string, data: CancelPushTaskRequest): Promise<PushTaskDetail> {
  return request.post(`/api/admin/v1/push/tasks/${taskId}/cancel`, data)
}

// 重试推送任务
export function retryPushTask(taskId: string, data?: RetryPushTaskRequest): Promise<PushTaskDetail> {
  return request.post(`/api/admin/v1/push/tasks/${taskId}/retry`, data)
}

// 获取推送任务统计
export function getPushTaskStats(): Promise<PushTaskStats> {
  return request.get('/api/admin/v1/push/tasks/stats')
}
