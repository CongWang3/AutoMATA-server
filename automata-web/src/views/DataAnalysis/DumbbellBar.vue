<template>
  <AnalysisForm
    title="Dumbbell Bar Chart"
    subtitle="Dumbbell Bar Chart"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    :multipleFiles="true"
    :second-file-visible="true"
    file-field-name="file1"
    file-label="1. Upload dumbbell data set"
    second-file-label="2. Upload bar data set"
    example-data-url="/example/draw_example/dumbbell_example.txt"
    example-file-name="dumbbell_example.txt"
    second-example-url="/example/draw_example/dumbbell_barplot_example.txt"
    second-example-file-name="dumbbell_barplot_example.txt"
    example-note="Please make sure that the first clumn of the bar data set is the same as the first column of the dumbbell data set"
    example-image-url="/images/dumbbell_bar_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

const analysisFields: AnalysisField[] = [
  {
    type: 'input',
    required: true,
    name: 'x_label',
    label: 'Label for the x-axis',
    placeholder: 'e.g. Number of Transitions'
  },
  {
    type: 'input',
    required: true,
    name: 'mark_fams',
    label: 'Terms to emphasize',
    placeholder: 'e.g. Notothenioid,Sebastidae,Liparidae,Zoarcidae,Pleuronectidae',
    tip: 'Please separate them by English comma, and entered terms should be included in the uploaded data set'
  }
]

const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runDumbbellBar(formData)
}
</script>
