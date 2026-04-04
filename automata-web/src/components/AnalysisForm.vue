<template>
  <div class="analysis-form">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{ title }}</span>
          <el-tag type="warning">{{ subtitle }}</el-tag>
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
                Drop file here or <em>click to upload</em>
              </div>
              <template #tip>
                <div class="upload-tip-container">
                  <div class="tip-content">
                    <span class="file-types">{{ fileTip || 'Only support txt file with tab delimiter' }}</span>
                    <el-button 
                      v-if="exampleDataUrl" 
                      type="primary" 
                      size="small" 
                      @click="downloadExampleData"
                      class="example-btn"
                    >
                      Download example
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
          v-if="showSecondFile" 
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
              :accept="secondAcceptTypes || acceptTypes"
              :before-upload="beforeSecondUpload"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                Drop file here or <em>click to upload</em>
              </div>
              <template #tip>
                <div class="upload-tip-container">
                  <div class="tip-content">
                    <span class="file-types">
                      {{ secondFileTip || fileTip || 'Only support txt file with tab delimiter' }}
                    </span>
                    <el-button 
                      v-if="secondExampleUrl" 
                      type="primary" 
                      size="small" 
                      @click="downloadSecondExampleData"
                      class="example-btn"
                    >
                      Download example
                    </el-button>
                  </div>
                </div>
              </template>
            </el-upload>
          </div>
        </el-form-item>

        <!-- 动态字段渲染 -->
        <!-- 保持左侧字体对齐，居左的命令 在el-form-item 用这个label-position="left" -->
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
              :placeholder="field.placeholder || 'Please select'"
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
            placeholder="Enter your email address"
            type="email"
          />
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item class="analysis-form-centered-row">
          <el-button 
            type="primary" 
            @click="submitForm"
            :loading="submitting"
            size="large"
            class="submit-btn"
          >
            {{ submitting ? 'Submitting…' : 'Submit' }}
          </el-button>
          <el-button @click="resetForm">Reset</el-button>
        </el-form-item>

        <!-- 示例图片展示 -->
        <el-form-item
          v-if="exampleImageUrl"
          class="analysis-form-centered-row"
        >
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
      <AnalysisResultPanel
        v-if="showResultDialog && currentJobId"
        :job-id="currentJobId"
        :status="jobStatus"
        :progress="jobProgress"
        :analysis-type-label="jobParams.gene_nomenclature"
        :param-rows="submittedAnalysisParams"
        :result-files="analysisResults"
        :error-message="analysisLastError"
        @enrichmentFollowupStarted="onEnrichmentFollowupStarted"
      />

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleDialogClose">Close and submit a new task</el-button>
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
import AnalysisResultPanel from './AnalysisResultPanel.vue'
import { webSocketService } from '@/api/websocket'
import { AnalysisAPI, type AnalysisField, type AnalysisResultFile } from '@/api/analysis'
import type { AnalysisParamRow } from './AnalysisResultPanel.vue'

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
  /** 提交到后端的主文件字段名 */
  fileFieldName?: string
  /** 示例数据下载地址 */
  exampleDataUrl?: string
  /** 示例文件名 */
  exampleFileName?: string
  /** 示例说明 */
  exampleNote?: string
  /** 是否支持多文件上传 */
  multipleFiles?: boolean
  /**
   * 第二个文件是否显示（可选）
   * - 若提供函数，则根据当前表单 formValues 决定
   * - 若未提供，则回退到 multipleFiles
   */
  secondFileVisible?: boolean | ((formValues: Record<string, any>) => boolean)
  /** 第二个文件上传标签 */
  secondFileLabel?: string
  /** 第二个示例数据URL */
  secondExampleUrl?: string
  /** 第二个示例文件名 */
  secondExampleFileName?: string
  /** 提交到后端的第二个文件字段名 */
  secondFileFieldName?: string
  /** 主文件上传标签 */
  fileLabel?: string
  /** 文件类型提示 */
  fileTip?: string
  /** 接受的文件类型 */
  acceptTypes?: string
  /** 第二个文件接受的后缀（用于可选第二文件场景） */
  secondAcceptTypes?: string
  /** 示例图片URL */
  exampleImageUrl?: string
  /** 第二个文件上传区域提示文案 */
  secondFileTip?: string
}

const props = withDefaults(defineProps<Props>(), {
  fileFieldName: 'file',
  multipleFiles: false,
  acceptTypes: '.txt,.csv,.tsv',
  secondFileFieldName: 'file2'
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
/** 提交快照：结果弹窗中展示与 AnalysisField 一致的参数行 */
const submittedAnalysisParams = ref<AnalysisParamRow[]>([])
/** 分析失败时的后端错误摘要 */
const analysisLastError = ref('')

// 表单值（动态字段 + 固定字段）
const formValues = reactive<Record<string, any>>({
  file: null,
  secondFile: null,
  email: ''
})

const showSecondFile = computed(() => {
  if (typeof props.secondFileVisible === 'function') {
    return !!props.secondFileVisible(formValues)
  }
  if (typeof props.secondFileVisible === 'boolean') {
    return props.secondFileVisible
  }
  return !!props.multipleFiles
})

// 任务参数（用于结果展示）
const jobParams = reactive({
  gene_nomenclature: '',
  data_type: '',
  organism: ''
})

// WebSocket 管理
const taskWsService = ref<any>(null)
const wsConnected = ref(false)
const statusPollTimer = ref<number | null>(null)

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

// 表单验证规则
const formRules = computed<FormRules>(() => {
  const rules: FormRules = {
    file: [{ required: true, message: '', trigger: 'change' }],
    email: [{ type: 'email', message: 'Please enter a valid email address', trigger: 'blur' }]
  }

  // 双文件模式下验证第二个文件
  if (showSecondFile.value) {
    rules.secondFile = [{ required: true, message: '', trigger: 'change' }]

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
      const options = field.options
      const first = options?.[0]
      if (first) formValues[field.name] = first.value
    } else if (field.type === 'radio' && field.options?.length) {
      const options = field.options
      const first = options?.[0]
      if (first) formValues[field.name] = first.value
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
  const baseIndex = showSecondFile.value ? 3 : 2
  return baseIndex + index
}

// 获取字段验证规则（默认必填：显示红星并与「上传数据」一致；显式 required: false 为可选项）
function buildSubmittedAnalysisParams(): AnalysisParamRow[] {
  const rows: AnalysisParamRow[] = []
  for (const field of visibleFields.value) {
    const raw = formValues[field.name]
    let display =
      raw === undefined || raw === null || raw === '' ? '' : String(raw)
    if (field.type === 'radio' || field.type === 'select') {
      const opt = field.options?.find((o) => String(o.value) === String(raw))
      if (opt) display = String(opt.label)
    }
    rows.push({ label: field.label, value: display })
  }
  return rows
}

async function hydrateAnalysisResults(jobId: string) {
  try {
    const r = await AnalysisAPI.getResult(jobId)
    if (r?.status) {
      jobStatus.value = String(r.status)
      if (String(r.status).toUpperCase() === 'COMPLETED') {
        jobProgress.value = 100
      }
    }
    if (r?.error_message) {
      analysisLastError.value = String(r.error_message)
    }
    if (r.result_files?.length) {
      analysisResults.value = r.result_files.map((f) => ({
        filename: f.filename,
        format: f.format,
        url: AnalysisAPI.getResultFileUrl(jobId, f.filename)
      }))
    }
  } catch (e) {
    console.error('拉取分析结果文件列表失败:', e)
  }
}

const stopStatusPolling = () => {
  if (statusPollTimer.value !== null) {
    window.clearInterval(statusPollTimer.value)
    statusPollTimer.value = null
  }
}

const startStatusPolling = (jobId: string) => {
  stopStatusPolling()
  statusPollTimer.value = window.setInterval(async () => {
    if (!showResultDialog.value || !currentJobId.value) return
    if (currentJobId.value !== jobId) return
    await hydrateAnalysisResults(jobId)

    const s = String(jobStatus.value || '').toUpperCase()
    if (s === 'COMPLETED' || s === 'FAILED') {
      stopStatusPolling()
    }
  }, 3000)
}

function onEnrichmentFollowupStarted(jobId: string) {
  // 综合分析：主流程 Completed 后轮询会停；继续 GO/KEGG 后必须重启轮询并刷新 result_files 才能展示富集结果
  void hydrateAnalysisResults(jobId)
  startStatusPolling(jobId)
}

const getFieldRules = (field: AnalysisField) => {
  if (field.required === false) return []
  const trigger: 'blur' | 'change' =
    field.type === 'radio' || field.type === 'select' || field.type === 'number'
      ? 'change'
      : 'blur'
  return [{ required: true, message: `Please fill in ${field.label}`, trigger }]
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
  ElMessage.warning('Only one file is allowed')
}

const beforeUpload = (file: File): boolean => {
  const fileName = file.name.toLowerCase()
  const allowedExtensions = (props.acceptTypes || '')
    .split(',')
    .map(s => s.trim().toLowerCase())
    .filter(Boolean)

  const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext))

  if (!hasValidExtension) {
    ElMessage.error('Unsupported file type. Please upload a file with an allowed extension.')
    return false
  }
  
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    ElMessage.error('File size must not exceed 10 MB')
    return false
  }
  
  return true
}

const beforeSecondUpload = (file: File): boolean => {
  const fileName = file.name.toLowerCase()
  const accept = props.secondAcceptTypes ?? props.acceptTypes
  const allowedExtensions = (accept || '')
    .split(',')
    .map(s => s.trim().toLowerCase())
    .filter(Boolean)

  const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext))

  if (!hasValidExtension) {
    ElMessage.error('Unsupported file type. Please upload a file with an allowed extension.')
    return false
  }

  const maxSize = 50 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    ElMessage.error('File size must not exceed 50 MB')
    return false
  }

  return true
}

// 下载示例数据
const downloadExampleData = () => {
  if (!props.exampleDataUrl) {
    ElMessage.warning('No example data available')
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
  
  ElMessage.success(`Example download started: ${fileName}`)

  // // 使用后端 API 下载示例数据
  // const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  // // 从 exampleDataUrl 中提取分析类型，例如：/example/draw_example/pca_example.txt -> pca
  // const analysisType = extractAnalysisType(props.exampleDataUrl)
  
  // if (analysisType) {
  //   const downloadUrl = `${apiBaseUrl}/api/v1/data-process/examples/draw/${analysisType}`
  //   window.open(downloadUrl, '_blank')
  //   ElMessage.success(`示例数据已开始下载：${fileName}`)
  // } else {
  //   // 降级处理：直接下载静态文件
  //   const link = document.createElement('a')
  //   link.href = props.exampleDataUrl
  //   link.download = fileName
  //   link.style.display = 'none'
    
  //   document.body.appendChild(link)
  //   link.click()
  //   document.body.removeChild(link)
    
  //   ElMessage.success(`示例数据已开始下载：${fileName}`)
  // }
}

// 从 URL 中提取分析类型
const extractAnalysisType = (url: string): string | null => {
  // 匹配 /example/draw_example/{type}_example.txt 格式
  const match = url.match(/\/example\/draw_example\/([\w-]+)_example\.txt/)
  if (match && match[1]) {
    return match[1]
  }
  return null
}

// 下载第二个示例数据
const downloadSecondExampleData = () => {
  if (!props.secondExampleUrl) {
    ElMessage.warning('No example data available')
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
  
  ElMessage.success(`Example download started: ${fileName}`)
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
        if (error_message) {
          analysisLastError.value = String(error_message)
        }
        
        // 更新结果文件
        if (result_files && Array.isArray(result_files)) {
          analysisResults.value = result_files.map((f: AnalysisResultFile) => ({
            ...f,
            url:
              f.url ||
              AnalysisAPI.getResultFileUrl(job_id, f.filename)
          }))
        }
        
        if (taskStatus === 'COMPLETED' || taskStatus === 'Completed') {
          analysisLastError.value = ''
          void hydrateAnalysisResults(job_id)
          ElMessage.success(`Analysis job ${job_id} completed.`)
        } else if (taskStatus === 'FAILED' || taskStatus === 'Failed') {
          ElMessage.error(`Analysis job ${job_id} failed: ${error_message || 'Unknown error'}`)
        }
      }
    })
    
    await taskWsService.value.connectTaskStatus()
    wsConnected.value = true
    
  } catch (error: any) {
    console.error('WebSocket 连接失败:', error)
    ElMessage.error('Task status connection failed: ' + (error.message || 'Unknown error'))
  }
}

const disconnectWebSocket = () => {
  if (taskWsService.value) {
    taskWsService.value.disconnectTaskStatus()
    taskWsService.value = null
    wsConnected.value = false
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 构造 FormData
    const requestData = new FormData()
    requestData.append(props.fileFieldName || 'file', formValues.file)
    
    if (showSecondFile.value && formValues.secondFile) {
      requestData.append(props.secondFileFieldName || 'file2', formValues.secondFile)
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
    submittedAnalysisParams.value = buildSubmittedAnalysisParams()
    
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
    analysisLastError.value = ''
    showResultDialog.value = true
    void hydrateAnalysisResults(result.job_id)
    startStatusPolling(result.job_id)
    
    emit('submit-success', result)
    
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || 'Submission failed. Please try again.')
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

// 关闭对话框
const handleDialogClose = () => {
  stopStatusPolling()
  showResultDialog.value = false
  currentJobId.value = ''
  jobStatus.value = 'WAITING'
  jobProgress.value = 0
  analysisResults.value = []
  submittedAnalysisParams.value = []
  analysisLastError.value = ''
  resetForm()
}

// 组件卸载时断开 WebSocket
onUnmounted(() => {
  stopStatusPolling()
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
  height: 170px;
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
  margin-top: -3px;
  margin-bottom: -4px;
}

.submit-btn {
  width: 120px;
}

.example-image-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
  max-width: 100%;
}

.example-label {
  margin: 0 0 15px;
  color: #606266;
  width: 100%;
}

.example-image {
  display: block;
  max-width: 100%;
  width: auto;
  height: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.dialog-footer {
  text-align: center;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  /* width: 250px; */
}

/* 无 label 的表单项在全局 label-width 下仍会占标签列宽，导致内容偏右；此处占满整行并居中 */
.analysis-form-content :deep(.analysis-form-centered-row.el-form-item .el-form-item__label) {
  display: none;
}

.analysis-form-content :deep(.analysis-form-centered-row.el-form-item .el-form-item__content) {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-left: 0 !important;
  max-width: 100%;
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
}
</style>
