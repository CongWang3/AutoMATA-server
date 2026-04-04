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
import { getWsBaseUrl } from '@/config/deploy'

type ConnectWaiter = { resolve: () => void; reject: (e: Error) => void }

export type TaskSocketState = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed'

export class WebSocketService {
  private static instance: WebSocketService | null = null
  // 文件进度 WebSocket
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3
  private reconnectDelay = 5000
  private isIntentionallyClosing = false
  private heartbeatInterval: number | null = null
  private heartbeatTimeout: number | null = null
  private fileWsConnectWaiters: ConnectWaiter[] = []

  // 任务状态 WebSocket（独立连接，不与文件进度 WS 冲突）
  private taskWs: WebSocket | null = null
  private taskHeartbeatInterval: number | null = null
  private taskIsIntentionallyClosing = false
  private taskReconnectAttempts = 0
  private taskReconnectTimer: ReturnType<typeof setTimeout> | null = null
  private taskWsConnectWaiters: ConnectWaiter[] = []

  // 回调函数
  private onProgressCallback: ((message: WebSocketProgressMessage) => void) | null = null
  private onTaskStatusCallback: ((message: any) => void) | null = null
  private onOpenCallback: (() => void) | null = null
  private onCloseCallback: (() => void) | null = null
  private onErrorCallback: ((error: Event) => void) | null = null
  private onTaskSocketStateCallback: ((state: TaskSocketState) => void) | null = null

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
   * 任务状态 WS 连接状态（供 UI 展示连接中/重连中等）
   */
  setOnTaskSocketState(callback: ((state: TaskSocketState) => void) | null): void {
    this.onTaskSocketStateCallback = callback
  }

  private emitTaskSocketState(state: TaskSocketState): void {
    this.onTaskSocketStateCallback?.(state)
  }

  private clearTaskReconnectSchedule(): void {
    if (this.taskReconnectTimer !== null) {
      clearTimeout(this.taskReconnectTimer)
      this.taskReconnectTimer = null
    }
  }

  private flushTaskWsWaitersResolve(): void {
    this.taskWsConnectWaiters.forEach((w) => w.resolve())
    this.taskWsConnectWaiters = []
  }

  private flushTaskWsWaitersReject(err: Error): void {
    this.taskWsConnectWaiters.forEach((w) => w.reject(err))
    this.taskWsConnectWaiters = []
  }

  private flushFileWsWaitersResolve(): void {
    this.fileWsConnectWaiters.forEach((w) => w.resolve())
    this.fileWsConnectWaiters = []
  }

  private flushFileWsWaitersReject(err: Error): void {
    this.fileWsConnectWaiters.forEach((w) => w.reject(err))
    this.fileWsConnectWaiters = []
  }

  private detachAndCloseFileSocket(code: number, reason: string): void {
    const w = this.ws
    this.ws = null
    if (!w) return
    w.onopen = null
    w.onmessage = null
    w.onerror = null
    w.onclose = null
    try {
      w.close(code, reason)
    } catch {
      /* ignore */
    }
  }

  /**
   * 连接到任务状态 WebSocket
   * @param baseUrl 基础URL（可选）
   * @returns 连接Promise
   */
  async connectTaskStatus(baseUrl?: string): Promise<void> {
    if (import.meta.env.DEV) console.log('🔌 开始任务状态 WebSocket 连接...')

    this.clearTaskReconnectSchedule()

    if (this.taskWs && this.taskWs.readyState === WebSocket.OPEN) {
      if (import.meta.env.DEV) console.log('✅ 任务状态 WebSocket 已连接，直接返回')
      return
    }

    if (this.taskWs && this.taskWs.readyState === WebSocket.CONNECTING) {
      return new Promise((resolve, reject) => {
        this.taskWsConnectWaiters.push({ resolve, reject })
      })
    }

    const base = baseUrl?.trim() || getWsBaseUrl()
    const token = AuthService.getAuthToken()

    if (!token) {
      throw new Error('未找到认证 token')
    }

    this.taskIsIntentionallyClosing = false
    this.detachAndCloseTaskSocket('Replacing task status connection')
    this.stopTaskHeartbeat()

    const wsUrl = `${base}/api/v1/tasks/ws/status`

    this.emitTaskSocketState('connecting')

    try {
      this.taskWs = new WebSocket(wsUrl)

      return new Promise((resolve, reject) => {
        let settled = false

        const finish = (fn: () => void) => {
          if (!settled) {
            settled = true
            fn()
          }
        }

        this.taskWs!.onopen = () => {
          if (import.meta.env.DEV) console.log('🟢 任务状态 WebSocket 连接已建立')
          this.taskReconnectAttempts = 0
          this.startTaskHeartbeat()
          this.sendTaskMessage({ type: 'auth', token })
          this.emitTaskSocketState('open')
          finish(() => {
            resolve()
            this.flushTaskWsWaitersResolve()
          })
        }

        this.taskWs!.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('解析任务状态 WebSocket 消息失败:', error)
          }
        }

        this.taskWs!.onclose = (event) => {
          if (import.meta.env.DEV) {
            console.log('🔴 任务状态 WebSocket 连接已关闭', event.code, event.reason)
          }
          this.stopTaskHeartbeat()
          this.taskWs = null

          finish(() => {
            const err = new Error('任务状态 WebSocket 在连接完成前关闭')
            reject(err)
            this.flushTaskWsWaitersReject(err)
          })

          const shouldReconnect =
            !this.taskIsIntentionallyClosing &&
            event.code !== 1000 &&
            event.code !== 4001 &&
            this.taskReconnectAttempts < this.maxReconnectAttempts

          if (shouldReconnect) {
            this.emitTaskSocketState('reconnecting')
            this.scheduleTaskReconnect(baseUrl)
          } else {
            if (import.meta.env.DEV) console.log('⏹️ 任务状态 WebSocket 停止重连')
            this.taskReconnectAttempts = 0
            this.emitTaskSocketState('closed')
          }

          this.taskIsIntentionallyClosing = false
        }

        this.taskWs!.onerror = (error) => {
          console.error('❌ 任务状态 WebSocket 错误:', error)
          if (!settled) {
            finish(() => {
              reject(error)
              this.flushTaskWsWaitersReject(new Error('任务状态 WebSocket 错误'))
            })
          }
        }
      })
    } catch (error) {
      console.error('建立任务状态 WebSocket 连接失败:', error)
      this.emitTaskSocketState('closed')
      throw error
    }
  }

  private scheduleTaskReconnect(baseUrl?: string): void {
    this.taskReconnectAttempts++
    if (import.meta.env.DEV) {
      console.log(`🔄 任务状态 WebSocket 计划第 ${this.taskReconnectAttempts} 次重连...`)
    }
    this.taskReconnectTimer = setTimeout(() => {
      this.taskReconnectTimer = null
      this.connectTaskStatus(baseUrl).catch((error) => {
        if (import.meta.env.DEV) console.error('任务状态 WebSocket 重连失败:', error)
      })
    }, this.reconnectDelay * this.taskReconnectAttempts)
  }

  /**
   * 断开任务状态 WebSocket（不影响文件进度 WS）
   */
  disconnectTaskStatus(): void {
    this.clearTaskReconnectSchedule()
    this.taskIsIntentionallyClosing = true
    this.taskReconnectAttempts = 0
    this.detachAndCloseTaskSocket('Client disconnect task status')
    this.stopTaskHeartbeat()
    this.flushTaskWsWaitersReject(new Error('任务状态 WebSocket 已断开'))
    this.emitTaskSocketState('idle')
  }

  /** 移除监听后再 close，避免异步 onclose 与新建连接逻辑竞态 */
  private detachAndCloseTaskSocket(reason: string): void {
    const tw = this.taskWs
    this.taskWs = null
    if (!tw) return
    tw.onopen = null
    tw.onmessage = null
    tw.onerror = null
    tw.onclose = null
    try {
      tw.close(1000, reason)
    } catch {
      /* ignore */
    }
  }

  /**
   * 发送任务状态 WebSocket 消息
   */
  private sendTaskMessage(message: any): void {
    if (this.taskWs && this.taskWs.readyState === WebSocket.OPEN) {
      this.taskWs.send(JSON.stringify(message))
    }
  }

  /**
   * 启动任务状态 WS 心跳
   */
  private startTaskHeartbeat(): void {
    this.taskHeartbeatInterval = window.setInterval(() => {
      if (this.taskWs?.readyState === WebSocket.OPEN) {
        this.sendTaskMessage({ type: 'heartbeat' })
      }
    }, 60000)
  }

  /**
   * 停止任务状态 WS 心跳
   */
  private stopTaskHeartbeat(): void {
    if (this.taskHeartbeatInterval) {
      clearInterval(this.taskHeartbeatInterval)
      this.taskHeartbeatInterval = null
    }
  }

  /**
   * 检查任务状态 WS 连接状态
   */
  isTaskStatusConnected(): boolean {
    return this.taskWs !== null && this.taskWs.readyState === WebSocket.OPEN
  }

  /**
   * 连接到 WebSocket
   * @param baseUrl 基础URL（可选）
   * @returns 连接Promise
   */
  async connect(baseUrl?: string): Promise<void> {
    if (import.meta.env.DEV) console.log('🔌 开始 WebSocket 连接...')
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        if (import.meta.env.DEV) console.log('✅ WebSocket 已经连接，直接返回')
        resolve()
        return
      }

      if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
        this.fileWsConnectWaiters.push({ resolve, reject })
        return
      }

      if (this.ws && this.ws.readyState === WebSocket.CLOSED) {
        this.ws = null
      }

      if (this.ws && this.ws.readyState === WebSocket.CLOSING) {
        this.ws = null
      }

      this.isIntentionallyClosing = false
      if (this.ws) {
        this.detachAndCloseFileSocket(1000, 'Replacing connection')
      }
      this.stopHeartbeat()

      const base = baseUrl?.trim() || getWsBaseUrl()
      const token = AuthService.getAuthToken()

      if (!token) {
        reject(new Error('未找到认证 token'))
        return
      }

      const wsUrl = `${base}/api/v1/files/ws/progress`
      try {
        this.ws = new WebSocket(wsUrl)

        let settled = false
        const finish = (fn: () => void) => {
          if (!settled) {
            settled = true
            fn()
          }
        }

        this.ws.onopen = () => {
          if (import.meta.env.DEV) console.log('🟢 WebSocket连接已建立')
          this.reconnectAttempts = 0
          this.startHeartbeat()

          this.sendMessage({ type: 'auth', token })

          this.onOpenCallback?.()
          finish(() => {
            resolve()
            this.flushFileWsWaitersResolve()
          })
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
          if (import.meta.env.DEV) {
            console.log('🔴 WebSocket连接已关闭', event.code, event.reason)
          }
          this.stopHeartbeat()
          this.ws = null
          this.onCloseCallback?.()

          finish(() => {
            const err = new Error('WebSocket 在连接完成前关闭')
            reject(err)
            this.flushFileWsWaitersReject(err)
          })

          const shouldReconnect =
            !this.isIntentionallyClosing &&
            event.code !== 1000 &&
            event.code !== 4001 &&
            this.reconnectAttempts < this.maxReconnectAttempts

          if (shouldReconnect) {
            if (import.meta.env.DEV) {
              console.log(`🔄 计划第 ${this.reconnectAttempts + 1} 次重连...`)
            }
            this.scheduleReconnect()
          } else {
            if (import.meta.env.DEV) console.log('⏹️ 停止重连尝试')
            this.reconnectAttempts = 0
          }

          this.isIntentionallyClosing = false
        }

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket错误:', error)
          this.onErrorCallback?.(error)
          if (!settled) {
            finish(() => {
              reject(error)
              this.flushFileWsWaitersReject(new Error('WebSocket 错误'))
            })
          }
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
    this.detachAndCloseFileSocket(1000, 'Client disconnect')
    this.stopHeartbeat()
    this.reconnectAttempts = 0
    this.flushFileWsWaitersReject(new Error('WebSocket 已断开'))
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
        if (import.meta.env.DEV) console.log('收到未知消息类型:', data.event, data)
    }
  }

  /**
   * 处理进度消息
   * @param message 进度消息
   */
  private handleProgressMessage(message: WebSocketProgressMessage): void {
    if (import.meta.env.DEV) console.log('📈 文件上传进度:', message.progress_percent + '%')
    this.onProgressCallback?.(message)
  }

  /**
   * 处理任务状态消息
   * @param message 任务状态消息
   */
  private handleTaskStatusMessage(message: any): void {
    if (import.meta.env.DEV) console.log('📊 任务状态更新:', message)

    const { job_id, status, progress, result_file, error_message } = message.data || {}

    if (import.meta.env.DEV && progress !== undefined) {
      console.log(`🎯 任务 ${job_id} 进度: ${progress}%`)
    }

    if (import.meta.env.DEV) {
      switch (status) {
        case 'PROCESSING':
          console.log(`🔄 任务 ${job_id} 正在处理中...`)
          break
        case 'COMPLETED':
          console.log(`✅ 任务 ${job_id} 已完成!`)
          if (result_file) console.log(`📁 结果文件: ${result_file}`)
          break
        case 'FAILED':
          console.log(`❌ 任务 ${job_id} 失败!`)
          if (error_message) console.log(`💬 错误信息: ${error_message}`)
          break
      }
    }

    this.onTaskStatusCallback?.(message.data)
  }

  /**
   * 处理心跳响应
   */
  private handleHeartbeatResponse(): void {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout)
    }
  }

  /**
   * 处理连接确认消息
   */
  private handleConnectedMessage(data: any): void {
    if (import.meta.env.DEV) {
      console.log('✅ WebSocket 连接已确认:', data.message || '连接成功')
      if (data.user_id) console.log('👤 用户ID:', data.user_id)
    }
  }

  /**
   * 处理心跳响应消息
   */
  private handlePongMessage(_data: any): void {
    if (import.meta.env.DEV) console.debug('💓 收到心跳响应')
  }

  /**
   * 启动心跳机制
   * 注意：心跳只用于保持连接活跃，不触发重连（避免影响 Vite 代理）
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'heartbeat' })
      }
    }, 60000)
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
    if (import.meta.env.DEV) console.log(`尝试第 ${this.reconnectAttempts} 次重连...`)

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('重连失败:', error)
      })
    }, this.reconnectDelay * this.reconnectAttempts)
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
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
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
