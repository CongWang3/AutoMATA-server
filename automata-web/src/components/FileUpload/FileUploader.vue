<template>
  <div class="file-uploader">
    <!-- 使用浏览器原生样式，保持与 ModelTrain 页面一致 -->
    <input
      ref="fileInput"
      type="file"
      :accept="allowedTypes.map(type => `.${type}`).join(',')"
      :multiple="multiple"
      class="form-control"
      @change="handleFileSelect"
    >

    <!-- 提示信息（不影响“原生文件输入”外观） -->
    <div class="upload-hint text-muted small mt-2">
      Supported {{ allowedTypes.join(', ') }} formats, maximum {{ formatFileSize(maxSize) }}
    </div>

    <!-- 仅当 autoUpload=true 时才展示“内部上传进度/列表”，避免干扰训练页/ModelUse 的选择交互 -->
    <div v-if="autoUpload && uploadProgress > 0 && uploadProgress < 100" class="upload-progress mt-3">
      <div class="progress-header d-flex justify-content-between align-items-center mb-2">
        <span>Upload progress: {{ uploadProgress }}%</span>
        <span v-if="uploadSpeed > 0" class="speed-indicator">
          {{ formatSpeed(uploadSpeed) }}
        </span>
      </div>
      <div class="progress">
        <div
          class="progress-bar"
          role="progressbar"
          :style="{ width: uploadProgress + '%' }"
        >
          {{ uploadProgress }}%
        </div>
      </div>
    </div>

    <div v-if="autoUpload && selectedFiles.length > 0" class="selected-files mt-3">
      <h6 class="mb-2">Selected files:</h6>
      <div
        v-for="(file, index) in selectedFiles"
        :key="index"
        class="file-item d-flex align-items-center justify-content-between p-2 mb-2 border rounded"
      >
        <div class="file-info d-flex align-items-center">
          <iconify-icon
            class="file-icon me-2"
            :icon="getFileIcon(file.type)"
          ></iconify-icon>
          <div>
            <div class="file-name">{{ file.name }}</div>
            <small class="text-muted">{{ formatFileSize(file.size) }}</small>
          </div>
        </div>
        <div class="file-actions d-flex gap-2">
          <button
            v-if="!isUploading"
            type="button"
            class="btn btn-sm btn-outline-danger"
            @click="removeFile(index)"
          >
            <iconify-icon icon="mdi:close"></iconify-icon>
          </button>
          <span v-if="isUploading" class="text-primary">
            <iconify-icon icon="mdi:loading" class="spin"></iconify-icon>
            Uploading…
          </span>
        </div>
      </div>
    </div>

    <div v-if="autoUpload && selectedFiles.length > 0 && !isUploading" class="upload-controls mt-3">
      <button
        type="button"
        class="btn btn-success"
        :disabled="!canUpload"
        @click="uploadFiles"
      >
        Start upload
      </button>
      <button
        type="button"
        class="btn btn-secondary ms-2"
        @click="selectedFiles = []"
      >
        Clear
      </button>
    </div>

    <!-- 错误信息 -->
    <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElLoading } from 'element-plus'

interface Props {
  allowedTypes?: string[]
  maxSize?: number // bytes
  multiple?: boolean
  autoUpload?: boolean
  fileType?: string // 文件类型标识，用于后端识别
  description?: string // 文件描述
}

const props = withDefaults(defineProps<Props>(), {
  allowedTypes: () => ['txt', 'csv', 'xlsx', 'xls'],
  maxSize: 500 * 1024 * 1024, // 500MB
  multiple: false,
  autoUpload: false,
  fileType: 'dataset',
  description: ''
})

const emit = defineEmits<{
  (e: 'file-selected', files: File[]): void
  (e: 'upload-start', files: File[]): void
  (e: 'upload-progress', progress: number): void
  (e: 'upload-complete', response: any): void
  (e: 'upload-error', error: Error): void
}>()

// 响应式数据
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFiles = ref<File[]>([])
const isDragging = ref(false)
const uploadProgress = ref(0)
const errorMessage = ref('')
const isUploading = ref(false)
const uploadSpeed = ref(0) // 上传速度 (bytes/sec)
const startTime = ref<number | null>(null)

// 计算属性
const totalSize = computed(() => {
  return selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
})

const canUpload = computed(() => {
  return selectedFiles.value.length > 0 && !isUploading.value
})

// 方法
const triggerFileSelect = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    processFiles(Array.from(input.files))
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
  
  if (event.dataTransfer?.files) {
    processFiles(Array.from(event.dataTransfer.files))
  }
}

const processFiles = (files: File[]) => {
  errorMessage.value = ''
  
  // 验证文件数量
  if (!props.multiple && files.length > 1) {
    errorMessage.value = 'Only one file can be selected'
    return
  }

  // 验证文件类型和大小
  const invalidFiles = files.filter(file => {
    const extension = file.name.split('.').pop()?.toLowerCase()
    const isValidType = props.allowedTypes.includes(extension || '')
    const isValidSize = file.size <= props.maxSize
    
    return !isValidType || !isValidSize
  })

  if (invalidFiles.length > 0) {
    errorMessage.value = `Invalid file(s): ${invalidFiles.map(f => f.name).join(', ')}`
    return
  }

  // 添加文件
  if (props.multiple) {
    selectedFiles.value.push(...files)
  } else {
    selectedFiles.value = files
  }

  // 触发事件
  emit('file-selected', selectedFiles.value)

  // 自动上传
  if (props.autoUpload) {
    uploadFiles()
  }
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0 || isUploading.value) return

  isUploading.value = true
  uploadProgress.value = 0
  startTime.value = Date.now()
  errorMessage.value = ''

  try {
    emit('upload-start', selectedFiles.value)
    
    // 逐个上传文件
    const results = []
    for (let i = 0; i < selectedFiles.value.length; i++) {
      const file = selectedFiles.value[i]
      if (!file) continue  // 类型守卫，确保 file 存在
      const result = await uploadSingleFile(file, i)
      results.push(result)
      
      // 更新整体进度
      uploadProgress.value = Math.round(((i + 1) / selectedFiles.value.length) * 100)
      emit('upload-progress', uploadProgress.value)
    }

    emit('upload-complete', { success: true, files: results })
    ElMessage.success(`${selectedFiles.value.length} file(s) uploaded successfully`)
    
    // 重置状态
    setTimeout(() => {
      uploadProgress.value = 0
      selectedFiles.value = []
      isUploading.value = false
      uploadSpeed.value = 0
    }, 1000)

  } catch (error: any) {
    isUploading.value = false
    uploadProgress.value = 0
    uploadSpeed.value = 0
    errorMessage.value = `Upload failed: ${error.message || 'Unknown error'}`
    emit('upload-error', error)
    ElMessage.error(errorMessage.value)
  }
}

const uploadSingleFile = (file: File, index: number): Promise<any> => {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', props.fileType)
    if (props.description) {
      formData.append('description', props.description)
    }

    let lastUploaded = 0
    const startTime = Date.now()

    const xhr = new XMLHttpRequest()

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const currentTime = Date.now()
        const elapsedTime = (currentTime - startTime) / 1000 // 秒
        const uploaded = event.loaded
        const total = event.total
        
        // 计算上传速度
        const bytesUploaded = uploaded - lastUploaded
        const timeElapsed = (currentTime - startTime) / 1000
        if (timeElapsed > 0) {
          uploadSpeed.value = bytesUploaded / (currentTime - startTime) * 1000
        }
        lastUploaded = uploaded

        // 计算当前文件的进度（占总进度的一部分）
        const fileProgress = (uploaded / total) * 100
        const overallProgress = ((index + fileProgress / 100) / selectedFiles.value.length) * 100
        uploadProgress.value = Math.round(overallProgress)
        emit('upload-progress', uploadProgress.value)
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        try {
          const response = JSON.parse(xhr.responseText)
          resolve(response)
        } catch (e) {
          resolve(xhr.responseText)
        }
      } else {
        reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`))
      }
    })

    xhr.addEventListener('error', () => {
      reject(new Error('Network error'))
    })

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload cancelled'))
    })

    // 发送请求
    xhr.open('POST', '/api/v1/files/upload')
    xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('access_token')}`)
    xhr.send(formData)
  })
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatSpeed = (bytesPerSec: number): string => {
  return formatFileSize(bytesPerSec) + '/s'
}

const getFileIcon = (fileType: string): string => {
  if (fileType.includes('text')) return 'mdi:file-document-outline'
  if (fileType.includes('spreadsheet')) return 'mdi:file-excel-outline'
  return 'mdi:file-outline'
}

// 暴露方法给父组件
defineExpose({
  upload: uploadFiles,
  clear: () => { selectedFiles.value = [] },
  getSelectedFiles: () => selectedFiles.value
})
</script>

<style scoped>
.file-uploader {
  /* 只保留虚线上传框的边框，避免外层边框在顶部/底部生成“莫名横线” */
  padding: 0;
  border: none;
  border-radius: 0;
  background-color: transparent;
}

.upload-area {
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-area:hover,
.drag-over {
  border-color: #0d6efd;
  background-color: rgba(13, 110, 253, 0.05);
}

.upload-content {
  padding: 2rem;
  text-align: center;
}

.upload-icon {
  transition: color 0.3s ease;
}

.drag-over .upload-icon {
  color: #0d6efd;
}

.file-item {
  background-color: #ffffff;
  transition: all 0.2s ease;
}

.file-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.file-icon {
  font-size: 1.5rem;
  color: #6c757d;
}

.progress {
  height: 20px;
  margin-bottom: 10px;
}

.progress-bar {
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.875rem;
}

.progress-header {
  font-weight: 500;
  color: #495057;
}

.speed-indicator {
  font-size: 0.875rem;
  color: #6c757d;
  background-color: #e9ecef;
  padding: 2px 8px;
  border-radius: 12px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.upload-controls {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.file-actions {
  align-items: center;
}

.alert {
  border-radius: 6px;
  margin-top: 15px;
}
</style>