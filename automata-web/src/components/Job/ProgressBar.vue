<template>
  <div class="progress-bar-container">
    <div class="progress-info" v-if="showInfo">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-percent">{{ percent }}%</span>
    </div>
    <div class="progress-track">
      <div 
        class="progress-fill" 
        :class="[status, { animated }]"
        :style="{ width: percent + '%' }"
      >
        <div class="progress-text" v-if="showText && percent > 0">
          {{ percent }}%
        </div>
      </div>
    </div>
    <div class="progress-status" v-if="statusText">
      <el-tag :type="getStatusTagType" size="small">
        {{ statusText }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  percent: number
  label?: string
  status?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  showInfo?: boolean
  showText?: boolean
  animated?: boolean
  statusText?: string
}

const props = withDefaults(defineProps<Props>(), {
  percent: 0,
  label: '',
  status: 'primary',
  showInfo: true,
  showText: false,
  animated: false,
  statusText: ''
})

// 计算属性
const getStatusTagType = computed(() => {
  const statusMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | ''> = {
    primary: 'info',
    success: 'success',
    warning: 'warning',
    danger: 'danger',
    info: 'info'
  }
  return statusMap[props.status] || 'info'
})
</script>

<style scoped>
.progress-bar-container {
  width: 100%;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.progress-label {
  color: #606266;
  font-weight: 500;
}

.progress-percent {
  color: #909399;
}

.progress-track {
  height: 12px;
  background-color: #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.3s ease;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
}

.progress-fill.primary {
  background: linear-gradient(90deg, #409eff, #66b1ff);
}

.progress-fill.success {
  background: linear-gradient(90deg, #67c23a, #85ce61);
}

.progress-fill.warning {
  background: linear-gradient(90deg, #e6a23c, #ebb563);
}

.progress-fill.danger {
  background: linear-gradient(90deg, #f56c6c, #f78989);
}

.progress-fill.info {
  background: linear-gradient(90deg, #909399, #a6a9ad);
}

.progress-fill.animated::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.3) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  animation: progress-animation 2s infinite;
}

.progress-text {
  color: white;
  font-size: 10px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.progress-status {
  margin-top: 8px;
}

@keyframes progress-animation {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .progress-info {
    font-size: 12px;
  }
  
  .progress-track {
    height: 10px;
  }
  
  .progress-text {
    font-size: 8px;
    padding-right: 4px;
  }
}
</style>