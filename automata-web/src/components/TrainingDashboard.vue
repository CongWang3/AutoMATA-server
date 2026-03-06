<template>
    <div class="training-dashboard">
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <h1 class="mb-4">AutoMATA 模型训练平台</h1>
                </div>
            </div>

            <!-- 模型选择和任务创建区域 -->
            <div class="row mb-4">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">创建训练任务</h5>
                        </div>
                        <div class="card-body">
                            <form @submit.prevent="submitTask">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">任务名称 *</label>
                                        <input v-model="form.taskName" type="text" class="form-control" required
                                            placeholder="请输入任务名称">
                                    </div>

                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">选择模型 *</label>
                                        <select v-model="form.modelType" class="form-control" required
                                            :disabled="loadingModels">
                                            <option value="">加载模型中...</option>
                                            <option v-for="model in availableModels" :key="model.model_type"
                                                :value="model.model_type" :disabled="!model.supported">
                                                {{ model.model_type.toUpperCase() }} - {{ model.description }}
                                                <span v-if="!model.supported">(暂不支持)</span>
                                            </option>
                                        </select>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">训练轮数 (epochs)</label>
                                        <input v-model.number="form.parameters.epochs" type="number"
                                            class="form-control" min="1" max="1000">
                                    </div>

                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">批处理大小 (batch_size)</label>
                                        <input v-model.number="form.parameters.batch_size" type="number"
                                            class="form-control" min="1" max="128">
                                    </div>

                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">学习率 (learning_rate)</label>
                                        <input v-model.number="form.parameters.learning_rate" type="number"
                                            class="form-control" step="0.0001" min="0.0001" max="1">
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <label class="form-label">数据集路径 *</label>
                                    <input v-model="form.datasetPath" type="text" class="form-control" required
                                        placeholder="/uploads/dataset.csv">
                                    <div class="form-text">请输入数据集文件的完整路径</div>
                                </div>

                                <div class="d-flex justify-content-between align-items-center">
                                    <div class="form-text">
                                        <i class="fas fa-info-circle me-1"></i>
                                        创建后可在任务列表中查看训练进度
                                    </div>
                                    <button type="submit" class="btn btn-primary" :disabled="loading || !formIsValid">
                                        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                                        {{ loading ? '创建中...' : '创建训练任务' }}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- 快捷操作面板 -->
                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">快捷操作</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <button @click="loadTasks" class="btn btn-outline-primary" :disabled="loadingTasks">
                                    <span v-if="loadingTasks" class="spinner-border spinner-border-sm me-2"></span>
                                    刷新任务列表
                                </button>

                                <button @click="applyModelPreset" class="btn btn-outline-secondary"
                                    :disabled="!form.modelType">
                                    应用{{ form.modelType?.toUpperCase() }}模型预设参数
                                </button>

                                <div class="mt-3">
                                    <h6 class="small text-muted">常用参数预设：</h6>
                                    <div class="btn-group w-100" role="group">
                                        <button v-for="(params, modelName) in MODEL_PARAMETERS" :key="modelName"
                                            @click="applyPreset(modelName)" type="button"
                                            class="btn btn-outline-info btn-sm" :disabled="loading">
                                            {{ modelName.toUpperCase() }}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 任务列表区域 -->
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">训练任务列表</h5>
                            <div class="d-flex align-items-center">
                                <span class="badge bg-primary me-2">总计: {{ tasks.length }}</span>
                                <span v-if="runningTasks.length > 0" class="badge bg-warning me-2">
                                    运行中: {{ runningTasks.length }}
                                </span>
                                <span v-if="completedTasks.length > 0" class="badge bg-success">
                                    已完成: {{ completedTasks.length }}
                                </span>
                            </div>
                        </div>
                        <div class="card-body">
                            <div v-if="loadingTasks" class="text-center py-4">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">加载中...</span>
                                </div>
                                <p class="mt-2">正在加载任务列表...</p>
                            </div>

                            <div v-else-if="tasks.length === 0" class="text-center py-4 text-muted">
                                <i class="fas fa-tasks fa-2x mb-3"></i>
                                <p>暂无训练任务</p>
                                <button @click="loadTasks" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-sync-alt me-1"></i>刷新
                                </button>
                            </div>

                            <div v-else class="task-list">
                                <div v-for="task in tasks" :key="task.id" class="task-item border rounded p-3 mb-3">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div class="flex-grow-1">
                                            <div class="d-flex align-items-center mb-2">
                                                <h6 class="mb-0 me-3">{{ task.task_name }}</h6>
                                                <span :class="getStatusBadgeClass(task.status)" class="badge me-2">
                                                    {{ getStatusText(task.status) }}
                                                </span>
                                                <span class="badge bg-info">
                                                    {{ task.model_type.toUpperCase() }}
                                                </span>
                                                <span class="badge bg-secondary ms-2">
                                                    {{ task.language }}
                                                </span>
                                            </div>

                                            <div class="row small text-muted">
                                                <div class="col-md-6">
                                                    <i class="fas fa-database me-1"></i>
                                                    数据集: {{ task.dataset_path || '未指定' }}
                                                </div>
                                                <div class="col-md-6">
                                                    <i class="fas fa-clock me-1"></i>
                                                    创建时间: {{ formatDate(task.created_at) }}
                                                </div>
                                            </div>

                                            <div v-if="task.result_path" class="mt-2">
                                                <small class="text-success">
                                                    <i class="fas fa-check-circle me-1"></i>
                                                    结果文件: {{ task.result_path }}
                                                </small>
                                            </div>
                                        </div>

                                        <div class="task-actions">
                                            <button @click="viewTaskDetails(task.id)"
                                                class="btn btn-outline-info btn-sm me-2">
                                                <i class="fas fa-eye me-1"></i>详情
                                            </button>
                                            <button v-if="task.status === TASK_STATUS.RUNNING"
                                                @click="viewTaskLogs(task.id)"
                                                class="btn btn-outline-secondary btn-sm me-2">
                                                <i class="fas fa-file-alt me-1"></i>日志
                                            </button>
                                            <button @click="deleteTask(task.id)" class="btn btn-outline-danger btn-sm"
                                                :disabled="task.status === TASK_STATUS.RUNNING">
                                                <i class="fas fa-trash me-1"></i>删除
                                            </button>
                                        </div>
                                    </div>

                                    <!-- 任务详情模态框 -->
                                    <div v-if="showTaskDetail && currentTask?.id === task.id"
                                        class="task-detail mt-3 p-3 bg-light rounded">
                                        <h6>任务详细信息</h6>
                                        <pre class="small mb-0">{{ formatTaskDetail(currentTask) }}</pre>
                                    </div>

                                    <!-- 任务日志模态框 -->
                                    <div v-if="showTaskLogs && currentTask?.id === task.id"
                                        class="task-logs mt-3 p-3 bg-dark rounded">
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <h6 class="text-white mb-0">训练日志</h6>
                                            <button @click="stopLogPolling" class="btn btn-outline-light btn-sm">
                                                停止轮询
                                            </button>
                                        </div>
                                        <div ref="logContainer" class="logs-container bg-black text-white p-2 rounded"
                                            style="max-height: 300px; overflow-y: auto;">
                                            <div v-for="log in taskLogs" :key="log.id"
                                                :class="`log-entry log-${log.log_level.toLowerCase()}`">
                                                <span class="log-timestamp text-muted">[{{ formatDate(log.timestamp)
                                                }}]</span>
                                                <span :class="`log-level log-${log.log_level.toLowerCase()}`">{{
                                                    log.log_level }}:</span>
                                                <span class="log-message">{{ log.message }}</span>
                                            </div>
                                            <div v-if="taskLogs.length === 0" class="text-muted">
                                                暂无日志信息
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import {
    trainingApi,
    TASK_STATUS,
    MODEL_PARAMETERS

} from '@/api'
import type { TrainingLog, TrainingTaskCreate, AvailableModel, TrainingTask } from '@/api'

// 响应式数据
const availableModels = ref<AvailableModel[]>([])
const tasks = ref<TrainingTask[]>([])
const taskLogs = ref<TrainingLog[]>([])
const currentTask = ref<TrainingTask | null>(null)

const loading = ref(false)
const loadingModels = ref(false)
const loadingTasks = ref(false)

const showTaskDetail = ref(false)
const showTaskLogs = ref(false)

let logPollingInterval: number | null = null

// 表单数据
const form = reactive({
    taskName: '',
    modelType: '',
    parameters: {
        epochs: 100,
        batch_size: 32,
        learning_rate: 0.001
    },
    datasetPath: ''
})

// 计算属性
const formIsValid = computed(() => {
    return form.taskName && form.modelType && form.datasetPath
})

const runningTasks = computed(() => {
    return tasks.value.filter(task => task.status === TASK_STATUS.RUNNING)
})

const completedTasks = computed(() => {
    return tasks.value.filter(task => task.status === TASK_STATUS.COMPLETED)
})

// 方法
const loadAvailableModels = async () => {
    loadingModels.value = true
    try {
        availableModels.value = await trainingApi.getAvailableModels()
    } catch (error) {
        console.error('加载模型列表失败:', error)
    } finally {
        loadingModels.value = false
    }
}

const loadTasks = async () => {
    loadingTasks.value = true
    try {
        tasks.value = await trainingApi.getTasks(0, 100)
    } catch (error) {
        console.error('加载任务列表失败:', error)
    } finally {
        loadingTasks.value = false
    }
}

const submitTask = async () => {
    if (!formIsValid.value) return

    loading.value = true
    try {
        const taskData: TrainingTaskCreate = {
            task_name: form.taskName,
            model_type: form.modelType,
            parameters: form.parameters,
            dataset_path: form.datasetPath,
            created_by: 1 // 实际应用中应从认证系统获取
        }

        const newTask = await trainingApi.createTask(taskData)
        tasks.value.unshift(newTask)

        // 重置表单
        Object.assign(form, {
            taskName: '',
            modelType: '',
            parameters: {
                epochs: 100,
                batch_size: 32,
                learning_rate: 0.001
            },
            datasetPath: ''
        })

    } catch (error) {
        console.error('创建任务失败:', error)
    } finally {
        loading.value = false
    }
}

const deleteTask = async (taskId: number) => {
    if (!confirm('确定要删除这个任务吗？')) return

    try {
        await trainingApi.deleteTask(taskId)
        tasks.value = tasks.value.filter(task => task.id !== taskId)
    } catch (error) {
        console.error('删除任务失败:', error)
    }
}

const viewTaskDetails = async (taskId: number) => {
    if (currentTask.value?.id === taskId) {
        showTaskDetail.value = !showTaskDetail.value
        return
    }

    try {
        currentTask.value = await trainingApi.getTask(taskId)
        showTaskDetail.value = true
        showTaskLogs.value = false
    } catch (error) {
        console.error('获取任务详情失败:', error)
    }
}

const viewTaskLogs = async (taskId: number) => {
    if (currentTask.value?.id === taskId) {
        showTaskLogs.value = !showTaskLogs.value
        if (showTaskLogs.value) {
            startLogPolling(taskId)
        } else {
            stopLogPolling()
        }
        return
    }

    try {
        currentTask.value = await trainingApi.getTask(taskId)
        showTaskLogs.value = true
        showTaskDetail.value = false
        startLogPolling(taskId)
    } catch (error) {
        console.error('获取任务日志失败:', error)
    }
}

const startLogPolling = async (taskId: number) => {
    stopLogPolling()

    const pollLogs = async () => {
        try {
            taskLogs.value = await trainingApi.getTaskLogs(taskId)
            // 滚动到底部
            setTimeout(() => {
                const container = document.querySelector('.logs-container')
                if (container) {
                    container.scrollTop = container.scrollHeight
                }
            }, 100)
        } catch (error) {
            console.error('轮询日志失败:', error)
        }
    }

    // 立即执行一次
    await pollLogs()
    // 设置定时轮询
    logPollingInterval = window.setInterval(pollLogs, 3000)
}

const stopLogPolling = () => {
    if (logPollingInterval) {
        clearInterval(logPollingInterval)
        logPollingInterval = null
    }
}

const applyModelPreset = () => {
    if (form.modelType && MODEL_PARAMETERS[form.modelType as keyof typeof MODEL_PARAMETERS]) {
        Object.assign(form.parameters, MODEL_PARAMETERS[form.modelType as keyof typeof MODEL_PARAMETERS])
    }
}

const applyPreset = (modelName: string) => {
    form.modelType = modelName
    applyModelPreset()
}

const getStatusBadgeClass = (status: string) => {
    const statusClasses: Record<string, string> = {
        [TASK_STATUS.PENDING]: 'bg-secondary',
        [TASK_STATUS.RUNNING]: 'bg-primary',
        [TASK_STATUS.COMPLETED]: 'bg-success',
        [TASK_STATUS.FAILED]: 'bg-danger'
    }
    return statusClasses[status] || 'bg-secondary'
}

const getStatusText = (status: string) => {
    const statusTexts: Record<string, string> = {
        [TASK_STATUS.PENDING]: '等待中',
        [TASK_STATUS.RUNNING]: '运行中',
        [TASK_STATUS.COMPLETED]: '已完成',
        [TASK_STATUS.FAILED]: '失败'
    }
    return statusTexts[status] || status
}

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
}

const formatTaskDetail = (task: TrainingTask) => {
    return JSON.stringify({
        id: task.id,
        task_name: task.task_name,
        model_type: task.model_type,
        language: task.language,
        status: task.status,
        parameters: typeof task.parameters === 'string'
            ? JSON.parse(task.parameters)
            : task.parameters,
        dataset_path: task.dataset_path,
        result_path: task.result_path,
        created_at: task.created_at,
        updated_at: task.updated_at
    }, null, 2)
}

// 生命周期
onMounted(() => {
    loadAvailableModels()
    loadTasks()
})

onUnmounted(() => {
    stopLogPolling()
})
</script>

<style scoped>
.task-item {
    transition: all 0.3s ease;
    border-left: 4px solid transparent;
}

.task-item:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-left-color: #007bff;
}

.task-detail pre {
    max-height: 300px;
    overflow-y: auto;
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    font-size: 0.875rem;
}

.log-entry {
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    margin-bottom: 4px;
    line-height: 1.4;
}

.log-timestamp {
    color: #6c757d;
}

.log-level {
    font-weight: bold;
    margin: 0 8px;
}

.log-info {
    color: #17a2b8;
}

.log-warning {
    color: #ffc107;
}

.log-error {
    color: #dc3545;
}

.log-debug {
    color: #6c757d;
}

.logs-container::-webkit-scrollbar {
    width: 8px;
}

.logs-container::-webkit-scrollbar-track {
    background: #2d2d2d;
}

.logs-container::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
    background: #777;
}
</style>