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
  // CSS 预处理配置
  // 注意：Uni-app 会自动注入 uni.scss，无需额外配置 additionalData
  css: {
    preprocessorOptions: {
      scss: {
        // 使用旧版 API 避免警告
        api: 'modern-compiler',
        silenceDeprecations: ['legacy-js-api'],
      },
    },
  },
})
