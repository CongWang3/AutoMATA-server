<template>
  <AnalysisForm
    title="Differential Gene Cluster Heatmap"
    subtitle="Differential Gene Cluster Heatmap"
    :fields="analysisFields"
    :on-submit="handleSubmit"
    example-data-url="/example/draw_example/df_gene_cluster_example.txt"
    example-file-name="df_gene_cluster_example.txt"
    example-image-url="/images/df_cluster_example.png"
  />
</template>

<script setup lang="ts">
import AnalysisForm from '@/components/AnalysisForm.vue'
import { AnalysisAPI } from '@/api'
import type { AnalysisField } from '@/api/analysis'

// 聚类距离方法选项
const clusteringDistanceMethods = [
  { label: 'Euclidean', value: 'euclidean' },
  { label: 'Correlation', value: 'correlation' },
  { label: 'Maximum', value: 'maximum' },
  { label: 'Manhattan', value: 'manhattan' },
  { label: 'Canberra', value: 'canberra' },
  { label: 'Binary', value: 'binary' },
  { label: 'Minkowski', value: 'minkowski' }
]

const analysisFields: AnalysisField[] = [
  {
    type: 'radio',
    name: 'show_col_name',
    label: 'Show column name',
    defaultValue: 'FALSE',
    options: [
      { label: 'Yes', value: 'TRUE' },
      { label: 'No', value: 'FALSE' }
    ]
  },
  {
    type: 'radio',
    name: 'show_row_name',
    label: 'Show row name',
    defaultValue: 'TRUE',
    options: [
      { label: 'Yes', value: 'TRUE' },
      { label: 'No', value: 'FALSE' }
    ]
  },
  {
    type: 'select',
    name: 'clustering_dis_row',
    label: 'Cluster method for row',
    defaultValue: 'euclidean',
    options: clusteringDistanceMethods
  },
  {
    type: 'select',
    name: 'clustering_dis_col',
    label: 'Cluster method for col',
    defaultValue: 'euclidean',
    options: clusteringDistanceMethods
  },
  {
    type: 'radio',
    name: 'scale',
    label: 'Center and scale data',
    defaultValue: 'none',
    options: [
      { label: 'No', value: 'none' },
      { label: 'Scale in row direction', value: 'row' },
      { label: 'Scale in column direction', value: 'col' }
    ]
  },
  {
    type: 'radio',
    name: 'annotation_type',
    label: 'Row/col annotation',
    defaultValue: 'only_data',
    options: [
      { label: 'No', value: 'only_data' },
      { label: 'Add row annotation', value: 'data_with_row_annotation' },
      { label: 'Add column annotation', value: 'data_with_col_annotation' },
      { label: 'Add both', value: 'data_with_row_col' }
    ],
    tip: 'Upload annotation files via additional file upload fields if needed'
  },
  {
    type: 'radio',
    name: 'group',
    label: 'Display data by group',
    defaultValue: 'FALSE',
    options: [
      { label: 'Yes', value: 'TRUE' },
      { label: 'No', value: 'FALSE' }
    ],
    visible: (formValues) => 
      formValues.annotation === 'data_with_col_annotation' || 
      formValues.annotation === 'data_with_row_col'
  }
]

const handleSubmit = async (formData: FormData) => {
  return await AnalysisAPI.runGeneClusterHeatmap(formData)
}
</script>
