/**
 * 统一任务管理 API 客户端
 * 
 * 提供跨模块的任务查询、取消、删除和下载功能
 */
import { apiClient } from './client'

// ===== 类型定义 =====

/**
 * 统一任务对象
 */
export interface UnifiedJob {
  job_id: string
  job_type: string
  job_type_display: string
  status: string
  status_display: string
  progress: number
  current_step?: string
  input_params?: Record<string, any>
  result_file?: string
  error_message?: string
  created_at?: string
  updated_at?: string
  started_at?: string
  completed_at?: string
}

/**
 * 任务列表响应
 */
export interface JobListResponse {
  total: number
  jobs: UnifiedJob[]
}

/**
 * 任务类型信息
 */
export interface JobTypeInfo {
  value: string
  display_name: string
  count: number
}

/**
 * 任务过滤参数
 */
export interface JobFilter {
  job_type?: string
  status?: string
  /** 按任务 job_id 模糊匹配（后端实现，不区分大小写） */
  keyword?: string
  limit?: number
  offset?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

/**
 * 下载链接响应
 */
export interface DownloadUrlResponse {
  download_url: string
}

// ===== 任务状态常量 =====

export const JOB_STATUS = {
  SUBMITTED: 'Submitted',
  PROCESSING: 'Processing',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
  CANCELLED: 'Cancelled'
} as const

// ===== API 类 =====

class JobsAPI {
  /**
   * 获取任务列表
   */
  async getAllJobs(filter?: JobFilter): Promise<JobListResponse> {
    const params: Record<string, string | number> = {}
    
    if (filter?.job_type) params.job_type = filter.job_type
    if (filter?.status) params.status = filter.status
    if (filter?.keyword) params.keyword = filter.keyword
    params.limit = filter?.limit ?? 20
    params.offset = filter?.offset ?? 0
    if (filter?.sort_by) params.sort_by = filter.sort_by
    if (filter?.sort_order) params.sort_order = filter.sort_order
    
    try {
      return await apiClient.get<JobListResponse>('/v1/jobs', params)
    } catch (error) {
      console.error('获取任务列表失败:', error)
      throw error
    }
  }

  /**
   * 获取任务类型列表（含数量）
   */
  async getJobTypes(): Promise<JobTypeInfo[]> {
    try {
      return await apiClient.get<JobTypeInfo[]>('/v1/jobs/types')
    } catch (error) {
      console.error('获取任务类型列表失败:', error)
      throw error
    }
  }

  /**
   * 获取任务详情
   */
  async getJobDetail(jobId: string): Promise<UnifiedJob> {
    try {
      return await apiClient.get<UnifiedJob>(`/v1/jobs/${jobId}`)
    } catch (error) {
      console.error('获取任务详情失败:', error)
      throw error
    }
  }

  /**
   * 取消任务
   */
  async cancelJob(jobId: string): Promise<UnifiedJob> {
    try {
      return await apiClient.post<UnifiedJob>(`/v1/jobs/${jobId}/cancel`)
    } catch (error) {
      console.error('取消任务失败:', error)
      throw error
    }
  }

  /**
   * 获取下载链接
   */
  async getDownloadUrl(jobId: string): Promise<string> {
    try {
      const response = await apiClient.get<DownloadUrlResponse>(`/v1/jobs/${jobId}/download-url`)
      return response.download_url
    } catch (error) {
      console.error('获取下载链接失败:', error)
      throw error
    }
  }

  /**
   * 删除任务
   */
  async deleteJob(jobId: string): Promise<void> {
    try {
      await apiClient.delete(`/v1/jobs/${jobId}`)
    } catch (error) {
      console.error('删除任务失败:', error)
      throw error
    }
  }
}

// 导出单例实例
export const jobsApi = new JobsAPI()

// 导出类（用于需要自定义实例的场景）
export default JobsAPI
