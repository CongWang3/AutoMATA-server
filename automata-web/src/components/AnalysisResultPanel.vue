<template>
  <div class="analysis-result-panel">
    <!-- 等待 / 分析中 -->
    <div v-if="phase === 'waiting'" class="phase waiting">
      <div class="banner">
        <h2 class="banner-title">数据分析任务</h2>
        <p class="hint">正在分析中，请稍候</p>
        <p class="job-line">JobID：{{ jobId }}</p>
      </div>
      <table class="info-table">
        <tbody>
          <tr>
            <td class="label-cell">JobID</td>
            <td>{{ jobId }}</td>
          </tr>
          <tr>
            <td class="label-cell">Analysis Type</td>
            <td>{{ analysisTypeLabel }}</td>
          </tr>
          <tr v-for="(row, idx) in paramRows" :key="'w-' + idx" :class="{ stripe: idx % 2 === 1 }">
            <td class="label-cell">{{ row.label }}</td>
            <td>{{ row.value }}</td>
          </tr>
          <tr class="stripe">
            <td class="label-cell">Running</td>
            <td>
              <img
                v-if="statusUpper === 'PROCESSING'"
                src="/images/progress_bar_new.gif"
                alt=""
                class="progress-gif"
              >
              <span v-else>Submitted</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 成功 -->
    <div v-else-if="phase === 'completed'" class="phase completed">
      <div class="banner">
        <h2 class="banner-title">Result</h2>
      </div>
      <table class="info-table">
        <tbody>
          <tr>
            <td class="label-cell">JobID</td>
            <td>{{ jobId }}</td>
          </tr>
          <tr>
            <td class="label-cell">Analysis Type</td>
            <td>{{ analysisTypeLabel }}</td>
          </tr>
          <tr v-for="(row, idx) in paramRows" :key="'c-' + idx" :class="{ stripe: idx % 2 === 1 }">
            <td class="label-cell">{{ row.label }}</td>
            <td>{{ row.value }}</td>
          </tr>
          <tr>
            <td class="label-cell">
              <div class="preview">
                <img
                  v-if="previewUrl"
                  :key="previewUrl"
                  :src="previewUrl"
                  height="400"
                  alt="Result"
                  class="preview-img"
                >
                <span v-else class="preview-placeholder">图片生成后可预览</span>
              </div>
            </td>
            <td>
              <el-dropdown trigger="click" @command="onDownloadFormat">
                <el-button
                  type="primary"
                  size="default"
                >
                  Download Figure
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="item in downloadFormats"
                      :key="item.ext"
                      :command="item.ext"
                      :disabled="!hasFile(item.ext)"
                    >
                      {{ item.label }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 失败 -->
    <div v-else-if="phase === 'failed'" class="phase failed">
      <div class="banner">
        <h2 class="banner-title">Result</h2>
        <p class="job-line fail-line">JobID：{{ jobId }}，处理失败</p>
      </div>
      <table class="info-table">
        <tbody>
          <tr>
            <td class="label-cell">Analysis Type</td>
            <td>{{ analysisTypeLabel }}</td>
          </tr>
          <tr v-for="(row, idx) in paramRows" :key="'f-' + idx" :class="{ stripe: idx % 2 === 1 }">
            <td class="label-cell">{{ row.label }}</td>
            <td>{{ row.value }}</td>
          </tr>
          <tr class="stripe">
            <td class="label-cell">Data Process Result</td>
            <td class="error-cell">{{ errorMessage || '未知错误' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="progress > 0 && progress < 100 && phase === 'waiting'"
      class="progress-inline"
    >
      <el-progress :percentage="progress" :stroke-width="10" striped striped-flow />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { AnalysisAPI, type AnalysisResultFile } from '@/api/analysis'

export interface AnalysisParamRow {
  label: string
  value: string
}

const props = defineProps<{
  jobId: string
  status: string
  progress: number
  analysisTypeLabel: string
  paramRows: AnalysisParamRow[]
  resultFiles: AnalysisResultFile[]
  errorMessage?: string
}>()

const statusUpper = computed(() => String(props.status || '').toUpperCase())

const phase = computed<'waiting' | 'completed' | 'failed'>(() => {
  const s = statusUpper.value
  if (s === 'FAILED') return 'failed'
  if (s === 'COMPLETED') return 'completed'
  return 'waiting'
})

const pngFile = computed(() => {
  const files = props.resultFiles || []
  return (
    files.find((f) => f.format === 'png') ||
    files.find((f) => f.filename.toLowerCase().endsWith('.png')) ||
    null
  )
})

const previewUrl = computed(() => {
  if (!props.jobId || phase.value !== 'completed') return ''
  if (!pngFile.value) return ''

  const url = (pngFile.value as any).url as string | undefined
  if (url) {
    const sep = url.includes('?') ? '&' : '?'
    return `${url}${sep}t=${Date.now()}`
  }

  return `${AnalysisAPI.getResultFileUrl(props.jobId, pngFile.value.filename)}?t=${Date.now()}`
})

const downloadFormats = [
  { label: 'PDF', ext: 'pdf' },
  { label: 'PNG', ext: 'png' },
  { label: 'SVG', ext: 'svg' },
  { label: 'TIFF', ext: 'tiff' },
  { label: 'JPEG', ext: 'jpeg' },
  { label: 'BMP', ext: 'bmp' }
] as const

function findFileByExt(ext: string): AnalysisResultFile | null {
  const files = props.resultFiles || []
  const e = ext.toLowerCase()
  return (
    files.find((f) => (f.format || '').toLowerCase() === e) ||
    files.find((f) => f.filename.toLowerCase().endsWith(`.${e}`)) ||
    null
  )
}

function hasFile(ext: string): boolean {
  return !!findFileByExt(ext)
}

function onDownloadFormat(ext: string) {
  if (!props.jobId) return
  const target = findFileByExt(ext)
  if (!target) return
  const downloadUrl = AnalysisAPI.getResultFileUrl(props.jobId, target.filename)
  window.open(downloadUrl, '_blank')
}
</script>

<style scoped>
.analysis-result-panel {
  min-height: 120px;
}

.phase {
  max-width: 1000px;
  margin: 0 auto;
}

.banner {
  text-align: center;
  margin-bottom: 16px;
}

.banner-title {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0 0 8px;
}

.hint {
  color: #409eff;
  font-size: 1.05rem;
  font-weight: 500;
  margin: 0 0 8px;
}

.job-line {
  color: #606266;
  margin: 0;
}

.fail-line {
  color: #f56c6c;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.info-table td {
  border: 1px solid #ddd;
  padding: 12px 16px;
  text-align: center;
  background: #F7F7F7;
}

.info-table tr.stripe {
  background: #F7F7F7;
}

.label-cell {
  width: 42%;
  border-right: 1px solid #c0c0c0 !important;
  font-weight: 500;
}

.progress-gif {
  height: 15px;
  vertical-align: middle;
}

.result-split {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-around;
  gap: 20px;
  line-height: normal;
}

.preview {
  flex: 1 1 240px;
  min-width: 200px;
}

.preview-img {
  max-width: 100%;
  height: auto;
  border: 1px solid #c0c0c0;
  vertical-align: middle;
}

.preview-placeholder {
  color: #909399;
  font-size: 14px;
}

.download-wrap {
  flex-shrink: 0;
}

.error-cell {
  color: #f56c6c;
  font-weight: 500;
}

.progress-inline {
  max-width: 480px;
  margin: 16px auto 0;
}
</style>
