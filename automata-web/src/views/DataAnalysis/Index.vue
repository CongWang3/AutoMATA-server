<template>
  <div class="data-analysis-index">
    <div class="page-header">
      <h1>数据分析</h1>
      <p>选择一个分析工具开始您的数据分析之旅</p>
    </div>
    
    <!-- 可视化分析 -->
    <h2 class="section-title">可视化分析</h2>
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in visualizationTools" :key="item.path">
        <el-card shadow="hover" class="tool-card" @click="$router.push(item.path)">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 富集与网络分析 -->
    <h2 class="section-title">富集与网络分析</h2>
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in enrichmentTools" :key="item.path">
        <el-card shadow="hover" class="tool-card" @click="$router.push(item.path)">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 综合分析 -->
    <h2 class="section-title">综合分析</h2>
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="tool-card" @click="$router.push('/data-analysis/comprehensive')">
          <h3>综合差异表达分析</h3>
          <p>一键完成差异分析、火山图、聚类热图、GO/KEGG富集分析</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
const visualizationTools = [
  {
    path: '/data-analysis/pca',
    title: 'PCA分析',
    description: '主成分分析，用于样本间差异和聚类的可视化'
  },
  {
    path: '/data-analysis/heatmap',
    title: '相关性热图',
    description: '展示样本或基因之间的相关性矩阵'
  },
  {
    path: '/data-analysis/volcano',
    title: '火山图',
    description: '展示差异表达基因的统计显著性和倍数变化'
  },
  {
    path: '/data-analysis/venn',
    title: '韦恩图',
    description: '展示多个基因集之间的交集和并集关系'
  },
  {
    path: '/data-analysis/cluster',
    title: '差异基因聚类热图',
    description: '对差异表达基因进行层次聚类分析'
  },
  {
    path: '/data-analysis/dumbbell',
    title: '哑铃图',
    description: '展示基因在不同条件下的表达变化'
  },
  {
    path: '/data-analysis/dumbbell-bar',
    title: '哑铃柱状图',
    description: '结合哑铃图和柱状图展示表达变化'
  }
]

const enrichmentTools = [
  {
    path: '/data-analysis/go',
    title: 'GO富集分析',
    description: '基因本体论富集分析，包括BP、MF、CC三个类别'
  },
  {
    path: '/data-analysis/kegg',
    title: 'KEGG富集分析',
    description: 'KEGG通路富集分析，揭示基因参与的生物学通路'
  },
  {
    path: '/data-analysis/ppi',
    title: 'PPI网络分析',
    description: '蛋白质-蛋白质相互作用网络构建与可视化'
  }
]
</script>

<style scoped>
.data-analysis-index {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 12px;
}

.page-header p {
  font-size: 16px;
  color: #909399;
}

.section-title {
  font-size: 20px;
  color: #303133;
  margin: 32px 0 16px;
  padding-left: 12px;
  border-left: 4px solid #409eff;
}

.tool-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 140px;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.tool-card h3 {
  font-size: 16px;
  color: #303133;
  margin: 0 0 12px;
}

.tool-card p {
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
  margin: 0;
}
</style>
