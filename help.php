<?php include __DIR__ . '/header.php' ?>



<!-- <style>
    引入css
    <?php include __DIR__ . '/../static/css/show.css' ?>  /*因为chrome直接用link加载css时会把css转为html，这是不对的，所以要用这样子加载*/
</style> -->
<!-- <section id="banner" style="background-image:url(images/background-img.jpg);"> -->
<section id="banner">
    <div class="container padding-medium-2">
        <div class="hero-content">
            <!-- <h2 class="display-2 fw-semibold">About <span class="text-primary"> Us</span></h2> -->
            <h2 class="display-2 fw-semibold">Help</span></h2>
            <nav class="breadcrumb">
                <a class="breadcrumb-item text-muted nav-link" href="#">Home</a>
                <!-- <a class="breadcrumb-item text-muted nav-link" href="index.php">Help</a> -->
                <span class="breadcrumb-item active" aria-current="page">Help</span>
            </nav>
        </div>
    </div>
</section>

<!-- 上传数据 -->
<section id="service" class="padding-medium">

    <div class="container">
        <!-- 数据处理：基因组和转录组
            基因组：提供将人类、小鼠、果蝇、拟南芥和牛的RPKM、TPM、ReadCount、FPKM和RPM格式的基因表达数据转换为log2(TPM)格式。用户可选择基因的不同命名格式，分别为GeneID、EnsemblID和Symbol。生成的结果文件中，提供了不同命名对应的基因Symbol数据。点击Example按钮，可下载人类基因表达的示例数据。输入Email，可在任务完成后，向用户发送带有结果附件的邮件。
            转录组：提供将人类、小鼠、果蝇和牛的RPKM、TPM、ReadCount、FPKM和RPM格式的mRNA表达数据转换为log2(TPM)格式。用户可选择mRNA的不同命名格式，分别为Refseq Accession、Transcript name和EnsemblID。生成的结果文件中，提供了不同命名对应的转录名。点击Example按钮，可下载数据示例。输入Email，可在任务完成后，向用户发送带有结果附件的邮件。
        模型：训练和使用
            训练：提供训练模型的功能，包括训练模型的选择、超参数设置（早停、迭代次数、学习率）和训练方式（验证集、StratifiedKFold）。在生成的结果压缩包中：model.pt为训练好的模型；terminal.log为训练日志，列出了每一次迭代的训练和验证的损失和精度，最后生成测试结果；figure.png为训练过程中的acc-loss曲线图；test_result.txt为使用测试集的得出的测试精度metrics
            使用：用户可上传平台训练好的模型或者自己训练好的模型（注意：模型必须是使用pickle包保存的pt文件），并上传测试集（注意：测试集维度必须和用于训练模型的训练集维度相同；在测试集中包含样本真实标签，以得到模型测试精度；但如果用户只想使用模型预测样本是否为正样本，那么可随意设置标签为0或1），最后生成测试结果压缩包。
                  在测试结果中，test_metrics_result.txt为使用测试集和模型的得出的测试精度，test_prediction.txt为样本预测结果，包含样本的预测概率值(Prediction Probability)。
        数据分析：多种数据分析方法
            每一个分析方法都提供相应的示例数据。尽量保持数据列名和示例数据列名相同，这可保证数据分析的顺利进行。

        邮件发送：推荐用户填写邮箱，任务完成后，结果会发送至邮箱。

        代码下载：我们提供模型训练和数据分析的代码，以供研究人员使用。

    -->

        <div class="pb-3" style="margin-bottom: 22px;">
            <!-- <label><b>Data Process</b></label> <br> -->
            <p><b>1. Data Process</b></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Genome: </b>
            This platform provides conversion of gene expression data from <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i>, <i>Drosophila Melanogaster</i> and <i>Arabidopsis Thaliana</i> in RPKM, TPM, ReadCounts, FPKM and RPM formats to log2(TPM+1) format.
            Users can select different gene nomenclatures as GeneID, EnsemblID and Symbol, and the generated result file provides the Symbol data of the genes corresponding to different nomenclatures. Click "Example" button to download the example data of human gene expression. Missing values were filled with zeros.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Transcriptome:  </b>
            This platform provides conversion of mRNA expression data from <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i> and <i>Drosophila Melanogaster</i> in RPKM, TPM, ReadCounts, FPKM and RPM formats to log2(TPM+1) format. 
            Users can select different nomenclatures for mRNA, which are Refseq Accession, Transcript name and EnsemblID. Transcript names corresponding to different nomenclatures are provided in the generated result file. Click "Example" button to download the example data. Missing values were filled with zeros.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Protein:  </b>
            This platform provides conversion of protein expression data from <i>Homo Sapiens</i>, <i>Bos Taurus</i>, <i>Mus Musculus</i> and <i>Drosophila Melanogaster</i> in expression value formats to log2(expression value) format. 
            Users can select different nomenclatures for protein, which are UniProt Entry, Refseq Accession, AlphaFoldDB ID, and EnsemblID. Entry names corresponding to different nomenclatures are provided in the generated result file. Click "Example" button to download the example data. Missing values were filled with zeros.
            </p>
            
        </div>

        <div class="pb-3" style="margin-bottom: 22px;">
            <!-- <label><b>Data Process</b></label> <br> -->
            <p><b>2. Model</b></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Train > supervised: </b>
            This platform provides training model function, which including model selection, hyperparameter settings (EarlyStopping, Epochs, Learning Rate, Batch Size, Loss Function, Optimizer, Random Seed, and Label number for multi-class task) and training methods (validation set, StratifiedKFold, or train-validation-test split). AutoMATA will removes samples with missing values.
            In the generated result folder: <i>model.pth</i> is the trained model; <i>terminal.log</i> is the training log, which lists the training and validation loss and accuracy of each epoch, and finally writes the test results; <i>figure.png</i> is the acc-loss plot during the training process; <i>test_result.txt</i> is the result metrics obtained using the testing set and trained model.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Train > unsupervised: </b>
            This platform provides training model function, which including model selection, hyperparameter settings (EarlyStopping, Epochs, Learning Rate, Batch Size, Loss Function, Optimizer, and Random Seed for unsupervised task) and training methods (validation set, StratifiedKFold, or train-validation-test split). AutoMATA will removes samples with missing values.
            Note: All sets don't need label and sample columns.
            In the generated result folder: <i>model.pth</i> is the trained model; <i>scaler.pkl</i> is the scaler; <i>terminal.log</i> is the training log, which lists the training and validation loss and accuracy of each epoch, and finally writes the test results; <i>test_result.png</i> is the metrics plot; <i>test_result.json</i> is the result metrics obtained using the testing set and trained model.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Train > semi-supervised: </b>
            This platform provides training model function, which including model selection, hyperparameter settings (EarlyStopping, Epochs, Learning Rate, Batch Size, Loss Function, Optimizer, Random Seed, and some parameters about loss weight for semi-supervised task) and training methods (validation set, StratifiedKFold, or train-validation-test split). AutoMATA will removes samples with missing values.
            Note: Validation and testing set must have label for each sample. Training set could contain 'Unknown' label for samples with no label.  
            In the generated result folder: <i>model.pth</i> is the trained model; <i>scaler.pkl</i> is the scaler; <i>terminal.log</i> is the training log, which lists the training and validation loss and accuracy of each epoch, and finally writes the test results; <i>test_result.png</i> is the metrics plot; <i>test_result.json</i> is the result metrics obtained using the testing set and trained model.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Use:  </b>
            Users can upload trained model or their own trained model (<i>NOTE: the model must be a pth file saved using the torch to achieve cross-platform prediction</i>), and upload the test set (<i>NOTE: the feature dimension of the testing set must be the same as that of the training set used to train the model; including the true label of sample in the testing set to get the model test metrics results; but if the user only wants to use the model to predict whether the sample is positive or not, then feel free to set labels 0 or 1</i>), and finally generate the test result zip.
            Among all the files of test results, <i>test_metrics_result.txt</i> is the test metrics results using the testing set and the model, and <i>test_prediction.txt</i> is the sample prediction result, which contains the sample's prediction probability value.
            </p>
            
        </div>

        <div class="pb-3" style="margin-bottom: 22px;">
            <!-- <label><b>Data Process</b></label> <br> -->
            <p><b>3. Data Analyse</b></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;
            Example data are provided for each analysis method. Try to keep the names of the data columns the same as the example data columns, as this will ensure smooth data analysis.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>All Analysis Flow: </b>
            This function provides differential expressed analysis to ReadCounts and FPKM, which use the DESeq2 and limma packages respectively. Automatically remove genes with low expression levels. Use k-NN to impute missing values.<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Expression Data</i>: The first column is row names, the first row is column names.  <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Sample Information</i>: You need to make sure that the order of the samples in the expression file corresponds to the group info file order here. Keep the row names in the group file the same as the column names in the expression file: Control_1, Control_2, Treatment_1, Treatment_2. The Group file must contain a Group column, and the value of the group column must be 'Control' or 'Treatment'. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>log2(FC) threshold</i>: Genes with |log2(FC)| > threshold were screened as significant differential genes to ensure that the magnitude of change was significant. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>padj threshold</i>: Genes with padj < threshold were screened as significant differential genes to ensure significance. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Correction method</i>: The corrective methods used when conducting difference analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: Volcano plot, differnetial gene cluster heatmap, all significantly up/down/non-regulated differentially expressed genes data files. Since then, GO and KEGG enrichment analysis can be performed on the significant differentially expressed genes if you click "GO" button.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Correlation Heatmap: </b>
            This function provides correlation heatmap analysis<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: The first row of input data file is the column name. The seperater is '\t'. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: Correlation heatmap.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Principal Component Analysis: </b>
            This function provides pca analysis<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: The first column of the data is the group information. The seperater is '\t'. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Boundary plot</i>: It decides whether to add boundary plots, which are the top and right sub-plots of the figure.<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>PERMANOVA analysis</i>: It decides whether to add PERMANOVA analysis.<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: PCA plot.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Volcano Plot with GSEA: </b>
            This function provides volcano plot analysis with GSEA analysis<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: Make sure the column names of the dataset are gene, logFC, padj. The seperater is '\t'. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>GSEA Analysis</i>: It decides whether to conduct GSEA analysis, if 'Yes', then please upload GMT file.<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Emphasize gene names</i>: The entered gene names should be included in the uploaded data set, the separator must be comma ','<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>TOP number</i>: The TOP shows the higher-order gene that needs to be displayed. The emphasized genes are in the dashed box.<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>log2FC and padj threshold for TOP genes</i>: These values should be the same as or stricter than the other values from previous step.<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: Volcano with GSEA plot.    
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>VENN Analysis: </b>
            This function provides venn analysis<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: The first row is the column names, and each column is the information for each group. The seperater is '\t'. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Plot Type</i>: It decides the type of output figure. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: Venn plot.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Differential Gene Cluster Analysis: </b>
            This function provides differential gene cluster analysis<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: The first row of input data file is the column name. The first column of input data file is the row name. The seperater is '\t'. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Show Column Name</i>: Generally the sample name <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Show Row Name</i>: Generally the gene name <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Add Annotation</i>: For example, 'row annotation' is the Path/Celltype in the example figure, 'column annotation' is the group/Age/Grade/Stage/Sex in the example figure. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: Differential Gene Cluster Heatmap.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>GO Enrichment: </b>
            This function provides GO enrichment analysis <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: The first column is row names, the first row is column names.  <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>pvalue</i>: pvalue threshold for GO enrichment analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>qvalue</i>: qvalue threshold for GO enrichment analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Plot Type</i>: It decides the type of output figure. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Term Number</i>: the number of terms for each ontology to be displayed. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Correction method</i>: The corrective methods used when conducting GO enrichment analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: GO enrichment analysis results and figure.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>KEGG Enrichment: </b>
            This function provides KEGG enrichment analysis <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: The first column is row names, the first row is column names.  <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>pvalue</i>: pvalue threshold for KEGG enrichment analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>qvalue</i>: qvalue threshold for KEGG enrichment analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Plot Type</i>: It decides the type of output figure. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Term Number</i>: the number of terms for each ontology to be displayed. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Correction method</i>: The corrective methods used when conducting KEGG enrichment analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: KEGG enrichment analysis results and figure.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>PPI Network: </b>
            This function provides KEGG enrichment analysis <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set</i>: The first column is gene.  <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Organism</i>: The organism that dataset indicated. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Nomenclature</i>: The gene nomenclature used in the data set. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Filtered threshold</i>: Input filtered threshold of score for PPI analysis. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Number</i>: Only gene names with more than this number of nodes are shown in the figure. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Plot type</i>: It decides the type of output figure. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: PPI figure.
            </p>

            <p>&nbsp;&nbsp;&nbsp;&nbsp;<b>Dumbbell with Bar Plot: </b>
            This function provides dumbbell with bar Plot<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set for dumbbell</i>: This file is used to draw dumbbell diagrams. The seperater is '\t'. <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Data Set for bar</i>: This file is used to draw barplot diagrams. Keep the contents and name of the first column in both two files similar and same respectively.<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Label</i>: the label for the x-axis<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Emphasize terms</i>: The entered terms should be included in the uploaded data set, the separator must be comma ','<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>Output results</i>: Dumbbell with Bar Plot.
            </p>

        </div>

        <div class="pb-3" style="margin-bottom: 22px;">
            <!-- <label><b>Data Process</b></label> <br> -->
            <p><b>4. Mail</b></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;
            Users can fill in their email address and the results are sent to the email address when the task is completed.
            </p>
        </div>

        <div class="pb-3" style="margin-bottom: 22px;">
            <!-- <label><b>Data Process</b></label> <br> -->
            <p><b>5. Download</b></p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;
            We provide <a href="https://github.com/ABILiLab/AutoMATA" style="text-decoration:underline;">docker version</a> of AutoMATA , and code for model <a href="https://github.com/ABILiLab/AutoMATA" style="text-decoration:underline;">training</a> and <a href="https://github.com/ABILiLab/AutoMATA" style="text-decoration:underline;">data analysis</a> for use by researchers.
            </p>
        </div>

        <div class="pb-3" style="margin-bottom: 22px;">
            <p><b>6. Data Process Procedure</b></p>
            <img src="images/data_process.png" alt="img" class="img-fluid">
        </div>
        



    </div>

</section>

<?php include __DIR__ . '/footer.php' ?>