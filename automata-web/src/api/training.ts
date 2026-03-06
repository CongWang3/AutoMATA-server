// 训练任务API接口
import { apiClient } from './client'
import { API_CONFIG } from './config'
import type { TrainingTask, TrainingTaskCreate, TrainingTaskUpdate, TrainingLog, AvailableModel } from './types'
import type { AxiosProgressEvent } from 'axios'





// 训练任务相关API
export const trainingApi = {
  // 获取可用模型列表
  async getAvailableModels(): Promise<AvailableModel[]> {
    const response = await apiClient.get<{models: AvailableModel[]}>('/training/models/available')
    return response.models
  },
  // 获取训练任务列表
  async getTasks(skip: number = 0, limit: number = 100): Promise<TrainingTask[]> {
    return apiClient.get<TrainingTask[]>(`/training/tasks`, { skip, limit })
  },

  // 获取单个训练任务
  async getTask(taskId: number): Promise<TrainingTask> {
    return apiClient.get<TrainingTask>(`/training/tasks/${taskId}`)
  },

  // 创建训练任务
  async createTask(taskData: TrainingTaskCreate): Promise<TrainingTask> {
    // 转换参数格式以匹配后端要求
    const formattedData = {
      task_name: taskData.task_name,
      model_type: taskData.model_type,
      language: taskData.language || 'python',
      parameters: typeof taskData.parameters === 'string' 
        ? taskData.parameters 
        : JSON.stringify(taskData.parameters),
      dataset_path: taskData.dataset_path,
      created_by: taskData.created_by
    }
    return apiClient.post<TrainingTask>('/training/tasks', formattedData)
  },

  // 更新训练任务
  async updateTask(taskId: number, taskData: TrainingTaskUpdate): Promise<TrainingTask> {
    return apiClient.put<TrainingTask>(`/training/tasks/${taskId}`, taskData)
  },

  // 删除训练任务
  async deleteTask(taskId: number): Promise<void> {
    return apiClient.delete<void>(`/training/tasks/${taskId}`)
  },

  // 获取训练日志
  async getTaskLogs(taskId: number): Promise<TrainingLog[]> {
    return apiClient.get<TrainingLog[]>(`/training/tasks/${taskId}/logs`)
  },

  // 添加训练日志
  async addTaskLog(taskId: number, logData: { log_level: string; message: string }): Promise<void> {
    return apiClient.post<void>(`/training/tasks/${taskId}/logs`, logData)
  },

  // 文件上传相关API
  async uploadFile(file: File, fileType: string = 'dataset', onUploadProgress?: (progressEvent: AxiosProgressEvent) => void): Promise<{ file_id: string; file_path: string }> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType) // 添加必需的文件类型参数
    
    // 直接使用完整的URL，绕过默认的/api前缀
    const fullUrl = `${API_CONFIG.BASE_URL.replace('/api', '')}/training/files/upload`
    
    return apiClient.getInstance().post<{ file_id: string; file_path: string }>(fullUrl, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress
    }).then(response => response.data)
  },

  // 获取文件下载链接
  async getFileDownloadUrl(fileId: string): Promise<string> {
    const response = await apiClient.get<{ download_url: string }>(`/training/files/${fileId}/download`)
    return response.download_url
  },

  // 删除文件
  async deleteFile(fileId: string): Promise<void> {
    return apiClient.delete<void>(`/training/files/${fileId}`)
  }
}

// 任务状态常量
export const TASK_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const

// 常用模型参数配置
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

// 导出默认实例
export default trainingApi