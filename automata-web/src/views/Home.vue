<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="container">
        <div class="hero-content">
          <h1 class="hero-title">AutoMATA</h1>
          <h2 class="hero-subtitle">
            a deep learning-enhanced bioinformatics platform
          </h2>
          <p class="hero-description">
            for multi-omics data processing, exploration and modelling
          </p>
          <div class="hero-actions">
            <el-button 
              type="primary" 
              size="large" 
              @click="goToTraining"
            >
              开始训练和分析
            </el-button>
            <el-button 
              size="large" 
              @click="viewDemo"
            >
              查看演示
            </el-button>
          </div>
        </div>
        <div class="hero-image">
          <img 
            src="/images/background.png" 
            alt="AutoMATA Platform" 
            class="img-fluid"
          >
        </div>
      </div>
    </section>

    <!-- Services Section -->
    <section class="services-section">
      <div class="container">
        <div class="section-header text-center">
          <h2 class="section-title">我们提供</h2>
        </div>
        
        <div class="services-grid">
          <div class="service-card" @click="goToDataProcess">
            <div class="service-icon">
              <el-icon size="48" color="#409eff"><DataAnalysis /></el-icon>
            </div>
            <h3 class="service-title">数据处理</h3>
            <p class="service-description">
              基因、mRNA、蛋白质表达数据的数据处理功能
            </p>
          </div>
          
          <div class="service-card" @click="goToModelTraining">
            <div class="service-icon">
              <el-icon size="48" color="#67c23a"><SetUp /></el-icon>
            </div>
            <h3 class="service-title">模型训练</h3>
            <p class="service-description">
              深度学习模型的训练和应用
            </p>
          </div>
          
          <div class="service-card" @click="goToDataAnalysis">
            <div class="service-icon">
              <el-icon size="48" color="#e6a23c"><PieChart /></el-icon>
            </div>
            <h3 class="service-title">数据分析</h3>
            <p class="service-description">
              多种数据可视化和分析功能
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">1000+</div>
            <div class="stat-label">已完成任务</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">500+</div>
            <div class="stat-label">活跃用户</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">50+</div>
            <div class="stat-label">支持模型</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">99.9%</div>
            <div class="stat-label">系统可用性</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Recent Tasks Section -->
    <section class="recent-tasks-section" v-if="recentTasks.length > 0">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">最近任务</h2>
          <el-button link @click="viewAllTasks">查看全部</el-button>
        </div>
        
        <JobList 
          :jobs="recentTasks" 
          :show-filters="false"
          :show-pagination="false"
          @view="viewTaskDetail"
          @delete="deleteTask"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { useUIStore } from '@/stores/ui'
import JobList from '@/components/Job/JobList.vue'
import { 
  DataAnalysis, 
  SetUp, 
  PieChart 
} from '@element-plus/icons-vue'

const router = useRouter()
const trainingStore = useTrainingStore()
const uiStore = useUIStore()

// 状态
const recentTasks = ref<any[]>([])

// 方法
function goToTraining() {
  router.push('/model/train/supervised')
}

function viewDemo() {
  uiStore.showInfo('演示功能', '演示功能正在开发中')
}

function goToDataProcess() {
  router.push('/data-process/genome')
}

function goToModelTraining() {
  router.push('/model/train/supervised')
}

function goToDataAnalysis() {
  router.push('/data-analysis')
}

function viewAllTasks() {
  router.push('/model/train/dashboard')
}

function viewTaskDetail(task: any) {
  router.push(`/model/task/${task.id}`)
}

function deleteTask(task: any) {
  // 实现删除逻辑
  console.log('Deleting task:', task)
}

// 生命周期
onMounted(async () => {
  try {
    // 模拟获取最近任务数据
    recentTasks.value = [
      {
        id: 1,
        task_name: '基因表达分析_MLP_20240306',
        model_type: 'mlp',
        status: 'completed',
        progress: 100,
        created_at: '2024-03-06T10:30:00Z'
      },
      {
        id: 2,
        task_name: '蛋白质相互作用预测_CNN_20240306',
        model_type: 'cnn',
        status: 'running',
        progress: 65,
        created_at: '2024-03-06T09:15:00Z'
      },
      {
        id: 3,
        task_name: '转录组差异分析_LSTM_20240305',
        model_type: 'lstm',
        status: 'failed',
        progress: 30,
        created_at: '2024-03-05T14:20:00Z'
      }
    ]
  } catch (error) {
    console.error('Failed to load recent tasks:', error)
  }
})
</script>

<style scoped>
.home-page {
  width: 100%;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 80px 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.hero-content {
  text-align: center;
  margin-bottom: 40px;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 1rem;
  letter-spacing: -1px;
}

.hero-subtitle {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 1rem;
  opacity: 0.9;
}

.hero-description {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.8;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 2rem;
}

.hero-image {
  text-align: center;
}

.hero-image img {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* Services Section */
.services-section {
  padding: 80px 0;
  background: white;
}

.section-header {
  margin-bottom: 50px;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
}

.service-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 40px 30px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.service-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.service-icon {
  margin-bottom: 20px;
}

.service-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 15px;
  color: #303133;
}

.service-description {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

/* Stats Section */
.stats-section {
  background: #f8f9fa;
  padding: 60px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 30px;
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-number {
  font-size: 3rem;
  font-weight: 700;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 1.1rem;
  color: #606266;
  font-weight: 500;
}

/* Recent Tasks Section */
.recent-tasks-section {
  padding: 80px 0;
  background: white;
}

.recent-tasks-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

/* 响应式调整 */
@media (max-width: 992px) {
  .hero-title {
    font-size: 2.8rem;
  }
  
  .hero-subtitle {
    font-size: 1.5rem;
  }
  
  .hero-description {
    font-size: 1.1rem;
  }
  
  .services-grid {
    grid-template-columns: 1fr;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 60px 0;
  }
  
  .hero-title {
    font-size: 2.2rem;
  }
  
  .hero-subtitle {
    font-size: 1.3rem;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .services-section,
  .recent-tasks-section {
    padding: 60px 0;
  }
  
  .container {
    padding: 0 16px;
  }
}
</style>