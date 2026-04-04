<template>
  <div class="data-process-form">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{ title }}</span>
          <el-tag :type="tagType">{{ subtitle }}</el-tag>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="200px"
        class="process-form"
      >
        <!-- 文件上传 -->
        <el-form-item :label="fileLabel" prop="file">
          <div class="file-upload-container">
            <el-upload
              ref="uploadRef"
              class="upload-demo"
              drag
              :auto-upload="false"
              :show-file-list="true"
              :limit="1"
              :on-change="handleFileChange"
              :on-exceed="handleExceed"
              :accept="acceptTypes"
              :before-upload="beforeUpload"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                Drag and drop the file here, or <em>click to upload</em>
              </div>
              <template #tip>
                <div class="upload-tip-container">
                  <div class="tip-content">
                    <span class="file-types">{{ fileTip }}</span>
                    <el-button 
                      v-if="exampleDataUrl" 
                      type="primary" 
                      size="small" 
                      @click="downloadExampleData"
                      class="example-btn"
                    >
                      Download Example Data
                    </el-button>
                  </div>
                  <div class="tip-notes">
                    <el-text v-if="exampleNote" type="warning" size="small" class="example-note">
                      {{ exampleNote }}
                    </el-text>
                  </div>
                </div>
              </template>
            </el-upload>
          </div>
        </el-form-item>
        
        <!-- 命名方式选择 -->
        <el-form-item :label="nomenclatureLabel" prop="nomenclature">
          <el-select 
            v-model="formData.nomenclature" 
            :placeholder="nomenclaturePlaceholder"
            style="width: 100%"
          >
            <el-option 
              v-for="option in nomenclatureOptions" 
              :key="option.value"
              :label="option.label" 
              :value="option.value" 
            />
          </el-select>
        </el-form-item>
        
        <!-- 数据类型选择（部分功能如蛋白质处理无需此项，可通过 props 控制显示） -->
        <el-form-item v-if="props.showDataType" label="Data Type" prop="dataType">
          <el-select 
            v-model="formData.dataType" 
            placeholder="Select data type"
            style="width: 100%"
          >
            <el-option label="FPKM" value="FPKM" />
            <el-option label="RPM" value="RPM" />
            <el-option label="RPKM" value="RPKM" />
            <el-option label="Read Counts" value="ReadCounts" />
            <el-option label="TPM" value="TPM" />
          </el-select>
        </el-form-item>
        
        <!-- 物种选择 -->
        <el-form-item label="Organism" prop="organism">
          <el-select 
            v-model="formData.organism" 
            placeholder="Select organism"
            style="width: 100%"
          >
            <el-option 
              v-for="species in speciesOptions" 
              :key="species.value"
              :label="species.label" 
              :value="species.value" 
            />
          </el-select>
        </el-form-item>
        
        <!-- 邮箱 -->
        <el-form-item label="Email" prop="email">
          <el-input 
            v-model="formData.email" 
            placeholder="Enter your email address (optional)"
            type="email"
          />
        </el-form-item>
        
        <!-- 提交按钮 -->
        <el-form-item>
          <el-button 
            type="primary" 
            @click="submitForm"
            :loading="submitting"
            size="large"
            class="submit-btn"
          >
            {{ submitting ? 'Processing...' : 'Submit' }}
          </el-button>
          <el-button @click="resetForm">Reset</el-button>
        </el-form-item>
        
        <!-- 进度显示 -->
        <el-form-item v-if="submitting && progressPercentage > 0">
          <div class="progress-container">
            <el-progress 
              :percentage="progressPercentage" 
              :stroke-width="12"
              striped
              striped-flow
            />
            <p class="progress-message" v-if="progressMessage">{{ progressMessage }}</p>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import type { FormData, NomenclatureOption, SpeciesOption } from '@/types/dataProcess'
import { webSocketService } from '@/api/websocket'
import type { WebSocketProgressMessage } from '@/api/types'
import { resolvePublicStaticUrl } from '@/config/deploy'

// <!-- 
// 审查上下文：
// - 设计意图：提取数据处理表单的公共逻辑，遵循 DRY 原则，减少重复代码
// - 已知局限：为了保持灵活性，某些配置项仍需要通过 props 传递
// - 业务背景：基因组和转录组表单具有高度相似性，适合组件化抽象
// - 测试重点：请验证表单验证、文件上传、参数传递等功能的正确性
// -->

interface Props {
  title: string
  subtitle: string
  tagType?: 'success' | 'info' | 'warning' | 'danger'
  fileLabel: string
  fileTip: string
  acceptTypes?: string
  nomenclatureLabel: string
  nomenclaturePlaceholder: string
  nomenclatureOptions: NomenclatureOption[]
  speciesOptions: SpeciesOption[]
  exampleDataUrl?: string
  exampleFileName?: string
  exampleNote?: string  // 示例数据说明
  /** 是否显示“数据类型”字段（蛋白质处理不需要），默认 true */
  showDataType?: boolean
  onSubmit: (formData: FormData) => Promise<any>
}

const props = withDefaults(defineProps<Props>(), {
  tagType: 'success',
  // acceptTypes: '.txt,.csv,.tsv',
  acceptTypes: '.txt',
  showDataType: true
})

const emit = defineEmits<{
  (e: 'submit-success', result: any): void
}>()

const formRef = ref<FormInstance>()
const uploadRef = ref()

const submitting = ref(false)
const progressPercentage = ref(0)
const progressMessage = ref('')

const formData = reactive<FormData>({
  file: null,
  nomenclature: '',
  dataType: '',
  organism: '',
  email: ''
})

const formRules = computed<FormRules>(() => {
  const rules: FormRules = {
    file: [{ required: true, message: 'Upload file', trigger: 'change' }],
    nomenclature: [
      { required: true, message: props.nomenclaturePlaceholder, trigger: 'change' }
    ],
    organism: [{ required: true, message: 'Select organism', trigger: 'change' }],
    email: [{ type: 'email', message: 'Enter a valid email address', trigger: 'blur' }]
  }

  // 仅在需要时添加“数据类型”校验规则（蛋白质处理不需要）
  if (props.showDataType) {
    rules.dataType = [{ required: true, message: 'Select data type', trigger: 'change' }]
  }

  return rules
})

const handleFileChange = (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    formData.file = uploadFile.raw
  }
}

const handleExceed = () => {
  ElMessage.warning('Only one file can be uploaded')
}

const beforeUpload = (file: File): boolean => {
  // <!-- 
  // 审查上下文：
  // - 设计意图：实现与PHP版本一致的文件格式验证
  // - 已知局限：前端验证作为第一道防线，后端仍有完整验证
  // - 业务背景：确保只接受指定格式的文本文件
  // - 测试重点：请验证各种文件格式的拒绝和接受逻辑
  // -->
  
  // const allowedTypes = ['text/plain', 'text/csv', 'application/csv']
  // const allowedExtensions = ['.txt', '.csv', '.tsv']
  const allowedTypes = ['text/plain']
  const allowedExtensions = ['.txt']
  
  // 检查MIME类型
  const isValidType = allowedTypes.includes(file.type)
  
  // 检查文件扩展名
  const fileName = file.name.toLowerCase()
  const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext))
  
  if (!isValidType && !hasValidExtension) {
    ElMessage.error('Only support txt files with tab delimiter.')
    return false
  }
  
  // 检查文件大小（限制为10MB）
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('File size cannot exceed 50MB')
    return false
  }
  
  return true
}

/** public 下示例文件请求 URL：生产可用 VITE_PUBLIC_SITE_ORIGIN，开发默认当前页 origin */
const resolveExampleFetchUrl = (): string => resolvePublicStaticUrl(props.exampleDataUrl || '')

const downloadExampleData = async () => {
  if (!props.exampleDataUrl) {
    ElMessage.warning('No example data available')
    return
  }

  const fileName = props.exampleFileName || 'example_data.txt'
  const fetchUrl = resolveExampleFetchUrl()

  try {
    const res = await fetch(fetchUrl)
    if (!res.ok) {
      throw new Error(`${res.status} ${res.statusText}`)
    }
    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = fileName
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(objectUrl)
    ElMessage.success(`Example data downloaded: ${fileName}`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    console.error('Example download failed:', fetchUrl, e)
    ElMessage.error(`Failed to download example (${msg}). Open in browser: ${fetchUrl}`)
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (!formData.file) {
      ElMessage.error('Please upload the file first')
      return
    }
    
    submitting.value = true
    progressPercentage.value = 0
    progressMessage.value = ''
    
    // 连接WebSocket以接收进度更新
    await connectProgressWebSocket()
    
    const result = await props.onSubmit(formData)
    
    emit('submit-success', result)
    
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || 'Submission failed. Please try again')
  } finally {
    submitting.value = false
    disconnectProgressWebSocket()
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  formData.file = null
  uploadRef.value?.clearFiles()
}

// 连接进度WebSocket
const connectProgressWebSocket = async () => {
  try {
    await webSocketService.connect()
    webSocketService.setOnProgress(handleProgressMessage)
  } catch (error) {
    console.error('WebSocket连接失败:', error)
  }
}

// 断开进度WebSocket
const disconnectProgressWebSocket = () => {
  webSocketService.disconnect()
  progressPercentage.value = 0
  progressMessage.value = ''
}

// 处理进度消息
const handleProgressMessage = (message: WebSocketProgressMessage) => {
  progressPercentage.value = message.progress_percent || 0
  progressMessage.value = message.message || 'Processing...'
  
  // 如果进度达到100%，可以做一些清理工作
  if (progressPercentage.value >= 100) {
    setTimeout(() => {
      progressPercentage.value = 0
      progressMessage.value = ''
    }, 2000)
  }
}

// 组件卸载时断开WebSocket连接
onUnmounted(() => {
  disconnectProgressWebSocket()
})

// 暴露方法给父组件使用
defineExpose({
  resetForm,
  connectProgressWebSocket,
  disconnectProgressWebSocket
})
</script>

<style scoped>
.data-process-form {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.process-form {
  padding: 20px 0;
}

.file-upload-container {
  width: 100%;
}

.upload-demo :deep(.el-upload) {
  width: 100%;
}

.upload-demo :deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
}

.submit-btn {
  width: 120px;
}

.example-btn {
  margin-left: 12px;
}

/* 上传提示区域优化 */
.upload-tip-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tip-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.file-types {
  color: #909399;
  font-size: 12px;
  flex-shrink: 0;
}

.tip-notes {
  width: 100%;
}

.example-note {
  line-height: 1.5;
  display: block;
}

.progress-container {
  width: 100%;
}

.progress-message {
  margin-top: 10px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.result-content {
  text-align: center;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

@media (max-width: 768px) {
  .data-process-form {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  /* 移动端上传提示优化 */
  .tip-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .file-types {
    order: 1;
  }
  
  .example-btn {
    order: 2;
    margin-left: 0;
    width: 100%;
    max-width: 200px;
  }
  
  .tip-notes {
    order: 3;
  }
}
</style>
