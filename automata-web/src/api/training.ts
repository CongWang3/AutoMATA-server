/**
 * 模型训练 API 客户端
 *
 * 设计风格与数据处理模块 (`data-process.ts`) 保持一致：
 * - 使用 apiClient 统一封装
 * - 为不同训练功能提供清晰的静态方法
 * - 目前仅实现监督学习训练和文件上传，后续可扩展无监督、半监督、模型应用等接口
 */
import { apiClient } from './client'
import type { BaseApiResponse } from './types'
import type { AxiosProgressEvent } from 'axios'

// 监督学习训练响应
export interface SupervisedTrainResponse extends BaseApiResponse {
  task_name: string
  model_type: string
  status: string
  job_id: string
  message: string
  created_at: string
}

// 训练文件上传响应
export interface TrainingFileUploadResponse {
  file_id: string
  file_path: string
}

export class TrainingAPI {
  /**
   * 监督学习训练任务提交
   *
   * 对应后端：POST /api/v1/training/supervised
   * 当前用于 Supervised 模型训练，后续可扩展更多训练方法
   */
  static async trainSupervised(payload: {
    task_name: string
    model_type: string
    parameters: any
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    try {
      return await apiClient.post<SupervisedTrainResponse>(
        '/v1/training/supervised',
        {
          task_name: payload.task_name,
          model_type: payload.model_type,
          parameters: payload.parameters,
          dataset_path: payload.dataset_path
        }
      )
    } catch (error) {
      console.error('创建监督学习训练任务失败:', error)
      throw error
    }
  }

  /**
   * 训练相关文件上传
   *
   * 对应后端：POST /api/v1/training/files/upload
   */
  static async uploadFile(
    file: File,
    fileType: string = 'dataset',
    onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
  ): Promise<TrainingFileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType)

    const response = await apiClient.post<TrainingFileUploadResponse>(
      '/v1/training/files/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress
      }
    )
    return response
  }

  /**
   * 查询训练任务状态
   */
  static async getStatus(jobId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/training/status/${jobId}`)
      return (response as any).data ?? response
    } catch (error) {
      console.error('查询训练任务状态失败:', error)
      throw error
    }
  }

  /**
   * 获取当前用户的训练任务列表
   */
  static async getJobs(limit: number = 20, offset: number = 0): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/training/jobs?limit=${limit}&offset=${offset}`)
      return (response as any).data ?? response
    } catch (error) {
      console.error('获取训练任务列表失败:', error)
      throw error
    }
  }

  /**
   * 生成任务结果下载链接（不带签名，直接指向 8001 端口的下载服务）
   * 注意：前端无法生成 HMAC 签名，这个方法主要用于简单场景或调试。
   */
  static getJobResultDownloadUrl(jobId: string, userId: number): string {
    const timestamp = Math.floor(Date.now() / 1000)
    return `http://localhost:8001/job-result/${jobId}?uid=${userId}&t=${timestamp}`
  }

  /**
   * 从主 API 获取带签名的任务结果下载链接
   */
  static async getDownloadUrl(jobId: string): Promise<string> {
    try {
      const response = await apiClient.get(`/v1/training/download-url/${jobId}`)
      return (response as any).download_url ?? (response as any).data?.download_url
    } catch (error) {
      console.error('获取训练结果下载链接失败:', error)
      throw error
    }
  }
}

// 任务状态常量（保持与原有导出兼容，便于复用）
export const TASK_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const

// 常用模型参数配置（预留给前端表单使用）
export const MODEL_PARAMETERS = {
  mlp: {
    epochs: 100,
    batch_size: 32,
    learning_rate: 0.001,
    dropout_rate: 0.2
  },
  cnn: {
    epochs: 50,
    batch_size: 16,
    learning_rate: 0.001,
    conv_layers: 2,
    filters: [32, 64]
  },
  lstm: {
    epochs: 30,
    batch_size: 8,
    learning_rate: 0.01,
    hidden_units: 128,
    sequence_length: 50
  }
}

// 与数据处理模块类似，导出类名和默认实例别名
export const trainingApi = TrainingAPI
export default TrainingAPI