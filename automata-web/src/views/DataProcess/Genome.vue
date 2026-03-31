<template>
  <div>
    <!-- 数据处理表单 -->
    <DataProcessForm
      ref="formComponent"
      title="Genome Data Processing"
      subtitle="Genome Data Processing"
      file-label="Upload gene expression data"
      file-tip="Only support txt file with tab delimiter"
      nomenclature-label="Nomenclature"
      nomenclature-placeholder="Select gene nomenclature"
      :nomenclature-options="[
        { label: 'Gene ID', value: 'GeneID' },
        { label: 'Ensembl ID', value: 'EnsemblID' },
        { label: 'Gene Symbol', value: 'Symbol' }
      ]"
      :species-options="[
        { label: 'Homo sapiens', value: 'homo_sapiens' },
        { label: 'Mus musculus', value: 'mus_musculus' },
        { label: 'Drosophila melanogaster', value: 'drosophila_melanogaster' },
        { label: 'Bos taurus', value: 'bos_taurus' }
      ]"
      :on-submit="handleSubmit"
      example-data-url="/example/test_geneid_multi_species.txt"
      example-file-name="geneid_multi_species_example.txt"
      example-note="The sample data contains the 'GeneID' and 'TPM' values of multiple species"
      @submit-success="handleSuccess"
    />
    <!-- 示例文件在这：/xp/www/AutoMATA/automata-web/public/example/test_geneid_multi_species.txt -->
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
          ElMessage.success(`Task ${job_id} completed`)
          if (result_file) {
            ElMessage.info(`Result file: ${result_file}`)
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
    taskWsService.value.disconnect()
    taskWsService.value = null
    wsConnected.value = false
  }
}

const handleSubmit = async (formData: FormData) => {
  // 构造 FormData
  const requestData = new FormData()
  requestData.append('file', formData.file!)
  requestData.append('gene_nomenclature', formData.nomenclature)
  requestData.append('data_type', formData.dataType)
  requestData.append('organism', formData.organism)
  if (formData.email) {
    requestData.append('email', formData.email)
  }
  
  // 保存参数用于结果显示
  jobParams.gene_nomenclature = formData.nomenclature
  jobParams.data_type = formData.dataType
  jobParams.organism = formData.organism
  
  // 连接 WebSocket（如果还没有连接）
  if (!wsConnected.value) {
    await connectWebSocket()
  }
  
  const result = await DataProcessAPI.processGenome(requestData)
  
  // 打开结果弹窗
  currentJobId.value = result.job_id
  jobStatus.value = 'SUBMITTED'
  jobProgress.value = 0
  showResultDialog.value = true
  
  return result
}

const handleSuccess = (result: any) => {
  ElMessage.success('Genome data processing task submitted')
}

const handleStatusChange = (status: string) => {
  jobStatus.value = status
  
  // 如果任务完成或失败，提示用户
  if (status === 'COMPLETED' || status === 'Completed' || status === 'FAILED' || status === 'Failed') {
    setTimeout(() => {
      ElMessage.info('Task finished')
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