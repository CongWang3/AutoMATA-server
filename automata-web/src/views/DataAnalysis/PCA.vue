<template>
  <AnalysisForm
    title="PCA Analysis"
    subtitle="Principal Component Analysis"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/pca_example.txt"
    example-file-name="pca_example.txt"
    example-image-url="/images/pca_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

// PERMANOVA 距离方法选项
const permanovaMethods = [
  { label: 'Bray', value: 'bray' },
  { label: 'Manhattan', value: 'manhattan' },
  { label: 'Euclidean', value: 'euclidean' },
  { label: 'Canberra', value: 'canberra' },
  { label: 'Clark', value: 'clark' },
  { label: 'Kulczynski', value: 'kulczynski' },
  { label: 'Jaccard', value: 'jaccard' },
  { label: 'Gower', value: 'gower' },
  { label: 'AltGower', value: 'altgower' },
  { label: 'Morisita', value: 'morisita' },
  { label: 'Horn', value: 'horn' },
  { label: 'Mountford', value: 'mountford' },
  { label: 'Raup', value: 'raup' },
  { label: 'Binomial', value: 'binomial' },
  { label: 'Chao', value: 'chao' },
  { label: 'Cao', value: 'cao' },
  { label: 'Mahalanobis', value: 'mahalanobis' },
  { label: 'Chisq', value: 'chisq' },
  { label: 'Chord', value: 'chord' },
  { label: 'Hellinger', value: 'hellinger' },
  { label: 'Aitchison', value: 'aitchison' },
  { label: 'Robust.aitchison', value: 'robust.aitchison' }
]

const analysisFields: AnalysisField[] = [
  {
    type: 'number',
    name: 'confidence',
    label: 'Confidence level',
    defaultValue: 0.95,
    min: 0,
    max: 1,
    step: 0.01,
    placeholder: 'Enter confidence level (0-1)'
  },
  {
    type: 'radio',
    name: 'boundary',
    label: 'Boundary plot',
    defaultValue: 'TRUE',
    options: [
      { label: 'Add boundary plot', value: 'TRUE' },
      { label: "Don't add", value: 'FALSE' }
    ]
  },
  {
    type: 'radio',
    name: 'permanova',
    label: 'PERMANOVA analysis',
    defaultValue: 'FALSE',
    options: [
      { label: 'Conduct PERMANOVA', value: 'TRUE' },
      { label: "Don't conduct", value: 'FALSE' }
    ]
  },
  {
    type: 'select',
    name: 'method',
    label: 'PERMANOVA distance',
    defaultValue: 'bray',
    options: permanovaMethods,
    visible: (formValues) => formValues.permanova === 'TRUE'
  }
]

const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runPCA(formData)
}
</script>
