<template>
    <div class="training-task-manager">
        <h2>训练任务管理</h2>

        <!-- 加载状态 -->
        <div v-if="loading" class="alert alert-info">
            加载中...
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="alert alert-danger">
            {{ error }}
        </div>

        <!-- 创建任务表单 -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">创建新任务</h5>
            </div>
            <div class="card-body">
                <form @submit.prevent="handleCreateTask">
                    <div class="row">
                        <div class="col-md-4 mb-3">
                            <label class="form-label">任务名称</label>
                            <input v-model="newTask.task_name" type="text" class="form-control" required>
                        </div>
                        <div class="col-md-3 mb-3">
                            <label class="form-label">模型类型</label>
                            <select v-model="newTask.model_type" class="form-control" required>
                                <option value="supervised">监督学习</option>
                                <option value="unsupervised">无监督学习</option>
                            </select>
                        </div>
                        <div class="col-md-3 mb-3">
                            <label class="form-label">编程语言</label>
                            <select v-model="newTask.language" class="form-control" required>
                                <option value="python">Python</option>
                                <option value="r">R</option>
                            </select>
                        </div>
                        <div class="col-md-2 mb-3 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary" :disabled="loading">
                                创建任务
                            </button>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">参数 (JSON格式)</label>
                        <textarea v-model="parametersJson" class="form-control" rows="3"
                            placeholder='{"epochs": 100, "batch_size": 32}'></textarea>
                    </div>
                </form>
            </div>
        </div>

        <!-- 任务列表 -->
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">任务列表</h5>
                <button @click="refreshTasks" class="btn btn-outline-secondary btn-sm">
                    刷新
                </button>
            </div>
            <div class="card-body">
                <div v-if="tasks.length === 0 && !loading" class="text-center text-muted">
                    暂无任务数据
                </div>

                <div v-for="task in tasks" :key="task.id" class="task-item border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6>{{ task.task_name }}</h6>
                            <div class="task-meta">
                                <span :class="getTaskStatusInfo(task.status).class" class="me-2">
                                    {{ getTaskStatusInfo(task.status).text }}
                                </span>
                                <span :class="getLanguageBadgeClass(task.language)" class="me-2">
                                    {{ task.language.toUpperCase() }}
                                </span>
                                <span class="text-muted small">
                                    创建时间: {{ formatDate(task.created_at) }}
                                </span>
                            </div>
                            <div v-if="task.dataset_path" class="mt-2">
                                <small class="text-muted">数据集: {{ task.dataset_path }}</small>
                            </div>
                        </div>

                        <div class="task-actions">
                            <button @click="viewTaskDetails(task.id)" class="btn btn-outline-info btn-sm me-2">
                                详情
                            </button>
                            <button @click="deleteTask(task.id)" class="btn btn-outline-danger btn-sm"
                                :disabled="loading">
                                删除
                            </button>
                        </div>
                    </div>

                    <!-- 任务详情模态框 -->
                    <div v-if="showTaskDetail && currentTask?.id === task.id"
                        class="task-detail mt-3 p-3 bg-light rounded">
                        <h6>任务详情</h6>
                        <pre class="small">{{ JSON.stringify(currentTask, null, 2) }}</pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
    useTrainingTasks,
    useTaskStatus,
    type TrainingTaskCreate
} from '@/api'

// 使用组合式函数
const {
    tasks,
    loading,
    error,
    fetchTasks,
    createTask,
    deleteTask: deleteTaskApi,
    fetchTask
} = useTrainingTasks()

const { getTaskStatusInfo, getLanguageBadgeClass } = useTaskStatus()

// 表单数据
const newTask = reactive<TrainingTaskCreate>({
    task_name: '',
    model_type: 'supervised',
    language: 'python',
    parameters: {},
    dataset_path: ''
})

const parametersJson = ref('')

// 详情显示
const showTaskDetail = ref(false)
const currentTask = ref<any>(null)

// 处理创建任务
const handleCreateTask = async () => {
    try {
        // 解析参数JSON
        if (parametersJson.value) {
            newTask.parameters = JSON.parse(parametersJson.value)
        }

        const result = await createTask(newTask)
        if (result) {
            // 重置表单
            Object.assign(newTask, {
                task_name: '',
                model_type: 'supervised',
                language: 'python',
                parameters: {},
                dataset_path: ''
            })
            parametersJson.value = ''
        }
    } catch (err) {
        console.error('创建任务失败:', err)
    }
}

// 查看任务详情
const viewTaskDetails = async (taskId: number) => {
    if (currentTask.value?.id === taskId) {
        // 切换显示/隐藏
        showTaskDetail.value = !showTaskDetail.value
        return
    }

    try {
        const task = await fetchTask(taskId)
        if (task) {
            currentTask.value = task
            showTaskDetail.value = true
        }
    } catch (err) {
        console.error('获取任务详情失败:', err)
    }
}

// 删除任务
const deleteTask = async (taskId: number) => {
    if (confirm('确定要删除这个任务吗？')) {
        await deleteTaskApi(taskId)
    }
}

// 刷新任务列表
const refreshTasks = () => {
    fetchTasks()
}

// 格式化日期
const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
}

// 组件挂载时获取任务列表
onMounted(() => {
    fetchTasks()
})
</script>

<style scoped>
.task-item {
    transition: all 0.3s ease;
}

.task-item:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-detail pre {
    max-height: 200px;
    overflow-y: auto;
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 4px;
}
</style>