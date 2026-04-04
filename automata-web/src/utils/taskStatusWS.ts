/**
 * 任务状态 WebSocket 客户端
 * 用于接收实时任务状态更新
 */

import { getToken } from '@/utils/auth'

class TaskStatusWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 5
  private reconnectDelay: number = 3000
  private isConnected: boolean = false
  private listeners: Map<string, Function[]> = new Map()
  private heartbeatInterval: number | null = null

  /**
   * 连接到任务状态 WebSocket 服务
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const token = getToken()
      if (!token) {
        reject(new Error('用户未登录'))
        return
      }

      // 关闭现有连接
      this.disconnect()

      // 动态获取 WebSocket URL
      const getDefaultWsBase = () => {
        if (import.meta.env.PROD) {
          const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
          return `${protocol}//${window.location.host}`
        }
        return 'ws://localhost:8005'
      }
      const wsUrl = `${import.meta.env.VITE_WEBSOCKET_URL || getDefaultWsBase()}/api/v1/tasks/ws/status`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('[Task WS] 连接已建立')
        this.isConnected = true
        this.reconnectAttempts = 0
        
        // 发送认证消息
        this.sendAuthMessage(token)
        
        // 启动心跳机制
        this.startHeartbeat()
        
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('[Task WS] 消息解析失败:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('[Task WS] 连接错误:', error)
        this.isConnected = false
        reject(error)
      }

      this.ws.onclose = (event) => {
        console.log(`[Task WS] 连接已关闭: ${event.code} ${event.reason}`)
        this.isConnected = false
        this.stopHeartbeat()
        
        // 自动重连逻辑
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`[Task WS] 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
          setTimeout(() => {
            this.connect().catch(err => {
              console.error('[Task WS] 重连失败:', err)
            })
          }, this.reconnectDelay)
        }
      }
    })
  }

  /**
   * 发送认证消息
   */
  private sendAuthMessage(token: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const authMessage = {
        type: 'auth',
        token: token
      }
      this.ws.send(JSON.stringify(authMessage))
      console.log('[Task WS] 认证消息已发送')
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: any): void {
    const { event, data, timestamp } = message
    
    console.log(`[Task WS] 收到事件: ${event}`, data)
    
    // 触发对应的事件监听器
    const listeners = this.listeners.get(event) || []
    listeners.forEach(listener => {
      try {
        listener(data, timestamp)
      } catch (error) {
        console.error(`[Task WS] 事件监听器执行错误:`, error)
      }
    })
  }

  /**
   * 启动心跳机制
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({
            type: 'ping',
            timestamp: Date.now()
          }))
        } catch (error) {
          console.error('[Task WS] 心跳发送失败:', error)
        }
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
   * 添加事件监听器
   */
  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)?.push(callback)
  }

  /**
   * 移除事件监听器
   */
  off(event: string, callback: Function): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  /**
   * 移除所有事件监听器
   */
  removeAllListeners(): void {
    this.listeners.clear()
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.stopHeartbeat()
    this.removeAllListeners()
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    
    this.isConnected = false
    this.reconnectAttempts = 0
  }

  /**
   * 检查连接状态
   */
  get connected(): boolean {
    return this.isConnected && this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  /**
   * 获取重连尝试次数
   */
  get attempts(): number {
    return this.reconnectAttempts
  }
}

// 创建全局实例
export const taskStatusWS = new TaskStatusWebSocket()

// 导出类型定义
export interface TaskStatusMessage {
  event: 'task_status' | 'connected' | 'auth_failed' | 'pong'
  data?: {
    job_id: string
    status: string
    progress?: number
    result_file?: string
    error_message?: string
    created_at?: string
    updated_at?: string
    message?: string
  }
  timestamp: number
}

export default taskStatusWS