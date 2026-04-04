/**
 * 部署相关运行时配置（通过 Vite 环境变量注入，见 .env.development / .env.production）
 */

/** 去掉尾部斜杠 */
function trimTrailingSlash(s: string): string {
  return s.replace(/\/+$/, '')
}

function devApiBaseFromEnv(): string {
  const origin = (import.meta.env.VITE_DEV_API_ORIGIN || '').trim().replace(/\/+$/, '')
  if (origin) {
    return `${origin}/api`
  }
  return 'http://127.0.0.1:8005/api'
}

/**
 * 与 Axios 客户端一致的 HTTP API 根路径（如 `/api` 或 `https://host/api`）
 */
export function getApiBaseUrl(): string {
  const explicit = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
  if (explicit) {
    return explicit
  }
  if (import.meta.env.VITE_DIRECT_API === 'true') {
    return devApiBaseFromEnv()
  }
  return '/api'
}

/**
 * 是否走浏览器同源 + Vite（或网关）代理：此时 WS 必须与页面同源，不能再用孤立的 VITE_WS_BASE_URL。
 */
export function isProxiedApiMode(): boolean {
  if (import.meta.env.VITE_DIRECT_API === 'true') {
    return false
  }
  const api = getApiBaseUrl()
  return api === '' || api.startsWith('/')
}

/**
 * 下载链接使用的「站点根」URL（无路径、无尾斜杠）。
 * 开发环境在浏览器内默认与当前页同源（如 IDE 把远程 5173 转到本机 localhost:5173 时，下载走同源 + Vite 反代，无需再映射远程 8001 到本机 8001）。
 * 可设 VITE_DOWNLOAD_ORIGIN 覆盖；无 window 时（非浏览器）回退 127.0.0.1:8001。
 */
export function getDownloadOrigin(): string {
  const explicit = (import.meta.env.VITE_DOWNLOAD_ORIGIN as string | undefined)?.trim()
  if (explicit) {
    return trimTrailingSlash(explicit)
  }
  if (import.meta.env.DEV && typeof window !== 'undefined') {
    return trimTrailingSlash(window.location.origin)
  }
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8001'
  }
  if (typeof window !== 'undefined') {
    return trimTrailingSlash(window.location.origin)
  }
  return 'http://127.0.0.1:8001'
}

/**
 * WebSocket 基础 URL（无路径、无尾斜杠），与 VITE_WS_BASE_URL 或 VITE_API_BASE_URL 同源推导一致
 */
export function getWsBaseUrl(): string {
  if (isProxiedApiMode()) {
    if (typeof window !== 'undefined') {
      const wsScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${wsScheme}//${window.location.host}`
    }
    return 'ws://127.0.0.1:8005'
  }

  const explicit = (import.meta.env.VITE_WS_BASE_URL as string | undefined)?.trim()
  if (explicit) {
    return trimTrailingSlash(explicit)
  }
  const legacyWs = (import.meta.env.VITE_WEBSOCKET_URL as string | undefined)?.trim()
  if (legacyWs) {
    return trimTrailingSlash(legacyWs)
  }
  const apiBase = getApiBaseUrl()
  if (apiBase) {
    try {
      const u = new URL(apiBase)
      const wsScheme = u.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${wsScheme}//${u.host}`
    } catch {
      /* ignore */
    }
  }
  if (import.meta.env.VITE_DIRECT_API === 'true') {
    const devWs = (import.meta.env.VITE_DEV_WS_ORIGIN as string | undefined)?.trim()
    if (devWs) {
      return trimTrailingSlash(devWs)
    }
    return 'ws://127.0.0.1:8005'
  }
  if (typeof window !== 'undefined') {
    const wsScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${wsScheme}//${window.location.host}`
  }
  return 'ws://127.0.0.1:8005'
}
