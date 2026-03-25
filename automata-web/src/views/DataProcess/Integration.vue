<template>
  <div>
    <!-- 多组学数据整合表单 -->
    <el-card class="integration-card">
      <template #header>
        <div class="card-header">
          <span class="title">多组学数据整合</span>
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
        <el-form-item label="上传表型数据" prop="phenoFile">
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
              将表型数据拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">仅支持 txt、csv、tsv 格式的文件</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('pheno')"
                  class="example-btn"
                >
                  下载示例数据
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 2. 基因组数据 -->
        <el-form-item label="上传基因组数据" prop="omics1File">
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
              将基因组数据拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">仅支持 txt、csv、tsv 格式的文件</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('omics1')"
                  class="example-btn"
                >
                  下载示例数据
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 3. 转录组数据 -->
        <el-form-item label="上传转录组数据" prop="omics2File">
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
              将转录组数据拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">仅支持 txt、csv、tsv 格式的文件</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('omics2')"
                  class="example-btn"
                >
                  下载示例数据
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 4. 蛋白组数据 -->
        <el-form-item label="上传蛋白组数据" prop="omics3File">
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
              将蛋白组数据拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="upload-tip-container">
                <span class="file-types">仅支持 txt、csv、tsv 格式的文件</span>
                <el-button
                  type="primary"
                  size="small"
                  @click="downloadExample('omics3')"
                  class="example-btn"
                >
                  下载示例数据
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 邮箱 -->
        <el-form-item label="您的邮箱" prop="email">
          <el-input
            v-model="formData.email"
            placeholder="请输入邮箱地址（可选）"
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
            {{ submitting ? '处理中...' : '提交整合' }}
          </el-button>
          <el-button @click="resetForm">重置</el-button>
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
          <el-button @click="handleClose">关闭并提交新任务</el-button>
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
  phenoFile: [{ required: true, message: '请上传表型数据文件', trigger: 'change' }],
  omics1File: [{ required: true, message: '请上传基因组数据文件', trigger: 'change' }],
  omics2File: [{ required: true, message: '请上传转录组数据文件', trigger: 'change' }],
  omics3File: [{ required: true, message: '请上传蛋白组数据文件', trigger: 'change' }],
  email: [{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }]
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
  ElMessage.warning('每个位置只能上传一个文件')
}

const downloadExample = (type: 'pheno' | 'omics1' | 'omics2' | 'omics3') => {
  // 使用独立下载服务 (8001) 提供示例文件：
  // 例如 http://localhost:8001/example/train_example/jobID_pheno.txt
  const origin = window.location.origin
  const base = origin.replace(/:\d+$/, ':8001')

  let relativePath = ''
  switch (type) {
    case 'pheno':
      relativePath = 'train_example/jobID_pheno.txt'
      break
    case 'omics1':
      relativePath = 'train_example/jobID_omics_1.txt'
      break
    case 'omics2':
      relativePath = 'train_example/jobID_omics_2.txt'
      break
    case 'omics3':
      relativePath = 'train_example/jobID_omics_3.txt'
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
          ElMessage.success(`任务 ${job_id} 已完成！`)
          if (result_file) {
            ElMessage.info(`结果文件已生成: ${result_file}`)
          }
        } else if (taskStatus === 'FAILED' || taskStatus === 'Failed') {
          ElMessage.error(`任务 ${job_id} 失败: ${error_message || '未知错误'}`)
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
      ElMessage.error('请上传所有必需的文件')
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

    ElMessage.success('多组学数据整合任务已提交')
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '提交失败，请重试')
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
  ElMessage.success('多组学数据整合任务已提交')
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
      ElMessage.info('任务已完成')
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

