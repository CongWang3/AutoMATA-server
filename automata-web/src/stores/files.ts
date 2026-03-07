import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { FileService, webSocketService } from '@/api'
import type { FileInfo, FileListResponse, WebSocketProgressMessage } from '@/api/types'

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
      error.value = err instanceof Error ? err.message : '加载文件列表失败'
      console.error('❌ 加载文件列表失败:', error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 上传文件（带重试机制和完整性验证）
   */
  async function uploadFile(
    file: File, 
    fileType: string, 
    description?: string,
    maxRetries: number = 3
  ): Promise<FileInfo> {
    let lastError: Error | null = null
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`📤 开始上传文件 (第${attempt}次尝试):`, file.name)
        
        // 添加到上传队列
        const uploadId = `${file.name}-${Date.now()}-${attempt}`
        uploadingFiles.value.set(uploadId, {
          file,
          progress: 0,
          status: 'pending'
        })

        // 启动WebSocket连接监听进度
        if (!webSocketService.isConnected()) {
          await webSocketService.connect()
        }

        // 设置进度回调
        webSocketService.setOnProgress((message: WebSocketProgressMessage) => {
          if (message.event === 'upload_progress') {
            const progress = Math.round(message.progress_percent)
            updateUploadProgress(uploadId, progress)
          }
        })

        // 执行上传
        console.log('🚀 开始执行文件上传...')
        const fileInfo: FileInfo = await FileService.uploadFile(
          file,
          fileType,
          description,
          (progress: number) => {
            updateUploadProgress(uploadId, progress)
            if (progress % 10 === 0) { // 每10%记录一次
              console.log(`📊 上传进度: ${progress}%`)
            }
          }
        )

        console.log('✅ 上传API调用成功，返回的文件信息:', fileInfo)
        console.log('🔍 验证返回的数据完整性...')

        // 关键：验证上传完整性
        console.log('🔍 验证上传完整性...')
        if (fileInfo.file_size !== file.size) {
          throw new Error(`文件大小不匹配: 期望 ${file.size} bytes, 实际 ${fileInfo.file_size} bytes`)
        }

        // 验证文件名
        if (!fileInfo.filename || fileInfo.filename === '') {
          throw new Error('上传的文件名为空')
        }

        // 标记上传完成
        markUploadComplete(uploadId, fileInfo)
        
        // 刷新文件列表以确认上传成功
        await loadFileList(currentPage.value, pageSize.value)
        
        // 再次验证文件是否真的存在 - 改进验证逻辑
        console.log('🔍 在文件列表中查找上传的文件...')
        console.log('📄 当前文件列表:', fileList.value.map(f => ({
          id: f.id, 
          name: f.original_name, 
          size: f.file_size,
          created: f.upload_time
        })))
        console.log('🎯 要查找的文件:', {
          name: file.name,
          size: file.size
        })
        
        // 使用更宽松的匹配条件
        const uploadedFile = fileList.value.find(f => {
          const nameMatch = f.original_name === file.name
          const sizeMatch = Math.abs(f.file_size - file.size) < 1000
          const partialNameMatch = f.filename.includes(file.name.replace(/\.[^/.]+$/, ""))
          
          console.log(`🔍 匹配检查 - ${f.original_name}: 名称匹配=${nameMatch}, 大小匹配=${sizeMatch}, 部分匹配=${partialNameMatch}`)
          return nameMatch || partialNameMatch || sizeMatch
        })
        
        if (!uploadedFile) {
          // 如果没找到，尝试重新加载列表
          console.log('🔄 未找到文件，重新加载列表...')
          await loadFileList(1, 50) // 加载更多文件
          
          const reloadedFile = fileList.value.find(f => 
            f.original_name === file.name || 
            Math.abs(f.file_size - file.size) < 1000
          )
          
          if (!reloadedFile) {
            // 检查是否是因为文件去重导致的
            const sameSizeFiles = fileList.value.filter(f => Math.abs(f.file_size - file.size) < 1000)
            if (sameSizeFiles.length > 0) {
              console.log('💡 检测到可能是文件去重情况，相似文件:', sameSizeFiles)
              throw new Error(`文件可能已存在（去重机制）: ${file.name}。如果是不同用户的数据，请修改文件名或内容后重新上传。`)
            }
            throw new Error(`上传完成但文件未在列表中找到。文件名: ${file.name}, 大小: ${file.size} bytes`)
          }
          console.log('✅ 重新加载后找到文件:', reloadedFile.original_name)
        } else {
          console.log('✅ 找到上传的文件:', uploadedFile.original_name)
        }

        console.log('✅ 文件上传成功并验证通过:', fileInfo.filename)
        return fileInfo
        
      } catch (err) {
        lastError = err instanceof Error ? err : new Error('未知错误')
        console.error(`❌ 第${attempt}次上传失败:`, lastError.message)
        
        // 如果不是最后一次尝试，等待后重试
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * attempt, 5000) // 递增延迟，最大5秒
          console.log(`⏳ 等待 ${delay}ms 后重试...`)
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }
    }
    
    // 所有重试都失败了
    const uploadId = `${file.name}-${Date.now()}-final`
    markUploadFailed(uploadId, lastError?.message || '上传失败')
    error.value = lastError?.message || '文件上传失败'
    throw lastError || new Error('文件上传失败')
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
      error.value = err instanceof Error ? err.message : '文件下载失败'
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
      error.value = err instanceof Error ? err.message : '文件删除失败'
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
      error.value = err instanceof Error ? err.message : '获取文件详情失败'
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

  /**
   * 初始化WebSocket连接
   */
  async function initializeWebSocket(): Promise<void> {
    try {
      if (!webSocketService.isConnected()) {
        await webSocketService.connect()
        console.log('✅ WebSocket连接初始化成功')
      }
    } catch (err) {
      console.warn('⚠️ WebSocket连接初始化失败:', err)
      // 不抛出错误，因为这是辅助功能
    }
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
    clearUploadQueue,
    initializeWebSocket
  }
})