/**
 * 部署相关运行时配置（通过 Vite 环境变量注入，见 .env.development / .env.production）
 */

/** 去掉尾部斜杠 */
function trimTrailingSlash(s: string): string {
  return s.replace(/\/+$/, '')
}

/**
 * 独立下载服务对外根 URL（无路径、无尾斜杠），例如 http://127.0.0.1:8001 或 https://example.com
 */
export function getDownloadOrigin(): string {
  const explicit = (import.meta.env.VITE_DOWNLOAD_ORIGIN as string | undefined)?.trim()
  if (explicit) {
    return trimTrailingSlash(explicit)
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
  const explicit = (import.meta.env.VITE_WS_BASE_URL as string | undefined)?.trim()
  if (explicit) {
    return trimTrailingSlash(explicit)
  }
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
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
