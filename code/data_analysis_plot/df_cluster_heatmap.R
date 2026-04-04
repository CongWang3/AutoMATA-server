# https://mp.weixin.qq.com/s/lz5tiBJ0GDs-t8htfdZFKg
# https://www.bilibili.com/video/BV16D421W7YF/?spm_id_from=333.337.search-card.all.click&vd_source=057f1ccccc12750f57f6d28b9c852bbd
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
# 工作目录
setwd(automata_path_data_analysis_plot())

# library(pheatmap)
library(ComplexHeatmap) 
library(ggplot2)
library(ggplotify)
library(optparse)  # 命令行

# 参数
# type <- "data_with_row_col" # data_with_col_annotation, data_with_row_annotation, only_data
# dev <- "pdf"  # 可选"eps", "ps", "pdf", "jpeg", "tiff", "png", "bmp", "svg"
# show_col_name <- F # 是否显示列名 T
# show_row_name <- T # 是否显示行名 T
# clustering_dis_row <- "euclidean" # 指定在对行进行聚类时使用欧几里得距离作为距离度量，可选"correlation", "euclidean", "maximum", "manhattan", "canberra", "binary" or "minkowski"
# clustering_dis_col <- "euclidean" # 聚类距离，可选"correlation", "euclidean", "maximum", "manhattan", "canberra", "binary" or "minkowski"
# scal <- "none" # 标准化 "row", "column" and "none". # 已进行了标准化，所以这里不再缩放
# group <- TRUE # 按照组别分开显示（type = data_with_col_annotation、data_with_row_col需要用到这个参数）（Tumor vs Normal，要求列注释文件的组别列名为group）

option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", default="df_cluster_example",action="store", help="This argument is jobID"),  # df_cluster_example df_cluster_heatmap_case1
  make_option(c("-a", "--type"), type="character", default="data_with_row_col", action="store", help="This argument is the type of figure"),  # data_with_row_col data_with_col_annotation
  make_option(c("-b", "--show_row_name"), type="logical", default=TRUE, action="store", help="This argument defines whether to show row name"),  # TRUE  FALSE 基因名
  make_option(c("-c", "--show_col_name"), type="logical", default=TRUE, action="store", help="This argument defines whether to show column name"),  # TRUE  FALSE 样本名
  make_option(c("-d", "--clustering_dis_row"), type="character", action="store", default="euclidean", help="This argument defines the method for clustering distance for rows"),
  make_option(c("-e", "--clustering_dis_col"), type="character", default="euclidean", action="store", help="This argument defines the method for clustering distance for columns"),
  make_option(c("-g", "--annotation_col_file"), default="", type="character", action="store", help="This argument is the path of column annotation file"),
  make_option(c("-f", "--annotation_row_file"), default="", type="character", action="store", help="This argument is the path of row annotation file"),
  make_option(c("-h", "--scal"), type="character", default="none", action="store", help="This argument defines whether to center and scale data"),
  make_option(c("-k", "--group"), type="logical", default=FALSE, action="store", help="This argument defines whether to display data by group")  # FALSE  TRUE
)

opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw Differential Gene Cluster Heatmap!", add_help_option=FALSE))
# 读取参数
type <- opt$type  # data_with_col_annotation, data_with_row_annotation, only_data, data_with_row_col
show_col_name <- opt$show_col_name # 是否显示列名 T
show_row_name <- opt$show_row_name # 是否显示行名 T
clustering_dis_row <- opt$clustering_dis_row # 指定在对行进行聚类时使用欧几里得距离作为距离度量，可选"correlation", "euclidean", "maximum", "manhattan", "canberra", "binary" or "minkowski"
clustering_dis_col <- opt$clustering_dis_col # 聚类距离，可选"correlation", "euclidean", "maximum", "manhattan", "canberra", "binary" or "minkowski"
scal <- opt$scal # 标准化 "row", "column" and "none". # 已进行了标准化，所以这里不再缩放
group <- opt$group # 按照组别分开显示（type = data_with_col_annotation、data_with_row_col需要用到这个参数）（Tumor vs Normal，要求列注释文件的组别列名为group）

opt$input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt"))
opt$annotation_col_file <- automata_job_file(opt$jobID, paste0(opt$jobID, "_col.txt"))
opt$annotation_row_file <- automata_job_file(opt$jobID, paste0(opt$jobID, "_row.txt"))

if (type == "only_data") {
    # 读取表达矩阵
    z_score_selected_expression <- read.table(opt$input, header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)  # \t
}else if (type == "data_with_col_annotation") {
    # 读取列注释
    annotation_col <- read.table(opt$annotation_col_file, header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)
    z_score_selected_expression <- read.table(opt$input, header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)
}else if (type == "data_with_row_annotation") {
    # 读取行注释
    annotation_row <- read.table(opt$annotation_row_file , header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)
    z_score_selected_expression <- read.table(opt$input, header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)
}else {
    annotation_row <- read.table(opt$annotation_row_file , header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)
    annotation_col <- read.table(opt$annotation_col_file, header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)
    z_score_selected_expression <- read.table(opt$input, header = TRUE, sep = "\t", quote="\"", fill=TRUE, comment.char="", row.names=1)

}
# exit(0)
if (type == "only_data") {
    # 用户可设置聚类距离方法、是否显示行列名、是否标准化
    p1 <- pheatmap(z_score_selected_expression,
            color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
            # breaks = seq(floor(min(z_score_selected_expression)), ceiling(max(z_score_selected_expression)), length.out = 256),  # 设置颜色断点
            clustering_distance_rows = clustering_dis_row,
            clustering_distance_cols = clustering_dis_col,
            show_colnames = show_col_name,
            show_rownames = show_row_name,
            fontsize = 20,
            fontsize_col =20,  
            heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                        legend_width = 0.2),  # 设置图例宽度
            scale = scal)  # 已进行了标准化，所以这里不再缩放
    p1 <- as.ggplot(p1)
    
}

# 添加列注释（在上面加一个热图
if (type == "data_with_col_annotation") {
    if (group == TRUE){
        # 按照组别分开
        p1 <- pheatmap(z_score_selected_expression,
                column_split = as.factor(annotation_col$group),####分开热图
                color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(floor(min(z_score_selected_expression)), ceiling(max(z_score_selected_expression)), length.out = 256),  # 设置颜色断点
                clustering_distance_rows = clustering_dis_row,
                clustering_distance_cols = clustering_dis_col,
                show_colnames = show_col_name,
                show_rownames = show_row_name,
                annotation_col = annotation_col,
                fontsize = 20,
                fontsize_col =20,  
                heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                            legend_width = 0.2),  # 设置图例宽度
                scale = scal)  # 已进行了标准化，所以这里不再缩放

    }else{
        # 不按照组别分开
        p1 <- pheatmap(z_score_selected_expression,
                # color = colorRampPalette(c("blue", "white", "red"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(-2, 2, length.out = 256),  # 设置颜色断点
                color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(floor(min(z_score_selected_expression)), ceiling(max(z_score_selected_expression)), length.out = 256),  # 设置颜色断点
                clustering_distance_rows = clustering_dis_row,
                clustering_distance_cols = clustering_dis_col,
                show_colnames = show_col_name,
                show_rownames = show_row_name,
                annotation_col = annotation_col,
                fontsize = 20,
                fontsize_col =20,  
                heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                            legend_width = 0.2),  # 设置图例宽度
                scale = scal)  # 已进行了标准化，所以这里不再缩放
    }
    p1 <- as.ggplot(p1)
}


# 添加行注释
if (type == "data_with_row_annotation") {
    p1 <- pheatmap(z_score_selected_expression,
            # color = colorRampPalette(c("blue", "white", "red"))(255),  # 使用蓝白红颜色映射
            # breaks = seq(-2, 2, length.out = 256),  # 设置颜色断点
            color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
            # breaks = seq(floor(min(z_score_selected_expression)), ceiling(max(z_score_selected_expression)), length.out = 256),  # 设置颜色断点
            clustering_distance_rows = clustering_dis_row,
            clustering_distance_cols = clustering_dis_col,
            show_colnames = show_col_name,
            show_rownames = show_row_name,
            annotation_row = annotation_row,
            fontsize = 20,
            fontsize_col =20,  
            heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                        legend_width = 0.2),  # 设置图例宽度
            scale = scal)  # 已进行了标准化，所以这里不再缩放
    p1 <- as.ggplot(p1)
 }

# 添加行列注释
if (type == "data_with_row_col") {
    if (group == TRUE){
        # 按照组别分开
        p1 <- pheatmap(z_score_selected_expression,
                column_split = as.factor(annotation_col$group),####分开热图
                # color = colorRampPalette(c("blue", "white", "red"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(-2, 2, length.out = 256),  # 设置颜色断点
                color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(floor(min(z_score_selected_expression)), ceiling(max(z_score_selected_expression)), length.out = 256),  # 设置颜色断点
                clustering_distance_rows = clustering_dis_row,
                clustering_distance_cols = clustering_dis_col,
                show_colnames = show_col_name,
                show_rownames = show_row_name,
                annotation_col = annotation_col,
                annotation_row = annotation_row,
                fontsize = 20,
                fontsize_col =20,  
                heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                            legend_width = 0.2),  # 设置图例宽度
                scale = scal)  # 已进行了标准化，所以这里不再缩放

    }else{
        # 不按照组别分开
        p1 <- pheatmap(z_score_selected_expression,
                # color = colorRampPalette(c("blue", "white", "red"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(-2, 2, length.out = 256),  # 设置颜色断点
                color = colorRampPalette(c("purple", "white", "yellow"))(255),  # 使用蓝白红颜色映射
                # breaks = seq(floor(min(z_score_selected_expression)), ceiling(max(z_score_selected_expression)), length.out = 256),  # 设置颜色断点
                clustering_distance_rows = clustering_dis_row,
                clustering_distance_cols = clustering_dis_col,
                show_colnames = show_col_name,
                show_rownames = show_row_name,
                annotation_col = annotation_col,
                annotation_row = annotation_row,
                fontsize = 20,
                fontsize_col =20,  
                heatmap_legend_param = list(legend_height = unit(4, "cm"),  # 设置图例高度
                                            legend_width = 0.2),  # 设置图例宽度
                scale = scal)  # 已进行了标准化，所以这里不再缩放
    }
    p1 <- as.ggplot(p1)
}

# 保存图片
result_path <- automata_job_file(opt$jobID, "result/df_cluster_heatmap")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width=20, height=20)  # 20, 20

}

