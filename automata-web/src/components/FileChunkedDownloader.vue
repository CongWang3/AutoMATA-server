<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

interface FileInfo {
  file_id: string
  file_name: string
  file_size: number
  chunk_size: number
  support_range: boolean
}

interface DownloadState {
  fileInfo: FileInfo | null
  downloadedBytes: number
  isDownloading: boolean
  progress: number
  chunks: Blob[]
  totalChunks: number
}

const props = defineProps<{
  fileId: string
  fileName: string
}>()

const emit = defineEmits<{
  (e: 'download-complete'): void
  (e: 'download-error', error: string): void
}>()

const downloadState = reactive<DownloadState>({
  fileInfo: null,
  downloadedBytes: 0,
  isDownloading: false,
  progress: 0,
  chunks: [],
  totalChunks: 0
})

const chunkSize = 5 * 1024 * 1024 // 5MB

// 获取文件信息
async function getFileInfo(): Promise<FileInfo | null> {
  try {
    const response = await axios.get(`/api/v1/files/chunked/session/${props.fileId}`)
    return response.data
  } catch (error: any) {
    console.error('获取文件信息失败:', error)
    if (error.response) {
      ElMessage.error(`服务器错误: ${error.response.status} - ${error.response.data.detail || '未知错误'}`)
    } else {
      ElMessage.error(`网络错误: ${error.message}`)
    }
    return null
  }
}

// 下载单个分片
async function downloadChunk(start: number, end: number): Promise<Blob | null> {
  try {
    const response = await axios.get(
      `/api/v1/files/chunked/download/${props.fileId}`,
      {
        responseType: 'blob',
        headers: {
          'Range': `bytes=${start}-${end}`
        }
      }
    )
    return response.data
  } catch (error: any) {
    console.error(`下载分片失败 (${start}-${end}):`, error)
    return null
  }
}

// 更新下载进度
function updateProgress() {
  if (downloadState.fileInfo) {
    downloadState.progress = Math.round(
      (downloadState.downloadedBytes / downloadState.fileInfo.file_size) * 100
    )
  }
}

// 并发下载所有分片
async function downloadAllChunks() {
  if (!downloadState.fileInfo) return

  const { file_size } = downloadState.fileInfo
  const totalChunks = Math.ceil(file_size / chunkSize)
  downloadState.totalChunks = totalChunks
  
  const pendingRanges: [number, number][] = []
  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize
    const end = Math.min(start + chunkSize - 1, file_size - 1)
    pendingRanges.push([start, end])
  }

  const maxConcurrent = 3
  const activeDownloads: Promise<void>[] = []

  while (pendingRanges.length > 0 || activeDownloads.length > 0) {
    // 启动新的下载任务
    while (pendingRanges.length > 0 && activeDownloads.length < maxConcurrent) {
      const [start, end] = pendingRanges.shift()!
      
      const downloadPromise = downloadChunk(start, end).then(blob => {
        if (blob) {
          downloadState.chunks.push(blob)
          downloadState.downloadedBytes += blob.size
          updateProgress()
        }
        // 从活动下载中移除完成的任务
        const index = activeDownloads.indexOf(downloadPromise as any)
        if (index > -1) {
          activeDownloads.splice(index, 1)
        }
      })

      activeDownloads.push(downloadPromise as any)
    }

    // 等待至少一个下载完成
    if (activeDownloads.length > 0) {
      await Promise.race(activeDownloads)
    }
  }
}

// 合并分片并触发下载
function mergeAndDownload() {
  if (downloadState.chunks.length === 0) return

  const blob = new Blob(downloadState.chunks, { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = props.fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
  
  // 清理内存
  downloadState.chunks = []
}

// 主下载函数
async function startChunkedDownload() {
  if (downloadState.isDownloading) return

  try {
    downloadState.isDownloading = true
    ElMessage.info('开始分片下载...')

    // 获取文件信息
    const fileInfo = await getFileInfo()
    if (!fileInfo) return

    downloadState.fileInfo = fileInfo
    console.log('📁 文件信息:', fileInfo)

    // 下载所有分片
    await downloadAllChunks()

    // 检查是否下载完整
    if (downloadState.downloadedBytes === fileInfo.file_size) {
      mergeAndDownload()
      ElMessage.success('文件下载完成！')
      emit('download-complete')
    } else {
      throw new Error(`下载不完整: 期望 ${fileInfo.file_size} bytes, 实际 ${downloadState.downloadedBytes} bytes`)
    }

  } catch (error: any) {
    console.error('分片下载失败:', error)
    const errorMessage = error.message || String(error)
    ElMessage.error(`下载失败: ${errorMessage}`)
    emit('download-error', errorMessage)
  } finally {
    downloadState.isDownloading = false
    downloadState.downloadedBytes = 0
    downloadState.progress = 0
  }
}

// 获取人类可读的文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

defineExpose({
  startChunkedDownload
})
</script>

<template>
  <div class="chunked-downloader">
    <div class="download-info">
      <h4>分片下载: {{ fileName }}</h4>
      <div class="file-stats" v-if="downloadState.fileInfo">
        <span>文件大小: {{ formatFileSize(downloadState.fileInfo.file_size) }}</span>
        <span>分片大小: {{ formatFileSize(chunkSize) }}</span>
        <span>总分片数: {{ downloadState.totalChunks }}</span>
      </div>
    </div>

    <div class="download-progress" v-if="downloadState.isDownloading">
      <el-progress 
        :percentage="downloadState.progress" 
        :stroke-width="20"
        status="success"
      />
      <div class="progress-details">
        <span>已下载: {{ formatFileSize(downloadState.downloadedBytes) }} / {{ formatFileSize(downloadState.fileInfo?.file_size || 0) }}</span>
        <span>进度: {{ downloadState.progress }}%</span>
        <span>已接收分片: {{ downloadState.chunks.length }}/{{ downloadState.totalChunks }}</span>
      </div>
    </div>

    <div class="download-controls">
      <el-button 
        type="primary" 
        @click="startChunkedDownload" 
        :loading="downloadState.isDownloading"
        :disabled="downloadState.isDownloading"
      >
        {{ downloadState.isDownloading ? '下载中...' : '开始分片下载' }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.chunked-downloader {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: #fafafa;
}

.download-info h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.file-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  font-size: 14px;
  color: #606266;
}

.download-progress {
  margin: 20px 0;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
}

.download-controls {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}
</style>