// Agent WebSocket 服务
// 用于与 AI Agent 进行实时聊天通信
import { AuthService } from './auth'
import { getWsBaseUrl } from '@/config/deploy'

// Agent 事件回调类型定义
type ThinkingCallback = (content: string) => void
type ToolCallCallback = (tool: string, args: any) => void
type ToolResultCallback = (tool: string, result: string) => void
type ResponseCallback = (content: string, done: boolean) => void
type IntentCallback = (intent: string, intentDisplay: string) => void
type JobContextCallback = (payload: { jobId: string; found: boolean; diagnosisReady: boolean; missingFields: string[] }) => void
type ErrorCallback = (message: string) => void
type ConnectedCallback = () => void
type DisconnectedCallback = () => void

export class AgentWebSocketService {
  private static instance: AgentWebSocketService | null = null
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3
  private reconnectDelay = 5000
  private isIntentionallyClosing = false
  private heartbeatInterval: number | null = null
  
  // 回调函数
  private onThinkingCallback: ThinkingCallback | null = null
  private onToolCallCallback: ToolCallCallback | null = null
  private onToolResultCallback: ToolResultCallback | null = null
  private onResponseCallback: ResponseCallback | null = null
  private onIntentCallback: IntentCallback | null = null
  private onJobContextCallback: JobContextCallback | null = null
  private onErrorCallback: ErrorCallback | null = null
  private onConnectedCallback: ConnectedCallback | null = null
  private onDisconnectedCallback: DisconnectedCallback | null = null

  private constructor() {}

  /**
   * 获取单例实例
   */
  static getInstance(): AgentWebSocketService {
    if (!AgentWebSocketService.instance) {
      AgentWebSocketService.instance = new AgentWebSocketService()
    }
    return AgentWebSocketService.instance
  }

  /**
   * 连接到 Agent WebSocket
   * @param baseUrl 基础URL（可选）
   */
  async connect(baseUrl?: string): Promise<void> {
    console.log('🤖 开始 Agent WebSocket 连接...')
    
    return new Promise((resolve, reject) => {
      // 如果已经连接，直接返回
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('✅ Agent WebSocket 已经连接')
        resolve()
        return
      }

      // 关闭现有连接
      this.disconnect()

      const base = baseUrl?.trim() || getWsBaseUrl()
      
      const token = AuthService.getAuthToken()
      if (!token) {
        reject(new Error('Authentication token not found'))
        return
      }

      const wsUrl = `${base}/api/v1/agent/chat`
      
      try {
        this.ws = new WebSocket(wsUrl)
        
        this.ws.onopen = () => {
          console.log('🟢 Agent WebSocket 连接已建立')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          
          // 发送认证消息
          this.sendMessage({ type: 'auth', token })
          
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('Failed to parse Agent WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('🔴 Agent WebSocket 连接已关闭', event.code, event.reason)
          this.stopHeartbeat()
          this.onDisconnectedCallback?.()
          
          // 尝试重连
          const shouldReconnect = !this.isIntentionallyClosing && 
                                 event.code !== 1000 && 
                                 event.code !== 4001 &&
                                 this.reconnectAttempts < this.maxReconnectAttempts
          
          if (shouldReconnect) {
            console.log(`🔄 计划第 ${this.reconnectAttempts + 1} 次重连...`)
            this.scheduleReconnect()
          }
          
          this.isIntentionallyClosing = false
        }

        this.ws.onerror = (error) => {
          console.error('❌ Agent WebSocket error:', error)
          this.onErrorCallback?.('Connection error')
          reject(error)
        }

      } catch (error) {
        console.error('建立 Agent WebSocket 连接失败:', error)
        reject(error)
      }
    })
  }

  /**
   * 发送聊天消息
   * @param message 消息内容
   * @param provider AI 提供商
   */
  sendChat(message: string, provider: string = 'openai', mode?: string, jobId?: string): void {
    this.sendMessage({
      type: 'chat',
      message,
      provider,
      mode,
      job_id: jobId
    })
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isIntentionallyClosing = true
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    this.stopHeartbeat()
    this.reconnectAttempts = 0
  }

  /**
   * 发送消息
   */
  private sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('Agent WebSocket is not connected, unable to send message')
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(data: any): void {
    const eventType = data.event || data.type
    
    switch (eventType) {
      case 'connected':
        console.log('✅ Agent connection confirmed:', data.message || 'Connected')
        this.onConnectedCallback?.()
        break
        
      case 'agent_thinking':
        this.onThinkingCallback?.(data.content || '')
        break
        
      case 'agent_tool_call':
        this.onToolCallCallback?.(data.tool, data.args)
        break
        
      case 'agent_tool_result':
        this.onToolResultCallback?.(data.tool, data.result)
        break
        
      case 'agent_response':
        this.onResponseCallback?.(data.content, data.done || false)
        break
      case 'agent_intent':
        this.onIntentCallback?.(data.intent || '', data.intent_display || '')
        break
      case 'agent_job_context':
        this.onJobContextCallback?.({
          jobId: data.job_id || '',
          found: !!data.found,
          diagnosisReady: !!data.diagnosis_ready,
          missingFields: Array.isArray(data.missing_fields) ? data.missing_fields : [],
        })
        break
        
      case 'error':
        console.error('❌ Agent error:', data.message)
        this.onErrorCallback?.(data.message || 'Unknown error')
        break
        
      case 'pong':
        // 心跳响应
        console.debug('💓 Received Agent heartbeat response')
        break
        
      default:
        console.log('Received unknown Agent message type:', eventType, data)
    }
  }

  /**
   * 启动心跳机制
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'heartbeat' })
      }
    }, 30000) // 每30秒发送一次心跳
  }

  /**
   * 停止心跳机制
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('Agent WebSocket reconnect failed:', error)
      })
    }, this.reconnectDelay * this.reconnectAttempts)
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  // 设置回调函数
  setOnThinking(callback: ThinkingCallback): void {
    this.onThinkingCallback = callback
  }

  setOnToolCall(callback: ToolCallCallback): void {
    this.onToolCallCallback = callback
  }

  setOnToolResult(callback: ToolResultCallback): void {
    this.onToolResultCallback = callback
  }

  setOnResponse(callback: ResponseCallback): void {
    this.onResponseCallback = callback
  }

  setOnIntent(callback: IntentCallback): void {
    this.onIntentCallback = callback
  }

  setOnJobContext(callback: JobContextCallback): void {
    this.onJobContextCallback = callback
  }

  setOnError(callback: ErrorCallback): void {
    this.onErrorCallback = callback
  }

  setOnConnected(callback: ConnectedCallback): void {
    this.onConnectedCallback = callback
  }

  setOnDisconnected(callback: DisconnectedCallback): void {
    this.onDisconnectedCallback = callback
  }
}

// 导出单例实例
export const agentWebSocketService = AgentWebSocketService.getInstance()
export default AgentWebSocketService
