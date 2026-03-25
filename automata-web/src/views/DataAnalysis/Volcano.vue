<template>
  <AnalysisForm
    title="Volcano Plot"
    subtitle="火山图"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    second-file-label="2. Upload GMT file for GSEA analysis"
    accept-types=".txt,.csv,.tsv"
    file-tip="仅支持 txt、csv、tsv格式的文件"
    :second-file-visible="(values: Record<string, any>) => values.gsea_analysis === 'yes'"
    second-file-field-name="gmt_file"
    second-accept-types=".gmt"
    second-file-tip="仅支持gmt格式的文件"
    :second-example-url="'/example/draw_example/volcano_gsea_example.gmt'"
    second-example-file-name="volcano_gsea_example.gmt"
    example-data-url="/example/draw_example/volcano_example.txt"
    example-file-name="volcano_example.txt"
    example-note="请确保数据集的列名为 gene, logFC, padj，分隔符为 Tab (\t)"
    example-image-url="/images/volcano_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

const analysisFields: AnalysisField[] = [
  {
    type: 'radio',
    name: 'gsea_analysis',
    label: 'Conduct GSEA analysis',
    defaultValue: 'no',
    options: [
      { label: 'Yes', value: 'yes' },
      { label: 'No', value: 'no' }
    ]
  },
  {
    required: false,
    type: 'input',
    name: 'gene_sig',
    label: 'Emphasized Genes',
    placeholder: 'e.g. KRAS,FOSL1,MYC (separate by comma; genes must be in uploaded dataset)',
    // tip: 'Please separate them by English comma, and entered gene names should be included in the uploaded data set'
  },
  {
    type: 'number',
    name: 'fc_thr',
    label: 'log2FC threshold',
    defaultValue: 0.5,
    min: 0,
    step: 0.1,
    tip: '|log2FC| > threshold. Generally 0.58, 1 or 2'
  },
  {
    type: 'number',
    name: 'padj_thr',
    label: 'padj threshold',
    defaultValue: 0.05,
    min: 0,
    max: 1,
    step: 0.01,
    tip: 'padj < threshold. Generally 0.05'
  },
  {
    type: 'number',
    name: 'top',
    label: 'TOP gene count',
    defaultValue: 200,
    min: 1,
    step: 1,
    tip: 'The TOP shows the higher-order gene that needs to be displayed'
  },
  {
    type: 'number',
    name: 'top_fc_thr',
    label: 'log2FC for TOP genes',
    defaultValue: 1,
    min: 0,
    step: 0.1
  },
  {
    type: 'number',
    name: 'top_padj_thr',
    label: 'padj for TOP genes',
    defaultValue: 0.01,
    min: 0,
    max: 1,
    step: 0.01
  }
]

const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runVolcano(formData)
}
</script>
