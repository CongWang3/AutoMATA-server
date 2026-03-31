// API客户端工厂
import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { API_CONFIG, ApiError } from './config'

export class ApiClient {
  private client: AxiosInstance

  constructor(baseURL: string = API_CONFIG.BASE_URL) {
    console.log('🔧 API Client 初始化:', { 
      baseURL, 
      envBaseUrl: import.meta.env.VITE_API_BASE_URL,
      configBaseUrl: API_CONFIG.BASE_URL 
    })

        
    this.client = axios.create({
      baseURL,
      timeout: API_CONFIG.TIMEOUT,
      headers: API_CONFIG.HEADERS,
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = localStorage.getItem('access_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        // 添加请求时间戳
        config.headers['X-Request-Time'] = new Date().toISOString()
        
        console.log('🚀 API Request:', {
          method: config.method?.toUpperCase(),
          url: config.url,
          params: config.params,
          data: config.data  // 原来的代码
          // data: (() => {
          //   const u = String(config.url || '')
          //   if (u.includes('/auth/login') || u.includes('/auth/register')) return '[REDACTED]'
          //   return config.data
          // })()
        })

                
        return config
      },
      (error) => {
        console.error('❌ Request Error:', error)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log('✅ API Response:', {
          status: response.status,
          url: response.config.url,
          data: response.data
        })
        return response
      },
      (error) => {
        const errorMessage = this.handleError(error)
        console.error('❌ API Error:', errorMessage)

        
        return Promise.reject(new ApiError(errorMessage, error.response?.status))
      }
    )
  }

  private handleError(error: any): string {
    if (error.response) {
      // 服务器响应错误
      const { status, data } = error.response
      switch (status) {
        case 400:
          return data?.detail || data?.message || 'Invalid request parameters'
        case 401:
          // 处理未授权，可能需要跳转登录
          localStorage.removeItem('access_token')
          localStorage.removeItem('user_info')
          localStorage.removeItem('token_expiry')
          return 'Unauthorized'
        case 403:
          return 'Forbidden'
        case 404:
          return 'Resource not found'
        case 500:
          return 'Internal server error'
        default:
          return data?.detail || data?.message || `HTTP ${status} error`
      }
    } else if (error.request) {
      // 网络错误
      return 'Network error. Please check your connection.'
    } else {
      // 其他错误
      return error.message || 'Unknown error'
    }
  }

  // 通用请求方法
  public async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.client.request<T>(config)
      return response.data
    } catch (error) {
      throw error
    }
  }

  // GET请求
  public async get<T = any>(url: string, params?: any): Promise<T> {
    return this.request<T>({ method: 'GET', url, params })
  }

  // POST请求
  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ method: 'POST', url, data, ...config })
  }

  // PUT请求
  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ method: 'PUT', url, data, ...config })
  }

  // DELETE请求
  public async delete<T = any>(url: string): Promise<T> {
    return this.request<T>({ method: 'DELETE', url })
  }

  // PATCH请求
  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ method: 'PATCH', url, data, ...config })
  }

  // 获取原始axios实例（用于特殊情况）
  public getInstance(): AxiosInstance {
    return this.client
  }
}

// 创建默认API客户端实例
export const apiClient = new ApiClient()

// 导出工厂函数，用于创建自定义API客户端
export function createApiClient(baseURL?: string): ApiClient {
  return new ApiClient(baseURL)
}

export default ApiClient