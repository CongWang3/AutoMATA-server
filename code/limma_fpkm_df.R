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
setwd(automata_path_code())
library(limma)
library(dplyr)
library(vegan)
library(ggrepel)
library(ggpubr)
library(ellipse)
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
  automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt")),
  header = TRUE,
  sep = "\t",
  check.names = FALSE,
  stringsAsFactors = FALSE,
  fill = TRUE,
  comment.char = "",
  quote = ""
)
group_info <- read.table(automata_job_file(opt$jobID, paste0(opt$jobID, "_info.txt")), header = TRUE, sep = "\t", check.names = FALSE, fill = TRUE, comment.char = "")


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
filename <- automata_job_file(opt$jobID, "result/select_all.txt")
write.table(res1_select, file = filename, row.names = FALSE, sep='\t', quote = FALSE)  # 所有上下调差异基因。能不能实现根据条件筛选？下拉框up down all

#根据 up 和 down 分开输出
res1_up <- subset(diff_results, sig == 'up')
res1_down <- subset(diff_results, sig == 'down')

filename <- automata_job_file(opt$jobID, "result/select_up.txt")
write.table(res1_up, file = filename, row.names = FALSE, sep='\t', quote = FALSE)  # 所有显著上调差异基因
filename <- automata_job_file(opt$jobID, "result/select_down.txt")
write.table(res1_down, file = filename,  row.names = FALSE, sep='\t', quote = FALSE)  # 所有显著下调差异基因


# PCA（风格对齐 data_analysis_plot/pca.R）
print("Drawing PCA Plot")
tryCatch({
  # limma 分支使用 log_fpkm 进行样本层面的 PCA
  pca_input <- t(as.matrix(log_fpkm))  # 行=样本，列=基因
  storage.mode(pca_input) <- "numeric"
  # 与 pca.R 保持一致：缺失值替换为 0，并移除零方差特征，避免 rda 失败
  if (any(is.na(pca_input))) {
    pca_input[is.na(pca_input)] <- 0
  }
  keep_var <- apply(pca_input, 2, function(x) !all(is.na(x)) && sd(x, na.rm = TRUE) > 0)
  pca_input <- pca_input[, keep_var, drop = FALSE]
  if (ncol(pca_input) == 0) {
    stop("No valid features for PCA after filtering zero-variance columns")
  }
  if (nrow(pca_input) < 2) {
    stop("No enough samples for PCA")
  }

  # 尽量按样本名对齐分组信息（group_info 第一列通常是样本名）
  group_df <- group_info
  if (ncol(group_df) >= 1) {
    sample_col <- as.character(group_df[[1]])
    if (all(rownames(pca_input) %in% sample_col)) {
      idx <- match(rownames(pca_input), sample_col)
      group_df <- group_df[idx, , drop = FALSE]
    }
  }

  rda_result <- rda(pca_input, scale = TRUE)
  pca_summary <- summary(rda_result)
  pc1_Explained <- round(pca_summary$cont$importance[2, 1] * 100, 2)
  pc2_Explained <- round(pca_summary$cont$importance[2, 2] * 100, 2)

  coords <- data.frame(scores(rda_result, display = "sites", choices = c(1, 2)))
  coords$group <- factor(group_df$Group, levels = unique(group_df$Group))

  # 保持箭头风格，但避免变量过多导致图面不可读：取 loading 最大前 20 个
  var_all <- data.frame(scores(rda_result, display = "species", choices = c(1, 2)))
  var_all$func <- rownames(var_all)
  var_all$loading <- sqrt(var_all$PC1^2 + var_all$PC2^2)
  var <- head(var_all[order(var_all$loading, decreasing = TRUE), ], 20)

  group_levels <- levels(coords$group)
  n_groups <- length(group_levels)
  base_colors <- c(
    "#1F77B4FF", "#FF7F0EFF", "#2CA02CFF",
    "#9467BDFF", "#8C564BFF", "#E377C2FF",
    "#7F7F7FFF", "#BCBD22FF", "#17BECFFF"
  )
  if (n_groups <= length(base_colors)) {
    group_colors <- base_colors[seq_len(n_groups)]
  } else {
    group_colors <- grDevices::rainbow(n_groups)
  }
  names(group_colors) <- group_levels

  group_unique <- unique(coords$group)
  oval_list <- lapply(group_unique, function(g) {
    subset <- dplyr::filter(coords, group == g)
    if (nrow(subset) < 3) return(NULL)
    cov_data <- cov(subset[, c("PC1", "PC2")])
    if (any(!is.finite(cov_data))) return(NULL)
    mean_data <- colMeans(subset[, c("PC1", "PC2")])
    oval_point <- ellipse::ellipse(cov_data, centre = mean_data, level = 0.95)
    data.frame(Group = g, oval_point)
  })
  oval_list <- Filter(Negate(is.null), oval_list)
  oval_data <- if (length(oval_list) > 0) do.call(rbind, oval_list) else data.frame(Group = factor(), PC1 = numeric(), PC2 = numeric())
  if (nrow(oval_data) > 0) {
    if ("x" %in% colnames(oval_data)) colnames(oval_data)[colnames(oval_data) == "x"] <- "PC1"
    if ("y" %in% colnames(oval_data)) colnames(oval_data)[colnames(oval_data) == "y"] <- "PC2"
  }

  p_pca <- ggplot() +
    geom_point(data = coords, aes(x = PC1, y = PC2, fill = group), size = 3, color = "transparent", shape = 21) +
    geom_segment(data = var, aes(x = 0, y = 0, xend = -1.25 * PC1, yend = 1.25 * PC2),
                 arrow = arrow(angle = 22.5, length = unit(0.25, "cm"), type = "closed")) +
    geom_text_repel(data = var, aes(x = -1.275 * PC1, y = 1.275 * PC2, label = func), size = 3.8) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "grey") +
    geom_vline(xintercept = 0, linetype = "dashed", color = "grey") +
    geom_path(data = oval_data, aes(x = PC1, y = PC2, group = Group, color = Group), show.legend = FALSE, linetype = "dashed") +
    geom_polygon(data = oval_data, aes(x = PC1, y = PC2, group = Group, fill = Group), alpha = 0.2) +
    scale_color_manual(values = group_colors, breaks = group_levels) +
    scale_fill_manual(values = group_colors, breaks = group_levels) +
    labs(x = paste("PC1 (", pc1_Explained, "%)", sep = ""), y = paste("PC2 (", pc2_Explained, "%)", sep = "")) +
    scale_x_continuous(limits = c(min(coords$PC1) - 1.5, max(coords$PC1) + 1.5)) +
    scale_y_continuous(limits = c(min(coords$PC2) - 1.5, max(coords$PC2) + 1.9)) +
    theme_classic2() +
    theme(
      legend.title = element_blank(),
      legend.key.size = unit(35, "pt"),
      axis.line = element_line(color = "black"),
      axis.ticks = element_blank()
    )

  result_path <- automata_job_file(opt$jobID, "result/pca")
  for (dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")) {
    ggsave(paste(result_path, dev, sep = "."), p_pca, device = dev, width = 8.8, height = 6)
  }
}, error = function(e) {
  # PCA 作为附加结果，失败不阻断后续 volcano / heatmap
  message("PCA generation skipped: ", e$message)
})
print("Drawing PCA Plot End")


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

result_path <- automata_job_file(opt$jobID, "result/volcano")
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

  result_path <- automata_job_file(opt$jobID, "result/df_cluster_heatmap")
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
  
  result_path <- automata_job_file(opt$jobID, "result/df_cluster_heatmap")
  for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
    ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width=20, height=20)
  }
}
