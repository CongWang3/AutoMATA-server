<template>
  <AnalysisForm
    title="Venn Diagram"
    subtitle="韦恩图"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/venn_example.txt"
    example-file-name="venn_example.txt"
    example-image-url="/images/venn_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

const analysisFields: AnalysisField[] = [
  {
    type: 'radio',
    name: 'plot',
    label: 'Choose plot type',
    defaultValue: 'Venn',
    options: [
      { label: 'Classic venn plot', value: 'Venn' },
      { label: 'Vennpie plot', value: 'Vennpie' },
      { label: 'Bar plot', value: 'Barplot' }
    ]
  }
]

const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runVenn(formData)
}
</script>
