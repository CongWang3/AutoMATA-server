import { createApiClient } from './client'

export interface AgentByokStatus {
  qwen_configured: boolean
  deepseek_configured: boolean
}

export async function fetchAgentByokStatus(): Promise<AgentByokStatus> {
  const client = createApiClient()
  const { data } = await client.get<AgentByokStatus>('/v1/agent/byok')
  return data
}

export async function saveAgentByokKeys(payload: {
  qwen?: string
  deepseek?: string
}): Promise<void> {
  const client = createApiClient()
  await client.put('/v1/agent/byok', payload)
}
