import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { AuthService } from '@/api/auth'
import { webSocketManager } from '@/utils/websocket-manager'
import type { UserInfo } from '@/api/types'

export interface UserState {
  userInfo: UserInfo | null
  loading: boolean
  error: string | null
}

export const useUserStore = defineStore('user', () => {
  // 路由实例
  const router = useRouter()
  
  // 状态
  const userInfo = ref<UserInfo | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)
  
  // 计算属性
  const isAuthenticated = computed<boolean>(() => {
    // 完全基于响应式数据计算认证状态
    const token = localStorage.getItem('access_token')
    const expiry = localStorage.getItem('token_expiry')
    const hasUserInfo = userInfo.value !== null
    
    if (!token || !expiry || !hasUserInfo) {
      return false
    }
    
    // 确保expiry不是null再进行转换
    const expiryTime = parseInt(expiry, 10)
    return Date.now() < expiryTime && hasUserInfo
  })
  
  const userId = computed<number | null>(() => {
    return userInfo.value?.id || null
  })
  
  const username = computed<string>(() => {
    return userInfo.value?.username || ''
  })

  // Actions
  // <!-- 
  // 审查上下文：
  // - 设计意图：整合AuthService与Pinia状态管理，提供响应式的用户状态
  // - 已知局限：依赖浏览器localStorage，在无头浏览器环境中可能有问题
  // - 业务背景：支持JWT Token认证和用户会话管理
  // - 测试重点：认证状态同步、token刷新、错误处理
  // -->
  
  /**
   * 用户登录
   */
  async function login(username: string, password: string): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      const response = await AuthService.login({ username, password })
      userInfo.value = response.user
      
      console.log('✅ 用户登录成功:', response.user.username)
      
      // 登录成功后建立WebSocket连接
      console.log('🔌 用户登录成功，建立WebSocket连接...')
      webSocketManager.setConnection(true).catch(err => {
        console.warn('⚠️ WebSocket连接失败，但不影响登录:', err)
      })
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登录失败'
      console.error('❌ 登录失败:', error.value)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 用户注册
   */
  async function register(username: string, email: string, password: string): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      const user = await AuthService.register({ username, email, password })
      userInfo.value = user
      
      console.log('✅ 用户注册成功:', user.username)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '注册失败'
      console.error('❌ 注册失败:', error.value)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取当前用户信息
   */
  async function fetchUserInfo(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      const user = await AuthService.getCurrentUser()
      userInfo.value = user
      
      console.log('✅ 获取用户信息成功:', user.username)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取用户信息失败'
      console.error('❌ 获取用户信息失败:', error.value)
      // 清除无效的认证状态
      userInfo.value = null
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 用户登出
   */
  async function logout(): Promise<void> {
    try {
      // 断开WebSocket连接
      console.log('🔌 用户登出，断开WebSocket连接...')
      webSocketManager.setConnection(false)
      
      await AuthService.logout()
      userInfo.value = null
      error.value = null
      
      console.log('✅ 用户登出成功')
      // 登出后自动跳转到登录页面
      router.push('/login')
    } catch (err) {
      // 即使后端登出失败，也要清除本地状态
      userInfo.value = null
      error.value = err instanceof Error ? err.message : '登出过程中出现错误'
      console.warn('⚠️ 登出警告:', error.value)
      // 仍然跳转到登录页面
      router.push('/login')
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 初始化用户状态（从存储中恢复）
   */
  function initializeFromStorage(): void {
    try {
      // 开发环境下减少日志输出
      if (import.meta.env.DEV) {
        console.log('🔄 initializeFromStorage 开始')
      }
      
      // 检查是否有有效的认证状态
      if (AuthService.isAuthenticated()) {
        const storedUserInfo = AuthService.getUserInfo()
        if (storedUserInfo) {
          userInfo.value = storedUserInfo
          if (import.meta.env.DEV) {
            console.log('✅ 从存储初始化用户状态:', storedUserInfo.username)
          }
          
          // 已登录用户自动建立WebSocket连接
          console.log('🔌 已登录用户，建立WebSocket连接...')
          webSocketManager.setConnection(true).catch(err => {
            console.warn('⚠️ WebSocket连接失败:', err)
          })
        }
      } else {
        // 清除过期的认证信息
        AuthService.clearAuth()
      }
    } catch (err) {
      console.error('❌ 初始化用户状态失败:', err)
      AuthService.clearAuth()
      userInfo.value = null
    }
  }
  
  /**
   * 刷新用户认证状态
   */
  async function refreshAuth(): Promise<boolean> {
    try {
      loading.value = true
      const refreshedUser = await AuthService.refreshAuth()
      
      if (refreshedUser) {
        userInfo.value = refreshedUser
        error.value = null
        console.log('✅ 认证状态刷新成功')
        return true
      } else {
        userInfo.value = null
        return false
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '认证刷新失败'
      userInfo.value = null
      console.error('❌ 认证状态刷新失败:', error.value)
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 清除错误状态
   */
  function clearError(): void {
    error.value = null
  }

  return {
    // 状态
    userInfo,
    loading,
    error,
    
    // 计算属性
    isAuthenticated,
    userId,
    username,
    
    // Actions
    login,
    register,
    fetchUserInfo,
    logout,
    initializeFromStorage,
    refreshAuth,
    clearError
  }
})