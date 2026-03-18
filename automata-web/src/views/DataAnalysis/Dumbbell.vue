<template>
  <AnalysisForm
    title="Dumbbell Plot"
    subtitle="哑铃图"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/dumbbell_example.txt"
    example-file-name="dumbbell_example.txt"
    example-image-url="/images/dumbbell_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

const analysisFields: AnalysisField[] = [
  {
    type: 'input',
    name: 'x_label',
    label: 'Label for the x-axis',
    placeholder: 'e.g. Number of Transitions'
  },
  {
    type: 'input',
    name: 'mark_fams',
    label: 'Terms to emphasize',
    placeholder: 'e.g. Notothenioid,Sebastidae,Liparidae,Zoarcidae,Pleuronectidae',
    tip: 'Please separate them by English comma, and entered terms should be included in the uploaded data set'
  }
]

const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runDumbbell(formData)
}
</script>
