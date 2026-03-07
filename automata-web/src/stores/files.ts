import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface UploadFile {
  id: string
  name: string
  size: number
  type: string
  upload_progress: number
  status: 'pending' | 'uploading' | 'completed' | 'failed'
  file?: File
}

export const useFilesStore = defineStore('files', () => {
  // 状态
  const files = ref<UploadFile[]>([])
  const isUploading = ref<boolean>(false)
  const uploadError = ref<string | null>(null)
  
  // Actions
  function addFile(file: File) {
    const uploadFile: UploadFile = {
      id: generateId(),
      name: file.name,
      size: file.size,
      type: file.type,
      upload_progress: 0,
      status: 'pending',
      file
    }
    files.value.push(uploadFile)
    return uploadFile
  }
  
  function updateFileProgress(fileId: string, progress: number) {
    const file = files.value.find(f => f.id === fileId)
    if (file) {
      file.upload_progress = progress
      if (progress === 100) {
        file.status = 'completed'
      } else if (progress > 0) {
        file.status = 'uploading'
      }
    }
  }
  
  function setFileStatus(fileId: string, status: UploadFile['status']) {
    const file = files.value.find(f => f.id === fileId)
    if (file) {
      file.status = status
    }
  }
  
  function removeFile(fileId: string) {
    const index = files.value.findIndex(f => f.id === fileId)
    if (index !== -1) {
      files.value.splice(index, 1)
    }
  }
  
  function clearCompletedFiles() {
    files.value = files.value.filter(f => f.status !== 'completed')
  }
  
  function clearAllFiles() {
    files.value = []
  }
  
  function setUploading(status: boolean) {
    isUploading.value = status
  }
  
  function setUploadError(error: string | null) {
    uploadError.value = error
  }
  
  function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }
  
  return {
    // 状态
    files,
    isUploading,
    uploadError,
    
    // Actions
    addFile,
    updateFileProgress,
    setFileStatus,
    removeFile,
    clearCompletedFiles,
    clearAllFiles,
    setUploading,
    setUploadError
  }
})