/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_WS_BASE_URL?: string
  readonly VITE_WEBSOCKET_URL?: string
  readonly VITE_DIRECT_API?: string
  readonly VITE_DOWNLOAD_ORIGIN?: string
  /** 开发时直连 API 用的 HTTP 根（无 /api），如 http://127.0.0.1:8005 */
  readonly VITE_DEV_API_ORIGIN?: string
  /** 开发时直连用 WebSocket 根，如 ws://127.0.0.1:8005 */
  readonly VITE_DEV_WS_ORIGIN?: string
  /** Vite 开发代理目标，默认 http://127.0.0.1:8005 */
  readonly VITE_DEV_PROXY_API?: string
  readonly VITE_DEV_PROXY_WS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
