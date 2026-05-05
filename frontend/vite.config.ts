import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import { resolve } from 'path'

export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  // 开发服务器代理配置
  // 前端 VITE_API_BASE_URL=/api/v1 使用相对路径，需代理到后端
  server: {
    proxy: {
      // WebSocket 代理（私聊）
      '/api/v1/ws': {
        target: 'http://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
      // SSE 流式接口（AI 对话流式）
      '/api/v1/ai/chat/stream': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // 通用 API 代理
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  // CSS 预处理配置
  // 注意：Uni-app 会自动注入 uni.scss，无需额外配置 additionalData
  css: {
    preprocessorOptions: {
      scss: {
        // 使用旧版 API 避免警告
        api: 'modern-compiler',
        silenceDeprecations: [
          'legacy-js-api',
          'import',
          'global-builtin',
        ],
      },
    },
  },
})
