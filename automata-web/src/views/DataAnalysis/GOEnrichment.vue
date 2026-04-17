<template>
  <AnalysisForm
    title="GO Enrichment Analysis"
    subtitle="GO Enrichment Analysis"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/go_enrichment_example.txt"
    example-file-name="go_enrichment_example.txt"
    example-image-url="/images/go_example.png"
    example-note="Chord, Cluster, Circle plots need input with 'logFC' column"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

/**
 * GO 富集分析字段配置
 * 参数对应后端 API 字段名
 */
const analysisFields: AnalysisField[] = [
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
    ],
    required: true
  },
  {
    type: 'number',
    name: 'pvalue',
    label: 'pvalue threshold',
    defaultValue: 0.05,
    min: 0,
    max: 1,
    step: 0.01,
    required: true,
    tip: 'The threshold range is [0, 1]'
  },
  {
    type: 'number',
    name: 'qvalue',
    label: 'qvalue threshold',
    defaultValue: 0.05,
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
    defaultValue: 'BH',
    options: [
      { label: 'BH (Benjamini-Hochberg)', value: 'BH' },
      { label: 'BY (Benjamini-Yekutieli)', value: 'BY' },
      { label: 'holm (Holm\'s step-down procedure)', value: 'holm' },
      { label: 'hochberg (Hochberg\'s step-up procedure)', value: 'hochberg' },
      { label: 'hommel (Hommel\'s procedure)', value: 'hommel' },
      { label: 'bonferroni (Bonferroni correction)', value: 'bonferroni' },
      { label: 'fdr (False Discovery Rate)', value: 'fdr' },
      { label: 'none', value: 'none' }
    ],
    required: true
  },
  {
    type: 'radio',
    name: 'plot_type',
    label: 'Plot type',
    defaultValue: 'bubble',
    options: [
      { label: 'Bubble', value: 'bubble' },
      { label: 'Barplot', value: 'barplot' },
      { label: 'Chord', value: 'chord' },
      { label: 'Cluster', value: 'cluster' },
      { label: 'Circle', value: 'circle' }
    ],
    required: true
  },
  {
    type: 'number',
    name: 'term_num',
    label: 'Terms per ontology',
    defaultValue: 5,
    min: 1,
    max: 50,
    step: 1,
    required: true
  }
]

/**
 * 提交 GO 富集分析
 * @param formData 表单数据
 */
const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runGOEnrichment(formData)
}
</script>
