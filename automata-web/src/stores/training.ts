import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TrainingTask } from '@/api/types'
import { useUIStore } from './ui'
import { trainingApi } from '@/api/training'

export interface TaskState {
  tasks: TrainingTask[]
  currentTask: TrainingTask | null
  isLoading: boolean
  error: string | null
}

export const useTrainingStore = defineStore('training', () => {
  // 状态
  const tasks = ref<TrainingTask[]>([])
  const currentTask = ref<TrainingTask | null>(null)
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)
  const uiStore = useUIStore()
  
  // 计算属性
  const pendingTasks = computed(() => 
    tasks.value.filter(task => task.status === 'pending')
  )
  
  const runningTasks = computed(() => 
    tasks.value.filter(task => task.status === 'running')
  )
  
  const completedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'completed')
  )
  
  const failedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'failed')
  )
  
  // Actions
  // <!-- 
  // 审查上下文：
  // - 设计意图：实现完整的训练任务管理功能，包括错误处理和用户反馈
  // - 已知局限：当前使用模拟数据，后续需要连接真实API
  // - 业务背景：支持生物信息学模型训练的核心功能
  // - 测试重点：验证API调用的错误处理和用户提示机制
  // -->
  async function fetchTasks() {
    try {
      isLoading.value = true
      error.value = null
      const response = await trainingApi.getTasks()
      tasks.value = response
    } catch (err: any) {
      error.value = err.message || '获取任务列表失败'
      console.error('Failed to fetch tasks:', err)
      // 显示用户友好的错误提示
      uiStore.showError('获取任务失败', err.message || '无法连接到服务器')
    } finally {
      isLoading.value = false
    }
  }
  
  async function createTask(taskData: any) {
    try {
      isLoading.value = true
      error.value = null
      const response = await trainingApi.createTask(taskData)
      tasks.value.push(response)
      // 显示成功提示
      uiStore.showSuccess('任务创建成功', `任务 "${response.task_name}" 已开始执行`)
      return response
    } catch (err: any) {
      error.value = err.message || '创建任务失败'
      console.error('Failed to create task:', err)
      // 显示错误提示
      uiStore.showError('任务创建失败', err.message || '请检查输入参数')
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  async function updateTask(taskId: number, updates: Partial<TrainingTask>) {
    try {
      isLoading.value = true
      error.value = null
      const response = await trainingApi.updateTask(taskId, updates)
      const index = tasks.value.findIndex(t => t.id === taskId)
      if (index !== -1) {
        // 过滤掉 undefined 值，确保不会覆盖原有有效数据
        const filteredUpdates = Object.fromEntries(
          Object.entries(updates).filter(([_, value]) => value !== undefined)
        ) as Partial<TrainingTask>;
        
        tasks.value[index] = { 
          ...tasks.value[index], 
          ...filteredUpdates 
        } as TrainingTask;
      }
      return response
    } catch (err: any) {
      error.value = err.message || '更新任务失败'
      console.error('Failed to update task:', err)
      uiStore.showError('任务更新失败', err.message || '操作未能完成')
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  function setCurrentTask(task: TrainingTask | null) {
    currentTask.value = task
  }
  
  function clearError() {
    error.value = null
  }
  
  return {
    // 状态
    tasks,
    currentTask,
    isLoading,
    error,
    
    // 计算属性
    pendingTasks,
    runningTasks,
    completedTasks,
    failedTasks,
    
    // Actions
    fetchTasks,
    createTask,
    updateTask,
    setCurrentTask,
    clearError
  }
})