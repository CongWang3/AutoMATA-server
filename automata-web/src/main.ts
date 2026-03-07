import './assets/main.css'
import 'bootstrap/dist/css/bootstrap.min.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'

import App from './App.vue'
import router from './router'
import { webSocketManager } from './utils/websocket-manager'

const app = createApp(App)
const pinia = createPinia()

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册Iconify组件
app.component('IconifyIcon', Icon)

// 按需引入Element Plus组件，解决el-notification警告
import { ElNotification } from 'element-plus'
app.config.globalProperties.$notify = ElNotification

app.use(router)
app.use(pinia)
app.use(ElementPlus)

// 初始化WebSocket管理器
webSocketManager.init(router)

app.mount('#app')
