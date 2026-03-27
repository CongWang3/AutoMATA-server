setwd("/xp/www/AutoMATA/code")
library(DESeq2)
library(dplyr)
getOption('timeout')  # 解决超时
options(timeout=100000)
library(optparse)  # 命令行

option_list <- list(
  make_option(c("-i", "--expression_file"), type="character", default="", action="store", help="This argument is expression file path"),
  make_option(c("-k", "--info_file"), type="character", default="", action="store", help="This argument is group information file path"),
  make_option(c("-j", "--jobID"), type="character", action="store", default="20250320172346_i95Jz8FI" ,help="This argument is jobID"),  # go_case1
  make_option(c("-c", "--fc_thr"), type="double", action="store", default="1", help="This argument defines log2FC threshold for differential expression analysis"),
  make_option(c("-d", "--padj_thr"), type="double", action="store", default="1", help="This argument defines padj threshold for differential expression analysis"),
  make_option(c("-e", "--correction"), type="character", action="store", default="BH", help="This argument defines hypothesis correction method, including none, BH, BY, holm, hochberg, hommel, or bonferroni")  # 一审

)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to conduct differential expression analysis and generate volcano and cluster plots!", add_help_option=FALSE))

# 差异基因阈值
fc_thr <- opt$fc_thr
padj_thr <- opt$padj_thr
# fc_thr <- 1
# padj_thr <-  1 # 0.01

# 读取数据
#指定分组，注意要保证表达矩阵中的样本顺序和这里的分组顺序是一一对应的
# counts <- read.csv("../example/read_count.csv", row.names = 1)
# group_info <- read.csv("../example/group_info.csv")
# counts <- read.table("../example/read_count.txt", row.names = 1, header = TRUE, sep = "\t", check.names = FALSE)
# group_info <- read.table("../example/group_info.txt", header = TRUE, sep = "\t", check.names = FALSE)
counts <- read.table(
  paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/", opt$jobID, "_data.txt", sep = ""),
  header = TRUE,
  sep = "\t",
  check.names = FALSE,
  stringsAsFactors = FALSE,
  fill = TRUE,
  comment.char = "",
  quote = ""
)
group_info <- read.table(paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/", opt$jobID, "_info.txt", sep = ""), header = TRUE, sep = "\t", check.names = FALSE, fill = TRUE, comment.char = "")
groups <- factor(group_info$Group, levels = c("Control", "Treatment"))

# 先读取首列为普通列，再进行基因名清洗与去重（避免 read.table(row.names=1) 因重复行名直接报错）
gene_names <- trimws(as.character(counts[[1]]))
valid_gene <- !(is.na(gene_names) | gene_names == "")
if (any(!valid_gene)) {
  counts <- counts[valid_gene, , drop = FALSE]
  gene_names <- gene_names[valid_gene]
  cat("Rows with empty gene names have been removed\n")
}
if (any(duplicated(gene_names))) {
  cat("Duplicate gene names detected; keeping first occurrence only\n")
  keep_idx <- !duplicated(gene_names)
  counts <- counts[keep_idx, , drop = FALSE]
  gene_names <- gene_names[keep_idx]
}
rownames(counts) <- gene_names
counts <- counts[, -1, drop = FALSE]

# 确保表达矩阵为数值型
counts[] <- lapply(counts, function(x) as.numeric(as.character(x)))

counts <- counts[which(rowSums(counts)!=0),] #删除表达量为0的基因  一审 新增

# 空值处理 K近邻插补  一审增加
if(any(is.na(counts))) {
  # K近邻插补
  cat("begin KNN imputation\n")
  library(impute)
  counts <- impute.knn(as.matrix(counts))$data
}


# 删除表达量过低的数据行 粗筛
counts <- counts[rowMeans(counts)>1,]

# 创建 DESeqDataSet 对象
dds <- DESeqDataSetFromMatrix(
  countData = counts,
  colData = data.frame(group = groups),
  design = ~ group
)

# 过滤低表达基因（至少 10 reads 总和） 细筛
keep <- rowSums(counts(dds)) >= 10
dds <- dds[keep, ]

# 差异分析
# dds <- DESeq(dds)
# parallel = TRUE 可以多线程运行，在数据量较大时建议开启
# minReplicatesForReplace = 5 表示至少有 5 个重复测序的样本才可以被替换 替换重复样本
dds <- DESeq(dds, minReplicatesForReplace=5, parallel = FALSE)  

# 提取结果
DESeq2_results <- results(dds, contrast = c("group", "Treatment", "Control"), pAdjustMethod = opt$correction)
DESeq2_results <- as.data.frame(DESeq2_results)

# # 筛选显著差异基因 (|log2FoldChange| > 1, padj < 0.05)
# sig_genes_DESeq2 <- subset(DESeq2_results, abs(log2FoldChange) > 1 & padj < 0.05)

# 修改列名
# log2FoldChange -> logFC
# 第一列 -> gene
DESeq2_results <- dplyr::rename(DESeq2_results, logFC = log2FoldChange)
gene <- rownames(DESeq2_results)
DESeq2_results <- cbind(gene,DESeq2_results)
#对表格排序，按 padj 值升序排序，相同 padj 值下继续按 log2FC 降序排序
DESeq2_results <- DESeq2_results[order(DESeq2_results$padj, DESeq2_results$logFC, decreasing = c(FALSE, TRUE)), ]
# 保存结果
# filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/DESeq2_results.txt", sep="")
# write.table(DESeq2_results, filename, row.names = FALSE, sep='\t')  # 待实现表格分页展示



# https://www.jianshu.com/p/b5541d695108
# 自定义阈值筛选差异表达基因

#log2FC≥1 & padj<0.01 标识 up，代表显著上调的基因
#log2FC≤-1 & padj<0.01 标识 down，代表显著下调的基因
#其余标识 none，代表非差异的基因
DESeq2_results[which(DESeq2_results$logFC >= fc_thr & DESeq2_results$padj < padj_thr),'sig'] <- 'up'
DESeq2_results[which(DESeq2_results$logFC <= -fc_thr & DESeq2_results$padj < padj_thr),'sig'] <- 'down'
DESeq2_results[which(abs(DESeq2_results$logFC) <= fc_thr | DESeq2_results$padj >= padj_thr),'sig'] <- 'none'

#输出选择的差异基因总表
res1_select <- subset(DESeq2_results, sig %in% c('up', 'down'))
filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/select_all.txt", sep="")
write.table(res1_select, file = filename, row.names = FALSE, sep='\t', quote = FALSE)  # 所有上下调差异基因。能不能实现根据条件筛选？下拉框up down all

#根据 up 和 down 分开输出
res1_up <- subset(DESeq2_results, sig == 'up')
res1_down <- subset(DESeq2_results, sig == 'down')

filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/select_up.txt", sep="")
write.table(res1_up, file = filename, row.names = FALSE, sep='\t', quote = FALSE)  # 所有显著上调差异基因
filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/select_down.txt", sep="")
write.table(res1_down, file = filename,  row.names = FALSE, sep='\t', quote = FALSE)  # 所有显著下调差异基因


# 画图
# 火山图
library(ggplot2)
print("Drawing Volcano Plot")
p1 <- ggplot(DESeq2_results, aes(x = logFC, y = -log10(padj))) + 
  annotate("rect", xmin = sort(res1_down$logFC)[1], xmax = max(res1_down$logFC), 
    ymin = -log10(padj_thr), ymax = ifelse(-log10(min(res1_down$padj)) >= -log10(min(res1_up$padj)), -log10(min(res1_down$padj)), -log10(min(res1_up$padj))), fill = "#CCDFF1") + #文章颜色#E6E7FC DOWN
  annotate("rect", xmin = min(res1_up$logFC), xmax = max(res1_up$logFC), 
    ymin = -log10(padj_thr), ymax = ifelse(-log10(min(res1_down$padj)) >= -log10(min(res1_up$padj)), -log10(min(res1_down$padj)), -log10(min(res1_up$padj))), fill = "#cfc6fe") + #文章颜色#FDE7E9 #DCEABB  #ffe7ff(浅粉)  #cfc6fe(浅紫) UP
  
  annotate("text", x = (sort(res1_down$logFC)[1] + max(res1_down$logFC)) / 2, y = ifelse(-log10(min(res1_down$padj)) >= -log10(min(res1_up$padj)), -log10(min(res1_down$padj)), -log10(min(res1_up$padj)))+0.1, label = "DOWN", color = "#5EA7D3", size = 5, lineheight = 0.8, vjust = 0) + #文章颜色#857CD9  # DOWN label
  annotate("text", x = (min(res1_up$logFC) + max(res1_up$logFC)) / 2, y = ifelse(-log10(min(res1_down$padj)) >= -log10(min(res1_up$padj)), -log10(min(res1_down$padj)), -log10(min(res1_up$padj)))+0.1, label = "UP", color = "#b285b2", size = 5, lineheight = 0.8, vjust = 0) + #文章颜色#FF7D81  # UP label
  annotate("text", x = max(res1_up$logFC)+0.1, y = -log10(0.05), label = "α = 0.05", color = "#b285b2", size = 4.5) +

  geom_vline(xintercept = 0, color = "grey60", linewidth = 0.6) +
  geom_hline(yintercept = 0, color = "grey60", linewidth = 0.6) +
  geom_hline(yintercept = -log10(0.05), linetype = "dotted", color = "#b285b2", linewidth = 0.6) +  # α的线

  geom_point(data = DESeq2_results, shape = 21, color = "black", alpha = 0.1, size = 1.2, stroke = 0.7, fill = "grey60") +
  scale_x_continuous(limits = c(floor(sort(res1_down$logFC)[1]), ceiling(max(res1_up$logFC)))) +
  
  labs(x = expression(paste(log[2],"FC",sep="")), y = expression(paste(-log[10]," adj.p-value",sep=""))) + # y轴：-log10(genes$padj)
  theme_classic(base_size = 15) + 
  theme (legend.position = "none")

result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/volcano", sep="")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width = 7.5, height = 6)
}

print("Drawing Volcano Plot End")


# 差异基因聚类热图df_cluster_heatmap
# https://zhuanlan.zhihu.com/p/531957349
# 在原表达矩阵中找到差异表达基因
library(ComplexHeatmap)
library(ggplotify)
print("Drawing Cluster Heatmap")
df <- counts[intersect(rownames(counts),rownames(res1_select)),]
df2<- as.matrix(df)  
col_annotation <- group_info                                               
rownames(col_annotation) <- col_annotation[,1] ## 第一列转换为行名
col_annotation <- col_annotation[,-1,drop=FALSE]  # 删除第一列 并保持为data frame

p1 <- pheatmap(df2,
                column_split = as.factor(group_info$Group), ####分开热图
                color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(floor(min(df2)), ceiling(max(df2)), length.out = 256),  # 设置颜色断点
                clustering_distance_rows = "euclidean",
                clustering_distance_cols = "euclidean",
                show_colnames = T,
                # show_rownames = T,
                annotation_col = col_annotation,
                annotation_colors = list(Group=c(Control='#cfc6fe',Treatment='#CCDFF1')),
                fontsize = 20,
                fontsize_col =20,  
                heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                            legend_width = 0.2),  # 设置图例宽度
                scale = "row")  # 已进行了标准化，所以这里不再缩放
p1 <- as.ggplot(p1)
result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/df_cluster_heatmap", sep="")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width=20, height=20)
}
print("Drawing Cluster Heatmap End")


