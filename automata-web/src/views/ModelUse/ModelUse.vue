<template>
  <div class="automata-training-supervised">
    <div class="container-fluid p-4">
      <!-- 模型使用表单卡片 -->
      <div class="row justify-content-center">
        <div class="col-12 col-lg-8">
          <el-card class="form-card">
            <template #header>
              <div class="card-header">
                <span class="title">模型应用（Model Use）</span>
                <el-tag type="success">Model Use</el-tag>
              </div>
            </template>
            <div class="card-body p-4">
              <form @submit.prevent="handleSubmit" class="use-form">
                <!-- 第一步：选择模型类型 -->
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center">
                    <h5 class="section-title">
                      1. 选择模型类型
                      <span class="section-subtitle">Required</span>
                    </h5>
                  </div>

                  <div class="mb-3">
                    <label class="form-label">模型类型 *</label>
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
                  <div class="step-header d-flex justify-content-between align-items-center">
                    <h5 class="section-title">
                      2. 上传测试数据
                      <span class="section-subtitle">Required</span>
                    </h5>
                  </div>

                  <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <label class="form-label mb-0">测试数据集</label>
                      <button
                        type="button"
                        class="btn btn-sm btn-primary"
                        @click="downloadTestDataExample"
                      >
                        下载示例数据
                      </button>
                    </div>
                    <FileUploader
                      ref="testDataUploader"
                      :allowed-types="['txt', 'csv', 'tsv']"
                      :max-size="50 * 1024 * 1024"
                      @file-selected="handleTestDataSelected"
                    />
                    <div class="form-text" v-if="showNoLabelNote">
                      注意：无监督模型的测试数据集不需要标签和样本名
                    </div>
                  </div>
                </div>

                <!-- 第三步：上传模型文件 -->
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center">
                    <h5 class="section-title">
                      3. 上传模型文件
                      <span class="section-subtitle">Required</span>
                    </h5>
                  </div>

                  <!-- 通用模型文件上传 -->
                  <div class="mb-3" v-show="showGenericModelUpload">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <label class="form-label mb-0">模型文件</label>
                      <button
                        type="button"
                        class="btn btn-sm btn-primary"
                        @click="downloadModelExample"
                      >
                        下载示例模型
                      </button>
                    </div>
                    <FileUploader
                      ref="modelUploader"
                      :allowed-types="['pth', 'pt', 'pkl']"
                      :max-size="100 * 1024 * 1024"
                      @file-selected="handleModelSelected"
                    />
                  </div>

                  <!-- SOM 特有文件上传 -->
                  <div v-show="formData.modelType === 'som'">
                    <div class="mb-3">
                      <label class="form-label">模型文件</label>
                      <FileUploader
                        ref="somModelUploader"
                        :allowed-types="['pth', 'pt']"
                        :max-size="100 * 1024 * 1024"
                        @file-selected="handleSomModelSelected"
                      />
                    </div>
                  </div>

                  <!-- AutoEncoder 特有文件上传 -->
                  <div v-show="formData.modelType === 'autoencoder'">
                    <div class="mb-3">
                      <label class="form-label">编码器模型文件</label>
                      <FileUploader
                        ref="encoderUploader"
                        :allowed-types="['pth', 'pt']"
                        :max-size="100 * 1024 * 1024"
                        @file-selected="handleEncoderSelected"
                      />
                    </div>
                    <div class="mb-3">
                      <label class="form-label">分类器模型文件</label>
                      <FileUploader
                        ref="classifierUploader"
                        :allowed-types="['pth', 'pt']"
                        :max-size="100 * 1024 * 1024"
                        @file-selected="handleClassifierSelected"
                      />
                    </div>
                  </div>

                  <!-- 无监督/半监督模型特有文件上传 -->
                  <div v-show="showUnSemiModelUpload">
                    <div class="mb-3">
                      <label class="form-label">Scaler 文件</label>
                      <FileUploader
                        ref="scalerUploader"
                        :allowed-types="['pkl']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleScalerSelected"
                      />
                    </div>
                    <div class="mb-3">
                      <label class="form-label">模型文件</label>
                      <FileUploader
                        ref="unSemiModelUploader"
                        :allowed-types="['pth', 'pt']"
                        :max-size="100 * 1024 * 1024"
                        @file-selected="handleUnSemiModelSelected"
                      />
                    </div>
                  </div>
                </div>

                <!-- 第四步：联系方式 -->
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center">
                    <h5 class="section-title">
                      4. 联系方式
                      <span class="section-subtitle">Optional</span>
                    </h5>
                  </div>

                  <div class="mb-3">
                    <label class="form-label">邮箱地址（可选）</label>
                    <input
                      type="email"
                      class="form-control"
                      v-model="formData.email"
                      placeholder="请输入邮箱地址（选填，用于接收预测结果）"
                    >
                    <div class="form-text">我们将通过邮件发送预测结果给您</div>
                  </div>
                </div>

                <!-- 提交按钮 -->
                <div class="d-flex justify-content-center gap-3 mt-4">
                  <button 
                    type="button" 
                    class="btn btn-secondary px-4"
                    @click="resetForm"
                  >
                    重置
                  </button>
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
                    {{ isSubmitting ? '预测中...' : '开始预测' }}
                  </button>
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
        <template #header>
          <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">模型应用任务</h5>
            <div>
              <el-tag type="info" class="me-2">{{ currentJob?.status || '等待中' }}</el-tag>
              <el-button
                v-if="currentJob?.resultFile"
                type="success"
                size="small"
                @click="downloadResult"
              >
                <i class="fas fa-download me-1"></i>
                下载结果
              </el-button>
            </div>
          </div>
        </template>

        <JobStatus
          v-if="currentJob"
          :job="currentJob"
          @cancel="cancelJob"
          @retry="retryJob"
          @view-result="viewResult"
        />

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="handleClose">关闭并提交新任务</el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import FileUploader from '@/components/FileUpload/FileUploader.vue'
import JobStatus from '@/components/Job/JobStatus.vue'
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
const router = useRouter()
const isSubmitting = ref(false)
const currentJob = ref<Job | null>(null)
const showResultDialog = ref(false)
let pollingTimer: ReturnType<typeof setTimeout> | null = null

const stopPolling = () => {
  if (pollingTimer) {
    clearTimeout(pollingTimer)
    pollingTimer = null
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

      if (['Completed', 'Failed', 'Cancelled'].includes(task.status)) {
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
  console.log('下载测试数据示例')
}

const downloadModelExample = () => {
  // TODO: 实现模型示例下载
  console.log('下载模型示例')
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    alert('请确保已上传所有必需的文件')
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
      currentStep: '已提交，等待执行'
    }

    console.log('模型预测任务已创建:', response)

    // 打开结果弹窗（与监督学习一致）
    showResultDialog.value = true
    pollTaskStatus(response.job_id)

  } catch (error) {
    console.error('创建模型预测任务失败:', error)
    alert('创建预测任务失败，请稍后重试')
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
  showResultDialog.value = false
}

const handleClose = () => {
  // 关闭并重置，保持与监督学习弹窗一致的交互
  showResultDialog.value = false
  stopPolling()
  resetForm()
}

const cancelJob = async (jobId: number | string) => {
  try {
    const id = String(jobId)
    await jobsApi.cancelJob(id)
    const task = await jobsApi.getJobDetail(id)
    if (currentJob.value && currentJob.value.id === id) {
      currentJob.value.status = task.status as Job['status']
      currentJob.value.progress = task.progress || 0
      currentJob.value.currentStep = task.current_step
      currentJob.value.errorMessage = task.error_message
      currentJob.value.updatedAt = task.updated_at || currentJob.value.updatedAt
    }
    stopPolling()
  } catch (error) {
    console.error('取消任务失败:', error)
  }
}

const retryJob = async (_jobId: number | string) => {
  // 这里直接复用当前表单已上传的文件，重新发起一个新的预测任务
  await handleSubmit()
}

const viewResult = (jobId: number | string) => {
  stopPolling()
  console.log('查看结果:', jobId)
  ElMessage.info('请在弹窗中点击下载结果按钮')
}

const downloadResult = async () => {
  if (!currentJob.value?.resultFile) {
    ElMessage.warning('暂无结果文件')
    return
  }
  try {
    const jobId = currentJob.value.id
    const downloadUrl = await jobsApi.getDownloadUrl(jobId)
    window.open(downloadUrl, '_blank')
    ElMessage.success('开始下载...')
  } catch (error: any) {
    console.error('下载失败:', error)
    ElMessage.error(error?.response?.data?.detail || error?.message || '下载失败')
  }
}

// 生命周期
onMounted(() => {
  console.log('模型使用页面已加载')
})
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

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0b5ed7;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
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
  background-color: #0d6efd;
}
</style>