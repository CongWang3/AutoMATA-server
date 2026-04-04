import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [ElementPlusResolver()],
      dirs: ['src/components'],
      extensions: ['vue'],
      deep: true,
      dts: true
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  server: {
    host: '0.0.0.0', // 绑定到所有网络接口
    // API代理配置
    proxy: {
      '/api': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        secure: false,
        // 允许 /api 下的 WebSocket（如 /api/v1/tasks/ws/status）
        ws: true,
        // 增加超时时间，防止代理超时
        timeout: 120000,  // 2分钟
        // 配置代理错误处理，防止崩溃
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.error('[Vite Proxy Error]', err.message)
            // 返回错误响应而不是崩溃
            if (res && !res.headersSent) {
              res.writeHead(502, { 'Content-Type': 'application/json' })
              res.end(JSON.stringify({ error: 'Proxy error', message: err.message }))
            }
          })
        }
      },
      // WebSocket代理配置
      '/ws': {
        target: 'ws://localhost:8005',
        ws: true,
        changeOrigin: true
      },
      // 开发环境：后端在 DEBUG 且默认 DOWNLOAD_PUBLIC_BASE_URL 时返回同源相对路径，由此反代到独立下载服务
      '/job-result': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/download': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/analysis-result': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      // 与 getDownloadOrigin() 同源；public/example 下有的文件仍由 Vite 静态优先
      '/example': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
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
