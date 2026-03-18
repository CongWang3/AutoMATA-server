/**
 * 统一任务管理 Pinia Store
 * 
 * 提供跨模块的任务状态管理，支持过滤、分页、WebSocket 状态更新
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { jobsApi, JOB_STATUS } from '@/api/jobs'
import type { UnifiedJob, JobFilter, JobTypeInfo } from '@/api/jobs'

export const useJobsStore = defineStore('jobs', () => {
  // ===== 状态 =====
  const jobs = ref<UnifiedJob[]>([])
  const total = ref(0)
  const jobTypes = ref<JobTypeInfo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 过滤器状态
  const filter = ref<JobFilter>({
    limit: 20,
    offset: 0,
    sort_by: 'created_at',
    sort_order: 'desc'
  })

  // ===== 计算属性 =====
  
  /** 是否还有更多数据可加载 */
  const hasMore = computed(() => jobs.value.length < total.value)
  
  /** 当前页码（从1开始） */
  const currentPage = computed(() => {
    const limit = filter.value.limit || 20
    const offset = filter.value.offset || 0
    return Math.floor(offset / limit) + 1
  })
  
  /** 总页数 */
  const totalPages = computed(() => {
    const limit = filter.value.limit || 20
    return Math.ceil(total.value / limit)
  })
  
  /** 运行中的任务 */
  const runningJobs = computed(() => 
    jobs.value.filter(j => 
      j.status === JOB_STATUS.PROCESSING || j.status === JOB_STATUS.SUBMITTED
    )
  )
  
  /** 已完成的任务 */
  const completedJobs = computed(() => 
    jobs.value.filter(j => j.status === JOB_STATUS.COMPLETED)
  )
  
  /** 失败的任务 */
  const failedJobs = computed(() => 
    jobs.value.filter(j => j.status === JOB_STATUS.FAILED)
  )

  // ===== Actions =====

  /**
   * 获取任务列表
   */
  async function fetchJobs() {
    loading.value = true
    error.value = null
    try {
      const response = await jobsApi.getAllJobs(filter.value)
      jobs.value = response.jobs
      total.value = response.total
    } catch (e: any) {
      error.value = e.message || '获取任务列表失败'
      console.error('获取任务列表失败:', e)
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取任务类型列表
   */
  async function fetchJobTypes() {
    try {
      jobTypes.value = await jobsApi.getJobTypes()
    } catch (e) {
      console.error('获取任务类型失败:', e)
    }
  }

  /**
   * 获取任务详情
   */
  async function fetchJobDetail(jobId: string): Promise<UnifiedJob> {
    try {
      return await jobsApi.getJobDetail(jobId)
    } catch (e: any) {
      throw new Error(e.message || '获取任务详情失败')
    }
  }

  /**
   * 取消任务
   */
  async function cancelJob(jobId: string): Promise<UnifiedJob> {
    try {
      const updated = await jobsApi.cancelJob(jobId)
      // 更新本地状态
      const idx = jobs.value.findIndex(j => j.job_id === jobId)
      if (idx !== -1) {
        jobs.value[idx] = updated
      }
      return updated
    } catch (e: any) {
      throw new Error(e.message || '取消任务失败')
    }
  }

  /**
   * 删除任务
   */
  async function deleteJob(jobId: string): Promise<void> {
    try {
      await jobsApi.deleteJob(jobId)
      // 从本地列表移除
      jobs.value = jobs.value.filter(j => j.job_id !== jobId)
      total.value = Math.max(0, total.value - 1)
    } catch (e: any) {
      throw new Error(e.message || '删除任务失败')
    }
  }

  /**
   * 获取下载链接
   */
  async function getDownloadUrl(jobId: string): Promise<string> {
    return await jobsApi.getDownloadUrl(jobId)
  }

  /**
   * 设置过滤器并刷新
   */
  function setFilter(newFilter: Partial<JobFilter>) {
    filter.value = { 
      ...filter.value, 
      ...newFilter, 
      offset: 0  // 重置到第一页
    }
    fetchJobs()
  }

  /**
   * 设置页码
   */
  function setPage(page: number) {
    const limit = filter.value.limit || 20
    filter.value.offset = (page - 1) * limit
    fetchJobs()
  }

  /**
   * 重置过滤器
   */
  function resetFilter() {
    filter.value = {
      limit: 20,
      offset: 0,
      sort_by: 'created_at',
      sort_order: 'desc'
    }
    fetchJobs()
  }

  /**
   * 更新单个任务状态（用于 WebSocket 回调）
   */
  function updateJobStatus(jobId: string, updates: Partial<UnifiedJob>) {
    const idx = jobs.value.findIndex(j => j.job_id === jobId)
    if (idx !== -1) {
      jobs.value[idx] = { ...jobs.value[idx], ...updates }
    }
  }

  /**
   * 清除错误状态
   */
  function clearError() {
    error.value = null
  }

  return {
    // 状态
    jobs,
    total,
    jobTypes,
    loading,
    error,
    filter,
    
    // 计算属性
    hasMore,
    currentPage,
    totalPages,
    runningJobs,
    completedJobs,
    failedJobs,
    
    // Actions
    fetchJobs,
    fetchJobTypes,
    fetchJobDetail,
    cancelJob,
    deleteJob,
    getDownloadUrl,
    setFilter,
    setPage,
    resetFilter,
    updateJobStatus,
    clearError
  }
})
