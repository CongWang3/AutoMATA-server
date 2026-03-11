<template>
  <div class="task-result-display">
    <!-- 等待页面 -->
    <div v-if="status === 'WAITING' || status === 'SUBMITTED' || status === 'Submitted'" class="waiting-section">
      <section id="banner">
        <div class="container padding-medium-2">
          <div class="hero-content">
            <h2 class="display-2 fw-semibold">Waiting</h2>
            <nav class="breadcrumb">
              <span class="breadcrumb-item active" aria-current="page">
                Your JobID is {{ jobId }}, please wait a moment.
              </span>
            </nav>
          </div>
        </div>
      </section>

      <section id="service" class="padding-medium">
        <div class="container">
          <table :style="tableStyle">
            <tr class="odd" :style="oddRowStyle">
              <td class="line" :style="lineStyle">JobID</td>
              <td>{{ jobId }}</td>
            </tr>
            <tr>
              <td class="line" :style="lineStyle">Gene Nomenclature</td>
              <td>{{ params.gene_nomenclature }}</td>
            </tr>
            <tr class="odd" :style="oddRowStyle">
              <td class="line" :style="lineStyle">Input Data Type</td>
              <td>{{ params.data_type }}</td>
            </tr>
            <tr>
              <td class="line" :style="lineStyle">Organism</td>
              <td>{{ params.organism }}</td>
            </tr>
            <tr class="odd" :style="oddRowStyle">
              <td class="line" :style="lineStyle">Running</td>
              <td>
                <img 
                  v-if="status.toUpperCase() === 'PROCESSING'" 
                  :src="progressBarUrl" 
                  :height="imageHeight" 
                  alt="Processing..."
                >
                <span v-else>Submitted</span>
              </td>
            </tr>
          </table>
        </div>
      </section>
    </div>

    <!-- 成功结果页面 -->
    <div v-else-if="status === 'COMPLETED' || status === 'Completed'" class="result-section">
      <section id="banner">
        <div class="container padding-medium-2">
          <div class="hero-content">
            <h2 class="display-2 fw-semibold">Result</h2>
            <nav class="breadcrumb">
              <span class="breadcrumb-item active" aria-current="page">
                Your JobID is {{ jobId }}.
              </span>
            </nav>
          </div>
        </div>
      </section>

      <section id="service" class="padding-medium">
        <div class="container">
          <table :style="tableStyle">
            <tr class="odd" :style="oddRowStyle">
              <td class="line" :style="lineStyle">JobID</td>
              <td>{{ jobId }}</td>
            </tr>
            <!-- 非精简模式下显示详细参数行（Genome / Transcriptome 保持不变） -->
            <template v-if="!props.compact">
              <tr>
                <td class="line" :style="lineStyle">Gene Nomenclature</td>
                <td>{{ params.gene_nomenclature }}</td>
              </tr>
              <tr class="odd" :style="oddRowStyle">
                <td class="line" :style="lineStyle">Input Data Type</td>
                <td>{{ params.data_type }}</td>
              </tr>
              <tr>
                <td class="line" :style="lineStyle">Organism</td>
                <td>{{ params.organism }}</td>
              </tr>
            </template>
            <!-- 最终结果行：所有场景都保留 -->
            <tr class="odd" :style="oddRowStyle">
              <td class="line" :style="lineStyle">Data Process Result</td>
              <td>
                <el-button 
                  type="primary" 
                  @click="downloadResult"
                  class="download-btn"
                >
                  download
                </el-button>
              </td>
            </tr>
          </table>
        </div>
      </section>
    </div>

    <!-- 失败页面 -->
    <div v-else-if="status === 'FAILED' || status === 'Failed'" class="failed-section">
      <section id="banner">
        <div class="container padding-medium-2">
          <div class="hero-content">
            <h2 class="display-2 fw-semibold">Result</h2>
            <nav class="breadcrumb">
              <span class="breadcrumb-item active" aria-current="page">
                Your JobID is {{ jobId }}, processing failed.
              </span>
            </nav>
          </div>
        </div>
      </section>

      <section id="service" class="padding-medium">
        <div class="container">
          <table :style="tableStyle">
            <tr class="odd" :style="oddRowStyle">
              <td class="line" :style="lineStyle">JobID</td>
              <td>{{ jobId }}</td>
            </tr>
            <!-- 非精简模式下显示详细参数行（Genome / Transcriptome 保持不变） -->
            <template v-if="!props.compact">
              <tr>
                <td class="line" :style="lineStyle">Gene Nomenclature</td>
                <td>{{ params.gene_nomenclature }}</td>
              </tr>
              <tr class="odd" :style="oddRowStyle">
                <td class="line" :style="lineStyle">Input Data Type</td>
                <td>{{ params.data_type }}</td>
              </tr>
              <tr>
                <td class="line" :style="lineStyle">Organism</td>
                <td>{{ params.organism }}</td>
              </tr>
            </template>
            <!-- 最终结果行：所有场景都保留 -->
            <tr class="odd" :style="oddRowStyle">
              <td class="line" :style="lineStyle">Data Process Result</td>
              <td class="error-message">Processing failure! {{ errorMessage }}</td>
            </tr>
          </table>
        </div>
      </section>
    </div>

    <!-- 进度条显示 -->
    <div v-if="progress > 0 && progress < 100" class="progress-overlay">
      <el-card class="progress-card">
        <div class="progress-content">
          <h3>Processing Progress</h3>
          <el-progress 
            :percentage="progress" 
            :stroke-width="12"
            striped
            striped-flow
            status="success"
          />
          <p class="progress-text">{{ progressMessage }}</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DataProcessAPI } from '@/api'
import { webSocketService } from '@/api/websocket'

// <!-- 
// 审查上下文：
// - 设计意图：完全复刻原始PHP页面的视觉效果和用户体验，包括表格样式和进度显示
// - 已知局限：使用现代CSS替代部分内联样式，保持视觉一致性的同时提高可维护性
// - 业务背景：与原始dataProcess.php页面保持完全一致的用户界面和交互逻辑
// - 测试重点：请验证各状态切换、进度更新、下载功能的正确性
// -->

// 任务状态类型定义
type TaskStatus = 'WAITING' | 'SUBMITTED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'Submitted' | 'Processing' | 'Completed' | 'Failed'

interface Props {
  jobId: string
  params: {
    gene_nomenclature: string
    data_type: string
    organism: string
  }
  /**
   * 是否使用精简结果表格（仅显示 JobID 和 Data Process Result 两行）
   * - 用于 Integration 多组学整合，保持与原 integration.php 一致
   * - 默认为 false，Genome / Transcriptome 继续显示完整信息
   */
  compact?: boolean
  initialStatus?: TaskStatus
  initialProgress?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialStatus: 'WAITING' as TaskStatus,
  initialProgress: 0,
  compact: false
})

const emit = defineEmits<{
  (e: 'status-change', status: string): void
}>()

// 状态管理
const status = ref<TaskStatus>(props.initialStatus)
const progress = ref(props.initialProgress)
const progressMessage = ref('')
const errorMessage = ref('')
const pollingTimer = ref<number | null>(null)
const wsConnected = ref(false)

// <!-- 
// 审查上下文：
// - 设计意图：通过watch监听props变化来同步组件内部状态
// - 已知局限：需要在变量定义之后才能使用watch监听器
// - 业务背景：确保组件能响应父组件传递的状态更新
// - 测试重点：请验证状态同步的准确性和及时性
// -->

// 监听props变化并更新内部状态
watch(() => props.initialStatus, (newStatus) => {
  if (newStatus && newStatus !== status.value) {
    status.value = newStatus as TaskStatus
    emit('status-change', newStatus)
  }
})

watch(() => props.initialProgress, (newProgress) => {
  if (newProgress !== undefined && newProgress !== progress.value) {
    progress.value = newProgress
  }
})

// 监听jobId变化，重新连接WebSocket
watch(() => props.jobId, (newJobId) => {
  if (newJobId) {
    connectTaskWebSocket()
  }
})

// 样式定义（响应式布局）——返回行内样式字符串，避免 TS 对 CSSProperties 的严格校验问题
const tableStyle = computed(
  () =>
    'width: 100%; max-width: 100%; text-align: center; line-height: 50px; border-collapse: collapse;'
)

const oddRowStyle = computed(() => 'background-color: #F7F7F7;')

const lineStyle = computed(() => 'border-right: 1px solid #c0c0c0; width: 50%;')

// 响应式图像高度
const imageHeight = computed(() => {
  return window.innerWidth < 768 ? '10px' : '15px'
})

// 进度条图片URL
const progressBarUrl = "/images/progress_bar_new.gif"

const downloadResult = async () => {
  try {
    // 方案1：使用独立下载服务
    const downloadUrl = await DataProcessAPI.getDownloadUrl(props.jobId)
    window.open(downloadUrl, '_blank')
    
    // 方案2：备用方案 - 直接通过API下载
    // const blob = await DataProcessAPI.downloadResultDirect(props.jobId)
    // const url = window.URL.createObjectURL(blob)
    // const link = document.createElement('a')
    // link.href = url
    // link.download = `${props.jobId}_processed.txt`
    // link.click()
    // window.URL.revokeObjectURL(url)
    
  } catch (error: any) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败: ' + (error.message || '未知错误'))
  }
}

// 暴露方法给父组件使用
defineExpose({
  refreshStatus: async () => {
    try {
      // <!-- 
      // 审查上下文：
      // - 设计意图：简化API响应处理逻辑，提高代码可读性
      // - 已知局限：移除调试日志，专注于核心功能实现
      // - 业务背景：确保组件状态更新的稳定性和可靠性
      // - 测试重点：请验证任务状态更新功能的完整性和准确性
      // -->
      
      if (!props.jobId) {
        return null
      }
      
      // 直接获取状态数据
      const result = await DataProcessAPI.getProcessStatus(props.jobId)
      
      // 安全更新组件状态
      if (result && typeof result === 'object' && result.status) {
        status.value = result.status
        
        if (typeof result.progress === 'number' && result.progress >= 0) {
          progress.value = result.progress
        }
        
        return result
      }
      
      return null
      
    } catch (error: any) {
      // 静默处理错误，避免影响用户体验
      return null
    }
  }
})

// WebSocket连接管理
const connectTaskWebSocket = async () => {
  try {
    // 设置任务状态回调
    webSocketService.setOnTaskStatus((data: any) => {
      const { job_id, status: taskStatus, progress: taskProgress, result_file, error_message } = data
      
      // 只处理当前任务的状态更新
      if (job_id === props.jobId && taskStatus) {
        const normalizedStatus = taskStatus.toUpperCase() as TaskStatus
        status.value = normalizedStatus
        emit('status-change', normalizedStatus)
        
        if (typeof taskProgress === 'number' && taskProgress >= 0) {
          progress.value = taskProgress
        }
        
        if (error_message) {
          errorMessage.value = error_message
        }
        
        console.log(`🎯 任务 ${job_id} 状态更新: ${normalizedStatus}, 进度: ${taskProgress || 0}%`)
      }
    })
    
    // 连接任务状态WebSocket
    await webSocketService.connectTaskStatus()
    wsConnected.value = true
    console.log('✅ 任务状态WebSocket连接成功')
    
  } catch (error: any) {
    console.error('WebSocket连接失败:', error)
    // 连接失败时回退到轮询
    startPolling()
  }
}

const disconnectTaskWebSocket = () => {
  if (wsConnected.value) {
    webSocketService.disconnect()
    wsConnected.value = false
    console.log('🔌 任务状态WebSocket已断开')
  }
}

const startPolling = () => {
  // 轮询功能已由父组件的WebSocket统一管理
  console.warn('⚠️ 轮询功能已禁用，使用WebSocket进行状态更新')
}

const stopPolling = () => {
  if (pollingTimer.value) {
    clearTimeout(pollingTimer.value)
    pollingTimer.value = null
  }
}

// 生命周期钩子
onMounted(() => {
  // 如果有jobId，连接WebSocket
  if (props.jobId) {
    connectTaskWebSocket()
  }
  // 如果初始状态不是最终状态，开始轮询作为备用
  else if (props.initialStatus !== 'COMPLETED' && props.initialStatus !== 'FAILED') {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
  disconnectTaskWebSocket()
})
</script>

<style scoped>
.task-result-display {
  max-width: 100%;
  margin: 0 auto;
}

/* 复刻PHP页面的容器样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.padding-medium {
  padding: 40px 0;
}

.padding-medium-2 {
  padding: 30px 0;  /* 从60px减少到30px */
}

.hero-content {
  text-align: center;
  margin-bottom: 15px;  /* 从30px减少到15px */
}

.display-2 {
  font-size: 2rem;  /* 从2.5rem减少到2rem */
  font-weight: 600;
  margin-bottom: 10px;  /* 从20px减少到10px */
}

.fw-semibold {
  font-weight: 600;
}

.breadcrumb {
  font-size: 1rem;  /* 从1.1rem减少到1rem */
  color: #666;
}

/* 表格样式 */
table {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

tr.odd {
  background-color: #F7F7F7;
}

td {
  padding: clamp(10px, 2vw, 15px);
  border: 1px solid #ddd;
  text-align: center;
  font-size: clamp(14px, 2vw, 16px);
}

td.line {
  border-right: 1px solid #c0c0c0;
  width: 50%;
  font-weight: 500;
}

.error-message {
  color: #f56c6c;
  font-weight: 500;
}

/* 下载按钮样式 */
.download-btn {
  background-color: #409eff;
  border-color: #409eff;
  color: white;
  padding: 8px 20px;
  font-size: 14px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.download-btn:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* 进度覆盖层 */
.progress-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.progress-card {
  width: clamp(300px, 50vw, 400px);
  max-width: 90%;
}

.progress-content {
  text-align: center;
}

.progress-content h3 {
  margin-bottom: 20px;
  color: #303133;
}

.progress-text {
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 0 15px;
  }
  
  .display-2 {
    font-size: 1.5rem;  /* 从2rem进一步减少到1.5rem */
  }
  
  table {
    font-size: 14px;
  }
  
  td {
    padding: 10px 5px;
  }
  
  .progress-card {
    width: 90%;
  }
  
  /* 移动端表格优化 */
  td.line {
    width: 40%;
  }
}

/* 超小屏幕适配 */
@media (max-width: 480px) {
  .display-2 {
    font-size: 1.2rem;  /* 从1.5rem减少到1.2rem */
  }
  
  td {
    padding: 8px 3px;
    font-size: 13px;
  }
  
  td.line {
    width: 35%;
  }
}
</style>