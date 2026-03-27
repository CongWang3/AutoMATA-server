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
    label: 'Organism',
    defaultValue: 'Mus_musculus',
    options: [
      { label: 'Mus musculus', value: 'Mus_musculus' },
      { label: 'Bos taurus', value: 'Bos_taurus' },
      { label: 'Homo sapiens', value: 'Homo_sapiens' },
      { label: 'Drosophila melanogaster', value: 'Drosophila_melanogaster' }
    ],
    required: true
  },
  {
    type: 'select',
    name: 'nomenclature',
    label: 'Nomenclature',
    defaultValue: 'SYMBOL',
    options: [
      { label: 'Gene Symbol', value: 'SYMBOL' },
      { label: 'Ensembl ID', value: 'ENSEMBL' },
      { label: 'ENTREZID', value: 'ENTREZID' }
    ],
    required: true
  },
  {
    type: 'number',
    name: 'thres',
    label: 'Score threshold',
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
    label: 'Min nodes',
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
