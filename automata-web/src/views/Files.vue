<template>
  <div class="files-page">
    <div class="page-header">
      <h1 class="page-title">文件管理</h1>
      <p class="page-description">上传、管理和分析您的生物信息学数据文件</p>
    </div>

    <div class="files-content">
      <!-- 上传区域 -->
      <div class="upload-section">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <span>文件上传</span>
              <el-tag type="info">支持 txt, csv, xlsx 格式</el-tag>
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
            <span>上传进度</span>
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
                  :type="getStatusTagType(uploadItem.status)"
                  size="small"
                >
                  {{ getStatusText(uploadItem.status) }}
                </el-tag>
              </div>
              <el-progress 
                :percentage="uploadItem.progress" 
                :status="getProgressStatus(uploadItem.status)"
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
              <span>我的文件</span>
              <div class="header-actions">
                <el-button 
                  type="primary" 
                  :icon="Refresh"
                  :loading="filesStore.loading"
                  @click="loadFiles"
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
          >
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
                {{ formatDate(row.upload_time) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <el-dropdown trigger="click" @command="(command: string) => handleDownloadCommand(command, row)">
                  <el-button type="primary" size="small" :icon="Download">
                    下载
                    <el-icon class="el-icon--right">
                      <arrow-down />
                    </el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="normal">普通下载</el-dropdown-item>
                      <el-dropdown-item command="chunked">分片下载</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button 
                  type="danger" 
                  size="small"
                  :icon="Delete"
                  @click="deleteFile(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container" v-if="filesStore.total > 0">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="filesStore.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 分片下载弹窗 -->
    <el-dialog
      v-model="showChunkedDownload"
      :title="`分片下载 - ${currentDownloadFile?.original_name}`"
      width="600px"
      destroy-on-close
    >
      <FileChunkedDownloader
        v-if="currentDownloadFile"
        :file-id="currentDownloadFile.id"
        :file-name="currentDownloadFile.original_name"
        @download-complete="handleChunkedDownloadComplete"
        @download-error="handleChunkedDownloadError"
      />
    </el-dialog>

    <!-- 错误提示 -->
    <div v-if="filesStore.error" class="error-toast">
      <el-alert
        :title="filesStore.error"
        type="error"
        show-icon
        closable
        @close="filesStore.clearError()"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
// <!-- 
// 审查上下文：
// - 设计意图：提供完整的文件管理界面，集成上传、列表、下载、删除功能
// - 已知局限：批量操作功能尚未实现，可以后续添加
// - 业务背景：支持生物信息学研究中的各种数据文件管理需求
// - 测试重点：文件上传流程、WebSocket进度更新、表格操作、分页功能
// -->
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Download, Delete, Refresh, ArrowDown } from '@element-plus/icons-vue'
import { useFilesStore } from '@/stores/files'
import FileUploader from '@/components/FileUpload/FileUploader.vue'
import FileChunkedDownloader from '@/components/FileChunkedDownloader.vue'
import { FileService } from '@/api'

const filesStore = useFilesStore()

// 状态
const selectedFile = ref<File | null>(null)
const showChunkedDownload = ref(false)
const currentDownloadFile = ref<any>(null)
const currentPage = ref<number>(1)
const pageSize = ref<number>(20)

// 上传表单
const uploadForm = reactive({
  fileType: '',
  description: ''
})

/**
 * 处理文件选择
 */
function handleFileSelected(files: File[]) {
  if (files.length > 0) {
    const file = files[0]
    if (file) {
      selectedFile.value = file
      // 自动推断文件类型
      uploadForm.fileType = FileService.inferFileType(file.name)
    } else {
      selectedFile.value = null
    }
  } else {
    selectedFile.value = null
  }
}

/**
 * 处理上传开始
 */
async function handleUploadStart(files: File[]) {
  if (files.length === 0) return
  
  const file = files[0]
  if (!file) return
  
  if (!uploadForm.fileType) {
    ElMessage.warning('请选择文件类型')
    return
  }

  try {
    await filesStore.uploadFile(
      file,
      uploadForm.fileType,
      uploadForm.description
    )
  } catch (error) {
    console.error('上传失败:', error)
  }
}

/**
 * 处理上传进度
 */
function handleUploadProgress(progress: number) {
  console.log('上传进度:', progress)
}

/**
 * 处理上传完成
 */
function handleUploadComplete(response: any) {
  ElMessage.success('文件上传成功！')
  selectedFile.value = null
  uploadForm.fileType = ''
  uploadForm.description = ''
  loadFiles()
}

/**
 * 处理上传错误
 */
function handleUploadError(error: Error) {
  ElMessage.error(`上传失败: ${error.message}`)
}

/**
 * 开始上传
 */
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
    await filesStore.uploadFile(
      selectedFile.value,
      uploadForm.fileType,
      uploadForm.description
    )
  } catch (error) {
    console.error('上传失败:', error)
  }
}

/**
 * 清除文件选择
 */
function clearSelection() {
  selectedFile.value = null
  uploadForm.fileType = ''
  uploadForm.description = ''
}

/**
 * 处理下载命令
 */
function handleDownloadCommand(command: string, fileInfo: any) {
  if (command === 'normal') {
    downloadFile(fileInfo)
  } else if (command === 'chunked') {
    startChunkedDownload(fileInfo)
  }
}

/**
 * 普通下载文件
 */
async function downloadFile(fileInfo: any) {
  try {
    await filesStore.downloadFile(fileInfo.id, fileInfo.original_name)
    ElMessage.success('文件下载已开始')
  } catch (error) {
    ElMessage.error('文件下载失败')
    console.error('下载失败:', error)
  }
}

/**
 * 开始分片下载
 */
function startChunkedDownload(fileInfo: any) {
  currentDownloadFile.value = fileInfo
  showChunkedDownload.value = true
}

/**
 * 分片下载完成处理
 */
function handleChunkedDownloadComplete() {
  ElMessage.success('分片下载完成！')
  showChunkedDownload.value = false
  currentDownloadFile.value = null
}

/**
 * 分片下载错误处理
 */
function handleChunkedDownloadError(error: string) {
  ElMessage.error(`分片下载失败: ${error}`)
  showChunkedDownload.value = false
  currentDownloadFile.value = null
}

/**
 * 删除文件
 */
async function deleteFile(fileInfo: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${fileInfo.original_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
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

/**
 * 加载文件列表
 */
async function loadFiles() {
  try {
    await filesStore.loadFileList(currentPage.value, pageSize.value)
  } catch (error) {
    console.error('加载文件列表失败:', error)
  }
}

/**
 * 处理分页大小变化
 */
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadFiles()
}

/**
 * 处理当前页变化
 */
function handleCurrentChange(page: number) {
  currentPage.value = page
  loadFiles()
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  return FileService.formatFileSize(bytes)
}

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString('zh-CN')
}

/**
 * 获取文件类型标签类型
 */
function getFileTypeTagType(fileType: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<string, any> = {
    'dataset': 'primary',
    'train': 'success',
    'validation': 'warning',
    'test': 'danger',
    'kfold_dataset': 'info'
  }
  return typeMap[fileType] || 'info'
}

/**
 * 获取文件类型文本
 */
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

/**
 * 获取状态标签类型
 */
function getStatusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<string, any> = {
    'pending': 'info',
    'uploading': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取状态文本
 */
function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    'pending': '等待上传',
    'uploading': '上传中',
    'completed': '上传完成',
    'failed': '上传失败'
  }
  return textMap[status] || status
}

/**
 * 获取进度状态
 */
function getProgressStatus(status: string): 'success' | 'exception' | 'warning' | undefined {
  const statusMap: Record<string, any> = {
    'completed': 'success',
    'failed': 'exception'
  }
  return statusMap[status]
}

// 初始化WebSocket连接
onMounted(async () => {
  await filesStore.initializeWebSocket()
  await loadFiles()
})

// 监听分页参数变化
watch([currentPage, pageSize], () => {
  loadFiles()
})
</script>

<style scoped>
.files-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.files-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.file-type-selector {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #409eff;
  font-size: 16px;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background-color: #fafafa;
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
}

.progress-bar {
  margin-top: 8px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  width: 400px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .files-page {
    padding: 12px;
  }
  
  .page-title {
    font-size: 24px;
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
}
</style>