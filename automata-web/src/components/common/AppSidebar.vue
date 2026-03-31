<template>
  <div class="app-sidebar" :class="{ 'collapsed': collapsed }">
    <div class="sidebar-header">
      <div class="logo" v-if="!collapsed">
        <img src="https://xxs-img.oss-cn-hangzhou.aliyuncs.com/img202601261643927.png" alt="AutoMATA" />
      </div>
      <div class="toggle-btn" @click="toggleCollapse">
        <el-icon><Expand v-if="collapsed" /><Fold v-else /></el-icon>
      </div>
    </div>
    
    <div class="sidebar-menu">
      <el-menu
        :default-active="currentRoute"
        :collapse="collapsed"
        :unique-opened="true"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <template #title>Home</template>
        </el-menu-item>
        
        <el-sub-menu index="data-process">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>Data processing</span>
          </template>
          <el-menu-item index="/data-process/genome">Genome</el-menu-item>
          <el-menu-item index="/data-process/transcriptome">Transcriptome</el-menu-item>
          <el-menu-item index="/data-process/protein">Proteome</el-menu-item>
          <el-menu-item index="/data-process/integration">Integration</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="model">
          <template #title>
            <el-icon><SetUp /></el-icon>
            <span>Model training</span>
          </template>
          <el-menu-item index="/model/train/supervised">Supervised</el-menu-item>
          <el-menu-item index="/model/train/unsupervised">Unsupervised</el-menu-item>
          <el-menu-item index="/model/train/semi-supervised">Semi-supervised</el-menu-item>
          <el-menu-item index="/model/train/analyze-train">Analyze &amp; train</el-menu-item>
          <el-menu-item index="/model/use">Model use</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="analysis">
          <template #title>
            <el-icon><PieChart /></el-icon>
            <span>Data analysis</span>
          </template>
          <el-menu-item index="/data-analysis">Differential expression</el-menu-item>
          <el-menu-item index="/data-analysis/go">Enrichment</el-menu-item>
          <el-menu-item index="/data-analysis/pca">Visualization</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/help">
          <el-icon><QuestionFilled /></el-icon>
          <template #title>Help</template>
        </el-menu-item>
      </el-menu>
    </div>
    
    <div class="sidebar-footer" v-if="!collapsed">
      <div class="user-info" v-if="userStore.userInfo">
        <el-avatar :size="32" :src="userStore.userInfo.avatar_url">
          {{ userStore.userInfo.username.charAt(0).toUpperCase() }}
        </el-avatar>
        <div class="user-details">
          <div class="username">{{ userStore.userInfo.username }}</div>
          <div class="email">{{ userStore.userInfo.email }}</div>
        </div>
      </div>
      <div class="quick-actions">
        <el-button 
          circle 
          size="small" 
          @click="toggleTheme"
          :icon="theme === 'dark' ? 'Sunny' : 'Moon'"
        />
        <el-button 
          circle 
          size="small" 
          @click="logout"
          icon="SwitchButton"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRefs } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useUIStore } from '@/stores/ui'
import { 
  House, 
  DataAnalysis, 
  SetUp, 
  PieChart, 
  QuestionFilled, 
  Expand, 
  Fold,
  Sunny,
  Moon
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const uiStore = useUIStore()

// 使用 toRefs 解构 store 属性以保持响应性
const { sidebarCollapsed: collapsed, theme } = toRefs(uiStore)
const currentRoute = computed(() => route.path)

// 方法
function toggleCollapse() {
  uiStore.toggleSidebar()
}

function toggleTheme() {
  const newTheme = theme.value === 'light' ? 'dark' : 'light'
  uiStore.setTheme(newTheme)
}

function handleMenuSelect(index: string) {
  router.push(index)
}

function logout() {
  userStore.logout()
  // 路由跳转已在 userStore.logout() 中处理
}
</script>

<style scoped>
.app-sidebar {
  width: 240px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.app-sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo img {
  height: 32px;
  width: auto;
}

.toggle-btn {
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.toggle-btn:hover {
  background-color: #f5f7fa;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
}

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.user-details {
  margin-left: 12px;
  overflow: hidden;
}

.username {
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.email {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-actions {
  display: flex;
  gap: 8px;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  height: 48px;
  line-height: 48px;
}

:deep(.el-menu-item.is-active) {
  background-color: #ecf5ff;
  color: #409eff;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: #f5f7fa;
}

/* 折叠状态样式 */
.app-sidebar.collapsed .user-info,
.app-sidebar.collapsed .quick-actions {
  display: none;
}
</style>