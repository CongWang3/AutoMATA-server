<template>
  <div class="model-train-supervised">
    <div class="container-fluid py-4">
      <!-- 页面标题 -->
      <div class="page-header mb-4">
        <h2 class="display-6 fw-semibold text-center mb-3">Train Your Supervised Model</h2>
        <nav class="breadcrumb-nav">
          <ol class="breadcrumb">
            <li class="breadcrumb-item">
              <router-link to="/">Home</router-link>
            </li>
            <li class="breadcrumb-item">
              <router-link to="/model">Model</router-link>
            </li>
            <li class="breadcrumb-item active">Supervised Training</li>
          </ol>
        </nav>
      </div>

      <!-- 训练表单卡片 -->
      <div class="row justify-content-center">
        <div class="col-12 col-lg-10">
          <div class="card border-0 shadow">
            <div class="card-header bg-primary text-white py-3">
              <h4 class="mb-0 text-center">模型训练配置</h4>
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
                      <label class="form-label">上传数据集</label>
                      <FileUploader
                        ref="datasetUploader"
                        :allowed-types="['txt', 'csv']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleDatasetSelected"
                      />
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
                          :allowed-types="['txt', 'csv']"
                          :max-size="50 * 1024 * 1024"
                          @file-selected="handleTrainSelected"
                        />
                      </div>
                      <div class="col-md-4 mb-3">
                        <label class="form-label">验证集</label>
                        <FileUploader
                          ref="validationUploader"
                          :allowed-types="['txt', 'csv']"
                          :max-size="50 * 1024 * 1024"
                          @file-selected="handleValidationSelected"
                        />
                      </div>
                      <div class="col-md-4 mb-3">
                        <label class="form-label">测试集</label>
                        <FileUploader
                          ref="testUploader"
                          :allowed-types="['txt', 'csv']"
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
                        :allowed-types="['txt', 'csv']"
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
                  </div>
                </div>

                <!-- 第三步：模型选择 -->
                <div class="step-section mb-4">
                  <h5 class="step-title">
                    <span class="step-number">3</span>
                    选择模型
                  </h5>

                  <div class="row">
                    <div class="col-md-4 mb-3">
                      <div class="model-option card h-100">
                        <div class="card-body text-center">
                          <iconify-icon 
                            class="model-icon fs-1 text-primary mb-2" 
                            icon="mdi:brain"
                          ></iconify-icon>
                          <h6>MLP</h6>
                          <p class="small text-muted">多层感知机</p>
                          <div class="form-check">
                            <input 
                              class="form-check-input" 
                              type="radio" 
                              id="mlpModel" 
                              value="mlp" 
                              v-model="formData.modelType"
                            >
                            <label class="form-check-label" for="mlpModel">
                              选择
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-md-4 mb-3">
                      <div class="model-option card h-100">
                        <div class="card-body text-center">
                          <iconify-icon 
                            class="model-icon fs-1 text-primary mb-2" 
                            icon="mdi:grid"
                          ></iconify-icon>
                          <h6>CNN</h6>
                          <p class="small text-muted">卷积神经网络</p>
                          <div class="form-check">
                            <input 
                              class="form-check-input" 
                              type="radio" 
                              id="cnnModel" 
                              value="cnn" 
                              v-model="formData.modelType"
                            >
                            <label class="form-check-label" for="cnnModel">
                              选择
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-md-4 mb-3">
                      <div class="model-option card h-100">
                        <div class="card-body text-center">
                          <iconify-icon 
                            class="model-icon fs-1 text-primary mb-2" 
                            icon="mdi:chart-timeline-variant"
                          ></iconify-icon>
                          <h6>LSTM</h6>
                          <p class="small text-muted">长短期记忆网络</p>
                          <div class="form-check">
                            <input 
                              class="form-check-input" 
                              type="radio" 
                              id="lstmModel" 
                              value="lstm" 
                              v-model="formData.modelType"
                            >
                            <label class="form-check-label" for="lstmModel">
                              选择
                            </label>
                          </div>
                        </div>
                      </div>
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
  modelType: string
  kfold?: number
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
  modelType: 'mlp',
  kfold: 5
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

const handleDatasetSelected = (files: File[]) => {
  console.log('数据集文件已选择:', files)
}

const handleTrainSelected = (files: File[]) => {
  console.log('训练集文件已选择:', files)
}

const handleValidationSelected = (files: File[]) => {
  console.log('验证集文件已选择:', files)
}

const handleTestSelected = (files: File[]) => {
  console.log('测试集文件已选择:', files)
}

const handleKfoldSelected = (files: File[]) => {
  console.log('K折数据集文件已选择:', files)
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  try {
    isSubmitting.value = true
    
    // 构造训练参数
    const trainingParams = {
      task_name: `supervised_${formData.modelType}_${Date.now()}`,
      model_type: formData.modelType,
      language: 'python',
      parameters: JSON.stringify({
        epochs: formData.epochs,
        learning_rate: formData.learningRate,
        batch_size: formData.batchSize,
        seed: formData.seed,
        early_stopping_patience: formData.earlyStopping,
        num_labels: formData.labels,
        strategy: formData.strategy,
        ...(formData.strategy === 'split' && {
          split_ratio: `${splitRatio.train}:${splitRatio.validation}:${splitRatio.test}`
        }),
        ...(formData.strategy === 'kfold' && {
          kfold: formData.kfold
        })
      })
    }

    // 调用API创建训练任务
    const response = await trainingApi.createTask(trainingParams)
    
    // 创建本地任务对象用于状态跟踪
    currentJob.value = {
      id: response.id,
      name: response.task_name,
      status: response.status,
      progress: 0,
      createdAt: response.created_at,
      updatedAt: response.updated_at,
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