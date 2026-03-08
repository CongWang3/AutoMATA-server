// WebSocket智能连接管理器
// <!-- 
// 审查上下文：
// - 设计意图：根据页面需求智能管理WebSocket连接，避免不必要的连接消耗
// - 已知局限：依赖Vue Router进行路由判断，需要保持路由配置同步
// - 业务背景：优化WebSocket资源使用，提升应用性能
// - 测试重点：连接时机控制、页面切换时的连接管理、内存泄漏防护
// -->

import { webSocketService } from '@/api'
import { useFilesStore } from '@/stores/files'
import type { Router } from 'vue-router'

export class WebSocketManager {
  private static instance: WebSocketManager | null = null
  private router: Router | null = null
  private isActive = false
  private checkDebounceTimer: number | null = null
  private lastCheckTime = 0
  private readonly CHECK_DEBOUNCE_DELAY = 1000 // 1秒防抖延迟
  
  // 需要实时功能的路由
  private readonly REALTIME_ROUTES = [
    '/dashboard',
    '/files',
    '/model/train',
    '/analysis'
  ]

  private constructor() {}

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager()
    }
    return WebSocketManager.instance
  }

  /**
   * 初始化管理器
   * @param router Vue Router实例
   */
  init(router: Router): void {
    this.router = router
    
    // 监听路由变化
    this.router.afterEach((to, from) => {
      this.handleRouteChange(to.path, from.path)
    })
    
    // 初始化连接状态
    this.checkAndManageConnection()
  }

  /**
   * 处理路由变化
   * @param toPath 目标路径
   * @param fromPath 源路径
   */
  private handleRouteChange(toPath: string, fromPath: string): void {
    // 开发环境下减少路由变化日志
    if (import.meta.env.DEV) {
      console.log(`🧭 路由变化: ${fromPath} -> ${toPath}`)
    }
    
    // 添加防抖机制，避免频繁检查
    if (this.checkDebounceTimer) {
      window.clearTimeout(this.checkDebounceTimer)
    }
    
    this.checkDebounceTimer = window.setTimeout(() => {
      this.checkAndManageConnection()
      this.checkDebounceTimer = null
    }, this.CHECK_DEBOUNCE_DELAY)
  }

  /**
   * 检查并管理WebSocket连接
   */
  private async checkAndManageConnection(): Promise<void> {
    if (!this.router) return

    const currentPath = this.router.currentRoute.value.path
    const needsRealtime = this.needsRealtimeFeatures(currentPath)
    
    // 记录检查时间，避免过于频繁的检查
    const now = Date.now()
    if (now - this.lastCheckTime < 500) { // 最少500ms间隔
      console.log('⏱️ 连接检查过于频繁，跳过本次检查')
      return
    }
    this.lastCheckTime = now
    
    // 开发环境下减少连接状态检查日志
    if (import.meta.env.DEV) {
      console.log(`🔍 连接状态检查 - 当前路径: ${currentPath}, 需要实时: ${needsRealtime}, 已激活: ${this.isActive}`)
    }
    
    // 更智能的连接管理逻辑
    if (needsRealtime) {
      // 需要实时功能的页面
      if (!this.isActive) {
        if (import.meta.env.DEV) console.log('🔌 需要启用实时连接')
        await this.connect()
      } else if (!webSocketService.isConnected()) {
        if (import.meta.env.DEV) console.log('🔄 实时连接已断开，尝试重连')
        await this.reconnect()
      } else {
        if (import.meta.env.DEV) console.log('✅ 实时连接正常，无需操作')
      }
    } else {
      // 不需要实时功能的页面
      if (this.isActive) {
        if (import.meta.env.DEV) console.log('🔌 需要禁用实时连接')
        await this.disconnect()
      } else {
        if (import.meta.env.DEV) console.log('✅ 实时连接已禁用，无需操作')
      }
    }
  }

  /**
   * 判断当前路由是否需要实时功能
   * @param path 当前路径
   * @returns 是否需要实时功能
   */
  private needsRealtimeFeatures(path: string): boolean {
    return this.REALTIME_ROUTES.some(route => path.startsWith(route))
  }

  /**
   * 建立WebSocket连接
   */
  private async connect(): Promise<void> {
    try {
      console.log('🔌 建立WebSocket连接...')
      await webSocketService.connect()
      
      // 设置文件上传进度回调
      const filesStore = useFilesStore()
      webSocketService.setOnProgress((message) => {
        console.log('📥 收到实时消息:', message)
        // 处理文件上传进度消息
        if (message.event === 'upload_progress') {
          // 查找正在上传的文件并更新进度
          this.updateUploadProgressFromWebSocket(filesStore, message)
        }
      })
      
      this.isActive = true
      console.log('✅ WebSocket连接建立成功')
    } catch (error) {
      console.error('❌ WebSocket连接失败:', error)
      this.isActive = false
    }
  }

  /**
   * 从WebSocket消息更新上传进度
   * @param filesStore 文件存储实例
   * @param message WebSocket进度消息
   */
  private updateUploadProgressFromWebSocket(
    filesStore: ReturnType<typeof useFilesStore>,
    message: import('@/api/types').WebSocketProgressMessage
  ): void {
    try {
      const progress = Math.round(message.progress_percent)
      
      // 获取当前所有正在上传的文件
      const uploadingFiles = filesStore.uploadingFiles
      
      // 如果只有一个上传任务，直接更新它
      if (uploadingFiles.size === 1) {
        const firstKey = Array.from(uploadingFiles.keys())[0]
        if (firstKey !== undefined) {
          filesStore.updateUploadProgress(firstKey, progress)
          console.log(`📊 更新上传进度: ${firstKey} -> ${progress}%`)
        }
        return
      }
      
      // 如果有多个上传任务，尝试根据进度匹配最合适的任务
      // 这里可以添加更复杂的匹配逻辑
      if (uploadingFiles.size > 1) {
        console.warn('⚠️ 检测到多个并发上传任务，无法精确匹配进度更新')
        // 可以选择更新最近开始的上传任务
        const latestUpload = Array.from(uploadingFiles.entries())
          .filter(([_, item]) => item.status === 'uploading')
          .sort(([_, a], [__, b]) => b.progress - a.progress)[0]
        
        if (latestUpload) {
          const [uploadId] = latestUpload
          if (uploadId !== undefined) {
            filesStore.updateUploadProgress(uploadId, progress)
            console.log(`📊 更新最新上传任务进度: ${uploadId} -> ${progress}%`)
          }
        }
      }
      
      // 如果没有上传任务但收到进度消息，可能是之前的任务
      if (uploadingFiles.size === 0) {
        console.log('ℹ️ 收到上传进度消息但没有活跃的上传任务')
      }
      
    } catch (error) {
      console.error('❌ 处理WebSocket进度消息时出错:', error)
    }
  }

  /**
   * 断开WebSocket连接
   */
  private async disconnect(): Promise<void> {
    try {
      console.log('🔌 断开WebSocket连接...')
      webSocketService.disconnect()
      this.isActive = false
      console.log('✅ WebSocket连接已断开')
    } catch (error) {
      console.error('❌ WebSocket断开失败:', error)
    }
  }

  /**
   * 强制重新连接
   */
  async reconnect(): Promise<void> {
    await this.disconnect()
    await this.connect()
  }

  /**
   * 获取当前连接状态
   * @returns 连接状态
   */
  getStatus(): {
    isActive: boolean
    isConnected: boolean
    currentRoute: string
  } {
    const currentRoute = this.router?.currentRoute.value.path;
    return {
      isActive: this.isActive,
      isConnected: webSocketService.isConnected(),
      currentRoute: currentRoute !== undefined ? currentRoute : 'unknown'
    }
  }

  /**
   * 手动控制连接
   * @param shouldConnect 是否应该连接
   */
  async setConnection(shouldConnect: boolean): Promise<void> {
    if (shouldConnect && !this.isActive) {
      await this.connect()
    } else if (!shouldConnect && this.isActive) {
      await this.disconnect()
    }
  }
}

// 导出单例实例
export const webSocketManager = WebSocketManager.getInstance()
export default WebSocketManager