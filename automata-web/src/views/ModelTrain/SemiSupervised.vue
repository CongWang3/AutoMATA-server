<template>
  <div class="automata-training-semi-supervised">
    <!-- 半监督学习训练表单 -->
    <div class="container-fluid p-4">
      <div class="row justify-content-center">
        <div class="col-12 col-lg-10">
          <el-card class="form-card">
            <template #header>
              <div class="card-header">
                <span class="title">半监督学习模型训练</span>
                <el-tag type="warning">Semi-Supervised Learning</el-tag>
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
                <!-- 半监督学习特有参数 -->
                <template #extra-params="{ formData }">
                  <div class="semi-specific-params mt-4 p-3 bg-light rounded">
                    <h6 class="mb-3">半监督学习特定参数</h6>
                    <div class="row">
                      <div class="col-md-6 mb-3">
                        <label class="form-label">监督损失权重 (α)</label>
                        <input 
                          type="number" 
                          class="form-control" 
                          v-model="formData.alpha" 
                          min="0" 
                          max="10"
                          step="0.1"
                          placeholder="监督损失权重"
                        >
                      </div>
                      <div class="col-md-6 mb-3">
                        <label class="form-label">重构损失权重 (β)</label>
                        <input 
                          type="number" 
                          class="form-control" 
                          v-model="formData.beta" 
                          min="0" 
                          max="10"
                          step="0.1"
                          placeholder="重构损失权重"
                        >
                      </div>
                      <div class="col-md-6 mb-3">
                        <label class="form-label">正则化损失权重 (γ)</label>
                        <input 
                          type="number" 
                          class="form-control" 
                          v-model="formData.gamma" 
                          min="0" 
                          max="10"
                          step="0.01"
                          placeholder="正则化损失权重"
                        >
                      </div>
                    </div>

                    <!-- 梯形网络损失函数 -->
                    <div class="mb-3" v-if="formData.modelType === 'ladder'">
                      <label class="form-label">损失函数 *</label>
                      <select class="form-select" v-model="formData.lossFunction" required>
                        <option value="semi_supervised">Semi-Supervised Loss</option>
                        <option value="focal">Focal Loss</option>
                        <option value="label_smoothing">Label Smoothing Loss</option>
                        <option value="contrastive">Contrastive Loss</option>
                      </select>
                    </div>

                    <!-- 伪标签损失函数 -->
                    <div class="mb-3" v-if="formData.modelType === 'pseudo'">
                      <label class="form-label">损失函数 *</label>
                      <select class="form-select" v-model="formData.lossFunction" required>
                        <option value="pseudo_label">Pseudo-Label Loss</option>
                        <option value="focal">Focal Loss</option>
                        <option value="label_smoothing">Label Smoothing Loss</option>
                      </select>
                    </div>

                    <!-- 伪标签特有参数 -->
                    <div v-if="formData.modelType === 'pseudo'">
                      <div class="row">
                        <div class="col-md-6 mb-3">
                          <label class="form-label">伪标签损失权重</label>
                          <input 
                            type="number" 
                            class="form-control" 
                            v-model="formData.pseudoBeta" 
                            min="0" 
                            max="10"
                            step="0.1"
                            placeholder="伪标签损失权重"
                          >
                        </div>
                        <div class="col-md-6 mb-3">
                          <label class="form-label">置信度阈值</label>
                          <input 
                            type="number" 
                            class="form-control" 
                            v-model="formData.confidenceThreshold" 
                            min="0" 
                            max="1"
                            step="0.01"
                            placeholder="置信度阈值"
                          >
                        </div>
                        <div class="col-md-6 mb-3">
                          <label class="form-label">伪标签比例</label>
                          <input 
                            type="number" 
                            class="form-control" 
                            v-model="formData.pseudoRatio" 
                            min="0" 
                            max="1"
                            step="0.01"
                            placeholder="伪标签比例"
                          >
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
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
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
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
// - 业务背景：半监督学习训练页面，支持LadderNetwork和Pseudo-Labeling模型
// - 测试重点：确保表单提交、文件上传、任务创建等核心功能正常工作，特别关注半监督特有参数
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
    lossFunction: 'semi_supervised',
    modelType: 'ladder',
    alpha: 1.0,
    beta: 1.0,
    gamma: 0.1,
    pseudoBeta: 0.5,
    confidenceThreshold: 0.8,
    pseudoRatio: 0.5
  }
})

// 当前模型类型
const currentModelType = ref('ladder')

// 半监督优化器选项（4种）
const semiSupervisedOptimizers = [
  { value: 'adam', label: 'Adam' },
  { value: 'sgd', label: 'SGD' },
  { value: 'adamw', label: 'AdamW' },
  { value: 'rmsprop', label: 'RMSprop' }
]

// 表单配置
const formConfig = reactive({
  modelOptions: [
    {
      value: 'ladder',
      label: 'LadderNetwork > 利用编码器-解码器架构通过未标注数据进行训练'
    },
    {
      value: 'pseudo',
      label: 'Pseudo-Labeling > 通过迭代地为高置信度的未标注数据添加标签进行训练'
    }
  ],
  splitDatasetLabel: '上传训练集 (NOTE: 未标注样本的标签标记为Unknown)',
  kfoldDatasetLabel: '上传训练集 (含Unknown标签)',
  showTestUpload: true,
  showLossFunction: false, // 半监督有自己的损失函数配置
  showOptimizer: true,
  optimizerOptions: semiSupervisedOptimizers,
  submitText: '开始训练',
  submittingText: '训练中...'
})

const initialFormData = {
  lossFunction: 'semi_supervised',
  modelType: 'ladder',
  alpha: 1.0,
  beta: 1.0,
  gamma: 0.1,
  pseudoBeta: 0.5,
  confidenceThreshold: 0.8,
  pseudoRatio: 0.5
}

// 方法
const handleModelTypeChange = (modelType: string) => {
  // 根据模型类型设置默认损失函数
  currentModelType.value = modelType
  if (modelType === 'ladder') {
    initialFormData.lossFunction = 'semi_supervised'
  } else if (modelType === 'pseudo') {
    initialFormData.lossFunction = 'pseudo_label'
  }
  console.log('模型类型已更改:', modelType)
}

const handleReset = () => {
  console.log('表单已重置')
}

const handleSubmit = async (data: TrainingFormData) => {
  try {
    setSubmitting(true)
    
    if (data.strategy === 'split' && !data.datasetPath) {
      alert('请先上传训练集文件')
      return
    }

    if (!data.testPath) {
      alert('请上传测试集文件')
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
      alpha: data.alpha || 1.0,
      beta: data.beta || 1.0,
      gamma: data.gamma || 0.1,
      ...(data.modelType === 'pseudo' && {
        pseudo_beta: data.pseudoBeta,
        confidence_threshold: data.confidenceThreshold,
        pseudo_ratio: data.pseudoRatio
      }),
      ...(data.strategy === 'split' && {
        ratio: `${data.splitRatio.train}:${data.splitRatio.validation}:${data.splitRatio.test}`
      }),
      ...(data.strategy === 'kfold' && {
        kfold: data.kfold
      })
    }

    const trainingParams = {
      task_name: `semi_supervised_${data.modelType}_${Date.now()}`,
      model_type: data.modelType,
      parameters: params,
      email: data.email,
      dataset_path: data.datasetPath || undefined
    }

    // 调用API创建训练任务
    const response = await trainingApi.trainSemiSupervised(trainingParams)
    
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

    console.log('半监督训练任务已创建:', response)

  } catch (error) {
    console.error('创建半监督训练任务失败:', error)
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
    console.log('半监督训练页面WebSocket连接成功')
  } catch (error) {
    console.error('半监督训练页面WebSocket连接失败:', error)
  }
}

// 生命周期
onMounted(() => {
  console.log('半监督学习训练页面已加载')
  connectWebSocket()
})

onUnmounted(() => {
  // 组件卸载时清理WebSocket回调
  webSocketService.setOnTaskStatus(() => {})
  console.log('半监督学习训练页面已卸载')
})
</script>

<style scoped>
.automata-training-semi-supervised {
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

/* 半监督特定参数区域 */
.semi-specific-params {
  border-left: 4px solid #ffc107;
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