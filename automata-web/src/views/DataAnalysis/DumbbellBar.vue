<template>
  <AnalysisForm
    title="Dumbbell Bar Chart"
    subtitle="哑铃柱状图"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    :multiple-files="true"
    file-label="1. Upload dumbbell data set"
    second-file-label="2. Upload bar data set"
    example-data-url="/example/draw_example/dumbbell_example.txt"
    example-file-name="dumbbell_example.txt"
    second-example-url="/example/draw_example/dumbbell_barplot_example.txt"
    second-example-file-name="dumbbell_barplot_example.txt"
    example-note="请确保柱状图数据的第一列与哑铃图数据的第一列相同"
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
  return await AnalysisAPI.runDumbbellBar(formData)
}
</script>
