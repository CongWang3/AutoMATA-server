import { ref, reactive, computed } from 'vue'
import type { Ref } from 'vue'
import FileUploader from '@/components/FileUpload/FileUploader.vue'

/**
 * 训练表单通用状态管理
 * 提供训练表单的共享状态和方法
 */

export interface TrainingFormData {
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
  // 半监督特有字段
  alpha?: number
  beta?: number
  gamma?: number
  pseudoBeta?: number
  confidenceThreshold?: number
  pseudoRatio?: number
  // 文件路径
  datasetPath?: string | null
  testPath?: string | null
  // 分割比例
  splitRatio?: {
    train: number
    validation: number
    test: number
  }
  [key: string]: any // 支持扩展字段
}

export interface SplitRatio {
  train: number
  validation: number
  test: number
}

export interface UseTrainingFormOptions {
  initialData?: Partial<TrainingFormData>
  needTestDataset?: boolean
}

export function useTrainingForm(options: UseTrainingFormOptions = {}) {
  // 响应式数据
  const isSubmitting = ref(false)
  const currentJob = ref<any>(null)
  
  const formData = reactive<TrainingFormData>({
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
    ...options.initialData
  })

  const splitRatio = reactive<SplitRatio>({
    train: 7,
    validation: 2,
    test: 1
  })

  // 文件上传引用
  const datasetUploader = ref<InstanceType<typeof FileUploader> | null>(null)
  const trainUploader = ref<InstanceType<typeof FileUploader> | null>(null)
  const validationUploader = ref<InstanceType<typeof FileUploader> | null>(null)
  const testUploader = ref<InstanceType<typeof FileUploader> | null>(null)
  const separateTestUploader = ref<InstanceType<typeof FileUploader> | null>(null)
  const kfoldUploader = ref<InstanceType<typeof FileUploader> | null>(null)
  const kfoldTestUploader = ref<InstanceType<typeof FileUploader> | null>(null)

  // 已上传的数据集主路径
  const datasetPath = ref<string | null>(null)
  const testPath = ref<string | null>(null)

  // 计算属性
  const isFormValid = computed(() => {
    return formData.modelType && 
           formData.epochs > 0 && 
           formData.learningRate > 0 &&
           formData.seed > 0 &&
           formData.earlyStopping > 0
  })

  // 方法
  const handleStrategyChange = () => {
    // 清除之前的选择
    if (datasetUploader.value) datasetUploader.value.clear()
    if (trainUploader.value) trainUploader.value.clear()
    if (validationUploader.value) validationUploader.value.clear()
    if (testUploader.value) testUploader.value.clear()
    if (separateTestUploader.value) separateTestUploader.value.clear()
    if (kfoldUploader.value) kfoldUploader.value.clear()
    if (kfoldTestUploader.value) kfoldTestUploader.value.clear()
  }

  const updateRatios = () => {
    // 确保比例总和为10
    const total = splitRatio.train + splitRatio.validation + splitRatio.test
    if (total !== 10) {
      splitRatio.test = 10 - splitRatio.train - splitRatio.validation
    }
  }

  const resetForm = (newInitialData?: Partial<TrainingFormData>) => {
    Object.assign(formData, {
      strategy: 'split',
      epochs: 50,
      learningRate: 0.001,
      seed: 42,
      earlyStopping: 5,
      batchSize: 32,
      lossFunction: 'crossentropy',
      optimizer: 'adam',
      modelType: newInitialData?.modelType || options.initialData?.modelType || '',
      kfold: 5,
      email: '',
      ...newInitialData,
      ...options.initialData
    })
    
    Object.assign(splitRatio, {
      train: 7,
      validation: 2,
      test: 1
    })
    
    datasetPath.value = null
    testPath.value = null
    handleStrategyChange()
    currentJob.value = null
  }

  const setSubmitting = (submitting: boolean) => {
    isSubmitting.value = submitting
  }

  const setCurrentJob = (job: any) => {
    currentJob.value = job
  }

  // 返回所有需要的状态和方法
  return {
    // 状态
    isSubmitting,
    currentJob,
    formData,
    splitRatio,
    datasetPath,
    testPath,
    
    // 引用
    datasetUploader,
    trainUploader,
    validationUploader,
    testUploader,
    separateTestUploader,
    kfoldUploader,
    kfoldTestUploader,
    
    // 计算属性
    isFormValid,
    
    // 方法
    handleStrategyChange,
    updateRatios,
    resetForm,
    setSubmitting,
    setCurrentJob
  }
}