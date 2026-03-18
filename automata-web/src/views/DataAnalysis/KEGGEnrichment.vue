<template>
  <AnalysisForm
    title="KEGG Enrichment Analysis"
    subtitle="KEGG 富集分析"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/kegg_enrichment_example.txt"
    example-file-name="kegg_enrichment_example.txt"
    example-image-url="/images/kegg_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

/**
 * KEGG 富集分析字段配置
 * 参数对应后端 API 字段名
 */
const analysisFields: AnalysisField[] = [
  {
    type: 'select',
    name: 'organism',
    label: 'The organism of the input data',
    defaultValue: '0',
    options: [
      { label: 'Homo sapiens', value: '0' },
      { label: 'Bos taurus', value: '1' },
      { label: 'Mus musculus', value: '2' },
      { label: 'Drosophila melanogaster', value: '3' }
    ],
    required: true
  },
  {
    type: 'number',
    name: 'pvalue',
    label: 'pvalue threshold (range [0, 1])',
    defaultValue: 0.1,
    min: 0,
    max: 1,
    step: 0.01,
    required: true,
    tip: 'The threshold range is [0, 1]'
  },
  {
    type: 'number',
    name: 'qvalue',
    label: 'qvalue threshold (range [0, 1])',
    defaultValue: 0.1,
    min: 0,
    max: 1,
    step: 0.01,
    required: true,
    tip: 'The threshold range is [0, 1]'
  },
  {
    type: 'select',
    name: 'correction',
    label: 'Correction Method',
    defaultValue: '0',
    options: [
      { label: 'BH (Benjamini-Hochberg)', value: '0' },
      { label: 'BY (Benjamini-Yekutieli)', value: '1' },
      { label: 'holm (Holm\'s step-down procedure)', value: '2' },
      { label: 'hochberg (Hochberg\'s step-up procedure)', value: '3' },
      { label: 'hommel (Hommel\'s procedure)', value: '5' },
      { label: 'bonferroni (Bonferroni correction)', value: '6' },
      { label: 'fdr (False Discovery Rate)', value: '7' },
      { label: 'none', value: '8' }
    ],
    required: true
  },
  {
    type: 'radio',
    name: 'type',
    label: 'Plot type',
    defaultValue: 'bubble',
    options: [
      { label: 'Bubble', value: 'bubble' },
      { label: 'Chord', value: 'chord' },
      { label: 'Cluster', value: 'cluster' }
    ],
    required: true
  },
  {
    type: 'number',
    name: 'termNum',
    label: 'Number of terms to display',
    defaultValue: 5,
    min: 1,
    max: 50,
    step: 1,
    required: true
  }
]

/**
 * 提交 KEGG 富集分析
 * @param formData 表单数据
 */
const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runKEGGEnrichment(formData)
}
</script>
