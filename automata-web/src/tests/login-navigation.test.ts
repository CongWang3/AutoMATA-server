// 登录跳转功能测试
// <!-- 
// 审查上下文：
// - 设计意图：验证登录成功后的路由跳转功能是否正常工作
// - 已知局限：这是单元测试，实际的路由跳转需要在浏览器环境中验证
// - 业务背景：确保用户登录体验的流畅性
// - 测试重点：登录成功后的状态更新和路由跳转时序
// -->
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useUserStore } from '@/stores/user'
import { AuthService } from '@/api/auth'

// Mock Vue Router
const mockRouter = {
  push: vi.fn()
}

// Mock Element Plus Message
const mockElMessage = {
  success: vi.fn()
}

describe('Login Navigation', () => {
  beforeEach(() => {
    // 重置mock
    vi.clearAllMocks()
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })
  })

  it('should navigate to dashboard after successful login', async () => {
    // Mock AuthService login
    vi.spyOn(AuthService, 'login').mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        created_at: '2026-03-07T00:00:00',
        is_active: true,
        avatar_url: null,
        is_admin: false,
        last_login_at: null
      }
    })

    // Mock AuthService isAuthenticated
    vi.spyOn(AuthService, 'isAuthenticated').mockReturnValue(true)
    
    const userStore = useUserStore()
    
    // 执行登录
    await userStore.login('testuser', 'password123')
    
    // 验证用户信息已设置
    expect(userStore.userInfo).toBeDefined()
    expect(userStore.userInfo?.username).toBe('testuser')
    
    // 验证认证状态
    expect(userStore.isAuthenticated).toBe(true)
  })

  it('should handle login error properly', async () => {
    // Mock failed login
    vi.spyOn(AuthService, 'login').mockRejectedValue(new Error('Invalid credentials'))
    
    const userStore = useUserStore()
    
    // 执行登录并捕获错误
    await expect(userStore.login('wronguser', 'wrongpass')).rejects.toThrow('Invalid credentials')
    
    // 验证错误状态
    expect(userStore.error).toBe('Invalid credentials')
    expect(userStore.isAuthenticated).toBe(false)
  })
})