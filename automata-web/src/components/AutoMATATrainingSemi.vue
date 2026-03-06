<template>
    <div class="automata-training-semi">
        <!-- 半监督训练表单 -->
        <div class="container-fluid p-4">
            <div class="row justify-content-center">
                <div class="col-12 col-lg-8">
                    <div class="card border-0 shadow">
                        <div class="card-header bg-primary text-white py-3">
                            <h4 class="mb-0 text-center">
                                <i class="fas fa-cogs me-2"></i>Train your semi-supervised model
                            </h4>
                        </div>
                        <div class="card-body p-4">
                            <form @submit.prevent="handleSubmit" class="train_form" enctype="multipart/form-data">

                                <!-- 策略选择 -->
                                <div class="pb-3" style="margin-bottom: 10px;">
                                    <label>1. Select strategy and upload files</label><br /><br />
                                    <input type="radio" name="strategy" value="upload" v-model="strategy" checked
                                        @click="useUpload">
                                    Upload dataset &nbsp;
                                    <input type="radio" name="strategy" value="split" v-model="strategy"
                                        @click="useSplit">
                                    Data split &nbsp;
                                    <input type="radio" name="strategy" value="kfold" v-model="strategy"
                                        @click="useKfold">
                                    K-Fold cross validation
                                </div>

                                <!-- 上传数据集区域 -->
                                <div class="upload_dataset" :style="{ display: strategy === 'upload' ? '' : 'none' }">
                                    <div class="pb-3">
                                        <label>Upload training set (NOTE: The categorized labels of unlabeled samples
                                            are marked as Unknown)</label>
                                        <input type="file" id="upload_file_1" name="upload_file_1" class="form-control"
                                            @change="handleFileUpload($event, 'train')" accept=".txt,.csv,.xlsx,.xls"
                                            required>
                                        <div v-if="uploadedFiles.train" class="mt-2">
                                            <span class="badge bg-success">{{ uploadedFiles.train }}</span>
                                        </div>
                                    </div>

                                    <div class="pb-3">
                                        <label>Validation set</label>
                                        <input type="file" id="upload_file_2" name="upload_file_2" class="form-control"
                                            @change="handleFileUpload($event, 'validation')"
                                            accept=".txt,.csv,.xlsx,.xls" required>
                                        <div v-if="uploadedFiles.validation" class="mt-2">
                                            <span class="badge bg-success">{{ uploadedFiles.validation }}</span>
                                        </div>
                                    </div>

                                    <div class="pb-3">
                                        <label>Upload testing set (NOTE: All samples must be labeled)</label>
                                        <input type="file" id="upload_file_3" name="upload_file_3" class="form-control"
                                            @change="handleFileUpload($event, 'test')" accept=".txt,.csv,.xlsx,.xls"
                                            required>
                                        <div v-if="uploadedFiles.test" class="mt-2">
                                            <span class="badge bg-success">{{ uploadedFiles.test }}</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- 数据分割区域 -->
                                <div class="split_dataset" :style="{ display: strategy === 'split' ? '' : 'none' }">
                                    <div class="pb-3">
                                        <label>Upload dataset (NOTE: The categorized labels of unlabeled samples are
                                            marked as Unknown)</label>
                                        <input type="file" id="upload_file_4" name="upload_file_4" class="form-control"
                                            @change="handleFileUpload($event, 'dataset')" accept=".txt,.csv,.xlsx,.xls"
                                            required>
                                        <div v-if="uploadedFiles.dataset" class="mt-2">
                                            <span class="badge bg-success">{{ uploadedFiles.dataset }}</span>
                                        </div>
                                    </div>

                                    <div class="pb-3">
                                        <label>Input Ratio value (note: If you want to use 8:2 data split method, then
                                            ratio value is 0.2)</label>
                                        <input type="number" step="0.01" min="0" max="1" name="ratio" id="ratio"
                                            v-model="formData.ratio" placeholder="0.2" class="form-control" required>
                                    </div>
                                </div>

                                <!-- K折交叉验证区域 -->
                                <div class="kfold_dataset" :style="{ display: strategy === 'kfold' ? '' : 'none' }">
                                    <div class="pb-3">
                                        <label>Upload labeled dataset (NOTE: All samples must be labeled)</label>
                                        <input type="file" id="upload_file_5" name="upload_file_5" class="form-control"
                                            @change="handleFileUpload($event, 'labeled')" accept=".txt,.csv,.xlsx,.xls"
                                            required>
                                        <div v-if="uploadedFiles.labeled" class="mt-2">
                                            <span class="badge bg-success">{{ uploadedFiles.labeled }}</span>
                                        </div>
                                    </div>

                                    <div class="pb-3">
                                        <label>Upload unlabeled dataset (NOTE: The categorized labels of all samples are
                                            marked as Unknown)</label>
                                        <input type="file" id="upload_file_6" name="upload_file_6" class="form-control"
                                            @change="handleFileUpload($event, 'unlabeled')"
                                            accept=".txt,.csv,.xlsx,.xls" required>
                                        <div v-if="uploadedFiles.unlabeled" class="mt-2">
                                            <span class="badge bg-success">{{ uploadedFiles.unlabeled }}</span>
                                        </div>
                                    </div>

                                    <div class="pb-3">
                                        <label>Input K value (note: If you want to use 3-Fold cross validation method,
                                            then K value is 3)</label>
                                        <input type="number" name="kfold" id="kfold" v-model="formData.kfold"
                                            placeholder="3" class="form-control" required>
                                    </div>
                                </div>

                                <!-- 训练参数 -->
                                <div class="pb-3">
                                    <label>2. Training parameters setting</label>
                                </div>

                                <div class="row g-3">
                                    <div class="col-md-4">
                                        <label class="form-label">Epoch *</label>
                                        <input type="number" class="form-control" id="epoch" v-model="formData.epoch"
                                            min="1" max="1000" required>
                                    </div>

                                    <div class="col-md-4">
                                        <label class="form-label">Learning Rate *</label>
                                        <input type="number" class="form-control" id="lr"
                                            v-model="formData.learningRate" step="0.0001" min="0.0001" max="1" required>
                                    </div>

                                    <div class="col-md-4">
                                        <label class="form-label">EarlyStopping Patience *</label>
                                        <input type="number" class="form-control" id="es"
                                            v-model="formData.earlyStopping" min="1" max="100" required>
                                    </div>

                                    <div class="col-md-4">
                                        <label class="form-label">Random Seed *</label>
                                        <input type="number" class="form-control" id="seed"
                                            v-model="formData.randomSeed" min="0" max="999999" required>
                                    </div>

                                    <div class="col-md-4">
                                        <label class="form-label">Batch Size *</label>
                                        <input type="number" class="form-control" v-model="formData.batchSize" min="1"
                                            max="1024" required>
                                    </div>

                                    <div class="col-md-4">
                                        <label class="form-label">Label Count *</label>
                                        <input type="number" class="form-control" v-model="formData.labelCount" min="2"
                                            max="1000" required>
                                    </div>
                                </div>

                                <!-- 模型配置 -->
                                <div class="pb-3 mt-4">
                                    <label>3. Model configuration</label>
                                </div>

                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="form-label">Model Type *</label>
                                        <select class="form-select" v-model="formData.modelType" required>
                                            <option value="">Please select</option>
                                            <option value="LSTM">LSTM</option>
                                            <option value="CNN">CNN</option>
                                            <option value="RNN">RNN</option>
                                            <option value="MLP">MLP</option>
                                        </select>
                                    </div>

                                    <div class="col-md-6">
                                        <label class="form-label">Loss Function *</label>
                                        <select class="form-select" v-model="formData.lossFunction" required>
                                            <option value="">Please select</option>
                                            <option value="CrossEntropy">Cross Entropy Loss</option>
                                            <option value="MSE">Mean Square Error</option>
                                            <option value="MAE">Mean Absolute Error</option>
                                        </select>
                                    </div>

                                    <div class="col-md-6">
                                        <label class="form-label">Optimizer *</label>
                                        <select class="form-select" v-model="formData.optimizer" required>
                                            <option value="">Please select</option>
                                            <option value="Adam">Adam</option>
                                            <option value="SGD">SGD</option>
                                            <option value="RMSprop">RMSprop</option>
                                        </select>
                                    </div>
                                </div>

                                <!-- 通知信息 -->
                                <div class="pb-3 mt-4">
                                    <label>4. Notification settings</label>
                                </div>

                                <div class="row g-3">
                                    <div class="col-12">
                                        <label class="form-label">Email *</label>
                                        <input type="email" class="form-control" id="email" v-model="formData.email"
                                            placeholder="Please input your email address" required>
                                    </div>
                                </div>

                                <!-- 提交按钮 -->
                                <div class="col-12 mt-4">
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
                <div class="col-12 col-lg-8">
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
    name: 'AutoMATATrainingSemi',
    setup() {
        // 响应式数据
        const strategy = ref('upload')
        const uploadedFiles = reactive({
            train: '',
            validation: '',
            test: '',
            dataset: '',
            labeled: '',
            unlabeled: ''
        })

        const formData = reactive({
            epoch: 20,
            learningRate: 0.0001,
            earlyStopping: 10,
            randomSeed: 42,
            batchSize: 32,
            labelCount: 2,
            modelType: '',
            lossFunction: '',
            optimizer: '',
            email: '',
            ratio: 0.2,
            kfold: 3
        })

        const isSubmitting = ref(false)
        const showTrainingResult = ref(false)
        const jobId = ref('')
        const currentStatus = ref('')
        const statusText = ref('Initializing...')
        const trainingResults = ref({})

        // 计算属性
        const isFormValid = computed(() => {
            // 检查必填字段
            const basicValid = formData.modelType &&
                formData.epoch &&
                formData.learningRate &&
                formData.earlyStopping &&
                formData.randomSeed &&
                formData.batchSize &&
                formData.labelCount &&
                formData.lossFunction &&
                formData.optimizer &&
                formData.email

            // 根据策略检查文件上传
            let filesValid = false
            if (strategy.value === 'upload') {
                filesValid = uploadedFiles.train && uploadedFiles.validation && uploadedFiles.test
            } else if (strategy.value === 'split') {
                filesValid = uploadedFiles.dataset && formData.ratio
            } else if (strategy.value === 'kfold') {
                filesValid = uploadedFiles.labeled && uploadedFiles.unlabeled && formData.kfold
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
                    event.target.value = '' // 清空文件输入
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

        const useUpload = () => {
            strategy.value = 'upload'
        }

        const useSplit = () => {
            strategy.value = 'split'
        }

        const useKfold = () => {
            strategy.value = 'kfold'
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
                    formData: formData,
                    uploadedFiles: uploadedFiles
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
            // 检查文件
            let filesToCheck = []
            if (strategy.value === 'upload') {
                filesToCheck = ['train', 'validation', 'test']
            } else if (strategy.value === 'split') {
                filesToCheck = ['dataset']
                if (!formData.ratio) {
                    alert("Please input Ratio value")
                    return false
                }
            } else if (strategy.value === 'kfold') {
                filesToCheck = ['labeled', 'unlabeled']
                if (!formData.kfold) {
                    alert("Please input Kfold value")
                    return false
                }
            }

            // 检查必填参数
            if (!formData.epoch) {
                alert("Please input Epoch value")
                return false
            }
            if (!formData.learningRate) {
                alert("Please input Learning Rate value")
                return false
            }
            if (!formData.earlyStopping) {
                alert("Please input EarlyStopping Patience value")
                return false
            }
            if (!formData.randomSeed) {
                alert("Please input random seed value")
                return false
            }

            // 检查邮箱格式
            const emailRegex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i
            if (!emailRegex.test(formData.email)) {
                alert("Please submit the correct email address")
                return false
            }

            return true
        }

        const resetForm = () => {
            // 重置表单数据
            Object.keys(formData).forEach(key => {
                if (typeof formData[key] === 'string') {
                    formData[key] = key === 'modelType' || key === 'lossFunction' || key === 'optimizer' ? '' : formData[key]
                } else if (typeof formData[key] === 'number') {
                    formData[key] = key === 'epoch' ? 20 :
                        key === 'learningRate' ? 0.0001 :
                            key === 'earlyStopping' ? 10 :
                                key === 'randomSeed' ? 42 :
                                    key === 'batchSize' ? 32 :
                                        key === 'labelCount' ? 2 :
                                            key === 'ratio' ? 0.2 :
                                                key === 'kfold' ? 3 : formData[key]
                }
            })

            // 重置文件上传状态
            Object.keys(uploadedFiles).forEach(key => {
                uploadedFiles[key] = ''
            })

            // 重置其他状态
            strategy.value = 'upload'
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
            uploadedFiles,
            formData,
            isSubmitting,
            showTrainingResult,
            jobId,
            currentStatus,
            statusText,
            trainingResults,

            // 计算属性
            isFormValid,

            // 方法
            handleFileUpload,
            useUpload,
            useSplit,
            useKfold,
            handleSubmit,
            resetForm,
            startNewTraining
        }
    }
})
</script>

<style scoped>
.automata-training-semi {
    min-height: 100vh;
    background-color: #f8f9fa;
}

.card {
    border-radius: 10px;
}

.form-label {
    font-weight: 500;
    color: #495057;
}

.btn-primary {
    background-color: #0d6efd;
    border-color: #0d6efd;
}

.btn-primary:hover {
    background-color: #0b5ed7;
    border-color: #0a58ca;
}

.badge.bg-success {
    font-size: 0.875rem;
}

.upload_dataset,
.split_dataset,
.kfold_dataset {
    transition: all 0.3s ease;
}
</style>