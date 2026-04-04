/**
 * 数据处理API客户端
 */
import { apiClient } from './client'
import type { BaseApiResponse } from './types'
import { getDownloadOrigin } from '@/config/deploy'

// <!-- 
// 审查上下文：
// - 设计意图：封装数据处理相关的API调用，提供类型安全的接口
// - 已知局限：目前仅实现基因组处理接口，后续需添加转录组等其他处理接口
// - 业务背景：支持前端数据处理页面与后端API的交互
// - 测试重点：请验证文件上传、参数传递、响应处理和错误处理
// -->

interface GenomeProcessResponse extends BaseApiResponse {
  job_id: string
  status: string
  message: string
  created_at: string
}

interface TranscriptomeProcessResponse extends BaseApiResponse {
  job_id: string
  status: string
  message: string
  created_at: string
}

interface ProteinProcessResponse extends BaseApiResponse {
  job_id: string
  status: string
  message: string
  created_at: string
}

interface IntegrationProcessResponse extends BaseApiResponse {
  job_id: string
  status: string
  message: string
  created_at: string
}

interface PvalueIntegrationProcessResponse extends BaseApiResponse {
  job_id: string
  status: string
  message: string
  created_at: string
}

export class DataProcessAPI {
  /**
   * 基因组数据处理
   */
  static async processGenome(formData: FormData): Promise<GenomeProcessResponse> {
    try {
      return await apiClient.post<GenomeProcessResponse>(
        '/v1/data-process/genome',  // 修复：移除重复的 /api 前缀
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('基因组数据处理失败:', error)
      throw error
    }
  }

  /**
   * 转录组数据处理
   */
  static async processTranscriptome(formData: FormData): Promise<TranscriptomeProcessResponse> {
    try {
      return await apiClient.post<TranscriptomeProcessResponse>(
        '/v1/data-process/transcriptome',  // 修复：移除重复的 /api 前缀
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('转录组数据处理失败:', error)
      throw error
    }
  }

  /**
   * 多组学数据整合
   */
  static async processIntegration(formData: FormData): Promise<IntegrationProcessResponse> {
    try {
      return await apiClient.post<IntegrationProcessResponse>(
        '/v1/data-process/integration',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('多组学数据整合失败:', error)
      throw error
    }
  }

  /**
   * pvalue 多组学整合
   */
  static async processPvalueIntegration(
    formData: FormData
  ): Promise<PvalueIntegrationProcessResponse> {
    try {
      return await apiClient.post<PvalueIntegrationProcessResponse>(
        '/v1/data-process/pvalue-integration',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('pvalue 多组学整合失败:', error)
      throw error
    }
  }

  /**
   * 蛋白质数据处理
   */
  static async processProtein(formData: FormData): Promise<ProteinProcessResponse> {
    try {
      return await apiClient.post<ProteinProcessResponse>(
        '/v1/data-process/protein',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )
    } catch (error) {
      console.error('蛋白质数据处理失败:', error)
      throw error
    }
  }

  /**
   * 查询数据处理任务状态
   */
  static async getProcessStatus(jobId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/data-process/status/${jobId}`)  // 修复：移除重复的 /api 前缀
      return response.data
    } catch (error) {
      console.error('查询处理状态失败:', error)
      throw error
    }
  }

  /**
   * 获取当前用户的任务列表
   */
  static async getJobs(limit: number = 20, offset: number = 0): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/data-process/jobs?limit=${limit}&offset=${offset}`)
      return response.data
    } catch (error) {
      console.error('获取任务列表失败:', error)
      throw error
    }
  }

  /**
   * 生成任务结果下载链接
   * 使用独立下载服务（端口8001）
   */
  static getJobResultDownloadUrl(jobId: string, userId: number): string {
    const timestamp = Math.floor(Date.now() / 1000)
    const base = getDownloadOrigin()
    return `${base}/job-result/${jobId}?uid=${userId}&t=${timestamp}`
  }

  /**
   * 从主API获取下载链接（包含签名）
   */
  static async getDownloadUrl(jobId: string): Promise<string> {
    try {
      // <!-- 
      // 审查上下文：
      // - 设计意图：正确处理API客户端返回的数据结构
      // - 已知局限：API客户端已经返回response.data，不需要再访问.data
      // - 业务背景：确保下载链接获取功能的正确性
      // - 测试重点：请验证下载链接的有效性和签名正确性
      // -->
      const response = await apiClient.get(`/v1/data-process/download-url/${jobId}`)
      // API客户端已经返回response.data，直接访问download_url
      return response.download_url
    } catch (error) {
      console.error('获取下载链接失败:', error)
      throw error
    }
  }
}

// 默认导出
export default DataProcessAPI