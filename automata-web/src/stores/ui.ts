import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface UIState {
  isLoading: boolean
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  notifications: Notification[]
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  timestamp: number
}

export const useUIStore = defineStore('ui', () => {
  // 状态
  const isLoading = ref<boolean>(false)
  const sidebarCollapsed = ref<boolean>(false)
  const theme = ref<'light' | 'dark'>('light')
  const notifications = ref<Notification[]>([])
  
  // 计算属性
  const activeNotifications = computed(() => 
    notifications.value.slice(-5) // 只显示最近5条通知
  )
  
  // Actions
  function setLoading(status: boolean) {
    isLoading.value = status
  }
  
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  function setSidebarCollapsed(collapsed: boolean) {
    sidebarCollapsed.value = collapsed
  }
  
  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
  }
  
  function addNotification(notification: Omit<Notification, 'id' | 'timestamp'>) {
    const newNotification: Notification = {
      id: generateId(),
      timestamp: Date.now(),
      ...notification
    }
    
    notifications.value.push(newNotification)
    
    // 自动移除通知
    if (notification.duration !== 0) {
      const duration = notification.duration || 5000
      setTimeout(() => {
        removeNotification(newNotification.id)
      }, duration)
    }
  }
  
  function removeNotification(id: string) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  function clearNotifications() {
    notifications.value = []
  }
  
  function showSuccess(title: string, message: string, duration?: number) {
    addNotification({
      type: 'success',
      title,
      message,
      duration
    })
  }
  
  function showError(title: string, message: string, duration?: number) {
    addNotification({
      type: 'error',
      title,
      message,
      duration
    })
  }
  
  function showWarning(title: string, message: string, duration?: number) {
    addNotification({
      type: 'warning',
      title,
      message,
      duration
    })
  }
  
  function showInfo(title: string, message: string, duration?: number) {
    addNotification({
      type: 'info',
      title,
      message,
      duration
    })
  }
  
  function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      theme.value = savedTheme
    } else {
      // 检测系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      theme.value = prefersDark ? 'dark' : 'light'
    }
  }
  
  function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }
  
  return {
    // 状态
    isLoading,
    sidebarCollapsed,
    theme,
    notifications,
    
    // 计算属性
    activeNotifications,
    
    // Actions
    setLoading,
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    initializeTheme
  }
})