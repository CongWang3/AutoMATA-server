<template>
  <div class="analysis-form">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{ title }}</span>
          <el-tag type="primary">{{ subtitle }}</el-tag>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="formValues"
        :rules="formRules"
        label-width="200px"
        class="analysis-form-content"
      >
        <!-- 主文件上传 -->
        <el-form-item :label="fileLabel || '1. Upload data set'" prop="file">
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
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="upload-tip-container">
                  <div class="tip-content">
                    <span class="file-types">{{ fileTip || '仅支持 txt、csv、tsv 格式的文件' }}</span>
                    <el-button 
                      v-if="exampleDataUrl" 
                      type="primary" 
                      size="small" 
                      @click="downloadExampleData"
                      class="example-btn"
                    >
                      下载示例数据
                    </el-button>
                  </div>
                  <div v-if="exampleNote" class="tip-notes">
                    <el-text type="warning" size="small" class="example-note">
                      {{ exampleNote }}
                    </el-text>
                  </div>
                </div>
              </template>
            </el-upload>
          </div>
        </el-form-item>

        <!-- 第二个文件上传（可选，用于综合分析等） -->
        <el-form-item 
          v-if="multipleFiles" 
          :label="secondFileLabel || '2. Upload second file'" 
          prop="secondFile"
        >
          <div class="file-upload-container">
            <el-upload
              ref="secondUploadRef"
              class="upload-demo"
              drag
              :auto-upload="false"
              :show-file-list="true"
              :limit="1"
              :on-change="handleSecondFileChange"
              :on-exceed="handleExceed"
              :accept="acceptTypes"
              :before-upload="beforeUpload"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="upload-tip-container">
                  <div class="tip-content">
                    <span class="file-types">{{ fileTip || '仅支持 txt、csv、tsv 格式的文件' }}</span>
                    <el-button 
                      v-if="secondExampleUrl" 
                      type="primary" 
                      size="small" 
                      @click="downloadSecondExampleData"
                      class="example-btn"
                    >
                      下载示例数据
                    </el-button>
                  </div>
                </div>
              </template>
            </el-upload>
          </div>
        </el-form-item>

        <!-- 动态字段渲染 -->
        <template v-for="(field, index) in visibleFields" :key="field.name">
          <el-form-item 
            :label="`${getFieldIndex(index)}. ${field.label}`" 
            :prop="field.name"
            :rules="getFieldRules(field)"
          >
            <!-- Input 类型 -->
            <el-input
              v-if="field.type === 'input'"
              v-model="formValues[field.name]"
              :placeholder="field.placeholder"
            />

            <!-- Number 类型 -->
            <el-input-number
              v-else-if="field.type === 'number'"
              v-model="formValues[field.name]"
              :min="field.min"
              :max="field.max"
              :step="field.step || 0.01"
              :placeholder="field.placeholder"
              style="width: 100%"
              controls-position="right"
            />

            <!-- Select 类型 -->
            <el-select
              v-else-if="field.type === 'select'"
              v-model="formValues[field.name]"
              :placeholder="field.placeholder || '请选择'"
              style="width: 100%"
            >
              <el-option
                v-for="opt in field.options"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>

            <!-- Radio 类型 -->
            <el-radio-group
              v-else-if="field.type === 'radio'"
              v-model="formValues[field.name]"
            >
              <el-radio-button
                v-for="opt in field.options"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </el-radio-button>
            </el-radio-group>

            <!-- 字段提示 -->
            <template v-if="field.tip">
              <div class="field-tip">
                <el-text type="info" size="small">{{ field.tip }}</el-text>
              </div>
            </template>
          </el-form-item>
        </template>

        <!-- 邮箱输入 -->
        <el-form-item label="Your Email" prop="email">
          <el-input 
            v-model="formValues.email" 
            placeholder="请输入邮箱地址"
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
            {{ submitting ? '处理中...' : '提交分析' }}
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>

        <!-- 示例图片展示 -->
        <el-form-item v-if="exampleImageUrl">
          <div class="example-image-container">
            <p class="example-label">Example Figure is as follows:</p>
            <img :src="exampleImageUrl" :alt="title" class="example-image" />
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 结果对话框 -->
    <el-dialog
      v-model="showResultDialog"
      width="80%"
      :close-on-click-modal="false"
      @close="handleDialogClose"
    >
      <TaskResultDisplay
        v-if="showResultDialog && currentJobId"
        :job-id="currentJobId"
        :params="jobParams"
        :initial-status="jobStatus"
        :initial-progress="jobProgress"
        :compact="true"
        :hide-data-type="true"
        :hide-organism="true"
        nomenclature-label="Analysis Type"
        @status-change="handleStatusChange"
      />

      <!-- 分析结果展示（图片预览 + 下载） -->
      <div v-if="analysisResults.length > 0" class="analysis-results">
        <el-divider>分析结果</el-divider>
        <div class="result-files">
          <div v-for="file in analysisResults" :key="file.filename" class="result-file-item">
            <!-- 图片预览 -->
            <div v-if="isImageFile(file.filename)" class="image-preview">
              <el-image
                :src="file.url"
                :preview-src-list="[file.url]"
                fit="contain"
                class="result-image"
              />
            </div>
            <!-- 文件下载 -->
            <div class="file-download">
              <span class="file-name">{{ file.filename }}</span>
              <el-button 
                type="primary" 
                size="small"
                @click="downloadFile(file)"
              >
                下载 {{ file.format.toUpperCase() }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 多格式下载按钮组 -->
        <div v-if="hasImageResults" class="download-formats">
          <el-divider content-position="left">下载其他格式</el-divider>
          <el-button-group>
            <el-button 
              v-for="format in downloadFormats" 
              :key="format" 
              size="small"
              @click="downloadInFormat(format)"
            >
              {{ format.toUpperCase() }}
            </el-button>
          </el-button-group>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleDialogClose">关闭并提交新任务</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import TaskResultDisplay from './TaskResultDisplay.vue'
import { webSocketService } from '@/api/websocket'
import type { AnalysisField, AnalysisResultFile } from '@/api/analysis'

// ==================== Props 定义 ====================

interface Props {
  /** 表单标题 */
  title: string
  /** 表单副标题 */
  subtitle: string
  /** 动态表单字段配置 */
  fields: AnalysisField[]
  /** 提交处理函数 */
  onSubmit: (formData: FormData) => Promise<any>
  /** 示例数据下载地址 */
  exampleDataUrl?: string
  /** 示例文件名 */
  exampleFileName?: string
  /** 示例说明 */
  exampleNote?: string
  /** 是否支持多文件上传 */
  multipleFiles?: boolean
  /** 第二个文件上传标签 */
  secondFileLabel?: string
  /** 第二个示例数据URL */
  secondExampleUrl?: string
  /** 第二个示例文件名 */
  secondExampleFileName?: string
  /** 主文件上传标签 */
  fileLabel?: string
  /** 文件类型提示 */
  fileTip?: string
  /** 接受的文件类型 */
  acceptTypes?: string
  /** 示例图片URL */
  exampleImageUrl?: string
}

const props = withDefaults(defineProps<Props>(), {
  multipleFiles: false,
  acceptTypes: '.txt,.csv,.tsv'
})

const emit = defineEmits<{
  (e: 'submit-success', result: any): void
}>()

// ==================== 响应式状态 ====================

const formRef = ref<FormInstance>()
const uploadRef = ref()
const secondUploadRef = ref()

const submitting = ref(false)
const showResultDialog = ref(false)
const currentJobId = ref('')
const jobStatus = ref('WAITING')
const jobProgress = ref(0)
const analysisResults = ref<AnalysisResultFile[]>([])

// 表单值（动态字段 + 固定字段）
const formValues = reactive<Record<string, any>>({
  file: null,
  secondFile: null,
  email: ''
})

// 任务参数（用于结果展示）
const jobParams = reactive({
  gene_nomenclature: '',
  data_type: '',
  organism: ''
})

// 下载格式列表
const downloadFormats = ['pdf', 'png', 'svg', 'tiff', 'jpeg', 'bmp']

// WebSocket 管理
const taskWsService = ref<any>(null)
const wsConnected = ref(false)

// ==================== 计算属性 ====================

// 可见字段（根据 visible 条件过滤）
const visibleFields = computed(() => {
  return props.fields.filter(field => {
    if (field.visible === undefined) return true
    if (typeof field.visible === 'boolean') return field.visible
    if (typeof field.visible === 'function') return field.visible(formValues)
    return true
  })
})

// 是否有图片结果
const hasImageResults = computed(() => {
  return analysisResults.value.some(file => isImageFile(file.filename))
})

// 表单验证规则
const formRules = computed<FormRules>(() => {
  const rules: FormRules = {
    file: [{ required: true, message: '请上传文件', trigger: 'change' }],
    email: [{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }]
  }

  // 双文件模式下验证第二个文件
  if (props.multipleFiles) {
    rules.secondFile = [{ required: true, message: '请上传第二个文件', trigger: 'change' }]
  }

  return rules
})

// ==================== 初始化 ====================

// 初始化表单默认值
const initFormValues = () => {
  props.fields.forEach(field => {
    if (field.defaultValue !== undefined) {
      formValues[field.name] = field.defaultValue
    } else if (field.type === 'select' && field.options?.length) {
      formValues[field.name] = field.options[0].value
    } else if (field.type === 'radio' && field.options?.length) {
      formValues[field.name] = field.options[0].value
    } else if (field.type === 'number') {
      formValues[field.name] = field.min ?? 0
    } else {
      formValues[field.name] = ''
    }
  })
}

// 监听 fields 变化重新初始化
watch(() => props.fields, () => {
  initFormValues()
}, { immediate: true })

// ==================== 方法 ====================

// 获取字段序号（考虑文件上传）
const getFieldIndex = (index: number): number => {
  const baseIndex = props.multipleFiles ? 3 : 2
  return baseIndex + index
}

// 获取字段验证规则
const getFieldRules = (field: AnalysisField) => {
  if (!field.required) return []
  return [{ required: true, message: `请填写${field.label}`, trigger: 'blur' }]
}

// 主文件上传处理
const handleFileChange = (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    formValues.file = uploadFile.raw
  }
}

// 第二个文件上传处理
const handleSecondFileChange = (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    formValues.secondFile = uploadFile.raw
  }
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const beforeUpload = (file: File): boolean => {
  const allowedTypes = ['text/plain', 'text/csv', 'application/csv']
  const allowedExtensions = ['.txt', '.csv', '.tsv']
  
  const isValidType = allowedTypes.includes(file.type)
  const fileName = file.name.toLowerCase()
  const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext))
  
  if (!isValidType && !hasValidExtension) {
    ElMessage.error('只支持 txt、csv、tsv 格式的文件！')
    return false
  }
  
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  
  return true
}

// 下载示例数据
const downloadExampleData = () => {
  if (!props.exampleDataUrl) {
    ElMessage.warning('暂无示例数据')
    return
  }
  
  const fileName = props.exampleFileName || 'example_data.txt'
  const link = document.createElement('a')
  link.href = props.exampleDataUrl
  link.download = fileName
  link.style.display = 'none'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success(`示例数据已开始下载: ${fileName}`)
}

// 下载第二个示例数据
const downloadSecondExampleData = () => {
  if (!props.secondExampleUrl) {
    ElMessage.warning('暂无示例数据')
    return
  }
  
  const fileName = props.secondExampleFileName || 'example_data_2.txt'
  const link = document.createElement('a')
  link.href = props.secondExampleUrl
  link.download = fileName
  link.style.display = 'none'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success(`示例数据已开始下载: ${fileName}`)
}

// 判断是否为图片文件
const isImageFile = (filename: string): boolean => {
  const imageExtensions = ['.png', '.jpg', '.jpeg', '.svg', '.pdf', '.tiff', '.bmp']
  const lowerName = filename.toLowerCase()
  return imageExtensions.some(ext => lowerName.endsWith(ext))
}

// 下载结果文件
const downloadFile = (file: AnalysisResultFile) => {
  window.open(file.url, '_blank')
}

// 以指定格式下载
const downloadInFormat = (format: string) => {
  if (!currentJobId.value) return
  // 构建格式化下载URL
  const downloadUrl = `http://localhost:8001/analysis-result/${currentJobId.value}/result.${format}`
  window.open(downloadUrl, '_blank')
}

// WebSocket 连接
const connectWebSocket = async () => {
  try {
    taskWsService.value = webSocketService
    
    taskWsService.value.setOnTaskStatus(async (data: any) => {
      const { job_id, status: taskStatus, progress: taskProgress, result_files, error_message } = data
      
      if (job_id === currentJobId.value) {
        jobStatus.value = taskStatus
        jobProgress.value = taskProgress || 0
        
        // 更新结果文件
        if (result_files && Array.isArray(result_files)) {
          analysisResults.value = result_files
        }
        
        if (taskStatus === 'COMPLETED' || taskStatus === 'Completed') {
          ElMessage.success(`分析任务 ${job_id} 已完成！`)
        } else if (taskStatus === 'FAILED' || taskStatus === 'Failed') {
          ElMessage.error(`分析任务 ${job_id} 失败: ${error_message || '未知错误'}`)
        }
      }
    })
    
    await taskWsService.value.connectTaskStatus()
    wsConnected.value = true
    
  } catch (error: any) {
    console.error('WebSocket 连接失败:', error)
    ElMessage.error('任务监控连接失败: ' + (error.message || '未知错误'))
  }
}

const disconnectWebSocket = () => {
  if (taskWsService.value) {
    taskWsService.value.disconnect()
    taskWsService.value = null
    wsConnected.value = false
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (!formValues.file) {
      ElMessage.error('请先上传文件')
      return
    }
    
    if (props.multipleFiles && !formValues.secondFile) {
      ElMessage.error('请上传第二个文件')
      return
    }
    
    submitting.value = true
    
    // 构造 FormData
    const requestData = new FormData()
    requestData.append('file', formValues.file)
    
    if (props.multipleFiles && formValues.secondFile) {
      requestData.append('file2', formValues.secondFile)
    }
    
    // 添加动态字段
    props.fields.forEach(field => {
      const value = formValues[field.name]
      if (value !== undefined && value !== null && value !== '') {
        requestData.append(field.name, String(value))
      }
    })
    
    // 添加邮箱
    if (formValues.email) {
      requestData.append('email', formValues.email)
    }
    
    // 保存参数用于结果显示
    jobParams.gene_nomenclature = props.title
    
    // 连接 WebSocket
    if (!wsConnected.value) {
      await connectWebSocket()
    }
    
    // 调用提交函数
    const result = await props.onSubmit(requestData)
    
    // 打开结果弹窗
    currentJobId.value = result.job_id
    jobStatus.value = 'SUBMITTED'
    jobProgress.value = 0
    analysisResults.value = []
    showResultDialog.value = true
    
    emit('submit-success', result)
    
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  formValues.file = null
  formValues.secondFile = null
  uploadRef.value?.clearFiles()
  secondUploadRef.value?.clearFiles()
  initFormValues()
}

// 处理状态变化
const handleStatusChange = (status: string) => {
  jobStatus.value = status
}

// 关闭对话框
const handleDialogClose = () => {
  showResultDialog.value = false
  currentJobId.value = ''
  jobStatus.value = 'WAITING'
  jobProgress.value = 0
  analysisResults.value = []
  resetForm()
}

// 组件卸载时断开 WebSocket
onUnmounted(() => {
  disconnectWebSocket()
})

// 暴露方法给父组件
defineExpose({
  resetForm,
  handleDialogClose
})
</script>

<style scoped>
.analysis-form {
  max-width: 900px;
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

.analysis-form-content {
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
  height: 150px;
}

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
}

.example-btn {
  margin-left: 12px;
}

.tip-notes {
  width: 100%;
}

.example-note {
  line-height: 1.5;
  display: block;
}

.field-tip {
  margin-top: 4px;
}

.submit-btn {
  width: 120px;
}

.example-image-container {
  text-align: center;
  width: 100%;
}

.example-label {
  margin-bottom: 15px;
  color: #606266;
}

.example-image {
  max-width: 100%;
  height: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

/* 结果展示样式 */
.analysis-results {
  margin-top: 20px;
}

.result-files {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-file-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
}

.image-preview {
  margin-bottom: 12px;
}

.result-image {
  max-width: 100%;
  max-height: 400px;
}

.file-download {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  color: #606266;
  font-size: 14px;
}

.download-formats {
  margin-top: 20px;
}

.dialog-footer {
  text-align: center;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .analysis-form {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .tip-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .example-btn {
    margin-left: 0;
    width: 100%;
    max-width: 200px;
  }
  
  .file-download {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
}
</style>
