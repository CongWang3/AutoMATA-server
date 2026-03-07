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
        <button 
          type="button" 
          class="btn btn-sm btn-outline-danger"
          @click="removeFile(index)"
        >
          <iconify-icon icon="mdi:close"></iconify-icon>
        </button>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  allowedTypes?: string[]
  maxSize?: number // bytes
  multiple?: boolean
  autoUpload?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  allowedTypes: () => ['txt', 'csv', 'xlsx', 'xls'],
  maxSize: 50 * 1024 * 1024, // 50MB
  multiple: false,
  autoUpload: false
})

const emit = defineEmits<{
  (e: 'file-selected', files: File[]): void
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

// 计算属性
const totalSize = computed(() => {
  return selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
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
  if (selectedFiles.value.length === 0) return

  try {
    uploadProgress.value = 0
    const formData = new FormData()
    
    selectedFiles.value.forEach((file, index) => {
      formData.append(`file${index}`, file)
    })

    // 模拟上传进度
    const interval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
        emit('upload-progress', uploadProgress.value)
      }
    }, 200)

    // 这里应该调用实际的上传API
    setTimeout(() => {
      clearInterval(interval)
      uploadProgress.value = 100
      emit('upload-progress', 100)
      emit('upload-complete', { success: true, files: selectedFiles.value })
      
      // 重置状态
      setTimeout(() => {
        uploadProgress.value = 0
        selectedFiles.value = []
      }, 1000)
    }, 2000)

  } catch (error) {
    uploadProgress.value = 0
    errorMessage.value = '上传失败'
    emit('upload-error', error as Error)
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileIcon = (fileType: string): string => {
  if (fileType.includes('text')) return 'mdi:file-document-outline'
  if (fileType.includes('spreadsheet')) return 'mdi:file-excel-outline'
  return 'mdi:file-outline'
}

// 暴露方法给父组件
defineExpose({
  upload: uploadFiles,
  clear: () => { selectedFiles.value = [] }
})
</script>

<style scoped>
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
  background-color: #f8f9fa;
}

.file-icon {
  font-size: 1.5rem;
  color: #6c757d;
}

.progress {
  height: 8px;
}

.progress-bar {
  transition: width 0.3s ease;
}
</style>