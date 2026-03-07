// 文件管理API服务
// <!-- 
// 审查上下文：
// - 设计意图：实现完整的文件上传、下载、管理功能，支持多种文件类型和进度监控
// - 已知局限：大文件上传可能存在内存问题，需要后续优化为分片上传
// - 业务背景：docs/api/BACKEND_API_REFERENCE.md#文件管理接口 部分定义的文件操作流程
// - 测试重点：文件上传进度、错误处理、文件类型验证、大文件支持
// -->
import { apiClient } from './client'
import type { 
  FileInfo, 
  FileListResponse, 
  FileDeleteResponse,
  BaseApiResponse 
} from './types'

export class FileService {
  private static readonly FILE_TYPES = [
    'dataset',
    'train', 
    'validation',
    'test',
    'kfold_dataset'
  ]

  /**
   * 上传文件
   * @param file 文件对象
   * @param fileType 文件类型
   * @param description 文件描述（可选）
   * @param onProgress 进度回调函数
   * @returns 上传成功的文件信息
   */
  static async uploadFile(
    file: File, 
    fileType: string, 
    description?: string,
    onProgress?: (progress: number) => void
  ): Promise<FileInfo> {
    try {
      // 验证文件类型
      if (!this.FILE_TYPES.includes(fileType)) {
        throw new Error(`不支持的文件类型: ${fileType}`)
      }

      // 验证文件大小（100MB限制）
      const maxSize = 100 * 1024 * 1024
      if (file.size > maxSize) {
        throw new Error('文件大小不能超过100MB')
      }

      const formData = new FormData()
      formData.append('file', file)
      formData.append('file_type', fileType)
      if (description) {
        formData.append('description', description)
      }

      // 使用axios实例直接发送请求以支持进度监控
      const response = await apiClient.getInstance().post<FileInfo>(
        '/v1/files/upload', 
        formData, 
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5分钟超时
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total && onProgress) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              onProgress(progress)
            }
          }
        }
      )

      return response.data
    } catch (error) {
      console.error('文件上传失败:', error)
      throw error
    }
  }

  /**
   * 获取文件列表（支持分页）
   * @param page 页码（从1开始）
   * @param size 每页数量
   * @returns 文件列表响应
   */
  static async getFileList(page: number = 1, size: number = 20): Promise<FileListResponse> {
    try {
      const response = await apiClient.get<FileListResponse>('/v1/files/', {
        page: Math.max(1, page),
        size: Math.min(100, Math.max(1, size))
      })
      return response
    } catch (error) {
      console.error('获取文件列表失败:', error)
      throw error
    }
  }

  /**
   * 获取文件详情
   * @param fileId 文件ID
   * @returns 文件详细信息
   */
  static async getFileInfo(fileId: string): Promise<FileInfo> {
    try {
      const response = await apiClient.get<FileInfo>(`/files/${fileId}`)
      return response
    } catch (error) {
      console.error('获取文件详情失败:', error)
      throw error
    }
  }

  /**
   * 下载文件
   * @param fileId 文件ID
   * @param filename 下载文件名（可选）
   * @returns 下载的Blob对象
   */
  static async downloadFile(fileId: string, filename?: string): Promise<Blob> {
    try {
      const response = await apiClient.getInstance().get(`/v1/files/${fileId}/download`, {
        responseType: 'blob'
      })

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename || response.headers['content-disposition']?.split('filename=')[1] || 'download')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      return response.data
    } catch (error) {
      console.error('文件下载失败:', error)
      throw error
    }
  }

  /**
   * 删除文件
   * @param fileId 文件ID
   * @returns 删除响应
   */
  static async deleteFile(fileId: string): Promise<FileDeleteResponse> {
    try {
      const response = await apiClient.delete<FileDeleteResponse>(`/v1/files/${fileId}`)
      return response
    } catch (error) {
      console.error('文件删除失败:', error)
      throw error
    }
  }

  /**
   * 获取支持的文件类型
   * @returns 支持的文件类型数组
   */
  static getSupportedFileTypes(): string[] {
    return [...this.FILE_TYPES]
  }

  /**
   * 格式化文件大小
   * @param bytes 字节数
   * @returns 格式化的文件大小字符串
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  /**
   * 验证文件类型是否支持
   * @param fileType 文件类型
   * @returns 是否支持
   */
  static isFileTypeSupported(fileType: string): boolean {
    return this.FILE_TYPES.includes(fileType)
  }

  /**
   * 根据文件扩展名推断文件类型
   * @param filename 文件名
   * @returns 推断的文件类型
   */
  static inferFileType(filename: string): string {
    const extension = filename.toLowerCase().split('.').pop() || ''
    
    switch (extension) {
      case 'txt':
        return 'dataset'
      case 'csv':
        return 'dataset'
      case 'xlsx':
      case 'xls':
        return 'dataset'
      default:
        return 'dataset' // 默认类型
    }
  }
}

export default FileService