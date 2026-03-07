<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'
import { useUIStore } from './stores/ui'
import AppHeader from './components/common/AppHeader.vue'
import AppFooter from './components/common/AppFooter.vue'
import AppSidebar from './components/common/AppSidebar.vue'
import LoadingSpinner from './components/common/LoadingSpinner.vue'
import ErrorBoundary from './components/common/ErrorBoundary.vue'
import { RouterView } from 'vue-router'

const userStore = useUserStore()
const uiStore = useUIStore()

// 初始化应用
onMounted(() => {
  // 从localStorage恢复用户状态
  userStore.initializeFromStorage()
  
  // 初始化主题
  uiStore.initializeTheme()
  
  // 设置全局loading状态监听
  // 这里可以根据需要添加全局loading控制逻辑
})
</script>

<template>
  <div class="app-container" :class="[`theme-${uiStore.theme}`]">
    <!-- 全局loading遮罩 -->
    <LoadingSpinner 
      v-if="uiStore.isLoading" 
      :fullscreen="true" 
      text="加载中..."
    />
    
    <!-- 侧边栏 -->
    <AppSidebar />
    
    <!-- 主内容区域 -->
    <div class="main-wrapper">
      <!-- 顶部导航 -->
      <AppHeader />
      
      <!-- 页面内容 -->
      <main class="main-content">
        <ErrorBoundary>
          <RouterView />
        </ErrorBoundary>
      </main>
      
      <!-- 底部 -->
      <AppFooter />
    </div>
    
    <!-- 全局通知 -->
    <div class="notifications-container">
      <transition-group name="notification" tag="div">
        <el-notification
          v-for="notification in uiStore.activeNotifications"
          :key="notification.id"
          :title="notification.title"
          :message="notification.message"
          :type="notification.type"
          :duration="notification.duration"
          @close="uiStore.removeNotification(notification.id)"
        />
      </transition-group>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-content {
  flex: 1;
  padding: 20px;
  margin-top: 80px; /* 为固定header留出空间 */
  overflow-y: auto;
}

.notifications-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  width: 320px;
}

/* 通知动画 */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* 主题样式 */
.theme-light {
  --bg-color: #ffffff;
  --text-color: #303133;
  --border-color: #e4e7ed;
}

.theme-dark {
  --bg-color: #1d1e1f;
  --text-color: #e4e7ed;
  --border-color: #4c4d4f;
}

/* 响应式调整 */
@media (max-width: 992px) {
  .app-container {
    flex-direction: column;
  }
  
  .main-content {
    margin-top: 70px;
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .main-content {
    margin-top: 60px;
    padding: 12px;
  }
  
  .notifications-container {
    width: 90%;
    right: 5%;
  }
}
</style>
