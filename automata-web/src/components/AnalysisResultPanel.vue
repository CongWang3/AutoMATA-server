<template>
  <div class="analysis-result-panel">
    <!-- 等待 / 分析中 -->
    <div v-if="phase === 'waiting'" class="phase waiting">
      <div class="banner">
        <h2 class="banner-title">Data analysis task</h2>
        <p class="hint">Analysis is in progress, please wait</p>
        <!-- <p class="job-line">JobID：{{ jobId }}</p> -->
      </div>
      <table class="info-table">
        <tbody>
          <tr>
            <td class="label-cell">JobID</td>
            <td>{{ jobId }}</td>
          </tr>
          <tr>
            <td class="label-cell">Analysis Type</td>
            <td>{{ displayAnalysisTypeLabel }}</td>
          </tr>
          <tr v-for="(row, idx) in displayParamRows" :key="'w-' + idx" :class="{ stripe: idx % 2 === 1 }">
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
            <td>{{ displayAnalysisTypeLabel }}</td>
          </tr>
          <tr v-for="(row, idx) in displayParamRows" :key="'c-' + idx" :class="{ stripe: idx % 2 === 1 }">
            <td class="label-cell">{{ row.label }}</td>
            <td>{{ row.value }}</td>
          </tr>
          <!-- Comprehensive: Volcano/Cluster 显示在表格内（左图右下载），且 Cluster 必须是倒数第一行 -->
          <tr v-if="isComprehensiveResult">
            <td class="label-cell">
              <div class="preview">
                <img
                  v-if="volcanoPreviewUrl"
                  :key="volcanoPreviewUrl"
                  :src="volcanoPreviewUrl"
                  height="400"
                  alt="Volcano Plot"
                  class="preview-img"
                >
                <span v-else class="preview-placeholder">图片生成后可预览</span>
              </div>
            </td>
            <td>
              <el-dropdown trigger="click" @command="(ext: string) => onDownloadComprehensiveFigure('volcano', ext)">
                <el-button
                  type="primary"
                  size="default"
                >
                  Download Volcano
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="item in downloadFormats"
                      :key="`vol-in-${item.ext}`"
                      :command="item.ext"
                      :disabled="!hasComprehensiveFigure('volcano', item.ext)"
                    >
                      {{ item.label }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </td>
          </tr>
          <tr v-if="isComprehensiveResult">
            <td class="label-cell">
              <div class="preview">
                <img
                  v-if="clusterPreviewUrl"
                  :key="clusterPreviewUrl"
                  :src="clusterPreviewUrl"
                  height="400"
                  alt="Cluster Heatmap"
                  class="preview-img"
                >
                <span v-else class="preview-placeholder">图片生成后可预览</span>
              </div>
            </td>
            <td>
              <el-dropdown trigger="click" @command="(ext: string) => onDownloadComprehensiveFigure('cluster', ext)">
                <el-button
                  type="primary"
                  size="default"
                >
                  Download Cluster Heatmap
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="item in downloadFormats"
                      :key="`cl-in-${item.ext}`"
                      :command="item.ext"
                      :disabled="!hasComprehensiveFigure('cluster', item.ext)"
                    >
                      {{ item.label }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </td>
          </tr>
          <tr v-if="!isComprehensiveResult">
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

      <div v-if="isComprehensiveResult" class="comprehensive-section">
        <div class="go-txt-outside">
          <div class="go-txt-title">Differential Expression Result</div>
          <div class="go-txt-actions">
            <el-select v-model="comprehensiveSigType" style="width: 180px">
              <el-option label="all" value="all" />
              <el-option label="up" value="up" />
              <el-option label="down" value="down" />
            </el-select>
            <el-button type="primary" size="small" :loading="comprehensiveTxtLoading" @click="loadComprehensiveTxt">
              {{ comprehensiveTxtLoaded ? 'Reload' : 'View content' }}
            </el-button>
            <el-button size="small" :disabled="!currentComprehensiveTxtFile" @click="downloadComprehensiveTxt">
              Download
            </el-button>
          </div>

          <div v-if="comprehensiveTxtLoaded" class="go-txt-table-wrap">
            <table class="go-txt-table">
              <thead>
                <tr>
                  <th v-for="col in comprehensiveTxtColumns" :key="col">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in comprehensiveTxtVisibleRows" :key="idx">
                  <td v-for="col in comprehensiveTxtColumns" :key="col">{{ row[col] }}</td>
                </tr>
              </tbody>
            </table>
            <div class="go-txt-pagination">
              <el-button
                v-if="comprehensiveTxtVisibleRows.length < comprehensiveTxtRows.length"
                size="small"
                @click="comprehensiveTxtVisibleCount = Math.min(comprehensiveTxtVisibleCount + goTxtPageSize, comprehensiveTxtRows.length)"
              >
                Load more ({{ comprehensiveTxtRows.length - comprehensiveTxtVisibleRows.length }} rows)
              </el-button>
            </div>
          </div>
          <div v-else class="go-txt-placeholder">
            Please click "View content" to load the file parsing table.
          </div>
        </div>

        <div class="go-txt-outside">
          <div class="go-txt-title">Continue GO &amp; KEGG Enrichment</div>

          <div class="continue-enrich-form">
            <!-- 仅在 GO+KEGG 完成后隐藏提交框；综合分析完成但 GO/KEGG 未完成时仍需展示 -->
            <template v-if="enrichState !== 'completed'">
              <div class="continue-enrich-row">
                <div class="continue-enrich-label">DEGs to analyze</div>
                <el-select v-model="enrichTypeAnalysis" style="width: 180px" :disabled="enrichState === 'running'">
                  <el-option label="all" value="all" />
                  <el-option label="up" value="up" />
                  <el-option label="down" value="down" />
                </el-select>
              </div>

              <div class="continue-enrich-grid">
                <div class="continue-enrich-card">
                  <div class="continue-enrich-card-title">GO parameters</div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">Organism</div>
                    <el-select v-model="goOrganism" style="width: 220px" :disabled="enrichState === 'running'">
                      <el-option label="Homo_sapiens" value="Homo_sapiens" />
                      <el-option label="Mus_musculus" value="Mus_musculus" />
                      <el-option label="Bos_taurus" value="Bos_taurus" />
                      <!-- <el-option label="Bovine" value="Bovine" /> -->
                      <el-option label="Drosophila_melanogaster" value="Drosophila_melanogaster" />
                    </el-select>
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">Correction</div>
                    <el-select v-model="goCorrection" style="width: 220px" :disabled="enrichState === 'running'">
                      <el-option label="BH (Benjamini-Hochberg)" value="BH" />
                      <el-option label="BY (Benjamini-Yekutieli)" value="BY" />
                      <el-option label="holm" value="holm" />
                      <el-option label="hochberg" value="hochberg" />
                      <el-option label="hommel" value="hommel" />
                      <el-option label="bonferroni" value="bonferroni" />
                      <el-option label="fdr" value="fdr" />
                      <el-option label="none" value="none" />
                    </el-select>
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">Plot</div>
                    <el-select v-model="goPlotType" style="width: 220px" :disabled="enrichState === 'running'">
                      <el-option label="bubble" value="bubble" />
                      <el-option label="barplot" value="barplot" />
                      <el-option label="circle" value="circle" />
                      <el-option label="chord" value="chord" />
                      <el-option label="cluster" value="cluster" />
                    </el-select>
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">pvalue</div>
                    <el-input-number v-model="goPvalue" :min="0" :max="1" :step="0.01" :precision="3" :disabled="enrichState === 'running'" />
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">qvalue</div>
                    <el-input-number v-model="goQvalue" :min="0" :max="1" :step="0.01" :precision="3" :disabled="enrichState === 'running'" />
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">term_num</div>
                    <el-input-number v-model="goTermNum" :min="1" :max="50" :step="1" :disabled="enrichState === 'running'" />
                  </div>
                </div>

                <div class="continue-enrich-card">
                  <div class="continue-enrich-card-title">KEGG parameters</div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">Organism</div>
                    <el-select v-model="keggOrganism" style="width: 220px" :disabled="enrichState === 'running'">
                      <el-option label="Homo_sapiens" value="hsa" />
                      <el-option label="Mus_musculus" value="mmu" />
                      <el-option label="Bos_taurus" value="bos" />
                      <el-option label="Drosophila_melanogaster" value="dme" />
                    </el-select>
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">Correction</div>
                    <el-select v-model="keggCorrection" style="width: 220px" :disabled="enrichState === 'running'">
                      <el-option label="BH (Benjamini-Hochberg)" value="BH" />
                      <el-option label="BY (Benjamini-Yekutieli)" value="BY" />
                      <el-option label="holm" value="holm" />
                      <el-option label="hochberg" value="hochberg" />
                      <el-option label="hommel" value="hommel" />
                      <el-option label="bonferroni" value="bonferroni" />
                      <el-option label="fdr" value="fdr" />
                      <el-option label="none" value="none" />
                    </el-select>
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">Plot</div>
                    <el-select v-model="keggPlotType" style="width: 220px" :disabled="enrichState === 'running'">
                      <el-option label="bubble" value="bubble" />
                      <el-option label="chord" value="chord" />
                      <el-option label="cluster" value="cluster" />
                    </el-select>
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">pvalue</div>
                    <el-input-number v-model="keggPvalue" :min="0" :max="1" :step="0.01" :precision="3" :disabled="enrichState === 'running'" />
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">qvalue</div>
                    <el-input-number v-model="keggQvalue" :min="0" :max="1" :step="0.01" :precision="3" :disabled="enrichState === 'running'" />
                  </div>
                  <div class="continue-enrich-row">
                    <div class="continue-enrich-label">term_num</div>
                    <el-input-number v-model="keggTermNum" :min="1" :max="50" :step="1" :disabled="enrichState === 'running'" />
                  </div>
                </div>
              </div>

              <div class="continue-enrich-actions">
                <el-button type="primary" :loading="enrichSubmitting" :disabled="enrichState === 'running'" @click="submitContinueEnrichment">
                  Submit (GO + KEGG)
                </el-button>
              </div>
            </template>

            <div v-if="enrichShowSubmittedParams" class="continue-enrich-submitted">
              <table class="info-table">
                <tbody>
                  <tr>
                    <td class="label-cell">Type</td>
                    <td>{{ enrichLastPayload?.type_analysis }}</td>
                  </tr>
                  <tr>
                    <td class="label-cell">GO</td>
                    <td>
                      organism={{ enrichLastPayload?.go_organism }},
                      correction={{ enrichLastPayload?.go_correction }},
                      plot={{ enrichLastPayload?.go_plot_type }},
                      pvalue={{ enrichLastPayload?.go_pvalue }},
                      qvalue={{ enrichLastPayload?.go_qvalue }},
                      term_num={{ enrichLastPayload?.go_term_num }}
                    </td>
                  </tr>
                  <tr>
                    <td class="label-cell">KEGG</td>
                    <td>
                      organism={{ enrichLastPayload?.kegg_organism }},
                      correction={{ enrichLastPayload?.kegg_correction }},
                      plot={{ enrichLastPayload?.kegg_plot_type }},
                      pvalue={{ enrichLastPayload?.kegg_pvalue }},
                      qvalue={{ enrichLastPayload?.kegg_qvalue }},
                      term_num={{ enrichLastPayload?.kegg_term_num }}
                    </td>
                  </tr>
                  <tr v-if="enrichState === 'running'">
                    <td class="label-cell">Running</td>
                    <td>
                      <img
                        src="/images/progress_bar_new.gif"
                        alt=""
                        class="progress-gif"
                      >
                    </td>
                  </tr>
                  <tr v-if="enrichState === 'failed'">
                    <td class="label-cell">Status</td>
                    <td>Failed</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="enrichState === 'completed'" class="continue-enrich-results">
              <div class="continue-enrich-results-title">GO / KEGG Results</div>
              <div class="continue-enrich-results-grid">
                <div class="continue-enrich-result-card">
                  <div class="preview">
                    <img
                      v-if="goEnrichPreviewUrl"
                      :key="goEnrichPreviewUrl"
                      :src="goEnrichPreviewUrl"
                      height="360"
                      alt="GO Enrichment"
                      class="preview-img"
                    >
                    <span v-else class="preview-placeholder">图片生成后可预览</span>
                  </div>
                  <el-dropdown trigger="click" @command="(ext: string) => onDownloadEnrichmentFigure('go', ext)">
                    <el-button type="primary" size="default">Download GO Enrichment</el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item
                          v-for="item in downloadFormats"
                          :key="`go-enrich-${item.ext}`"
                          :command="item.ext"
                          :disabled="!hasEnrichmentFigure('go', item.ext)"
                        >
                          {{ item.label }}
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>

                <div class="continue-enrich-result-card">
                  <div class="preview">
                    <img
                      v-if="keggEnrichPreviewUrl"
                      :key="keggEnrichPreviewUrl"
                      :src="keggEnrichPreviewUrl"
                      height="360"
                      alt="KEGG Enrichment"
                      class="preview-img"
                    >
                    <span v-else class="preview-placeholder">图片生成后可预览</span>
                  </div>
                  <el-dropdown trigger="click" @command="(ext: string) => onDownloadEnrichmentFigure('kegg', ext)">
                    <el-button type="primary" size="default">Download KEGG Enrichment</el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item
                          v-for="item in downloadFormats"
                          :key="`kegg-enrich-${item.ext}`"
                          :command="item.ext"
                          :disabled="!hasEnrichmentFigure('kegg', item.ext)"
                        >
                          {{ item.label }}
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="goTxtFile" class="go-txt-outside">
        <div class="go-txt-title">GO Enrichment Result</div>

        <div class="go-txt-actions">
          <el-button
            type="primary"
            size="small"
            :loading="goTxtLoading"
            @click="loadGoTxt"
          >
            {{ goTxtLoaded ? 'Reload' : 'View content' }}
          </el-button>
          <el-button
            size="small"
            :disabled="!goTxtFile"
            @click="downloadGoTxt"
          >
            Download
          </el-button>
        </div>

        <div v-if="goTxtLoaded" class="go-txt-table-wrap">
          <table class="go-txt-table">
            <thead>
              <tr>
                <th v-for="col in goTxtColumns" :key="col">
                  {{ col }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in goTxtVisibleRows" :key="idx">
                <td v-for="col in goTxtColumns" :key="col">
                  {{ row[col] }}
                </td>
              </tr>
            </tbody>
          </table>
          <div class="go-txt-pagination">
            <el-button
              v-if="goTxtVisibleRows.length < goTxtRows.length"
              size="small"
              @click="goTxtVisibleCount = Math.min(goTxtVisibleCount + goTxtPageSize, goTxtRows.length)"
            >
              Load more ({{ goTxtRows.length - goTxtVisibleRows.length }} rows)
            </el-button>
          </div>
        </div>

        <div v-else class="go-txt-placeholder">
          Please click "View content" to load the file parsing table.
        </div>
      </div>

      <div v-if="keggTxtFile" class="go-txt-outside">
        <div class="go-txt-title">KEGG Enrichment Result</div>

        <div class="go-txt-actions">
          <el-button
            type="primary"
            size="small"
            :loading="keggTxtLoading"
            @click="loadKeggTxt"
          >
            {{ keggTxtLoaded ? 'Reload' : 'View content' }}
          </el-button>
          <el-button
            size="small"
            :disabled="!keggTxtFile"
            @click="downloadKeggTxt"
          >
            Download
          </el-button>
        </div>

        <div v-if="keggTxtLoaded" class="go-txt-table-wrap">
          <table class="go-txt-table">
            <thead>
              <tr>
                <th v-for="col in keggTxtColumns" :key="col">
                  {{ col }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in keggTxtVisibleRows" :key="idx">
                <td v-for="col in keggTxtColumns" :key="col">
                  {{ row[col] }}
                </td>
              </tr>
            </tbody>
          </table>
          <div class="go-txt-pagination">
            <el-button
              v-if="keggTxtVisibleRows.length < keggTxtRows.length"
              size="small"
              @click="keggTxtVisibleCount = Math.min(keggTxtVisibleCount + goTxtPageSize, keggTxtRows.length)"
            >
              Load more ({{ keggTxtRows.length - keggTxtVisibleRows.length }} rows)
            </el-button>
          </div>
        </div>

        <div v-else class="go-txt-placeholder">
          Please click "View content" to load the file parsing table.
        </div>
      </div>
    </div>

    <!-- 失败 -->
    <div v-else-if="phase === 'failed'" class="phase failed">
      <div class="banner">
        <h2 class="banner-title">Result</h2>
        <p class="job-line fail-line">JobID：{{ jobId }}，Failed</p>
      </div>
      <table class="info-table">
        <tbody>
          <tr>
            <td class="label-cell">Analysis Type</td>
            <td>{{ displayAnalysisTypeLabel }}</td>
          </tr>
          <tr v-for="(row, idx) in displayParamRows" :key="'f-' + idx" :class="{ stripe: idx % 2 === 1 }">
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
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { AnalysisAPI, type AnalysisResultFile, type ComprehensiveEnrichmentPayload } from '@/api/analysis'

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
const tablePageSize = 30

const phase = computed<'waiting' | 'completed' | 'failed'>(() => {
  const s = statusUpper.value
  if (s === 'FAILED') return 'failed'
  if (s === 'COMPLETED') return 'completed'
  return 'waiting'
})

const displayAnalysisTypeLabel = computed(() => {
  if (isComprehensiveResult.value && enrichState.value === 'running') {
    return 'Comprehensive Analysis (GO + KEGG Enrichment)'
  }
  return props.analysisTypeLabel
})

const displayParamRows = computed<AnalysisParamRow[]>(() => {
  if (!isComprehensiveResult.value) return props.paramRows || []
  if (enrichState.value !== 'running' || !enrichLastPayload.value) return props.paramRows || []

  const p = enrichLastPayload.value
  return [
    { label: 'Type', value: String(p.type_analysis) },
    {
      label: 'GO params',
      value: `organism=${p.go_organism}, correction=${p.go_correction}, plot=${p.go_plot_type}, pvalue=${p.go_pvalue}, qvalue=${p.go_qvalue}, term_num=${p.go_term_num}`,
    },
    {
      label: 'KEGG params',
      value: `organism=${p.kegg_organism}, correction=${p.kegg_correction}, plot=${p.kegg_plot_type}, pvalue=${p.kegg_pvalue}, qvalue=${p.kegg_qvalue}, term_num=${p.kegg_term_num}`,
    },
  ]
})

const pngFile = computed(() => {
  const files = props.resultFiles || []
  return (
    files.find((f) => f.format === 'png') ||
    files.find((f) => f.filename.toLowerCase().endsWith('.png')) ||
    null
  )
})

const isComprehensiveResult = computed(() => {
  const files = props.resultFiles || []
  const names = files.map((f) => f.filename.toLowerCase())
  return names.includes('select_all.txt') || names.some((n) => n.startsWith('volcano.') || n.startsWith('df_cluster_heatmap.'))
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
  { label: 'BMP', ext: 'bmp' },
  { label: 'TXT', ext: 'txt' }
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

function findComprehensiveFigure(base: 'volcano' | 'cluster', ext: string): AnalysisResultFile | null {
  const files = props.resultFiles || []
  const normalizedExt = ext.toLowerCase()
  const prefix = base === 'volcano' ? 'volcano.' : 'df_cluster_heatmap.'
  return files.find((f) => f.filename.toLowerCase() === `${prefix}${normalizedExt}`) || null
}

const volcanoPreviewUrl = computed(() => {
  if (!props.jobId || phase.value !== 'completed') return ''
  const f = findComprehensiveFigure('volcano', 'png')
  if (!f) return ''
  return `${AnalysisAPI.getResultFileUrl(props.jobId, f.filename)}?t=${Date.now()}`
})

const clusterPreviewUrl = computed(() => {
  if (!props.jobId || phase.value !== 'completed') return ''
  const f = findComprehensiveFigure('cluster', 'png')
  if (!f) return ''
  return `${AnalysisAPI.getResultFileUrl(props.jobId, f.filename)}?t=${Date.now()}`
})

function hasComprehensiveFigure(base: 'volcano' | 'cluster', ext: string): boolean {
  return !!findComprehensiveFigure(base, ext)
}

function onDownloadComprehensiveFigure(base: 'volcano' | 'cluster', ext: string) {
  if (!props.jobId) return
  const target = findComprehensiveFigure(base, ext)
  if (!target) return
  const downloadUrl = AnalysisAPI.getResultFileUrl(props.jobId, target.filename)
  window.open(downloadUrl, '_blank')
}

const comprehensiveSigType = ref<'all' | 'up' | 'down'>('all')
const comprehensiveTxtLoading = ref(false)
const comprehensiveTxtLoaded = ref(false)
const comprehensiveTxtColumns = ref<string[]>([])
const comprehensiveTxtRows = ref<Record<string, string>[]>([])
const comprehensiveTxtVisibleCount = ref(tablePageSize)
const comprehensiveTxtVisibleRows = computed(() =>
  comprehensiveTxtRows.value.slice(0, comprehensiveTxtVisibleCount.value)
)

const currentComprehensiveTxtFile = computed<AnalysisResultFile | null>(() => {
  const files = props.resultFiles || []
  const targetName =
    comprehensiveSigType.value === 'up'
      ? 'select_up.txt'
      : comprehensiveSigType.value === 'down'
        ? 'select_down.txt'
        : 'select_all.txt'
  return files.find((f) => f.filename.toLowerCase() === targetName) || null
})

async function loadComprehensiveTxt() {
  if (!currentComprehensiveTxtFile.value) return
  comprehensiveTxtLoading.value = true
  try {
    const url = AnalysisAPI.getResultFileUrl(props.jobId, currentComprehensiveTxtFile.value.filename)
    const sep = url.includes('?') ? '&' : '?'
    const text = await fetch(`${url}${sep}t=${Date.now()}`).then((r) => r.text())
    const parsed = parseTsvQuoted(text)
    comprehensiveTxtColumns.value = parsed.columns
    comprehensiveTxtRows.value = parsed.rows
    comprehensiveTxtVisibleCount.value = tablePageSize
    comprehensiveTxtLoaded.value = true
  } catch (e) {
    console.error('加载综合分析 txt 结果失败:', e)
  } finally {
    comprehensiveTxtLoading.value = false
  }
}

function downloadComprehensiveTxt() {
  if (!props.jobId || !currentComprehensiveTxtFile.value) return
  const downloadUrl = AnalysisAPI.getResultFileUrl(props.jobId, currentComprehensiveTxtFile.value.filename)
  window.open(downloadUrl, '_blank')
}

// ==================== Comprehensive: continue GO + KEGG ====================
const enrichTypeAnalysis = ref<'all' | 'up' | 'down'>('all')

const goOrganism = ref('Homo_sapiens')
const goCorrection = ref('BH')
const goPlotType = ref('bubble')
const goPvalue = ref(0.05)
const goQvalue = ref(0.1)
const goTermNum = ref(5)

const keggOrganism = ref('hsa')
const keggCorrection = ref('BH')
const keggPlotType = ref('bubble')
const keggPvalue = ref(0.05)
const keggQvalue = ref(0.1)
const keggTermNum = ref(5)

const enrichSubmitting = ref(false)
const enrichLastPayload = ref<ComprehensiveEnrichmentPayload | null>(null)
const enrichState = ref<'idle' | 'running' | 'completed' | 'failed'>('idle')

const enrichShowSubmittedParams = computed(() => enrichLastPayload.value !== null)

function enrichPayloadStorageKey(jobId: string) {
  return `automata:comprehensive_enrich_payload:${jobId}`
}

function persistEnrichPayload(jobId: string, payload: ComprehensiveEnrichmentPayload) {
  try {
    localStorage.setItem(enrichPayloadStorageKey(jobId), JSON.stringify(payload))
  } catch (e) {
    console.warn('persistEnrichPayload failed:', e)
  }
}

function restoreEnrichPayload(jobId: string) {
  try {
    const raw = localStorage.getItem(enrichPayloadStorageKey(jobId))
    if (!raw) return
    const p = JSON.parse(raw) as ComprehensiveEnrichmentPayload
    if (!p || typeof p !== 'object') return
    enrichLastPayload.value = p
  } catch (e) {
    console.warn('restoreEnrichPayload failed:', e)
  }
}

async function submitContinueEnrichment() {
  if (!props.jobId) return
  if (!isComprehensiveResult.value) return

  const payload: ComprehensiveEnrichmentPayload = {
    type_analysis: enrichTypeAnalysis.value,
    go_organism: goOrganism.value,
    go_pvalue: Number(goPvalue.value),
    go_qvalue: Number(goQvalue.value),
    go_plot_type: goPlotType.value,
    go_term_num: Number(goTermNum.value),
    go_correction: goCorrection.value,
    kegg_organism: keggOrganism.value,
    kegg_pvalue: Number(keggPvalue.value),
    kegg_qvalue: Number(keggQvalue.value),
    kegg_plot_type: keggPlotType.value,
    kegg_term_num: Number(keggTermNum.value),
    kegg_correction: keggCorrection.value,
  }

  enrichSubmitting.value = true
  enrichLastPayload.value = payload
  persistEnrichPayload(props.jobId, payload)
  enrichState.value = 'running'
  try {
    await AnalysisAPI.runComprehensiveEnrichment(props.jobId, payload)
    ElMessage.success('Submitted')
  } catch (e: any) {
    enrichState.value = 'failed'
    ElMessage.error(e?.response?.data?.detail || 'Submit failed')
  } finally {
    enrichSubmitting.value = false
  }
}

function findEnrichmentFigure(kind: 'go' | 'kegg', ext: string): AnalysisResultFile | null {
  const files = props.resultFiles || []
  const normalizedExt = ext.toLowerCase()
  const prefix = kind === 'go' ? 'go_enrichment.' : 'kegg_enrichment.'
  return files.find((f) => f.filename.toLowerCase() === `${prefix}${normalizedExt}`) || null
}

function hasEnrichmentFigure(kind: 'go' | 'kegg', ext: string): boolean {
  return !!findEnrichmentFigure(kind, ext)
}

function onDownloadEnrichmentFigure(kind: 'go' | 'kegg', ext: string) {
  if (!props.jobId) return
  const target = findEnrichmentFigure(kind, ext)
  if (!target) return
  const downloadUrl = AnalysisAPI.getResultFileUrl(props.jobId, target.filename)
  window.open(downloadUrl, '_blank')
}

const goEnrichPreviewUrl = computed(() => {
  if (!props.jobId || phase.value !== 'completed') return ''
  const f = findEnrichmentFigure('go', 'png')
  if (!f) return ''
  return `${AnalysisAPI.getResultFileUrl(props.jobId, f.filename)}?t=${Date.now()}`
})

const keggEnrichPreviewUrl = computed(() => {
  if (!props.jobId || phase.value !== 'completed') return ''
  const f = findEnrichmentFigure('kegg', 'png')
  if (!f) return ''
  return `${AnalysisAPI.getResultFileUrl(props.jobId, f.filename)}?t=${Date.now()}`
})

watch(
  () => props.jobId,
  (jobId) => {
    if (!jobId) return
    // 弹窗重新打开/刷新时恢复参数回显
    if (!enrichLastPayload.value) restoreEnrichPayload(jobId)
  },
  { immediate: true }
)

watch(
  () => [enrichState.value, statusUpper.value, (props.resultFiles || []).map((f) => f.filename).join('|')],
  ([state, s]) => {
    if (state !== 'running') return
    if (String(s).toUpperCase() === 'FAILED') {
      enrichState.value = 'failed'
      return
    }
    // 完成判定：同时出现 GO + KEGG 图（任意格式）即可
    const hasGo = !!findEnrichmentFigure('go', 'png') || !!findEnrichmentFigure('go', 'pdf')
    const hasKegg = !!findEnrichmentFigure('kegg', 'png') || !!findEnrichmentFigure('kegg', 'pdf')
    if (hasGo && hasKegg) {
      enrichState.value = 'completed'
    }
  },
  { immediate: true }
)

// 若页面刷新导致 enrichState 回到 idle，但结果文件已存在，则推断为 completed
watch(
  () => [phase.value, (props.resultFiles || []).map((f) => f.filename).join('|')],
  ([p]) => {
    if (p !== 'completed') return
    const hasGo = !!findEnrichmentFigure('go', 'png') || !!findEnrichmentFigure('go', 'pdf')
    const hasKegg = !!findEnrichmentFigure('kegg', 'png') || !!findEnrichmentFigure('kegg', 'pdf')
    if (hasGo && hasKegg && enrichState.value === 'idle') {
      enrichState.value = 'completed'
    }
  },
  { immediate: true }
)

// ==================== GO enrichment txt ====================
const goTxtFile = computed<AnalysisResultFile | null>(() => {
  const files = props.resultFiles || []
  const direct = files.find((f) => f.filename === 'GO_enrichment_result.txt')
  if (direct) return direct
  // 兜底：包含关键字且为 txt 的文件
  return (
    files.find(
      (f) =>
        f.format?.toLowerCase() === 'txt' && f.filename.toLowerCase().includes('go_enrichment_result')
    ) || null
  )
})

const goTxtLoading = ref(false)
const goTxtLoaded = ref(false)
const goTxtColumns = ref<string[]>([])
const goTxtRows = ref<Record<string, string>[]>([])

const goTxtPageSize = tablePageSize
const goTxtVisibleCount = ref(goTxtPageSize)

const goTxtVisibleRows = computed(() => goTxtRows.value.slice(0, goTxtVisibleCount.value))

function stripOuterQuotes(v: string): string {
  const s = v.trim()
  if (s.length >= 2 && s.startsWith('"') && s.endsWith('"')) return s.slice(1, -1)
  return s
}

function parseTsvQuoted(text: string): { columns: string[]; rows: Record<string, string>[] } {
  const lines = text
    .split('\n')
    .map((l) => l.trimEnd())
    .filter((l) => l.trim().length > 0)

  if (lines.length === 0) return { columns: [], rows: [] }

  const header = lines[0]
  const columns = (header ?? '').split('\t').map((h) => stripOuterQuotes(h))
  const rows: Record<string, string>[] = []

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i]
    if (!line) continue

    const parts = line.split('\t').map((p) => stripOuterQuotes(p))
    const row: Record<string, string> = {}
    for (let c = 0; c < columns.length; c++) {
      const col = columns[c]
      if (!col) continue
      row[col] = parts[c] ?? ''
    }
    rows.push(row)
  }

  return { columns, rows }
}

async function loadGoTxt() {
  if (!goTxtFile.value) return
  goTxtLoading.value = true
  try {
    const url = (goTxtFile.value as any).url as string | undefined
    if (!url) return

    const sep = url.includes('?') ? '&' : '?'
    const text = await fetch(`${url}${sep}t=${Date.now()}`).then((r) => r.text())

    const parsed = parseTsvQuoted(text)
    goTxtColumns.value = parsed.columns
    goTxtRows.value = parsed.rows
    goTxtVisibleCount.value = goTxtPageSize
    goTxtLoaded.value = true
  } catch (e) {
    console.error('加载 GO_enrichment_result.txt 失败:', e)
  } finally {
    goTxtLoading.value = false
  }
}

function downloadGoTxt() {
  if (!props.jobId || !goTxtFile.value) return
  const downloadUrl = AnalysisAPI.getResultFileUrl(props.jobId, goTxtFile.value.filename)
  window.open(downloadUrl, '_blank')
}

// 弹窗打开后自动加载（如果你希望更轻量，也可以删除这段）
watch(
  () => [phase.value, goTxtFile.value?.filename],
  ([p, filename]) => {
    if (p === 'completed' && filename) void loadGoTxt()
  },
  { immediate: true }
)

// ==================== KEGG enrichment txt ====================
const keggTxtFile = computed<AnalysisResultFile | null>(() => {
  const files = props.resultFiles || []
  const direct = files.find((f) => f.filename === 'KEGG_enrichment_result.txt')
  if (direct) return direct
  return (
    files.find(
      (f) => f.format?.toLowerCase() === 'txt' && f.filename.toLowerCase().includes('kegg_enrichment_result')
    ) || null
  )
})

const keggTxtLoading = ref(false)
const keggTxtLoaded = ref(false)
const keggTxtColumns = ref<string[]>([])
const keggTxtRows = ref<Record<string, string>[]>([])
const keggTxtVisibleCount = ref(goTxtPageSize)

const keggTxtVisibleRows = computed(() => keggTxtRows.value.slice(0, keggTxtVisibleCount.value))

async function loadKeggTxt() {
  if (!keggTxtFile.value) return
  keggTxtLoading.value = true
  try {
    const url = (keggTxtFile.value as any).url as string | undefined
    if (!url) return

    const sep = url.includes('?') ? '&' : '?'
    const text = await fetch(`${url}${sep}t=${Date.now()}`).then((r) => r.text())

    const parsed = parseTsvQuoted(text)
    keggTxtColumns.value = parsed.columns
    keggTxtRows.value = parsed.rows
    keggTxtVisibleCount.value = goTxtPageSize
    keggTxtLoaded.value = true
  } catch (e) {
    console.error('加载 KEGG_enrichment_result.txt 失败:', e)
  } finally {
    keggTxtLoading.value = false
  }
}

function downloadKeggTxt() {
  if (!props.jobId || !keggTxtFile.value) return
  const downloadUrl = AnalysisAPI.getResultFileUrl(props.jobId, keggTxtFile.value.filename)
  window.open(downloadUrl, '_blank')
}

watch(
  () => [phase.value, keggTxtFile.value?.filename],
  ([p, filename]) => {
    if (p === 'completed' && filename) void loadKeggTxt()
  },
  { immediate: true }
)

watch(
  () => [phase.value, currentComprehensiveTxtFile.value?.filename, comprehensiveSigType.value],
  ([p, filename]) => {
    if (p === 'completed' && isComprehensiveResult.value && filename) {
      void loadComprehensiveTxt()
    }
  },
  { immediate: true }
)
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

.go-txt-actions {
  display: flex;
  justify-content: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.go-txt-placeholder {
  color: #909399;
  font-size: 14px;
  text-align: left;
}

.go-txt-outside {
  margin-top: 16px;
  width: 100%;
}

.comprehensive-section {
  margin-top: 16px;
}

.comprehensive-figures {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.comprehensive-figure-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  padding: 12px;
}

.go-txt-title {
  font-weight: 600;
  margin-bottom: 10px;
  text-align: left;
  color: #606266;
}

.go-txt-table-wrap {
  width: 100%;
  max-height: 360px;
  overflow-x: auto;
  overflow-y: auto;
}

.go-txt-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.go-txt-table th,
.go-txt-table td {
  border: 1px solid #e5e7eb;
  padding: 6px 8px;
  background: #F7F7F7;
  white-space: nowrap;
}

.go-txt-table th {
  position: sticky;
  top: 0;
  background: #f5f5f5;
  z-index: 1;
  font-weight: 600;
}

.go-txt-pagination {
  margin-top: 10px;
  text-align: left;
}

.continue-enrich-form {
  width: 100%;
}

.continue-enrich-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 16px;
  margin-top: 10px;
}

.continue-enrich-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  padding: 12px;
}

.continue-enrich-card-title {
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
  text-align: left;
}

.continue-enrich-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 10px 0;
}

.continue-enrich-label {
  width: 100px;
  text-align: left;
  color: #606266;
  font-size: 13px;
  flex-shrink: 0;
}

.continue-enrich-actions {
  margin-top: 12px;
  display: flex;
  justify-content: center;
}

.continue-enrich-submitted {
  margin-top: 12px;
}

.continue-enrich-results {
  margin-top: 12px;
}

.continue-enrich-results-title {
  font-weight: 600;
  color: #606266;
  margin: 10px 0;
  text-align: left;
}

.continue-enrich-results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 16px;
}

.continue-enrich-result-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
