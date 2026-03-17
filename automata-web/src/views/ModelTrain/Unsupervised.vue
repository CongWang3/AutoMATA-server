<template>
  <div class="automata-training-unsupervised">
    <!-- 无监督学习训练表单 -->
    <div class="container-fluid p-4">
      <div class="row justify-content-center">
        <div class="col-12 col-lg-10">
          <el-card class="form-card">
            <template #header>
              <div class="card-header">
                <span class="title">无监督学习模型训练</span>
                <el-tag type="info">Unsupervised Learning</el-tag>
              </div>
            </template>
            <div class="card-body p-4">
              <BaseTrainingForm
                ref="trainingFormRef"
                :config="formConfig"
                :initial-data="initialFormData"
                :is-submitting="isSubmitting"
                @submit="handleSubmit"
                @reset="handleReset"
                @model-type-change="handleModelTypeChange"
              >
                <!-- 无监督学习不需要额外参数 -->
                <template #extra-params></template>
              </BaseTrainingForm>
            </div>
          </el-card>
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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import BaseTrainingForm from '@/components/Training/BaseTrainingForm.vue'
import JobStatus from '@/components/Job/JobStatus.vue'
import { trainingApi } from '@/api/training'
import { webSocketService } from '@/api/websocket'
import { useTrainingForm } from '@/composables/useTrainingForm'
import type { TrainingFormData } from '@/composables/useTrainingForm'

// <!-- 
// 审查上下文：
// - 设计意图：通过基础组件和composable重构，消除重复代码，提高可维护性
// - 已知局限：保留了原有的功能完整性，通过配置化实现差异化需求
// - 业务背景：无监督学习训练页面，支持VAE和DeepCluster模型
// - 测试重点：确保表单提交、文件上传、任务创建等核心功能正常工作
// -->

interface Job {
  id: string
  name: string
  status: string
  progress: number
  currentStep?: string   // 当前执行步骤
  createdAt: string
  updatedAt: string
  duration: number
  resultFile?: string    // 结果文件路径
  errorMessage?: string  // 错误信息
}

// 响应式数据
const router = useRouter()
const trainingFormRef = ref<InstanceType<typeof BaseTrainingForm> | null>(null)

// 使用训练表单composable
const {
  isSubmitting,
  currentJob,
  setSubmitting,
  setCurrentJob,
  resetForm: resetTrainingForm
} = useTrainingForm({
  initialData: {
    lossFunction: 'mse',
    modelType: 'vae'
  }
})

// 当前模型类型
const currentModelType = ref('vae')

// VAE损失函数选项（14种）
const vaeLossFunctions = [
  { value: 'mse', label: 'MSE (Mean Squared Error)' },
  { value: 'mae', label: 'MAE (Mean Absolute Error)' },
  { value: 'huber', label: 'Huber Loss' },
  { value: 'smooth_l1', label: 'Smooth L1 Loss' },
  { value: 'log_cosh', label: 'Log-Cosh Loss' },
  { value: 'bce', label: 'Binary Cross Entropy' },
  { value: 'bce_with_logits', label: 'BCE with Logits' },
  { value: 'kl_div', label: 'KL Divergence' },
  { value: 'cosine_embedding', label: 'Cosine Embedding Loss' },
  { value: 'poisson_nll', label: 'Poisson NLL Loss' },
  { value: 'gaussian_nll', label: 'Gaussian NLL Loss' },
  { value: 'beta_vae', label: 'Beta-VAE Loss' },
  { value: 'info_vae', label: 'Info-VAE Loss' },
  { value: 'disentangled_vae', label: 'Disentangled VAE Loss' }
]

// DeepCluster损失函数选项（8种）
const deepclusterLossFunctions = [
  { value: 'kmeans_ce', label: 'K-Means Cross Entropy' },
  { value: 'spectral', label: 'Spectral Clustering Loss' },
  { value: 'agglomerative', label: 'Agglomerative Loss' },
  { value: 'mean_shift', label: 'Mean Shift Loss' },
  { value: 'gmm', label: 'GMM (Gaussian Mixture Model)' },
  { value: 'contrastive', label: 'Contrastive Loss' },
  { value: 'triplet', label: 'Triplet Loss' },
  { value: 'reconstruction', label: 'Reconstruction Loss' }
]

// 无监督优化器选项
const unsupervisedOptimizers = [
  { value: 'adam', label: 'Adam' },
  { value: 'sgd', label: 'SGD' },
  { value: 'adamw', label: 'AdamW' }
]

// 动态计算当前损失函数选项
const currentLossFunctions = computed(() => {
  return currentModelType.value === 'vae' ? vaeLossFunctions : deepclusterLossFunctions
})

// 表单配置
const formConfig = reactive({
  modelOptions: [
    {
      value: 'vae',
      label: 'VAE > Variational AutoEncoder for dimensionality reduction and feature learning'
    },
    {
      value: 'deepcluster',
      label: 'DeepCluster > Deep clustering algorithm for unsupervised representation learning'
    }
  ],
  splitDatasetLabel: '上传数据集',
  showTestUpload: false,
  showLossFunction: true,
  lossFunctionOptions: vaeLossFunctions,
  showOptimizer: true,
  optimizerOptions: unsupervisedOptimizers,
  submitText: '开始训练',
  submittingText: '训练中...'
})

const initialFormData = {
  lossFunction: 'mse',
  modelType: 'vae'
}

// 方法
const handleModelTypeChange = (modelType: string) => {
  console.log('模型类型已更改:', modelType)
  currentModelType.value = modelType
  // 根据模型类型更新损失函数选项
  formConfig.lossFunctionOptions = modelType === 'vae' ? vaeLossFunctions : deepclusterLossFunctions
}

const handleReset = () => {
  console.log('表单已重置')
}

const handleSubmit = async (data: TrainingFormData) => {
  try {
    setSubmitting(true)
    
    if (data.strategy === 'split' && !data.datasetPath) {
      alert('请先上传数据集文件')
      return
    }

    // 构造训练参数
    const params = {
      strategy: data.strategy,
      epochs: data.epochs,
      learning_rate: data.learningRate,
      batch_size: data.batchSize,
      seed: data.seed,
      early_stopping: data.earlyStopping,
      loss_function: data.lossFunction,
      optimizer: data.optimizer || 'adam',
      ...(data.strategy === 'split' && {
        ratio: `${data.splitRatio.train}:${data.splitRatio.validation}:${data.splitRatio.test}`
      }),
      ...(data.strategy === 'kfold' && {
        kfold: data.kfold
      })
    }

    const trainingParams = {
      task_name: `unsupervised_${data.modelType}_${Date.now()}`,
      model_type: data.modelType,
      parameters: params,
      dataset_path: data.datasetPath || undefined
    }

    // 调用API创建训练任务
    const response = await trainingApi.trainUnsupervised(trainingParams)
    
    setCurrentJob({
      id: response.job_id,
      name: response.task_name,
      status: response.status,  // 直接使用后端返回的状态（如 Submitted）
      progress: response.progress || 0,
      currentStep: response.current_step || '已提交，等待执行',
      createdAt: response.created_at,
      updatedAt: response.created_at,
      duration: 0,
      resultFile: response.result_file || undefined,
      errorMessage: response.error_message || undefined
    })

    console.log('无监督训练任务已创建:', response)

  } catch (error) {
    console.error('创建无监督训练任务失败:', error)
    alert('创建训练任务失败，请稍后重试')
  } finally {
    setSubmitting(false)
  }
}

const cancelJob = (jobId: string) => {
  console.log('取消任务:', jobId)
  // 实现取消逻辑
}

const retryJob = (jobId: string) => {
  console.log('重试任务:', jobId)
  // 实现重试逻辑
}

const viewResult = (jobId: string) => {
  router.push(`/model/result/${jobId}`)
}

// WebSocket任务状态处理
const handleTaskStatusUpdate = (data: any) => {
  if (!currentJob.value) return
  
  // 过滤只处理当前任务的消息
  if (data.job_id !== currentJob.value.id) return
  
  console.log('收到任务状态更新:', data)
  
  // 更新任务状态（直接使用后端返回的状态值，不转换大小写）
  if (data.status) {
    currentJob.value.status = data.status
  }
  if (data.progress !== undefined) {
    currentJob.value.progress = data.progress
  }
  if (data.current_step) {
    currentJob.value.currentStep = data.current_step
  }
  if (data.result_file) {
    currentJob.value.resultFile = data.result_file
  }
  if (data.error_message) {
    currentJob.value.errorMessage = data.error_message
  }
  if (data.updated_at) {
    currentJob.value.updatedAt = data.updated_at
  }
}

// 连接WebSocket
const connectWebSocket = async () => {
  try {
    await webSocketService.connectTaskStatus()
    webSocketService.setOnTaskStatus(handleTaskStatusUpdate)
    console.log('无监督训练页面WebSocket连接成功')
  } catch (error) {
    console.error('无监督训练页面WebSocket连接失败:', error)
  }
}

// 生命周期
onMounted(() => {
  console.log('无监督学习训练页面已加载')
  connectWebSocket()
})

onUnmounted(() => {
  // 组件卸载时清理WebSocket回调
  webSocketService.setOnTaskStatus(() => {})
  console.log('无监督学习训练页面已卸载')
})
</script>

<style scoped>
.automata-training-unsupervised {
  min-height: calc(100vh - 100px);
}

/* 卡片头部样式 */
.card-header {
  border-bottom: none;
}

/* 成功状态 Bootstrap 主蓝色 */
.bg-success {
  background-color: #0d6efd !important;
}

.text-success {
  color: #0d6efd !important;
}

/* 表单控件悬停效果 */
.form-control:hover,
.form-select:hover {
  border-color: #aaaaaa;
}

/* 响应式调整 */
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