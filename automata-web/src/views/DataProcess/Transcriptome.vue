<template>
  <DataProcessForm
    ref="formComponent"
    title="转录组数据处理"
    subtitle="Transcriptome Data Processing"
    tag-type="success"
    file-label="1. 上传 mRNA 表达数据"
    file-tip="仅支持 txt、csv、tsv 格式的文件"
    nomenclature-label="2. mRNA 命名方式"
    nomenclature-placeholder="请选择 mRNA 命名方式"
    :nomenclature-options="[
      { label: 'Refseq', value: 'Refseq' },
      { label: 'Ensembl ID', value: 'EnsemblID' },
      { label: 'Transcript name', value: 'Transcript_name' }
    ]"
    :species-options="[
      { label: 'Homo sapiens', value: 'homo_sapiens' },
      { label: 'Mus musculus', value: 'mus_musculus' },
      { label: 'Drosophila melanogaster', value: 'drosophila_melanogaster' },
      { label: 'Bos taurus', value: 'bos_taurus' }
    ]"
    :on-submit="handleSubmit"
    example-data-url="/example/test_refseq_fpkm_mrna.txt"
    example-file-name="refseq_fpkm_mrna_example.txt"
    @submit-success="handleSuccess"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormData } from '@/types/dataProcess'
import { DataProcessAPI } from '@/api'

// <!-- 
// 审查上下文：
// - 设计意图：使用可复用的 DataProcessForm 组件简化代码，遵循 DRY 原则
// - 已知局限：保持与原组件相同的 API 接口，确保向后兼容
// - 业务背景：重构转录组数据处理页面以提高代码复用性和可维护性
// - 测试重点：请验证表单功能、API 调用和用户交互流程
// -->

const formComponent = ref()

const handleSubmit = async (formData: FormData) => {
  // 构造 FormData
  const requestData = new FormData()
  requestData.append('file', formData.file!)
  requestData.append('mrna_nomenclature', formData.nomenclature)
  requestData.append('data_type', formData.dataType)
  requestData.append('organism', formData.organism)
  if (formData.email) {
    requestData.append('email', formData.email)
  }
  
  return await DataProcessAPI.processTranscriptome(requestData)
}

const handleSuccess = (result: any) => {
  ElMessage.success('转录组数据处理任务已提交')
}

// 暴露方法给外部使用
defineExpose({
  resetForm: () => formComponent.value?.resetForm()
})
</script>

<style scoped>
/* 样式已移至 DataProcessForm.vue 组件 */
</style>
