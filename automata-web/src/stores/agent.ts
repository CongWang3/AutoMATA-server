// Agent 聊天状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { agentWebSocketService } from '@/api/agent'

// 聊天消息接口
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  timestamp: Date
  toolCall?: { tool: string; args: any }
  toolResult?: { tool: string; result: string }
  isThinking?: boolean
}

export type AgentMode = 'param_advice' | 'failure_diagnosis' | 'result_interpretation'

// AI 提供商选项
export interface ProviderOption {
  value: string
  label: string
  description: string
}

// 可用的 AI 提供商
export const PROVIDERS: ProviderOption[] = [
  // { value: 'openai', label: 'OpenAI', description: 'GPT-4o' },
  { value: 'qwen', label: 'Qwen', description: 'qwen-plus' },
  // { value: 'deepseek', label: 'DeepSeek', description: 'DeepSeek' }
  { value: 'deepseek', label: 'DeepSeek', description: 'deepseek-chat' }
]

/**
 * 生成唯一 ID
 */
function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

export const useAgentStore = defineStore('agent', () => {
  // 状态
  const messages = ref<ChatMessage[]>([])
  const isOpen = ref(false)
  const isConnected = ref(false)
  const isSending = ref(false)
  // const currentProvider = ref('openai')
  const currentProvider = ref('deepseek')
  const error = ref<string | null>(null)
  const currentIntent = ref<string>('')
  const currentIntentDisplay = ref<string>('')
  const currentJobContext = ref<{
    jobId: string
    found: boolean
    diagnosisReady: boolean
    missingFields: string[]
  } | null>(null)
  
  // 当前正在生成的 assistant 消息 ID（用于流式更新）
  const currentAssistantMessageId = ref<string | null>(null)
  
  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const currentProviderInfo = computed(() => 
    PROVIDERS.find(p => p.value === currentProvider.value) || PROVIDERS[0]
  )

  /**
   * 切换面板开关状态
   */
  function togglePanel(): void {
    isOpen.value = !isOpen.value
    
    // 打开面板时自动连接 WebSocket
    if (isOpen.value && !isConnected.value) {
      connect()
    }
  }

  /**
   * 打开面板
   */
  function openPanel(): void {
    isOpen.value = true
    if (!isConnected.value) {
      connect()
    }
  }

  /**
   * 关闭面板
   */
  function closePanel(): void {
    isOpen.value = false
  }

  /**
   * 连接到 Agent WebSocket
   */
  async function connect(): Promise<void> {
    if (isConnected.value) return
    
    try {
      // 设置回调
      setupCallbacks()
      
      await agentWebSocketService.connect()
      isConnected.value = true
      error.value = null
      console.log('Agent connected')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Connection failed'
      console.error('Agent connection failed:', error.value)
    }
  }

  /**
   * 断开连接
   */
  function disconnect(): void {
    agentWebSocketService.disconnect()
    isConnected.value = false
  }

  /**
   * 设置 WebSocket 回调
   */
  function setupCallbacks(): void {
    // 连接成功
    agentWebSocketService.setOnConnected(() => {
      isConnected.value = true
    })
    
    // 连接断开
    agentWebSocketService.setOnDisconnected(() => {
      isConnected.value = false
    })
    
    // Agent 思考中
    agentWebSocketService.setOnThinking((content) => {
      // 如果没有当前消息，创建一个新的 thinking 消息
      if (!currentAssistantMessageId.value) {
        const id = generateId()
        currentAssistantMessageId.value = id
        messages.value.push({
          id,
          role: 'assistant',
          content: content,
          timestamp: new Date(),
          isThinking: true
        })
      } else {
        // 更新现有消息内容
        const msg = messages.value.find(m => m.id === currentAssistantMessageId.value)
        if (msg) {
          msg.content = content
          msg.isThinking = true
        }
      }
    })
    
    // 工具调用
    agentWebSocketService.setOnToolCall((tool, args) => {
      const id = generateId()
      messages.value.push({
        id,
        role: 'tool',
        content: `Calling ${tool}...`,
        timestamp: new Date(),
        toolCall: { tool, args }
      })
    })
    
    // 工具结果
    agentWebSocketService.setOnToolResult((tool, result) => {
      // 查找对应的工具调用消息并更新
      const toolMsg = [...messages.value].reverse().find(
        m => m.role === 'tool' && m.toolCall?.tool === tool
      )
      if (toolMsg) {
        toolMsg.toolResult = { tool, result }
        toolMsg.content = `${tool} completed`
      }
    })
    
    // Agent 回复
    agentWebSocketService.setOnResponse((content, done) => {
      if (!currentAssistantMessageId.value) {
        // 创建新的 assistant 消息
        const id = generateId()
        currentAssistantMessageId.value = id
        messages.value.push({
          id,
          role: 'assistant',
          content,
          timestamp: new Date(),
          isThinking: false
        })
      } else {
        // 更新现有消息
        const msg = messages.value.find(m => m.id === currentAssistantMessageId.value)
        if (msg) {
          msg.content = content
          msg.isThinking = false
        }
      }
      
      // 回复完成
      if (done) {
        currentAssistantMessageId.value = null
        isSending.value = false
      }
    })

    // Agent 意图分类
    agentWebSocketService.setOnIntent((intent, intentDisplay) => {
      currentIntent.value = intent
      currentIntentDisplay.value = intentDisplay
    })
    agentWebSocketService.setOnJobContext((payload) => {
      if (!payload.jobId) {
        currentJobContext.value = null
      } else {
        currentJobContext.value = payload
      }
    })
    
    // 错误处理
    agentWebSocketService.setOnError((message) => {
      error.value = message
      isSending.value = false
      currentAssistantMessageId.value = null
      
      // 添加错误消息
      messages.value.push({
        id: generateId(),
        role: 'assistant',
        content: `❌ Error: ${message}`,
        timestamp: new Date()
      })
    })
  }

  /**
   * 发送消息
   */
  async function sendMessage(content: string, mode?: AgentMode, jobId?: string): Promise<void> {
    if (!content.trim() || isSending.value) return
    
    // 确保已连接
    if (!isConnected.value) {
      await connect()
    }

    // 显式 job 与当前上下文不一致时先清空，避免等不到 WS 时仍显示旧 Identified Job
    const explicitJob = (jobId ?? '').trim()
    const prevJob = currentJobContext.value?.jobId ?? ''
    if (explicitJob && explicitJob !== prevJob) {
      currentJobContext.value = null
    }
    
    // 添加用户消息
    messages.value.push({
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    })
    
    // 发送到服务器
    isSending.value = true
    error.value = null
    agentWebSocketService.sendChat(content.trim(), currentProvider.value, mode, jobId)
  }

  /**
   * 切换 AI 提供商
   */
  function switchProvider(provider: string): void {
    if (PROVIDERS.some(p => p.value === provider)) {
      currentProvider.value = provider
    }
  }

  /**
   * 清空聊天历史
   */
  function clearHistory(): void {
    messages.value = []
    currentAssistantMessageId.value = null
    error.value = null
    currentJobContext.value = null
  }

  /**
   * 清除错误
   */
  function clearError(): void {
    error.value = null
  }

  /** 清空已识别的 Job 上下文（例如用户修改了 Linked JobID 输入框） */
  function clearJobContext(): void {
    currentJobContext.value = null
  }

  return {
    // 状态
    messages,
    isOpen,
    isConnected,
    isSending,
    currentProvider,
    currentIntent,
    currentIntentDisplay,
    currentJobContext,
    error,
    
    // 计算属性
    hasMessages,
    currentProviderInfo,
    
    // 方法
    togglePanel,
    openPanel,
    closePanel,
    connect,
    disconnect,
    sendMessage,
    switchProvider,
    clearHistory,
    clearError,
    clearJobContext,
  }
})
