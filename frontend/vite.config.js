import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// 判断是否为生产环境
const isProduction = process.env.NODE_ENV === 'production'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',  // 监听所有网络接口，允许外部访问
    port: 5173,
    allowedHosts: [
      'localhost',
      'ocrtranslate.quirkymeowcorner.fun',  // 允许你的域名
      '.quirkymeowcorner.fun',  // 允许所有子域名
    ],
    proxy: {
      '/api': {
        // 本地开发用 8000，生产环境用 32546
        target: isProduction ? 'http://localhost:32546' : 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
