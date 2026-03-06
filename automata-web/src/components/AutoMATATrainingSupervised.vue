<template>
    <div class="automata-training-supervised">
        <!-- 监督学习训练表单 -->
        <div class="container-fluid p-4">
            <div class="row justify-content-center">
                <div class="col-12 col-lg-10">
                    <div class="card border-0 shadow">
                        <div class="card-header bg-primary text-white py-3">
                            <h4 class="mb-0 text-center">
                                <i class="fas fa-cogs me-2"></i>Train Your Supervised Model
                            </h4>
                        </div>
                        <div class="card-body p-4">
                            <form @submit.prevent="handleSubmit" class="train_form" enctype="multipart/form-data">

                                <!-- 步骤1：选择策略并上传文件 -->
                                <div class="step-section mb-4">
                                    <h5 class="step-title">
                                        <span class="step-number">1</span>
                                        Select strategy and upload files
                                    </h5>

                                    <div class="strategy-options mb-4">
                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="radio" name="strategy"
                                                id="splitStrategy" value="split" v-model="strategy"
                                                @change="handleStrategyChange" checked>
                                            <label class="form-check-label" for="splitStrategy">
                                                Upload a dataset to conduct train/validation/testing split
                                            </label>
                                        </div>

                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="radio" name="strategy"
                                                id="uploadStrategy" value="upload" v-model="strategy"
                                                @change="handleStrategyChange">
                                            <label class="form-check-label" for="uploadStrategy">
                                                Upload train/validation/testing datasets respectively
                                            </label>
                                        </div>

                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="strategy"
                                                id="kfoldStrategy" value="kfold" v-model="strategy"
                                                @change="handleStrategyChange">
                                            <label class="form-check-label" for="kfoldStrategy">
                                                Upload a dataset to conduct K-Fold cross-validation
                                            </label>
                                        </div>
                                    </div>

                                    <!-- 数据集上传区域 -->
                                    <div class="upload-section" v-if="strategy === 'split'">
                                        <div class="mb-3">
                                            <label class="form-label">Upload dataset</label>
                                            <input type="file" class="form-control"
                                                @change="handleFileUpload($event, 'dataset')"
                                                accept=".txt,.csv,.xlsx,.xls" required>
                                            <div v-if="uploadedFiles.dataset" class="mt-2">
                                                <span class="badge bg-success">
                                                    <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.dataset }}
                                                </span>
                                            </div>
                                        </div>

                                        <div class="row g-3">
                                            <div class="col-md-4">
                                                <label class="form-label">Training ratio</label>
                                                <input type="number" class="form-control" v-model="splitRatio.train"
                                                    min="0" max="100" @input="updateRatios">
                                                <small class="form-text text-muted">%</small>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Validation ratio</label>
                                                <input type="number" class="form-control"
                                                    v-model="splitRatio.validation" min="0" max="100"
                                                    @input="updateRatios">
                                                <small class="form-text text-muted">%</small>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Testing ratio</label>
                                                <input type="number" class="form-control" v-model="splitRatio.test"
                                                    min="0" max="100" readonly>
                                                <small class="form-text text-muted">%</small>
                                            </div>
                                        </div>
                                        <div class="ratio-display mt-2">
                                            <small class="text-muted">Current ratio: {{ ratioDisplay }}</small>
                                        </div>
                                    </div>

                                    <!-- 分别上传区域 -->
                                    <div class="upload-section" v-if="strategy === 'upload'">
                                        <div class="row g-3">
                                            <div class="col-md-4">
                                                <label class="form-label">Training set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'train')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                                <div v-if="uploadedFiles.train" class="mt-2">
                                                    <span class="badge bg-success">{{ uploadedFiles.train }}</span>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Validation set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'validation')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                                <div v-if="uploadedFiles.validation" class="mt-2">
                                                    <span class="badge bg-success">{{ uploadedFiles.validation }}</span>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Testing set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'test')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                                <div v-if="uploadedFiles.test" class="mt-2">
                                                    <span class="badge bg-success">{{ uploadedFiles.test }}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- K折交叉验证区域 -->
                                    <div class="upload-section" v-if="strategy === 'kfold'">
                                        <div class="mb-3">
                                            <label class="form-label">Upload dataset</label>
                                            <input type="file" class="form-control"
                                                @change="handleFileUpload($event, 'kfoldDataset')"
                                                accept=".txt,.csv,.xlsx,.xls" required>
                                            <div v-if="uploadedFiles.kfoldDataset" class="mt-2">
                                                <span class="badge bg-success">{{ uploadedFiles.kfoldDataset }}</span>
                                            </div>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">K value</label>
                                            <input type="number" class="form-control" v-model="kfoldValue" min="2"
                                                max="10" placeholder="5">
                                        </div>
                                    </div>
                                </div>

                                <!-- 步骤2：选择模型 -->
                                <div class="step-section mb-4">
                                    <h5 class="step-title">
                                        <span class="step-number">2</span>
                                        Choose model
                                    </h5>

                                    <div class="model-selection">
                                        <div class="row">
                                            <div class="col-md-6 mb-3" v-for="model in availableModels" :key="model.id">
                                                <div class="model-card"
                                                    :class="{ 'selected': selectedModel === model.id }"
                                                    @click="selectModel(model.id)">
                                                    <div class="model-header">
                                                        <input class="form-check-input me-2" type="radio"
                                                            :id="'model_' + model.id" :value="model.id"
                                                            v-model="selectedModel" name="modelType">
                                                        <label class="form-check-label fw-bold"
                                                            :for="'model_' + model.id">
                                                            {{ model.name }}
                                                        </label>
                                                    </div>
                                                    <div class="model-description mt-2">
                                                        <small class="text-muted">{{ model.description }}</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 步骤3：上传训练超参数 -->
                                <div class="step-section mb-4">
                                    <h5 class="step-title">
                                        <span class="step-number">3</span>
                                        Upload training hyperparameters
                                    </h5>

                                    <div class="hyperparameters-form">
                                        <div class="row g-3">
                                            <div class="col-md-4">
                                                <label class="form-label">Epoch *</label>
                                                <input type="number" class="form-control" id="epoch"
                                                    v-model="hyperparameters.epoch" min="1" max="1000" required>
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Learning Rate *</label>
                                                <input type="number" class="form-control" id="lr"
                                                    v-model="hyperparameters.learningRate" step="0.001" min="0.001"
                                                    max="1" required>
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">EarlyStopping Patience *</label>
                                                <input type="number" class="form-control" id="es"
                                                    v-model="hyperparameters.earlyStopping" min="1" max="100" required>
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Batch Size</label>
                                                <input type="number" class="form-control"
                                                    v-model="hyperparameters.batchSize" min="1" max="1024">
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Random Seed</label>
                                                <input type="number" class="form-control"
                                                    v-model="hyperparameters.randomSeed" min="0" max="999999">
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Label Count</label>
                                                <input type="number" class="form-control"
                                                    v-model="hyperparameters.labelCount" min="2" max="1000">
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 通知信息 -->
                                <div class="notification-section mb-4">
                                    <h5 class="section-title">Notification</h5>
                                    <div class="row g-3">
                                        <div class="col-12">
                                            <label class="form-label">Email *</label>
                                            <input type="email" class="form-control" id="email"
                                                v-model="notification.email"
                                                placeholder="Please input your email address" required>
                                        </div>
                                    </div>
                                </div>

                                <!-- 提交按钮 -->
                                <div class="submission-section">
                                    <div class="d-grid gap-2">
                                        <button type="submit" class="btn btn-primary btn-lg"
                                            :disabled="isSubmitting || !isFormValid">
                                            <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"
                                                role="status"></span>
                                            {{ isSubmitting ? 'Submitting...' : 'Start Training' }}
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary" @click="resetForm">Reset
                                            Form</button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 训练结果展示 -->
            <div v-if="showTrainingResult" class="row justify-content-center mt-4">
                <div class="col-12 col-lg-10">
                    <div class="card border-0 shadow">
                        <div class="card-header bg-success text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-check-circle me-2"></i>Training Result
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Job ID:</strong> {{ jobId }}</p>
                                    <p><strong>Status:</strong> {{ statusText }}</p>
                                    <p><strong>Model:</strong> {{ getModelName(selectedModel) }}</p>
                                </div>
                                <div class="col-md-6" v-if="Object.keys(trainingResults).length > 0">
                                    <p><strong>Accuracy:</strong> {{ trainingResults.accuracy }}</p>
                                    <p><strong>Loss:</strong> {{ trainingResults.loss }}</p>
                                    <p><strong>Epochs Trained:</strong> {{ trainingResults.epochs_trained }}</p>
                                    <p><strong>Training Time:</strong> {{ trainingResults.training_time }}</p>
                                </div>
                            </div>
                            <div class="mt-3">
                                <button class="btn btn-primary me-2" @click="startNewTraining">New Training</button>
                                <button class="btn btn-outline-secondary"
                                    @click="showTrainingResult = false">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { defineComponent, ref, reactive, computed } from 'vue'

export default defineComponent({
    name: 'AutoMATATrainingSupervised',
    setup() {
        // 响应式数据
        const strategy = ref('split')
        const selectedModel = ref('cnn')
        const kfoldValue = ref(5)

        const uploadedFiles = reactive({
            dataset: '',
            train: '',
            validation: '',
            test: '',
            kfoldDataset: ''
        })

        const splitRatio = reactive({
            train: 80,
            validation: 10,
            test: 10
        })

        const hyperparameters = reactive({
            epoch: 20,
            learningRate: 0.001,
            earlyStopping: 10,
            batchSize: 32,
            randomSeed: 42,
            labelCount: 2
        })

        const notification = reactive({
            email: ''
        })

        const isSubmitting = ref(false)
        const showTrainingResult = ref(false)
        const jobId = ref('')
        const currentStatus = ref('')
        const statusText = ref('Initializing...')
        const trainingResults = ref({})

        // 可用模型
        const availableModels = [
            {
                id: 'cnn',
                name: 'CNN',
                description: 'CNN Excels at extracting discriminative features from 1D signals with local patterns (e.g., mass spectrometry)'
            },
            {
                id: 'lstm',
                name: 'LSTM',
                description: 'LSTM Captures long-range dependencies in sequential data, ideal for time-series analysis'
            },
            {
                id: 'rnn',
                name: 'RNN',
                description: 'RNN Processes sequential data with recurrent connections, suitable for variable-length sequences'
            },
            {
                id: 'mlp',
                name: 'MLP',
                description: 'MLP Traditional feedforward neural network for tabular data and feature engineering'
            }
        ]

        // 计算属性
        const ratioDisplay = computed(() => {
            return `${splitRatio.train}:${splitRatio.validation}:${splitRatio.test}`
        })

        const isFormValid = computed(() => {
            // 检查基本必填项
            const basicValid = selectedModel.value &&
                hyperparameters.epoch &&
                hyperparameters.learningRate &&
                hyperparameters.earlyStopping &&
                notification.email

            // 根据策略检查文件上传
            let filesValid = false
            if (strategy.value === 'split') {
                filesValid = uploadedFiles.dataset
            } else if (strategy.value === 'upload') {
                filesValid = uploadedFiles.train && uploadedFiles.validation && uploadedFiles.test
            } else if (strategy.value === 'kfold') {
                filesValid = uploadedFiles.kfoldDataset && kfoldValue.value
            }

            return basicValid && filesValid
        })

        // 方法
        const handleFileUpload = (event, fileType) => {
            const file = event.target.files[0]
            if (file) {
                // 检查文件格式
                const allowedExtensions = ['txt', 'csv', 'xlsx', 'xls']
                const fileExtension = file.name.split('.').pop().toLowerCase()

                if (!allowedExtensions.includes(fileExtension)) {
                    alert('Please upload a txt, csv or excel file!')
                    event.target.value = ''
                    return
                }

                if (file.size > 100 * 1024 * 1024) {
                    alert('File size cannot exceed 100MB')
                    event.target.value = ''
                    return
                }

                uploadedFiles[fileType] = file.name
                console.log(`Uploaded ${fileType} file:`, file.name)
            }
        }

        const handleStrategyChange = () => {
            // 清空之前上传的文件
            Object.keys(uploadedFiles).forEach(key => {
                uploadedFiles[key] = ''
            })
        }

        const updateRatios = () => {
            const total = splitRatio.train + splitRatio.validation
            if (total <= 100) {
                splitRatio.test = 100 - total
            } else {
                splitRatio.train = 80
                splitRatio.validation = 10
                splitRatio.test = 10
            }
        }

        const selectModel = (modelId) => {
            selectedModel.value = modelId
        }

        const getModelName = (modelId) => {
            const model = availableModels.find(m => m.id === modelId)
            return model ? model.name : ''
        }

        const handleSubmit = async () => {
            isSubmitting.value = true

            try {
                // 验证表单
                if (!checkInput()) {
                    isSubmitting.value = false
                    return
                }

                console.log('Submitting form data:', {
                    strategy: strategy.value,
                    selectedModel: selectedModel.value,
                    hyperparameters: hyperparameters,
                    uploadedFiles: uploadedFiles,
                    splitRatio: splitRatio,
                    kfoldValue: kfoldValue.value
                })

                // 模拟提交成功
                jobId.value = 'TASK_' + Date.now()
                currentStatus.value = 'Submitted'
                statusText.value = 'Training submitted'
                showTrainingResult.value = true

                // 模拟训练完成
                setTimeout(() => {
                    currentStatus.value = 'Finished'
                    statusText.value = 'Training completed'
                    trainingResults.value = {
                        accuracy: '0.95',
                        loss: '0.023',
                        epochs_trained: '20',
                        training_time: '120 seconds'
                    }
                }, 2000)

            } catch (error) {
                console.error('Submission error:', error)
                statusText.value = 'Submission failed'
            } finally {
                isSubmitting.value = false
            }
        }

        const checkInput = () => {
            // 检查邮箱格式
            const emailRegex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i
            if (!emailRegex.test(notification.email)) {
                alert("Please submit the correct email address")
                return false
            }

            return true
        }

        const resetForm = () => {
            // 重置表单数据
            strategy.value = 'split'
            selectedModel.value = 'cnn'
            kfoldValue.value = 5

            Object.keys(uploadedFiles).forEach(key => {
                uploadedFiles[key] = ''
            })

            splitRatio.train = 80
            splitRatio.validation = 10
            splitRatio.test = 10

            hyperparameters.epoch = 20
            hyperparameters.learningRate = 0.001
            hyperparameters.earlyStopping = 10
            hyperparameters.batchSize = 32
            hyperparameters.randomSeed = 42
            hyperparameters.labelCount = 2

            notification.email = ''

            showTrainingResult.value = false
            jobId.value = ''
            currentStatus.value = ''
            statusText.value = 'Initializing...'
            trainingResults.value = {}
        }

        const startNewTraining = () => {
            resetForm()
        }

        return {
            // 数据
            strategy,
            selectedModel,
            kfoldValue,
            uploadedFiles,
            splitRatio,
            hyperparameters,
            notification,
            isSubmitting,
            showTrainingResult,
            jobId,
            currentStatus,
            statusText,
            trainingResults,
            availableModels,

            // 计算属性
            ratioDisplay,
            isFormValid,

            // 方法
            handleFileUpload,
            handleStrategyChange,
            updateRatios,
            selectModel,
            getModelName,
            handleSubmit,
            checkInput,
            resetForm,
            startNewTraining
        }
    }
})
</script>

<style scoped>
.automata-training-supervised {
    min-height: 100vh;
    background-color: #f5f5f5;
    /* 浅灰色背景 */
}

.card {
    border-radius: 10px;
    border: 1px solid #e0e0e0;
}

.step-section {
    border-left: 4px solid #9c88ff;
    /* 淡紫色步骤边框 */
    padding-left: 20px;
    margin-bottom: 2rem;
}

.step-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #9c88ff;
    /* 淡紫色标题 */
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
}

.step-number {
    background-color: #9c88ff;
    /* 淡紫色数字背景 */
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 10px;
    font-size: 0.9rem;
    font-weight: bold;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #333333;
    /* 深灰色标题 */
    margin-bottom: 1rem;
}

.model-card {
    border: 2px solid #e0e0e0;
    /* 浅灰色边框 */
    border-radius: 8px;
    padding: 15px;
    cursor: pointer;
    transition: all 0.3s ease;
    height: 100%;
    background-color: #fafafa;
    /* 浅灰背景 */
}

.model-card:hover {
    border-color: #9c88ff;
    /* 淡紫色悬停边框 */
    box-shadow: 0 2px 8px rgba(156, 136, 255, 0.2);
    /* 淡紫色阴影 */
}

.model-card.selected {
    border-color: #9c88ff;
    /* 淡紫色选中边框 */
    background-color: rgba(156, 136, 255, 0.1);
    /* 淡紫色背景 */
}

.model-header {
    display: flex;
    align-items: center;
}

.model-description {
    min-height: 60px;
    color: #666666;
    /* 中灰色文字 */
}

.form-label {
    font-weight: 500;
    color: #444444;
    /* 深灰色标签 */
}

/* 淡紫色主按钮 */
.btn-primary {
    background-color: #9c88ff;
    border-color: #9c88ff;
    color: white;
}

.btn-primary:hover {
    background-color: #8a77e0;
    /* 稍深的淡紫色 */
    border-color: #8a77e0;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(156, 136, 255, 0.3);
}

/* 灰色次要按钮 */
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
    background-color: #9c88ff;
    /* 淡紫色徽章 */
    font-size: 0.875rem;
}

.ratio-display {
    background-color: #f0f0f0;
    /* 浅灰色显示区域 */
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid #dddddd;
    color: #555555;
}

.upload-section {
    background-color: #f8f8f8;
    /* 浅灰色上传区域 */
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
    border-color: #9c88ff;
    box-shadow: 0 0 0 0.2rem rgba(156, 136, 255, 0.25);
}

.form-check-input:checked {
    background-color: #9c88ff;
    border-color: #9c88ff;
}

/* 卡片头部淡紫色 */
.card-header {
    background: linear-gradient(135deg, #9c88ff 0%, #b1a2ff 100%);
    /* 淡紫色渐变 */
    border-bottom: none;
}

/* 成功状态淡紫色 */
.bg-success {
    background-color: #9c88ff !important;
}

.text-success {
    color: #9c88ff !important;
}

/* 输入框悬停效果 */
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