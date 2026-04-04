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
import { JobApiBase } from './jobApiBase'

// 监督学习训练响应
export interface SupervisedTrainResponse extends BaseApiResponse {
  task_name: string
  model_type: string
  status: string
  job_id: string
  message: string
  created_at: string
  parameters?: any
  progress?: number        // 进度百分比 0-100
  current_step?: string    // 当前执行步骤描述
  result_file?: string     // 结果文件路径
  error_message?: string   // 错误信息
}

// 训练文件上传响应
export interface TrainingFileUploadResponse {
  file_id: string
  file_path: string
}

// 训练类型枚举
type TrainingType = 'supervised' | 'unsupervised' | 'semi-supervised'

const trainingEndpointMap: Record<TrainingType, { path: string; logPrefix: string }> = {
  supervised: { path: '/v1/training/supervised', logPrefix: '监督学习' },
  unsupervised: { path: '/v1/training/unsupervised', logPrefix: '无监督学习' },
  'semi-supervised': { path: '/v1/training/semi-supervised', logPrefix: '半监督学习' }
}

export class TrainingAPI extends JobApiBase<TrainingFileUploadResponse, any> {
  constructor() {
    super('/v1/training')
  }

  /**
   * 获取可用模型列表
   */
  async getAvailableModels(): Promise<Array<{ model_type: string; description: string }>> {
    try {
      const response = await apiClient.get<Array<{ model_type: string; description: string }>>('/v1/training/models')
      return response
    } catch (error) {
      console.error('获取可用模型列表失败:', error)
      // 返回默认模型列表
      return [
        { model_type: 'cnn', description: '卷积神经网络' },
        { model_type: 'lstm', description: '长短期记忆网络' },
        { model_type: 'mlp', description: '多层感知机' }
      ]
    }
  }

  /**
   * 监督学习训练任务提交（实例方法）
   */
  async trainSupervised(payload: {
    task_name: string
    model_type: string
    parameters: any
    email?: string
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    return TrainingAPI.trainSupervised(payload)
  }

  /**
   * 无监督学习训练任务提交（实例方法）
   */
  async trainUnsupervised(payload: {
    task_name: string
    model_type: string
    parameters: any
    email?: string
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    return TrainingAPI.trainUnsupervised(payload)
  }

  /**
   * 半监督学习训练任务提交（实例方法）
   */
  async trainSemiSupervised(payload: {
    task_name: string
    model_type: string
    parameters: any
    email?: string
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    return TrainingAPI.trainSemiSupervised(payload)
  }

  /**
   * 创建训练任务（通用入口）
   */
  static async createTask(payload: {
    task_name: string
    model_type: string
    parameters: any
    email?: string
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    // 默认使用监督学习训练
    return this.trainSupervised(payload)
  }

  /**
   * 通用训练任务创建方法
   */
  private static async createTrainingTask(
    type: TrainingType,
    payload: {
      task_name: string
      model_type: string
      parameters: any
      email?: string
      dataset_path?: string
    }
  ): Promise<SupervisedTrainResponse> {
    const { path, logPrefix } = trainingEndpointMap[type]
    try {
      return await apiClient.post<SupervisedTrainResponse>(path, payload)
    } catch (error) {
      console.error(`创建${logPrefix}训练任务失败:`, error)
      throw error
    }
  }

  /**
   * 监督学习训练任务提交
   */
  static async trainSupervised(payload: {
    task_name: string
    model_type: string
    parameters: any
    email?: string
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    return this.createTrainingTask('supervised', payload)
  }

  /**
   * 无监督学习训练任务提交
   */
  static async trainUnsupervised(payload: {
    task_name: string
    model_type: string
    parameters: any
    email?: string
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    return this.createTrainingTask('unsupervised', payload)
  }

  /**
   * 半监督学习训练任务提交
   */
  static async trainSemiSupervised(payload: {
    task_name: string
    model_type: string
    parameters: any
    email?: string
    dataset_path?: string
  }): Promise<SupervisedTrainResponse> {
    return this.createTrainingTask('semi-supervised', payload)
  }

  /**
   * 生成任务结果下载链接（不带签名，直接指向 8001 端口的下载服务）
   * 注意：前端无法生成 HMAC 签名，这个方法主要用于简单场景或调试。
   */
  static getJobResultDownloadUrl(jobId: string, userId: number): string {
    const timestamp = Math.floor(Date.now() / 1000)
    const base = import.meta.env.PROD
      ? `${window.location.origin}`
      : 'http://localhost:8001'
    return `${base}/job-result/${jobId}?uid=${userId}&t=${timestamp}`
  }

  /**
   * 获取带签名的训练任务结果下载链接
   */
  async getDownloadUrl(jobId: string): Promise<{ download_url: string; expires_in: number }> {
    try {
      const response = await apiClient.get<{ download_url: string; expires_in: number }>(
        `/v1/training/download-url/${jobId}`
      )
      return response
    } catch (error) {
      console.error('获取下载链接失败:', error)
      throw error
    }
  }
}

// 任务状态常量（与后端Job状态枚举值对齐，首字母大写）
export const TASK_STATUS = {
  SUBMITTED: 'Submitted',    // 已提交
  PROCESSING: 'Processing',  // 处理中
  COMPLETED: 'Completed',    // 已完成
  FAILED: 'Failed',          // 失败
  CANCELLED: 'Cancelled',    // 已取消
  // 兼容旧版本小写状态
  PENDING: 'pending',
  RUNNING: 'running'
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
export const trainingApi = new TrainingAPI()
export default TrainingAPI