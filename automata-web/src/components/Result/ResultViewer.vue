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
        
        <el-dropdown @command="handleExport">
          <el-button>
            导出 <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">CSV格式</el-dropdown-item>
              <el-dropdown-item command="json">JSON格式</el-dropdown-item>
              <el-dropdown-item command="excel">Excel格式</el-dropdown-item>
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
}

const props = withDefaults(defineProps<Props>(), {
  title: '结果查看',
  data: () => [],
  columns: () => [],
  chartData: undefined,
  rawData: '',
  summary: undefined,
  loading: false
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

function handleExport(format: string) {
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