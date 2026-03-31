<template>
  <div class="training-result-panel">
    <!-- Waiting -->
    <div v-if="phase === 'waiting'" class="phase waiting">
      <div class="banner">
        <h2 class="banner-title">Data training task</h2>
        <p class="hint">Trainings is in progress, please wait</p>
      </div>

      <table class="info-table">
        <tbody>
          <tr>
            <td class="label-cell">JobID</td>
            <td>{{ jobId }}</td>
          </tr>
          <tr
            v-for="(row, idx) in visibleParamRows"
            :key="'w-' + idx"
            :class="{ stripe: idx % 2 === 1 }"
          >
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

    <!-- Completed -->
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
          <tr
            v-for="(row, idx) in visibleParamRows"
            :key="'c-' + idx"
            :class="{ stripe: idx % 2 === 1 }"
          >
            <td class="label-cell">{{ row.label }}</td>
            <td>{{ row.value }}</td>
          </tr>
          <tr class="stripe">
            <td class="label-cell">Data Training Result</td>
            <td>
              <el-button type="primary" size="default" @click="handleDownload">
                Download
              </el-button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Failed -->
    <div v-else class="phase failed">
      <div class="banner">
        <h2 class="banner-title">Result</h2>
        <p class="job-line fail-line">JobID：{{ jobId }}，Failed</p>
      </div>

      <table class="info-table">
        <tbody>
          <tr>
            <td class="label-cell">JobID</td>
            <td>{{ jobId }}</td>
          </tr>
          <tr
            v-for="(row, idx) in visibleParamRows"
            :key="'f-' + idx"
            :class="{ stripe: idx % 2 === 1 }"
          >
            <td class="label-cell">{{ row.label }}</td>
            <td>{{ row.value }}</td>
          </tr>
          <tr class="stripe">
            <td class="label-cell">Data Training Result</td>
            <td class="error-cell">{{ errorMessage || 'Unknown error' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { buildTrainingResultParamRows, type TrainingParamRow } from './trainingResultParams'

const props = defineProps<{
  jobId: string
  status: string
  inputParams: unknown
  errorMessage?: string
  /**
   * 下载是否已经完全就绪（后端确认结果文件可下载）
   * - 未传入时默认视为 true，保证向后兼容
   */
  downloadReady?: boolean
  /**
   * 按 label 隐藏指定行（例如 ModelUse 中隐藏 Test Dataset / Model File）
   */
  hideLabels?: string[]
  onDownload: () => void | Promise<void>
}>()

const statusUpper = computed(() => String(props.status || '').toUpperCase())

const phase = computed<'waiting' | 'completed' | 'failed'>(() => {
  const s = statusUpper.value
  if (s === 'FAILED' || s === 'CANCELLED') return 'failed'
  if (s === 'COMPLETED') {
    // 只有在后端确认结果文件可下载后，才展示“已完成 + 下载”界面
    if (props.downloadReady === false) return 'waiting'
    return 'completed'
  }
  // default: Submitted / Processing
  return 'waiting'
})

const paramRows = computed<TrainingParamRow[]>(() => buildTrainingResultParamRows(props.inputParams))

const visibleParamRows = computed<TrainingParamRow[]>(() => {
  const rows = paramRows.value
  const hidden = new Set((props.hideLabels || []).map((s) => String(s || '').toLowerCase()))
  if (!hidden.size) return rows
  return rows.filter((r) => !hidden.has(String(r.label || '').toLowerCase()))
})

async function handleDownload() {
  await props.onDownload?.()
}
</script>

<style scoped>
.training-result-panel {
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

.error-cell {
  color: #f56c6c;
  font-weight: 500;
}
</style>

