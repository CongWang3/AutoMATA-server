<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h2 class="login-title">AutoMATA</h2>
          <p class="login-subtitle">Bioinformatics data analysis platform</p>
        </div>

        <div class="login-form">
          <el-tabs v-model="activeTab" class="login-tabs">
            <!-- 登录标签页 -->
            <el-tab-pane label="Sign in" name="login">
              <el-form
                ref="loginFormRef"
                :model="loginForm"
                :rules="loginRules"
                label-position="top"
                @submit.prevent="handleLogin"
              >
                <el-form-item label="Username or email" prop="username">
                  <el-input
                    v-model="loginForm.username"
                    placeholder="Enter username or email"
                    prefix-icon="User"
                    size="large"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="Password" prop="password">
                  <el-input
                    v-model="loginForm.password"
                    type="password"
                    placeholder="Enter password"
                    prefix-icon="Lock"
                    size="large"
                    show-password
                    @keyup.enter="handleLogin"
                  />
                </el-form-item>

                <el-form-item>
                  <el-checkbox v-model="rememberMe">Remember me</el-checkbox>
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    size="large"
                    :loading="userStore.loading"
                    class="login-button"
                    @click="handleLogin"
                  >
                    {{ userStore.loading ? 'Signing in…' : 'Sign in' }}
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 注册标签页 -->
            <el-tab-pane label="Register" name="register">
              <el-form
                ref="registerFormRef"
                :model="registerForm"
                :rules="registerRules"
                label-position="top"
                @submit.prevent="handleRegister"
              >
                <el-form-item label="Username" prop="username">
                  <el-input
                    v-model="registerForm.username"
                    placeholder="Username (5–50 characters)"
                    prefix-icon="User"
                    size="large"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="Email" prop="email">
                  <el-input
                    v-model="registerForm.email"
                    placeholder="Email address"
                    prefix-icon="Message"
                    size="large"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="Password" prop="password">
                  <el-input
                    v-model="registerForm.password"
                    type="password"
                    placeholder="At least 8 characters with upper, lower, and digits"
                    prefix-icon="Lock"
                    size="large"
                    show-password
                  />
                </el-form-item>

                <el-form-item label="Confirm password" prop="confirmPassword">
                  <el-input
                    v-model="registerForm.confirmPassword"
                    type="password"
                    placeholder="Re-enter password"
                    prefix-icon="Lock"
                    size="large"
                    show-password
                    @keyup.enter="handleRegister"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="success"
                    size="large"
                    :loading="userStore.loading"
                    class="register-button"
                    @click="handleRegister"
                  >
                    {{ userStore.loading ? 'Registering…' : 'Register' }}
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 错误提示 -->
        <div v-if="userStore.error" class="error-message">
          <el-alert
            :title="userStore.error"
            type="error"
            show-icon
            closable
            @close="userStore.clearError()"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// <!-- 
// 审查上下文：
// - 设计意图：提供用户友好的登录注册界面，集成表单验证和错误处理
// - 已知局限：密码强度验证规则相对简单，可根据安全要求增强
// - 业务背景：作为整个平台的入口，需要提供良好的用户体验
// - 测试重点：表单验证、认证流程、错误处理、响应式布局
// -->
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

// 状态
const activeTab = ref<'login' | 'register'>('login')
const rememberMe = ref<boolean>(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 登录表单验证规则
const loginRules = reactive<FormRules>({
  username: [
    { required: true, message: 'Please enter username or email', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ]
})

// 注册表单验证规则
const registerRules = reactive<FormRules>({
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 5, max: 50, message: 'Username must be 5–50 characters', trigger: 'blur' }
  ],
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { 
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,
      message: 'At least 8 characters with upper, lower, and digits',
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm password', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('Passwords do not match'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

/**
 * 处理登录
 */
async function handleLogin() {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    
    console.log('🔍 开始真实登录流程...')
    
    // 使用真实的认证服务
    await userStore.login(loginForm.username, loginForm.password)
    
    console.log('✅ 真实登录成功')
    
    // 调试：检查存储状态
    console.log('🔍 登录后存储状态检查:')
    console.log('- access_token:', localStorage.getItem('access_token'))
    console.log('- token_expiry:', localStorage.getItem('token_expiry'))
    console.log('- user_info:', localStorage.getItem('user_info'))
    console.log('- isAuthenticated computed:', userStore.isAuthenticated)
    console.log('- userInfo exists:', !!userStore.userInfo)
    
    // 处理记住我功能
    if (rememberMe.value) {
      localStorage.setItem('remember_me', 'true')
    } else {
      localStorage.removeItem('remember_me')
    }
    
    ElMessage.success('Signed in successfully')
    
    // 确保状态完全更新后再跳转
    await nextTick()
    console.log('🚀 准备跳转到 /dashboard')
    router.push('/dashboard')
    
  } catch (error) {
    // 错误已在store中处理
    console.error('登录失败:', error)
  }
}

/**
 * 处理注册
 */
async function handleRegister() {
  if (!registerFormRef.value) return
  
  try {
    await registerFormRef.value.validate()
    
    await userStore.register(
      registerForm.username,
      registerForm.email,
      registerForm.password
    )
    
    ElMessage.success('Registered successfully. You are now signed in.')
    
    // 确保状态完全更新后再跳转
    await nextTick()
    router.push('/dashboard')
  } catch (error) {
    // 错误已在store中处理
    console.error('注册失败:', error)
  }
}

// 页面加载时检查是否已登录
onMounted(() => {
  if (userStore.isAuthenticated) {
    router.push('/dashboard')
  }
  
  // 恢复记住我状态
  rememberMe.value = localStorage.getItem('remember_me') === 'true'
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 450px;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.login-header {
  text-align: center;
  padding: 40px 30px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.login-form {
  padding: 30px;
}

.login-tabs {
  border: none;
}

.login-tabs :deep(.el-tabs__nav-wrap)::after {
  display: none;
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
  padding: 0 20px;
}

.login-button,
.register-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}

.error-message {
  padding: 0 30px 30px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-page {
    padding: 10px;
  }
  
  .login-header {
    padding: 30px 20px 15px;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  .login-form {
    padding: 20px;
  }
  
  .error-message {
    padding: 0 20px 20px;
  }
}
</style>