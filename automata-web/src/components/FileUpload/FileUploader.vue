<template>
  <div class="file-uploader">
    <div class="upload-area" @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop">
      <div class="upload-content" :class="{ 'drag-over': isDragging }">
        <iconify-icon 
          class="upload-icon fs-1 text-primary mb-3" 
          icon="mdi:cloud-upload-outline"
        ></iconify-icon>
        <p class="upload-text mb-2">拖拽文件到此处或点击选择文件</p>
        <p class="upload-hint text-muted small">
          支持 {{ allowedTypes.join(', ') }} 格式，最大 {{ formatFileSize(maxSize) }}
        </p>
        <input
          ref="fileInput"
          type="file"
          :accept="allowedTypes.map(type => `.${type}`).join(',')"
          :multiple="multiple"
          class="d-none"
          @change="handleFileSelect"
        >
        <button 
          type="button" 
          class="btn btn-primary mt-3"
          @click="triggerFileSelect"
        >
          选择文件
        </button>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress mt-3">
      <div class="progress-header d-flex justify-content-between align-items-center mb-2">
        <span>上传进度: {{ uploadProgress }}%</span>
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

    <!-- 已选择文件列表 -->
    <div v-if="selectedFiles.length > 0" class="selected-files mt-3">
      <h6 class="mb-2">已选择文件：</h6>
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
            上传中...
          </span>
        </div>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div v-if="selectedFiles.length > 0 && !autoUpload" class="upload-controls mt-3">
      <button 
        type="button" 
        class="btn btn-success"
        :disabled="!canUpload"
        @click="uploadFiles"
      >
        <iconify-icon 
          v-if="isUploading" 
          icon="mdi:loading" 
          class="spin me-1"
        ></iconify-icon>
        {{ isUploading ? '上传中...' : '开始上传' }}
      </button>
      <button 
        v-if="!isUploading"
        type="button" 
        class="btn btn-secondary ms-2"
        @click="selectedFiles = []"
      >
        清空
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
    errorMessage.value = '只能选择一个文件'
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
    errorMessage.value = `发现无效文件：${invalidFiles.map(f => f.name).join(', ')}`
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
    ElMessage.success(`${selectedFiles.value.length} 个文件上传成功`)
    
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
    errorMessage.value = `上传失败: ${error.message || '未知错误'}`
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
      reject(new Error('网络错误'))
    })

    xhr.addEventListener('abort', () => {
      reject(new Error('上传被取消'))
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
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: #fafafa;
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