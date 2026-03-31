<template>
  <el-button
    :type="type"
    :size="size"
    :loading="downloading"
    :disabled="disabled"
    @click="handleDownload"
  >
    <el-icon v-if="!downloading"><Download /></el-icon>
    {{ downloading ? 'Downloading…' : text }}
  </el-button>
</template>

<script setup lang="ts">
/**
 * 智能下载按钮组件
 * 
 * 所有下载都使用独立下载服务器（8001端口），完全绕过 Vite 代理，避免阻塞
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { apiClient } from '@/api/client'

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
  text: 'Download',
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
 * 处理下载 - 所有文件都通过独立下载服务器，避免阻塞 Vite 代理
 */
async function handleDownload() {
  if (downloading.value) return
  
  downloading.value = true
  emit('download-start')
  
  try {
    console.log(`📦 下载文件 (${formatFileSize(props.fileSize)})，使用独立下载服务器`)
    await downloadViaServer()
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Download failed'
    console.error('❌ 下载失败:', errorMsg)
    ElMessage.error(errorMsg)
    emit('download-error', errorMsg)
  } finally {
    downloading.value = false
  }
}

/**
 * 通过独立下载服务器下载文件
 */
async function downloadViaServer() {
  try {
    // 获取直接下载链接（指向独立下载服务器 8001 端口）
    const response = await apiClient.getInstance().get(`/v1/files/${props.fileId}/direct-link`)
    const { download_url } = response.data
    
    console.log('✅ 获取下载链接成功，有效期 300 秒')
    console.log('📥 下载链接:', download_url)
    
    // 使用 <a> 标签触发下载（比 iframe 更轻量）
    const link = document.createElement('a')
    link.href = download_url
    link.download = props.fileName
    link.target = '_blank'  // 在新窗口打开，避免阻塞当前页面
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 显示提示
    ElMessage.success('Download started')
    
    emit('download-complete')
  } catch (error) {
    throw error
  }
}
</script>
