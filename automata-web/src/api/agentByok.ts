import { createApiClient } from './client'
import { getApiBaseUrl } from '@/config/deploy'

export interface AgentByokStatus {
  qwen_configured: boolean
  deepseek_configured: boolean
}

// #region agent log
/** 远程部署时浏览器无法打到本机 :7618 ingest；同步打 console 便于在服务器环境抓证据（不含密钥）。 */
function __dbgAgentByok(hypothesisId: string, message: string, data: Record<string, unknown>): void {
  if (typeof window === 'undefined') return
  const payload = {
    sessionId: 'da4ec2',
    hypothesisId,
    location: 'agentByok.ts',
    message,
    data,
    timestamp: Date.now(),
  }
  console.info('[BYOK_DBG]', payload)
  fetch('http://localhost:7618/ingest/6cda10c1-514a-4099-b96b-d25dcd87149d', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'da4ec2' },
    body: JSON.stringify(payload),
  }).catch(() => {})
}
// #endregion

export async function fetchAgentByokStatus(): Promise<AgentByokStatus> {
  const client = createApiClient()
  const base = getApiBaseUrl()
  const path = '/v1/agent/byok'
  let resolved = ''
  if (typeof window !== 'undefined') {
    try {
      resolved = base.startsWith('http')
        ? new URL(path.replace(/^\//, ''), base.endsWith('/') ? base : `${base}/`).href
        : `${window.location.origin}${base === '/' ? '' : base.replace(/\/$/, '')}${path}`
    } catch {
      resolved = 'resolve-error'
    }
  }
  // #region agent log
  __dbgAgentByok('H1', 'byok GET before', {
    base,
    path,
    resolved,
    origin: typeof window !== 'undefined' ? window.location.origin : '',
    viteMode: import.meta.env.MODE,
  })
  // #endregion
  try {
    const out = await client.get<AgentByokStatus>(path)
    // #region agent log
    __dbgAgentByok('H2', 'byok GET success', {
      qwen_configured: !!out?.qwen_configured,
      deepseek_configured: !!out?.deepseek_configured,
    })
    // #endregion
    return out
  } catch (e: unknown) {
    const ax = e as { response?: { status?: number; data?: unknown }; message?: string }
    const data = ax.response?.data
    const dataSnippet =
      typeof data === 'string' ? data.slice(0, 200) : JSON.stringify(data ?? '').slice(0, 200)
    // #region agent log
    __dbgAgentByok('H3', 'byok GET error', {
      status: ax.response?.status,
      dataSnippet,
      msg: ax.message,
    })
    // #endregion
    throw e
  }
}

export async function saveAgentByokKeys(payload: {
  qwen?: string
  deepseek?: string
}): Promise<void> {
  const client = createApiClient()
  const base = getApiBaseUrl()
  let resolved = ''
  if (typeof window !== 'undefined') {
    try {
      resolved = `${window.location.origin}${base === '/' ? '' : base.replace(/\/$/, '')}/v1/agent/byok`
    } catch {
      resolved = 'resolve-error'
    }
  }
  // #region agent log
  __dbgAgentByok('H1', 'byok POST before', { base, resolved, keys: Object.keys(payload || {}) })
  // #endregion
  try {
    await client.post('/v1/agent/byok', payload)
    // #region agent log
    __dbgAgentByok('H2', 'byok POST success', {})
    // #endregion
  } catch (e: unknown) {
    const ax = e as { response?: { status?: number; data?: unknown }; message?: string }
    const data = ax.response?.data
    const dataSnippet =
      typeof data === 'string' ? data.slice(0, 200) : JSON.stringify(data ?? '').slice(0, 200)
    // #region agent log
    __dbgAgentByok('H3', 'byok POST error', {
      status: ax.response?.status,
      dataSnippet,
      msg: ax.message,
    })
    // #endregion
    throw e
  }
}
