<template>
  <div>
    <!-- 多组学数据整合表单 -->
    <el-card class="integration-card">
      <template #header>
        <div class="card-header">
          <span class="title">Multi-omics Data Integration</span>
          <el-tag type="success">Multi-omics Data Integration</el-tag>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="220px"
        class="integration-form"
      >
        <!-- 1. 表型数据 -->
        <el-form-item label="Upload Phenotype Data" prop="phenoFile">
          <el-upload
            class="upload-block"
            drag
            :auto-upload="false"
            :limit="1"
            :show-file-list="true"
            :on-change="(file: UploadFile) => handleFileChange(file, 'phenoFile')"
            :on-exceed="handleExceed"
            accept=".txt,.csv,.tsv"
          >
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">
              Drag and drop the phenotype file here, or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">Only support txt file with tab delimiter</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('pheno')"
                  class="example-btn"
                >
                  Download Example Phenotype Data
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 2. 基因组数据 -->
        <el-form-item label="Upload Genome Data" prop="omics1File">
          <el-upload
            class="upload-block"
            drag
            :auto-upload="false"
            :limit="1"
            :show-file-list="true"
            :on-change="(file: UploadFile) => handleFileChange(file, 'omics1File')"
            :on-exceed="handleExceed"
            accept=".txt,.csv,.tsv"
          >
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">
              Drag and drop the genome file here, or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">Only support txt file with tab delimiter</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('omics1')"
                  class="example-btn"
                >
                  Download Example Genome Data
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 3. 转录组数据 -->
        <el-form-item label="Upload Transcriptome Data" prop="omics2File">
          <el-upload
            class="upload-block"
            drag
            :auto-upload="false"
            :limit="1"
            :show-file-list="true"
            :on-change="(file: UploadFile) => handleFileChange(file, 'omics2File')"
            :on-exceed="handleExceed"
            accept=".txt,.csv,.tsv"
          >
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">
              Drag and drop the transcriptome file here, or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">Only support txt file with tab delimiter</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('omics2')"
                  class="example-btn"
                >
                  Download Example Transcriptome Data
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 4. 蛋白组数据 -->
        <el-form-item label="Upload Proteomics Data" prop="omics3File">
          <el-upload
            class="upload-block"
            drag
            :auto-upload="false"
            :limit="1"
            :show-file-list="true"
            :on-change="(file: UploadFile) => handleFileChange(file, 'omics3File')"
            :on-exceed="handleExceed"
            accept=".txt,.csv,.tsv"
          >
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">
              Drag and drop the proteomics file here, or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">Only support txt file with tab delimiter</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('omics3')"
                  class="example-btn"
                >
                  Download Example Proteomics Data
                </el-button>
              </div>
            </template>
          </el-upload>
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
      </el-form>
    </el-card>

    <!-- 任务结果弹窗 -->
    <el-dialog
      v-model="showResultDialog"
      width="80%"
      :close-on-click-modal="false"
      @close="handleClose"
    >
      <TaskResultDisplay
        v-if="showResultDialog && currentJobId"
        :job-id="currentJobId"
        :params="jobParams"
        :compact="true"
        :initial-status="jobStatus"
        :initial-progress="jobProgress"
        @status-change="handleStatusChange"
      />

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">Close and Submit New Task</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { DataProcessAPI } from '@/api'
import { getDownloadOrigin } from '@/config/deploy'

const formRef = ref<FormInstance>()

interface IntegrationFormData {
  phenoFile: File | null
  omics1File: File | null
  omics2File: File | null
  omics3File: File | null
  email: string
}

const formData = reactive<IntegrationFormData>({
  phenoFile: null,
  omics1File: null,
  omics2File: null,
  omics3File: null,
  email: ''
})

const formRules: FormRules = {
  phenoFile: [{ required: true, message: 'Upload phenotype data file', trigger: 'change' }],
  omics1File: [{ required: true, message: 'Upload genome data file', trigger: 'change' }],
  omics2File: [{ required: true, message: 'Upload transcriptome data file', trigger: 'change' }],
  omics3File: [{ required: true, message: 'Upload proteomics data file', trigger: 'change' }],
  email: [{ type: 'email', message: 'Enter a valid email address', trigger: 'blur' }]
}

const submitting = ref(false)

// 任务状态
const showResultDialog = ref(false)
const currentJobId = ref('')
const jobStatus = ref('WAITING')
const jobProgress = ref(0)

// 任务参数：为了复用 TaskResultDisplay，这里填充描述性字段
const jobParams = reactive({
  gene_nomenclature: 'Multi-omics Integration',
  data_type: 'N/A',
  organism: 'N/A'
})

// WebSocket 管理
const taskWsService = ref<any>(null)
const wsConnected = ref(false)

const handleFileChange = (uploadFile: UploadFile, key: keyof IntegrationFormData) => {
  if (uploadFile.raw) {
    // 由于 key 是联合类型，这里通过类型缩小分别赋值，避免 TS 推断为 string | File
    if (key === 'phenoFile') {
      formData.phenoFile = uploadFile.raw as File
    } else if (key === 'omics1File') {
      formData.omics1File = uploadFile.raw as File
    } else if (key === 'omics2File') {
      formData.omics2File = uploadFile.raw as File
    } else if (key === 'omics3File') {
      formData.omics3File = uploadFile.raw as File
    }
  }
}

const handleExceed = () => {
  ElMessage.warning('Only one file can be uploaded at each location')
}

const downloadExample = (type: 'pheno' | 'omics1' | 'omics2' | 'omics3') => {
  const base = getDownloadOrigin()

  let relativePath = ''
  switch (type) {
    case 'pheno':
      relativePath = 'jobID_pheno.txt'
      break
    case 'omics1':
      relativePath = 'jobID_omics_1.txt'
      break
    case 'omics2':
      relativePath = 'jobID_omics_2.txt'
      break
    case 'omics3':
      relativePath = 'jobID_omics_3.txt'
      break
  }

  const url = `${base}/example/${relativePath}`
  window.open(url, '_blank')
}

const connectWebSocket = async () => {
  try {
    const { webSocketService } = await import('@/api/websocket')
    taskWsService.value = webSocketService

    taskWsService.value.setOnTaskStatus(async (data: any) => {
      const { job_id, status: taskStatus, progress: taskProgress, result_file, error_message } =
        data

      if (job_id === currentJobId.value) {
        jobStatus.value = taskStatus
        jobProgress.value = taskProgress || 0

        if (taskStatus === 'COMPLETED' || taskStatus === 'Completed') {
          ElMessage.success(`Task ${job_id} has been completed!`)
          if (result_file) {
            ElMessage.info(`Result file has been generated: ${result_file}`)
          }
        } else if (taskStatus === 'FAILED' || taskStatus === 'Failed') {
          ElMessage.error(`Task ${job_id} failed: ${error_message || 'Unknown error'}`)
        }
      }
    })

    await taskWsService.value.connectTaskStatus()
    wsConnected.value = true
  } catch (error: any) {
    console.error('WebSocket 连接失败:', error)
    ElMessage.error('Task monitoring connection failed: ' + (error.message || 'Unknown error'))
  }
}

const disconnectWebSocket = () => {
  if (taskWsService.value) {
    taskWsService.value.disconnectTaskStatus()
    taskWsService.value = null
    wsConnected.value = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (
      !formData.phenoFile ||
      !formData.omics1File ||
      !formData.omics2File ||
      !formData.omics3File
    ) {
      ElMessage.error('Please upload all required files')
      return
    }

    submitting.value = true

    // 构造 FormData
    const requestData = new FormData()
    requestData.append('pheno_file', formData.phenoFile)
    requestData.append('file_1', formData.omics1File)
    requestData.append('file_2', formData.omics2File)
    requestData.append('file_3', formData.omics3File)
    if (formData.email) {
      requestData.append('email', formData.email)
    }

    // 连接 WebSocket（如果还没有连接）
    if (!wsConnected.value) {
      await connectWebSocket()
    }

    const result = await DataProcessAPI.processIntegration(requestData)

    currentJobId.value = result.job_id
    jobStatus.value = 'SUBMITTED'
    jobProgress.value = 0
    showResultDialog.value = true

    ElMessage.success('Multi-omics data integration task has been submitted')
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || 'Submission failed. Please try again')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  formData.phenoFile = null
  formData.omics1File = null
  formData.omics2File = null
  formData.omics3File = null
}

const handleSuccess = (result: any) => {
  ElMessage.success('Multi-omics data integration task has been submitted')
}

const handleStatusChange = (status: string) => {
  jobStatus.value = status

  if (
    status === 'COMPLETED' ||
    status === 'Completed' ||
    status === 'FAILED' ||
    status === 'Failed'
  ) {
    setTimeout(() => {
      ElMessage.info('Task has been completed')
    }, 2000)
  }
}

const handleClose = () => {
  showResultDialog.value = false
  currentJobId.value = ''
  jobStatus.value = 'WAITING'
  jobProgress.value = 0
}

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.integration-card {
  max-width: 800px;
  margin: 0 auto;
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.integration-form {
  padding: 20px 0;
}

.upload-block {
  width: 100%;
  flex: 1 1 auto;
}

.upload-block :deep(.el-upload) {
  width: 100%;
}

.upload-block :deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
}

/* 让本页的表单内容区域占满一整行，上传框覆盖 el-form-item__content 的可用宽度 */
.integration-form :deep(.el-form-item__content) {
  flex: 1 1 auto;
  width: 100%;
}

.upload-tip-container {
  width: 100%;
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

.submit-btn {
  width: 140px;
}
</style>

