<template>
  <el-button
    :type="type"
    :size="size"
    :loading="downloading"
    :disabled="disabled"
    @click="handleDownload"
  >
    <el-icon v-if="!downloading"><Download /></el-icon>
    {{ downloading ? '下载中...' : text }}
  </el-button>
</template>

<script setup lang="ts">
/**
 * 智能下载按钮组件
 * 
 * 根据文件大小自动选择下载方式：
 * - 小文件（< 10MB）：直接下载
 * - 大文件（>= 10MB）：使用签名链接，通过iframe下载，不阻塞前端
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { apiClient } from '@/api/client'

// 文件大小阈值：10MB
const LARGE_FILE_THRESHOLD = 10 * 1024 * 1024

interface Props {
  fileId: string
  fileName: string
  fileSize: number
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  size?: 'large' | 'default' | 'small'
  text?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'primary',
  size: 'small',
  text: '下载',
  disabled: false
})

const emit = defineEmits<{
  (e: 'download-start'): void
  (e: 'download-complete'): void
  (e: 'download-error', error: string): void
}>()

const downloading = ref(false)

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

/**
 * 处理下载
 */
async function handleDownload() {
  if (downloading.value) return
  
  downloading.value = true
  emit('download-start')
  
  try {
    const isLargeFile = props.fileSize >= LARGE_FILE_THRESHOLD
    
    if (isLargeFile) {
      console.log(`📦 大文件下载 (${formatFileSize(props.fileSize)})，使用直接链接`)
      await downloadLargeFile()
    } else {
      console.log(`📄 小文件下载 (${formatFileSize(props.fileSize)})，使用普通下载`)
      await downloadSmallFile()
    }
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : '下载失败'
    console.error('❌ 下载失败:', errorMsg)
    ElMessage.error(errorMsg)
    emit('download-error', errorMsg)
  } finally {
    downloading.value = false
  }
}

/**
 * 小文件下载：直接通过API下载
 */
async function downloadSmallFile() {
  try {
    // 获取文件内容
    const response = await apiClient.getInstance().get(`/v1/files/${props.fileId}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', props.fileName)
    document.body.appendChild(link)
    link.click()
    
    // 清理
    window.URL.revokeObjectURL(url)
    document.body.removeChild(link)
    
    ElMessage.success('下载完成')
    emit('download-complete')
  } catch (error) {
    throw error
  }
}

/**
 * 大文件下载：使用签名链接 + iframe方式
 */
async function downloadLargeFile() {
  try {
    // 获取直接下载链接
    const response = await apiClient.getInstance().get(`/v1/files/${props.fileId}/direct-link`)
    const { download_url } = response.data
    
    console.log('✅ 获取下载链接成功，有效期 300 秒')
    
    // 使用隐藏的iframe下载，不阻塞页面
    const iframe = document.createElement('iframe')
    iframe.style.display = 'none'
    iframe.src = download_url
    document.body.appendChild(iframe)
    
    // 显示提示
    ElMessage.success('下载已开始，请勿关闭页面')
    
    // 5分钟后清理iframe（足够完成下载）
    setTimeout(() => {
      if (iframe.parentNode) {
        iframe.parentNode.removeChild(iframe)
      }
    }, 300000)
    
    emit('download-complete')
  } catch (error) {
    throw error
  }
}
</script>
