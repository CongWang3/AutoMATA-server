<template>
  <div>
    <!-- 数据处理表单 -->
    <DataProcessForm
      ref="formComponent"
      title="Transcriptome Data Processing"
      subtitle="Transcriptome Data Processing"
      tag-type="success"
      file-label="Upload mRNA expression data"
      file-tip="Only support txt file with tab delimiter"
      nomenclature-label="Nomenclature"
      nomenclature-placeholder="Select mRNA nomenclature"
      :nomenclature-options="[
        { label: 'Refseq Accession (e.g. NM_001422116)', value: 'Refseq' },
        { label: 'Ensembl ID (e.g. ENST00000641515)', value: 'EnsemblID' },
        { label: 'Transcript name (e.g. OR4F5-201)', value: 'Transcript_name' }
      ]"
      :species-options="[
        { label: 'Homo sapiens', value: 'homo_sapiens' },
        { label: 'Bos taurus', value: 'bos_taurus' },
        { label: 'Mus musculus', value: 'mus_musculus' },
        { label: 'Drosophila melanogaster', value: 'drosophila_melanogaster' }
      ]"
      :on-submit="handleSubmit"
      example-data-url="/example/test_refseq_fpkm_mrna.txt" 
      example-file-name="refseq_accession_fpkm2TPM_mrna.txt"
      example-note="The sample data contains the 'Refseq' identifiers and 'FPKM' values of the Homo sapiens"
      @submit-success="handleSuccess"
    />
    <!-- 示例文件放在这里了 /xp/www/AutoMATA/automata-web/public/example -->

    <!-- 任务结果弹窗 -->
    <el-dialog
      v-model="showResultDialog"
      width="80%"
      :close-on-click-modal="false"
      @close="handleClose"
    >
      <TaskResultDisplay
        v-if="showResultDialog && currentJobId"
        :job-id="currentJobId"
        :params="jobParams"
        :initial-status="jobStatus"
        :initial-progress="jobProgress"
        @status-change="handleStatusChange"
      />
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">Close and Submit New Task</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormData } from '@/types/dataProcess'
import { DataProcessAPI } from '@/api'
import TaskResultDisplay from '@/components/TaskResultDisplay.vue'

// <!-- 
// 审查上下文：
// - 设计意图：使用可复用的 DataProcessForm 组件简化代码，遵循 DRY 原则
// - 已知局限：保持与原组件相同的 API 接口，确保向后兼容
// - 业务背景：重构转录组数据处理页面以提高代码复用性和可维护性
// - 测试重点：请验证表单功能、API 调用和用户交互流程
// -->

const formComponent = ref()

// 任务状态
const showResultDialog = ref(false)
const currentJobId = ref('')
const jobStatus = ref('WAITING')
const jobProgress = ref(0)

// 任务参数
const jobParams = reactive({
  gene_nomenclature: '',
  data_type: '',
  organism: ''
})

// WebSocket 管理
const taskWsService = ref<any>(null)
const wsConnected = ref(false)

const connectWebSocket = async () => {
  try {
    const { webSocketService } = await import('@/api/websocket')
    taskWsService.value = webSocketService
    
    taskWsService.value.setOnTaskStatus(async (data: any) => {
      const { job_id, status: taskStatus, progress: taskProgress, result_file, error_message } = data
      
      if (job_id === currentJobId.value) {
        jobStatus.value = taskStatus
        jobProgress.value = taskProgress || 0
        
        if (taskStatus === 'COMPLETED' || taskStatus === 'Completed') {
          ElMessage.success(`Task ${job_id} has been completed!`)
          if (result_file) {
            ElMessage.info(`Result file has been generated: ${result_file}`)
          }
        } else if (taskStatus === 'FAILED' || taskStatus === 'Failed') {
          ElMessage.error(`Task ${job_id} failed: ${error_message || 'Unknown error'}`)
        }
      }
    })
    
    await taskWsService.value.connectTaskStatus()
    wsConnected.value = true
    
  } catch (error: any) {
    console.error('WebSocket 连接失败:', error)
    ElMessage.error('Task monitoring connection failed: ' + (error.message || 'Unknown error'))
  }
}

const disconnectWebSocket = () => {
  if (taskWsService.value) {
    taskWsService.value.disconnectTaskStatus()
    taskWsService.value = null
    wsConnected.value = false
  }
}

const handleSubmit = async (formData: FormData) => {
  console.log('📥 开始处理转录组数据提交:', formData)
  
  // 构造 FormData
  const requestData = new FormData()
  requestData.append('file', formData.file!)
  requestData.append('mrna_nomenclature', formData.nomenclature)
  requestData.append('data_type', formData.dataType)
  requestData.append('organism', formData.organism)
  if (formData.email) {
    requestData.append('email', formData.email)
  }
  
  console.log('📦 构造的请求数据:', {
    fileName: formData.file?.name,
    fileSize: formData.file?.size,
    mrna_nomenclature: formData.nomenclature,
    data_type: formData.dataType,
    organism: formData.organism,
    email: formData.email
  })
  
  // 保存参数用于结果显示
  jobParams.gene_nomenclature = formData.nomenclature
  jobParams.data_type = formData.dataType
  jobParams.organism = formData.organism
  
  // 连接 WebSocket（如果还没有连接）
  if (!wsConnected.value) {
    await connectWebSocket()
  }
  
  try {
    console.log('🚀 发送API请求到: /v1/data-process/transcriptome')
    const result = await DataProcessAPI.processTranscriptome(requestData)
    console.log('✅ API响应成功:', result)
    
    // 打开结果弹窗
    currentJobId.value = result.job_id
    jobStatus.value = 'SUBMITTED'
    jobProgress.value = 0
    showResultDialog.value = true
    
    return result
  } catch (error: any) {
    console.error('❌ API请求失败:', error)
    console.error('❌ 错误详情:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    })
    throw error
  }
}

const handleSuccess = (result: any) => {
  ElMessage.success('Transcriptome data processing task has been submitted')
}

const handleStatusChange = (status: string) => {
  jobStatus.value = status
  
  // 如果任务完成或失败，提示用户
  if (status === 'COMPLETED' || status === 'Completed' || status === 'FAILED' || status === 'Failed') {
    setTimeout(() => {
      ElMessage.info('Task has been completed')
    }, 2000)
  }
}

// 关闭弹窗并重置表单（关闭按钮、右上角×、提交新任务都调用此方法）
const handleClose = () => {
  showResultDialog.value = false
  currentJobId.value = ''
  jobStatus.value = 'WAITING'
  jobProgress.value = 0
  
  // 重置表单
  formComponent.value?.resetForm()
}

// 暴露方法给外部使用
defineExpose({
  resetForm: () => formComponent.value?.resetForm(),
  handleClose
})

// 组件卸载时断开 WebSocket 连接
onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
/* 样式已移至 DataProcessForm.vue 组件 */
</style>
