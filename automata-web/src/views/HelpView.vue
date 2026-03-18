<template>
  <div class="help-page">
    <!-- 页面标题 -->
    <div class="help-header">
      <h1 class="help-title">帮助中心 / Help Center</h1>
      <p class="help-subtitle">AutoMATA 平台使用指南</p>
    </div>

    <!-- 帮助内容 -->
    <div class="help-content">
      <el-collapse v-model="activeNames" accordion>
        <!-- 1. Data Process -->
        <el-collapse-item name="data-process">
          <template #title>
            <div class="collapse-title">
              <el-icon><DataAnalysis /></el-icon>
              <span>1. 数据处理 / Data Process</span>
            </div>
          </template>
          <div class="module-content">
            <!-- Genome -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="primary" size="small">Genome</el-tag>
                基因组数据处理
              </h4>
              <p class="module-desc">
                This platform provides conversion of gene expression data from 
                <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i>, 
                <i>Drosophila Melanogaster</i> and <i>Arabidopsis Thaliana</i> 
                in RPKM, TPM, ReadCounts, FPKM and RPM formats to log2(TPM+1) format.
              </p>
              <p class="module-desc">
                Users can select different gene nomenclatures as GeneID, EnsemblID and Symbol, 
                and the generated result file provides the Symbol data of the genes corresponding 
                to different nomenclatures. Click "Example" button to download the example data 
                of human gene expression. Missing values were filled with zeros.
              </p>
            </div>

            <!-- Transcriptome -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="success" size="small">Transcriptome</el-tag>
                转录组数据处理
              </h4>
              <p class="module-desc">
                This platform provides conversion of mRNA expression data from 
                <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i> and 
                <i>Drosophila Melanogaster</i> in RPKM, TPM, ReadCounts, FPKM and RPM 
                formats to log2(TPM+1) format.
              </p>
              <p class="module-desc">
                Users can select different nomenclatures for mRNA, which are 
                Refseq Accession, Transcript name and EnsemblID. Transcript names 
                corresponding to different nomenclatures are provided in the generated 
                result file. Click "Example" button to download the example data. 
                Missing values were filled with zeros.
              </p>
            </div>

            <!-- Protein -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="warning" size="small">Protein</el-tag>
                蛋白质数据处理
              </h4>
              <p class="module-desc">
                This platform provides conversion of protein expression data from 
                <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i> and 
                <i>Drosophila Melanogaster</i> in expression value formats to 
                log2(expression value) format.
              </p>
              <p class="module-desc">
                Users can select different nomenclatures for protein, which are 
                UniProt Entry, Refseq Accession, AlphaFoldDB ID, and EnsemblID. 
                Entry names corresponding to different nomenclatures are provided 
                in the generated result file. Click "Example" button to download 
                the example data. Missing values were filled with zeros.
              </p>
            </div>
          </div>
        </el-collapse-item>

        <!-- 2. Model -->
        <el-collapse-item name="model">
          <template #title>
            <div class="collapse-title">
              <el-icon><SetUp /></el-icon>
              <span>2. 模型 / Model</span>
            </div>
          </template>
          <div class="module-content">
            <!-- Supervised -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="primary" size="small">Train > Supervised</el-tag>
                监督学习训练
              </h4>
              <p class="module-desc">
                This platform provides training model function, which including model selection, 
                hyperparameter settings (EarlyStopping, Epochs, Learning Rate, Batch Size, 
                Loss Function, Optimizer, Random Seed, and Label number for multi-class task) 
                and training methods (validation set, StratifiedKFold, or train-validation-test split). 
                AutoMATA will removes samples with missing values.
              </p>
              <div class="output-info">
                <p><strong>Output files:</strong></p>
                <ul>
                  <li><code>model.pth</code> - the trained model</li>
                  <li><code>terminal.log</code> - training log with loss and accuracy for each epoch</li>
                  <li><code>figure.png</code> - acc-loss plot during training</li>
                  <li><code>test_result.txt</code> - metrics obtained using testing set</li>
                </ul>
              </div>
            </div>

            <!-- Unsupervised -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="success" size="small">Train > Unsupervised</el-tag>
                无监督学习训练
              </h4>
              <p class="module-desc">
                This platform provides training model function for unsupervised tasks, 
                including model selection, hyperparameter settings (EarlyStopping, Epochs, 
                Learning Rate, Batch Size, Loss Function, Optimizer, and Random Seed).
              </p>
              <el-alert type="info" :closable="false" show-icon>
                <strong>Note:</strong> All sets don't need label and sample columns.
              </el-alert>
              <div class="output-info">
                <p><strong>Output files:</strong></p>
                <ul>
                  <li><code>model.pth</code> - the trained model</li>
                  <li><code>scaler.pkl</code> - the scaler</li>
                  <li><code>terminal.log</code> - training log</li>
                  <li><code>test_result.png</code> - metrics plot</li>
                  <li><code>test_result.json</code> - result metrics</li>
                </ul>
              </div>
            </div>

            <!-- Semi-supervised -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="warning" size="small">Train > Semi-supervised</el-tag>
                半监督学习训练
              </h4>
              <p class="module-desc">
                This platform provides training model function for semi-supervised tasks, 
                including model selection, hyperparameter settings (EarlyStopping, Epochs, 
                Learning Rate, Batch Size, Loss Function, Optimizer, Random Seed, and 
                loss weight parameters).
              </p>
              <el-alert type="info" :closable="false" show-icon>
                <strong>Note:</strong> Validation and testing set must have label for each sample. 
                Training set could contain 'Unknown' label for samples with no label.
              </el-alert>
            </div>

            <!-- Model Use -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="danger" size="small">Use</el-tag>
                模型使用
              </h4>
              <p class="module-desc">
                Users can upload trained model or their own trained model 
                (<strong>NOTE: the model must be a pth file saved using torch</strong>), 
                and upload the test set (<strong>NOTE: the feature dimension of the testing set 
                must be the same as that of the training set used to train the model</strong>).
              </p>
              <div class="output-info">
                <p><strong>Output files:</strong></p>
                <ul>
                  <li><code>test_metrics_result.txt</code> - test metrics results</li>
                  <li><code>test_prediction.txt</code> - sample prediction with probability values</li>
                </ul>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 3. Data Analyse -->
        <el-collapse-item name="data-analyse">
          <template #title>
            <div class="collapse-title">
              <el-icon><PieChart /></el-icon>
              <span>3. 数据分析 / Data Analyse</span>
            </div>
          </template>
          <div class="module-content">
            <el-alert type="info" :closable="false" show-icon class="mb-4">
              Example data are provided for each analysis method. 
              Try to keep the names of the data columns the same as the example data columns, 
              as this will ensure smooth data analysis.
            </el-alert>

            <!-- All Analysis Flow -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="primary" size="small">All Analysis Flow</el-tag>
                综合分析流程
              </h4>
              <p class="module-desc">
                This function provides differential expressed analysis to ReadCounts and FPKM, 
                which use the DESeq2 and limma packages respectively. 
                Automatically remove genes with low expression levels. Use k-NN to impute missing values.
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Expression Data">
                    The first column is row names, the first row is column names.
                  </el-descriptions-item>
                  <el-descriptions-item label="Sample Information">
                    Keep the row names in the group file same as the column names in expression file. 
                    The Group column value must be 'Control' or 'Treatment'.
                  </el-descriptions-item>
                  <el-descriptions-item label="log2(FC) threshold">
                    Genes with |log2(FC)| > threshold were screened as significant differential genes.
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    Volcano plot, differential gene cluster heatmap, all significantly up/down/non-regulated DEGs.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- Correlation Heatmap -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Correlation Heatmap</el-tag>
                相关性热图
              </h4>
              <p class="module-desc">
                The first row of input data file is the column name. The separator is '\t'.
              </p>
            </div>

            <!-- PCA -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Principal Component Analysis</el-tag>
                PCA分析
              </h4>
              <p class="module-desc">
                The first column of the data is the group information. The separator is '\t'.
                Options include boundary plot and PERMANOVA analysis.
              </p>
            </div>

            <!-- Volcano Plot with GSEA -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Volcano Plot with GSEA</el-tag>
                火山图与GSEA分析
              </h4>
              <p class="module-desc">
                Make sure the column names of the dataset are gene, logFC, padj. The separator is '\t'.
                GSEA analysis requires GMT file upload.
              </p>
            </div>

            <!-- VENN Analysis -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">VENN Analysis</el-tag>
                韦恩图分析
              </h4>
              <p class="module-desc">
                The first row is the column names, and each column is the information for each group. 
                The separator is '\t'.
              </p>
            </div>

            <!-- Differential Gene Cluster -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Differential Gene Cluster Analysis</el-tag>
                差异基因聚类分析
              </h4>
              <p class="module-desc">
                The first row of input data file is the column name. 
                The first column of input data file is the row name. The separator is '\t'.
              </p>
            </div>

            <!-- GO Enrichment -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">GO Enrichment</el-tag>
                GO富集分析
              </h4>
              <p class="module-desc">
                The first column is row names, the first row is column names.
                Parameters include pvalue/qvalue threshold, plot type, term number, and correction method.
              </p>
            </div>

            <!-- KEGG Enrichment -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">KEGG Enrichment</el-tag>
                KEGG富集分析
              </h4>
              <p class="module-desc">
                The first column is row names, the first row is column names.
                Parameters include pvalue/qvalue threshold, plot type, term number, and correction method.
              </p>
            </div>

            <!-- PPI Network -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">PPI Network</el-tag>
                蛋白互作网络
              </h4>
              <p class="module-desc">
                The first column is gene. Select organism, nomenclature, filtered threshold of score, 
                node number threshold, and plot type for analysis.
              </p>
            </div>

            <!-- Dumbbell with Bar Plot -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Dumbbell with Bar Plot</el-tag>
                哑铃柱状图
              </h4>
              <p class="module-desc">
                Data Set for dumbbell is used to draw dumbbell diagrams. 
                Data Set for bar is used to draw barplot diagrams. 
                Keep the contents and name of the first column in both files similar and same respectively.
              </p>
            </div>
          </div>
        </el-collapse-item>

        <!-- 4. Mail -->
        <el-collapse-item name="mail">
          <template #title>
            <div class="collapse-title">
              <el-icon><Message /></el-icon>
              <span>4. 邮件通知 / Mail</span>
            </div>
          </template>
          <div class="module-content">
            <div class="sub-module">
              <p class="module-desc">
                Users can fill in their email address and the results are sent to the email address 
                when the task is completed.
              </p>
              <el-alert type="success" :closable="false" show-icon>
                推荐用户填写邮箱，任务完成后，结果会发送至邮箱。
              </el-alert>
            </div>
          </div>
        </el-collapse-item>

        <!-- 5. Download -->
        <el-collapse-item name="download">
          <template #title>
            <div class="collapse-title">
              <el-icon><Download /></el-icon>
              <span>5. 下载 / Download</span>
            </div>
          </template>
          <div class="module-content">
            <div class="sub-module">
              <p class="module-desc">
                We provide <a href="https://github.com/ABILiLab/AutoMATA" target="_blank" class="link">
                  docker version
                </a> of AutoMATA, and code for model 
                <a href="https://github.com/ABILiLab/AutoMATA" target="_blank" class="link">training</a> and 
                <a href="https://github.com/ABILiLab/AutoMATA" target="_blank" class="link">data analysis</a> 
                for use by researchers.
              </p>
              <div class="download-buttons">
                <el-button type="primary" @click="openGitHub">
                  <el-icon><Link /></el-icon>
                  GitHub Repository
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 6. Data Process Procedure -->
        <el-collapse-item name="procedure">
          <template #title>
            <div class="collapse-title">
              <el-icon><Operation /></el-icon>
              <span>6. 数据处理流程 / Data Process Procedure</span>
            </div>
          </template>
          <div class="module-content">
            <!-- 暂时移除不存在的图片引用 -->
            <p class="image-caption">AutoMATA 数据处理流程图（示意图待添加）</p>
          </div>
        </el-collapse-item>

        <!-- 7. Quick Start -->
        <el-collapse-item name="quickstart">
          <template #title>
            <div class="collapse-title">
              <el-icon><Promotion /></el-icon>
              <span>7. 快速开始 / Quick Start</span>
            </div>
          </template>
          <div class="module-content">
            <div class="sub-module">
              <el-steps :active="0" direction="vertical" finish-status="success">
                <el-step title="注册/登录" description="创建账户或登录现有账户" />
                <el-step title="上传数据" description="上传您的基因/转录/蛋白表达数据" />
                <el-step title="数据处理" description="选择合适的数据处理方法进行格式转换" />
                <el-step title="模型训练" description="配置参数并训练深度学习模型" />
                <el-step title="数据分析" description="使用多种可视化工具分析数据" />
                <el-step title="下载结果" description="下载分析结果或接收邮件通知" />
              </el-steps>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 快速导航 -->
    <div class="quick-nav">
      <el-card class="nav-card">
        <template #header>
          <div class="card-header">
            <el-icon><Guide /></el-icon>
            <span>快速导航</span>
          </div>
        </template>
        <div class="nav-buttons">
          <el-button @click="router.push('/data-process/genome')">数据处理</el-button>
          <el-button @click="router.push('/model/train/supervised')">模型训练</el-button>
          <el-button @click="router.push('/data-analysis')">数据分析</el-button>
          <el-button @click="router.push('/dashboard')">返回首页</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  DataAnalysis,
  SetUp,
  PieChart,
  Message,
  Download,
  Operation,
  Promotion,
  Guide,
  Link
} from '@element-plus/icons-vue'
import { ElAlert, ElTag } from 'element-plus'

const router = useRouter()

// 当前展开的面板
const activeNames = ref<string>('data-process')

// 打开 GitHub
function openGitHub() {
  window.open('https://github.com/ABILiLab/AutoMATA', '_blank')
}

// 图片加载错误处理
function handleImageError(e: Event) {
  const target = e.target as HTMLImageElement
  target.style.display = 'none'
}
</script>

<style scoped>
.help-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.help-header {
  text-align: center;
  margin-bottom: 32px;
}

.help-title {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 12px 0;
}

.help-subtitle {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.help-content {
  margin-bottom: 32px;
}

/* 手风琴标题 */
.collapse-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 600;
}

.collapse-title .el-icon {
  font-size: 20px;
  color: #409eff;
}

/* 模块内容 */
.module-content {
  padding: 8px 0;
}

.sub-module {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.sub-module:last-child {
  margin-bottom: 0;
}

.sub-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  margin: 0 0 12px 0;
}

.module-desc:last-child {
  margin-bottom: 0;
}

.module-desc i {
  color: #409eff;
  font-style: italic;
}

/* 输出信息 */
.output-info {
  margin-top: 16px;
  padding: 12px 16px;
  background: #ecf5ff;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.output-info p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.output-info ul {
  margin: 0;
  padding-left: 20px;
}

.output-info li {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.output-info code {
  background: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  color: #e6a23c;
}

/* 参数信息 */
.params-info {
  margin-top: 16px;
}

/* 链接样式 */
.link {
  color: #409eff;
  text-decoration: underline;
}

.link:hover {
  color: #66b1ff;
}

/* 下载按钮 */
.download-buttons {
  margin-top: 16px;
}

/* 流程图 */
.procedure-image {
  text-align: center;
}

.procedure-image img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.image-caption {
  margin-top: 12px;
  font-size: 14px;
  color: #909399;
}

/* 快速导航 */
.quick-nav {
  margin-top: 32px;
}

.nav-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.nav-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

/* Element Plus 覆盖 */
.mb-4 {
  margin-bottom: 16px;
}

:deep(.el-collapse-item__header) {
  height: 56px;
  padding: 0 16px;
  font-size: 16px;
}

:deep(.el-collapse-item__content) {
  padding: 16px;
}

:deep(.el-alert) {
  margin-bottom: 16px;
}

:deep(.el-descriptions) {
  margin-top: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .help-page {
    padding: 16px;
  }

  .help-title {
    font-size: 24px;
  }

  .sub-module {
    padding: 12px;
  }

  .nav-buttons {
    flex-direction: column;
  }

  .nav-buttons .el-button {
    width: 100%;
  }
}
</style>
