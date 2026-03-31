<template>
  <div class="help-page">
    <!-- 页面标题 -->
    <div class="help-header">
      <h1 class="help-title">Help Center</h1>
      <p class="help-subtitle">AutoMATA user guide</p>
    </div>

    <!-- 帮助内容 -->
    <div class="help-content">
      <el-collapse v-model="activeNames" accordion>
        <!-- 1. Data Process -->
        <el-collapse-item name="data-process">
          <template #title>
            <div class="collapse-title">
              <el-icon><DataAnalysis /></el-icon>
              <span>1. Data processing</span>
            </div>
          </template>
          <div class="module-content">
            <!-- Genome -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="primary" size="small">Genome</el-tag>
                Genome data processing
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
                of multiple species gene expression data. Missing values were filled with zeros.
              </p>
            </div>

            <!-- Transcriptome -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="success" size="small">Transcriptome</el-tag>
                Transcriptome data processing
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
                Protein data processing
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

            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="primary" size="small">Integration</el-tag>
                Multi-omics data integration
              </h4>
              <p class="module-desc">
                This platform provides combination of multi-omics data from 
                gene expression, transcriptome, protein and phenotype data by sample name.
              </p>
              <p class="module-desc">
                Click "Example" button to download the example data (Example data are gene expression, transcriptome, protein and phenotype data). 
                Missing values were filled with k-NN imputation.
              </p>
            </div>

            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="success" size="small">Pvalue integration</el-tag>
                Pvalue integration for multi-omics data
              </h4>
              <p class="module-desc">
                This platform provides integration of p-values from different sources using directional and non-directional methods.
                Users can select different methods to merge multi-omics data by p-value, including Fisher, Fisher_directional, Brown, DPM, Stouffer, Stouffer_directional, Strube, Strube_directional, and None.
              </p>
              <p class="module-desc">
                Click "Example" button to download the example data (Example data are p-values from different sources). 
                Set the p-value for missing values to 1, and the logFC for missing values to 0
              </p>
            </div>

            
          </div>
        </el-collapse-item>

        <!-- 2. Model -->
        <el-collapse-item name="model">
          <template #title>
            <div class="collapse-title">
              <el-icon><SetUp /></el-icon>
              <span>2. Model training</span>
            </div>
          </template>
          <div class="module-content">
            <!-- Supervised -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="primary" size="small">Train > Supervised</el-tag>
                Supervised training
              </h4>
              <p class="module-desc">
                This platform provides training model function, which including model selection, 
                hyperparameter settings (EarlyStopping, Epochs, Learning Rate, Batch Size, 
                Loss Function, Optimizer, Random Seed, Regularization method, Regularization weight / strength, Dropout rate, Feature selection method, and Label number for multi-class task) 
                and training methods (validation set, StratifiedKFold, or train-validation-test split). 
                AutoMATA will removes samples with missing values.
              </p>
              <el-alert type="info" :closable="false" show-icon>
                <strong>Note:</strong> The last column must be Label with numerical values.
              </el-alert>
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
                Unsupervised training
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
                Semi-supervised training
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

            <!-- Model Use -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="danger" size="small">Use</el-tag>
                Model use
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
              <span>3. Data analysis</span>
            </div>
          </template>
          <div class="module-content">
            <el-alert type="info" :closable="false" show-icon class="mb-4">
              Example data are provided for each analysis method. 
              Try to keep the names of the data columns the same as the example data columns, 
              as this will ensure smooth data analysis.
            </el-alert>

            <!-- All Analysis Flow (aligns with ComprehensiveAnalysis.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag type="primary" size="small">All Analysis Flow</el-tag>
                Comprehensive analysis workflow
              </h4>
              <p class="module-desc">
                Differential expression for Read Counts (DESeq2) or FPKM (limma); low-expression genes are filtered
                and missing values imputed with k-NN. After the run you may start GO/KEGG enrichment from the result view
                when available.
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Expression data file">
                    First column = feature IDs, first row = sample names; tab-separated.
                  </el-descriptions-item>
                  <el-descriptions-item label="Sample data file (group)">
                    Row names must match expression column names. Include a Group column with values
                    <code>Control</code> or <code>Treatment</code>.
                  </el-descriptions-item>
                  <el-descriptions-item label="Select data type">
                    Read Counts or FPKM (matches DESeq2 vs limma on the backend).
                  </el-descriptions-item>
                  <el-descriptions-item label="Organism">
                    Homo sapiens, Bos taurus, Mus musculus, or Drosophila melanogaster (gene ID mapping).
                  </el-descriptions-item>
                  <el-descriptions-item label="Correction method">
                    Multiple-testing correction for differential analysis (e.g. BH, BY, holm, bonferroni, none).
                  </el-descriptions-item>
                  <el-descriptions-item label="log2FC threshold">
                    Genes with |log2FC| above this value are treated as significant by magnitude (typical 0.58, 1, or 2).
                  </el-descriptions-item>
                  <el-descriptions-item label="padj threshold">
                    Genes with adjusted p-value below this value are treated as significant (often 0.05).
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    Volcano plot, differential gene cluster heatmap, and tables of up / down / non-regulated genes.
                    Follow-up GO/KEGG enrichment can be launched from the results UI when offered.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- Correlation Heatmap (CorrelationHeatmap.vue — no extra params) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Correlation Heatmap</el-tag>
                Correlation heatmap
              </h4>
              <p class="module-desc">
                Computes and plots a sample correlation heatmap from your matrix. Only the main data upload and email
                are required on the form.
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    First row = column (sample) names; tab-separated text.
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    Correlation heatmap figure (and related result files in the job folder).
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- PCA (PCA.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Principal Component Analysis</el-tag>
                PCA
              </h4>
              <p class="module-desc">
                Principal component analysis with optional density boundaries and optional PERMANOVA (distance method
                configurable when PERMANOVA is enabled).
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    First column = group or sample label; remaining columns = numeric features; tab-separated.
                  </el-descriptions-item>
                  <el-descriptions-item label="Confidence level">
                    Number between 0 and 1 for ellipse / interval construction (default 0.95).
                  </el-descriptions-item>
                  <el-descriptions-item label="Boundary plot">
                    Add top/right marginal density plots along the PCA axes, or omit them.
                  </el-descriptions-item>
                  <el-descriptions-item label="PERMANOVA analysis">
                    Run PERMANOVA or skip; when enabled, choose a distance metric (e.g. Bray, Euclidean, Manhattan, …).
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    PCA score plot (and PERMANOVA output when requested).
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- Volcano (Volcano.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Volcano Plot with GSEA</el-tag>
                Volcano plot and GSEA
              </h4>
              <p class="module-desc">
                Volcano plot from DE statistics; optional GSEA with a GMT file. Thresholds for highlighting and “TOP”
                labels can be tuned independently.
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    Columns must include <code>gene</code>, <code>logFC</code>, <code>padj</code>; tab-separated.
                  </el-descriptions-item>
                  <el-descriptions-item label="Conduct GSEA analysis">
                    If Yes, upload a GMT file for GSEA; if No, only the volcano workflow runs.
                  </el-descriptions-item>
                  <el-descriptions-item label="Emphasized Genes">
                    Optional comma-separated gene symbols present in the uploaded table (highlighted on the plot).
                  </el-descriptions-item>
                  <el-descriptions-item label="log2FC / padj threshold">
                    Screen significant genes by |log2FC| and padj (defaults 0.5 and 0.05; tips shown on the form).
                  </el-descriptions-item>
                  <el-descriptions-item label="TOP gene count">
                    How many top-ranked genes to emphasize in the display order.
                  </el-descriptions-item>
                  <el-descriptions-item label="log2FC / padj for TOP genes">
                    Stricter (or equal) cutoffs for the TOP layer versus the main thresholds.
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    Volcano figure (and GSEA panels when GMT + Yes are used).
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- Venn (Venn.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">VENN Analysis</el-tag>
                Venn diagram
              </h4>
              <p class="module-desc">
                Overlap visualization across groups; plot style is selectable on the form.
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    First row = column names; each column lists IDs for one group; tab-separated.
                  </el-descriptions-item>
                  <el-descriptions-item label="Choose plot type">
                    Classic Venn, Vennpie, or bar plot.
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    Venn-style figure per selected type.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- Gene cluster (GeneClusterHeatmap.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Differential Gene Cluster Analysis</el-tag>
                Differential gene clustering
              </h4>
              <p class="module-desc">
                Clustered heatmap with configurable distances, scaling, and optional row/column annotations (upload
                annotation files when the UI offers them).
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    First row = column names, first column = row names; tab-separated.
                  </el-descriptions-item>
                  <el-descriptions-item label="Show column / row name">
                    Whether to show sample (column) and gene (row) labels.
                  </el-descriptions-item>
                  <el-descriptions-item label="Cluster method for row / col">
                    Distance for hierarchical clustering (e.g. Euclidean, Correlation, Manhattan, …).
                  </el-descriptions-item>
                  <el-descriptions-item label="Center and scale data">
                    None, scale rows, or scale columns before heatmapping.
                  </el-descriptions-item>
                  <el-descriptions-item label="Row/col annotation">
                    None, row only, column only, or both; extra annotation uploads may appear when needed.
                  </el-descriptions-item>
                  <el-descriptions-item label="Display data by group">
                    Shown only when column annotation or both annotations are selected—split layout by group if Yes.
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    Differential gene cluster heatmap figure.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- GO (GOEnrichment.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">GO Enrichment</el-tag>
                GO enrichment
              </h4>
              <p class="module-desc">
                GO over-representation / visualization. Chord, Cluster, and Circle plot types expect a
                <code>logFC</code> column in the input (see form note).
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    First column = feature IDs, first row = column names; tab-separated.
                  </el-descriptions-item>
                  <el-descriptions-item label="Organism">
                    Homo sapiens, Bos taurus, Mus musculus, or Drosophila melanogaster.
                  </el-descriptions-item>
                  <el-descriptions-item label="pvalue / qvalue threshold">
                    Each in [0, 1]; used to filter enriched terms.
                  </el-descriptions-item>
                  <el-descriptions-item label="Correction method">
                    BH, BY, holm, hochberg, hommel, bonferroni, fdr, or none.
                  </el-descriptions-item>
                  <el-descriptions-item label="Plot type">
                    Bubble, Barplot, Chord, Cluster, or Circle.
                  </el-descriptions-item>
                  <el-descriptions-item label="Terms per ontology">
                    Maximum number of terms to show per ontology (1–50).
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    GO enrichment table and figure.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- KEGG (KEGGEnrichment.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">KEGG Enrichment</el-tag>
                KEGG enrichment
              </h4>
              <p class="module-desc">
                KEGG pathway enrichment. Chord and Cluster plot types require a <code>logFC</code> column (see form note).
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    First column = feature IDs, first row = column names; tab-separated.
                  </el-descriptions-item>
                  <el-descriptions-item label="Organism">
                    Homo sapiens, Bos taurus, Mus musculus, or Drosophila melanogaster
                  </el-descriptions-item>
                  <el-descriptions-item label="pvalue / qvalue threshold">
                    Each in [0, 1]; defaults may differ from GO (see form defaults).
                  </el-descriptions-item>
                  <el-descriptions-item label="Correction method">
                    Same family as GO (BH, BY, holm, …, none).
                  </el-descriptions-item>
                  <el-descriptions-item label="Plot type">
                    Bubble, Chord, or Cluster.
                  </el-descriptions-item>
                  <el-descriptions-item label="Number of terms to display">
                    1–50 pathways/terms in the figure.
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    KEGG enrichment table and figure.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- PPI (PPINetwork.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">PPI Network</el-tag>
                Protein–protein interaction network
              </h4>
              <p class="module-desc">
                Builds a PPI network from a gene list using STRING-style scores; layout and stringency follow the form. The default organism is Mus musculus, and the example data is provided for Mus musculus.
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Data set">
                    First column lists gene identifiers (tab-separated file).
                  </el-descriptions-item>
                  <el-descriptions-item label="Organism">
                    Mus musculus, Bos taurus, Homo sapiens, or Drosophila melanogaster.
                  </el-descriptions-item>
                  <el-descriptions-item label="Nomenclature">
                    Gene Symbol, Ensembl ID, or ENTREZID—must match your input IDs.
                  </el-descriptions-item>
                  <el-descriptions-item label="Score threshold">
                    Minimum interaction score to keep an edge (0–1000; higher = stricter).
                  </el-descriptions-item>
                  <el-descriptions-item label="Min nodes">
                    Only genes with at least this many connected nodes are drawn in the figure.
                  </el-descriptions-item>
                  <el-descriptions-item label="Plot type">
                    Linear, KK, or Stress graph layout.
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    PPI network figure.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>

            <!-- Dumbbell (DumbbellBar.vue) -->
            <div class="sub-module">
              <h4 class="sub-title">
                <el-tag size="small">Dumbbell with Bar Plot</el-tag>
                Dumbbell bar chart
              </h4>
              <p class="module-desc">
                Combined dumbbell and bar chart: two uploads (dumbbell matrix + bar summary) plus axis label and
                optional highlighted terms.
              </p>
              <div class="params-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="Dumbbell data set">
                    Tab-separated file used for the dumbbell tracks.
                  </el-descriptions-item>
                  <el-descriptions-item label="Bar data set">
                    Tab-separated file for bars; first column should align with the dumbbell file’s first column.
                  </el-descriptions-item>
                  <el-descriptions-item label="Label for the x-axis">
                    Text label shown under the x-axis (required).
                  </el-descriptions-item>
                  <el-descriptions-item label="Terms to emphasize">
                    Comma-separated labels that must appear in the uploaded data (required).
                  </el-descriptions-item>
                  <el-descriptions-item label="Output">
                    Dumbbell with bar plot figure.
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </div>
        </el-collapse-item>

        <!-- 训练分析集成流程 -->
        <el-collapse-item name="analyze-train">
          <template #title>
            <div class="collapse-title">
              <el-icon><SetUp /></el-icon>
              <span>4. Analyze & train</span>
            </div>
          </template>
          <div class="module-content">
            <!-- Supervised -->
              <el-alert type="info" :closable="false" show-icon class="mb-4">
                Example data are provided for the comprehensive differential analysis and supervised training function. 
                The samples of whole dataset or training dataset for model training must match group info file.
              </el-alert>
            <div class="sub-module">
              
              <h4 class="sub-title">
                <el-tag type="primary" size="small">Analyze &amp; Train</el-tag>
                Comprehensive differential analysis + Supervised training
              </h4>
              <p class="module-desc">
                This platform provides comprehensive differential analysis and supervised training function, which including data integration, differential analysis, model selection, 
                hyperparameter settings (EarlyStopping, Epochs, Learning Rate, Batch Size, 
                Loss Function, Optimizer, Random Seed, Regularization method, Regularization weight / strength, Dropout rate, Feature selection method, and Label number for multi-class task) 
                and training methods (validation set, StratifiedKFold, or train-validation-test split). AutoMATA will removes samples with missing values. Differential expression for Read Counts (DESeq2) or FPKM (limma); low-expression genes are filtered.
                After the run you may start GO/KEGG enrichment from the result view when available.
                
              </p>
              <el-alert type="info" :closable="false" show-icon>
                <strong>Note:</strong> The last column must be Label with numerical values.
              </el-alert>
              <div class="output-info">
                <p><strong>Output files:</strong></p>
                <ul>
                  <li><code>model.pth</code> - the trained model</li>
                  <li><code>terminal.log</code> - training log with loss and accuracy for each epoch</li>
                  <li><code>figure.png</code> - acc-loss plot during training</li>
                  <li><code>test_result.txt</code> - metrics obtained using testing set</li>
                  <li><code>Volcano plot</code> - png/pdf/jpeg/tiff/svg/bmp format</li>
                  <li><code>Differential gene cluster heatmap</code> - png/pdf/jpeg/tiff/svg/bmp format</li>
                  <li><code>Tables of up / down / non-regulated genes</code> - txt format</li>
                  <li><code>GO/KEGG enrichment result</code> - figures in png/pdf/jpeg/tiff/svg/bmp format and tables in txt format</li>
                </ul>
              </div>
            </div>

          </div>
        </el-collapse-item>

        <!-- 4. Mail -->
        <el-collapse-item name="mail">
          <template #title>
            <div class="collapse-title">
              <el-icon><Message /></el-icon>
              <span>5. Email notifications</span>
            </div>
          </template>
          <div class="module-content">
            <div class="sub-module">
              <p class="module-desc">
                Users can fill in their email address and the results are sent to the email address 
                when the task is completed.
              </p>
              <el-alert type="success" :closable="false" show-icon>
                We recommend adding an email address so results can be sent when tasks complete.
              </el-alert>
            </div>
          </div>
        </el-collapse-item>

        <!-- 5. Download -->
        <el-collapse-item name="download">
          <template #title>
            <div class="collapse-title">
              <el-icon><Download /></el-icon>
              <span>6. Download</span>
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
              <span>7. Workflow</span>
            </div>
          </template>
          <div class="module-content">
            <!-- <p class="image-caption">AutoMATA data processing diagram</p> -->
            <div class="procedure-image-wrap">
              <img
                src="/images/help_data_process.png"
                alt="AutoMATA data processing diagram"
                class="procedure-image"
                loading="lazy"
              />
            </div>
          </div>
        </el-collapse-item>

        <!-- 7. Quick Start -->
        <!-- <el-collapse-item name="quickstart">
          <template #title>
            <div class="collapse-title">
              <el-icon><Promotion /></el-icon>
              <span>7. Quick start</span>
            </div>
          </template>
          <div class="module-content">
            <div class="sub-module">
              <el-steps :active="0" direction="vertical" finish-status="success">
                <el-step title="Register / sign in" description="Create an account or sign in" />
                <el-step title="Upload data" description="Upload gene, transcript, or protein expression data" />
                <el-step title="Data processing" description="Choose a pipeline and convert formats" />
                <el-step title="Model training" description="Configure hyperparameters and train models" />
                <el-step title="Data analysis" description="Run visualizations and statistical analyses" />
                <el-step title="Get results" description="Download outputs or receive email notifications" />
              </el-steps>
            </div>
          </div>
        </el-collapse-item> -->
      </el-collapse>
    </div>

    <!-- 快速导航 -->
    <div class="quick-nav">
      <el-card class="nav-card">
        <template #header>
          <div class="card-header">
            <el-icon><Guide /></el-icon>
            <span>Quick links</span>
          </div>
        </template>
        <div class="nav-buttons">
          <el-button @click="router.push('/data-process/genome')">Data processing</el-button>
          <el-button @click="router.push('/model/train/supervised')">Model training</el-button>
          <el-button @click="router.push('/data-analysis')">Data analysis</el-button>
          <el-button @click="router.push('/dashboard')">Home</el-button>
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

/* 流程图：宽图在容器内缩放；极宽时可在横轴内滚动查看全貌 */
.procedure-image-wrap {
  width: 95%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  text-align: center;
  line-height: 0;
}

img.procedure-image {
  max-width: 95%;
  width: auto;
  height: auto;
  display: inline-block;
  vertical-align: top;
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
