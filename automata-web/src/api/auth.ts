// 认证API服务
// <!-- 
// 审查上下文：
// - 设计意图：实现与后端JWT认证系统的完整对接，提供注册、登录、用户信息获取等功能
// - 已知局限：当前实现基于JWT Token认证，需要配合后端的认证中间件
// - 业务背景：docs/api/BACKEND_API_REFERENCE.md#认证接口 部分定义的认证流程
// - 测试重点：Token存储、刷新机制、权限验证等核心认证功能
// -->
import { apiClient } from './client'
import type { 
  UserRegister, 
  UserLogin, 
  AuthResponse, 
  UserInfo,
  BaseApiResponse 
} from './types'

export class AuthService {
  private static readonly AUTH_TOKEN_KEY = 'access_token'
  private static readonly USER_INFO_KEY = 'user_info'
  private static readonly TOKEN_EXPIRY_KEY = 'token_expiry'

  /**
   * 用户注册
   * @param userData 注册数据
   * @returns 注册成功的用户信息
   */
  static async register(userData: UserRegister): Promise<UserInfo> {
    try {
      const response = await apiClient.post<UserInfo>('/v1/auth/register', userData)
      return response
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }

  /**
   * 用户登录
   * @param credentials 登录凭据
   * @returns 认证响应，包含token和用户信息
   */
  static async login(credentials: UserLogin): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<AuthResponse>('/v1/auth/login', credentials)
      
      // 存储认证信息
      this.setAuthToken(response.access_token, response.expires_in)
      this.setUserInfo(response.user)
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  /**
   * 获取当前用户信息
   * @returns 当前用户信息
   */
  static async getCurrentUser(): Promise<UserInfo> {
    try {
      // 检查token是否有效
      if (!this.isAuthenticated()) {
        throw new Error('未认证或token已过期')
      }
      
      const response = await apiClient.get<UserInfo>('/v1/auth/me')
      this.setUserInfo(response)
      return response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果是认证错误，清除本地存储
      if ((error as any).response?.status === 401) {
        this.clearAuth()
      }
      throw error
    }
  }

  /**
   * 通知服务端登出（JWT 无状态场景下可为空操作）。
   * 不 await、不清理本地；须在仍持有 token 时调用，与 clearAuth 配合使用。
   */
  static notifyLogout(): void {
    void apiClient.post<BaseApiResponse>('/v1/auth/logout').catch(() => {
      // 网络/网关异常不影响本地登出
    })
  }

  /**
   * 用户登出
   * @returns 登出响应
   */
  static async logout(): Promise<BaseApiResponse> {
    try {
      const response = await apiClient.post<BaseApiResponse>('/v1/auth/logout')
      // 清除本地认证信息
      this.clearAuth()
      return response
    } catch (error) {
      console.error('登出失败:', error)
      // 即使后端登出失败，也要清除本地信息
      this.clearAuth()
      throw error
    }
  }

  /**
   * 检查是否已认证
   * @returns 是否已认证
   */
  static isAuthenticated(): boolean {
    const token = this.getAuthToken()
    const expiry = this.getTokenExpiry()
    
    console.log('🔍 isAuthenticated 检查:')
    console.log('- token exists:', !!token)
    console.log('- expiry exists:', !!expiry)
    console.log('- current time:', Date.now())
    console.log('- expiry time:', expiry ? parseInt(expiry, 10) : 'null')
    console.log('- time comparison:', expiry ? Date.now() < parseInt(expiry, 10) : 'false')
    
    if (!token || !expiry) return false
    
    // 确保expiry不是null再进行转换
    const expiryTime = parseInt(expiry, 10)
    const result = Date.now() < expiryTime
    console.log('- final result:', result)
    return result
  }

  /**
   * 获取存储的认证token
   * @returns 认证token
   */
  static getAuthToken(): string | null {
    return localStorage.getItem(this.AUTH_TOKEN_KEY)
  }

  /**
   * 获取存储的用户信息
   * @returns 用户信息
   */
  static getUserInfo(): UserInfo | null {
    const userInfoStr = localStorage.getItem(this.USER_INFO_KEY)
    return userInfoStr ? JSON.parse(userInfoStr) : null
  }

  /**
   * 设置认证token
   * @param token 访问令牌
   * @param expiresIn 过期时间（秒）
   */
  static setAuthToken(token: string, expiresIn: number): void {
    localStorage.setItem(this.AUTH_TOKEN_KEY, token)
    const expiryTime = Date.now() + (expiresIn * 1000)
    localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString())
  }

  /**
   * 设置用户信息
   * @param userInfo 用户信息
   */
  static setUserInfo(userInfo: UserInfo): void {
    localStorage.setItem(this.USER_INFO_KEY, JSON.stringify(userInfo))
  }

  /**
   * 获取token过期时间
   * @returns 过期时间戳
   */
  private static getTokenExpiry(): string | null {
    return localStorage.getItem(this.TOKEN_EXPIRY_KEY)
  }

  /**
   * 清除所有认证信息
   */
  static clearAuth(): void {
    localStorage.removeItem(this.AUTH_TOKEN_KEY)
    localStorage.removeItem(this.USER_INFO_KEY)
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY)
  }

  /**
   * 刷新认证状态
   * @returns 刷新后的用户信息
   */
  static async refreshAuth(): Promise<UserInfo | null> {
    try {
      const userInfo = await this.getCurrentUser()
      return userInfo
    } catch (error) {
      console.error('刷新认证失败:', error)
      this.clearAuth()
      return null
    }
  }
}

export default AuthService