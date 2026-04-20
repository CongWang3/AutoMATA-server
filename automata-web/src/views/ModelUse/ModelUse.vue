<template>
  <div class="automata-training-supervised">
    <div class="container-fluid p-4">
      <!-- 模型使用表单卡片 -->
      <div class="row justify-content-center">
        <div class="col-12 col-lg-8">
          <el-card class="form-card">
            <template #header>
              <div class="card-header">
                <span class="title">Use Your Own Model</span>
                <el-tag type="primary">Model Use</el-tag>
              </div>
            </template>
            <div class="card-body p-4">
              <form @submit.prevent="handleSubmit" class="use-form">
                <!-- 第一步：选择模型类型 -->
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center"  style="border-bottom: none; padding-bottom: 0;">
                    <h5 class="section-title">
                      1. Choose Model
                      <span class="section-subtitle">Required</span>
                    </h5>
                  </div>

                  <div class="mb-3">
                    <!-- <label class="form-label">模型类型 *</label> -->
                    <select 
                      class="form-select" 
                      v-model="formData.modelType" 
                      required
                      @change="handleModelTypeChange"
                    >
                      <option value="cnn">CNN</option>
                      <option value="lstm">LSTM</option>
                      <option value="rnn">RNN</option>
                      <option value="mlp">MLP</option>
                      <option value="autoencoder">AutoEncoder</option>
                      <option value="transformer">Transformer</option>
                      <option value="som">SOM</option>
                      <option value="rbfn">RBFNN</option>
                      <option value="vae">VAE</option>
                      <option value="deepcluster">DeepCluster</option>
                      <option value="ladder">LadderNetwork</option>
                      <option value="pseudo">Pseudo-Labeling</option>
                    </select>
                  </div>
                </div>

                <!-- 第二步：上传测试数据 -->
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center"  style="border-bottom: none; padding-bottom: 0;">
                    <h5 class="section-title">
                      2. Upload Testing Data
                      <span class="section-subtitle">Required</span>
                    </h5>
                    <el-button 
                        type="primary" 
                        size="small" 
                        @click="downloadTestDataExample"
                        class="example-btn"
                        >
                        Download Example Data
                    </el-button>
                  </div>

                  <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <!-- <label class="form-label mb-0">测试数据集</label> -->
                      <!-- <button
                        type="button"
                        class="btn btn-sm btn-primary"
                        @click="downloadTestDataExample"
                      >
                        下载示例数据
                      </button> -->
                    </div>
                    <FileUploader
                      ref="testDataUploader"
                      :allowed-types="['txt', 'csv', 'tsv']"
                      :max-size="50 * 1024 * 1024"
                      @file-selected="handleTestDataSelected"
                    />
                    <div class="form-text" v-if="showNoLabelNote">
                      NOTE: The testing dataset of unsupervised models does not need labels and sample names
                    </div>
                  </div>
                </div>

                <!-- 第三步：上传模型文件 -->
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center"  style="border-bottom: none; padding-bottom: 0;">
                    <h5 class="section-title">
                      3. Upload the model file
                      <span class="section-subtitle">Required</span>
                    </h5>
                    <el-button 
                        type="primary" 
                        size="small" 
                        @click="downloadModelExample"
                        class="example-btn"
                        >
                        Download Example Model
                    </el-button>
                  </div>

                  <!-- 通用模型文件上传 -->
                  <div class="mb-3" v-show="showGenericModelUpload">
                    <!-- <div class="d-flex justify-content-between align-items-center mb-2">

                    </div> -->
                    <FileUploader
                      ref="modelUploader"
                      :allowed-types="['pth']"
                      :max-size="50 * 1024 * 1024"
                      @file-selected="handleModelSelected"
                    />
                  </div>

                  <!-- SOM 特有文件上传 -->
                  <div v-show="formData.modelType === 'som'">
                    <div class="mb-3">
                      <!-- <label class="form-label">模型文件</label> -->
                      <FileUploader
                        ref="somModelUploader"
                        :allowed-types="['pth']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleSomModelSelected"
                      />
                    </div>
                  </div>

                  <!-- AutoEncoder 特有文件上传 -->
                  <div v-show="formData.modelType === 'autoencoder'">
                    <div class="mb-3">
                      <label class="form-label">Encoder model file</label>
                      <FileUploader
                        ref="encoderUploader"
                        :allowed-types="['pth']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleEncoderSelected"
                      />
                    </div>
                    <div class="mb-3">
                      <label class="form-label">Classifier model file</label>
                      <FileUploader
                        ref="classifierUploader"
                        :allowed-types="['pth']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleClassifierSelected"
                      />
                    </div>
                  </div>

                  <!-- 无监督/半监督模型特有文件上传 -->
                  <div v-show="showUnSemiModelUpload">
                    <div class="mb-3">
                      <label class="form-label">Scaler file</label>
                      <FileUploader
                        ref="scalerUploader"
                        :allowed-types="['pkl']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleScalerSelected"
                      />
                    </div>
                    <div class="mb-3">
                      <label class="form-label">Model file</label>
                      <FileUploader
                        ref="unSemiModelUploader"
                        :allowed-types="['pth']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleUnSemiModelSelected"
                      />
                    </div>
                  </div>
                </div>

                <!-- 第四步：联系方式 -->
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center"  style="border-bottom: none; padding-bottom: 0;">
                    <h5 class="section-title">
                      4. Notification
                      <span class="section-subtitle">Optional</span>
                    </h5>
                  </div>

                  <div class="mb-3">
                    <!-- <label class="form-label">邮箱地址（可选）</label> -->
                    <input
                      type="email"
                      class="form-control"
                      v-model="formData.email"
                      placeholder="Email (optional, for prediction result notifications)"
                    >
                    <!-- <div class="form-text">我们将通过邮件发送预测结果给您</div> -->
                  </div>
                </div>

                <!-- 提交按钮 -->
                <div class="d-flex justify-content-center gap-3 mt-4">
                  
                  <button 
                    type="submit" 
                    class="btn btn-primary px-5"
                    :disabled="!isFormValid || isSubmitting"
                  >
                    <span 
                      v-if="isSubmitting" 
                      class="spinner-border spinner-border-sm me-2" 
                      role="status"
                    ></span>
                    {{ isSubmitting ? 'Predicting...' : 'Submit' }}
                  </button>

                  <!-- <el-button 
                    type="primary" 
                    @click="submitForm"
                    :loading="submitting"
                    size="large"
                    class="submit-btn"
                  >
                    {{ submitting ? 'Submitting…' : 'Submit' }}
                  </el-button> -->

                  <!-- <button 
                    type="button" 
                    class="btn btn-secondary px-4"
                    @click="resetForm"
                  >
                    Reset
                  </button> -->
                  <el-button 
                    class="btn btn-secondary px-4"
                    @click="resetForm"
                  >
                    Reset
                  </el-button>

                </div>
              </form>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 结果弹窗（与监督学习保持一致） -->
      <el-dialog
        v-model="showResultDialog"
        width="80%"
        :close-on-click-modal="false"
        @close="handleClose"
      >
        <TrainingResultPanel
          v-if="currentJob?.id"
          :job-id="currentJob.id"
          :status="currentJob.status"
          :input-params="unifiedJob?.input_params || submittedInputParams || {}"
          :error-message="currentJob.errorMessage"
          :download-ready="downloadReady"
          :hide-labels="['Test Dataset', 'Model File']"
          :on-download="onDownload"
        />

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="handleClose">Close and submit a new task</el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import FileUploader from '@/components/FileUpload/FileUploader.vue'
import TrainingResultPanel from '@/components/Training/TrainingResultPanel.vue'
import { modelUseApi } from '@/api/modelUse'
import { jobsApi } from '@/api/jobs'
import { ElMessage } from 'element-plus'

interface FormData {
  modelType: string
  email: string
}

interface Job {
  id: string
  name: string
  status:
    | 'Submitted'
    | 'Processing'
    | 'Completed'
    | 'Failed'
    | 'Cancelled'
    | 'PENDING'
    | 'RUNNING'
    | 'COMPLETED'
    | 'FAILED'
    | 'CANCELLED'
  progress: number
  currentStep?: string
  createdAt: string
  updatedAt: string
  duration: number
  resultFile?: string
  errorMessage?: string
}

// 响应式数据
const isSubmitting = ref(false)
const currentJob = ref<Job | null>(null)
const showResultDialog = ref(false)
const unifiedJob = ref<any | null>(null)
const submittedInputParams = ref<Record<string, any> | null>(null)
const downloadReady = ref(false)
const preparedDownloadUrl = ref<string | null>(null)
let pollingTimer: ReturnType<typeof setTimeout> | null = null

const stopPolling = () => {
  if (pollingTimer) {
    clearTimeout(pollingTimer)
    pollingTimer = null
  }
}

const isTerminalStatus = (status: unknown) => {
  const s = String(status || '').toUpperCase()
  return s === 'COMPLETED' || s === 'FAILED' || s === 'CANCELLED'
}

const refreshUnifiedJob = async (jobId: string) => {
  try {
    const detail = await jobsApi.getJobDetail(jobId)
    if (currentJob.value?.id === jobId) {
      unifiedJob.value = detail
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
  }
}

const pollTaskStatus = async (taskId: string) => {
  stopPolling()

  const poll = async () => {
    try {
      const task = await jobsApi.getJobDetail(taskId)

      if (currentJob.value && currentJob.value.id === taskId) {
        currentJob.value.status = task.status as Job['status']
        currentJob.value.progress = task.progress || 0
        currentJob.value.currentStep = task.current_step || undefined
        currentJob.value.resultFile = task.result_file
        currentJob.value.errorMessage = task.error_message
        if (task.created_at) currentJob.value.createdAt = task.created_at
        if (task.updated_at) currentJob.value.updatedAt = task.updated_at
      }

      if (isTerminalStatus(task.status)) {
        // 终态再拉一次 unified job detail（获取最终 input_params 等）
        await refreshUnifiedJob(taskId)
        if (String(task.status).toUpperCase() === 'COMPLETED') {
          await ensureDownloadReady(taskId)
        }
        stopPolling()
        return
      }

      pollingTimer = setTimeout(poll, 5000)
    } catch (error) {
      console.error('轮询任务状态失败:', error)
      stopPolling()
    }
  }

  await poll()
}

const formData = reactive<FormData>({
  modelType: 'cnn',
  email: ''
})

// 文件上传引用
const testDataUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const modelUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const somModelUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const encoderUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const classifierUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const scalerUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const unSemiModelUploader = ref<InstanceType<typeof FileUploader> | null>(null)

// 文件路径
const testDataSetPath = ref<string | null>(null)
const modelPath = ref<string | null>(null)
const somModelPath = ref<string | null>(null)
const encoderPath = ref<string | null>(null)
const classifierPath = ref<string | null>(null)
const scalerPath = ref<string | null>(null)
const unSemiModelPath = ref<string | null>(null)

// 计算属性
const isFormValid = computed(() => {
  if (!formData.modelType) return false
  
  // 根据模型类型检查必需的文件
  if (formData.modelType === 'som') {
    return testDataSetPath.value && somModelPath.value
  } else if (formData.modelType === 'autoencoder') {
    return testDataSetPath.value && encoderPath.value && classifierPath.value
  } else if (['vae', 'deepcluster', 'ladder', 'pseudo'].includes(formData.modelType)) {
    return testDataSetPath.value && scalerPath.value && unSemiModelPath.value
  } else {
    return testDataSetPath.value && modelPath.value
  }
})

const showGenericModelUpload = computed(() => {
  return !['som', 'autoencoder', 'vae', 'deepcluster', 'ladder', 'pseudo'].includes(formData.modelType)
})

const showUnSemiModelUpload = computed(() => {
  return ['vae', 'deepcluster', 'ladder', 'pseudo'].includes(formData.modelType)
})

const showNoLabelNote = computed(() => {
  return ['vae', 'deepcluster'].includes(formData.modelType)
})

// 方法
const handleModelTypeChange = () => {
  // 清除之前的选择
  clearAllUploads()
}

const clearAllUploads = () => {
  if (testDataUploader.value) testDataUploader.value.clear()
  if (modelUploader.value) modelUploader.value.clear()
  if (somModelUploader.value) somModelUploader.value.clear()
  if (encoderUploader.value) encoderUploader.value.clear()
  if (classifierUploader.value) classifierUploader.value.clear()
  if (scalerUploader.value) scalerUploader.value.clear()
  if (unSemiModelUploader.value) unSemiModelUploader.value.clear()
  
  // 清除文件路径
  testDataSetPath.value = null
  modelPath.value = null
  somModelPath.value = null
  encoderPath.value = null
  classifierPath.value = null
  scalerPath.value = null
  unSemiModelPath.value = null
}

const handleTestDataSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  if (!file) return
  console.log('测试数据集已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'test_dataset')
  testDataSetPath.value = info.file_path
}

const handleModelSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  if (!file) return
  console.log('模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'model')
  modelPath.value = info.file_path
}

const handleSomModelSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  if (!file) return
  console.log('SOM模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'som_model')
  somModelPath.value = info.file_path
}

const handleEncoderSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  if (!file) return
  console.log('编码器模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'encoder')
  encoderPath.value = info.file_path
}

const handleClassifierSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  if (!file) return
  console.log('分类器模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'classifier')
  classifierPath.value = info.file_path
}

const handleScalerSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  if (!file) return
  console.log('Scaler文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'scaler')
  scalerPath.value = info.file_path
}

const handleUnSemiModelSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  if (!file) return
  console.log('无监督/半监督模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'un_semi_model')
  unSemiModelPath.value = info.file_path
}

const downloadTestDataExample = () => {
  // TODO: 实现测试数据示例下载
  // console.log('下载测试数据示例')
  try {
      const fileName = 'useModel_testing_Example.txt'
      // 直接从后端暴露的 example 目录下载（避免 Vite public/example 缺失导致返回 html）
      // const downloadUrl = `http://localhost:8005/example/${fileName}`
      const downloadUrl = '/example/useModel_testing_Example.txt'

      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = fileName
      link.target = '_blank' // 新窗口打开，避免阻塞当前页面
      link.style.display = 'none'

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
  } catch (error: any) {
      console.error('❓️ 示例文件下载失败:', error)
      ElMessage.error(`Download failed: ${error.message || 'Unknown error'}`)
  }
}

const downloadModelExample = () => {
  // TODO: 实现模型示例下载
  // console.log('下载模型示例')
  try {
      const fileName = 'useModel_cnn_Example.pth'
      // 直接从后端暴露的 example 目录下载（避免 Vite public/example 缺失导致返回 html）
      // const downloadUrl = `http://localhost:8005/example/${fileName}`
      const downloadUrl = '/example/useModel_cnn_Example.pth'
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = fileName
      link.target = '_blank' // 新窗口打开，避免阻塞当前页面
      link.style.display = 'none'

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
  } catch (error: any) {
      console.error('❓️ 示例文件下载失败:', error)
      ElMessage.error(`Download failed: ${error.message || 'Unknown error'}`)
  }
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    alert('Please upload all required files')
    return
  }

  try {
    isSubmitting.value = true

    // 由于 isFormValid 已经保证 test 数据已上传，这里做一次类型断言
    const testDataPath = testDataSetPath.value as string

    // 构造预测参数
    const predictParams = {
      model_type: formData.modelType,
      test_data_path: testDataPath,
      email: formData.email || undefined,
      ...(modelPath.value && { model_path: modelPath.value }),
      ...(somModelPath.value && { som_model_path: somModelPath.value }),
      ...(encoderPath.value && { encoder_path: encoderPath.value }),
      ...(classifierPath.value && { classifier_path: classifierPath.value }),
      ...(scalerPath.value && { scaler_path: scalerPath.value }),
      ...(unSemiModelPath.value && { un_semi_model_path: unSemiModelPath.value })
    }
    // 等待阶段参数展示兜底：先展示前端提交快照，后端 input_params 写入后再自动覆盖
    submittedInputParams.value = { ...predictParams }

    // 调用API进行模型预测
    const response = await modelUseApi.predict(predictParams)
    
    currentJob.value = {
      id: response.job_id,
      name: `model_use_${formData.modelType}_${Date.now()}`,
      status: response.status as Job['status'],
      progress: 0,
      createdAt: response.created_at,
      updatedAt: response.created_at,
      duration: 0,
      currentStep: 'Submitted, waiting to run'
    }
    unifiedJob.value = null

    console.log('模型预测任务已创建:', response)

    // 打开结果弹窗（与监督学习一致）
    showResultDialog.value = true
    downloadReady.value = false
    preparedDownloadUrl.value = null
    // 弹窗打开/提交后立即拉取 unified job detail（input_params 等）
    refreshUnifiedJob(response.job_id)
    pollTaskStatus(response.job_id)

  } catch (error) {
    console.error('创建模型预测任务失败:', error)
    alert('Failed to create prediction task. Please try again later.')
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  Object.assign(formData, {
    modelType: 'cnn',
    email: ''
  })

  clearAllUploads()
  currentJob.value = null
  unifiedJob.value = null
  submittedInputParams.value = null
  showResultDialog.value = false
}

const handleClose = () => {
  // 关闭并重置，保持与监督学习弹窗一致的交互
  showResultDialog.value = false
  stopPolling()
  resetForm()
}

const ensureDownloadReady = async (jobId: string) => {
  downloadReady.value = false
  preparedDownloadUrl.value = null

  const maxAttempts = 6
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  for (let i = 0; i < maxAttempts; i++) {
    try {
      const resp = await jobsApi.getDownloadUrl(jobId)
      preparedDownloadUrl.value = resp
      downloadReady.value = true
      return
    } catch (error: any) {
      const detail: string = error?.response?.data?.detail || ''
      const statusCode: number | undefined = error?.response?.status
      const retryableDetail =
        /任务尚未完成|结果文件不存在|not completed|not ready|does not exist|Result file/i.test(detail)
      const retryableCode = statusCode === 400 || statusCode === 404 || statusCode === 409
      const canRetry = retryableDetail || retryableCode || !detail
      if (!canRetry && i === 0) {
        console.warn('准备下载链接失败，将不再自动重试:', error)
        break
      }
      if (i === maxAttempts - 1) {
        console.warn('多次重试后仍未准备好下载链接:', error)
        break
      }
      await delay(2000)
    }
  }
}

const onDownload = async () => {
  const jobId = currentJob.value?.id
  if (!jobId) return
  try {
    if (!downloadReady.value || !preparedDownloadUrl.value) {
      ElMessage.info('Result file is still being prepared, please wait a moment…')
      await ensureDownloadReady(jobId)
    }
    if (!downloadReady.value || !preparedDownloadUrl.value) {
      ElMessage.error('Result file is not ready yet, please try again later')
      return
    }
    window.open(preparedDownloadUrl.value, '_blank')
    ElMessage.success('Download started…')
  } catch (error: any) {
    console.error('下载失败:', error)
    ElMessage.error(error?.response?.data?.detail || error?.message || 'Download failed')
  }
}

// 生命周期
onMounted(() => {
  console.log('模型使用页面已加载')
})

watch(
  () => showResultDialog.value,
  (open) => {
    if (open && currentJob.value?.id) {
      refreshUnifiedJob(currentJob.value.id)
    }
  }
)
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.automata-training-supervised {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.form-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: white;
  border-bottom: none;
  padding: 0.5rem 1.25rem;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.card {
  border-radius: 10px;
  border: 1px solid #e0e0e0;
}

.step-section {
  margin-bottom: 2rem;
}

.step-header {
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333333;
  margin-bottom: 1rem;
}

.section-subtitle {
  font-size: 14px;
  color: #6c757d;
  margin-left: 12px;
  font-weight: normal;
}

.form-label {
  font-weight: 500;
  color: #444444;
}

.btn-primary {
  background-color: #409eff;
  border-color: #409eff;
  color: #fff;
  font-size: 14px;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  /* transform: translateY(-1px); */
  /* box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3); */
}

.btn-primary:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
  color: #fff;
  font-size: 14px;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.btn-outline-secondary {
  border-color: #cccccc;
  color: #666666;
}

.btn-outline-secondary:hover {
  background-color: #f0f0f0;
  border-color: #999999;
  color: #333333;
}

.badge.bg-success {
  background-color: #409eff;
}

.form-control:hover{
  border-color: #aaaaaa;
}

.form-control:focus {
    border-color: #409eff;
    box-shadow: 0 0 0 0.1rem rgba(13, 110, 253, 0.25);
}

.form-control {
    border: 1px solid #cccccc;
    background-color: white;
    color: #606266;
    font-size: 14px;
}

.form-select:focus {
    border-color: #409eff;
    box-shadow: 0 0 0 0.1rem rgba(13, 110, 253, 0.25);
}

</style>