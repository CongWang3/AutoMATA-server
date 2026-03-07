// API配置和通用工具
// <!-- 
// 审查上下文：
// - 设计意图：使用环境变量配置API端点，支持不同环境部署
// - 已知局限：当前配置适用于开发环境，生产环境需要HTTPS和域名配置
// - 业务背景：支持前后端分离部署，便于维护和扩展
// - 测试重点：验证不同环境下API连接的正确性
// -->
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  TIMEOUT: 300000, // 5分钟超时，适应大文件上传
  HEADERS: {
    'Content-Type': 'application/json',
  }
}

// API错误处理
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// 分页参数接口
export interface PaginationParams {
  skip?: number
  limit?: number
  page?: number
  pageSize?: number
}

// 分页响应接口
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 通用API响应接口
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// 请求方法枚举
export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH'
}

// 通用请求配置
export interface RequestConfig {
  method?: HttpMethod
  url: string
  data?: any
  params?: Record<string, any>
  headers?: Record<string, string>
  timeout?: number
}