/**
 * 回声 - Pinia Store 入口
 * 文件：src/stores/index.ts
 * 说明：统一导出所有 Store
 */

import { createPinia } from 'pinia'

const pinia = createPinia()

export default pinia

// 导出各模块 Store
export { useUserStore } from './user'
export { useSettingsStore } from './settings'
export { useChatStore } from './chat'
export { useDiaryStore } from './diary'
