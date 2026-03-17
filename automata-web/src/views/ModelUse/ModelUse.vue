<template>
  <div class="model-use">
    <div class="container-fluid py-4">
      <!-- 模型使用表单卡片 -->
      <div class="row justify-content-center">
        <div class="col-12 col-lg-8">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white border-0 pt-3 pb-0 px-4 d-flex justify-content-between align-items-center">
              <h4 class="mb-0 fw-semibold">使用训练好的模型</h4>
              <span class="badge bg-success text-wrap">Use Your Trained Model</span>
            </div>

            <div class="card-body p-4">
              <form @submit.prevent="handleSubmit" class="use-form">
                <!-- 第一步：选择模型类型 -->
                <div class="step-section mb-4">
                  <h5 class="step-title">
                    <span class="step-number">1</span>
                    选择模型类型
                  </h5>

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
                  <h5 class="step-title">
                    <span class="step-number">2</span>
                    上传测试数据
                  </h5>

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
                  <h5 class="step-title">
                    <span class="step-number">3</span>
                    上传模型文件
                  </h5>

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
                    <div class="mb-3">
                      <label class="form-label">Winmap 文件</label>
                      <FileUploader
                        ref="winmapUploader"
                        :allowed-types="['pkl']"
                        :max-size="50 * 1024 * 1024"
                        @file-selected="handleWinmapSelected"
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
                  <h5 class="step-title">
                    <span class="step-number">4</span>
                    联系方式
                  </h5>

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
import { modelUseApi } from '@/api/modelUse'

interface FormData {
  modelType: string
  email: string
}

interface Job {
  id: string
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
  modelType: 'cnn',
  email: ''
})

// 文件上传引用
const testDataUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const modelUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const somModelUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const winmapUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const encoderUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const classifierUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const scalerUploader = ref<InstanceType<typeof FileUploader> | null>(null)
const unSemiModelUploader = ref<InstanceType<typeof FileUploader> | null>(null)

// 文件路径
const testDataSetPath = ref<string | null>(null)
const modelPath = ref<string | null>(null)
const somModelPath = ref<string | null>(null)
const winmapPath = ref<string | null>(null)
const encoderPath = ref<string | null>(null)
const classifierPath = ref<string | null>(null)
const scalerPath = ref<string | null>(null)
const unSemiModelPath = ref<string | null>(null)

// 计算属性
const isFormValid = computed(() => {
  if (!formData.modelType) return false
  
  // 根据模型类型检查必需的文件
  if (formData.modelType === 'som') {
    return testDataSetPath.value && somModelPath.value && winmapPath.value
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
  if (winmapUploader.value) winmapUploader.value.clear()
  if (encoderUploader.value) encoderUploader.value.clear()
  if (classifierUploader.value) classifierUploader.value.clear()
  if (scalerUploader.value) scalerUploader.value.clear()
  if (unSemiModelUploader.value) unSemiModelUploader.value.clear()
  
  // 清除文件路径
  testDataSetPath.value = null
  modelPath.value = null
  somModelPath.value = null
  winmapPath.value = null
  encoderPath.value = null
  classifierPath.value = null
  scalerPath.value = null
  unSemiModelPath.value = null
}

const handleTestDataSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('测试数据集已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'test_dataset')
  testDataSetPath.value = info.file_path
}

const handleModelSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'model')
  modelPath.value = info.file_path
}

const handleSomModelSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('SOM模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'som_model')
  somModelPath.value = info.file_path
}

const handleWinmapSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('Winmap文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'winmap')
  winmapPath.value = info.file_path
}

const handleEncoderSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('编码器模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'encoder')
  encoderPath.value = info.file_path
}

const handleClassifierSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('分类器模型文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'classifier')
  classifierPath.value = info.file_path
}

const handleScalerSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
  console.log('Scaler文件已选择:', file.name)
  const info = await modelUseApi.uploadFile(file, 'scaler')
  scalerPath.value = info.file_path
}

const handleUnSemiModelSelected = async (files: File[]) => {
  if (!files.length) return
  const file = files[0]
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

    // 构造预测参数
    const predictParams = {
      model_type: formData.modelType,
      test_data_path: testDataSetPath.value,
      email: formData.email || undefined,
      ...(modelPath.value && { model_path: modelPath.value }),
      ...(somModelPath.value && { som_model_path: somModelPath.value }),
      ...(winmapPath.value && { winmap_path: winmapPath.value }),
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
      status: response.status,
      progress: 0,
      createdAt: response.created_at,
      updatedAt: response.created_at,
      duration: 0
    }

    console.log('模型预测任务已创建:', response)

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
  router.push(`/model/use/result/${jobId}`)
}

// 生命周期
onMounted(() => {
  console.log('模型使用页面已加载')
})
</script>

<style scoped>
.model-use {
  min-height: calc(100vh - 100px);
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
  background: #28a745;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: bold;
}

.form-check-input:checked {
  background-color: #28a745;
  border-color: #28a745;
}
</style>