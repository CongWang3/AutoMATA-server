import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Index.vue')
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
      path: '/genome',
      name: 'genome',
      component: () => import('../views/AboutView.vue') // 临时使用 AboutView，后续替换为实际组件
    },
    {
      path: '/transcriptome',
      name: 'transcriptome',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/protein',
      name: 'protein',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/integration',
      name: 'integration',
      component: () => import('../views/AboutView.vue')
    },
    // 模型相关路由
    {
      path: '/model/train/supervised',
      name: 'train-supervised',
      component: () => import('../views/model/components/AutoMATATrainingSupervised.vue')
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
    // 数据分析路由
    {
      path: '/analysis',
      name: 'analysis',
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

export default router