<template>
  <div class="result-viewer">
    <div class="viewer-header">
      <h3 class="viewer-title">{{ title }}</h3>
      <div class="viewer-actions">
        <el-button-group>
          <el-button 
            :type="viewMode === 'table' ? 'primary' : 'default'"
            @click="setViewMode('table')"
            icon="Grid"
          >
            表格
          </el-button>
          <el-button 
            :type="viewMode === 'chart' ? 'primary' : 'default'"
            @click="setViewMode('chart')"
            icon="PieChart"
            v-if="hasChartData"
          >
            图表
          </el-button>
          <el-button 
            :type="viewMode === 'raw' ? 'primary' : 'default'"
            @click="setViewMode('raw')"
            icon="Document"
          >
            原始数据
          </el-button>
        </el-button-group>
        
        <el-dropdown @command="handleExport" trigger="click">
          <el-button type="primary">
            导出数据 <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">CSV 格式</el-dropdown-item>
              <el-dropdown-item command="txt">TXT 格式 (Tab分隔)</el-dropdown-item>
              <el-dropdown-item command="excel">Excel 格式</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <div class="viewer-content">
      <!-- 表格视图 -->
      <div v-show="viewMode === 'table'" class="table-view">
        <el-table 
          :data="tableData" 
          :loading="loading"
          stripe
          style="width: 100%"
          max-height="600"
        >
          <el-table-column 
            v-for="column in tableColumns" 
            :key="column.prop"
            :prop="column.prop"
            :label="column.label"
            :width="column.width"
            :sortable="column.sortable"
          >
            <template #default="{ row }">
              <div v-if="column.formatter">
                {{ column.formatter(row[column.prop]) }}
              </div>
              <div v-else>
                {{ row[column.prop] }}
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 图表视图 -->
      <div v-show="viewMode === 'chart'" class="chart-view">
        <div class="chart-container" ref="chartContainer">
          <!-- 图表将在这里渲染 -->
        </div>
      </div>
      
      <!-- 原始数据视图 -->
      <div v-show="viewMode === 'raw'" class="raw-view">
        <el-scrollbar max-height="600">
          <pre class="raw-data">{{ rawData }}</pre>
        </el-scrollbar>
      </div>
    </div>
    
    <div class="viewer-footer" v-if="summary">
      <div class="summary-info">
        <el-descriptions :column="4" size="small" border>
          <el-descriptions-item 
            v-for="(value, key) in summary" 
            :key="key"
            :label="key"
          >
            {{ value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

interface TableColumn {
  prop: string
  label: string
  width?: string | number
  sortable?: boolean
  formatter?: (value: any) => string
}

interface SummaryData {
  [key: string]: string | number
}

interface Props {
  title?: string
  data: any[]
  columns?: TableColumn[]
  chartData?: any
  rawData?: string
  summary?: SummaryData
  loading?: boolean
  exportFilename?: string  // 导出文件名，默认使用 'result'
}

const props = withDefaults(defineProps<Props>(), {
  title: '结果查看',
  data: () => [],
  columns: () => [],
  chartData: undefined,
  rawData: '',
  summary: undefined,
  loading: false,
  exportFilename: 'result'
})

const emit = defineEmits<{
  (e: 'export', format: string): void
}>()

// 状态
const viewMode = ref<'table' | 'chart' | 'raw'>('table')
const chartContainer = ref<HTMLElement | null>(null)

// 计算属性
const hasChartData = computed(() => !!props.chartData)
const tableData = computed(() => props.data)
const tableColumns = computed(() => props.columns)
const rawJsonData = computed(() => {
  return props.rawData || JSON.stringify(props.data, null, 2)
})

// 方法
function setViewMode(mode: 'table' | 'chart' | 'raw') {
  viewMode.value = mode
}

/**
 * 通用下载方法 - 使用 Blob 和 URL.createObjectURL
 * 添加 BOM 头确保中文 Excel 正确显示
 */
function downloadBlob(content: string, filename: string, mimeType: string) {
  const blob = new Blob(['\ufeff' + content], { type: `${mimeType};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * 获取导出数据的表头
 * 优先使用 columns 配置，否则从数据中自动推断
 */
function getExportHeaders(): string[] {
  if (props.columns && props.columns.length > 0) {
    return props.columns.map(col => col.prop)
  }
  if (props.data.length > 0) {
    return Object.keys(props.data[0])
  }
  return []
}

/**
 * 获取表头显示名称
 */
function getHeaderLabels(): string[] {
  if (props.columns && props.columns.length > 0) {
    return props.columns.map(col => col.label || col.prop)
  }
  return getExportHeaders()
}

/**
 * 导出为 CSV 格式（逗号分隔）
 */
function exportCSV() {
  if (props.data.length === 0) {
    console.warn('没有可导出的数据')
    return
  }
  
  const headers = getExportHeaders()
  const headerLabels = getHeaderLabels()
  
  const csv = [
    headerLabels.join(','),
    ...props.data.map(row => 
      headers.map(h => {
        const value = row[h] ?? ''
        // 处理包含逗号、引号或换行的值
        const strValue = String(value)
        if (strValue.includes(',') || strValue.includes('"') || strValue.includes('\n')) {
          return `"${strValue.replace(/"/g, '""')}"`
        }
        return `"${strValue}"`
      }).join(',')
    )
  ].join('\n')
  
  downloadBlob(csv, `${props.exportFilename}.csv`, 'text/csv')
}

/**
 * 导出为 TXT 格式（Tab分隔）
 */
function exportTXT() {
  if (props.data.length === 0) {
    console.warn('没有可导出的数据')
    return
  }
  
  const headers = getExportHeaders()
  const headerLabels = getHeaderLabels()
  
  const txt = [
    headerLabels.join('\t'),
    ...props.data.map(row => 
      headers.map(h => row[h] ?? '').join('\t')
    )
  ].join('\n')
  
  downloadBlob(txt, `${props.exportFilename}.txt`, 'text/plain')
}

/**
 * 导出为 Excel 格式（使用 HTML table 转 xls 方式）
 */
function exportExcel() {
  if (props.data.length === 0) {
    console.warn('没有可导出的数据')
    return
  }
  
  const headers = getExportHeaders()
  const headerLabels = getHeaderLabels()
  
  let html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">'
  html += '<head><meta charset="UTF-8"><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>Sheet1</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head>'
  html += '<body><table border="1"><tr>'
  
  // 表头
  html += headerLabels.map(h => `<th style="background-color:#f5f5f5;font-weight:bold;">${escapeHtml(String(h))}</th>`).join('')
  html += '</tr>'
  
  // 数据行
  props.data.forEach(row => {
    html += '<tr>'
    html += headers.map(h => `<td>${escapeHtml(String(row[h] ?? ''))}</td>`).join('')
    html += '</tr>'
  })
  
  html += '</table></body></html>'
  
  downloadBlob(html, `${props.exportFilename}.xls`, 'application/vnd.ms-excel')
}

/**
 * HTML 转义，防止 XSS
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * 处理导出命令
 */
function handleExport(format: string) {
  switch (format) {
    case 'csv':
      exportCSV()
      break
    case 'txt':
      exportTXT()
      break
    case 'excel':
      exportExcel()
      break
    default:
      console.warn('未知的导出格式:', format)
  }
  // 同时发出事件，以便父组件可以监听
  emit('export', format)
}

// 初始化图表（如果需要）
function initChart() {
  if (viewMode.value === 'chart' && props.chartData && chartContainer.value) {
    // 这里可以集成具体的图表库，如ECharts
    console.log('Initializing chart with data:', props.chartData)
  }
}

// 监听数据变化
watch(() => props.chartData, () => {
  if (viewMode.value === 'chart') {
    initChart()
  }
})

watch(viewMode, (newMode) => {
  if (newMode === 'chart') {
    initChart()
  }
})

// 生命周期
onMounted(() => {
  if (viewMode.value === 'chart') {
    initChart()
  }
})
</script>

<style scoped>
.result-viewer {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.viewer-title {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.viewer-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.viewer-content {
  padding: 20px;
  min-height: 400px;
}

.table-view,
.chart-view,
.raw-view {
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 500px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.raw-data {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.viewer-footer {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

.summary-info {
  width: 100%;
}

:deep(.el-table) {
  border-radius: 4px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  font-weight: 500;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .viewer-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .viewer-actions {
    justify-content: center;
  }
  
  .viewer-content {
    padding: 16px;
  }
}
</style>