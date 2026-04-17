# B站：https://www.bilibili.com/video/BV1T1421274d/?spm_id_from=333.788&vd_source=057f1ccccc12750f57f6d28b9c852bbd
invisible(local({
  if (!"automata:paths" %in% search()) {
    ca <- commandArgs(trailingOnly = FALSE)
    ff <- ca[grepl("^--file=", ca)]
    ap <- NA_character_
    if (length(ff)) {
      sp <- suppressWarnings(tryCatch(
        normalizePath(sub("^--file=", "", ff[1]), winslash = "/", mustWork = TRUE),
        error = function(e) NA_character_))
      if (!is.na(sp) && nzchar(sp)) {
        d <- dirname(sp)
        for (i in 1:16) {
          cand <- file.path(d, "automata_paths.R")
          if (file.exists(cand)) { ap <- cand; break }
          p <- dirname(d)
          if (p == d) break
          d <- p
        }
      }
    }
    if ((is.na(ap) || !nzchar(ap)) && nzchar(Sys.getenv("AUTOMATA_REPO_ROOT", unset = "")))
      ap <- file.path(Sys.getenv("AUTOMATA_REPO_ROOT"), "code", "automata_paths.R")
    if (!is.na(ap) && nzchar(ap) && file.exists(ap)) source(ap, local = FALSE) else
      stop("找不到 code/automata_paths.R；请设置 AUTOMATA_REPO_ROOT。", call. = FALSE)
  }
}))
rm(list=ls())
setwd(automata_path_data_analysis_plot())

library(clusterProfiler)
if (!requireNamespace("org.Hs.eg.db", quietly=TRUE)) {
    message("Installing org.Hs.eg.db from Bioconductor (persistent cache: R_LIBS_USER)...")
    BiocManager::install("org.Hs.eg.db", ask=FALSE, update=FALSE)
}
library(org.Hs.eg.db)  # 人类的包 待修改为其他物种的包 下载链接：https://www.bioconductor.org/packages/release/BiocViews.html#___OrgDb
library(dplyr)
library(GOplot)
library(DOSE)  # yulab.utils最新包下载https://cran.rstudio.com/web/packages/yulab.utils/index.html
library(ggplot2)
library(tidyr)
getOption('timeout')  # 解决超时
options(timeout=100000)
library(optparse)  # 命令行

# 还未实现：用GO.txt文件直接绘制GO富集分析结果
# 还未实现：用过滤后的GO_filtered数据绘制barplot和bubbleplot


# NOTE: 按照GeneRatio排序呈现图片
# NOTE: 如果要使用chord/cluster/circle，请确保上传的文件有列名为logFC的数值型数据，用来根据数值大小进行排序。同时保证第一列为gene name（symbol）,否则仅需要gene name（symbol）数据

option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", action="store", default="go_case1" ,help="This argument is jobID"),  # go_case1
  make_option(c("-a", "--type"), type="character", action="store",default="chord", help="This argument is the type of figure"),
  make_option(c("-b", "--organism"), type="character", default="Homo_sapiens", action="store", help="This argument defines organism"),
  make_option(c("-c", "--pvalue"), type="double", action="store", default="0.05", help="This argument defines pvalue threshold for GO enrichment analysis"),
  make_option(c("-d", "--qvalue"), type="double", action="store", default="0.05", help="This argument defines qvalue threshold for GO enrichment analysis"),
  make_option(c("-e", "--termNum"), type="integer", default="5", action="store", help="This argument is the number of terms for each ontology to be displayed"),
  make_option(c("-f", "--type_analysis"), default="none", type="character", action="store", help="up, down, all, or none. All analysis need this parameter, otherwise set it to none."),
  make_option(c("-g", "--adjust"), type="character", default="BH", action="store", help="This argument is the pvalue adjustment method for GO enrichment analysis, one of holm, hochberg, hommel, bonferroni,BH, BY, fdr, none")  # 一审

)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw GO Enrichment!", add_help_option=FALSE))

organism <- opt$organism  # Mus musculus, Bovine, Homo_sapiens
if (organism == "Homo_sapiens"){
    db <- "org.Hs.eg.db"  # 人类的包 待修改为其他物种的包
}else if(organism == "Mus_musculus"){
    db <- "org.Mm.eg.db"
}else if (organism == "Bovine"){
    db <- "org.Bt.eg.db"
}else if (organism == "Drosophila_melanogaster"){
    db <- "org.Dm.eg.db"  # 待下载
}else if (organism == "Arabidopsis"){
    db <- "org.At.tair.db"  # 待下载
}
# 按需安装物种对应注释包（org.Hs.eg.db 已在上方加载；其余首次使用时下载到持久卷 R_LIBS_USER）
if (exists("db") && !is.null(db) && db != "org.Hs.eg.db") {
    if (!requireNamespace(db, quietly=TRUE)) {
        message("Installing R package: ", db, " from Bioconductor...")
        BiocManager::install(db, ask=FALSE, update=FALSE)
    }
    library(package=db, character.only=TRUE)
}
# 富集分析的参数
pvalue <- opt$pvalue  # 显著性水平
qvalue <- opt$qvalue  # 显著性水平
# 过滤富集分析结果GO.txt。不过滤的话adj和pval=1。
# pval <- 0.05
# adj <- 0.05
type <- opt$type # 气泡图bubble，柱状图bar，和弦图chord，聚类图cluser，圆形图circle
termNum <- opt$termNum  # 呈现数据集中的前几个通路。chord 和 cluster 图要用到. termNum和show参数意思相同，所以删除show参数，只使用termNum参数
adjust <- opt$adjust  # 调整方法，默认使用BH  一审

# 不需要富集分析的参数
# show <- opt$show  # 显示每个ontology的前10个通路。 barplot 和 bubble要用的
# interesting <- c()
# interesting <- c("GO:0045061","GO:0043383","GO:2000561","GO:0046641","GO:0032633",
#                 "GO:0098978", "GO:0044304", "GO:0062023", "GO:0030669", "GO:0060170",
#                 "GO:0051020", "GO:0005261", "GO:0045296", "GO:0015631", "GO:0016887")  # 选择感兴趣的GO分类呈现，如GO:0008150，即细胞生物学相关的GO分类
# png 的width=1050，height=600

# read data
if (opt$type_analysis == "none"){
    opt$input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt"))
    table_data <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)  # 不检查列名是否存在 \t
}else{
    # 读取up, down, all数据
    table_data <- read.table(automata_job_file(opt$jobID, paste0("result/select_", opt$type_analysis, ".txt")), header = TRUE, sep = "\t", check.names = FALSE)  # 不检查列名是否存在 \t
}

# 提取表格第一列，即基因名称列
gene_column <- table_data[[1]]
# 存储基因的EntrezID
entrez_ids <- c()

# 遍历基因名称列中的每个基因，获取gene的EntrezID
for (gene in gene_column){
    # 使用try catch捕获错误
    id <- tryCatch({
        if (organism == "Homo_sapiens"){
            mget(gene, org.Hs.egSYMBOL2EG)[[1]][1] 
        }else if(organism == "Mus_musculus"){
            mget(gene, org.Mm.egSYMBOL2EG)[[1]][1] 
        }else if (organism == "Bovine"){
            mget(gene, org.Bt.egSYMBOL2EG)[[1]][1] 
        }else if (organism == "Fly"){
            mget(gene, org.Dm.egSYMBOL2EG)[[1]][1] 
        }else if (organism == "Arabidopsis"){
            mget(gene, org.At.tairSYMBOL)
        }
    }, error = function(e) {
        # 如果匹配不到，则返回NA
        NA
        # return(NA)
    })

    # 将匹配到的EntrezID添加到entrez_ids向量中
    entrez_ids <- c(entrez_ids, id)
}


# 处理entrez_ids
# 将entrez_ids向量转换为字符向量
entrez_ids <- as.character(entrez_ids)
# 将entrez_ids添加到原始数据表格中，生成新列entrezID
table_data$entrezID <- entrez_ids
# table_data <- cbind(table_data, entrezID=entrez_ids)
# 删除entrezID为空的行
table_data <- table_data[!is.na(table_data$entrezID), ]



# 进行GO富集分析, 设置pvalue和qvalue阈值，选择所有ontology，结果可读
# 提取表格中的entrezID列
gene <- table_data$entrezID
GO <- enrichGO(gene = gene, 
               OrgDb = db, 
               pvalueCutoff = pvalue, 
               qvalueCutoff = qvalue, 
               ont = "ALL",
               readable  = TRUE,
               pAdjustMethod = adjust)


# 筛选数据 过滤数据
# 根据pvalue和adjusted pvalue过滤GO结果
# GO_filtered <- GO[(GO$p.adjust < adj) & (GO$pvalue < pval), ]
# 将富集结果写入GO.txt文件，制表符分隔，输出行名
filename <- automata_job_file(opt$jobID, "result/GO_enrichment_result.txt")
write.table(GO, file = filename, sep = "\t", row.names = FALSE)


# # 绘制GO富集分析结果
# if (length(interesting) != 0){
#     # 选择感兴趣的GO分类
#     selected_GO <- subset(GO, GO$ID %in% interesting)
#     GO@result <- selected_GO
# }
# 保存图片
result_path <- automata_job_file(opt$jobID, "result/go_enrichment")


# 气泡图
if (type == "bubble"){
    # 判断GO结果是否为空
    if (length(GO) > 0){
        # 绘制气泡图, 显示前5个ontology分类，按基因比例排序
        bubble <- dotplot(GO, showCategory = termNum, split="ONTOLOGY", orderBy="GeneRatio") +   
            facet_grid(ONTOLOGY ~ ., scale = "free")  # 创建分面网格，每个ontology分类一个面
        
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), bubble, device = dev, width = 15, height = 10)
        }
            
    }else{
        print("No GO enrichment data found")
        empty_plot <- ggplot() + theme_void()
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
        }
    }

    
    # ggsave(paste("GO", dev, sep="."), bubble, width = 15, height = 10, device = dev)
    # # ggsave("GO_bubble.pdf", bubble, width = 20, height = 10)
}




# 柱状图
if (type == "barplot"){
    # 判断GO结果是否为空
    if (length(GO) > 0){
        # 绘制柱状图, 显示前5个ontology分类，按基因比例排序
        bar <- barplot(GO, drop=TRUE, showCategory = termNum, split="ONTOLOGY", orderBy="GeneRatio") +
            facet_grid(ONTOLOGY ~ ., scale = "free") # 创建分面网格，每个ontology分类一个面
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), bar, device = dev, width = 15, height = 10)
        }
    }else{
        print("No GO enrichment data found")
        empty_plot <- ggplot() + theme_void()
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
        }
    }
}




# 和弦图（需要富集分析。使用GO富集结果）
GO <- GO[order(GO$Count, decreasing = TRUE), ]  # 按照Count降序排列
if (type == "chord" || type == "cluster" || type == "circle"){
    # 将过滤后的GO结果转换为dataframe (ONTOLOGY, ID, Description, geneID, p.adjust)
    go <- data.frame(
        Category = GO$ONTOLOGY,
        ID = GO$ID,
        Term = GO$Description,
        Genes = gsub("/", ", ", GO$geneID), 
        adj_pval = GO$p.adjust
    )
    # 从原始数据中提取geneID和logFC，创建数据框genelist
    genelist <- data.frame(
        # ID = table_data$gene,
        # logFC = table_data$logFC
        ID = table_data[[1]],  # 第一列为基因名
        logFC = table_data[[2]]  # 第二列为logFC 按列取值
    )

    # 将genelist的行名设置为geneID，以便后续引用
    row.names(genelist) <- genelist$ID

    # 使用circle_dat函数创建圆形布局的数据，用于后续圆形图的绘制
    circ <- circle_dat(go, genelist)

    # 根据go数据框中的术语数量设置termNum，如果少于termNum则使用实际术语数量
    termNum <- ifelse(nrow(go) < termNum, nrow(go), termNum)

    # 获取genelist中的基因数量
    geneNum = nrow(genelist)
}


# 绘制和弦图
if (type == "chord"){
    # go$Term[1:termNum]为需要展示的GO条目
    chord <- chord_dat(circ, genelist[1:geneNum, ], go$Term[1:termNum])
    # 检查chord对象是否创建成功，如果成功则绘制圆形图
    if (!is.null(chord)){
        # 绘制和弦图
        # 设置基因之间的距离、基因排序、基因大小、边框大小和处理标签
        print("Drawing GO chord plot")
        gochord <- GOChord(chord,
                space=0.02,
                gene.order="logFC",
                gene.space=0.25,  # 基因在圆周上的间距
                gene.size = 5,  # 基因名大小
                # border.size = 0.1,  # 基因节点边框大小
                process.label = 10  # 处理标签大小？
                ) 
        for(dev in c("jpeg", "pdf", "tiff", "png", "bmp", "svg")){  # "pdf", "jpeg", "tiff", "png", "bmp", "svg"
            ggsave(paste(result_path, dev, sep = "."), gochord, device = dev, width = 15, height = 15)
        }
    }else{
        print("No created chord object")
        empty_plot <- ggplot() + theme_void()
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
        }
    }

}



# 绘制GO聚类图
if (type == "cluster"){
    chord <- chord_dat(circ, genelist[1:geneNum, ], go$Term[1:termNum])
    # 如果GO数据不为空且行数大于0，则绘制GO聚类图，使用前termNum个术语
    if (!is.null(GO) && nrow(GO) > 0){
        gocluster <- GOCluster(circ, as.character(GO[1:termNum, 3]))
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), gocluster, device = dev, width = 15, height = 8)
        }
    }else{
        print("No GO enrichment data found, we can not draw GO cluster plot")
        empty_plot <- ggplot() + theme_void()
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
        }
    }
    
}

# 圆形图
if (type == "circle"){
    go_circ <- GOCircle(circ, zsc.col=c("purple", "black", "cyan"), label.size=4)
    if (!is.null(go_circ)){
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), go_circ, device = dev, width = 15, height = 8)
        }
    }else{
        print("No GO enrichment data found, we can not draw GO circle plot")
        empty_plot <- ggplot() + theme_void()
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
        }
    }
}
