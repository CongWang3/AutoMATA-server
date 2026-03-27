<template>
  <AnalysisForm
    title="Comprehensive differential expression analysis"
    subtitle="Comprehensive Analysis Flow"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    :multiple-files="true"
    :second-file-visible="true"
    file-field-name="expression_file"
    second-file-field-name="group_file"
    file-label="1. Upload expression data file"
    second-file-label="2. Upload sample data file"
    example-data-url="/example/draw_example/read_count.txt"
    example-file-name="read_count.txt"
    second-example-url="/example/draw_example/group_info.txt"
    second-example-file-name="group_info.txt"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

/**
 * 综合分析表单字段配置
 * 字段名需与后端 API Form 参数名匹配
 */
const analysisFields: AnalysisField[] = [
  {
    type: 'select',
    name: 'data_type',
    label: 'Select data type',
    defaultValue: 'read_counts',
    options: [
      { label: 'Read Counts', value: 'read_counts' },
      { label: 'FPKM', value: 'fpkm' }
    ]
  },
  {
    type: 'select',
    name: 'organism',
    label: 'Organism',
    defaultValue: 'Homo_sapiens',
    options: [
      { label: 'Homo sapiens', value: 'Homo_sapiens' },
      { label: 'Bos taurus', value: 'Bovine' },
      { label: 'Mus musculus', value: 'Mus_musculus' },
      { label: 'Drosophila melanogaster', value: 'Drosophila_melanogaster' }
    ]
  },
  {
    type: 'select',
    name: 'correction',
    label: 'Correction method',
    defaultValue: 'BH',
    options: [
      { label: 'BH (Benjamini-Hochberg)', value: 'BH' },
      { label: 'BY (Benjamini-Yekutieli)', value: 'BY' },
      { label: 'holm', value: 'holm' },
      { label: 'hochberg', value: 'hochberg' },
      { label: 'hommel', value: 'hommel' },
      { label: 'bonferroni', value: 'bonferroni' },
      { label: 'none', value: 'none' }
    ]
  },
  {
    type: 'number',
    name: 'fc_threshold',
    label: 'log2FC threshold',
    defaultValue: 1,
    min: 0,
    max: 10,
    step: 0.01,
    tip: 'NOTE: |log2FC| > threshold. Generally 0.58, 1 or 2'
  },
  {
    type: 'number',
    name: 'padj_threshold',
    label: 'padj threshold',
    defaultValue: 0.05,
    min: 0,
    max: 1,
    step: 0.01,
    tip: 'NOTE: padj < threshold. Generally 0.05'
  }
]

/**
 * 提交综合分析任务
 * @param formData 表单数据
 */
const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runComprehensive(formData)
}
</script>
