<template>
  <nav class="main-menu navbar fixed-top navbar-expand-lg">
    <div class="container-fluid">
      <!-- <div class="main-logo">
        <router-link to="/" class="navbar-brand">
          <img 
            :src="logoPath" 
            alt="AutoMATA Logo" 
            class="img-fluid" 
            width="220" 
            height="44"
          >
        </router-link>
      </div> -->
      
      <!-- 桌面端菜单 -->
      <div class="desktop-menu d-none d-lg-flex align-items-center">
        <ul class="navbar-nav menu-list d-flex gap-3 mb-0">
          <li class="nav-item">
            <router-link 
              to="/dashboard" 
              class="nav-link" 
              :class="{ active: $route.name === 'dashboard' }"
            >
              <el-icon class="menu-icon"><House /></el-icon>
              首页
            </router-link>
          </li>
          
          <li class="nav-item dropdown">
            <a 
              class="nav-link dropdown-toggle" 
              role="button" 
              id="dataProcessDropdown"
              data-bs-toggle="dropdown" 
              aria-expanded="false"
            >
              <el-icon class="menu-icon"><DataAnalysis /></el-icon>
              数据处理
            </a>
            <ul class="dropdown-menu" aria-labelledby="dataProcessDropdown">
              <li>
                <router-link 
                  to="/data-process/genome" 
                  class="dropdown-item"
                >
                  基因组
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/data-process/transcriptome" 
                  class="dropdown-item"
                >
                  转录组
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/data-process/protein" 
                  class="dropdown-item"
                >
                  蛋白质组
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/data-process/integration" 
                  class="dropdown-item"
                >
                  数据整合
                </router-link>
              </li>
            </ul>
          </li>
          
          <li class="nav-item dropdown">
            <a 
              class="nav-link dropdown-toggle" 
              role="button" 
              id="modelDropdown"
              data-bs-toggle="dropdown" 
              aria-expanded="false"
            >
              <el-icon class="menu-icon"><SetUp /></el-icon>
              模型训练
            </a>
            <ul class="dropdown-menu" aria-labelledby="modelDropdown">
              <li>
                <router-link 
                  to="/model/train/supervised" 
                  class="dropdown-item"
                >
                  监督学习
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/model/train/unsupervised" 
                  class="dropdown-item"
                >
                  无监督学习
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/model/train/semi-supervised" 
                  class="dropdown-item"
                >
                  半监督学习
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/model/use" 
                  class="dropdown-item"
                >
                  模型使用
                </router-link>
              </li>
            </ul>
          </li>
          
          <li class="nav-item dropdown">
            <a 
              class="nav-link dropdown-toggle" 
              role="button" 
              id="analysisDropdown"
              data-bs-toggle="dropdown" 
              aria-expanded="false"
            >
              <el-icon class="menu-icon"><PieChart /></el-icon>
              数据分析
            </a>
            <ul class="dropdown-menu" aria-labelledby="analysisDropdown">
              <li>
                <router-link 
                  to="/analysis/differential" 
                  class="dropdown-item"
                >
                  差异表达
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/analysis/enrichment" 
                  class="dropdown-item"
                >
                  富集分析
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/analysis/visualization" 
                  class="dropdown-item"
                >
                  可视化
                </router-link>
              </li>
            </ul>
          </li>
          
          <li class="nav-item">
            <router-link 
              to="/files" 
              class="nav-link"
              :class="{ active: $route.name === 'files' }"
            >
              <el-icon class="menu-icon"><Document /></el-icon>
              文件管理
            </router-link>
          </li>
          
          <li class="nav-item">
            <router-link 
              to="/help" 
              class="nav-link"
              :class="{ active: $route.name === 'help' }"
            >
              <el-icon class="menu-icon"><QuestionFilled /></el-icon>
              帮助
            </router-link>
          </li>
        </ul>
      </div>
      
      <!-- 用户信息和操作 -->
      <div class="user-section d-flex align-items-center gap-3">
        <!-- 系统状态指示器 -->
        <div class="status-indicators d-flex align-items-center gap-2">
          <el-tooltip 
            :content="`WebSocket: ${webSocketStatus.text}`" 
            placement="bottom"
          >
            <el-tag 
              :type="webSocketStatus.type" 
              size="small"
              effect="dark"
            >
              <el-icon><Connection /></el-icon>
            </el-tag>
          </el-tooltip>
          
          <el-tooltip 
            :content="`认证: ${authStatus.text}`" 
            placement="bottom"
          >
            <el-tag 
              :type="authStatus.type" 
              size="small"
              effect="dark"
            >
              <el-icon><User /></el-icon>
            </el-tag>
          </el-tooltip>
        </div>
        
        <!-- 用户头像和菜单 -->
        <div class="user-dropdown" v-if="userStore.userInfo">
          <el-dropdown @command="handleUserCommand">
            <div class="user-trigger d-flex align-items-center gap-2">
              <el-avatar :size="32" :src="userStore.userInfo.avatar_url">
                {{ userStore.userInfo.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username d-none d-md-inline">
                {{ userStore.userInfo.username }}
              </span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人资料
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <!-- 移动端菜单按钮 -->
        <button 
          class="navbar-toggler d-lg-none" 
          type="button" 
          data-bs-toggle="offcanvas" 
          data-bs-target="#mobileMenu"
          aria-controls="mobileMenu"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
      </div>
    </div>
    
    <!-- 移动端菜单 -->
    <div 
      class="offcanvas offcanvas-end d-lg-none" 
      tabindex="-1" 
      id="mobileMenu" 
      aria-labelledby="mobileMenuLabel"
    >
      <div class="offcanvas-header">
        <h5 class="offcanvas-title" id="mobileMenuLabel">菜单</h5>
        <button 
          type="button" 
          class="btn-close" 
          data-bs-dismiss="offcanvas" 
          aria-label="Close"
        ></button>
      </div>
      
      <div class="offcanvas-body">
        <div class="mobile-menu">
          <div class="menu-section">
            <h6 class="section-title">主要功能</h6>
            <ul class="menu-list">
              <li>
                <router-link 
                  to="/dashboard" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  <el-icon><House /></el-icon>
                  首页
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/files" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  <el-icon><Document /></el-icon>
                  文件管理
                </router-link>
              </li>
            </ul>
          </div>
          
          <div class="menu-section">
            <h6 class="section-title">数据处理</h6>
            <ul class="menu-list">
              <li>
                <router-link 
                  to="/data-process/genome" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  基因组
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/data-process/transcriptome" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  转录组
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/data-process/protein" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  蛋白质组
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/data-process/integration" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  数据整合
                </router-link>
              </li>
            </ul>
          </div>
          
          <div class="menu-section">
            <h6 class="section-title">模型训练</h6>
            <ul class="menu-list">
              <li>
                <router-link 
                  to="/model/train/supervised" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  监督学习
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/model/train/unsupervised" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  无监督学习
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/model/train/semi-supervised" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  半监督学习
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/model/use" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  模型使用
                </router-link>
              </li>
            </ul>
          </div>
          
          <div class="menu-section">
            <h6 class="section-title">数据分析</h6>
            <ul class="menu-list">
              <li>
                <router-link 
                  to="/analysis/differential" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  差异表达
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/analysis/enrichment" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  富集分析
                </router-link>
              </li>
              <li>
                <router-link 
                  to="/analysis/visualization" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  可视化
                </router-link>
              </li>
            </ul>
          </div>
          
          <div class="menu-section">
            <h6 class="section-title">其他</h6>
            <ul class="menu-list">
              <li>
                <router-link 
                  to="/help" 
                  class="menu-item"
                  @click="closeMobileMenu"
                >
                  <el-icon><QuestionFilled /></el-icon>
                  帮助
                </router-link>
              </li>
            </ul>
          </div>
          
          <!-- 移动端用户信息 -->
          <div class="mobile-user-info mt-4 pt-4 border-top" v-if="userStore.userInfo">
            <div class="user-card">
              <div class="user-avatar">
                <el-avatar :size="48" :src="userStore.userInfo.avatar_url">
                  {{ userStore.userInfo.username.charAt(0).toUpperCase() }}
                </el-avatar>
              </div>
              <div class="user-details">
                <div class="username">{{ userStore.userInfo.username }}</div>
                <div class="email">{{ userStore.userInfo.email }}</div>
              </div>
            </div>
            
            <div class="user-actions mt-3">
              <el-button 
                type="primary" 
                size="small" 
                @click="handleLogout"
                class="w-100"
              >
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useFilesStore } from '@/stores/files'
import { webSocketService } from '@/api/websocket'
import { webSocketManager } from '@/utils/websocket-manager'
import { 
  House, 
  DataAnalysis, 
  SetUp, 
  PieChart, 
  Document,
  QuestionFilled,
  Connection,
  User,
  ArrowDown,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const filesStore = useFilesStore()

// <!-- 
// 审查上下文：
// - 设计意图：使用环境变量配置Logo路径，避免硬编码外部资源URL
// - 已知局限：当前使用本地相对路径，在生产环境中需要配置CDN路径
// - 业务背景：提高应用安全性和可靠性，避免外部依赖
// - 测试重点：验证不同环境下的Logo加载是否正常
// -->
const logoPath = computed(() => {
  return import.meta.env.VITE_LOGO_PATH || '/images/logo.png'
})

// 状态计算属性
const webSocketStatus = computed(() => {
  // 使用WebSocket管理器的状态
  const managerStatus = webSocketManager.getStatus()
  if (managerStatus.isActive && managerStatus.isConnected) {
    return { text: '已连接', type: 'success' }
  } else if (managerStatus.isActive && !managerStatus.isConnected) {
    return { text: '连接中', type: 'warning' }
  } else {
    return { text: '已断开', type: 'danger' }
  }
})

const authStatus = computed(() => {
  return userStore.isAuthenticated 
    ? { text: '已认证', type: 'success' }
    : { text: '未认证', type: 'warning' }
})

const connectionStatus = computed(() => {
  const managerStatus = webSocketManager.getStatus()
  return managerStatus.isActive && managerStatus.isConnected
    ? { text: '已连接', type: 'success' }
    : { text: '未连接', type: 'danger' }
})

// 方法
function handleUserCommand(command: string) {
  switch (command) {
    case 'profile':
      // TODO: 跳转到个人资料页面
      break
    case 'settings':
      // TODO: 跳转到系统设置页面
      break
    case 'logout':
      handleLogout()
      break
  }
}

function handleLogout() {
  userStore.logout()
  // 路由跳转已在 userStore.logout() 中处理
}

function closeMobileMenu() {
  const mobileMenu = document.getElementById('mobileMenu')
  if (mobileMenu) {
    const bsOffcanvas = (window as any).bootstrap.Offcanvas.getInstance(mobileMenu)
    if (bsOffcanvas) {
      bsOffcanvas.hide()
    }
  }
}
</script>

<style scoped>
.main-menu {
  background-color: white !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1050;
  padding: 0.5rem 1rem;
}

.navbar-brand img {
  max-height: 44px;
  width: auto;
}

/* 桌面端菜单样式 */
.desktop-menu {
  flex: 1;
  justify-content: center;
}

.menu-list {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #333 !important;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  text-decoration: none;
}

.nav-link:hover,
.nav-link.active {
  color: #0d6efd !important;
  background-color: #f8f9fa;
}

.menu-icon {
  font-size: 16px;
}

.dropdown-menu {
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  margin-top: 0.5rem;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  transition: background-color 0.2s ease;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

/* 用户区域样式 */
.user-section {
  margin-left: auto;
}

.status-indicators {
  margin-right: 1rem;
}

.user-dropdown {
  cursor: pointer;
}

.user-trigger {
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.user-trigger:hover {
  background-color: #f8f9fa;
}

.username {
  font-weight: 500;
  color: #333;
}

/* 移动端菜单样式 */
.mobile-menu {
  padding: 1rem 0;
}

.menu-section {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: #333;
  text-decoration: none;
  border-radius: 6px;
  transition: background-color 0.2s ease;
  margin-bottom: 0.25rem;
}

.menu-item:hover {
  background-color: #f8f9fa;
  color: #0d6efd;
}

.menu-item.router-link-active {
  background-color: #e7f3ff;
  color: #0d6efd;
  font-weight: 500;
}

/* 移动端用户信息 */
.mobile-user-info {
  padding: 1rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-details {
  flex: 1;
  overflow: hidden;
}

.user-details .username {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.25rem;
}

.user-details .email {
  font-size: 0.875rem;
  color: #6c757d;
}

/* Offcanvas 样式 */
.offcanvas {
  background-color: white;
  width: 280px !important;
}

.offcanvas-header {
  border-bottom: 1px solid #e9ecef;
  padding: 1rem 1.5rem;
}

.offcanvas-title {
  font-weight: 600;
  color: #333;
}

.offcanvas-body {
  padding: 0;
}

/* 响应式调整 */
@media (max-width: 991.98px) {
  .main-menu {
    padding: 0.5rem 1rem;
  }
  
  .status-indicators {
    display: none !important;
  }
}

@media (max-width: 767.98px) {
  .username {
    display: none !important;
  }
  
  .nav-link span:not(.menu-icon) {
    display: none;
  }
  
  .menu-list {
    gap: 0.5rem;
  }
  
  .nav-link {
    padding: 0.5rem;
    font-size: 0.875rem;
  }
}
</style>