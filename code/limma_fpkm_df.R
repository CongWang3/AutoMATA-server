setwd("/xp/www/AutoMATA/code")
library(limma)
library(dplyr)
getOption('timeout')  # 解决超时
options(timeout=100000)
library(pheatmap)
library(ggplot2)
library(optparse)  # 命令行

option_list <- list(
  make_option(c("-i", "--expression_file"), type="character", default="", action="store", help="This argument is expression file path"),
  make_option(c("-k", "--info_file"), type="character", default="", action="store", help="This argument is group information file path"),
  make_option(c("-j", "--jobID"), type="character", action="store", default="go_case1" ,help="This argument is jobID"),  # go_case1
  make_option(c("-c", "--fc_thr"), type="double", action="store", default="1", help="This argument defines log2FC threshold for differential expression analysis"),
  make_option(c("-d", "--padj_thr"), type="double", action="store", default="1", help="This argument defines padj threshold for differential expression analysis"),
  make_option(c("-e", "--correction"), type="character", action="store", default="BH", help="This argument defines hypothesis correction method, including none, BH, BY, holm, hochberg, hommel, bonferroni")  # 一审
)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to conduct differential expression analysis and generate volcano and cluster plots!", add_help_option=FALSE))

# 差异基因阈值
fc_thr <- opt$fc_thr
padj_thr <- opt$padj_thr

# read data
# fpkm <- read.csv("E:\\deskTop\\multi_omics\\manu\\多组学平台\\article\\case study2-analysis\\BLCA_fpkm.csv", row.names = 1)
# group_info <- read.csv("E:\\deskTop\\multi_omics\\manu\\多组学平台\\article\\case study2-analysis\\BLCA_response_processed.csv")
fpkm <- read.table(
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


# # 行名为空 删除此行 一审增加
# if(any(is.na(fpkm[,1]))) {
#   # 方案1：删除基因名为NA的行
#   fpkm <- fpkm[!is.na(fpkm[,1]), ]
#   # cat("已删除基因名为NA的行\n")
#   cat("The row with the gene name NA has been deleted\n")
# }

# # 如果有重复的行名，使用 make.unique 一审增加
# if(any(duplicated(fpkm[,1]))) {
#   rownames(fpkm) <- make.unique(as.character(fpkm[,1]))  # 重复值加后缀gene.1
#   fpkm <- fpkm[, -1]  # 删除原始第一列
# }
# 先读取首列为普通列，再进行基因名清洗与去重（避免 read.table(row.names=1) 因重复行名直接报错）
gene_names <- trimws(as.character(fpkm[[1]]))
valid_gene <- !(is.na(gene_names) | gene_names == "")
if (any(!valid_gene)) {
  fpkm <- fpkm[valid_gene, , drop = FALSE]
  gene_names <- gene_names[valid_gene]
  cat("Rows with empty gene names have been removed\n")
}
if (any(duplicated(gene_names))) {
  cat("Duplicate gene names detected; keeping first occurrence only\n")
  keep_idx <- !duplicated(gene_names)
  fpkm <- fpkm[keep_idx, , drop = FALSE]
  gene_names <- gene_names[keep_idx]
}
rownames(fpkm) <- gene_names
fpkm <- fpkm[, -1, drop = FALSE]

# 对齐样本：确保表达矩阵列与分组文件 Sample 一一对应（且维度匹配）
colnames(fpkm) <- trimws(colnames(fpkm))
if ("Sample" %in% colnames(group_info)) {
  group_info$Sample <- trimws(as.character(group_info$Sample))
}
if (!("Sample" %in% colnames(group_info)) || !("Group" %in% colnames(group_info))) {
  stop("Group info file must contain columns: Sample and Group")
}

expr_samples <- colnames(fpkm)
info_samples <- as.character(group_info$Sample)
common_samples <- intersect(expr_samples, info_samples)
if (length(common_samples) < 2) {
  stop("No matched samples between expression file header and group info file Sample column")
}

# 以表达矩阵列顺序为准进行重排，避免顺序错乱；并丢弃不匹配列
fpkm <- fpkm[, common_samples, drop = FALSE]
group_info <- group_info[match(common_samples, group_info$Sample), , drop = FALSE]

# 确保表达矩阵为数值型
fpkm[] <- lapply(fpkm, function(x) as.numeric(as.character(x)))

# 空值处理 K近邻插补  一审增加
if(any(is.na(fpkm))) {
  # K近邻插补
  cat("begin KNN imputation\n")
  library(impute)
  fpkm <- impute.knn(as.matrix(fpkm))$data
}


log_fpkm <- log2(fpkm + 1) #log化处理
log_fpkm[log_fpkm == -Inf] = 0 #将log化后的负无穷值替换为0

# 删除表达量为 0 的基因（保持 log_fpkm 与 fpkm 一致）
keep_gene <- which(rowSums(fpkm) != 0)
fpkm <- fpkm[keep_gene, , drop = FALSE]
log_fpkm <- log_fpkm[keep_gene, , drop = FALSE]


# construct design matrix
# 1 代表正样本，复发 Recurrence，treament
# 0 代表负样本，正常 Non-Recurrence，control
groups <- factor(group_info$Group, levels = c("Control", "Treatment"))
design <- model.matrix(~0 + groups)
colnames(design) <- levels(groups)

# 再次确保维度匹配（避免隐藏的 read.table(fill=TRUE) 扩列问题）
if (ncol(log_fpkm) != nrow(design)) {
  stop(paste0(
    "Design matrix rows (", nrow(design),
    ") do not match expression columns (", ncol(log_fpkm), ")."
  ))
}

# run linear model
fit <- lmFit(log_fpkm, design)
contrasts <- makeContrasts(Treatment - Control, levels = design)
fit2 <- contrasts.fit(fit, contrasts)
# fit2 <- eBayes(fit2)
fit2 <- eBayes(fit2, trend=TRUE)  # trend=TRUE是新加的。https://www.zhihu.com/question/445830860中的limma用户手册15.4章节

# 提取差异分析结果
diff_results <- topTable(fit2, coef = 1, number = Inf, adjust.method = opt$correction)


# 修改列名
# P.Value -> pvalue
# adj.P.Val -> padj
# 第一列 -> gene
diff_results <- dplyr::rename(diff_results, pvalue = P.Value, padj = adj.P.Val)
gene <- rownames(diff_results)
diff_results <- cbind(gene,diff_results)
#对表格排序，按 padj 值升序排序，相同 padj 值下继续按 log2FC 降序排序
diff_results <- diff_results[order(diff_results$padj, diff_results$logFC, decreasing = c(FALSE, TRUE)), ]
# 保存结果
# filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/limma_results.txt", sep="")
# write.table(diff_results, filename, row.names = FALSE, sep='\t')  # 待实现表格分页展示


# 筛选差异基因
#log2FC≥1 & padj<0.01 标识 up，代表显著上调的基因
#log2FC≤-1 & padj<0.01 标识 down，代表显著下调的基因
#其余标识 none，代表非差异的基因
diff_results[which(diff_results$logFC >= fc_thr & diff_results$padj < padj_thr),'sig'] <- 'up'
diff_results[which(diff_results$logFC <= -fc_thr & diff_results$padj < padj_thr),'sig'] <- 'down'
diff_results[which(abs(diff_results$logFC) <= fc_thr | diff_results$padj >= padj_thr),'sig'] <- 'none'

#输出选择的差异基因总表
res1_select <- subset(diff_results, sig %in% c('up', 'down'))
filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/select_all.txt", sep="")
write.table(res1_select, file = filename, row.names = FALSE, sep='\t', quote = FALSE)  # 所有上下调差异基因。能不能实现根据条件筛选？下拉框up down all

#根据 up 和 down 分开输出
res1_up <- subset(diff_results, sig == 'up')
res1_down <- subset(diff_results, sig == 'down')

filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/select_up.txt", sep="")
write.table(res1_up, file = filename, row.names = FALSE, sep='\t', quote = FALSE)  # 所有显著上调差异基因
filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/select_down.txt", sep="")
write.table(res1_down, file = filename,  row.names = FALSE, sep='\t', quote = FALSE)  # 所有显著下调差异基因


# 画图
# 火山图
library(ggplot2)

p1 <- ggplot(diff_results, aes(x = logFC, y = -log10(padj))) + 
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

  geom_point(data = diff_results, shape = 21, color = "black", alpha = 0.1, size = 1.2, stroke = 0.7, fill = "grey60") +
  scale_x_continuous(limits = c(floor(sort(res1_down$logFC)[1]), ceiling(max(res1_up$logFC)))) +
  
  labs(x = expression(paste(log[2],"FC",sep="")), y = expression(paste(-log[10]," adj.p-value",sep=""))) + # y轴：-log10(genes$padj)
  theme_classic(base_size = 15) + 
  theme (legend.position = "none")

result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/volcano", sep="")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width = 7.5, height = 6)
}


# 差异基因聚类热图df_cluster_heatmap
# https://zhuanlan.zhihu.com/p/531957349
# 在原表达矩阵中找到差异表达基因
library(ComplexHeatmap)
# 这里使用 log_fpkm 作为表达矩阵（此前脚本里 counts 未定义会直接报错）
counts <- as.matrix(log_fpkm)
df <- counts[intersect(rownames(counts), rownames(res1_select)), , drop = FALSE]
df2<- as.matrix(df)  
col_annotation <- group_info                                               
rownames(col_annotation) <- col_annotation[,1] ## 第一列转换为行名
col_annotation <- col_annotation[,-1,drop=FALSE]  # 删除第一列 并保持为data frame

if (nrow(df2) < 2 || ncol(df2) < 2) {
  cat("No enough differential genes for cluster heatmap. Generate a blank placeholder figure.\n")

  blank <- ggplot() +
    theme_void() +
    annotate("text", x = 0, y = 0, label = "No differential genes", size = 8, color = "grey40") +
    xlim(-1, 1) + ylim(-1, 1)

  result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/df_cluster_heatmap", sep="")
  for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
    ggsave(paste(result_path, dev, sep = "."), blank, device = dev, width = 20, height = 20)
  }
} else {
  p1 <- pheatmap(df2,
                  column_split = as.factor(group_info$Group), ####分开热图
                  color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
                  # breaks = seq(floor(min(df2)), ceiling(max(df2)), length.out = 256),  # 设置颜色断点
                  clustering_distance_rows = "euclidean",
                  clustering_distance_cols = "euclidean",
                  show_colnames = T,
                  show_rownames = T,
                  annotation_col = col_annotation,
                  annotation_colors = list(Group=c(Control='#cfc6fe',Treatment='#CCDFF1')),
                  fontsize = 20,
                  fontsize_col =20,  
                  heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                              legend_width = 0.2),  # 设置图例宽度
                  scale = "row")  # 已进行了标准化，所以这里不再缩放
  
  result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/df_cluster_heatmap", sep="")
  for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
    ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width=20, height=20)
  }
}
