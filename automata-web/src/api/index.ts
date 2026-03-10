// API入口文件 - 统一导出所有API相关模块

// 核心模块
export { ApiClient, apiClient, createApiClient } from './client'
export { API_CONFIG, ApiError } from './config'
export * from './types'

// 新增的服务模块
export { AuthService } from './auth'
export { FileService } from './files'
export { webSocketService, WebSocketService } from './websocket'
export { DataProcessAPI } from './data-process'

// 业务API
export { trainingApi, TASK_STATUS, MODEL_PARAMETERS } from './training'

// 组合式函数
export {
  useTrainingTasks,
  useTaskStatus,
  usePagination
} from './composables'

// 类型重新导出以便于使用
export type {
  AvailableModel,
  TrainingTask,
  TrainingTaskCreate,
  TrainingTaskUpdate,
  TrainingLog,
  User,
  UserLogin,
  UserRegister,
  AuthResponse,
  UploadResponse,
  TrainingStats,
  WebSocketMessage,
  TaskProgressMessage,
  SuccessResponse,
  ErrorResponse,
  ApiResponse,
  // 新增类型
  UserInfo,
  FileUploadRequest,
  FileInfo,
  FileListResponse,
  FileDeleteResponse,
  WebSocketProgressMessage,
  BaseApiResponse
} from './types'