<template>
  <div class="task-management-page">
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">任务与文件管理</h1>
          <p class="page-description">管理您的任务进度和数据文件</p>
        </div>
        <div class="header-actions-global">
          <el-button 
            type="primary" 
            :icon="Refresh" 
            :loading="jobsStore.loading || filesStore.loading"
            @click="refreshAll"
            size="default"
          >
            刷新全部
          </el-button>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
      <!-- Tab 1: 任务管理 -->
      <el-tab-pane label="任务管理" name="tasks">
        <div class="tasks-content">
          <!-- 筛选栏 -->
          <div class="filter-bar">
            <el-select
              v-model="jobTypeFilter"
              placeholder="任务类型"
              clearable
              style="width: 160px"
              @change="handleFilterChange"
            >
              <el-option label="全部类型" value="" />
              <el-option label="基因组处理" value="genome_process" />
              <el-option label="转录组处理" value="transcriptome_process" />
              <el-option label="蛋白质处理" value="protein_process" />
              <el-option label="多组学整合" value="integration_process" />
              <el-option label="P值整合分析" value="pvalue_integration" />
              <el-option label="模型训练" value="model_train" />
              <el-option label="数据分析" value="data_analysis" />
            </el-select>

            <el-select
              v-model="statusFilter"
              placeholder="任务状态"
              clearable
              style="width: 140px"
              @change="handleFilterChange"
            >
              <el-option label="全部状态" value="" />
              <el-option label="已提交" value="Submitted" />
              <el-option label="处理中" value="Processing" />
              <el-option label="已完成" value="Completed" />
              <el-option label="失败" value="Failed" />
              <el-option label="已取消" value="Cancelled" />
            </el-select>

            <el-input
              v-model="keywordFilter"
              placeholder="搜索关键词"
              clearable
              style="width: 200px"
              @keyup.enter="handleFilterChange"
              @clear="handleFilterChange"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>

            <el-button type="primary" :icon="Refresh" :loading="jobsStore.loading" @click="refreshJobs">
              刷新
            </el-button>
          </div>

          <!-- 任务列表表格 -->
          <el-table
            :data="jobsStore.jobs"
            v-loading="jobsStore.loading"
            stripe
            style="width: 100%"
            empty-text="暂无任务"
            header-cell-class-name="table-header-cell"
          >
            <template #empty>
              <div class="empty-state">
                <el-icon :size="48" color="#c0c4cc"><Document /></el-icon>
                <p>暂无任务</p>
              </div>
            </template>
            <el-table-column prop="job_type_display" label="任务类型" width="130">
              <template #default="{ row }">
                <el-tag :type="getJobTypeTagType(row.job_type)" size="small">
                  {{ row.job_type_display || getJobTypeDisplay(row.job_type) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="job_id" label="任务ID" width="200">
              <template #default="{ row }">
                <span class="job-id">{{ row.job_id }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" :class="{ 'processing-badge': row.status === 'Processing' }">
                  {{ row.status_display || getStatusDisplay(row.status) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="progress" label="进度" width="150">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.progress || 0"
                  :status="getProgressStatus(row.status)"
                  :stroke-width="10"
                />
              </template>
            </el-table-column>

            <el-table-column prop="current_step" label="当前步骤" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="current-step">{{ row.current_step || '-' }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                <span class="create-time">{{ formatDateTime(row.created_at) }}</span>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="400" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <!-- 下载结果：仅 Completed 状态且有 result_file 时显示 -->
                  <el-button
                    v-if="row.status === 'Completed' && row.result_file"
                    type="success"
                    size="small"
                    :icon="Download"
                    @click="handleDownload(row)"
                  >
                    下载
                  </el-button>

                  <!-- 取消：仅 Submitted/Processing 状态时显示 -->
                  <el-button
                    v-if="row.status === 'Submitted' || row.status === 'Processing'"
                    type="warning"
                    size="small"
                    @click="handleCancel(row)"
                  >
                    取消
                  </el-button>

                  <!-- 删除：仅 Completed/Failed/Cancelled 状态时显示 -->
                  <el-button
                    v-if="['Completed', 'Failed', 'Cancelled'].includes(row.status)"
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="handleDelete(row)"
                  >
                    删除
                  </el-button>

                  <!-- 查看详情：始终显示 -->
                  <el-button type="info" size="small" plain @click="showJobDetail(row)">
                    详情
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container" v-if="jobsStore.total > 0">
            <el-pagination
              v-model:current-page="jobsCurrentPage"
              v-model:page-size="jobsPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="jobsStore.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleJobsSizeChange"
              @current-change="handleJobsPageChange"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: 文件管理 -->
      <el-tab-pane label="文件管理" name="files">
        <div class="files-content">
          <!-- 上传区域 -->
          <div class="upload-section">
            <el-card class="upload-card">
              <template #header>
                <div class="card-header">
                  <span class="card-title">文件上传</span>
                  <el-tag type="info" size="small">支持 txt, csv, xlsx 格式</el-tag>
                </div>
              </template>
              
              <FileUploader
                :allowed-types="['txt', 'csv', 'xlsx', 'xls']"
                :max-size="100 * 1024 * 1024"
                :auto-upload="false"
                @file-selected="handleFileSelected"
                @upload-start="handleUploadStart"
                @upload-progress="handleUploadProgress"
                @upload-complete="handleUploadComplete"
                @upload-error="handleUploadError"
              />
              
              <!-- 文件类型选择 -->
              <div v-if="selectedFile" class="file-type-selector mt-3">
                <el-form :model="uploadForm" label-position="top">
                  <el-row :gutter="20">
                    <el-col :span="12">
                      <el-form-item label="文件类型" required>
                        <el-select 
                          v-model="uploadForm.fileType" 
                          placeholder="请选择文件类型"
                          style="width: 100%"
                        >
                          <el-option label="数据集文件" value="dataset" />
                          <el-option label="训练数据" value="train" />
                          <el-option label="验证数据" value="validation" />
                          <el-option label="测试数据" value="test" />
                          <el-option label="交叉验证数据集" value="kfold_dataset" />
                        </el-select>
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="文件描述（可选）">
                        <el-input 
                          v-model="uploadForm.description" 
                          placeholder="请输入文件描述"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                  <el-form-item>
                    <el-button 
                      type="primary" 
                      :loading="filesStore.isUploading"
                      @click="startUpload"
                    >
                      {{ filesStore.isUploading ? '上传中...' : '开始上传' }}
                    </el-button>
                    <el-button @click="clearSelection">取消</el-button>
                  </el-form-item>
                </el-form>
              </div>
            </el-card>
          </div>

          <!-- 上传进度 -->
          <div v-if="filesStore.uploadingFiles.size > 0" class="upload-progress-section">
            <el-card class="progress-card">
              <template #header>
                <div class="card-header">
                  <span class="card-title">上传进度</span>
                  <el-button 
                    type="danger" 
                    size="small" 
                    :icon="Delete"
                    @click="clearCompletedUploads"
                  >
                    清理已完成
                  </el-button>
                </div>
              </template>
              <div class="progress-list">
                <div 
                  v-for="[uploadId, uploadItem] in filesStore.uploadingFiles" 
                  :key="uploadId"
                  class="progress-item"
                >
                  <div class="file-info">
                    <el-icon class="file-icon"><Document /></el-icon>
                    <span class="file-name">{{ uploadItem.file.name }}</span>
                    <el-tag 
                      :type="getUploadStatusTagType(uploadItem.status)"
                      size="small"
                    >
                      {{ getUploadStatusText(uploadItem.status) }}
                    </el-tag>
                  </div>
                  <el-progress 
                    :percentage="uploadItem.progress" 
                    :status="getUploadProgressStatus(uploadItem.status)"
                    class="progress-bar"
                  />
                </div>
              </div>
            </el-card>
          </div>

          <!-- 文件列表 -->
          <div class="files-list-section">
            <el-card class="files-card">
              <template #header>
                <div class="card-header">
                  <span class="card-title">我的文件</span>
                  <div class="header-actions">
                    <el-button 
                      type="primary" 
                      :icon="Refresh"
                      :loading="filesStore.loading"
                      @click="loadFiles"
                      size="default"
                    >
                      刷新
                    </el-button>
                  </div>
                </div>
              </template>

              <!-- 文件列表 -->
              <el-table
                :data="filesStore.fileList"
                :loading="filesStore.loading"
                stripe
                style="width: 100%"
                empty-text="暂无文件"
                header-cell-class-name="table-header-cell"
              >
                <template #empty>
                  <div class="empty-state">
                    <el-icon :size="48" color="#c0c4cc"><Folder /></el-icon>
                    <p>暂无文件</p>
                  </div>
                </template>
                <el-table-column prop="original_name" label="文件名" min-width="200">
                  <template #default="{ row }">
                    <div class="file-name-cell">
                      <el-icon class="file-icon"><Document /></el-icon>
                      <span>{{ row.original_name }}</span>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column prop="file_type" label="类型" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getFileTypeTagType(row.file_type)">
                      {{ getFileTypeText(row.file_type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="file_size" label="大小" width="120">
                  <template #default="{ row }">
                    {{ formatFileSize(row.file_size) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="upload_time" label="上传时间" width="180">
                  <template #default="{ row }">
                    {{ getFileUploadTime(row) }}
                  </template>
                </el-table-column>
                
                <el-table-column label="操作" width="200" fixed="right">
                  <template #default="{ row }">
                    <SmartDownloadButton
                      :file-id="row.id"
                      :file-name="row.original_name"
                      :file-size="row.file_size"
                      type="primary"
                      size="small"
                      text="下载"
                    />
                    <el-button 
                      type="danger" 
                      size="small"
                      :icon="Delete"
                      @click="deleteFile(row)"
                      style="margin-left: 8px"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 分页 -->
              <div class="pagination-container" v-if="filesStore.total > 0">
                <el-pagination
                  v-model:current-page="filesCurrentPage"
                  v-model:page-size="filesPageSize"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="filesStore.total"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleFilesSizeChange"
                  @current-change="handleFilesPageChange"
                />
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 任务详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="任务详情" width="700px" destroy-on-close>
      <div v-if="currentJobDetail" class="job-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID" :span="2">
            <span class="job-id">{{ currentJobDetail.job_id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="任务类型">
            <el-tag :type="getJobTypeTagType(currentJobDetail.job_type)" size="small">
              {{ currentJobDetail.job_type_display || getJobTypeDisplay(currentJobDetail.job_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(currentJobDetail.status)">
              {{ currentJobDetail.status_display || getStatusDisplay(currentJobDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">
            <el-progress :percentage="currentJobDetail.progress || 0" :stroke-width="15" />
          </el-descriptions-item>
          <el-descriptions-item label="当前步骤">
            {{ currentJobDetail.current_step || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(currentJobDetail.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ formatDateTime(currentJobDetail.started_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间" :span="2">
            {{ formatDateTime(currentJobDetail.completed_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentJobDetail.error_message" label="错误信息" :span="2">
            <el-text type="danger">{{ currentJobDetail.error_message }}</el-text>
          </el-descriptions-item>
          <el-descriptions-item v-if="currentJobDetail.result_file" label="结果文件" :span="2">
            <el-link type="primary">{{ currentJobDetail.result_file }}</el-link>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 输入参数 -->
        <div v-if="currentJobDetail.input_params" class="input-params-section">
          <h4>输入参数</h4>
          <el-card shadow="never" class="params-card">
            <pre class="params-json">{{ formatJson(currentJobDetail.input_params) }}</pre>
          </el-card>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button
            v-if="currentJobDetail?.status === 'Completed' && currentJobDetail?.result_file"
            type="success"
            :icon="Download"
            @click="handleDownload(currentJobDetail)"
          >
            下载结果
          </el-button>
          <el-button
            v-if="currentJobDetail?.status === 'Submitted' || currentJobDetail?.status === 'Processing'"
            type="warning"
            @click="handleCancel(currentJobDetail!)"
          >
            取消任务
          </el-button>
          <el-button
            v-if="['Completed', 'Failed', 'Cancelled'].includes(currentJobDetail?.status || '')"
            type="danger"
            :icon="Delete"
            @click="handleDelete(currentJobDetail!)"
          >
            删除任务
          </el-button>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 错误提示 -->
    <div v-if="filesStore.error || jobsStore.error" class="error-toast">
      <el-alert
        :title="filesStore.error || jobsStore.error || ''"
        type="error"
        show-icon
        closable
        @close="clearErrors"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Delete, Refresh, Download, Search, Folder } from '@element-plus/icons-vue'
import { useFilesStore } from '@/stores/files'
import { useJobsStore } from '@/stores/jobs'
import FileUploader from '@/components/FileUpload/FileUploader.vue'
import SmartDownloadButton from '@/components/SmartDownloadButton.vue'
import { FileService } from '@/api'
import { getFileUploadTime } from '@/utils/date-utils'
import { webSocketService } from '@/api/websocket'
import type { UnifiedJob } from '@/api/jobs'
import { JOB_STATUS } from '@/api/jobs'

const route = useRoute()
const filesStore = useFilesStore()
const jobsStore = useJobsStore()

// ===== Tab 状态 =====
const activeTab = ref('tasks')

// ===== 任务管理状态 =====
const jobTypeFilter = ref('')
const statusFilter = ref('')
const keywordFilter = ref('')
const jobsCurrentPage = ref(1)
const jobsPageSize = ref(20)
const detailDialogVisible = ref(false)
const currentJobDetail = ref<UnifiedJob | null>(null)

// ===== 文件管理状态 =====
const selectedFile = ref<File | null>(null)
const filesCurrentPage = ref(1)
const filesPageSize = ref(20)

const uploadForm = reactive({
  fileType: '',
  description: ''
})

// ===== 任务类型映射 =====
const JOB_TYPE_MAP: Record<string, { display: string; tagType: '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' }> = {
  genome_process: { display: '基因组处理', tagType: 'primary' },
  transcriptome_process: { display: '转录组处理', tagType: '' },
  protein_process: { display: '蛋白质处理', tagType: '' },
  integration_process: { display: '多组学整合', tagType: 'warning' },
  pvalue_integration: { display: 'P值整合', tagType: '' },
  model_train: { display: '模型训练', tagType: 'success' },
  data_analysis: { display: '数据分析', tagType: 'info' }
}

// ===== 状态映射 =====
const STATUS_MAP: Record<string, { display: string; tagType: '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' }> = {
  Submitted: { display: '已提交', tagType: 'info' },
  Processing: { display: '处理中', tagType: 'primary' },
  Completed: { display: '已完成', tagType: 'success' },
  Failed: { display: '失败', tagType: 'danger' },
  Cancelled: { display: '已取消', tagType: 'warning' }
}

// ===== 任务管理方法 =====

function getJobTypeDisplay(jobType: string): string {
  return JOB_TYPE_MAP[jobType]?.display || jobType
}

function getJobTypeTagType(jobType: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  return JOB_TYPE_MAP[jobType]?.tagType || 'info'
}

function getStatusDisplay(status: string): string {
  return STATUS_MAP[status]?.display || status
}

function getStatusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  return STATUS_MAP[status]?.tagType || 'info'
}

function getProgressStatus(status: string): '' | 'success' | 'exception' | 'warning' {
  if (status === 'Completed') return 'success'
  if (status === 'Failed') return 'exception'
  if (status === 'Cancelled') return 'warning'
  return ''
}

function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

function formatJson(obj: Record<string, any>): string {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

function handleFilterChange() {
  jobsCurrentPage.value = 1
  loadJobs()
}

async function loadJobs() {
  jobsStore.setFilter({
    job_type: jobTypeFilter.value || undefined,
    status: statusFilter.value || undefined,
    keyword: keywordFilter.value || undefined,
    limit: jobsPageSize.value,
    offset: (jobsCurrentPage.value - 1) * jobsPageSize.value
  })
}

async function refreshJobs() {
  await jobsStore.fetchJobs()
}

async function refreshAll() {
  await Promise.all([
    jobsStore.fetchJobs(),
    filesStore.loadFileList(filesCurrentPage.value, filesPageSize.value)
  ])
}

function handleJobsSizeChange(size: number) {
  jobsPageSize.value = size
  jobsCurrentPage.value = 1
  loadJobs()
}

function handleJobsPageChange(page: number) {
  jobsCurrentPage.value = page
  loadJobs()
}

async function showJobDetail(job: UnifiedJob) {
  try {
    currentJobDetail.value = await jobsStore.fetchJobDetail(job.job_id)
    detailDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '获取任务详情失败')
  }
}

async function handleDownload(job: UnifiedJob) {
  try {
    const downloadUrl = await jobsStore.getDownloadUrl(job.job_id)
    window.open(downloadUrl, '_blank')
  } catch (error: any) {
    ElMessage.error(error.message || '获取下载链接失败')
  }
}

async function handleCancel(job: UnifiedJob) {
  try {
    await ElMessageBox.confirm(
      `确定要取消任务 "${job.job_id}" 吗？`,
      '确认取消',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await jobsStore.cancelJob(job.job_id)
    ElMessage.success('任务已取消')
    detailDialogVisible.value = false
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '取消任务失败')
    }
  }
}

async function handleDelete(job: UnifiedJob) {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${job.job_id}" 吗？删除后无法恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await jobsStore.deleteJob(job.job_id)
    ElMessage.success('任务已删除')
    detailDialogVisible.value = false
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除任务失败')
    }
  }
}

// ===== WebSocket 集成 =====
function setupWebSocket() {
  webSocketService.setOnTaskStatus((data: any) => {
    const { job_id, status, progress, current_step, result_file, error_message } = data
    if (job_id) {
      jobsStore.updateJobStatus(job_id, {
        status,
        progress,
        current_step,
        result_file,
        error_message
      })
    }
  })

  webSocketService.connectTaskStatus().catch((error) => {
    console.error('WebSocket 连接失败:', error)
  })
}

function cleanupWebSocket() {
  webSocketService.setOnTaskStatus(() => {})
}

// ===== 文件管理方法 =====

function handleFileSelected(files: File[]) {
  if (files.length > 0) {
    const file = files[0]
    if (file) {
      selectedFile.value = file
      uploadForm.fileType = FileService.inferFileType(file.name)
    } else {
      selectedFile.value = null
    }
  } else {
    selectedFile.value = null
  }
}

async function handleUploadStart(files: File[]) {
  if (files.length === 0) return
  const file = files[0]
  if (!file) return
  
  if (!uploadForm.fileType) {
    ElMessage.warning('请选择文件类型')
    return
  }

  try {
    await filesStore.uploadFile(file, uploadForm.fileType, uploadForm.description)
  } catch (error) {
    console.error('上传失败:', error)
  }
}

function handleUploadProgress(progress: number) {
  console.log('上传进度:', progress)
}

function handleUploadComplete(_response: any) {
  ElMessage.success('文件上传成功！')
  selectedFile.value = null
  uploadForm.fileType = ''
  uploadForm.description = ''
  loadFiles()
}

function handleUploadError(error: Error) {
  ElMessage.error(`上传失败: ${error.message}`)
}

async function startUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  if (!uploadForm.fileType) {
    ElMessage.warning('请选择文件类型')
    return
  }

  try {
    await filesStore.uploadFile(selectedFile.value, uploadForm.fileType, uploadForm.description)
  } catch (error) {
    console.error('上传失败:', error)
  }
}

function clearSelection() {
  selectedFile.value = null
  uploadForm.fileType = ''
  uploadForm.description = ''
}

function clearCompletedUploads() {
  filesStore.uploadingFiles.forEach((uploadItem, uploadId) => {
    if (uploadItem.status === 'completed' || uploadItem.status === 'failed') {
      filesStore.uploadingFiles.delete(uploadId)
    }
  })
}

async function deleteFile(fileInfo: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${fileInfo.original_name}" 吗？`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )

    await filesStore.deleteFile(fileInfo.id)
    ElMessage.success('文件删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('文件删除失败')
      console.error('删除失败:', error)
    }
  }
}

async function loadFiles() {
  try {
    await filesStore.loadFileList(filesCurrentPage.value, filesPageSize.value)
  } catch (error) {
    console.error('加载文件列表失败:', error)
  }
}

function handleFilesSizeChange(size: number) {
  filesPageSize.value = size
  filesCurrentPage.value = 1
  loadFiles()
}

function handleFilesPageChange(page: number) {
  filesCurrentPage.value = page
  loadFiles()
}

function formatFileSize(bytes: number): string {
  return FileService.formatFileSize(bytes)
}

function getFileTypeTagType(fileType: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const typeMap: Record<string, any> = {
    'dataset': 'primary',
    'train': 'success',
    'validation': 'warning',
    'test': 'danger',
    'kfold_dataset': 'info'
  }
  return typeMap[fileType] || 'info'
}

function getFileTypeText(fileType: string): string {
  const textMap: Record<string, string> = {
    'dataset': '数据集',
    'train': '训练集',
    'validation': '验证集',
    'test': '测试集',
    'kfold_dataset': '交叉验证集'
  }
  return textMap[fileType] || fileType
}

function getUploadStatusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const typeMap: Record<string, any> = {
    'pending': 'info',
    'uploading': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

function getUploadStatusText(status: string): string {
  const textMap: Record<string, string> = {
    'pending': '等待上传',
    'uploading': '上传中',
    'completed': '上传完成',
    'failed': '上传失败'
  }
  return textMap[status] || status
}

function getUploadProgressStatus(status: string): 'success' | 'exception' | 'warning' | undefined {
  const statusMap: Record<string, any> = {
    'completed': 'success',
    'failed': 'exception'
  }
  return statusMap[status]
}

function clearErrors() {
  filesStore.clearError()
  jobsStore.clearError()
}

// ===== 生命周期 =====
onMounted(async () => {
  // 根据路由参数决定默认 Tab
  if (route.query.tab === 'files') {
    activeTab.value = 'files'
  }

  // 加载任务和文件列表
  await Promise.all([
    loadJobs(),
    loadFiles()
  ])

  // 设置 WebSocket
  setupWebSocket()
})

onUnmounted(() => {
  cleanupWebSocket()
})

// 监听 Tab 切换，按需加载数据
watch(activeTab, (newTab) => {
  if (newTab === 'tasks') {
    loadJobs()
  } else if (newTab === 'files') {
    loadFiles()
  }
})
</script>

<style scoped>
.task-management-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.title-section {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0;
  line-height: 1.5;
}

.header-actions-global {
  display: flex;
  gap: 12px;
  align-items: center;
}

.main-tabs {
  min-height: 600px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 任务管理样式 */
.tasks-content {
  padding: 20px 16px;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.filter-bar .el-select,
.filter-bar .el-input {
  transition: all 0.3s ease;
}

.filter-bar .el-select:hover,
.filter-bar .el-input:hover {
  transform: translateY(-1px);
}

/* 输入框和选择框优化 */
:deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px #e4e7ed inset;
  transition: all 0.3s ease;
}

:deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e4e7ed inset;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset !important;
}

.job-id {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.current-step {
  color: #303133;
  font-size: 14px;
  line-height: 1.5;
}

.create-time {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.action-buttons .el-button {
  transition: all 0.3s ease;
}

.action-buttons .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.processing-badge {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { 
    opacity: 1;
    transform: scale(1);
  }
  50% { 
    opacity: 0.6;
    transform: scale(1.05);
  }
}

/* 表格样式优化 */
.el-table {
  border-radius: 4px;
  overflow: hidden;
}

.table-header-cell {
  background-color: #fafafa !important;
  color: #606266;
  font-weight: 600;
  font-size: 14px;
}

.el-table th {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
  font-size: 14px;
}

.el-table td {
  padding: 12px 0;
}

.el-table__row:hover {
  background-color: #f5f7fa !important;
  transition: all 0.2s ease;
}

/* 加载动画优化 */
:deep(.el-loading-spinner) {
  animation: loadingPulse 1.5s ease-in-out infinite;
}

@keyframes loadingPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

:deep(.el-loading-spinner .path) {
  stroke-width: 3;
}

:deep(.el-loading-spinner .el-loading-text) {
  font-size: 14px;
  color: #606266;
  margin-top: 12px;
  font-weight: 500;
}

/* 标签样式 */
.el-tag {
  border-radius: 4px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.el-tag--small {
  padding: 2px 8px;
}

/* 进度条样式 */
:deep(.el-progress__text) {
  font-size: 13px !important;
  font-weight: 500;
}

:deep(.el-progress-bar) {
  border-radius: 5px;
}

/* 文件管理样式 */
.files-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px 16px;
}

.upload-section {
  margin-bottom: 8px;
}

.upload-card {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.upload-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 上传进度区域 */
.upload-progress-section {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.progress-card {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.file-type-selector {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
  margin-top: 8px;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  color: #409eff;
  font-size: 18px;
  flex-shrink: 0;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.progress-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transform: translateX(2px);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.file-name {
  flex: 1;
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-bar {
  margin-top: 8px;
}

/* 文件列表区域 */
.files-list-section {
  animation: fadeIn 0.3s ease;
}

.files-card {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  padding: 16px 0;
  border-top: 1px solid #ebeef5;
}

/* 任务详情弹窗样式 */
:deep(.el-dialog) {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

:deep(.el-dialog__header) {
  padding: 20px 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
}

/* 卡片头部样式 */
:deep(.el-card__header) {
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
  padding: 16px 20px;
}

.job-detail {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 8px;
}

.job-detail::-webkit-scrollbar {
  width: 6px;
}

.job-detail::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 3px;
}

.job-detail::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.job-detail::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.input-params-section {
  margin-top: 20px;
}

.input-params-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

/* 描述列表样式 */
:deep(.el-descriptions__header) {
  margin-bottom: 16px;
}

:deep(.el-descriptions__label) {
  background-color: #fafafa;
  font-weight: 500;
}

:deep(.el-descriptions__content) {
  word-break: break-word;
}

.params-card {
  background-color: #f5f7fa;
}

.params-json {
  margin: 0;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  color: #606266;
  max-height: 300px;
  overflow-y: auto;
  background-color: #fafafa;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
  transition: all 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 表格滚动条 */
:deep(.el-table__body-wrapper)::-webkit-scrollbar,
:deep(.el-table__header-wrapper)::-webkit-scrollbar {
  height: 6px;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-track,
:deep(.el-table__header-wrapper)::-webkit-scrollbar-track {
  background: #f5f7fa;
}

:deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb,
:deep(.el-table__header-wrapper)::-webkit-scrollbar-thumb {
  background: #c0c4cc;
}

.dialog-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  width: 400px;
  animation: slideInRight 0.3s ease;
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state .el-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 992px) {
  .task-management-page {
    padding: 16px;
  }
  
  .page-header {
    padding: 20px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions-global {
    width: 100%;
    justify-content: flex-end;
  }

  .filter-bar {
    flex-direction: row;
  }

  .filter-bar .el-select,
  .filter-bar .el-input {
    flex: 1;
    min-width: 140px;
  }
  
  .files-content {
    padding: 16px;
  }
  
  .tasks-content {
    padding: 16px 12px;
  }
}

@media (max-width: 768px) {
  .task-management-page {
    padding: 12px;
  }
  
  .page-header {
    padding: 16px;
  }
  
  .page-title {
    font-size: 22px;
  }
  
  .page-description {
    font-size: 13px;
  }

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    padding: 12px;
  }

  .filter-bar .el-select,
  .filter-bar .el-input {
    width: 100% !important;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: stretch;
  }
  
  .header-actions .el-button {
    flex: 1;
  }
  
  .error-toast {
    width: calc(100% - 40px);
    left: 20px;
    right: 20px;
  }

  .action-buttons {
    flex-direction: column;
  }
  
  .action-buttons .el-button {
    width: 100%;
  }
  
  .files-content {
    padding: 12px;
    gap: 16px;
  }
  
  .upload-card,
  .progress-card,
  .files-card {
    border-radius: 6px;
  }
  
  .progress-item {
    padding: 12px;
  }
  
  .file-name {
    font-size: 13px;
  }
}
</style>
