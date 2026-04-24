/**
 * 回声 - 应用主入口
 * 文件：src/main.ts
 * 说明：Vue 应用挂载、Pinia 初始化、全局配置
 */
import { createSSRApp } from 'vue'
import App from './App.vue'
import pinia from './stores'

// 创建 SSR 应用实例
export function createApp() {
  const app = createSSRApp(App)

  // 使用 Pinia 状态管理
  app.use(pinia)

  return {
    app,
  }
}
