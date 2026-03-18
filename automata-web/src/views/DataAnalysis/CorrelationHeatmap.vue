<template>
  <AnalysisForm
    title="Correlation Heatmap"
    subtitle="相关性热图"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/cor_heatmap_example.txt"
    example-file-name="cor_heatmap_example.txt"
    example-image-url="/images/cor_heatmap_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

// 相关性热图无额外参数，只需要文件上传和邮箱
const analysisFields: AnalysisField[] = []

const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runCorrelationHeatmap(formData)
}
</script>
