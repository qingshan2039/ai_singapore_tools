import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 后端跨域问题已经在后端 .env CORS 里加了 5173；
    // 这里再加 proxy 让前端直接用相对路径 /api/* 也可以
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
