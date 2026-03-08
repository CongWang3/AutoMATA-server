import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  server: {
    // API代理配置
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    },
    // 修复WebSocket HMR连接问题
    hmr: {
      overlay: false // 禁用错误覆盖层减少干扰
    },
    // 优化开发服务器性能
    watch: {
      // 忽略大文件变化，提高监听性能
      ignored: ['**/uploaded_files/**', '**/logs/**', '**/node_modules/.vite/**']
    }
  },
  build: {
    // 生产环境优化
    rollupOptions: {
      output: {
        // 代码分割优化
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          'utils': ['axios', 'crypto-js']
        }
      }
    },
    // 启用压缩
    minify: 'terser'
  }
})
