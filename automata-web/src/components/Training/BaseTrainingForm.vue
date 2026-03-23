<template>
  <div class="base-training-form">
    <form @submit.prevent="onSubmit" class="train_form" enctype="multipart/form-data">
      <!-- 第一步：选择策略并上传文件 -->
      <div class="step-section mb-4">
        <div class="step-header d-flex justify-content-between align-items-center">
          <h5 class="step-title mb-0">
            <span class="step-number">1</span>
            选择策略并上传数据
          </h5>
          <button type="button" class="btn btn-outline-primary btn-sm" @click="downloadExample">
            <i class="fas fa-download me-1"></i>
            下载示例数据
          </button>
        </div>
        
        <div class="strategy-options mb-4 mt-3">
          <div class="form-check mb-3">
            <input 
              class="form-check-input" 
              type="radio" 
              id="splitStrategy" 
              value="split" 
              v-model="localFormData.strategy"
              @change="handleStrategyChange"
              checked
            >
            <label class="form-check-label" for="splitStrategy">
              Upload a dataset to conduct train/validation/testing split
            </label>
          </div>

          <div class="form-check mb-3">
            <input 
              class="form-check-input" 
              type="radio" 
              id="uploadStrategy" 
              value="upload" 
              v-model="localFormData.strategy"
              @change="handleStrategyChange"
            >
            <label class="form-check-label" for="uploadStrategy">
              Upload train/validation/testing datasets respectively
            </label>
          </div>

          <div class="form-check">
            <input 
              class="form-check-input" 
              type="radio" 
              id="kfoldStrategy" 
              value="kfold" 
              v-model="localFormData.strategy"
              @change="handleStrategyChange"
            >
            <label class="form-check-label" for="kfoldStrategy">
              Upload a dataset to conduct K-Fold cross-validation
            </label>
          </div>
        </div>

        <!-- 数据集上传区域 -->
        <div class="upload-section" v-show="localFormData.strategy === 'split'">
          <div class="mb-3">
            <label class="form-label">{{ config.splitDatasetLabel || '上传数据集' }}</label>
            <FileUploader
              ref="datasetUploader"
              :allowed-types="['txt', 'csv', 'tsv']"
              :max-size="50 * 1024 * 1024"
              @file-selected="handleDatasetSelected"
            />
          </div>
          
          <label class="form-label">当前比例</label>
          <div class="ratio-controls d-flex align-items-center">
            <div class="ratio-item d-flex align-items-center me-4">
              <label class="ratio-label me-2">训练集：</label>
              <input 
                type="number" 
                class="form-control ratio-input text-center"
                v-model="localSplitRatio.train" 
                min="1" 
                max="10" 
                step="1"
                @input="updateRatios"
                style="width: 180px;"
              >
            </div>
            <span class="ratio-separator me-4">-</span>
            <div class="ratio-item d-flex align-items-center me-4">
              <label class="ratio-label me-2">验证集：</label>
              <input 
                type="number" 
                class="form-control ratio-input text-center"
                v-model="localSplitRatio.validation" 
                min="1" 
                max="10" 
                step="1"
                @input="updateRatios"
                style="width: 180px;"
              >
            </div>
            <span class="ratio-separator me-4">-</span>
            <div class="ratio-item d-flex align-items-center">
              <label class="ratio-label me-2">测试集：</label>
              <input 
                type="number" 
                class="form-control ratio-input text-center"
                v-model="localSplitRatio.test" 
                min="1" 
                max="10" 
                step="1" 
                readonly
                style="width: 180px; background-color: #e9ecef;"
              >
            </div>
          </div>
          <div class="ratio-display mt-3">
            当前分割比例: {{ localSplitRatio.train }}:{{ localSplitRatio.validation }}:{{ localSplitRatio.test }}
          </div>
        </div>

        <!-- 分别上传区域 -->
        <div class="upload-section" v-show="localFormData.strategy === 'upload'">
          <div class="row">
            <div class="col-md-4 mb-3" v-if="config.showTrainUpload !== false">
              <label class="form-label">训练集</label>
              <FileUploader
                ref="trainUploader"
                :allowed-types="['txt', 'csv', 'tsv']"
                :max-size="50 * 1024 * 1024"
                @file-selected="handleTrainSelected"
              />
            </div>
            <div class="col-md-4 mb-3" v-if="config.showValidationUpload !== false">
              <label class="form-label">验证集</label>
              <FileUploader
                ref="validationUploader"
                :allowed-types="['txt', 'csv', 'tsv']"
                :max-size="50 * 1024 * 1024"
                @file-selected="handleValidationSelected"
              />
            </div>
            <div class="col-md-4 mb-3" v-if="config.showTestUpload !== false">
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
        <div class="upload-section" v-show="localFormData.strategy === 'kfold'">
          <div class="mb-3">
            <label class="form-label">{{ config.kfoldDatasetLabel || '上传数据集' }}</label>
            <FileUploader
              ref="kfoldUploader"
              :allowed-types="['txt', 'csv', 'tsv']"
              :max-size="50 * 1024 * 1024"
              @file-selected="handleKfoldSelected"
            />
          </div>
          <div class="mb-3" v-if="config.showTestUpload !== false">
            <label class="form-label">上传测试集</label>
            <FileUploader
              ref="kfoldTestUploader"
              :allowed-types="['txt', 'csv', 'tsv']"
              :max-size="50 * 1024 * 1024"
              @file-selected="handleTestSelected"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">K值</label>
            <input 
              type="number" 
              class="form-control" 
              v-model="localFormData.kfold" 
              min="2" 
              max="10"
              placeholder="请输入K折数 (2-10)"
            >
          </div>
        </div>
      </div>

      <!-- 第二步：模型参数配置 -->
      <div class="step-section mb-4">
        <div class="step-header">
          <h5 class="step-title mb-0">
            <span class="step-number">2</span>
            模型参数配置
          </h5>
        </div>

        <div class="row mt-3">
          <div class="col-md-6 mb-3">
            <label class="form-label">Epochs *</label>
            <input 
              type="number" 
              class="form-control" 
              v-model="localFormData.epochs" 
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
              v-model="localFormData.learningRate" 
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
              v-model="localFormData.seed" 
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
              v-model="localFormData.earlyStopping" 
              min="1"
              required
              placeholder="早停耐心值"
            >
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label">Batch Size</label>
            <select class="form-select" v-model="localFormData.batchSize">
              <option value="16">16</option>
              <option value="32">32</option>
              <option value="64">64</option>
              <option value="128">128</option>
            </select>
          </div>
          <div class="col-md-6 mb-3" v-if="config.showLossFunction !== false">
            <label class="form-label">Loss Function *</label>
            <select class="form-select" v-model="localFormData.lossFunction" required>
              <option 
                v-for="option in config.lossFunctionOptions || defaultLossFunctions" 
                :key="option.value" 
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
          <div class="col-md-6 mb-3" v-if="config.showOptimizer !== false">
            <label class="form-label">Optimizer *</label>
            <select class="form-select" v-model="localFormData.optimizer" required>
              <option 
                v-for="option in config.optimizerOptions || defaultOptimizers" 
                :key="option.value" 
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <!-- 扩展参数插槽 -->
        <slot name="extra-params" :form-data="localFormData" :split-ratio="localSplitRatio"></slot>
      </div>

      <!-- 第三步：模型选择 -->
      <div class="step-section mb-4">
        <div class="step-header">
          <h5 class="step-title mb-0">
            <span class="step-number">3</span>
            选择模型
          </h5>
        </div>

        <div class="row mt-3">
          <div class="col-md-6 mb-3">
            <label class="form-label">模型类型 *</label>
            <select 
              class="form-select" 
              v-model="localFormData.modelType" 
              required
              @change="$emit('model-type-change', localFormData.modelType)"
            >
              <option 
                v-for="option in config.modelOptions" 
                :key="option.value" 
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label">联系邮箱（可选）</label>
            <input
              type="email"
              class="form-control"
              v-model="localFormData.email"
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
          {{ isSubmitting ? config.submittingText || '训练中...' : config.submitText || '开始训练' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import FileUploader from '@/components/FileUpload/FileUploader.vue'
import { trainingApi } from '@/api/training'
import { useUserStore } from '@/stores/user'

// 定义Props
interface FormConfig {
  modelOptions: Array<{ value: string; label: string }>
  splitDatasetLabel?: string
  kfoldDatasetLabel?: string
  showTrainUpload?: boolean
  showValidationUpload?: boolean
  showTestUpload?: boolean
  showLossFunction?: boolean
  lossFunctionOptions?: Array<{ value: string; label: string }>
  showOptimizer?: boolean
  optimizerOptions?: Array<{ value: string; label: string }>
  submitText?: string
  submittingText?: string
}

interface FormData {
  strategy: 'split' | 'upload' | 'kfold'
  epochs: number
  learningRate: number
  seed: number
  earlyStopping: number
  batchSize: number
  lossFunction: string
  optimizer: string
  modelType: string
  kfold?: number
  email?: string
  [key: string]: any // 支持扩展字段
}

const props = defineProps<{
  config: FormConfig
  initialData?: Partial<FormData>
  isSubmitting?: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', data: FormData): void
  (e: 'reset'): void
  (e: 'model-type-change', modelType: string): void
}>()

// 默认损失函数选项
const defaultLossFunctions = [
  { value: 'crossentropy', label: 'Cross Entropy' },
  { value: 'mse', label: 'MSE (Mean Squared Error)' },
  { value: 'mae', label: 'MAE (Mean Absolute Error)' }
]

// 默认优化器选项
const defaultOptimizers = [
  { value: 'adam', label: 'Adam' },
  { value: 'sgd', label: 'SGD' },
  { value: 'adamw', label: 'AdamW' }
]

// 响应式数据
const localFormData = reactive<FormData>({
  strategy: 'split',
  epochs: 50,
  learningRate: 0.001,
  seed: 42,
  earlyStopping: 5,
  batchSize: 32,
  lossFunction: 'crossentropy',
  optimizer: 'adam',
  modelType: '',
  kfold: 5,
  email: '',
  ...props.initialData
})

// 邮箱输入的自动回填/保持空规则
const userStore = useUserStore()
const emailTouched = ref(false) // 用户是否动过邮箱（包含清空）
const isAutoFilling = ref(false) // 程序性赋值阶段：避免触发 emailTouched=true
const userEmailCache = ref<string>('') // 缓存登录邮箱

const programmaticSetEmail = async (nextEmail: string) => {
  isAutoFilling.value = true
  localFormData.email = nextEmail
  await nextTick()
  isAutoFilling.value = false
}

const tryAutoFillEmail = async () => {
  const nextEmail = userStore.userInfo?.email || ''
  userEmailCache.value = nextEmail
  if (emailTouched.value) return
  if (nextEmail && localFormData.email) return
  await programmaticSetEmail(nextEmail)
}

// 当登录用户信息变更时（例如路由守卫异步拉取），再进行一次自动回填
onMounted(() => {
  if (userStore.userInfo?.email) {
    tryAutoFillEmail()
  }
})

watch(
  () => userStore.userInfo?.email,
  async (newEmail) => {
    userEmailCache.value = newEmail || ''
    if (emailTouched.value) return
    if (!newEmail) return
    if (localFormData.email) return
    await programmaticSetEmail(newEmail)
  }
)

// 用户对邮箱的任何手动改动都将置 touched=true
watch(
  () => localFormData.email,
  () => {
    if (isAutoFilling.value) return
    emailTouched.value = true
  }
)

const localSplitRatio = reactive({
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
const kfoldTestUploader = ref<InstanceType<typeof FileUploader> | null>(null)

// 已上传的数据集主路径
const datasetPath = ref<string | null>(null)
const testPath = ref<string | null>(null)

// 计算属性
const isFormValid = computed(() => {
  return localFormData.modelType && 
         localFormData.epochs > 0 && 
         localFormData.learningRate > 0 &&
         localFormData.seed > 0 &&
         localFormData.earlyStopping > 0
})

// 方法
const handleStrategyChange = () => {
  // 清除之前的选择
  if (datasetUploader.value) datasetUploader.value.clear()
  if (trainUploader.value) trainUploader.value.clear()
  if (validationUploader.value) validationUploader.value.clear()
  if (testUploader.value) testUploader.value.clear()
  if (kfoldUploader.value) kfoldUploader.value.clear()
  if (kfoldTestUploader.value) kfoldTestUploader.value.clear()
  
  // 发送事件通知父组件
  emit('reset')
}

const updateRatios = () => {
  // 确保比例总和为10
  const total = localSplitRatio.train + localSplitRatio.validation + localSplitRatio.test
  if (total !== 10) {
    localSplitRatio.test = 10 - localSplitRatio.train - localSplitRatio.validation
  }
}

const handleDatasetSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('数据集文件已选择:', file.name)
  const info = await trainingApi.uploadFile(file, 'dataset')
  datasetPath.value = info.file_path
}

const handleTrainSelected = async (files: File[]) => {
  if (!files.length) return
  console.log('训练集文件已选择:', files[0].name)
}

const handleValidationSelected = async (files: File[]) => {
  if (!files.length) return
  console.log('验证集文件已选择:', files[0].name)
}

const handleTestSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('测试集文件已选择:', file.name)
  const info = await trainingApi.uploadFile(file, 'test_dataset')
  testPath.value = info.file_path
}

const handleKfoldSelected = async (files: File[]) => {
  if (!files.length) return
  console.log('K折数据集文件已选择:', files[0].name)
}

const downloadExample = () => {
  // TODO: 实现示例数据下载
  console.log('下载示例数据')
}

const onSubmit = () => {
  if (!isFormValid.value) return
  
  const submitData = {
    ...localFormData,
    splitRatio: localSplitRatio,
    datasetPath: datasetPath.value,
    testPath: testPath.value
  }
  
  emit('submit', submitData)
}

const resetForm = () => {
  const nextEmail = emailTouched.value ? localFormData.email : (userEmailCache.value || '')
  isAutoFilling.value = true
  Object.assign(localFormData, {
    strategy: 'split',
    epochs: 50,
    learningRate: 0.001,
    seed: 42,
    earlyStopping: 5,
    batchSize: 32,
    lossFunction: 'crossentropy',
    optimizer: 'adam',
    modelType: props.initialData?.modelType || '',
    kfold: 5,
    ...props.initialData,
    // 保证 reset 逻辑的 email 行为优先级最高
    email: nextEmail,
  })
  
  Object.assign(localSplitRatio, {
    train: 7,
    validation: 2,
    test: 1
  })
  
  datasetPath.value = null
  testPath.value = null
  handleStrategyChange()

  // 确保 resetForm 设置的 email 不会触发 touched=true
  nextTick(() => {
    isAutoFilling.value = false
  })
}

// 监听外部isSubmitting变化
watch(() => props.isSubmitting, (newValue) => {
  // 可以在这里处理提交状态变化
})

// 暴露方法给父组件
defineExpose({
  resetForm,
  getFormData: () => ({ ...localFormData }),
  getSplitRatio: () => ({ ...localSplitRatio }),
  getDatasetPath: () => datasetPath.value,
  getTestPath: () => testPath.value
})
</script>

<style scoped>
/* 步骤区域样式 */
.step-section {
  position: relative;
  padding-left: 50px;
}

.step-title {
  position: relative;
  color: #2c3e50;
  font-weight: 600;
}

.step-number {
  position: absolute;
  left: -50px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(13, 110, 253, 0.3);
}

/* 策略选项样式 */
.strategy-options .form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

/* 上传区域样式 */
.upload-section {
  background-color: #f8f8f8;
  padding: 20px;
  border-radius: 8px;
  margin-top: 15px;
  border: 1px solid #eeeeee;
}

/* 比例控制样式 */
.ratio-controls {
  background: #f0f0f0;
  padding: 15px;
  border-radius: 6px;
  margin-top: 15px;
  border: 1px solid #dddddd;
}

.ratio-display {
  background-color: #f0f0f0;
  padding: 10px 15px;
  border-radius: 6px;
  border: 1px solid #dddddd;
  color: #555555;
  text-align: center;
  margin-top: 15px;
}

.ratio-input {
  display: inline-block;
}

.ratio-separator {
  font-weight: bold;
  color: #666;
}

/* 表单控件样式 */
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

/* 步骤头部样式 */
.step-header {
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .step-section {
    padding-left: 15px;
  }

  .upload-section {
    padding: 15px;
  }
  
  .ratio-controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .ratio-separator {
    display: none;
  }
}
</style>