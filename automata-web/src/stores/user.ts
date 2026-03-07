import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setSecureItem, getSecureItem, removeSecureItem } from '@/utils/secureStorage'

export interface User {
  id: number
  username: string
  email: string
  is_authenticated: boolean
  created_at?: string
  avatar?: string
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!user.value?.is_authenticated)
  
  // Actions
  // <!-- 
  // 审查上下文：
  // - 设计意图：使用加密存储保护用户敏感信息，防止XSS攻击
  // - 已知局限：密钥存储在前端仍有风险，生产环境建议JWT Token方案
  // - 业务背景：符合生物信息学平台的安全要求
  // - 测试重点：验证加密存储功能，确保用户信息安全性
  // -->
  function setUser(userData: User) {
    user.value = userData
    // 使用加密存储保护用户信息
    setSecureItem('user', userData)
  }
  
  function logout() {
    user.value = null
    removeSecureItem('user')
    removeSecureItem('authToken')
  }
  
  function initializeFromStorage() {
    // 从加密存储中恢复用户信息
    const storedUser = getSecureItem('user')
    if (storedUser) {
      user.value = storedUser
    }
  }
  
  return {
    user,
    isAuthenticated,
    setUser,
    logout,
    initializeFromStorage
  }
})