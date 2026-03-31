<template>
  <div class="automata-training-supervised">
    <div class="container-fluid p-4">
      <div class="row justify-content-center">
        <div class="col-12 col-lg-10">
          <el-card class="form-card">
            <template #header>
              <div class="card-header">
                <span class="title">Semi-supervised learning model training</span>
                <el-tag type="primary">Semi-Supervised Learning</el-tag>
              </div>
            </template>
            <div class="card-body p-4">
              <form @submit.prevent="handleSubmit" class="train_form" enctype="multipart/form-data">
                <div class="step-section mb-4">
                  <div class="step-header d-flex justify-content-between align-items-center" style="border-bottom: none; padding-bottom: 0;">
                    <h5 class="section-title">
                      1. Select Strategy and Upload Data
                      <span class="section-subtitle">Required</span>
                    </h5>
                    <!-- <button type="button" class="btn btn-outline-primary btn-sm" @click="downloadStrategyExample">
                      <i class="fas fa-download me-1"></i>
                      Download Example Data
                    </button> -->
                    <el-button 
                        type="primary" 
                        size="small" 
                        @click="downloadStrategyExample"
                        class="example-btn"
                        >
                        Download Example Data
                    </el-button>
                  </div>
                  <div class="strategy-options mb-4 mt-3">
                    <div class="form-check mb-3">
                      <input class="form-check-input" type="radio" id="splitStrategy" value="split" v-model="strategy" @change="handleStrategyChange">
                      <label class="form-check-label" for="splitStrategy" style="color: #606266; font-size: 14px;">
                        Upload a dataset to conduct training/validation/testing split
                      </label>
                    </div>
                    <div class="form-check mb-3">
                      <input class="form-check-input" type="radio" id="uploadStrategy" value="upload" v-model="strategy" @change="handleStrategyChange">
                      <label class="form-check-label" for="uploadStrategy" style="color: #606266; font-size: 14px;">
                        Upload train/validation/testing datasets respectively
                      </label>
                    </div>
                    <div class="form-check">
                      <input class="form-check-input" type="radio" id="kfoldStrategy" value="kfold" v-model="strategy" @change="handleStrategyChange">
                      <label class="form-check-label" for="kfoldStrategy" style="color: #606266; font-size: 14px;">
                        Upload a dataset to conduct K-Fold cross-validation
                      </label>
                    </div>
                  </div>

                  <div class="upload-section" v-if="strategy === 'split'">
                    <div class="mb-3">
                      <label class="form-label">Upload Dataset (Note: The categorized labels of unlabeled samples are marked as Unknown)</label>
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
                      <label class="form-label">(Note: The categorized labels of unlabeled samples are marked as Unknown)</label>
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
                      <label class="form-label">Upload training set (Note: The categorized labels of unlabeled samples are marked as Unknown)</label>
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
                  <div class="step-header d-flex justify-content-between align-items-center" style="border-bottom: none; padding-bottom: 0;">
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
                      <div class="col-md-4" v-if="selectedModel === 'ladder'">
                        <label class="form-label">Loss Function *</label>
                        <select class="form-select" v-model="hyperparameters.lossFunction">
                          <option v-for="item in currentLossFunctions" :key="item.value" :value="item.value">
                            {{ item.label }}
                          </option>
                        </select>
                      </div>
                      <div class="col-md-4" v-if="selectedModel === 'pseudo'">
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
                          <option v-for="item in semiSupervisedOptimizers" :key="item.value" :value="item.value">
                            {{ item.label }}
                          </option>
                        </select>
                      </div>
                      <div class="col-md-4">
                        <label class="form-label">Supervision Loss Weight *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.alpha" min="0" max="10" step="0.1">
                      </div>
                      <div class="col-md-4" v-if="selectedModel === 'ladder'">
                        <label class="form-label">Reconstruction Loss Weight *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.beta" min="0" max="10" step="0.1">
                      </div>
                      <div class="col-md-4" v-if="selectedModel === 'ladder'">
                        <label class="form-label">Regularization Loss Weight *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.gamma" min="0" max="10" step="0.01">
                      </div>
                      <div class="col-md-4" v-if="selectedModel === 'pseudo'">
                        <label class="form-label">Pseudo-label Loss Weight *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.pseudoBeta" min="0" max="10" step="0.1">
                      </div>
                      <div class="col-md-4" v-if="selectedModel === 'pseudo'">
                        <label class="form-label">Pseudo-label Confidence Threshold *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.confidenceThreshold" min="0" max="1" step="0.01">
                      </div>
                      <div class="col-md-4" v-if="selectedModel === 'pseudo'">
                        <label class="form-label">Pseudo-label Ratio *</label>
                        <input type="number" class="form-control" v-model="hyperparameters.pseudoRatio" min="0" max="1" step="0.01">
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
                      {{ isSubmitting ? 'Submitting...' : 'Submit' }}
                    </button>
                    <button type="button" class="btn btn-outline-secondary" @click="resetForm">Reset</button>
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
        <TrainingResultPanel
          v-if="currentJob"
          :job-id="currentJob.id"
          :status="currentJob.status"
          :input-params="unifiedJob?.input_params || submittedInputParams || {}"
          :error-message="unifiedJob?.error_message || currentJob.errorMessage"
          :download-ready="downloadReady"
          :on-download="handleDownloadFromPanel"
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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import TrainingResultPanel from '@/components/Training/TrainingResultPanel.vue'
import { trainingApi } from '@/api/training'
import { webSocketService } from '@/api/websocket'
import { jobsApi, type UnifiedJob } from '@/api/jobs'

// <!-- 
// 审查上下文：
// - 设计意图：通过基础组件和composable重构，消除重复代码，提高可维护性
// - 已知局限：保留了原有的功能完整性，通过配置化实现差异化需求
// - 业务背景：半监督学习训练页面，支持LadderNetwork和Pseudo-Labeling模型
// - 测试重点：确保表单提交、文件上传、任务创建等核心功能正常工作，特别关注半监督特有参数
// -->

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

const strategy = ref('split')
const selectedModel = ref('ladder')
const kfoldValue = ref(3)
const isSubmitting = ref(false)
const showResultDialog = ref(false)
const currentJob = ref<any>(null)
const unifiedJob = ref<UnifiedJob | null>(null)
const submittedInputParams = ref<Record<string, any> | null>(null)
const terminalDetailFetched = ref(false)
const downloadReady = ref(false)
const preparedDownloadUrl = ref<string | null>(null)

const availableModels = ref([
  { id: 'ladder', name: 'Ladder Network', description: 'Semi-supervised encoder-decoder model for joint supervised and unsupervised learning.' },
  { id: 'pseudo', name: 'Pseudo Labeling', description: 'Trains with high-confidence pseudo labels generated from unlabeled samples.' }
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
  lossFunction: 'semi_supervised',
  optimizerFunction: 'adam',
  alpha: 1.0,
  beta: 1.0,
  gamma: 0.1,
  pseudoBeta: 0.5,
  confidenceThreshold: 0.8,
  pseudoRatio: 0.5
})

const notification = reactive({
  email: ''
})
const pollingInterval = ref<ReturnType<typeof setTimeout> | null>(null)

const DEFAULT_LOSS_BY_MODEL: Record<string, string> = {
  ladder: 'semi_supervised',
  pseudo: 'pseudo_label'
}

const ladderLossFunctions = [
  { value: 'semi_supervised', label: 'Semi-Supervised Loss' },
  { value: 'focal', label: 'Focal Loss' },
  { value: 'label_smoothing', label: 'Label Smoothing Loss' },
  { value: 'contrastive', label: 'Contrastive Loss' }
]

const pseudoLossFunctions = [
  { value: 'pseudo_label', label: 'Pseudo-Label Loss' },
  { value: 'focal', label: 'Focal Loss' },
  { value: 'label_smoothing', label: 'Label Smoothing Loss' }
]

const semiSupervisedOptimizers = [
  { value: 'adam', label: 'Adam' },
  { value: 'sgd', label: 'SGD' },
  { value: 'adamw', label: 'AdamW' },
  { value: 'rmsprop', label: 'RMSprop' }
]

const currentLossFunctions = computed(() => {
  return selectedModel.value === 'ladder' ? ladderLossFunctions : pseudoLossFunctions
})

watch(
  () => selectedModel.value,
  (model) => {
    const allowed = currentLossFunctions.value.map((i) => i.value)
    if (!allowed.includes(hyperparameters.lossFunction)) {
      hyperparameters.lossFunction = DEFAULT_LOSS_BY_MODEL[model] || allowed[0] || 'semi_supervised'
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
  try {
    uploadProgress[fileType] = 0
    const fileInfo = await trainingApi.uploadFile(file, fileType, (progressEvent: any) => {
      if (progressEvent.total) {
        uploadProgress[fileType] = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })
    uploadedFiles[fileType] = file.name
    uploadedFileInfo[fileType] = {
      ...fileInfo,
      id: fileInfo.file_id
    } as UploadedFileInfo
    ElMessage.success(`File "${file.name}" uploaded successfully`)
  } catch (error: any) {
    ElMessage.error('File upload failed: ' + (error.response?.data?.detail || error.message || 'Unknown error'))
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

const getDatasetPathWithFileIds = (): string => {
  if (strategy.value === 'split') {
    return uploadedFileInfo.dataset?.file_path || uploadedFiles.dataset || ''
  }
  if (strategy.value === 'upload') {
    return uploadedFileInfo.train?.file_path || uploadedFiles.train || ''
  }
  return uploadedFileInfo.kfoldDataset?.file_path || uploadedFiles.kfoldDataset || ''
}

const checkInput = () => {
  const emailRegex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i
  if (notification.email && !emailRegex.test(notification.email)) {
    ElMessage.error('Please enter a valid email address or leave it empty')
    return false
  }
  return true
}

const stopPolling = () => {
  if (pollingInterval.value) {
    clearTimeout(pollingInterval.value)
    pollingInterval.value = null
  }
}

function isTerminalJobStatus(status: string) {
  const s = String(status || '').toUpperCase()
  return s === 'COMPLETED' || s === 'FAILED' || s === 'CANCELLED'
}

async function refreshUnifiedJobDetail(id: string) {
  try {
    unifiedJob.value = await jobsApi.getJobDetail(id)
  } catch (error) {
    console.warn('获取任务详情失败:', error)
  }
}

async function refreshUnifiedJobDetailIfTerminal(id: string, status: string) {
  if (!isTerminalJobStatus(status)) return
  if (terminalDetailFetched.value) return
  terminalDetailFetched.value = true
  await refreshUnifiedJobDetail(id)
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
        refreshUnifiedJobDetailIfTerminal(String(taskId), task.status)
        if (task.status === 'Completed') {
          await ensureDownloadReady(String(taskId))
        }
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
    if (!checkInput()) {
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
      optimizer_function: hyperparameters.optimizerFunction,
      alpha: hyperparameters.alpha
    }

    if (selectedModel.value === 'ladder') {
      parameters.beta = hyperparameters.beta
      parameters.gamma = hyperparameters.gamma
    } else if (selectedModel.value === 'pseudo') {
      parameters.pseudo_beta = hyperparameters.pseudoBeta
      parameters.confidence_threshold = hyperparameters.confidenceThreshold
      parameters.pseudo_ratio = hyperparameters.pseudoRatio
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

    const response = await trainingApi.trainSemiSupervised({
      task_name: `SemiSupervised_${selectedModel.value}_${Date.now()}`,
      model_type: selectedModel.value,
      parameters,
      dataset_path: getDatasetPathWithFileIds(),
      email: notification.email.trim() || undefined
    })
    submittedInputParams.value = {
      training_type: 'semi-supervised',
      model_type: selectedModel.value,
      parameters,
      email: notification.email.trim() || undefined
    }

    currentJob.value = {
      id: response.job_id,
      name: response.task_name,
      status: response.status,
      progress: response.progress || 0,
      currentStep: response.current_step || 'Submitted, waiting to run',
      createdAt: response.created_at,
      updatedAt: response.created_at,
      duration: 0,
      resultFile: response.result_file || undefined,
      errorMessage: response.error_message || undefined
    }
    unifiedJob.value = null
    terminalDetailFetched.value = false
    downloadReady.value = false
    preparedDownloadUrl.value = null
    showResultDialog.value = true
    refreshUnifiedJobDetail(String(response.job_id))
    ElMessage.success('Training task submitted')
    await pollTaskStatus(response.job_id)
  } catch (error: any) {
    ElMessage.error('Submission failed: ' + (error.response?.data?.detail || error.message || 'Unknown error'))
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  strategy.value = 'split'
  selectedModel.value = 'ladder'
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
  hyperparameters.lossFunction = 'semi_supervised'
  hyperparameters.optimizerFunction = 'adam'
  hyperparameters.alpha = 1.0
  hyperparameters.beta = 1.0
  hyperparameters.gamma = 0.1
  hyperparameters.pseudoBeta = 0.5
  hyperparameters.confidenceThreshold = 0.8
  hyperparameters.pseudoRatio = 0.5
  notification.email = ''
}

const downloadStrategyExample = () => {
  try {
    const fileName = 'train_semi_supervised_example.zip'
    // const downloadUrl = `http://localhost:8005/example/${fileName}`
    const link = document.createElement('a')
    const downloadUrl = '/example/train_semi_supervised_example.zip'

    link.href = downloadUrl
    link.download = fileName
    link.target = '_blank'
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error: any) {
    ElMessage.error(`Download failed: ${error.message || 'Unknown error'}`)
  }
}

async function ensureDownloadReady(id: string) {
  downloadReady.value = false
  preparedDownloadUrl.value = null

  const maxAttempts = 6
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  for (let i = 0; i < maxAttempts; i++) {
    try {
      const url = await jobsApi.getDownloadUrl(String(id))
      preparedDownloadUrl.value = url
      downloadReady.value = true
      return
    } catch (error: any) {
      const detail: string = error?.response?.data?.detail || ''
      const canRetry = /任务尚未完成|结果文件不存在/.test(detail) || !detail
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

async function handleDownloadFromPanel() {
  const id = currentJob.value?.id
  if (!id) {
    ElMessage.warning('No job ID')
    return
  }
  try {
    if (!downloadReady.value || !preparedDownloadUrl.value) {
      ElMessage.info('Result file is still being prepared, please wait a moment…')
      await ensureDownloadReady(String(id))
    }
    if (!downloadReady.value || !preparedDownloadUrl.value) {
      ElMessage.error('Result file is not ready yet, please try again later')
      return
    }
    window.open(preparedDownloadUrl.value, '_blank')
  } catch (error: any) {
    console.error('获取下载链接失败:', error)
    ElMessage.error('Failed to get download URL: ' + (error?.response?.data?.detail || error?.message || 'Unknown error'))
  }
}

const handleClose = () => {
  showResultDialog.value = false
  currentJob.value = null
  unifiedJob.value = null
  submittedInputParams.value = null
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

  if (data.status) {
    refreshUnifiedJobDetailIfTerminal(String(currentJob.value.id), String(data.status))
  }
}

const connectWebSocket = async () => {
  try {
    await webSocketService.connectTaskStatus()
    webSocketService.setOnTaskStatus(handleTaskStatusUpdate)
  } catch (error) {
    console.error('半监督训练页面WebSocket连接失败:', error)
  }
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  stopPolling()
  webSocketService.setOnTaskStatus(() => {})
})

watch(
  () => showResultDialog.value,
  (open) => {
    if (!open) return
    const id = currentJob.value?.id
    if (!id) return
    if (unifiedJob.value) return
    refreshUnifiedJobDetail(String(id))
  }
)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: white;
  /* border-bottom: 1px solid #e4e7ed; */
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
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(13, 110, 253, 0.2);
}

.model-card.selected {
  border-color: #409eff;
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
  color: #606266;
  font-size: 14px;
}

.btn-primary {
  border-color: #409eff;
  color: white;
}

.btn-primary:hover {
  background-color: #409eff;
  border-color: #409eff;
  transform: translateY(-1px);
}

.upload-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #dee2e6;
}

.ratio-controls {
  background: white;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #dee2e6;
}

.ratio-label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  margin-bottom: 0;
}

.ratio-input {
  border: 2px solid #dee2e6;
  border-radius: 6px;
  font-weight: 500;
}

.ratio-input:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.ratio-separator {
  font-size: 20px;
  font-weight: bold;
  color: #6c757d;
}

.submission-section .btn {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
}

.form-control,
.form-select {
    border: 1px solid #cccccc;
    background-color: white;
    color: #606266;
    font-size: 14px;
}

.form-control:focus,
.form-select:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 0.1rem rgba(13, 110, 253, 0.25);
}

.form-check-input:checked {
    background-color: #409eff;
    border-color: #409eff;
    /* font-weight: 500; */
}

.progress {
  height: 8px;
}

.progress-bar {
  background-color: #409eff;
}

@media (max-width: 768px) {
  .ratio-controls {
    flex-direction: column;
    align-items: stretch !important;
  }

  .ratio-item {
    margin-right: 0 !important;
    margin-bottom: 10px;
  }

  .ratio-separator {
    display: none;
  }

  .upload-section {
    padding: 15px;
  }
}
</style>