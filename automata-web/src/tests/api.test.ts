// API服务测试
// <!-- 
// 审查上下文：
// - 设计意图：验证新创建的API服务模块功能正确性
// - 已知局限：这些是基础功能测试，实际使用中需要更多边界情况测试
// - 业务背景：确保认证、文件管理、WebSocket等核心功能正常工作
// - 测试重点：API调用、错误处理、状态管理
// -->
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { AuthService } from '@/api/auth'
import { FileService } from '@/api/files'
import { webSocketService } from '@/api/websocket'

// Mock localStorage
const mockLocalStorage = {
  store: {} as Record<string, string>,
  getItem(key: string) {
    return this.store[key] || null
  },
  setItem(key: string, value: string) {
    this.store[key] = value
  },
  removeItem(key: string) {
    delete this.store[key]
  },
  clear() {
    this.store = {}
  }
}

describe('AuthService', () => {
  beforeEach(() => {
    // 重置mock数据
    mockLocalStorage.clear()
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true
    })
  })

  it('should set and get auth token correctly', () => {
    const token = 'test-token'
    const expiresIn = 3600
    
    AuthService.setAuthToken(token, expiresIn)
    
    expect(AuthService.getAuthToken()).toBe(token)
    expect(AuthService.isAuthenticated()).toBe(true)
  })

  it('should clear auth data', () => {
    AuthService.setAuthToken('test-token', 3600)
    AuthService.setUserInfo({
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      created_at: '2026-03-07T00:00:00',
      is_active: true,
      avatar_url: null,
      is_admin: false,
      last_login_at: null
    })
    
    AuthService.clearAuth()
    
    expect(AuthService.getAuthToken()).toBeNull()
    expect(AuthService.getUserInfo()).toBeNull()
    expect(AuthService.isAuthenticated()).toBe(false)
  })

  it('should detect expired token', () => {
    // 设置一个已经过期的token
    const pastTime = Date.now() - 1000
    localStorage.setItem('token_expiry', pastTime.toString())
    localStorage.setItem('access_token', 'expired-token')
    
    expect(AuthService.isAuthenticated()).toBe(false)
  })
})

describe('FileService', () => {
  it('should format file size correctly', () => {
    expect(FileService.formatFileSize(0)).toBe('0 Bytes')
    expect(FileService.formatFileSize(1024)).toBe('1 KB')
    expect(FileService.formatFileSize(1024 * 1024)).toBe('1 MB')
    expect(FileService.formatFileSize(1024 * 1024 * 1024)).toBe('1 GB')
  })

  it('should validate supported file types', () => {
    expect(FileService.isFileTypeSupported('dataset')).toBe(true)
    expect(FileService.isFileTypeSupported('train')).toBe(true)
    expect(FileService.isFileTypeSupported('unsupported')).toBe(false)
  })

  it('should infer file type from filename', () => {
    expect(FileService.inferFileType('data.txt')).toBe('dataset')
    expect(FileService.inferFileType('data.csv')).toBe('dataset')
    expect(FileService.inferFileType('data.xlsx')).toBe('dataset')
  })
})

describe('WebSocketService', () => {
  it('should get singleton instance', () => {
    const instance1 = webSocketService
    const instance2 = webSocketService
    
    expect(instance1).toBe(instance2)
  })

  it('should track connection status', () => {
    expect(webSocketService.isConnected()).toBe(false)
    expect(webSocketService.getReadyState()).toBe(WebSocket.CLOSED)
  })
})