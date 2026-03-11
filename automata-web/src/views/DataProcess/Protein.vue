<template>
  <div>
    <!-- 数据处理表单 -->
    <DataProcessForm
      ref="formComponent"
      title="蛋白质数据处理"
      subtitle="Protein Data Processing"
      tag-type="warning"
      file-label="1. 上传蛋白质表达数据"
      file-tip="仅支持 txt、csv、tsv 格式的文件"
      nomenclature-label="2. 蛋白质命名方式"
      nomenclature-placeholder="请选择蛋白质命名方式"
      :nomenclature-options="[
        { label: 'UniProt Entry', value: 'Entry' },
        { label: 'RefSeq Accession', value: 'RefSeq' },
        { label: 'AlphaFoldDB ID', value: 'AlphaFoldDB' },
        { label: 'Ensembl ID', value: 'Ensembl' }
      ]"
      :species-options="[
        { label: 'Homo sapiens', value: 'homo_sapiens' },
        { label: 'Bos taurus', value: 'bos_taurus' },
        { label: 'Mus musculus', value: 'mus_musculus' },
        { label: 'Drosophila melanogaster', value: 'drosophila_melanogaster' }
      ]"
      :on-submit="handleSubmit"
      example-data-url="/example/test_protein_refseq.txt"
      example-file-name="protein_refseq_example.txt"
      example-note="示例数据包含RefSeq蛋白质标识符，请选择对应物种查看结果"
      @submit-success="handleSuccess"
    />
    
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
          <el-button @click="handleClose">关闭并提交新任务</el-button>
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

// <!-- 
// 审查上下文：
// - 设计意图：实现蛋白质数据处理功能，支持多种蛋白质命名方式和物种
// - 已知局限：需要相应的数据库表支持蛋白质标识符到基因符号的映射
// - 业务背景：提供与基因组、转录组类似的蛋白质数据标准化处理功能
// - 测试重点：请验证不同命名方式的处理、物种支持、结果文件生成
// -->

const formComponent = ref()

// 任务状态
const showResultDialog = ref(false)
const currentJobId = ref('')
const jobStatus = ref('WAITING')
const jobProgress = ref(0)

// 任务参数
const jobParams = reactive({
  protein_nomenclature: '',
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
          ElMessage.success(`任务 ${job_id} 已完成！`)
          if (result_file) {
            ElMessage.info(`结果文件已生成: ${result_file}`)
          }
        } else if (taskStatus === 'FAILED' || taskStatus === 'Failed') {
          ElMessage.error(`任务 ${job_id} 失败: ${error_message || '未知错误'}`)
        }
      }
    })
    
    await taskWsService.value.connectTaskStatus()
    wsConnected.value = true
    
  } catch (error: any) {
    console.error('WebSocket 连接失败:', error)
    ElMessage.error('任务监控连接失败: ' + (error.message || '未知错误'))
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
  requestData.append('protein_nomenclature', formData.nomenclature)
  requestData.append('organism', formData.organism)
  if (formData.email) {
    requestData.append('email', formData.email)
  }
  
  // 保存参数用于结果显示
  jobParams.protein_nomenclature = formData.nomenclature
  jobParams.organism = formData.organism
  
  // 连接 WebSocket（如果还没有连接）
  if (!wsConnected.value) {
    await connectWebSocket()
  }
  
  const result = await DataProcessAPI.processProtein(requestData)
  
  // 打开结果弹窗
  currentJobId.value = result.job_id
  jobStatus.value = 'SUBMITTED'
  jobProgress.value = 0
  showResultDialog.value = true
  
  return result
}

const handleSuccess = (result: any) => {
  ElMessage.success('蛋白质数据处理任务已提交')
}

const handleStatusChange = (status: string) => {
  jobStatus.value = status
  
  // 如果任务完成或失败，提示用户
  if (status === 'COMPLETED' || status === 'Completed' || status === 'FAILED' || status === 'Failed') {
    setTimeout(() => {
      ElMessage.info('任务已完成')
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