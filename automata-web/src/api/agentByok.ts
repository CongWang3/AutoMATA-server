import { createApiClient } from './client'

export interface AgentByokStatus {
  qwen_configured: boolean
  deepseek_configured: boolean
}

export async function fetchAgentByokStatus(): Promise<AgentByokStatus> {
  const client = createApiClient()
  // get() 已返回 response.data（见 ApiClient.request），勿再解构 .data
  return await client.get<AgentByokStatus>('/v1/agent/byok')
}

export async function saveAgentByokKeys(payload: {
  qwen?: string
  deepseek?: string
}): Promise<void> {
  const client = createApiClient()
  // 使用 POST：部分网关对 /api/... 的 PUT 未转发会返回 404；后端 PUT/POST 语义一致
  await client.post('/v1/agent/byok', payload)
}
