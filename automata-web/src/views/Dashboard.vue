<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h1 class="dashboard-title">欢迎回来，{{ userStore.username }} 👋</h1>
      <p class="dashboard-subtitle">您的生物信息学分析平台</p>
    </div>

    <div class="dashboard-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon primary">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ filesStore.total }}</div>
              <div class="stat-label">文件总数</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><Upload /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ uploadingCount }}</div>
              <div class="stat-label">正在上传</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">0</div>
              <div class="stat-label">分析任务</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon danger">
              <el-icon><Finished /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">0</div>
              <div class="stat-label">完成任务</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 快捷操作 -->
      <div class="quick-actions">
        <el-card class="actions-card">
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          
          <div class="actions-grid">
            <el-button 
              type="primary" 
              size="large"
              class="action-button"
              @click="goToFiles"
            >
              <template #icon>
                <el-icon><Upload /></el-icon>
              </template>
              上传文件
            </el-button>
            
            <el-button 
              type="success" 
              size="large"
              class="action-button"
              @click="goToTraining"
            >
              <template #icon>
                <el-icon><Setting /></el-icon>
              </template>
              模型训练
            </el-button>
            
            <el-button 
              type="warning" 
              size="large"
              class="action-button"
              @click="goToAnalysis"
            >
              <template #icon>
                <el-icon><DataAnalysis /></el-icon>
              </template>
              数据分析
            </el-button>
            
            <el-button 
              type="info" 
              size="large"
              class="action-button"
              @click="goToHelp"
            >
              <template #icon>
                <el-icon><QuestionFilled /></el-icon>
              </template>
              使用帮助
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 最近文件 -->
      <div class="recent-files">
        <el-card class="files-card">
          <template #header>
            <div class="card-header">
              <span>最近文件</span>
              <el-button 
                type="primary" 
                text
                @click="goToFiles"
              >
                查看全部
              </el-button>
            </div>
          </template>

          <div v-if="recentFiles.length > 0" class="files-list">
            <div 
              v-for="file in recentFiles" 
              :key="file.id"
              class="file-item"
              @click="downloadRecentFile(file)"
            >
              <div class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <div class="file-details">
                  <div class="file-name">{{ file.original_name }}</div>
                  <div class="file-meta">
                    <el-tag 
                      :type="getFileTypeTagType(file.file_type)"
                      size="small"
                    >
                      {{ getFileTypeText(file.file_type) }}
                    </el-tag>
                    <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                    <span class="file-time">{{ getFileUploadTime(file) }}</span>
                  </div>
                </div>
              </div>
              <el-button 
                type="primary" 
                text 
                :icon="Download"
                size="small"
              >
                下载
              </el-button>
            </div>
          </div>
          
          <div v-else class="empty-state">
            <el-empty description="暂无文件，快来上传您的第一个文件吧！">
              <el-button type="primary" @click="goToFiles">上传文件</el-button>
            </el-empty>
          </div>
        </el-card>
      </div>

      <!-- 系统状态 -->
      <div class="system-status">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
              <el-tag :type="connectionStatus.type">
                {{ connectionStatus.text }}
              </el-tag>
            </div>
          </template>

          <div class="status-content">
            <div class="status-item">
              <span class="status-label">WebSocket连接:</span>
              <el-tag :type="webSocketStatus.type">
                {{ webSocketStatus.text }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">认证状态:</span>
              <el-tag :type="authStatus.type">
                {{ authStatus.text }}
              </el-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">服务器时间:</span>
              <span>{{ currentTime }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// <!-- 
// 审查上下文：
// - 设计意图：提供综合性的仪表板界面，展示关键指标和快速访问入口
// - 已知局限：部分统计数据目前是静态的，需要与后端API对接获取实时数据
// - 业务背景：作为用户进入平台后的首页，需要提供全面的信息概览
// - 测试重点：数据展示准确性、链接跳转、状态监控、响应式布局
// -->
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Document, 
  Upload, 
  DataAnalysis, 
  Finished, 
  Setting, 
  QuestionFilled, 
  Download 
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useFilesStore } from '@/stores/files'
import { webSocketService } from '@/api'
import { webSocketManager } from '@/utils/websocket-manager'
import { FileService } from '@/api'
import { getFileUploadTime } from '@/utils/date-utils'

const router = useRouter()
const userStore = useUserStore()
const filesStore = useFilesStore()

// 状态
const currentTime = ref<string>('')

// 计算属性
const recentFiles = computed(() => {
  return filesStore.fileList.slice(0, 5)
})

const uploadingCount = computed(() => {
  let count = 0
  for (const item of filesStore.uploadingFiles.values()) {
    if (item.status === 'uploading') {
      count++
    }
  }
  return count
})

const connectionStatus = computed(() => {
  if (webSocketService.isConnected()) {
    return { type: 'success', text: '已连接' }
  } else {
    return { type: 'danger', text: '未连接' }
  }
})

const webSocketStatus = computed(() => {
  const managerStatus = webSocketManager.getStatus()
  if (managerStatus.isActive && managerStatus.isConnected) {
    return { type: 'success', text: '已连接' }
  } else if (managerStatus.isActive && !managerStatus.isConnected) {
    return { type: 'warning', text: '连接中' }
  } else {
    return { type: 'danger', text: '已断开' }
  }
})

const authStatus = computed(() => {
  if (userStore.isAuthenticated) {
    return { type: 'success', text: '已认证' }
  } else {
    return { type: 'danger', text: '未认证' }
  }
})

// 方法
function goToFiles() {
  router.push('/files')
}

function goToTraining() {
  router.push('/model/train/dashboard')
}

function goToAnalysis() {
  router.push('/analysis')
}

function goToHelp() {
  router.push('/help')
}

async function downloadRecentFile(file: any) {
  try {
    await filesStore.downloadFile(file.id, file.original_name)
    ElMessage.success('文件下载已开始')
  } catch (error) {
    ElMessage.error('文件下载失败')
    console.error('下载失败:', error)
  }
}

function formatFileSize(bytes: number): string {
  return FileService.formatFileSize(bytes)
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

function getFileTypeTagType(fileType: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
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

function updateTime() {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

// 生命周期
onMounted(async () => {
  // 初始化数据
  if (userStore.isAuthenticated) {
    try {
      await filesStore.loadFileList(1, 10)
      // WebSocket连接由管理器自动处理，无需手动初始化
      console.log('✅ Dashboard数据初始化完成')
    } catch (error) {
      console.error('加载文件列表失败:', error)
    }
  }
  
  // 启动时间更新
  updateTime()
  const timer = setInterval(updateTime, 1000)
  
  // 保存定时器引用以便清理
  ;(window as any).__dashboardTimer = timer
})

onUnmounted(() => {
  // 清理定时器
  const timer = (window as any).__dashboardTimer
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
}

.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.dashboard-subtitle {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.primary {
  background: linear-gradient(135deg, #409eff, #337ecc);
}

.stat-icon.success {
  background: linear-gradient(135deg, #67c23a, #529b2e);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #e6a23c, #b88230);
}

.stat-icon.danger {
  background: linear-gradient(135deg, #f56c6c, #c45656);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

/* 快捷操作 */
.actions-card {
  height: fit-content;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}

.action-button {
  height: 60px;
  font-size: 16px;
  font-weight: 500;
}

/* 最近文件 */
.files-card {
  height: fit-content;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-item:hover {
  border-color: #409eff;
  background-color: #f5f7fa;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  font-size: 20px;
  color: #409eff;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.file-size::before {
  content: "•";
}

.file-time::before {
  content: "•";
}

.empty-state {
  padding: 40px 0;
}

/* 系统状态 */
.status-card {
  height: fit-content;
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-label {
  font-weight: 500;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-page {
    padding: 12px;
  }
  
  .dashboard-title {
    font-size: 24px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  
  .stat-content {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .file-meta {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .file-size::before,
  .file-time::before {
    content: "";
  }
  
  .status-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>