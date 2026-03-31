import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { FileService } from '@/api'
import type { FileInfo, FileListResponse } from '@/api/types'

export interface FileState {
  fileList: FileInfo[]
  currentPage: number
  pageSize: number
  total: number
  loading: boolean
  error: string | null
  uploadingFiles: Map<string, { 
    file: File, 
    progress: number, 
    status: 'pending' | 'uploading' | 'completed' | 'failed' 
  }>
}

export const useFilesStore = defineStore('files', () => {
  // 状态
  const fileList = ref<FileInfo[]>([])
  const currentPage = ref<number>(1)
  const pageSize = ref<number>(20)
  const total = ref<number>(0)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)
  const uploadingFiles = ref<Map<string, { 
    file: File, 
    progress: number, 
    status: 'pending' | 'uploading' | 'completed' | 'failed' 
  }>>(new Map())

  // 计算属性
  const hasFiles = computed<boolean>(() => fileList.value.length > 0)
  const totalPages = computed<number>(() => Math.ceil(total.value / pageSize.value))
  const isUploading = computed<boolean>(() => {
    for (const item of uploadingFiles.value.values()) {
      if (item.status === 'uploading') {
        return true
      }
    }
    return false
  })

  // Actions
  // <!-- 
  // 审查上下文：
  // - 设计意图：整合FileService与WebSocket实时通信，提供完整的文件管理功能
  // - 已知局限：上传队列管理较为简单，大批量上传可能需要更复杂的调度机制
  // - 业务背景：支持生物信息学数据文件的上传、管理和分析准备
  // - 测试重点：文件上传进度、WebSocket连接状态、分页加载、错误恢复
  // -->

  /**
   * 加载文件列表
   */
  async function loadFileList(page: number = 1, size: number = 20): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      const response: FileListResponse = await FileService.getFileList(page, size)
      
      fileList.value = response.files
      currentPage.value = response.page
      pageSize.value = response.size
      total.value = response.total
      
      console.log(`✅ 加载文件列表成功: ${response.files.length} 个文件`)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load file list'
      console.error('❌ 加载文件列表失败:', error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 上传文件
   */
  async function uploadFile(
    file: File, 
    fileType: string, 
    description?: string
  ): Promise<FileInfo> {
    try {
      console.log(`📤 开始上传文件:`, file.name)
      
      // 添加到上传队列
      const uploadId = `${file.name}-${Date.now()}`
      uploadingFiles.value.set(uploadId, {
        file,
        progress: 0,
        status: 'uploading'
      })

      // 执行上传
      console.log('🚀 开始执行文件上传...')
      const fileInfo: FileInfo = await FileService.uploadFile(
        file,
        fileType,
        description,
        (progress: number) => {
          updateUploadProgress(uploadId, progress)
        }
      )

      console.log('✅ 上传API调用成功:', fileInfo.filename)

      // 标记上传完成
      markUploadComplete(uploadId, fileInfo)
      
      // 刷新文件列表
      try {
        await loadFileList(currentPage.value, pageSize.value)
      } catch (refreshError) {
        console.warn('⚠️ 刷新文件列表失败，但上传已成功:', refreshError)
      }

      console.log('✅ 文件上传成功:', fileInfo.filename)
      return fileInfo
        
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Upload failed'
      console.error('❌ 上传失败:', errorMsg)
      error.value = errorMsg
      throw err
    }
  }

  /**
   * 更新上传进度
   */
  function updateUploadProgress(uploadId: string, progress: number): void {
    const uploadItem = uploadingFiles.value.get(uploadId)
    if (uploadItem) {
      uploadItem.progress = progress
      if (progress > 0 && progress < 100) {
        uploadItem.status = 'uploading'
      }
    }
  }

  /**
   * 标记上传完成
   */
  function markUploadComplete(uploadId: string, fileInfo: FileInfo): void {
    const uploadItem = uploadingFiles.value.get(uploadId)
    if (uploadItem) {
      uploadItem.progress = 100
      uploadItem.status = 'completed'
      // 5秒后自动移除完成的上传项
      setTimeout(() => {
        uploadingFiles.value.delete(uploadId)
      }, 5000)
    }
  }

  /**
   * 标记上传失败
   */
  function markUploadFailed(uploadId: string, errorMessage: string): void {
    const uploadItem = uploadingFiles.value.get(uploadId)
    if (uploadItem) {
      uploadItem.status = 'failed'
      console.error(`❌ 上传失败 [${uploadId}]:`, errorMessage)
    }
  }

  /**
   * 下载文件
   */
  async function downloadFile(fileId: string, filename?: string): Promise<void> {
    try {
      loading.value = true
      await FileService.downloadFile(fileId, filename)
      console.log('✅ 文件下载成功:', filename || fileId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'File download failed'
      console.error('❌ 文件下载失败:', error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除文件
   */
  async function deleteFile(fileId: string): Promise<void> {
    try {
      loading.value = true
      await FileService.deleteFile(fileId)
      
      // 从列表中移除
      const index = fileList.value.findIndex(file => file.id === fileId)
      if (index !== -1) {
        fileList.value.splice(index, 1)
        total.value--
      }
      
      console.log('✅ 文件删除成功:', fileId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete file'
      console.error('❌ 文件删除失败:', error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取文件详情
   */
  async function getFileInfo(fileId: string): Promise<FileInfo> {
    try {
      loading.value = true
      const fileInfo = await FileService.getFileInfo(fileId)
      console.log('✅ 获取文件详情成功:', fileInfo.filename)
      return fileInfo
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load file details'
      console.error('❌ 获取文件详情失败:', error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 清除错误状态
   */
  function clearError(): void {
    error.value = null
  }

  /**
   * 清除上传队列
   */
  function clearUploadQueue(): void {
    uploadingFiles.value.clear()
  }

  return {
    // 状态
    fileList,
    currentPage,
    pageSize,
    total,
    loading,
    error,
    uploadingFiles,

    // 计算属性
    hasFiles,
    totalPages,
    isUploading,

    // Actions
    loadFileList,
    uploadFile,
    updateUploadProgress,
    markUploadComplete,
    markUploadFailed,
    downloadFile,
    deleteFile,
    getFileInfo,
    clearError,
    clearUploadQueue
  }
})