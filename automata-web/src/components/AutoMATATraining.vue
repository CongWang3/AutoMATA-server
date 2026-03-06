<template>
  <div class="automata-training-simple">
    <!-- 简化版训练表单 -->
    <div class="container-fluid p-4">
      <div class="row justify-content-center">
        <div class="col-12 col-lg-8">
          <div class="card border-0 shadow">
            <div class="card-header bg-primary text-white py-3">
              <h4 class="mb-0 text-center">
                <i class="fas fa-cogs me-2"></i>模型训练配置
              </h4>
            </div>
            <div class="card-body p-4">
              <form @submit.prevent="handleSubmit" class="row g-3">
                <!-- 模型类型 -->
                <div class="col-md-6">
                  <label class="form-label fw-medium">
                    <i class="fas fa-network-wired me-1 text-primary"></i>模型类型 *
                  </label>
                  <select class="form-select form-select-lg" v-model="formData.modelType" required>
                    <option value="">请选择模型架构</option>
                    <option value="LSTM">LSTM (长短期记忆网络)</option>
                    <option value="CNN">CNN (卷积神经网络)</option>
                    <option value="RNN">RNN (循环神经网络)</option>
                    <option value="MLP">MLP (多层感知机)</option>
                  </select>
                  <div class="form-text">选择适合您数据特征的神经网络架构</div>
                </div>

                <!-- Epoch -->
                <div class="col-md-6">
                  <label class="form-label fw-medium">
                    <i class="fas fa-redo me-1 text-primary"></i>训练轮数 (Epoch) *
                  </label>
                  <input type="number" class="form-control form-control-lg" v-model="formData.epoch" min="1" max="1000"
                    required>
                  <div class="form-text">建议范围：10-200，默认值：20</div>
                </div>

                <!-- 学习率 -->
                <div class="col-md-6">
                  <label class="form-label fw-medium">
                    <i class="fas fa-tachometer-alt me-1 text-primary"></i>学习率 *
                  </label>
                  <input type="number" class="form-control form-control-lg" v-model="formData.learningRate"
                    step="0.0001" min="0.0001" max="1" required>
                  <div class="form-text">推荐值：0.001 或 0.0001</div>
                </div>

                <!-- Early Stopping -->
                <div class="col-md-6">
                  <label class="form-label fw-medium">
                    <i class="fas fa-stopwatch me-1 text-primary"></i>早停耐心值 *
                  </label>
                  <input type="number" class="form-control form-control-lg" v-model="formData.earlyStopping" min="1"
                    max="100" required>
                  <div class="form-text">连续多少轮无改善时停止训练</div>
                </div>
            </div>
          </div>

          <!-- 数据参数配置 -->
          <div v-show="currentStep === 1" class="step-pane">
            <h5 class="mb-4 pb-2 border-bottom">
              <i class="fas fa-database me-2 text-primary"></i>数据处理参数
            </h5>
            <div class="row g-3">
              <!-- 标签数量 -->
              <div class="col-md-6">
                <label class="form-label fw-medium">
                  <i class="fas fa-tags me-1 text-primary"></i>标签类别数 *
                </label>
                <input type="number" class="form-control form-control-lg" v-model="formData.labelCount" min="2"
                  max="1000" required>
                <div class="form-text">分类任务中的类别总数</div>
              </div>

              <!-- 批次大小 -->
              <div class="col-md-6">
                <label class="form-label fw-medium">
                  <i class="fas fa-layer-group me-1 text-primary"></i>批次大小 *
                </label>
                <input type="number" class="form-control form-control-lg" v-model="formData.batchSize" min="1"
                  max="1024" required>
                <div class="form-text">每批处理的样本数量</div>
              </div>

              <!-- 随机种子 -->
              <div class="col-md-6">
                <label class="form-label fw-medium">
                  <i class="fas fa-random me-1 text-primary"></i>随机种子
                </label>
                <input type="number" class="form-control form-control-lg" v-model="formData.randomSeed" min="0"
                  max="999999">
                <div class="form-text">确保实验可重现性</div>
              </div>

              <!-- 验证集比例 -->
              <div class="col-md-6">
                <label class="form-label fw-medium">
                  <i class="fas fa-chart-pie me-1 text-primary"></i>验证集比例 (%)
                </label>
                <input type="number" class="form-control form-control-lg" v-model="formData.validationSplit" min="0"
                  max="50">
                <div class="form-text">用于验证的数据占比</div>
              </div>
            </div>
          </div>

          <!-- 训练策略配置 -->
          <div v-show="currentStep === 2" class="step-pane">
            <h5 class="mb-4 pb-2 border-bottom">
              <i class="fas fa-cog me-2 text-primary"></i>优化器与策略
            </h5>
            <div class="row g-3">
              <!-- 损失函数 -->
              <div class="col-md-6">
                <label class="form-label fw-medium">
                  <i class="fas fa-balance-scale me-1 text-primary"></i>损失函数 *
                </label>
                <select class="form-select form-select-lg" v-model="formData.lossFunction" required>
                  <option value="">请选择损失计算方式</option>
                  <option value="CrossEntropy">交叉熵损失 (分类任务)</option>
                  <option value="MSE">均方误差 (回归任务)</option>
                  <option value="MAE">平均绝对误差</option>
                </select>
              </div>

              <!-- 优化器 -->
              <div class="col-md-6">
                <label class="form-label fw-medium">
                  <i class="fas fa-rocket me-1 text-primary"></i>优化器 *
                </label>
                <select class="form-select form-select-lg" v-model="formData.optimizer" required>
                  <option value="">请选择优化算法</option>
                  <option value="Adam">Adam (自适应矩估计)</option>
                  <option value="SGD">SGD (随机梯度下降)</option>
                  <option value="RMSprop">RMSprop (均方根传播)</option>
                </select>
              </div>

              <!-- 训练策略 -->
              <div class="col-md-6">
                <label class="form-label fw-medium">
                  <i class="fas fa-project-diagram me-1 text-primary"></i>训练策略 *
                </label>
                <select class="form-select form-select-lg" v-model="formData.trainStrategy" required>
                  <option value="">请选择训练方式</option>
                  <option value="split">数据集分割</option>
                  <option value="cross_validation">K折交叉验证</option>
                </select>
              </div>

              <!-- K折数量 -->
              <div class="col-md-6" v-if="formData.trainStrategy === 'cross_validation'">
                <label class="form-label fw-medium">
                  <i class="fas fa-th-large me-1 text-primary"></i>K折数量
                </label>
                <input type="number" class="form-control form-control-lg" v-model="formData.kFold" min="2" max="10">
                <div class="form-text">交叉验证的折数</div>
              </div>
            </div>
          </div>

          <!-- 文件上传与通知 -->
          <div v-show="currentStep === 3" class="step-pane">
            <h5 class="mb-4 pb-2 border-bottom">
              <i class="fas fa-cloud-upload-alt me-2 text-primary"></i>数据上传与通知
            </h5>
            <div class="row g-3">

              <!-- 数据文件上传 -->
              <div class="col-12">
                <label class="form-label fw-medium">
                  <i class="fas fa-file-csv me-1 text-primary"></i>训练数据文件 *
                </label>
                <div class="file-upload-area border rounded-3 p-4 text-center"
                  :class="{ 'border-primary bg-light': isDragging }" @dragover.prevent="handleDragOver"
                  @dragleave.prevent="handleDragLeave" @drop.prevent="handleDrop">
                  <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                  <div class="mb-3">
                    <p class="mb-1">拖拽文件到此处或点击选择</p>
                    <small class="text-muted">支持 .txt 和 .csv 格式，文件大小不超过 100MB</small>
                  </div>
                  <input type="file" class="form-control d-none" ref="fileInput" @change="handleFileUpload"
                    accept=".txt,.csv" required>
                  <button type="button" class="btn btn-outline-primary" @click="$refs.fileInput.click()">
                    <i class="fas fa-folder-open me-2"></i>选择文件
                  </button>
                  <div v-if="uploadedFileName" class="mt-3">
                    <span class="badge bg-success">
                      <i class="fas fa-check-circle me-1"></i>{{ uploadedFileName }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 邮箱通知 -->
              <div class="col-md-8">
                <label class="form-label fw-medium">
                  <i class="fas fa-envelope me-1 text-primary"></i>训练完成通知邮箱
                </label>
                <input type="email" class="form-control form-control-lg" v-model="formData.email"
                  placeholder="请输入您的邮箱地址">
                <div class="form-text">训练完成后将发送详细结果报告</div>
              </div>

              <!-- 项目名称 -->
              <div class="col-md-4">
                <label class="form-label fw-medium">
                  <i class="fas fa-tag me-1 text-primary"></i>项目标识
                </label>
                <input type="text" class="form-control form-control-lg" v-model="formData.projectName" placeholder="可选">
                <div class="form-text">便于识别和管理训练任务</div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- 导航按钮 -->
      <div class="col-12 mt-4">
        <div class="d-flex justify-content-between">
          <button type="button" class="btn btn-outline-secondary btn-lg px-4" @click="prevStep"
            :disabled="currentStep === 0">
            <i class="fas fa-arrow-left me-2"></i>上一步
          </button>

          <div class="step-navigation">
            <button v-if="currentStep < steps.length - 1" type="button" class="btn btn-primary btn-lg px-4"
              @click="nextStep">
              下一步<i class="fas fa-arrow-right ms-2"></i>
            </button>

            <button v-else type="submit" class="btn btn-success btn-lg px-4" :disabled="isSubmitting || !isFormValid">
              <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status"></span>
              <i v-else class="fas fa-rocket me-2"></i>
              {{ isSubmitting ? '训练启动中...' : '开始训练' }}
            </button>
          </div>

          <button type="button" class="btn btn-outline-danger btn-lg px-4" @click="resetForm">
            <i class="fas fa-redo me-2"></i>重置
          </button>
        </div>
      </div>
      </form>
    </div>
  </div>
  </div>
  </div>

  <!-- 训练状态显示 -->
  <div v-if="showTrainingResult" class="training-result-section mt-5 pt-4 border-top">
    <div class="row">
      <div class="col-12">
        <div class="result-header text-center mb-4">
          <h4 class="fw-bold text-primary">
            <i class="fas fa-chart-bar me-2"></i>训练结果详情
          </h4>
          <p class="text-muted">您的模型训练已完成，以下是详细结果</p>
        </div>
      </div>
    </div>

    <div class="row g-4">
      <!-- Job信息卡片 -->
      <div class="col-md-4">
        <div class="card result-summary-card border-0 shadow-sm h-100">
          <div class="card-body text-center">
            <div class="job-id-display mb-3">
              <div class="badge bg-primary-subtle text-primary-emphasis px-4 py-2 fs-6">
                <i class="fas fa-hashtag me-2"></i>{{ jobId }}
              </div>
            </div>
            <div class="status-indicator mb-3">
              <div class="status-badge" :class="'status-' + currentStatus.toLowerCase()">
                <i :class="getStatusIcon(currentStatus) + ' me-2'"></i>
                {{ statusText }}
              </div>
            </div>
            <div class="training-meta">
              <small class="text-muted">
                <i class="fas fa-clock me-1"></i>
                {{ formatDate(new Date()) }}
              </small>
            </div>
          </div>
        </div>
      </div>

      <!-- 性能指标卡片 -->
      <div class="col-md-8">
        <div class="card performance-card border-0 shadow-sm">
          <div class="card-header bg-gradient-success text-white">
            <h5 class="mb-0">
              <i class="fas fa-tachometer-alt me-2"></i>模型性能指标
            </h5>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <div class="metric-box p-3 bg-light rounded">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 class="text-muted mb-1">准确率</h6>
                      <h3 class="text-success mb-0 fw-bold">{{ trainingResults.accuracy }}</h3>
                    </div>
                    <div class="metric-icon bg-success text-white rounded-circle p-2">
                      <i class="fas fa-percentage"></i>
                    </div>
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="metric-box p-3 bg-light rounded">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 class="text-muted mb-1">损失值</h6>
                      <h3 class="text-warning mb-0 fw-bold">{{ trainingResults.loss }}</h3>
                    </div>
                    <div class="metric-icon bg-warning text-white rounded-circle p-2">
                      <i class="fas fa-chart-line"></i>
                    </div>
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="metric-box p-3 bg-light rounded">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 class="text-muted mb-1">训练轮数</h6>
                      <h3 class="text-info mb-0 fw-bold">{{ trainingResults.epochs_trained }}</h3>
                    </div>
                    <div class="metric-icon bg-info text-white rounded-circle p-2">
                      <i class="fas fa-redo"></i>
                    </div>
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="metric-box p-3 bg-light rounded">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 class="text-muted mb-1">训练耗时</h6>
                      <h3 class="text-secondary mb-0 fw-bold">{{ trainingResults.training_time }}</h3>
                    </div>
                    <div class="metric-icon bg-secondary text-white rounded-circle p-2">
                      <i class="fas fa-stopwatch"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细日志和下载区域 -->
    <div class="row mt-4 g-4">
      <!-- 详细日志 -->
      <div class="col-lg-8">
        <div class="card log-card border-0 shadow-sm">
          <div class="card-header bg-dark text-white">
            <h5 class="mb-0">
              <i class="fas fa-terminal me-2"></i>训练日志详情
            </h5>
          </div>
          <div class="card-body p-0">
            <div class="log-container bg-dark text-white p-4" style="max-height: 300px; overflow-y: auto;">
              <pre class="mb-0 text-white"><code>{{ formatLogData(trainingDetails) }}</code></pre>
            </div>
          </div>
        </div>
      </div>

      <!-- 下载选项 -->
      <div class="col-lg-4">
        <div class="card download-card border-0 shadow-sm h-100">
          <div class="card-header bg-primary text-white">
            <h5 class="mb-0">
              <i class="fas fa-download me-2"></i>结果下载
            </h5>
          </div>
          <div class="card-body">
            <div class="d-grid gap-3">
              <button class="btn btn-success btn-lg" @click="downloadResults('model_weights.h5')">
                <i class="fas fa-brain me-2"></i>下载模型权重
              </button>
              <button class="btn btn-info btn-lg" @click="downloadResults('training_history.json')">
                <i class="fas fa-history me-2"></i>训练历史记录
              </button>
              <button class="btn btn-warning btn-lg" @click="downloadResults('evaluation_metrics.csv')">
                <i class="fas fa-table me-2"></i>评估指标表
              </button>
              <button class="btn btn-secondary btn-lg" @click="downloadResults('full_report.pdf')">
                <i class="fas fa-file-pdf me-2"></i>完整报告
              </button>
            </div>

            <div class="mt-4 pt-3 border-top">
              <h6 class="text-muted mb-3">
                <i class="fas fa-share-alt me-2"></i>分享结果
              </h6>
              <div class="d-grid gap-2">
                <button class="btn btn-outline-primary">
                  <i class="fas fa-envelope me-2"></i>邮件分享
                </button>
                <button class="btn btn-outline-success">
                  <i class="fas fa-copy me-2"></i>复制链接
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="row mt-4">
      <div class="col-12 text-center">
        <div class="action-buttons">
          <button class="btn btn-primary btn-lg me-3" @click="startNewTraining">
            <i class="fas fa-plus-circle me-2"></i>新建训练任务
          </button>
          <button class="btn btn-outline-secondary btn-lg" @click="viewTrainingHistory">
            <i class="fas fa-history me-2"></i>查看历史记录
          </button>
        </div>
      </div>
    </div>
  </div>
  </div>
  </section>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, computed } from 'vue'

export default defineComponent({
  name: 'AutoMATATraining',
  setup() {
    // 响应式数据
    const formData = reactive({
      modelType: '',
      epoch: 20,
      learningRate: 0.0001,
      earlyStopping: 10,
      labelCount: 2,
      batchSize: 32,
      randomSeed: 42,
      validationSplit: 20,
      lossFunction: 'CrossEntropy',
      optimizer: 'Adam',
      trainStrategy: 'split',
      kFold: 5,
      email: '',
      projectName: ''
    })

    // 步骤控制
    const currentStep = ref(0)
    const steps = [
      { id: 'basic', label: '基础参数' },
      { id: 'data', label: '数据处理' },
      { id: 'strategy', label: '训练策略' },
      { id: 'upload', label: '文件上传' }
    ]

    // 文件上传相关
    const isDragging = ref(false)
    const uploadedFileName = ref('')
    const fileInput = ref(null)

    const isSubmitting = ref(false)
    const showTrainingResult = ref(false)
    const jobId = ref('')
    const currentStatus = ref('')
    const statusText = ref('初始化中...')
    const trainingResults = ref({})
    const trainingDetails = ref({})
    const trainingForm = ref(null)

    // 计算属性
    const isFormValid = computed(() => {
      return formData.modelType &&
        formData.epoch &&
        formData.learningRate &&
        formData.earlyStopping &&
        formData.labelCount >= 2 &&
        formData.batchSize &&
        formData.lossFunction &&
        formData.optimizer &&
        formData.trainStrategy &&
        uploadedFileName.value
    })

    // 特性数据
    const features = [
      {
        title: '多种神经网络架构',
        description: '支持CNN、LSTM、RNN、MLP等主流深度学习模型',
        icon: 'fas fa-network-wired',
        color: 'primary',
        stats: '4种模型可选'
      },
      {
        title: '高性能训练引擎',
        description: 'GPU加速训练，支持大规模数据集高效处理',
        icon: 'fas fa-bolt',
        color: 'success',
        stats: '训练速度提升3倍'
      },
      {
        title: '智能训练监控',
        description: '实时可视化训练过程，自动调参优化',
        icon: 'fas fa-chart-line',
        color: 'info',
        stats: '99.2%成功率'
      }
    ]

    // 方法
    const scrollToForm = () => {
      trainingForm.value?.scrollIntoView({ behavior: 'smooth' })
    }

    const showDocumentation = () => {
      alert('使用指南功能即将上线，敬请期待！')
    }

    // 步骤导航方法
    const nextStep = () => {
      if (currentStep.value < steps.length - 1) {
        currentStep.value++
      }
    }

    const prevStep = () => {
      if (currentStep.value > 0) {
        currentStep.value--
      }
    }

    // 文件上传处理
    const handleFileUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        if (file.size > 100 * 1024 * 1024) { // 100MB限制
          alert('文件大小不能超过100MB')
          return
        }
        uploadedFileName.value = file.name
        console.log('选择的文件:', file.name, '大小:', (file.size / 1024 / 1024).toFixed(2) + 'MB')
      }
    }

    const handleDragOver = () => {
      isDragging.value = true
    }

    const handleDragLeave = () => {
      isDragging.value = false
    }

    const handleDrop = (event) => {
      isDragging.value = false
      const file = event.dataTransfer.files[0]
      if (file && (file.type === 'text/plain' || file.name.endsWith('.csv'))) {
        if (file.size > 100 * 1024 * 1024) {
          alert('文件大小不能超过100MB')
          return
        }
        uploadedFileName.value = file.name
        // 这里可以添加文件处理逻辑
        console.log('拖拽上传的文件:', file.name)
      } else {
        alert('请上传 .txt 或 .csv 格式的文件')
      }
    }

    const handleSubmit = async () => {
      isSubmitting.value = true

      try {
        // 这里应该发送到后端API
        console.log('提交表单数据:', formData)

        // 模拟提交成功
        jobId.value = '20260205144235_hNFy68cn'
        currentStatus.value = 'Submitted'
        statusText.value = '训练已提交'
        showTrainingResult.value = true

        // 模拟轮询状态更新
        setTimeout(() => {
          currentStatus.value = 'Finished'
          statusText.value = '状态: Finished'
          trainingResults.value = {
            accuracy: '0.95',
            loss: '0.023',
            epochs_trained: '20',
            training_time: '120 seconds'
          }
        }, 3000)

      } catch (error) {
        console.error('提交错误:', error)
        statusText.value = '提交失败'
      } finally {
        isSubmitting.value = false
      }
    }

    const resetForm = () => {
      Object.keys(formData).forEach(key => {
        if (typeof formData[key] === 'string') {
          formData[key] = key === 'modelType' || key === 'lossFunction' || key === 'optimizer' || key === 'trainStrategy' ? '' : formData[key]
        } else if (typeof formData[key] === 'number') {
          formData[key] = key === 'epoch' ? 20 :
            key === 'learningRate' ? 0.0001 :
              key === 'earlyStopping' ? 10 :
                key === 'labelCount' ? 2 :
                  key === 'batchSize' ? 32 :
                    key === 'randomSeed' ? 42 : formData[key]
        }
      })
      showTrainingResult.value = false
      jobId.value = ''
      currentStatus.value = ''
      statusText.value = '初始化中...'
      trainingResults.value = {}
      trainingDetails.value = {}
    }

    const downloadResults = async (fileName) => {
      try {
        // 这里应该调用实际的下载API
        console.log('下载文件:', fileName)

        // 模拟下载过程
        const link = document.createElement('a')
        link.href = '#' // 实际应该是API返回的文件URL
        link.download = fileName
        link.click()

        // 显示成功提示
        alert(`文件 ${fileName} 开始下载！`)
      } catch (error) {
        console.error('下载错误:', error)
        alert(`下载失败: ${error.message}`)
      }
    }

    // 新增的状态管理方法
    const getStatusIcon = (status) => {
      const statusIcons = {
        'Submitted': 'fas fa-paper-plane',
        'Running': 'fas fa-spinner fa-spin',
        'Finished': 'fas fa-check-circle',
        'Failed': 'fas fa-exclamation-triangle',
        'Cancelled': 'fas fa-times-circle'
      }
      return statusIcons[status] || 'fas fa-question-circle'
    }

    const formatDate = (date) => {
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }

    const formatLogData = (details) => {
      if (Object.keys(details).length === 0) {
        return '暂无详细日志信息'
      }

      let logText = ''
      Object.entries(details).forEach(([key, value]) => {
        logText += `${key}: ${value}\n`
      })
      return logText
    }

    const startNewTraining = () => {
      resetForm()
      scrollToForm()
    }

    const viewTrainingHistory = () => {
      alert('训练历史功能即将上线，敬请期待！')
    }

    // 返回需要暴露给模板的数据和方法
    return {
      // 数据
      formData,
      currentStep,
      steps,
      isDragging,
      uploadedFileName,
      fileInput,
      isSubmitting,
      showTrainingResult,
      jobId,
      currentStatus,
      statusText,
      trainingResults,
      trainingDetails,
      trainingForm,
      features,

      // 计算属性
      isFormValid,

      // 方法
      scrollToForm,
      showDocumentation,
      nextStep,
      prevStep,
      handleFileUpload,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      handleSubmit,
      resetForm,
      downloadResults,
      getStatusIcon,
      formatDate,
      formatLogData,
      startNewTraining,
      viewTrainingHistory
    }
  }
})
</script>

<style scoped>
/* 主题颜色定义 */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.hero-section {
  background: var(--primary-gradient);
  color: white;
  padding: 100px 0 60px 0;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
}

.hero-icon-wrapper {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-10px);
  }
}

.animated-icon {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 0.7;
  }

  50% {
    opacity: 1;
  }
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.features-section {
  background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
  padding: 80px 0;
}

.feature-card {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  height: 100%;
  border-radius: 15px;
  overflow: hidden;
}

.feature-card:hover {
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.hover-lift:hover {
  transform: translateY(-8px);
}

.feature-icon-wrapper {
  position: relative;
}

.feature-icon-wrapper::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.1;
  animation: ripple 2s infinite;
}

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 0.1;
  }

  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.form-section {
  background: #fafbff;
  padding: 60px 0;
}

.training-card {
  border-radius: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.training-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}

.bg-gradient-primary {
  background: var(--primary-gradient) !important;
}

/* 步骤指示器样式 */
.progress-steps {
  position: relative;
}

.progress-steps::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 0;
  right: 0;
  height: 3px;
  background: #e9ecef;
  z-index: 1;
}

.step-indicator {
  text-align: center;
  position: relative;
  z-index: 2;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin: 0 auto 10px;
  transition: all 0.3s ease;
}

.step-label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.step-indicator.active .step-number {
  background: #0d6efd;
  color: white;
  transform: scale(1.1);
}

.step-indicator.completed .step-number {
  background: #198754;
  color: white;
}

.step-indicator.completed .step-label {
  color: #198754;
}

/* 文件上传区域样式 */
.file-upload-area {
  transition: all 0.3s ease;
  cursor: pointer;
}

.file-upload-area:hover {
  border-color: #0d6efd !important;
  background-color: #f8f9ff !important;
}

.file-upload-area.border-primary {
  border-style: dashed !important;
}

/* 表单元素增强 */
.form-control-lg,
.form-select-lg {
  padding: 1rem 1.25rem;
  font-size: 1rem;
}

.form-label.fw-medium {
  font-weight: 500;
  color: #495057;
}

/* 按钮动画效果 */
.btn {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.btn::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.btn:active::after {
  width: 300px;
  height: 300px;
}

.btn-primary {
  background: var(--primary-gradient);
  border: none;
}

.btn-success {
  background: var(--success-gradient);
  border: none;
}

.card-header .icon-wrapper {
  animation: bounce 2s infinite;
}

@keyframes bounce {

  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }

  40% {
    transform: translateY(-10px);
  }

  60% {
    transform: translateY(-5px);
  }
}

/* 结果卡片样式 */
.result-card {
  border: 1px solid #dee2e6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.result-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.result-item {
  margin-bottom: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f1f3f5;
}

.result-item:last-child {
  border-bottom: none;
}

/* 响应式设计增强 */
@media (max-width: 768px) {
  .hero-section {
    padding: 70px 0 40px 0;
  }

  .container {
    padding: 0 15px;
  }

  .display-4 {
    font-size: 2.2rem;
  }

  .lead {
    font-size: 1.1rem;
  }

  .btn-lg {
    padding: 0.75rem 1.5rem;
    font-size: 1.1rem;
  }

  .feature-card {
    margin-bottom: 20px;
  }

  .step-indicator .step-label {
    font-size: 0.75rem;
  }

  .d-flex.justify-content-between {
    flex-direction: column;
    gap: 15px;
  }

  .step-navigation {
    order: -1;
  }
}

@media (max-width: 576px) {
  .hero-section {
    padding: 50px 0 30px 0;
  }

  .container {
    padding: 0 10px;
  }

  .display-4 {
    font-size: 1.8rem;
  }

  .btn {
    width: 100%;
    margin-bottom: 10px;
  }

  .form-control-lg,
  .form-select-lg {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }

  .step-indicator {
    flex: 1;
    min-width: 60px;
  }

  .progress-steps {
    flex-wrap: wrap;
    gap: 10px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-section {
    padding: 60px 0 30px 0;
  }

  .container {
    padding: 0 15px;
  }

  .display-4 {
    font-size: 2rem;
  }

  .lead {
    font-size: 1rem;
  }

  .btn-lg {
    padding: 0.5rem 1rem;
    font-size: 1rem;
  }
}

@media (max-width: 576px) {
  .hero-section {
    padding: 40px 0 20px 0;
  }

  .container {
    padding: 0 10px;
  }

  .display-4 {
    font-size: 1.5rem;
  }

  .btn {
    width: 100%;
    margin-bottom: 10px;
  }
}
</style>