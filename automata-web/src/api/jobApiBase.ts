import { apiClient } from './client'
import type { AxiosProgressEvent } from 'axios'

/**
 * 基于Job的通用API基类
 * 提供文件上传、任务状态查询、任务列表获取等通用功能
 */

export class JobApiBase<TUploadResponse, TStatusResponse> {
  constructor(private basePath: string) {}

  /**
   * 文件上传
   */
  async uploadFile(
    file: File,
    fileType: string = 'dataset',
    onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
  ): Promise<TUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType)

    const response = await apiClient.post<TUploadResponse>(
      `${this.basePath}/files/upload`,
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
   * 查询任务状态
   */
  async getStatus(jobId: string): Promise<TStatusResponse> {
    try {
      const response = await apiClient.get(`${this.basePath}/status/${jobId}`)
      return (response as any).data ?? response
    } catch (error) {
      console.error(`查询任务状态失败:`, error)
      throw error
    }
  }

  /**
   * 获取当前用户的任务列表
   */
  async getJobs(limit: number = 20, offset: number = 0): Promise<any> {
    try {
      const response = await apiClient.get(`${this.basePath}/jobs?limit=${limit}&offset=${offset}`)
      return (response as any).data ?? response
    } catch (error) {
      console.error('获取任务列表失败:', error)
      throw error
    }
  }

  /**
   * 生成任务结果下载链接
   */
  async getDownloadUrl(jobId: string): Promise<string> {
    try {
      const response = await apiClient.get(`${this.basePath}/download-url/${jobId}`)
      return (response as any).download_url ?? (response as any).data?.download_url
    } catch (error) {
      console.error('获取任务结果下载链接失败:', error)
      throw error
    }
  }
}