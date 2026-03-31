<template>
  <div>
    <!-- pvalue 多组学整合表单 -->
    <el-card class="pvalue-card">
      <template #header>
        <div class="card-header">
          <span class="title">Pvalue Multi-omics Integration</span>
          <el-tag type="success">Pvalue Multi-omics Integration</el-tag>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="220px"
        class="pvalue-form"
      >
        <!-- 1. 组学文件 1 -->
        <el-form-item label="Upload omics file 1" prop="file1">
          <el-upload
            class="upload-block"
            drag
            :auto-upload="false"
            :limit="1"
            :show-file-list="true"
            :on-change="(file: UploadFile) => handleFileChange(file, 'file1')"
            :on-exceed="handleExceed"
            accept=".txt,.csv,.tsv"
          >
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">
              Drag and drop the omics file 1 here, or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">Only support txt file with tab delimiter (contains pvalue)</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample(1)"
                  class="example-btn"
                >
                  Download Example Data
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 2. 组学文件 2 -->
        <el-form-item label="Upload omics file 2" prop="file2">
          <el-upload
            class="upload-block"
            drag
            :auto-upload="false"
            :limit="1"
            :show-file-list="true"
            :on-change="(file: UploadFile) => handleFileChange(file, 'file2')"
            :on-exceed="handleExceed"
            accept=".txt,.csv,.tsv"
          >
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">
              Drag and drop the omics file 2 here, or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">Only support txt file with tab delimiter (contains pvalue)</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample(2)"
                  class="example-btn"
                >
                  Download Example Data
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 3. 组学文件 3 -->
        <el-form-item label="Upload omics file 3" prop="file3">
          <el-upload
            class="upload-block"
            drag
            :auto-upload="false"
            :limit="1"
            :show-file-list="true"
            :on-change="(file: UploadFile) => handleFileChange(file, 'file3')"
            :on-exceed="handleExceed"
            accept=".txt,.csv,.tsv"
          >
            <el-icon class="el-icon--upload">
              <upload-filled />
            </el-icon>
            <div class="el-upload__text">
              Drag and drop the omics file 3 here, or <em>click to upload</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">Only support txt file with tab delimiter (contains pvalue)</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample(3)"
                  class="example-btn"
                >
                  Download Example Data
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 4. 方法选择 -->
        <el-form-item label="Select pvalue method" prop="method">
          <el-select
            v-model="formData.method"
            placeholder="Select pvalue integration method"
            style="width: 100%"
          >
            <el-option label="Fisher" value="Fisher" />
            <el-option label="Fisher_directional" value="Fisher_directional" />
            <el-option label="Brown" value="Brown" />
            <el-option label="DPM" value="DPM" />
            <el-option label="Stouffer" value="Stouffer" />
            <el-option label="Stouffer_directional" value="Stouffer_directional" />
            <el-option label="Strube" value="Strube" />
            <el-option label="Strube_directional" value="Strube_directional" />
            <el-option label="None" value="None" />
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
        :compact="false"
        :hide-data-type="true"
        :hide-organism="true"
        nomenclature-label="Method"
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
import TaskResultDisplay from '@/components/TaskResultDisplay.vue'

interface PvalueFormData {
  file1: File | null
  file2: File | null
  file3: File | null
  method: string
  email: string
}

const formRef = ref<FormInstance>()

const formData = reactive<PvalueFormData>({
  file1: null,
  file2: null,
  file3: null,
  method: '',
  email: ''
})

const formRules: FormRules = {
  file1: [{ required: true, message: 'Upload omics file 1', trigger: 'change' }],
  file2: [{ required: true, message: 'Upload omics file 2', trigger: 'change' }],
  file3: [{ required: true, message: 'Upload omics file 3', trigger: 'change' }],
  method: [{ required: true, message: 'Select pvalue integration method', trigger: 'change' }],
  email: [{ type: 'email', message: 'Enter a valid email address', trigger: 'blur' }]
}

const submitting = ref(false)

// 任务状态
const showResultDialog = ref(false)
const currentJobId = ref('')
const jobStatus = ref<any>('WAITING')
const jobProgress = ref(0)

// 任务参数：用于结果页展示（jobid + 方法 + Data Process Result）
const jobParams = reactive({
  gene_nomenclature: '',
  data_type: 'N/A',
  organism: 'N/A'
})

// WebSocket 管理
const taskWsService = ref<any>(null)
const wsConnected = ref(false)

const handleFileChange = (uploadFile: UploadFile, key: keyof PvalueFormData) => {
  if (uploadFile.raw) {
    if (key === 'file1') {
      formData.file1 = uploadFile.raw as File
    } else if (key === 'file2') {
      formData.file2 = uploadFile.raw as File
    } else if (key === 'file3') {
      formData.file3 = uploadFile.raw as File
    }
  }
}

const handleExceed = () => {
  ElMessage.warning('Only one file can be uploaded at each location')
}

const downloadExample = (index: 1 | 2 | 3) => {
  // 示例文件位于 Vite public 目录：/example/omics_integration_file_X.txt
  const fileNameMap: Record<number, string> = {
    1: 'omics_integration_file_1.txt',
    2: 'omics_integration_file_2.txt',
    3: 'omics_integration_file_3.txt'
  }
  const fileName = fileNameMap[index] || ''
  const url = `/example/${fileName}`
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
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
    taskWsService.value.disconnect()
    taskWsService.value = null
    wsConnected.value = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (!formData.file1 || !formData.file2 || !formData.file3) {
      ElMessage.error('Please upload all required files')
      return
    }

    submitting.value = true

    // 构造 FormData
    const requestData = new FormData()
    requestData.append('file_1', formData.file1)
    requestData.append('file_2', formData.file2)
    requestData.append('file_3', formData.file3)
    requestData.append('method', formData.method)
    if (formData.email) {
      requestData.append('email', formData.email)
    }

    // 保存方法名称用于结果展示
    jobParams.gene_nomenclature = formData.method

    // 连接 WebSocket（如果还没有连接）
    if (!wsConnected.value) {
      await connectWebSocket()
    }

    const result = await DataProcessAPI.processPvalueIntegration(requestData)

    currentJobId.value = result.job_id
    jobStatus.value = 'SUBMITTED'
    jobProgress.value = 0
    showResultDialog.value = true

    ElMessage.success('P-value multi-omics integration task submitted')
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || 'Submission failed. Please try again.')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  formData.file1 = null
  formData.file2 = null
  formData.file3 = null
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
      ElMessage.info('Task finished')
    }, 2000)
  }
}

const handleClose = () => {
  showResultDialog.value = false
  currentJobId.value = ''
  jobStatus.value = 'WAITING'
  jobProgress.value = 0
  jobParams.gene_nomenclature = ''
}

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.pvalue-card {
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

.pvalue-form {
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

.pvalue-form :deep(.el-form-item__content) {
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
  width: 180px;
}
</style>

