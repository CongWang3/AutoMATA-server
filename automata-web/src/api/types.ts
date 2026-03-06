// API类型定义

// 可用模型类型
export interface AvailableModel {
  model_type: string
  description: string
  supported: boolean
}

// 训练任务相关类型
export interface TrainingTask {
  id: number
  task_name: string
  model_type: string
  language: string
  status: string
  parameters: string | Record<string, any>
  dataset_path?: string
  result_path?: string
  created_at: string
  updated_at: string
  created_by?: number
}

export interface TrainingTaskCreate {
  task_name: string
  model_type: string
  language?: string
  parameters: string | Record<string, any>
  dataset_path?: string
  created_by?: number
}

export interface TrainingTaskUpdate {
  task_name?: string
  status?: string
  result_path?: string
}

export interface TrainingLog {
  id: number
  task_id: number
  log_level: string
  message: string
  timestamp: string
}

// 用户相关类型
export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface UserRegister {
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// 文件上传相关类型
export interface UploadResponse {
  filename: string
  filepath: string
  size: number
  upload_time: string
}

// 统计数据类型
export interface TrainingStats {
  total_tasks: number
  pending_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
  python_tasks: number
  r_tasks: number
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface TaskProgressMessage extends WebSocketMessage {
  type: 'task_progress'
  data: {
    task_id: number
    progress: number
    status: string
    message: string
  }
}

// 通用响应类型
export interface SuccessResponse<T = any> {
  success: true
  data: T
  message?: string
}

export interface ErrorResponse {
  success: false
  error: string
  message?: string
  code?: string
}

export type ApiResponse<T = any> = SuccessResponse<T> | ErrorResponse