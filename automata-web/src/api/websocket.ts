// WebSocket实时通信服务
// <!-- 
// 审查上下文：
// - 设计意图：实现与后端的WebSocket连接，用于实时接收文件上传进度和任务状态更新
// - 已知局限：当前实现为单例模式，同一时间只能维持一个WebSocket连接
// - 业务背景：docs/api/BACKEND_API_REFERENCE.md#WebSocket实时通信 部分定义的实时通信协议
// - 测试重点：连接状态管理、心跳机制、消息处理、重连逻辑
// -->
import type { WebSocketProgressMessage } from './types'
import { AuthService } from './auth'

export class WebSocketService {
  private static instance: WebSocketService | null = null
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 2  // 进一步减少最大重连次数
  private reconnectDelay = 8000    // 增加重连延迟到8秒
  private isIntentionallyClosing = false  // 标记是否为主动关闭
  private heartbeatInterval: number | null = null
  private heartbeatTimeout: number | null = null
  
  // 回调函数
  private onProgressCallback: ((message: WebSocketProgressMessage) => void) | null = null
  private onTaskStatusCallback: ((message: any) => void) | null = null
  private onOpenCallback: (() => void) | null = null
  private onCloseCallback: (() => void) | null = null
  private onErrorCallback: ((error: Event) => void) | null = null

  private constructor() {}

  /**
   * 获取单例实例
   * @returns WebSocketService实例
   */
  static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService()
    }
    return WebSocketService.instance
  }

  /**
   * 连接到任务状态 WebSocket
   * @param baseUrl 基础URL（可选）
   * @returns 连接Promise
   */
  async connectTaskStatus(baseUrl?: string): Promise<void> {
    // <!-- 
    // 审查上下文：
    // - 设计意图：为任务状态监控提供专用的 WebSocket 连接
    // - 已知局限：复用现有的连接管理逻辑，避免重复代码
    // - 业务背景：与文件上传 WebSocket 共享基础设施但独立管理
    // - 测试重点：连接建立、认证流程、消息路由
    // -->
    
    console.log('🔌 开始任务状态 WebSocket 连接...')
    
    // 如果启用了直接 API 连接，使用后端地址而不是 Vite代理
    const useDirectAPI = import.meta.env.VITE_DIRECT_API === 'true'
    const base = baseUrl || (useDirectAPI 
      ? 'ws://localhost:8005' 
      : import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8005')
    const token = AuthService.getAuthToken()
      
    if (!token) {
      throw new Error('未找到认证 token')
    }

    const wsUrl = `${base}/api/v1/tasks/ws/status`
    
    try {
      this.ws = new WebSocket(wsUrl)
      
      return new Promise((resolve, reject) => {
        this.ws!.onopen = (event) => {
          console.log('🟢 任务状态 WebSocket 连接已建立')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          
          // 发送认证token
          this.sendMessage({ type: 'auth', token })
          
          this.onOpenCallback?.()
          resolve()
        }

        this.ws!.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('解析任务状态 WebSocket 消息失败:', error)
          }
        }

        this.ws!.onclose = (event) => {
          console.log('🔴 任务状态 WebSocket 连接已关闭', event.code, event.reason)
          this.stopHeartbeat()
          this.onCloseCallback?.()
        }

        this.ws!.onerror = (error) => {
          console.error('❌ 任务状态 WebSocket 错误:', error)
          this.onErrorCallback?.(error)
          reject(error)
        }
      })
      
    } catch (error) {
      console.error('建立任务状态 WebSocket 连接失败:', error)
      throw error
    }
  }

  /**
   * 连接到 WebSocket
   * @param baseUrl 基础URL（可选）
   * @returns 连接Promise
   */
  async connect(baseUrl?: string): Promise<void> {
    console.log('🔌 开始 WebSocket 连接...')
    return new Promise((resolve, reject) => {
      // 如果已经连接，直接返回
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('✅ WebSocket 已经连接，直接返回')
        resolve()
        return
      }
  
      // 关闭现有连接
      this.disconnect()
  
      // 如果启用了直接 API 连接，使用后端地址而不是 Vite代理
      const useDirectAPI = import.meta.env.VITE_DIRECT_API === 'true'
      const base = baseUrl || (useDirectAPI 
        ? 'ws://localhost:8005' 
        : import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8005')
      const token = AuthService.getAuthToken()
        
      if (!token) {
        reject(new Error('未找到认证 token'))
        return
      }
  
      const wsUrl = `${base}/api/v1/files/ws/progress`
      
      try {
        this.ws = new WebSocket(wsUrl)
        
        this.ws.onopen = (event) => {
          console.log('🟢 WebSocket连接已建立')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          
          // 发送认证token
          this.sendMessage({ type: 'auth', token })
          
          this.onOpenCallback?.()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('解析WebSocket消息失败:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('🔴 WebSocket连接已关闭', event.code, event.reason)
          this.stopHeartbeat()
          this.onCloseCallback?.()
              
          // 尝试重连（如果不是主动关闭且不是认证失败）
          const shouldReconnect = !this.isIntentionallyClosing && 
                                 event.code !== 1000 && 
                                 event.code !== 4001 && // 认证失败
                                 this.reconnectAttempts < this.maxReconnectAttempts
              
          if (shouldReconnect) {
            console.log(`🔄 计划第 ${this.reconnectAttempts + 1} 次重连...`)
            this.scheduleReconnect()
          } else {
            console.log('⏹️ 停止重连尝试')
            this.reconnectAttempts = 0 // 重置计数器
          }
              
          // 重置主动关闭标记
          this.isIntentionallyClosing = false
        }

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket错误:', error)
          this.onErrorCallback?.(error)
          reject(error)
        }

      } catch (error) {
        console.error('建立WebSocket连接失败:', error)
        reject(error)
      }
    })
  }

  /**
   * 关闭WebSocket连接
   */
  disconnect(): void {
    this.isIntentionallyClosing = true
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    this.stopHeartbeat()
    // 重置重连计数器
    this.reconnectAttempts = 0
  }

  /**
   * 发送消息
   * @param message 消息对象
   */
  sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }

  /**
   * 处理接收到的消息
   * @param data 消息数据
   */
  private handleMessage(data: any): void {
    switch (data.event) {
      case 'upload_progress':
        this.handleProgressMessage(data)
        break
      case 'task_status':
        this.handleTaskStatusMessage(data)
        break
      case 'heartbeat_response':
        this.handleHeartbeatResponse()
        break
      case 'connected':
        this.handleConnectedMessage(data)
        break
      case 'pong':
        this.handlePongMessage(data)
        break
      default:
        console.log('收到未知消息类型:', data.event, data)
    }
  }

  /**
   * 处理进度消息
   * @param message 进度消息
   */
  private handleProgressMessage(message: WebSocketProgressMessage): void {
    console.log('📈 文件上传进度:', message.progress_percent + '%')
    this.onProgressCallback?.(message)
  }

  /**
   * 处理任务状态消息
   * @param message 任务状态消息
   */
  private handleTaskStatusMessage(message: any): void {
    console.log('📊 任务状态更新:', message)
    
    const { job_id, status, progress, result_file, error_message } = message.data || {}
    
    // 显示进度更新
    if (progress !== undefined) {
      console.log(`🎯 任务 ${job_id} 进度: ${progress}%`)
    }
    
    // 显示状态变化
    switch (status) {
      case 'PROCESSING':
        console.log(`🔄 任务 ${job_id} 正在处理中...`)
        break
      case 'COMPLETED':
        console.log(`✅ 任务 ${job_id} 已完成!`)
        if (result_file) {
          console.log(`📁 结果文件: ${result_file}`)
        }
        break
      case 'FAILED':
        console.log(`❌ 任务 ${job_id} 失败!`)
        if (error_message) {
          console.log(`💬 错误信息: ${error_message}`)
        }
        break
    }
    
    // 调用回调函数（如果设置了的话）
    this.onTaskStatusCallback?.(message.data)
  }

  /**
   * 处理心跳响应
   */
  private handleHeartbeatResponse(): void {
    // 重置心跳超时
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout)
    }
  }

  /**
   * 处理连接确认消息
   */
  private handleConnectedMessage(data: any): void {
    console.log('✅ WebSocket 连接已确认:', data.message || '连接成功')
    if (data.user_id) {
      console.log('👤 用户ID:', data.user_id)
    }
  }

  /**
   * 处理心跳响应消息
   */
  private handlePongMessage(data: any): void {
    // pong 是服务器对心跳的响应，连接正常
    console.debug('💓 收到心跳响应')
  }

  /**
   * 启动心跳机制
   * 注意：心跳只用于保持连接活跃，不触发重连（避免影响 Vite 代理）
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      // 只有连接正常时才发送心跳
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'heartbeat' })
      }
      // 移除心跳超时重连逻辑 - 依赖 WebSocket 原生的 onclose 事件来处理断线
    }, 60000) // 每60秒发送一次心跳
  }

  /**
   * 停止心跳机制
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout)
      this.heartbeatTimeout = null
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++
    console.log(`尝试第 ${this.reconnectAttempts} 次重连...`)
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('重连失败:', error)
      })
    }, this.reconnectDelay * this.reconnectAttempts) // 指数退避
  }

  /**
   * 手动重连
   */
  private reconnect(): void {
    this.disconnect()
    this.connect().catch(error => {
      console.error('重连失败:', error)
    })
  }

  /**
   * 设置进度回调
   * @param callback 回调函数
   */
  setOnProgress(callback: (message: WebSocketProgressMessage) => void): void {
    this.onProgressCallback = callback
  }

  /**
   * 设置任务状态回调
   * @param callback 回调函数
   */
  setOnTaskStatus(callback: (message: any) => void): void {
    this.onTaskStatusCallback = callback
  }

  /**
   * 设置连接打开回调
   * @param callback 回调函数
   */
  setOnOpen(callback: () => void): void {
    this.onOpenCallback = callback
  }

  /**
   * 设置连接关闭回调
   * @param callback 回调函数
   */
  setOnClose(callback: () => void): void {
    this.onCloseCallback = callback
  }

  /**
   * 设置错误回调
   * @param callback 回调函数
   */
  setOnError(callback: (error: Event) => void): void {
    this.onErrorCallback = callback
  }

  /**
   * 检查连接状态
   * @returns 连接状态
   */
  isConnected(): boolean {
    const connected = this.ws !== null && this.ws.readyState === WebSocket.OPEN
    // 减少日志输出频率，只在调试时显示
    if (import.meta.env.DEV) {
      console.debug('🔍 WebSocket连接状态检查:', {
        hasWebSocket: !!this.ws,
        readyState: this.ws?.readyState,
        isConnected: connected
      })
    }
    return connected
  }

  /**
   * 获取连接状态
   * @returns WebSocket readyState
   */
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}

// 导出单例实例
export const webSocketService = WebSocketService.getInstance()
export default WebSocketService