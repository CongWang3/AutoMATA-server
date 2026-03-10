// API类型定义

// 后端API基础响应类型
export interface BaseApiResponse {
  detail?: string
}

// 认证相关类型
export interface User {
  username?: string
  email?: string
  password?: string
}

export interface UserRegister {
  username: string
  email: string
  password: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface UserInfo {
  id: number
  username: string
  email: string
  created_at: string
  is_active: boolean
  avatar_url: string | null
  is_admin: boolean
  last_login_at: string | null
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

// 文件管理相关类型
export interface FileUploadRequest {
  file: File
  file_type: string
  description?: string
}

export interface FileInfo {
  id: string
  filename: string
  original_name: string
  file_path: string
  file_size: number
  file_type: string
  md5_hash: string
  uploaded_by?: number
  upload_time?: string      // 兼容旧版本
  created_at?: string       // 新版本字段
  updated_at?: string
  delete_marked_at?: string | null
  download_count?: number
  is_public?: boolean
}

export interface FileListResponse {
  total: number
  files: FileInfo[]
  page: number
  size: number
}

export interface FileDeleteResponse {
  message: string
  file_id: string
  status: string
}

// WebSocket消息类型
export interface WebSocketProgressMessage {
  event: string
  uploaded_bytes: number
  total_bytes: number
  progress_percent: number
}

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

// 注意：User 相关类型已在前面定义（UserInfo, UserLogin, UserRegister, AuthResponse）
// 为避免类型冲突，此处不再重复定义

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