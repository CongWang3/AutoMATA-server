<template>
  <AnalysisForm
    title="PPI Network Analysis"
    subtitle="蛋白质相互作用网络"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/ppi_example.txt"
    example-file-name="ppi_example.txt"
    example-image-url="/images/ppi_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

/**
 * PPI 蛋白互作网络分析字段配置
 * 参数对应后端 API 字段名
 */
const analysisFields: AnalysisField[] = [
  {
    type: 'select',
    name: 'organism',
    label: 'The organism of the input data',
    defaultValue: '0',
    options: [
      { label: 'Mus musculus', value: '0' },
      { label: 'Bos taurus', value: '1' },
      { label: 'Homo sapiens', value: '2' },
      { label: 'Drosophila melanogaster', value: '3' }
    ],
    required: true
  },
  {
    type: 'select',
    name: 'nomenclature',
    label: 'The nomenclature used in the data set',
    defaultValue: '0',
    options: [
      { label: 'Gene Symbol', value: '0' },
      { label: 'Ensembl ID', value: '1' },
      { label: 'ENTREZID', value: '2' }
    ],
    required: true
  },
  {
    type: 'number',
    name: 'thres',
    label: 'Filtered threshold of score for PPI analysis',
    defaultValue: 400,
    min: 0,
    max: 1000,
    step: 10,
    required: true,
    tip: 'Higher scores indicate higher confidence interactions'
  },
  {
    type: 'number',
    name: 'show',
    label: 'Minimum number of nodes to display gene names',
    defaultValue: 5,
    min: 1,
    max: 100,
    step: 1,
    required: true,
    tip: 'Only gene names with more than this number of nodes are shown in the figure'
  },
  {
    type: 'radio',
    name: 'type',
    label: 'Plot type',
    defaultValue: 'linear',
    options: [
      { label: 'Linear', value: 'linear' },
      { label: 'KK', value: 'kk' },
      { label: 'Stress', value: 'stress' }
    ],
    required: true
  }
]

/**
 * 提交 PPI 网络分析
 * @param formData 表单数据
 */
const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runPPI(formData)
}
</script>
