import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// dev server (npm run dev) 与 preview server (npm run preview) 用同一份 proxy 设置
// 把 backend 反代到 /api/*，前端代码里可以始终用相对路径 fetch('/api/...')。
const proxy = {
  '/api':          { target: 'http://127.0.0.1:8000', changeOrigin: true },
  '/health':       { target: 'http://127.0.0.1:8000', changeOrigin: true },
  '/docs':         { target: 'http://127.0.0.1:8000', changeOrigin: true },
  '/redoc':        { target: 'http://127.0.0.1:8000', changeOrigin: true },
  '/openapi.json': { target: 'http://127.0.0.1:8000', changeOrigin: true },
}

export default defineConfig({
  plugins: [vue()],

  // 开发服务器：vite / npm run dev
  server: {
    host: true,       // 同时绑 IPv4 + IPv6，方便手机/同网设备访问
    port: 5173,
    strictPort: true, // 端口被占就报错而不是悄悄换端口
    proxy,
  },

  // 预览服务器：vite preview / npm run preview
  // 关键：Vite 不会把 server.proxy 自动应用到 preview，必须重复声明
  preview: {
    host: true,
    port: 4173,
    strictPort: true,
    proxy,
  },
})
