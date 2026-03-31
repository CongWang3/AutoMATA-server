<template>
  <div class="job-status">
    <div class="status-header d-flex align-items-center justify-content-between mb-3">
      <h5 class="mb-0">Job status</h5>
      <span 
        class="status-badge badge"
        :class="getStatusClass(job.status)"
      >
        {{ getStatusText(job.status) }}
      </span>
    </div>

    <div class="status-details">
      <!-- 当前步骤显示 -->
      <div class="current-step-section mb-3" v-if="job.currentStep">
        <div class="d-flex align-items-center">
          <span class="small text-muted me-2">Current step:</span>
          <span class="current-step-text">{{ job.currentStep }}</span>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section mb-3" v-if="showProgress">
        <div class="d-flex justify-content-between mb-1">
          <span class="small text-muted">Progress</span>
          <span class="small">{{ job.progress }}%</span>
        </div>
        <div class="progress" style="height: 10px;">
          <div 
            class="progress-bar" 
            role="progressbar"
            :class="getProgressClass(job.status)"
            :style="{ width: job.progress + '%' }"
          ></div>
        </div>
      </div>

      <!-- 任务信息 -->
      <div class="info-grid">
        <div class="info-item">
          <small class="text-muted">Job ID</small>
          <div class="fw-medium">#{{ job.id }}</div>
        </div>
        <div class="info-item">
          <small class="text-muted">Created</small>
          <div class="fw-medium">{{ formatDate(job.createdAt) }}</div>
        </div>
        <div class="info-item">
          <small class="text-muted">Updated</small>
          <div class="fw-medium">{{ formatDate(job.updatedAt) }}</div>
        </div>
        <div class="info-item">
          <small class="text-muted">Duration</small>
          <div class="fw-medium">{{ formatDuration(job.duration) }}</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons d-flex gap-2 mt-3">
        <button 
          v-if="canCancel"
          type="button" 
          class="btn btn-sm btn-outline-danger"
          @click="$emit('cancel', job.id)"
        >
          <iconify-icon icon="mdi:cancel" class="me-1"></iconify-icon>
          Cancel
        </button>
        <button 
          v-if="canRetry"
          type="button" 
          class="btn btn-sm btn-outline-warning"
          @click="$emit('retry', job.id)"
        >
          <iconify-icon icon="mdi:refresh" class="me-1"></iconify-icon>
          Retry
        </button>
        <button 
          v-if="canViewResult"
          type="button" 
          class="btn btn-sm btn-primary"
          @click="$emit('view-result', job.id)"
        >
          <iconify-icon icon="mdi:eye" class="me-1"></iconify-icon>
          View result
        </button>
      </div>
    </div>

    <!-- 状态日志 -->
    <div v-if="showLogs && job.logs?.length" class="logs-section mt-4">
      <h6 class="border-bottom pb-2 mb-3">Execution log</h6>
      <div class="logs-container" style="max-height: 200px; overflow-y: auto;">
        <div 
          v-for="log in job.logs" 
          :key="log.id"
          class="log-entry mb-2 p-2 rounded"
          :class="getLogClass(log.level)"
        >
          <div class="d-flex justify-content-between">
            <span class="log-message">{{ log.message }}</span>
            <small class="text-muted">{{ formatTime(log.timestamp) }}</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface JobLog {
  id: number
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  message: string
  timestamp: string
}

interface Job {
  id: number | string
  name: string
  status: 'Submitted' | 'Processing' | 'Completed' | 'Failed' | 'Cancelled' | 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  progress: number
  currentStep?: string   // 当前执行步骤描述
  createdAt: string
  updatedAt: string
  duration: number // seconds
  resultFile?: string    // 结果文件路径
  errorMessage?: string  // 错误信息
  logs?: JobLog[]
}

interface Props {
  job: Job
  showProgress?: boolean
  showLogs?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showProgress: true,
  showLogs: true
})

const emit = defineEmits<{
  (e: 'cancel', jobId: number | string): void
  (e: 'retry', jobId: number | string): void
  (e: 'view-result', jobId: number | string): void
}>()

// 状态映射（支持后端新格式和旧版本大写格式）
const STATUS_MAP: Record<string, { class: string; text: string; progressClass: string }> = {
  // 后端新状态枚举值（首字母大写）
  Submitted: { class: 'bg-secondary', text: 'Submitted', progressClass: 'bg-secondary' },
  Processing: { class: 'bg-primary', text: 'Processing', progressClass: 'bg-primary progress-bar-animated progress-bar-striped' },
  Completed: { class: 'bg-success', text: 'Completed', progressClass: 'bg-success' },
  Failed: { class: 'bg-danger', text: 'Failed', progressClass: 'bg-danger' },
  Cancelled: { class: 'bg-warning', text: 'Cancelled', progressClass: 'bg-warning' },
  // 兼容旧版本大写状态
  PENDING: { class: 'bg-secondary', text: 'Pending', progressClass: 'bg-secondary' },
  RUNNING: { class: 'bg-primary', text: 'Running', progressClass: 'bg-primary progress-bar-animated progress-bar-striped' },
  COMPLETED: { class: 'bg-success', text: 'Completed', progressClass: 'bg-success' },
  FAILED: { class: 'bg-danger', text: 'Failed', progressClass: 'bg-danger' },
  CANCELLED: { class: 'bg-warning', text: 'Cancelled', progressClass: 'bg-warning' }
}

// 计算属性
const canCancel = computed(() => {
  const status = props.job.status
  return ['Submitted', 'Processing', 'PENDING', 'RUNNING'].includes(status)
})

const canRetry = computed(() => {
  const status = props.job.status
  return ['Failed', 'Cancelled', 'FAILED', 'CANCELLED'].includes(status)
})

const canViewResult = computed(() => {
  const status = props.job.status
  return ['Completed', 'COMPLETED'].includes(status)
})

// 方法
const getStatusClass = (status: string): string => {
  return STATUS_MAP[status]?.class || 'bg-secondary'
}

const getStatusText = (status: string): string => {
  return STATUS_MAP[status]?.text || status
}

const getProgressClass = (status: string): string => {
  return STATUS_MAP[status]?.progressClass || 'bg-secondary'
}

const getLogClass = (level: string): string => {
  const classes: Record<string, string> = {
    DEBUG: 'bg-light text-dark',
    INFO: 'bg-info text-white',
    WARNING: 'bg-warning text-dark',
    ERROR: 'bg-danger text-white'
  }
  return classes[level] || 'bg-light'
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatTime = (dateString: string): string => {
  return new Date(dateString).toLocaleTimeString('zh-CN')
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}
</script>

<style scoped>
.job-status {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.status-badge {
  font-size: 0.875rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.info-item small {
  display: block;
  margin-bottom: 0.25rem;
}

.log-entry {
  font-family: monospace;
  font-size: 0.875rem;
}

.current-step-section {
  padding: 0.5rem 0;
}

.current-step-text {
  font-weight: 500;
  color: #495057;
  background-color: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.progress-bar-animated {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  0% {
    background-position-x: 1rem;
  }
}
</style>