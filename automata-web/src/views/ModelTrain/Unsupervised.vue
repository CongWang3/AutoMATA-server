<template>
  <div class="automata-training-supervised">
    <div class="container-fluid p-4">
      <div class="row justify-content-center">
        <div class="col-12 col-lg-10">
          <el-card class="form-card">
            <template #header>
              <div class="card-header">
                <span class="title">Unsupervised learning model training</span>
                <el-tag type="info">Unsupervised Learning</el-tag>
              </div>
            </template>
            <div class="card-body p-4">
              <form @submit.prevent="handleSubmit" class="train_form" enctype="multipart/form-data">
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center">
                    <h5 class="section-title">
                      1. Select Strategy and Upload Data
                      <span class="section-subtitle">Required</span>
                    </h5>
                    <button type="button" class="btn btn-outline-primary btn-sm" @click="downloadStrategyExample">
                      <i class="fas fa-download me-1"></i>
                      Download Example Data
                    </button>
                  </div>
                  <div class="strategy-options mb-4 mt-3">
                    <div class="form-check mb-3">
                      <input class="form-check-input" type="radio" id="splitStrategy" value="split" v-model="strategy" @change="handleStrategyChange">
                      <label class="form-check-label" for="splitStrategy">
                        Upload a dataset to conduct train/validation/testing split
                      </label>
                    </div>
                    <div class="form-check mb-3">
                      <input class="form-check-input" type="radio" id="uploadStrategy" value="upload" v-model="strategy" @change="handleStrategyChange">
                      <label class="form-check-label" for="uploadStrategy">
                        Upload train/validation/testing datasets respectively
                      </label>
                    </div>
                    <div class="form-check">
                      <input class="form-check-input" type="radio" id="kfoldStrategy" value="kfold" v-model="strategy" @change="handleStrategyChange">
                      <label class="form-check-label" for="kfoldStrategy">
                        Upload a dataset to conduct K-Fold cross-validation
                      </label>
                    </div>
                  </div>

                  <div class="upload-section" v-if="strategy === 'split'">
                    <div class="mb-3">
                      <label class="form-label">Upload Dataset (Note: The uploaded dataset should not contain label or index columns)</label>
                      <input type="file" class="form-control" @change="handleFileUpload($event, 'dataset')" accept=".txt,.csv,.xlsx,.xls,.tsv" required>
                      <div v-if="uploadProgress.dataset > 0 && uploadProgress.dataset < 100" class="mt-2">
                        <div class="progress">
                          <div class="progress-bar" role="progressbar" :style="{ width: uploadProgress.dataset + '%' }">
                            {{ uploadProgress.dataset }}%
                          </div>
                        </div>
                      </div>
                      <div v-if="uploadedFiles.dataset" class="mt-2">
                        <span class="badge bg-success">
                          <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.dataset }}
                        </span>
                      </div>
                    </div>

                    <label class="form-label">Current Ratio</label>
                    <div class="ratio-controls d-flex align-items-center">
                      <div class="ratio-item d-flex align-items-center me-4">
                        <label class="ratio-label me-2">Train Set:</label>
                        <input type="number" class="form-control ratio-input text-center" v-model="splitRatio.train" min="1" max="10" step="1" @input="updateRatios" style="width: 180px;">
                      </div>
                      <span class="ratio-separator me-4">-</span>
                      <div class="ratio-item d-flex align-items-center me-4">
                        <label class="ratio-label me-2">Validation Set:</label>
                        <input type="number" class="form-control ratio-input text-center" v-model="splitRatio.validation" min="1" max="10" step="1" @input="updateRatios" style="width: 180px;">
                      </div>
                      <span class="ratio-separator me-4">-</span>
                      <div class="ratio-item d-flex align-items-center">
                        <label class="ratio-label me-2">Test Set:</label>
                        <input type="number" class="form-control ratio-input text-center" v-model="splitRatio.test" min="1" max="10" step="1" readonly style="width: 180px; background-color: #e9ecef;">
                      </div>
                    </div>
                  </div>

                  <div class="upload-section" v-if="strategy === 'upload'">
                    <div class="row g-3">
                      <label class="form-label">(Note: The uploaded dataset should not contain label or index columns)</label>
                      <div class="col-md-4">
                        
                        <label class="form-label">Upload Training Set</label>
                        <input type="file" class="form-control" @change="handleFileUpload($event, 'train')" accept=".txt,.csv,.xlsx,.xls,.tsv" required>
                        <div v-if="uploadProgress.train > 0 && uploadProgress.train < 100" class="mt-2">
                          <div class="progress">
                            <div class="progress-bar" role="progressbar" :style="{ width: uploadProgress.train + '%' }">{{ uploadProgress.train }}%</div>
                          </div>
                        </div>
                        <div v-if="uploadedFiles.train" class="mt-2">
                          <span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.train }}</span>
                        </div>
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Upload Validation Set</label>
                        <input type="file" class="form-control" @change="handleFileUpload($event, 'validation')" accept=".txt,.csv,.xlsx,.xls,.tsv" required>
                        <div v-if="uploadProgress.validation > 0 && uploadProgress.validation < 100" class="mt-2">
                          <div class="progress">
                            <div class="progress-bar" role="progressbar" :style="{ width: uploadProgress.validation + '%' }">{{ uploadProgress.validation }}%</div>
                          </div>
                        </div>
                        <div v-if="uploadedFiles.validation" class="mt-2">
                          <span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.validation }}</span>
                        </div>
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Upload Test Set</label>
                        <input type="file" class="form-control" @change="handleFileUpload($event, 'test')" accept=".txt,.csv,.xlsx,.xls,.tsv" required>
                        <div v-if="uploadProgress.test > 0 && uploadProgress.test < 100" class="mt-2">
                          <div class="progress">
                            <div class="progress-bar" role="progressbar" :style="{ width: uploadProgress.test + '%' }">{{ uploadProgress.test }}%</div>
                          </div>
                        </div>
                        <div v-if="uploadedFiles.test" class="mt-2">
                          <span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.test }}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="upload-section" v-if="strategy === 'kfold'">
                    <div class="mb-3">
                      <label class="form-label">Upload training set (Note: The uploaded dataset should not contain label or index columns)</label>
                      <input type="file" class="form-control" @change="handleFileUpload($event, 'kfoldDataset')" accept=".txt,.csv,.xlsx,.xls,.tsv" required>
                      <div v-if="uploadProgress.kfoldDataset > 0 && uploadProgress.kfoldDataset < 100" class="mt-2">
                        <div class="progress">
                          <div class="progress-bar" role="progressbar" :style="{ width: uploadProgress.kfoldDataset + '%' }">{{ uploadProgress.kfoldDataset }}%</div>
                        </div>
                      </div>
                      <div v-if="uploadedFiles.kfoldDataset" class="mt-2">
                        <span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.kfoldDataset }}</span>
                      </div>
                    </div>
                    <div class="mb-3">
                      <label class="form-label">K value</label>
                      <input type="number" class="form-control" v-model="kfoldValue" min="2" max="10" placeholder="3">
                    </div>
                    <div class="mb-3">
                      <label class="form-label">Upload testing set</label>
                      <input type="file" class="form-control" @change="handleFileUpload($event, 'kfoldTest')" accept=".txt,.csv,.xlsx,.xls,.tsv" required>
                      <div v-if="uploadProgress.kfoldTest > 0 && uploadProgress.kfoldTest < 100" class="mt-2">
                        <div class="progress">
                          <div class="progress-bar" role="progressbar" :style="{ width: uploadProgress.kfoldTest + '%' }">{{ uploadProgress.kfoldTest }}%</div>
                        </div>
                      </div>
                      <div v-if="uploadedFiles.kfoldTest" class="mt-2">
                        <span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.kfoldTest }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center">
                    <h5 class="section-title">
                      2. Choose Model
                      <span class="section-subtitle">Required</span>
                    </h5>
                  </div>
                  <div class="model-selection mt-3">
                    <div class="row">
                      <div class="col-md-6 mb-3" v-for="model in availableModels" :key="model.id">
                        <div class="model-card" :class="{ selected: selectedModel === model.id }" @click="selectModel(model.id)">
                          <div class="model-header">
                            <input class="form-check-input me-2" type="radio" :id="'model_' + model.id" :checked="selectedModel === model.id" @change="selectModel(model.id)">
                            <label class="form-check-label fw-bold" :for="'model_' + model.id">{{ model.name }}</label>
                          </div>
                          <div class="model-description mt-2">
                            <small class="text-muted">{{ model.description }}</small>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="step-section mb-4">
                  <h5 class="section-title">
                    3. Set Training Hyperparameters
                    <span class="section-subtitle">Required</span>
                  </h5>
                  <div class="hyperparameters-form">
                    <div class="row g-3">
                      <div class="col-md-4">
                        <label class="form-label">Epoch *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.epoch" min="1" max="1000" required>
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Learning Rate *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.learningRate" step="0.00001" min="0.00001" max="1" required>
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Early Stopping Patience *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.earlyStopping" min="1" required>
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Batch Size *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.batchSize" min="1" max="256">
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Random Seed *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.randomSeed" min="0" max="999999">
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Loss Function *</label>
                        <select class="form-select" v-model="hyperparameters.lossFunction">
                          <option v-for="item in currentLossFunctions" :key="item.value" :value="item.value">
                            {{ item.label }}
                          </option>
                        </select>
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Optimizer *</label>
                        <select class="form-select" v-model="hyperparameters.optimizerFunction">
                          <option v-for="item in unsupervisedOptimizers" :key="item.value" :value="item.value">
                            {{ item.label }}
                          </option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="notification-section mb-4">
                  <h5 class="section-title">
                    4. Notification
                    <span class="section-subtitle">Optional</span>
                  </h5>
                  <div class="row g-3">
                    <div class="col-12">
                      <input type="email" class="form-control" v-model="notification.email" placeholder="Please input your email address（Optional, for receiving training result notifications）">
                    </div>
                  </div>
                </div>

                <div class="submission-section">
                  <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-primary btn-lg" :disabled="isSubmitting || !isFormValid">
                      <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status"></span>
                      {{ isSubmitting ? '提交中...' : '开始训练' }}
                    </button>
                    <button type="button" class="btn btn-outline-secondary" @click="resetForm">重置表单</button>
                  </div>
                </div>
              </form>
            </div>
          </el-card>
        </div>
      </div>

      <el-dialog
        v-model="showResultDialog"
        width="80%"
        :close-on-click-modal="false"
        @close="handleClose"
      >
        <template #header>
          <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">无监督学习训练任务</h5>
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
          @cancel="handleCancel"
          @retry="handleRetry"
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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import JobStatus from '@/components/Job/JobStatus.vue'
import { trainingApi } from '@/api/training'
import { webSocketService } from '@/api/websocket'

interface UploadedFileInfo {
  id: string
  file_id: string
  file_path: string
}

interface UploadFilesState {
  dataset: string
  train: string
  validation: string
  test: string
  kfoldDataset: string
  kfoldTest: string
}

interface UploadProgressState {
  dataset: number
  train: number
  validation: number
  test: number
  kfoldDataset: number
  kfoldTest: number
}

interface UploadedFileInfoState {
  dataset: UploadedFileInfo | null
  train: UploadedFileInfo | null
  validation: UploadedFileInfo | null
  test: UploadedFileInfo | null
  kfoldDataset: UploadedFileInfo | null
  kfoldTest: UploadedFileInfo | null
}

type UploadKey = keyof UploadFilesState

const router = useRouter()
const strategy = ref('split')
const selectedModel = ref('vae')
const kfoldValue = ref(3)
const isSubmitting = ref(false)
const showResultDialog = ref(false)
const currentJob = ref<any>(null)

const availableModels = ref<Array<{ id: string; name: string; description: string }>>([
  { id: 'vae', name: 'VAE', description: 'Variational autoencoder for representation learning and reconstruction.' },
  { id: 'deepcluster', name: 'DeepCluster', description: 'Deep clustering for unsupervised feature learning.' }
])

const uploadedFiles = reactive<UploadFilesState>({
  dataset: '',
  train: '',
  validation: '',
  test: '',
  kfoldDataset: '',
  kfoldTest: ''
})

const uploadProgress = reactive<UploadProgressState>({
  dataset: 0,
  train: 0,
  validation: 0,
  test: 0,
  kfoldDataset: 0,
  kfoldTest: 0
})

const uploadedFileInfo = reactive<UploadedFileInfoState>({
  dataset: null,
  train: null,
  validation: null,
  test: null,
  kfoldDataset: null,
  kfoldTest: null
})
const uploadKeys: UploadKey[] = ['dataset', 'train', 'validation', 'test', 'kfoldDataset', 'kfoldTest']

const splitRatio = reactive({
  train: 8,
  validation: 1,
  test: 1
})

const hyperparameters = reactive({
  epoch: 20,
  learningRate: 0.001,
  earlyStopping: 10,
  batchSize: 32,
  randomSeed: 42,
  lossFunction: 'mse',
  optimizerFunction: 'adam'
})

const notification = reactive({
  email: ''
})
const pollingInterval = ref<ReturnType<typeof setTimeout> | null>(null)
const DEFAULT_LOSS_BY_MODEL: Record<string, string> = {
  vae: 'mse',
  deepcluster: 'deepcluster'
}

const vaeLossFunctions = [
  { value: 'mse', label: 'MSE (Mean Squared Error)' },
  { value: 'mae', label: 'MAE (Mean Absolute Error)' },
  { value: 'smooth_l1', label: 'Smooth L1 Loss' },
  { value: 'focal', label: 'Focal Loss' },
  { value: 'contrastive', label: 'Contrastive Loss' },
  { value: 'spectral', label: 'Spectral Loss' },
  { value: 'wasserstein', label: 'Wasserstein Loss' },
  { value: 'perceptual', label: 'Perceptual Loss' },
  { value: 'cosine', label: 'Cosine Loss' },
  { value: 'kl_div', label: 'KL Divergence' },
  { value: 'regularization', label: 'Regularization Loss' },
  { value: 'bce', label: 'Binary Cross Entropy' },
  { value: 'huber', label: 'Huber Loss' },
  { value: 'infonce', label: 'InfoNCE' }
]

const deepclusterLossFunctions = [
  { value: 'deepcluster', label: 'DeepCluster Loss' },
  { value: 'combined', label: 'Combined Loss' },
  { value: 'center', label: 'Center Loss' },
  { value: 'contrastive', label: 'Contrastive Loss' },
  { value: 'spectral', label: 'Spectral Clustering Loss' },
  { value: 'entropy', label: 'Entropy Loss' },
  { value: 'compactness', label: 'Compactness Loss' },
  { value: 'separation', label: 'Separation Loss' }
]

const unsupervisedOptimizers = [
  { value: 'adam', label: 'Adam' },
  { value: 'sgd', label: 'SGD' },
  { value: 'adamw', label: 'AdamW' }
]

const currentLossFunctions = computed(() => {
  return selectedModel.value === 'vae' ? vaeLossFunctions : deepclusterLossFunctions
})

watch(
  () => selectedModel.value,
  (model) => {
    const allowed = currentLossFunctions.value.map((i) => i.value)
    if (!allowed.includes(hyperparameters.lossFunction)) {
      hyperparameters.lossFunction = DEFAULT_LOSS_BY_MODEL[model] || allowed[0] || 'mse'
    }
  },
  { immediate: true }
)

const isFormValid = computed(() => {
  const baseValid = !!selectedModel.value && !!hyperparameters.epoch && !!hyperparameters.learningRate && !!hyperparameters.earlyStopping
  if (!baseValid) return false

  if (strategy.value === 'split') return !!uploadedFiles.dataset
  if (strategy.value === 'upload') return !!(uploadedFiles.train && uploadedFiles.validation && uploadedFiles.test)
  if (strategy.value === 'kfold') return !!(uploadedFiles.kfoldDataset && uploadedFiles.kfoldTest && kfoldValue.value >= 2)
  return false
})

const selectModel = (modelId: string) => {
  selectedModel.value = modelId
}

const updateRatios = () => {
  const total = splitRatio.train + splitRatio.validation
  if (total <= 10) {
    splitRatio.test = 10 - total
  } else {
    const ratioSum = splitRatio.train + splitRatio.validation
    splitRatio.train = Math.round((splitRatio.train / ratioSum) * 10)
    splitRatio.validation = 10 - splitRatio.train
    splitRatio.test = 0
  }
}

const handleFileUpload = async (event: Event, fileType: UploadKey) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const allowedExtensions = ['txt', 'csv', 'xlsx', 'xls', 'tsv']
  const fileExtension = file.name.split('.').pop()?.toLowerCase() || ''
  if (!allowedExtensions.includes(fileExtension)) {
    ElMessage.error('Please upload a txt, csv or excel file!')
    input.value = ''
    return
  }

  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error('File size cannot exceed 100MB')
    input.value = ''
    return
  }

  try {
    uploadProgress[fileType] = 0
    const fileInfo = await trainingApi.uploadFile(file, fileType, (progressEvent) => {
      if (progressEvent.total) {
        uploadProgress[fileType] = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })

    uploadedFileInfo[fileType] = {
      ...fileInfo,
      id: fileInfo.file_id
    }
    uploadedFiles[fileType] = file.name
    ElMessage.success(`文件 ${file.name} 上传成功`)
  } catch (error: any) {
    ElMessage.error('文件上传失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
    input.value = ''
  }
}

const handleStrategyChange = () => {
  uploadKeys.forEach((key) => {
    uploadedFiles[key] = ''
    uploadProgress[key] = 0
    uploadedFileInfo[key] = null
  })
}

const getDatasetPathWithFileIds = () => {
  if (strategy.value === 'split' && uploadedFileInfo.dataset) return `file://${uploadedFileInfo.dataset.id}`
  if (strategy.value === 'upload' && uploadedFileInfo.train) return `file://${uploadedFileInfo.train.id}`
  if (strategy.value === 'kfold' && uploadedFileInfo.kfoldDataset) return `file://${uploadedFileInfo.kfoldDataset.id}`
  return undefined
}

const checkInput = () => {
  const emailRegex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i
  if (notification.email && !emailRegex.test(notification.email)) {
    ElMessage.error('Please submit the correct email address（或留空）')
    return false
  }
  const allowed = currentLossFunctions.value.map((i) => i.value)
  if (!allowed.includes(hyperparameters.lossFunction)) {
    hyperparameters.lossFunction = DEFAULT_LOSS_BY_MODEL[selectedModel.value] || allowed[0] || 'mse'
  }
  return true
}

const stopPolling = () => {
  if (pollingInterval.value) {
    clearTimeout(pollingInterval.value)
    pollingInterval.value = null
  }
}

const pollTaskStatus = async (taskId: string) => {
  stopPolling()
  const poll = async () => {
    try {
      const task = await trainingApi.getStatus(taskId)
      if (currentJob.value && String(currentJob.value.id) === String(taskId)) {
        currentJob.value.status = task.status
        currentJob.value.progress = task.progress || 0
        currentJob.value.currentStep = task.current_step || currentJob.value.currentStep
        currentJob.value.resultFile = task.result_file || currentJob.value.resultFile
        currentJob.value.errorMessage = task.error_message || currentJob.value.errorMessage
      }
      if (task.status === 'Completed' || task.status === 'Failed' || task.status === 'Cancelled') {
        stopPolling()
        return
      }
      pollingInterval.value = setTimeout(poll, 5000)
    } catch {
      stopPolling()
    }
  }
  await poll()
}

const handleSubmit = async () => {
  isSubmitting.value = true
  try {
    if (!checkInput()){
      isSubmitting.value = false
      return
    } 

    const parameters: Record<string, any> = {
      strategy: strategy.value,
      epochs: hyperparameters.epoch,
      learning_rate: hyperparameters.learningRate,
      batch_size: hyperparameters.batchSize,
      seed: hyperparameters.randomSeed,
      early_stopping: hyperparameters.earlyStopping,
      loss_function: hyperparameters.lossFunction,
      optimizer: hyperparameters.optimizerFunction,
      optimizer_function: hyperparameters.optimizerFunction
    }

    if (strategy.value === 'split') {
      parameters.ratio = `${splitRatio.train}:${splitRatio.validation}:${splitRatio.test}`
    } else if (strategy.value === 'upload') {
      parameters.train_dataset_file_id = uploadedFileInfo.train?.id
      parameters.validation_dataset_file_id = uploadedFileInfo.validation?.id
      parameters.test_dataset_file_id = uploadedFileInfo.test?.id
    } else if (strategy.value === 'kfold') {
      parameters.kfold = kfoldValue.value
      parameters.kfold_train_dataset_file_id = uploadedFileInfo.kfoldDataset?.id
      parameters.kfold_test_dataset_file_id = uploadedFileInfo.kfoldTest?.id
    }

    const response = await trainingApi.trainUnsupervised({
      task_name: `Unsupervised_${selectedModel.value}_${Date.now()}`,
      model_type: selectedModel.value,
      parameters,
      dataset_path: getDatasetPathWithFileIds(),
      email: notification.email.trim() || undefined
    })

    currentJob.value = {
      id: response.job_id,
      name: response.task_name,
      status: response.status,
      progress: response.progress || 0,
      currentStep: response.current_step || '已提交，等待执行',
      createdAt: response.created_at,
      updatedAt: response.created_at,
      duration: 0,
      resultFile: response.result_file || undefined,
      errorMessage: response.error_message || undefined
    }
    showResultDialog.value = true
    ElMessage.success('训练任务已提交')
    await pollTaskStatus(response.job_id)
  } catch (error: any) {
    ElMessage.error('提交失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  strategy.value = 'split'
  selectedModel.value = 'vae'
  kfoldValue.value = 3
  uploadKeys.forEach((key) => {
    uploadedFiles[key] = ''
    uploadProgress[key] = 0
    uploadedFileInfo[key] = null
  })
  const fileInputs = document.querySelectorAll('input[type="file"]') as NodeListOf<HTMLInputElement>
  fileInputs.forEach((input) => {
    input.value = ''
  })
  splitRatio.train = 8
  splitRatio.validation = 1
  splitRatio.test = 1
  hyperparameters.epoch = 20
  hyperparameters.learningRate = 0.001
  hyperparameters.earlyStopping = 10
  hyperparameters.batchSize = 32
  hyperparameters.randomSeed = 42
  hyperparameters.lossFunction = 'mse'
  hyperparameters.optimizerFunction = 'adam'
}

const downloadStrategyExample = () => {
  try {
        const fileName = 'train_unsupervised_example.zip'
        // 直接从后端暴露的 example 目录下载（避免 Vite public/example 缺失导致返回 html）
        const downloadUrl = `http://localhost:8005/example/${fileName}`

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
        ElMessage.error(`下载失败: ${error.message || '未知错误'}`)
    }
}

const handleCancel = (jobId: number) => {
  console.log('取消任务:', jobId)
  ElMessage.info('任务取消功能暂未实现')
}

const handleRetry = (jobId: number) => {
  console.log('重试任务:', jobId)
  handleSubmit()
}

const viewResult = (jobId: number) => {
  console.log('查看结果:', jobId)
  ElMessage.info('请在弹窗中点击下载结果按钮')
}

const downloadResult = async () => {
  if (!currentJob.value?.resultFile) {
    ElMessage.warning('暂无结果文件')
    return
  }

  try {
    const result = await trainingApi.getDownloadUrl(currentJob.value.id)
    window.open(result.download_url, '_blank')
    ElMessage.success('开始下载...')
  } catch (error: any) {
    ElMessage.error('下载失败：' + (error.response?.data?.detail || error.message || '未知错误'))
  }
}

const handleClose = () => {
  showResultDialog.value = false
  currentJob.value = null
  stopPolling()
}

const handleTaskStatusUpdate = (data: any) => {
  if (!currentJob.value) return
  if (String(data.job_id) !== String(currentJob.value.id)) return
  if (data.status) currentJob.value.status = data.status
  if (data.progress !== undefined) currentJob.value.progress = data.progress
  if (data.current_step) currentJob.value.currentStep = data.current_step
  if (data.result_file) currentJob.value.resultFile = data.result_file
  if (data.error_message) currentJob.value.errorMessage = data.error_message
  if (data.updated_at) currentJob.value.updatedAt = data.updated_at
}

const connectWebSocket = async () => {
  try {
    await webSocketService.connectTaskStatus()
    webSocketService.setOnTaskStatus(handleTaskStatusUpdate)
  } catch (error) {
    console.error('无监督训练页面WebSocket连接失败:', error)
  }
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  stopPolling()
  webSocketService.setOnTaskStatus(() => {})
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: white;
  border-bottom: 1px solid #e4e7ed;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.step-section {
  margin-bottom: 2rem;
}

.section-subtitle {
  font-size: 14px;
  color: #6c757d;
  margin-left: 12px;
  font-weight: normal;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333333;
  margin-bottom: 1rem;
}

.model-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;
  background-color: #fafafa;
}

.model-card:hover {
  border-color: #0d6efd;
  box-shadow: 0 2px 8px rgba(13, 110, 253, 0.2);
}

.model-card.selected {
  border-color: #0d6efd;
  background-color: rgba(13, 110, 253, 0.1);
}

.model-header {
  display: flex;
  align-items: center;
}

.model-description {
  min-height: 60px;
  color: #666666;
}

.form-label {
  font-weight: 500;
  color: #444444;
}

.btn-primary {
  border-color: #0d6efd;
  color: white;
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
  font-size: 0.875rem;
}

.ratio-controls {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: center;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.ratio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 150px;
}

.ratio-label {
  font-weight: 500;
  color: #495057;
  white-space: nowrap;
  margin-bottom: 0;
}

.ratio-input {
  width: 80px;
  padding: 6px 10px;
  text-align: center;
  border-radius: 4px;
}

.ratio-input:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.upload-section {
  background-color: #f8f8f8;
  padding: 20px;
  border-radius: 8px;
  margin-top: 15px;
  border: 1px solid #eeeeee;
}

.form-control,
.form-select {
  border: 1px solid #cccccc;
  background-color: white;
}

.form-control:focus,
.form-select:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.form-control:hover,
.form-select:hover {
  border-color: #aaaaaa;
}

.step-header {
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.strategy-options .form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

@media (max-width: 768px) {
  .step-section {
    padding-left: 15px;
  }

  .model-card {
    margin-bottom: 15px;
  }

  .upload-section {
    padding: 15px;
  }
}
</style>
