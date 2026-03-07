<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-content">
      <div class="error-icon">
        <el-icon size="48" color="#dc3545"><Warning /></el-icon>
      </div>
      <h3 class="error-title">{{ title }}</h3>
      <p class="error-message">{{ message }}</p>
      <div class="error-actions">
        <el-button @click="handleRetry" type="primary" v-if="showRetry">
          重试
        </el-button>
        <el-button @click="handleRefresh" v-if="showRefresh">
          刷新页面
        </el-button>
      </div>
      <details v-if="showDetails && error" class="error-details">
        <summary>查看详情</summary>
        <pre>{{ error.stack }}</pre>
      </details>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { Warning } from '@element-plus/icons-vue'

interface Props {
  title?: string
  message?: string
  showRetry?: boolean
  showRefresh?: boolean
  showDetails?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '出现错误',
  message: '抱歉，页面遇到了一些问题',
  showRetry: true,
  showRefresh: true,
  showDetails: false
})

const emit = defineEmits<{
  (e: 'retry'): void
  (e: 'error', error: unknown): void
}>()

// 状态
const hasError = ref(false)
const error = ref<Error | null>(null)

// 错误捕获
onErrorCaptured((err) => {
  hasError.value = true
  error.value = err as Error
  emit('error', err)
  return false // 阻止错误继续传播
})

// 方法
function handleRetry() {
  hasError.value = false
  error.value = null
  emit('retry')
}

function handleRefresh() {
  window.location.reload()
}

// 暴露方法给父组件
defineExpose({
  reset: () => {
    hasError.value = false
    error.value = null
  }
})
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 2rem;
}

.error-content {
  text-align: center;
  max-width: 500px;
}

.error-icon {
  margin-bottom: 1rem;
}

.error-title {
  color: #dc3545;
  margin-bottom: 0.5rem;
  font-size: 1.5rem;
}

.error-message {
  color: #6c757d;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.error-actions {
  margin-bottom: 1rem;
}

.error-actions .el-button {
  margin: 0 0.5rem;
}

.error-details {
  margin-top: 1rem;
  text-align: left;
}

.error-details summary {
  cursor: pointer;
  color: #0d6efd;
  font-weight: 500;
}

.error-details pre {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  font-size: 0.875rem;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 0.5rem;
}
</style>