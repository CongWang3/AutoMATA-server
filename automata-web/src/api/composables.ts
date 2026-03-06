// Vue组合式API钩子
import { ref, type Ref, watch } from 'vue'
import { trainingApi } from '../api/training'
import type { TrainingTask, TrainingTaskCreate, TrainingTaskUpdate, TrainingLog } from '../api/types'

// 训练任务管理组合式函数
export function useTrainingTasks() {
  const tasks: Ref<TrainingTask[]> = ref([])
  const loading: Ref<boolean> = ref(false)
  const error: Ref<string | null> = ref(null)
  const pagination = ref({
    skip: 0,
    limit: 100,
    total: 0
  })

  // 获取任务列表
  const fetchTasks = async (skip: number = 0, limit: number = 100) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await trainingApi.getTasks(skip, limit)
      tasks.value = data
      pagination.value.skip = skip
      pagination.value.limit = limit
      pagination.value.total = data.length
    } catch (err: any) {
      error.value = err.message || '获取任务列表失败'
      console.error('Fetch tasks error:', err)
    } finally {
      loading.value = false
    }
  }

  // 获取单个任务
  const fetchTask = async (taskId: number) => {
    loading.value = true
    error.value = null
    
    try {
      return await trainingApi.getTask(taskId)
    } catch (err: any) {
      error.value = err.message || '获取任务详情失败'
      console.error('Fetch task error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  // 创建任务
  const createTask = async (taskData: TrainingTaskCreate) => {
    loading.value = true
    error.value = null
    
    try {
      const newTask = await trainingApi.createTask(taskData)
      tasks.value.unshift(newTask) // 添加到列表开头
      return newTask
    } catch (err: any) {
      error.value = err.message || '创建任务失败'
      console.error('Create task error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  // 更新任务
  const updateTask = async (taskId: number, taskData: TrainingTaskUpdate) => {
    loading.value = true
    error.value = null
    
    try {
      const updatedTask = await trainingApi.updateTask(taskId, taskData)
      
      // 更新本地列表
      const index = tasks.value.findIndex(task => task.id === taskId)
      if (index !== -1) {
        tasks.value[index] = updatedTask
      }
      
      return updatedTask
    } catch (err: any) {
      error.value = err.message || '更新任务失败'
      console.error('Update task error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  // 删除任务
  const deleteTask = async (taskId: number) => {
    loading.value = true
    error.value = null
    
    try {
      await trainingApi.deleteTask(taskId)
      
      // 从本地列表移除
      const index = tasks.value.findIndex(task => task.id === taskId)
      if (index !== -1) {
        tasks.value.splice(index, 1)
      }
      
      return true
    } catch (err: any) {
      error.value = err.message || '删除任务失败'
      console.error('Delete task error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  // 获取任务日志
  const fetchTaskLogs = async (taskId: number) => {
    loading.value = true
    error.value = null
    
    try {
      return await trainingApi.getTaskLogs(taskId)
    } catch (err: any) {
      error.value = err.message || '获取任务日志失败'
      console.error('Fetch task logs error:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  // 添加任务日志
  const addTaskLog = async (taskId: number, logData: { log_level: string; message: string }) => {
    loading.value = true
    error.value = null
    
    try {
      await trainingApi.addTaskLog(taskId, logData)
      return true
    } catch (err: any) {
      error.value = err.message || '添加任务日志失败'
      console.error('Add task log error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    // 数据
    tasks,
    loading,
    error,
    pagination,
    
    // 方法
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    deleteTask,
    fetchTaskLogs,
    addTaskLog
  }
}

// 任务状态管理组合式函数
export function useTaskStatus() {
  const taskStatusMap = {
    pending: { text: '待处理', class: 'badge bg-secondary' },
    running: { text: '运行中', class: 'badge bg-primary' },
    completed: { text: '已完成', class: 'badge bg-success' },
    failed: { text: '失败', class: 'badge bg-danger' }
  }

  const getTaskStatusInfo = (status: string) => {
    return taskStatusMap[status as keyof typeof taskStatusMap] || 
           { text: status, class: 'badge bg-secondary' }
  }

  const getLanguageBadgeClass = (language: string) => {
    return language === 'python' ? 'badge bg-info' : 'badge bg-warning'
  }

  return {
    taskStatusMap,
    getTaskStatusInfo,
    getLanguageBadgeClass
  }
}

// 分页管理组合式函数
export function usePagination(initialLimit: number = 20) {
  const currentPage = ref(1)
  const pageSize = ref(initialLimit)
  const totalItems = ref(0)
  const totalPages = ref(0)

  const calculatePagination = () => {
    totalPages.value = Math.ceil(totalItems.value / pageSize.value)
  }

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  const nextPage = () => {
    if (currentPage.value < totalPages.value) {
      currentPage.value++
    }
  }

  const prevPage = () => {
    if (currentPage.value > 1) {
      currentPage.value--
    }
  }

  // 监听数据变化重新计算分页
  watch([totalItems, pageSize], calculatePagination)

  return {
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    calculatePagination,
    goToPage,
    nextPage,
    prevPage
  }
}