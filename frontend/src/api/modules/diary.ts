/**
 * 回声 - 日记接口
 * 文件：src/api/modules/diary.ts
 * 说明：情绪日记相关接口
 */

import api from '../index'

/** 创建日记 */
export function createDiary(data: {
  content: string
  emotion: string
  intensity: number
  date: string
}) {
  return api.post('/diary/create', data)
}

/** 获取日记列表 */
export function getDiaryList(page = 1, pageSize = 20) {
  return api.get('/diary/list', { page, pageSize })
}

/** 获取日记详情 */
export function getDiaryDetail(id: string) {
  return api.get(`/diary/${id}`)
}

/** 更新日记 */
export function updateDiary(id: string, data: { content?: string; emotion?: string; intensity?: number }) {
  return api.put(`/diary/${id}`, data)
}

/** 删除日记 */
export function deleteDiary(id: string) {
  return api.delete(`/diary/${id}`)
}

/** 获取日记统计（连续记录等） */
export function getDiaryStats() {
  return api.get('/diary/stats')
}
