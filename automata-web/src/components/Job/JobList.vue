<template>
  <div class="job-list">
    <div class="list-header">
      <h3 class="list-title">{{ title }}</h3>
      <div class="list-actions">
        <el-button 
          size="small" 
          @click="refreshJobs"
          :loading="isLoading"
          icon="Refresh"
        >
          刷新
        </el-button>
        <el-button 
          size="small" 
          @click="clearCompleted"
          icon="Delete"
        >
          清除已完成
        </el-button>
      </div>
    </div>
    
    <div class="list-filters" v-if="showFilters">
      <el-select 
        v-model="filterStatus" 
        placeholder="筛选状态" 
        size="small"
        clearable
        @change="applyFilter"
      >
        <el-option label="全部" value="" />
        <el-option label="等待中" value="pending" />
        <el-option label="运行中" value="running" />
        <el-option label="已完成" value="completed" />
        <el-option label="已失败" value="failed" />
      </el-select>
      
      <el-input
        v-model="searchKeyword"
        placeholder="搜索任务名称"
        size="small"
        clearable
        @input="applyFilter"
        style="width: 200px; margin-left: 12px;"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    
    <div class="list-content">
      <el-table 
        :data="filteredJobs" 
        v-loading="isLoading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="id" label="任务ID" width="100" />
        
        <el-table-column prop="task_name" label="任务名称" min-width="200">
          <template #default="{ row }">
            <div class="task-name-cell">
              <el-tooltip :content="row.task_name" placement="top">
                <span class="task-name">{{ row.task_name }}</span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="model_type" label="模型类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getModelTagType(row.model_type)">
              {{ getModelDisplayName(row.model_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusDisplayName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <ProgressBar 
              :percent="row.progress || 0"
              :status="getProgressStatus(row.status)"
              :animated="row.status === 'running'"
              :show-text="true"
              :show-info="false"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                size="small" 
                type="primary" 
                @click="viewJob(row)"
                icon="View"
              >
                查看
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteJob(row)"
                :disabled="row.status === 'running'"
                icon="Delete"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div class="list-pagination" v-if="showPagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalJobs"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { TrainingTask } from '@/api/types'
import ProgressBar from './ProgressBar.vue'
import { Search } from '@element-plus/icons-vue'

// <!-- 
// 审查上下文：
// - 设计意图：提供完整的任务列表展示和管理功能，支持筛选、分页和操作
// - 已知局限：当前使用模拟数据，后续需要连接真实API和WebSocket实时更新
// - 业务背景：生物信息学任务管理的核心UI组件
// - 测试重点：验证各种筛选条件、分页功能和用户交互的正确性
// -->

interface Props {
  title?: string
  jobs?: TrainingTask[]
  isLoading?: boolean
  showFilters?: boolean
  showPagination?: boolean
  totalJobs?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '任务列表',
  jobs: () => [],
  isLoading: false,
  showFilters: true,
  showPagination: true,
  totalJobs: 0
})

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'delete', job: TrainingTask): void
  (e: 'view', job: TrainingTask): void
  (e: 'clear-completed'): void
  (e: 'page-change', page: number, size: number): void
}>()

const router = useRouter()

// 状态
const filterStatus = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedJobs = ref<TrainingTask[]>([])

// 计算属性
const filteredJobs = computed(() => {
  let result = [...props.jobs]
  
  // 状态筛选
  if (filterStatus.value) {
    result = result.filter(job => job.status === filterStatus.value)
  }
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(job => 
      job.task_name.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

// 方法
function applyFilter() {
  // 筛选逻辑已经在computed中实现
}

function refreshJobs() {
  emit('refresh')
}

function clearCompleted() {
  emit('clear-completed')
}

function handleSelectionChange(selection: TrainingTask[]) {
  selectedJobs.value = selection
}

function viewJob(job: TrainingTask) {
  router.push(`/model/task/${job.id}`)
  emit('view', job)
}

function deleteJob(job: TrainingTask) {
  emit('delete', job)
}

function handleSizeChange(size: number) {
  pageSize.value = size
  emit('page-change', currentPage.value, size)
}

function handleCurrentChange(page: number) {
  currentPage.value = page
  emit('page-change', page, pageSize.value)
}

function getModelTagType(modelType: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    mlp: 'info',
    cnn: 'success',
    lstm: 'warning',
    transformer: 'danger'
  }
  return typeMap[modelType] || 'info'
}

function getModelDisplayName(modelType: string): string {
  const nameMap: Record<string, string> = {
    mlp: 'MLP',
    cnn: 'CNN',
    lstm: 'LSTM',
    transformer: 'Transformer'
  }
  return nameMap[modelType] || modelType.toUpperCase()
}

function getStatusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

function getStatusDisplayName(status: string): string {
  const nameMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '已失败'
  }
  return nameMap[status] || status
}

function getProgressStatus(status: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  const statusMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  // 组件挂载时的初始化逻辑
})
</script>

<style scoped>
.job-list {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.list-title {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.list-actions {
  display: flex;
  gap: 12px;
}

.list-filters {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
}

.list-content {
  padding: 20px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.task-name-cell {
  max-width: 200px;
}

.task-name {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-pagination {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  border-radius: 4px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  font-weight: 500;
}
</style>