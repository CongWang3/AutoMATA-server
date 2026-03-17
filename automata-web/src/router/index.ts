import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { AuthService } from '@/api'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/files',
      name: 'files',
      component: () => import('../views/Files.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue')
    },
    // 数据处理相关路由
    {
      path: '/data-process/genome',
      name: 'genome',
      component: () => import('../views/DataProcess/Genome.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/data-process/transcriptome',
      name: 'transcriptome',
      component: () => import('../views/DataProcess/Transcriptome.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/data-process/protein',
      name: 'protein',
      component: () => import('../views/DataProcess/Protein.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/data-process/integration',
      name: 'integration',
      component: () => import('../views/DataProcess/Integration.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/data-process/pvalue-integration',
      name: 'pvalue-integration',
      component: () => import('../views/DataProcess/PvalueIntegration.vue'),
      meta: { requiresAuth: true }
    },
    // 模型相关路由
    {
      path: '/model/train/supervised',
      name: 'train-supervised',
      component: () => import('../views/ModelTrain/Supervised.vue')
    },
    {
      path: '/model/train/unsupervised',
      name: 'train-unsupervised',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/model/train/semi-supervised',
      name: 'train-semi-supervised',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/model/train/dashboard',
      name: 'train-dashboard',
      component: () => import('../components/TrainingDashboard.vue')
    },
    {
      path: '/model/use',
      name: 'model-use',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/data-analysis',
      name: 'data-analysis',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/analysis/differential',
      name: 'analysis-differential',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/analysis/enrichment',
      name: 'analysis-enrichment',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/analysis/visualization',
      name: 'analysis-visualization',
      component: () => import('../views/AboutView.vue')
    },
    // 帮助页面路由
    {
      path: '/help',
      name: 'help',
      component: () => import('../views/AboutView.vue')
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 开发环境下减少日志输出
  if (import.meta.env.DEV) {
    console.log('🚦 路由守卫触发:', { from: from.path, to: to.path })
  }
  
  const userStore = useUserStore()
  
  // 开发环境下减少认证状态日志
  if (import.meta.env.DEV) {
    console.log('👤 当前认证状态:', {
      isAuthenticated: userStore.isAuthenticated,
      hasUserInfo: !!userStore.userInfo,
      username: userStore.username
    })
    
    // 调试：检查底层认证状态
    console.log('🔍 底层认证检查:')
    console.log('- AuthService.isAuthenticated():', AuthService.isAuthenticated())
    console.log('- userInfo exists:', !!userStore.userInfo)
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    console.log('🔐 需要认证的路由:', to.path)
    
    // 检查用户是否已认证
    if (!userStore.isAuthenticated) {
      console.log('❌ 用户未认证，尝试从存储恢复...')
      // 尝试从存储中恢复认证状态
      userStore.initializeFromStorage()
      
      console.log('🔄 恢复后状态:')
      console.log('- isAuthenticated:', userStore.isAuthenticated)
      console.log('- userInfo:', userStore.userInfo)
      
      // 如果仍然未认证，重定向到登录页
      if (!userStore.isAuthenticated) {
        console.log('🚫 未认证，重定向到登录页')
        next('/login')
        return
      }
    }
    
    // 如果已认证但用户信息不存在，尝试获取用户信息
    if (!userStore.userInfo) {
      console.log('ℹ️ 用户已认证但缺少用户信息，尝试获取...')
      try {
        await userStore.fetchUserInfo()
        console.log('✅ 用户信息获取成功')
      } catch (error) {
        console.error('❌ 获取用户信息失败:', error)
        userStore.logout()
        next('/login')
        return
      }
    }
  }
  
  // 检查是否需要游客访问（未登录状态）
  if (to.meta.requiresGuest && userStore.isAuthenticated) {
    console.log('🏠 已认证用户访问游客页面，重定向到仪表板')
    next('/dashboard')
    return
  }
  
  console.log('✅ 路由守卫通过，允许访问:', to.path)
  next()
})

export default router