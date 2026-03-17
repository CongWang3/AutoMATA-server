<template>
  <div class="model-train-supervised">
    <div class="container-fluid py-4">
      <!-- 训练表单卡片（风格对齐数据处理页面） -->
      <div class="row justify-content-center">
        <div class="col-12 col-lg-8">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white border-0 pt-3 pb-0 px-4 d-flex justify-content-between align-items-center">
              <h4 class="mb-0 fw-semibold">监督模型训练</h4>
              <span class="badge bg-success text-wrap">Train Your Supervised Model</span>
            </div>

            <div class="card-body p-4">
              <form @submit.prevent="handleSubmit" class="train-form">
                <!-- 第一步：选择策略并上传文件 -->
                <div class="step-section mb-4">
                  <h5 class="step-title">
                    <span class="step-number">1</span>
                    选择策略并上传文件
                  </h5>

                  <div class="strategy-options mb-4">
                    <div class="form-check mb-3">
                      <input 
                        class="form-check-input" 
                        type="radio" 
                        id="splitStrategy" 
                        value="split" 
                        v-model="formData.strategy"
                        @change="handleStrategyChange"
                      >
                      <label class="form-check-label" for="splitStrategy">
                        上传数据集进行训练/验证/测试分割
                      </label>
                    </div>

                    <div class="form-check mb-3">
                      <input 
                        class="form-check-input" 
                        type="radio" 
                        id="uploadStrategy" 
                        value="upload" 
                        v-model="formData.strategy"
                        @change="handleStrategyChange"
                      >
                      <label class="form-check-label" for="uploadStrategy">
                        分别上传训练/验证/测试数据集
                      </label>
                    </div>

                    <div class="form-check">
                      <input 
                        class="form-check-input" 
                        type="radio" 
                        id="kfoldStrategy" 
                        value="kfold" 
                        v-model="formData.strategy"
                        @change="handleStrategyChange"
                      >
                      <label class="form-check-label" for="kfoldStrategy">
                        上传数据集进行K折交叉验证
                      </label>
                    </div>
                  </div>

                  <!-- 数据集上传区域 -->
                  <div class="upload-section" v-show="formData.strategy === 'split'">
                    <div class="mb-3">
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <label class="form-label mb-0">上传数据集</label>
                        <button
                          type="button"
                          class="btn btn-sm btn-primary"
                          @click="downloadExample"
                        >
                          下载示例数据
                        </button>
                      </div>
                      <FileUploader
                        ref="datasetUploader"
                        :allowed-types="['txt', 'csv', 'tsv']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleDatasetSelected"
                      />
                      <!-- <el-form-item :label="fileLabel" prop="file">
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
                                  <span class="file-types">{{ fileTip }}</span>
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
                                <div class="tip-notes">
                                  <el-text v-if="exampleNote" type="warning" size="small" class="example-note">
                                    {{ exampleNote }}
                                  </el-text>
                                </div>
                              </div>
                            </template>
                          </el-upload>
                        </div>
                      </el-form-item> -->
                    </div>
                    
                    <div class="ratio-controls">
                      <label class="form-label">分割比例</label>
                      <div class="d-flex align-items-center">
                        <div class="ratio-item me-4">
                          <label class="ratio-label me-2">训练:</label>
                          <input 
                            type="number" 
                            class="form-control ratio-input text-center"
                            v-model="splitRatio.train" 
                            min="1" 
                            max="10" 
                            step="1"
                            @input="updateRatios"
                            style="width: 80px;"
                          >
                        </div>
                        <span class="ratio-separator me-4">-</span>
                        <div class="ratio-item me-4">
                          <label class="ratio-label me-2">验证:</label>
                          <input 
                            type="number" 
                            class="form-control ratio-input text-center"
                            v-model="splitRatio.validation" 
                            min="1" 
                            max="10" 
                            step="1"
                            @input="updateRatios"
                            style="width: 80px;"
                          >
                        </div>
                        <span class="ratio-separator me-4">-</span>
                        <div class="ratio-item">
                          <label class="ratio-label me-2">测试:</label>
                          <input 
                            type="number" 
                            class="form-control ratio-input text-center"
                            v-model="splitRatio.test" 
                            min="1" 
                            max="10" 
                            step="1" 
                            readonly
                            style="width: 80px; background-color: #e9ecef;"
                          >
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 分别上传区域 -->
                  <div class="upload-section" v-show="formData.strategy === 'upload'">
                    <div class="row">
                      <div class="col-md-4 mb-3">
                        <label class="form-label">训练集</label>
                        <FileUploader
                          ref="trainUploader"
                          :allowed-types="['txt', 'csv', 'tsv']"
                          :max-size="50 * 1024 * 1024"
                          @file-selected="handleTrainSelected"
                        />
                      </div>
                      <div class="col-md-4 mb-3">
                        <label class="form-label">验证集</label>
                        <FileUploader
                          ref="validationUploader"
                          :allowed-types="['txt', 'csv', 'tsv']"
                          :max-size="50 * 1024 * 1024"
                          @file-selected="handleValidationSelected"
                        />
                      </div>
                      <div class="col-md-4 mb-3">
                        <label class="form-label">测试集</label>
                        <FileUploader
                          ref="testUploader"
                          :allowed-types="['txt', 'csv', 'tsv']"
                          :max-size="50 * 1024 * 1024"
                          @file-selected="handleTestSelected"
                        />
                      </div>
                    </div>
                  </div>

                  <!-- K折交叉验证区域 -->
                  <div class="upload-section" v-show="formData.strategy === 'kfold'">
                    <div class="mb-3">
                      <label class="form-label">上传数据集</label>
                      <FileUploader
                        ref="kfoldUploader"
                        :allowed-types="['txt', 'csv', 'tsv']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleKfoldSelected"
                      />
                    </div>
                    <div class="mb-3">
                      <label class="form-label">K值</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        v-model="formData.kfold" 
                        min="2" 
                        max="10"
                        placeholder="请输入K折数 (2-10)"
                      >
                    </div>
                  </div>
                </div>

                <!-- 第二步：模型参数配置 -->
                <div class="step-section mb-4">
                  <h5 class="step-title">
                    <span class="step-number">2</span>
                    模型参数配置
                  </h5>

                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Epochs *</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        v-model="formData.epochs" 
                        min="1" 
                        required
                        placeholder="训练轮数"
                      >
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Learning Rate *</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        v-model="formData.learningRate" 
                        min="0.0001" 
                        max="1" 
                        step="0.0001"
                        required
                        placeholder="学习率"
                      >
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Random Seed *</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        v-model="formData.seed" 
                        min="1"
                        required
                        placeholder="随机种子"
                      >
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Early Stopping Patience *</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        v-model="formData.earlyStopping" 
                        min="1"
                        required
                        placeholder="早停耐心值"
                      >
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">标签数量 *</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        v-model="formData.labels" 
                        min="2"
                        required
                        placeholder="分类标签数"
                      >
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Batch Size</label>
                      <select class="form-select" v-model="formData.batchSize">
                        <option value="16">16</option>
                        <option value="32">32</option>
                        <option value="64">64</option>
                        <option value="128">128</option>
                      </select>
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Loss Function *</label>
                      <select class="form-select" v-model="formData.lossFunction" required>
                        <option value="crossentropy">CrossEntropyLoss</option>
                        <option value="focalloss">FocalLoss</option>
                        <option value="nllloss">NLLLoss</option>
                      </select>
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Optimizer *</label>
                      <select class="form-select" v-model="formData.optimizer" required>
                        <option value="adam">Adam</option>
                        <option value="sgd">SGD</option>
                        <option value="rmsprop">RMSprop</option>
                      </select>
                    </div>
                  </div>
                </div>

                <!-- 第三步：模型选择 -->
                <div class="step-section mb-4">
                  <h5 class="step-title">
                    <span class="step-number">3</span>
                    选择模型
                  </h5>

                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label class="form-label">模型类型 *</label>
                      <select 
                        class="form-select" 
                        v-model="formData.modelType" 
                        required
                      >
                        <option value="cnn">
                          CNN &gt; CNN Excels at extracting discriminative features from 1D signals with local patterns (e.g., mass spectrometry)
                        </option>
                        <option value="lstm">
                          LSTM &gt; Designed for modeling data with long-term dependencies
                        </option>
                        <option value="rnn">
                          RNN &gt; Used for processing simple sequences with short-term dependencies
                        </option>
                        <option value="mlp">
                          MLP &gt; A general-purpose benchmark model for non-linear classification of feature vectors without explicit structure
                        </option>
                        <option value="autoencoder">
                          AutoEncoder &gt; Generates better feature representations for classification tasks through dimensionality reduction and denoising
                        </option>
                        <option value="transformer">
                          Transformer &gt; Models the global context via the self-attention mechanism
                        </option>
                        <option value="rbfn">
                          RBFNN &gt; Suitable for fast learning and local approximation of small-scale tabular data
                        </option>
                        <option value="all">
                          All &gt; All the above models are trained in parallel using the same set of data
                        </option>
                      </select>
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">联系邮箱（可选）</label>
                      <input
                        type="email"
                        class="form-control"
                        v-model="formData.email"
                        placeholder="请输入邮箱地址（选填，用于接收训练结果通知）"
                      >
                    </div>
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
                    {{ isSubmitting ? '训练中...' : '开始训练' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- 任务状态面板 -->
      <div v-if="currentJob" class="row justify-content-center mt-4">
        <div class="col-12 col-lg-10">
          <JobStatus 
            :job="currentJob"
            @cancel="cancelJob"
            @retry="retryJob"
            @view-result="viewResult"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import FileUploader from '@/components/FileUpload/FileUploader.vue'
import JobStatus from '@/components/Job/JobStatus.vue'
import { trainingApi } from '@/api/training'

interface FormData {
  strategy: 'split' | 'upload' | 'kfold'
  epochs: number
  learningRate: number
  seed: number
  earlyStopping: number
  labels: number
  batchSize: number
  lossFunction: string
  optimizer: string
  modelType: string
  kfold?: number
  email?: string
}

interface Job {
  id: number
  name: string
  status: string
  progress: number
  createdAt: string
  updatedAt: string
  duration: number
}

// 响应式数据
const router = useRouter()
const isSubmitting = ref(false)
const currentJob = ref<Job | null>(null)

const formData = reactive<FormData>({
  strategy: 'split',
  epochs: 100,
  learningRate: 0.001,
  seed: 42,
  earlyStopping: 10,
  labels: 2,
  batchSize: 32,
  lossFunction: 'crossentropy',
  optimizer: 'adam',
  modelType: 'mlp',
  kfold: 5,
  email: ''
})

const splitRatio = reactive({
  train: 7,
  validation: 2,
  test: 1
})

// 文件上传引用
const datasetUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const trainUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const validationUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const testUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const kfoldUploader = ref<InstanceType<typeof FileUploader> | null>(null)

// 计算属性
const isFormValid = computed(() => {
  return formData.modelType && 
         formData.epochs > 0 && 
         formData.learningRate > 0 &&
         formData.seed > 0 &&
         formData.earlyStopping > 0 &&
         formData.labels >= 2
})

// 方法
const handleStrategyChange = () => {
  // 清除之前的选择
  if (datasetUploader.value) datasetUploader.value.clear()
  if (trainUploader.value) trainUploader.value.clear()
  if (validationUploader.value) validationUploader.value.clear()
  if (testUploader.value) testUploader.value.clear()
  if (kfoldUploader.value) kfoldUploader.value.clear()
}

const updateRatios = () => {
  // 确保比例总和为10
  const total = splitRatio.train + splitRatio.validation + splitRatio.test
  if (total !== 10) {
    splitRatio.test = 10 - splitRatio.train - splitRatio.validation
  }
}

// 已上传的数据集主路径（简化版：当前版本以一个主数据集为入口）
const datasetPath = ref<string | null>(null)

const handleDatasetSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('数据集文件已选择:', file.name)
  const info = await trainingApi.uploadFile(file, 'dataset')
  datasetPath.value = info.file_path
}

const handleTrainSelected = async (files: File[]) => {
  // TODO: 后续扩展为分别上传 train/val/test 三个数据集
  if (!files.length) return
  console.log('训练集文件已选择:', files[0].name)
}

const handleValidationSelected = async (files: File[]) => {
  if (!files.length) return
  console.log('验证集文件已选择:', files[0].name)
}

const handleTestSelected = async (files: File[]) => {
  if (!files.length) return
  console.log('测试集文件已选择:', files[0].name)
}

const handleKfoldSelected = async (files: File[]) => {
  if (!files.length) return
  console.log('K折数据集文件已选择:', files[0].name)
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  try {
    isSubmitting.value = true
    
    if (formData.strategy === 'split' && !datasetPath.value) {
      alert('请先上传数据集文件')
      return
    }

    // 构造训练参数（与后端 TrainingService 对应）
    const params = {
      strategy: formData.strategy,
      epochs: formData.epochs,
      learning_rate: formData.learningRate,
      batch_size: formData.batchSize,
      seed: formData.seed,
      early_stopping: formData.earlyStopping,
      labels: formData.labels,
      loss_function: formData.lossFunction,
      optimizer_function: formData.optimizer,
      ...(formData.strategy === 'split' && {
        ratio: `${splitRatio.train}:${splitRatio.validation}:${splitRatio.test}`
      }),
      ...(formData.strategy === 'kfold' && {
        kfold: formData.kfold
      })
    }

    const trainingParams = {
      task_name: `supervised_${formData.modelType}_${Date.now()}`,
      model_type: formData.modelType,
      parameters: params,
      dataset_path: datasetPath.value || undefined
    }

    // 调用API创建训练任务
    const response = await trainingApi.trainSupervised(trainingParams)
    
    currentJob.value = {
      id: response.job_id,
      name: response.task_name,
      status: response.status,
      progress: 0,
      createdAt: response.created_at,
      updatedAt: response.created_at,
      duration: 0
    }

    console.log('训练任务已创建:', response)

  } catch (error) {
    console.error('创建训练任务失败:', error)
    alert('创建训练任务失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  Object.assign(formData, {
    strategy: 'split',
    epochs: 100,
    learningRate: 0.001,
    seed: 42,
    earlyStopping: 10,
    labels: 2,
    batchSize: 32,
    modelType: 'mlp',
    kfold: 5
  })
  
  Object.assign(splitRatio, {
    train: 7,
    validation: 2,
    test: 1
  })

  datasetPath.value = null
  // 清除文件上传
  handleStrategyChange()
  
  currentJob.value = null
}

const cancelJob = (jobId: number) => {
  console.log('取消任务:', jobId)
  // 实现取消逻辑
}

const retryJob = (jobId: number) => {
  console.log('重试任务:', jobId)
  // 实现重试逻辑
}

const viewResult = (jobId: number) => {
  router.push(`/model/result/${jobId}`)
}

// 生命周期
onMounted(() => {
  console.log('监督学习训练页面已加载')
})
</script>

<style scoped>
.model-train-supervised {
  min-height: calc(100vh - 100px);
}

.page-header h2 {
  color: #2c3e50;
}

.breadcrumb {
  background: none;
  padding: 0;
  margin-bottom: 0;
}

.step-title {
  position: relative;
  padding-left: 40px;
  margin-bottom: 1rem;
  color: #2c3e50;
}

.step-number {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  background: #0d6efd;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: bold;
}

.strategy-options .form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.ratio-controls {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.ratio-input {
  display: inline-block;
}

.model-option {
  transition: all 0.3s ease;
  cursor: pointer;
}

.model-option:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.model-icon {
  transition: color 0.3s ease;
}

.model-option:hover .model-icon {
  color: #0d6efd;
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}
</style>