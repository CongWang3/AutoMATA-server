<template>
  <div class="data-analysis-index">
    <div class="page-header">
      <h1>Data Analysis</h1>
      <p>Select an analysis tool to start your data analysis journey</p>
    </div>

    <el-row :gutter="20">
      <el-col
        :xs="24"
        :sm="12"
        :md="8"
        :lg="8"
        :xl="8"
        v-for="item in allAnalysisTools"
        :key="item.path"
      >
        <el-card shadow="hover" class="tool-card" @click="$router.push(item.path)">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
const visualizationTools = [
  {
    path: '/data-analysis/pca',
    title: 'Principal Component Analysis',
    description: 'PCA can assess inter-group differences and intra-group sample duplication'
  },
  {
    path: '/data-analysis/heatmap',
    title: 'Correlation Heatmap',
    description: 'Correlation analysis mainly focuses on sample differences between groups and sample duplication within groups'
  },
  {
    path: '/data-analysis/volcano',
    title: 'Volcano Plot with GSEA',
    description: 'Volcano plot can quickly and intuitively identify genes with statistically significant multiplicative differences'
  },
  {
    path: '/data-analysis/venn',
    title: 'Venn Plot',
    description: 'Venn Plot demonstrates the intersecting and non-intersecting parts of the data, often used in genetic screening'
  },
  {
    path: '/data-analysis/cluster',
    title: 'Differential Gene Cluster Heatmap',
    description: 'Expression of differential genes in different samples'
  }
]

const dumbbellTool = {
  path: '/data-analysis/dumbbell-bar',
  title: 'Dumbbell with Bar Plot',
  description: 'Dumbbell with Bar Plot can clearly see the differences between data'
}

const enrichmentTools = [
  {
    path: '/data-analysis/go',
    title: 'GO Enrichment',
    description: 'GO Enrichment is used to determine the enrichment of a set list of genes in gene ontology'
  },
  {
    path: '/data-analysis/kegg',
    title: 'KEGG Enrichment',
    description: 'KEGG Enrichment annotates genes for pathways and analyses the major metabolic and signal transduction pathways'
  },
  {
    path: '/data-analysis/ppi',
    title: 'PPI Network',
    description: 'Protein-Protein Interaction Network is used to visualize functional relationships and interactions between proteins in a cellular context'
  }
]

const comprehensiveTool = {
  path: '/data-analysis/comprehensive',
  title: 'Comprehensive Differential Expression Analysis',
  description:
    'One-click workflow for differential expression, generate PCA plot, volcano plot, cluster heatmap, and GO/KEGG enrichment plots'
}

/** 顺序：左上 Comprehensive；其余按原可视化→富集顺延；左下角（末格）Dumbbell */
const allAnalysisTools = [
  comprehensiveTool,
  ...visualizationTools,
  ...enrichmentTools,
  dumbbellTool
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
