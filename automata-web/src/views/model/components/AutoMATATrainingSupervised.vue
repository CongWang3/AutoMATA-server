<template>
    <div class="automata-training-supervised">
        <!-- 监督学习训练表单 -->
        <div class="container-fluid p-4">
            <div class="row justify-content-center">
                <div class="col-12 col-lg-10">
                    <div class="card border-0 shadow">
                        <div class="card-header bg-primary text-white py-3">
                            <h4 class="mb-0 text-center">
                                Train Your Supervised Model
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
                                            <!-- 上传进度条 -->
                                            <div v-if="uploadProgress.dataset > 0 && uploadProgress.dataset < 100"
                                                class="mt-2">
                                                <div class="progress">
                                                    <div class="progress-bar" role="progressbar"
                                                        :style="{ width: uploadProgress.dataset + '%' }">
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
                                        <label class="form-label">Current ratio</label>
                                        <div class="ratio-controls d-flex align-items-center">
                                            <div class="ratio-item d-flex align-items-center me-4">
                                                <label class="ratio-label me-2">Training:</label>
                                                <input type="number" class="form-control ratio-input text-center"
                                                    v-model="splitRatio.train" min="1" max="10" step="1"
                                                    @input="updateRatios" style="width: 180px;">
                                            </div>
                                            <span class="ratio-separator me-4">-</span>
                                            <div class="ratio-item d-flex align-items-center me-4">
                                                <label class="ratio-label me-2">Validation:</label>
                                                <input type="number" class="form-control ratio-input text-center"
                                                    v-model="splitRatio.validation" min="1" max="10" step="1"
                                                    @input="updateRatios" style="width: 180px;">
                                            </div>
                                            <span class="ratio-separator me-4">-</span>
                                            <div class="ratio-item d-flex align-items-center">
                                                <label class="ratio-label me-2">Testing:</label>
                                                <input type="number" class="form-control ratio-input text-center"
                                                    v-model="splitRatio.test" min="1" max="10" step="1" readonly
                                                    style="width: 180px; background-color: #e9ecef;">
                                            </div>
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
                                                <!-- 上传进度条 -->
                                                <div v-if="uploadProgress.train > 0 && uploadProgress.train < 100"
                                                    class="mt-2">
                                                    <div class="progress">
                                                        <div class="progress-bar" role="progressbar"
                                                            :style="{ width: uploadProgress.train + '%' }">
                                                            {{ uploadProgress.train }}%
                                                        </div>
                                                    </div>
                                                </div>
                                                <div v-if="uploadedFiles.train" class="mt-2">
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.train
                                                        }}
                                                    </span>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Validation set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'validation')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                                <!-- 上传进度条 -->
                                                <div v-if="uploadProgress.validation > 0 && uploadProgress.validation < 100"
                                                    class="mt-2">
                                                    <div class="progress">
                                                        <div class="progress-bar" role="progressbar"
                                                            :style="{ width: uploadProgress.validation + '%' }">
                                                            {{ uploadProgress.validation }}%
                                                        </div>
                                                    </div>
                                                </div>
                                                <div v-if="uploadedFiles.validation" class="mt-2">
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-check-circle me-1"></i>{{
                                                            uploadedFiles.validation }}
                                                    </span>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Testing set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'test')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                                <!-- 上传进度条 -->
                                                <div v-if="uploadProgress.test > 0 && uploadProgress.test < 100"
                                                    class="mt-2">
                                                    <div class="progress">
                                                        <div class="progress-bar" role="progressbar"
                                                            :style="{ width: uploadProgress.test + '%' }">
                                                            {{ uploadProgress.test }}%
                                                        </div>
                                                    </div>
                                                </div>
                                                <div v-if="uploadedFiles.test" class="mt-2">
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.test }}
                                                    </span>
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
                                            <!-- 上传进度条 -->
                                            <div v-if="uploadProgress.kfoldDataset > 0 && uploadProgress.kfoldDataset < 100"
                                                class="mt-2">
                                                <div class="progress">
                                                    <div class="progress-bar" role="progressbar"
                                                        :style="{ width: uploadProgress.kfoldDataset + '%' }">
                                                        {{ uploadProgress.kfoldDataset }}%
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-if="uploadedFiles.kfoldDataset" class="mt-2">
                                                <span class="badge bg-success">
                                                    <i class="fas fa-check-circle me-1"></i>{{
                                                        uploadedFiles.kfoldDataset }}
                                                </span>
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
                                    <div class="step-header d-flex justify-content-between align-items-center">
                                        <h5 class="step-title mb-0">
                                            <span class="step-number">2</span>
                                            Choose model
                                        </h5>
                                        <button type="button" class="btn btn-outline-primary btn-sm"
                                            :class="{ 'active': isAllSelected }" @click="selectAllModels">
                                            <i class="fas fa-check-square me-1" v-if="isAllSelected"></i>
                                            <i class="far fa-square me-1" v-else></i>
                                            All
                                        </button>
                                    </div>

                                    <div class="model-selection mt-3">
                                        <div v-if="loadingModels" class="text-center py-4">
                                            <div class="spinner-border text-primary" role="status">
                                                <span class="visually-hidden">加载中...</span>
                                            </div>
                                            <p class="mt-2 text-muted">正在加载可用模型...</p>
                                        </div>

                                        <div v-else class="row">
                                            <div v-if="availableModels && availableModels.length > 0">
                                                <p class="text-muted mb-3">共找到 {{ availableModels.length }} 个可用模型
                                                </p>
                                            </div>
                                            <div v-else>
                                                <p class="text-warning">暂无可用模型</p>
                                            </div>
                                            <div class="col-md-6 mb-3" v-for="model in availableModels" :key="model.id">
                                                <div class="model-card"
                                                    :class="{ 'selected': selectedModels.includes(model.id) }"
                                                    @click="toggleModelSelection(model.id)">
                                                    <div class="model-header">
                                                        <input class="form-check-input me-2" type="checkbox"
                                                            :id="'model_' + model.id"
                                                            :checked="selectedModels.includes(model.id)"
                                                            @change="toggleModelSelection(model.id)">
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

                                        <div class="all-models-info mt-3 p-3 bg-light rounded">
                                            <small class="text-muted">
                                                <!-- <i class="fas fa-info-circle me-1"></i> -->
                                                All the above models are trained in parallel using the same set of data
                                            </small>
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
import { defineComponent, ref, reactive, computed, onMounted } from 'vue'
import { trainingApi, MODEL_PARAMETERS } from '@/api'

export default defineComponent({
    name: 'AutoMATATrainingSupervised',
    setup() {
        // 响应式数据
        const strategy = ref('split')
        const selectedModels = ref(['cnn']) // 默认选择CNN
        const kfoldValue = ref(5)

        const uploadedFiles = reactive({
            dataset: '',
            train: '',
            validation: '',
            test: '',
            kfoldDataset: ''
        })

        // 文件上传进度
        const uploadProgress = reactive({
            dataset: 0,
            train: 0,
            validation: 0,
            test: 0,
            kfoldDataset: 0
        })

        // 已上传文件信息
        const uploadedFileInfo = reactive({
            dataset: null,
            train: null,
            validation: null,
            test: null,
            kfoldDataset: null
        })

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

        // 可用模型 - 从API获取
        const availableModels = ref([])
        const loadingModels = ref(false)

        // 任务轮询控制
        let pollingInterval = null

        // 计算属性
        const ratioDisplay = computed(() => {
            return `${splitRatio.train}:${splitRatio.validation}:${splitRatio.test}`
        })

        const simplifiedRatioDisplay = computed(() => {
            // 计算最大公约数
            const gcd = (a, b) => {
                return b === 0 ? a : gcd(b, a % b)
            }

            const total = splitRatio.train + splitRatio.validation + splitRatio.test
            if (total === 0) return '0:0:0'

            // 计算简化比例
            const trainPart = Math.round((splitRatio.train / total) * 10)
            const validationPart = Math.round((splitRatio.validation / total) * 10)
            let testPart = 10 - trainPart - validationPart

            // 确保总和为10
            if (testPart < 0) testPart = 0

            return `${trainPart}:${validationPart}:${testPart}`
        })

        const isAllSelected = computed(() => {
            return selectedModels.value.length === availableModels.value.length
        })

        const isFormValid = computed(() => {
            // 检查基本必填项
            const basicValid = selectedModels.value.length > 0 &&
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
        const handleFileUpload = async (event, fileType) => {
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

                try {
                    // 重置进度
                    uploadProgress[fileType] = 0

                    // 上传文件到后端
                    const fileInfo = await trainingApi.uploadFile(file, fileType, (progressEvent) => {
                        if (progressEvent.total) {
                            uploadProgress[fileType] = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                        }
                    })

                    // 保存文件信息
                    uploadedFileInfo[fileType] = fileInfo
                    uploadedFiles[fileType] = file.name

                    console.log(`Uploaded ${fileType} file:`, file.name, 'File ID:', fileInfo.id)
                    console.log('uploadedFileInfo:', uploadedFileInfo)
                    console.log('Current strategy:', strategy.value)

                } catch (error) {
                    console.error('文件上传失败:', error)
                    alert('文件上传失败: ' + error.message)
                    event.target.value = ''
                }
            }
        }

        const handleStrategyChange = () => {
            // 清空之前上传的文件
            Object.keys(uploadedFiles).forEach(key => {
                uploadedFiles[key] = ''
                uploadProgress[key] = 0
                uploadedFileInfo[key] = null
            })
        }

        const updateRatios = () => {
            const total = splitRatio.train + splitRatio.validation
            if (total <= 10) {
                splitRatio.test = 10 - total
            } else {
                // 如果总和超过10，按比例调整
                const ratioSum = splitRatio.train + splitRatio.validation
                splitRatio.train = Math.round((splitRatio.train / ratioSum) * 10)
                splitRatio.validation = 10 - splitRatio.train
                splitRatio.test = 0
            }
        }

        const selectModel = (modelId) => {
            const index = selectedModels.value.indexOf(modelId)
            if (index > -1) {
                selectedModels.value.splice(index, 1)
            } else {
                selectedModels.value.push(modelId)
            }
        }

        const toggleModelSelection = (modelId) => {
            const index = selectedModels.value.indexOf(modelId)
            if (index > -1) {
                selectedModels.value.splice(index, 1)
            } else {
                selectedModels.value.push(modelId)
            }
        }

        const selectAllModels = () => {
            if (isAllSelected.value) {
                selectedModels.value = []
            } else {
                selectedModels.value = availableModels.value.map(model => model.id)
            }
        }

        const isSelected = (modelId) => {
            return selectedModels.value.includes(modelId)
        }

        const getModelNames = () => {
            return selectedModels.value.map(id => {
                const model = availableModels.value.find(m => m.id === id)
                return model ? model.name : ''
            }).join(', ')
        }

        const getModelName = (modelId) => {
            const model = availableModels.value.find(m => m.id === modelId)
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

                // 准备训练任务数据
                const taskData = {
                    task_name: `Supervised Training - ${getModelNames()}`,
                    model_type: selectedModels.value[0], // 使用第一个选中的模型
                    language: 'python',
                    parameters: JSON.stringify({
                        epochs: hyperparameters.epoch,
                        learning_rate: hyperparameters.learningRate,
                        early_stopping: hyperparameters.earlyStopping,
                        batch_size: hyperparameters.batchSize,
                        random_seed: hyperparameters.randomSeed,
                        label_count: hyperparameters.labelCount,
                        strategy: strategy.value,
                        split_ratio: splitRatio,
                        kfold_value: kfoldValue.value
                    }),
                    // 使用文件ID作为数据集路径，后端会自动关联文件
                    dataset_path: getDatasetPathWithFileIds(),
                    created_by: 1 // 实际应用中应从认证获取
                }

                console.log('Submitting training task:', taskData)
                console.log('Dataset path with file IDs:', getDatasetPathWithFileIds())
                console.log('Original dataset path:', getDatasetPath())

                // 调用API创建训练任务
                const result = await trainingApi.createTask(taskData)

                jobId.value = result.id
                currentStatus.value = 'Submitted'
                statusText.value = 'Training task submitted'
                showTrainingResult.value = true

                // 启动任务状态轮询
                pollTaskStatus(result.id)

            } catch (error) {
                console.error('Submission error:', error)
                statusText.value = 'Submission failed: ' + error.message
                alert('提交失败: ' + error.message)
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
            selectedModels.value = ['cnn'] // 修正：重置为数组形式
            kfoldValue.value = 5

            // 重置文件上传状态
            Object.keys(uploadedFiles).forEach(key => {
                uploadedFiles[key] = ''
                uploadProgress[key] = 0
                uploadedFileInfo[key] = null
            })

            // 重置文件输入元素
            const fileInputs = document.querySelectorAll('input[type="file"]')
            fileInputs.forEach(input => {
                input.value = ''
            })

            // 重置分割比例
            splitRatio.train = 8
            splitRatio.validation = 1
            splitRatio.test = 1

            // 重置超参数
            hyperparameters.epoch = 20
            hyperparameters.learningRate = 0.001
            hyperparameters.earlyStopping = 10
            hyperparameters.batchSize = 32
            hyperparameters.randomSeed = 42
            hyperparameters.labelCount = 2

            // 重置通知设置
            notification.email = ''

            // 重置训练结果显示相关状态
            showTrainingResult.value = false
            jobId.value = ''
            currentStatus.value = ''
            statusText.value = 'Initializing...'
            trainingResults.value = {}

            // 停止任务轮询
            stopPolling()
        }

        const startNewTraining = () => {
            resetForm()
        }

        // 新增方法
        const loadAvailableModels = async () => {
            loadingModels.value = true
            try {
                const models = await trainingApi.getAvailableModels()
                availableModels.value = models.map(model => ({
                    id: model.model_type,
                    name: model.model_type.toUpperCase(),
                    description: model.description
                }))
            } catch (error) {
                console.error('加载模型列表失败:', error)
                // 使用默认模型列表作为后备
                availableModels.value = [
                    { id: 'cnn', name: 'CNN', description: '卷积神经网络' },
                    { id: 'lstm', name: 'LSTM', description: '长短期记忆网络' },
                    { id: 'mlp', name: 'MLP', description: '多层感知机' }
                ]
            } finally {
                loadingModels.value = false
            }
        }

        const getDatasetPath = () => {
            if (strategy.value === 'split') {
                return uploadedFiles.dataset
            } else if (strategy.value === 'upload') {
                return `${uploadedFiles.train},${uploadedFiles.validation},${uploadedFiles.test}`
            } else if (strategy.value === 'kfold') {
                return uploadedFiles.kfoldDataset
            }
            return ''
        }

        // 获取包含文件ID的数据集路径（用于后端自动关联）
        const getDatasetPathWithFileIds = () => {
            console.log('getDatasetPathWithFileIds called, strategy:', strategy.value)
            console.log('uploadedFileInfo:', uploadedFileInfo)

            if (strategy.value === 'split' && uploadedFileInfo.dataset) {
                console.log('Using dataset file ID:', uploadedFileInfo.dataset.id)
                return `file://${uploadedFileInfo.dataset.id}`
            } else if (strategy.value === 'upload') {
                // 对于分别上传，返回主要训练文件ID
                if (uploadedFileInfo.train) {
                    console.log('Using train file ID:', uploadedFileInfo.train.id)
                    return `file://${uploadedFileInfo.train.id}`
                }
            } else if (strategy.value === 'kfold' && uploadedFileInfo.kfoldDataset) {
                console.log('Using kfoldDataset file ID:', uploadedFileInfo.kfoldDataset.id)
                return `file://${uploadedFileInfo.kfoldDataset.id}`
            }

            console.log('Falling back to getDatasetPath')
            return getDatasetPath()
        }

        const pollTaskStatus = async (taskId) => {
            // 停止之前的轮询
            stopPolling()

            const poll = async () => {
                try {
                    const task = await trainingApi.getTask(taskId)
                    currentStatus.value = task.status
                    statusText.value = `Status: ${task.status}`

                    if (task.status === 'completed') {
                        // 获取训练结果
                        try {
                            const logs = await trainingApi.getTaskLogs(taskId)
                            const finalLog = logs.find(log => log.message.includes('Final'))
                            if (finalLog) {
                                trainingResults.value = {
                                    accuracy: finalLog.message.match(/accuracy: ([0-9.]+)/)?.[1] || 'N/A',
                                    loss: finalLog.message.match(/loss: ([0-9.]+)/)?.[1] || 'N/A',
                                    epochs_trained: hyperparameters.epoch,
                                    training_time: 'Calculated'
                                }
                            }
                        } catch (logError) {
                            console.error('获取训练日志失败:', logError)
                        }
                        // 任务完成，停止轮询
                        stopPolling()
                    } else if (task.status === 'running' || task.status === 'pending') {
                        // 继续轮询，每5秒一次
                        pollingInterval = setTimeout(poll, 5000)
                    } else if (task.status === 'failed') {
                        // 任务失败，停止轮询
                        stopPolling()
                        statusText.value = 'Training failed'
                    }
                } catch (error) {
                    console.error('轮询任务状态失败:', error)
                    // 出错时也停止轮询
                    stopPolling()
                }
            }

            // 立即执行一次
            poll()
        }

        const stopPolling = () => {
            if (pollingInterval) {
                clearTimeout(pollingInterval)
                pollingInterval = null
            }
        }

        // 组件挂载时加载数据
        onMounted(() => {
            loadAvailableModels()
        })

        return {
            // 数据
            strategy,
            selectedModels,
            kfoldValue,
            uploadedFiles,
            uploadProgress,
            uploadedFileInfo,
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
            loadingModels,

            // 计算属性
            ratioDisplay,
            simplifiedRatioDisplay,
            isAllSelected,
            isFormValid,

            // 方法
            handleFileUpload,
            handleStrategyChange,
            updateRatios,
            selectModel,
            toggleModelSelection,
            selectAllModels,
            isSelected,
            getModelNames,
            getModelName,
            handleSubmit,
            checkInput,
            resetForm,
            startNewTraining,
            loadAvailableModels,
            getDatasetPath,
            getDatasetPathWithFileIds,
            pollTaskStatus,
            stopPolling
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

.ratio-controls {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
    align-items: center;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.ratio-item {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 150px;
}

.ratio-label {
    font-weight: 500;
    color: #495057;
    white-space: nowrap;
    margin-bottom: 0;
}

.ratio-input {
    width: 80px;
    padding: 6px 10px;
    text-align: center;
    border-radius: 4px;
}

.ratio-input:focus {
    border-color: #9c88ff;
    box-shadow: 0 0 0 0.2rem rgba(156, 136, 255, 0.25);
}

.ratio-display {
    background-color: #f0f0f0;
    padding: 10px 15px;
    border-radius: 6px;
    border: 1px solid #dddddd;
    color: #555555;
    text-align: center;
}

.upload-section {
    background-color: #f8f8f8;
    /* 浅灰色上传区域 */
    padding: 20px;
    border-radius: 8px;
    margin-top: 15px;
    border: 1px solid #eeeeee;
}

/* All Models 卡片特殊样式 */
.all-models-card {
    background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
    border: 2px dashed #9c88ff;
}

.all-models-card.selected {
    background: linear-gradient(135deg, rgba(156, 136, 255, 0.1) 0%, rgba(156, 136, 255, 0.2) 100%);
    border-style: solid;
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

/* 新增样式 - All按钮和信息区域 */
.step-header {
    padding-bottom: 15px;
    border-bottom: 2px solid #e9ecef;
}

.all-models-info {
    border-left: 3px solid #9c88ff;
}

.btn-outline-primary.active {
    background-color: #9c88ff;
    border-color: #9c88ff;
    color: white;
}

.btn-outline-primary:not(.active):hover {
    background-color: #f8f9fa;
    border-color: #9c88ff;
    color: #9c88ff;
}
</style>