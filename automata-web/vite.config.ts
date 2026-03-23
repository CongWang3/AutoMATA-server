import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // #region systematic-debugging instrumentation
    {
      name: 'debug-systematic-debugging-requests',
      configureServer(server) {
        server.middlewares.use((req, _res, next) => {
          try {
            const urlStr = req.url || ''
            const isTarget = urlStr.startsWith('/systematic-debugging')
            if (isTarget) {
              // 只记录必要字段；token 可能包含敏感信息，做红action
              const redactedUrl = urlStr.replace(/([?&]token=)[^&]*/g, '$1REDACTED')
              let uid = ''
              let t = ''
              const queryPart = urlStr.split('?')[1] || ''
              const params = new URLSearchParams(queryPart)
              uid = params.get('uid') || ''
              t = params.get('t') || ''

              //region agent log
              fetch('http://localhost:7618/ingest/6cda10c1-514a-4099-b96b-d25dcd87149d', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-Debug-Session-Id': 'd45b01',
                },
                body: JSON.stringify({
                  sessionId: 'd45b01',
                  runId: 'pre-fix',
                  hypothesisId: 'H1_vite_receives_systematic_debugging',
                  location: 'vite.config.ts:middlewares/systematic-debugging',
                  message: 'Vite received systematic-debugging request',
                  data: {
                    path: '/systematic-debugging*',
                    uid,
                    t,
                    hasToken: queryPart.includes('token='),
                    redactedUrl,
                  },
                  timestamp: Date.now(),
                }),
              }).catch(() => {})
              //endregion
            }
          } catch {
            // Never block dev server for debug logging.
          }
          next()
        })
      },
    },
    // #endregion
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
      }
      // 注意：/download 路径不代理，直接访问 8001 端口
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
