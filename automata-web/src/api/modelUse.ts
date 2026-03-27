/**
 * 模型使用 API 客户端
 * 
 * 用于模型预测和推理功能
 */
import { apiClient } from './client'
import type { BaseApiResponse } from '../types'
import { JobApiBase } from './jobApiBase'

// 模型预测响应
export interface ModelPredictResponse extends BaseApiResponse {
  job_id: string
  model_type: string
  status: string
  message: string
  created_at: string
}

// 模型文件上传响应
export interface ModelFileUploadResponse {
  id: string
  file_path: string
}

export class ModelUseAPI extends JobApiBase<ModelFileUploadResponse, any> {
  constructor() {
    // 上传使用通用文件上传接口：/api/v1/files/upload
    // 预测接口仍使用 /api/v1/model-use/predict
    super('/v1')
  }

  /**
   * 模型预测任务提交
   */
  async predict(payload: {
    model_type: string
    test_data_path: string
    email?: string
    model_path?: string
    som_model_path?: string
    winmap_path?: string
    encoder_path?: string
    classifier_path?: string
    scaler_path?: string
    un_semi_model_path?: string
  }): Promise<ModelPredictResponse> {
    try {
      return await apiClient.post<ModelPredictResponse>(
        '/v1/model-use/predict',
        payload
      )
    } catch (error) {
      console.error('创建模型预测任务失败:', error)
      throw error
    }
  }
}

// 导出默认实例
export const modelUseApi = new ModelUseAPI()
export default ModelUseAPI