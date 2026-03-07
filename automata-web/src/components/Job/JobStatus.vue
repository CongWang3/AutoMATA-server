<template>
  <div class="job-status">
    <div class="status-header d-flex align-items-center justify-content-between mb-3">
      <h5 class="mb-0">任务状态</h5>
      <span 
        class="status-badge badge"
        :class="getStatusClass(job.status)"
      >
        {{ getStatusText(job.status) }}
      </span>
    </div>

    <div class="status-details">
      <!-- 进度条 -->
      <div class="progress-section mb-3" v-if="showProgress">
        <div class="d-flex justify-content-between mb-1">
          <span class="small text-muted">进度</span>
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
          <small class="text-muted">任务ID</small>
          <div class="fw-medium">#{{ job.id }}</div>
        </div>
        <div class="info-item">
          <small class="text-muted">创建时间</small>
          <div class="fw-medium">{{ formatDate(job.createdAt) }}</div>
        </div>
        <div class="info-item">
          <small class="text-muted">更新时间</small>
          <div class="fw-medium">{{ formatDate(job.updatedAt) }}</div>
        </div>
        <div class="info-item">
          <small class="text-muted">耗时</small>
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
          取消
        </button>
        <button 
          v-if="canRetry"
          type="button" 
          class="btn btn-sm btn-outline-warning"
          @click="$emit('retry', job.id)"
        >
          <iconify-icon icon="mdi:refresh" class="me-1"></iconify-icon>
          重试
        </button>
        <button 
          v-if="canViewResult"
          type="button" 
          class="btn btn-sm btn-primary"
          @click="$emit('view-result', job.id)"
        >
          <iconify-icon icon="mdi:eye" class="me-1"></iconify-icon>
          查看结果
        </button>
      </div>
    </div>

    <!-- 状态日志 -->
    <div v-if="showLogs && job.logs?.length" class="logs-section mt-4">
      <h6 class="border-bottom pb-2 mb-3">执行日志</h6>
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
  id: number
  name: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  progress: number
  createdAt: string
  updatedAt: string
  duration: number // seconds
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
  (e: 'cancel', jobId: number): void
  (e: 'retry', jobId: number): void
  (e: 'view-result', jobId: number): void
}>()

// 计算属性
const canCancel = computed(() => {
  return ['PENDING', 'RUNNING'].includes(props.job.status)
})

const canRetry = computed(() => {
  return ['FAILED', 'CANCELLED'].includes(props.job.status)
})

const canViewResult = computed(() => {
  return props.job.status === 'COMPLETED'
})

// 方法
const getStatusClass = (status: string): string => {
  const classes: Record<string, string> = {
    PENDING: 'bg-secondary',
    RUNNING: 'bg-primary',
    COMPLETED: 'bg-success',
    FAILED: 'bg-danger',
    CANCELLED: 'bg-warning'
  }
  return classes[status] || 'bg-secondary'
}

const getStatusText = (status: string): string => {
  const texts: Record<string, string> = {
    PENDING: '等待中',
    RUNNING: '运行中',
    COMPLETED: '已完成',
    FAILED: '失败',
    CANCELLED: '已取消'
  }
  return texts[status] || status
}

const getProgressClass = (status: string): string => {
  const classes: Record<string, string> = {
    PENDING: 'bg-secondary',
    RUNNING: 'bg-primary progress-bar-animated progress-bar-striped',
    COMPLETED: 'bg-success',
    FAILED: 'bg-danger',
    CANCELLED: 'bg-warning'
  }
  return classes[status] || 'bg-secondary'
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
  if (seconds < 60) return `${Math.round(seconds)}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
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

.progress-bar-animated {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  0% {
    background-position-x: 1rem;
  }
}
</style>