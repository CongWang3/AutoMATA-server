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
                                <!-- 基础参数 -->
                                <div class="col-md-6">
                                    <label class="form-label">模型类型 *</label>
                                    <select class="form-select" v-model="formData.modelType" required>
                                        <option value="">请选择</option>
                                        <option value="LSTM">LSTM</option>
                                        <option value="CNN">CNN</option>
                                        <option value="RNN">RNN</option>
                                        <option value="MLP">MLP</option>
                                    </select>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">训练轮数 (Epoch) *</label>
                                    <input type="number" class="form-control" v-model="formData.epoch" min="1"
                                        max="1000" required>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">学习率 *</label>
                                    <input type="number" class="form-control" v-model="formData.learningRate"
                                        step="0.0001" min="0.0001" max="1" required>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">早停耐心值 *</label>
                                    <input type="number" class="form-control" v-model="formData.earlyStopping" min="1"
                                        max="100" required>
                                </div>

                                <!-- 数据参数 -->
                                <div class="col-md-6">
                                    <label class="form-label">标签类别数 *</label>
                                    <input type="number" class="form-control" v-model="formData.labelCount" min="2"
                                        max="1000" required>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">批次大小 *</label>
                                    <input type="number" class="form-control" v-model="formData.batchSize" min="1"
                                        max="1024" required>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">随机种子</label>
                                    <input type="number" class="form-control" v-model="formData.randomSeed" min="0"
                                        max="999999">
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">验证集比例 (%)</label>
                                    <input type="number" class="form-control" v-model="formData.validationSplit" min="0"
                                        max="50">
                                </div>

                                <!-- 训练策略 -->
                                <div class="col-md-6">
                                    <label class="form-label">损失函数 *</label>
                                    <select class="form-select" v-model="formData.lossFunction" required>
                                        <option value="">请选择</option>
                                        <option value="CrossEntropy">交叉熵损失</option>
                                        <option value="MSE">均方误差</option>
                                        <option value="MAE">平均绝对误差</option>
                                    </select>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">优化器 *</label>
                                    <select class="form-select" v-model="formData.optimizer" required>
                                        <option value="">请选择</option>
                                        <option value="Adam">Adam</option>
                                        <option value="SGD">SGD</option>
                                        <option value="RMSprop">RMSprop</option>
                                    </select>
                                </div>

                                <div class="col-md-6">
                                    <label class="form-label">训练策略 *</label>
                                    <select class="form-select" v-model="formData.trainStrategy" required>
                                        <option value="">请选择</option>
                                        <option value="split">数据集分割</option>
                                        <option value="cross_validation">K折交叉验证</option>
                                    </select>
                                </div>

                                <div class="col-md-6" v-if="formData.trainStrategy === 'cross_validation'">
                                    <label class="form-label">K折数量</label>
                                    <input type="number" class="form-control" v-model="formData.kFold" min="2" max="10">
                                </div>

                                <!-- 文件上传 -->
                                <div class="col-12">
                                    <label class="form-label">训练数据文件 *</label>
                                    <input type="file" class="form-control" @change="handleFileUpload"
                                        accept=".txt,.csv" required>
                                    <div v-if="uploadedFileName" class="mt-2">
                                        <span class="badge bg-success">{{ uploadedFileName }}</span>
                                    </div>
                                </div>

                                <!-- 通知信息 -->
                                <div class="col-md-8">
                                    <label class="form-label">通知邮箱</label>
                                    <input type="email" class="form-control" v-model="formData.email" placeholder="可选">
                                </div>

                                <div class="col-md-4">
                                    <label class="form-label">项目名称</label>
                                    <input type="text" class="form-control" v-model="formData.projectName"
                                        placeholder="可选">
                                </div>

                                <!-- 提交按钮 -->
                                <div class="col-12 mt-4">
                                    <div class="d-grid gap-2">
                                        <button type="submit" class="btn btn-primary btn-lg"
                                            :disabled="isSubmitting || !isFormValid">
                                            <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"
                                                role="status"></span>
                                            {{ isSubmitting ? '提交中...' : '开始训练' }}
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary"
                                            @click="resetForm">重置表单</button>
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
                                <i class="fas fa-check-circle me-2"></i>训练结果
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>任务ID:</strong> {{ jobId }}</p>
                                    <p><strong>状态:</strong> {{ statusText }}</p>
                                </div>
                                <div class="col-md-6" v-if="Object.keys(trainingResults).length > 0">
                                    <p><strong>准确率:</strong> {{ trainingResults.accuracy }}</p>
                                    <p><strong>损失值:</strong> {{ trainingResults.loss }}</p>
                                    <p><strong>训练轮数:</strong> {{ trainingResults.epochs_trained }}</p>
                                    <p><strong>训练时间:</strong> {{ trainingResults.training_time }}</p>
                                </div>
                            </div>
                            <div class="mt-3">
                                <button class="btn btn-primary me-2" @click="startNewTraining">新建训练</button>
                                <button class="btn btn-outline-secondary"
                                    @click="showTrainingResult = false">关闭</button>
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
    name: 'AutoMATATrainingSimple',
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

        const isSubmitting = ref(false)
        const showTrainingResult = ref(false)
        const jobId = ref('')
        const currentStatus = ref('')
        const statusText = ref('初始化中...')
        const trainingResults = ref({})
        const uploadedFileName = ref('')

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

        // 方法
        const handleFileUpload = (event) => {
            const file = event.target.files[0]
            if (file) {
                if (file.size > 100 * 1024 * 1024) {
                    alert('文件大小不能超过100MB')
                    return
                }
                uploadedFileName.value = file.name
                console.log('选择的文件:', file.name)
            }
        }

        const handleSubmit = async () => {
            isSubmitting.value = true

            try {
                console.log('提交表单数据:', formData)

                // 模拟提交成功
                jobId.value = 'TASK_' + Date.now()
                currentStatus.value = 'Submitted'
                statusText.value = '训练已提交'
                showTrainingResult.value = true

                // 模拟训练完成
                setTimeout(() => {
                    currentStatus.value = 'Finished'
                    statusText.value = '训练完成'
                    trainingResults.value = {
                        accuracy: '0.95',
                        loss: '0.023',
                        epochs_trained: '20',
                        training_time: '120秒'
                    }
                }, 2000)

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
            uploadedFileName.value = ''
            showTrainingResult.value = false
            jobId.value = ''
            currentStatus.value = ''
            statusText.value = '初始化中...'
            trainingResults.value = {}
        }

        const startNewTraining = () => {
            resetForm()
        }

        return {
            // 数据
            formData,
            isSubmitting,
            showTrainingResult,
            jobId,
            currentStatus,
            statusText,
            trainingResults,
            uploadedFileName,

            // 计算属性
            isFormValid,

            // 方法
            handleFileUpload,
            handleSubmit,
            resetForm,
            startNewTraining
        }
    }
})
</script>

<style scoped>
.automata-training-simple {
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
</style>