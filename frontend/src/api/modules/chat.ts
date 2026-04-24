/**
 * 回声 - 对话接口
 * 文件：src/api/modules/chat.ts
 * 说明：AI对话相关接口
 */

import api from '../index'
import type { SendMessageParams } from '@/types/chat'

/** 发送消息（SSE流式响应入口） */
export function sendMessage(params: SendMessageParams) {
  return api.post('/chat/send', params)
}

/** 获取对话历史 */
export function getChatHistory(sessionId: string, page = 1, pageSize = 50) {
  return api.get('/chat/history', { sessionId, page, pageSize })
}

/** 获取会话列表 */
export function getChatSessions() {
  return api.get('/chat/sessions')
}

/** 创建新会话 */
export function createChatSession(personalityType: string) {
  return api.post('/chat/sessions', { personalityType })
}

/** 删除会话 */
export function deleteChatSession(sessionId: string) {
  return api.delete(`/chat/sessions/${sessionId}`)
}
