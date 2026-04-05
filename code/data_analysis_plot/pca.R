# https://mp.weixin.qq.com/s/1XJ61hv0IilKcHdyp0VX7w
# 数据来源：https://onlinelibrary.wiley.com/doi/10.1002/imt2.187
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

library(ggplot2)    # 加载 ggplot2，用于绘图
library(vegan)      # 加载 vegan，用于生态学数据分析
library(dplyr)      # 加载 dplyr，用于数据处理
library(ggrepel)    # 加载 ggrepel，用于绘制避让标签
library(ggpubr)     # 加载 ggpubr，用于绘制多图
library(patchwork)  # 加载 patchwork，用于组合多个图形
library(optparse)  # 命令行

option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", action="store", help="This argument is jobID"),
  make_option(c("-c", "--confidence_level"), type="double", action="store", help="This argument is confidence level"),
  make_option(c("-b", "--boundary"), type="logical", action="store", help="This argument defines whether to add boundary plot"),
  make_option(c("-p", "--permanova"), type="logical", action="store", help="This argument defines whether to add PERMANOVA analysis"),
  make_option(c("-m", "--method"), type="character", default="bray", action="store", help="If permanova is TRUE, this argument is PERMANOVA method, can be 'manhattan', 'euclidean', 'canberra', 'clark', 'bray', 'kulczynski', 'jaccard', 'gower', 'altGower', 'morisita', 'horn', 'mountford', 'raup', 'binomial', 'chao', 'cao', 'mahalanobis', 'chisq', 'chord', 'hellinger', 'aitchison', or 'robust.aitchison'.")

)
print("This Script is to draw PCA!")
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw PCA!"))
opt$input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt"))


# 参数
confidence_level <- opt$confidence_level  # 置信水平
method <- opt$method          # 多变量方差分析 PERMANOVA 的方法，可选"manhattan", "euclidean", "canberra", "clark", "bray", "kulczynski", "jaccard", "gower", "altGower", "morisita", "horn", "mountford", "raup", "binomial", "chao", "cao", "mahalanobis", "chisq", "chord", "hellinger", "aitchison", or "robust.aitchison".
permanova <- opt$permanova           # 是否进行PERMANOVA分析
boundary <- opt$boundary                 # 要加边际图
dev <- "pdf" # 可选 "pdf", "jpeg", "tiff", "png", "bmp", "svg". 

# 添加显著性星号
get_stars <- function(p){
    if (is.na(p)) {  # 二审
      return("")
    }
    if (p <= 0.001) {
    return("***")
  } else if (p <= 0.01) {
    return("**")
  } else if (p <= 0.05) {
    return("*")
  } else {
    return("")
  }
}

# 1. 读取数据. 数据第一列为组别信息,列名为Group，其他数据类型均为数字, 列名不同
table_data <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)

# 数据验证：检查文件是否正确读取
if (nrow(table_data) == 0) {
    stop("错误：数据文件为空或格式不正确，请检查上传的文件")
}

if (ncol(table_data) < 2) {
    stop("错误：数据文件至少需要两列（组别列和至少一个数据列）")
}

# 检查第一列是否为组别信息
if (colnames(table_data)[1] != "Group") {
    warning("警告：第一列列名不是'Group'，但仍将其作为组别信息处理")
}

# 2. 主成分分析，并标准化, 删除组别信息进行pca
# res.pca <- PCA(table_data, graph = FALSE)  # res.pca$eig的转置==pca

# 提取数值列进行验证
data_cols <- dplyr::select(table_data, colnames(table_data)[-1])

# 检查是否有足够的数值数据进行 PCA
if (ncol(data_cols) == 0) {
    stop("错误：没有可用于 PCA 分析的数值数据列")
}

# 尝试转换为数值矩阵并检查
tryCatch({
    data_matrix <- as.matrix(data_cols)
    storage.mode(data_matrix) <- "numeric"
    
    # 检查是否有 NA 值
    if (any(is.na(data_matrix))) {
        na_count <- sum(is.na(data_matrix))
        warning(paste("警告：数据中包含", na_count, "个 NA 值，已替换为 0"))
        data_matrix[is.na(data_matrix)] <- 0
    }
    # 去掉“全 NA”或“标准差为 0”的列；
    data_matrix <- data_matrix[, apply(data_matrix, 2, function(x) {
      !all(is.na(x)) && sd(x, na.rm = TRUE) > 0
    }), drop = FALSE]
    
    if (ncol(data_matrix) == 0) {
        stop("错误：没有可用于 PCA 分析的数值数据列")
    }
    # 执行 PCA 分析（rda_result 保存原始对象，pca_summary 保存摘要用于提取解释度）
    rda_result <- rda(data_matrix, scale=T)
    pca_summary <- summary(rda_result)
}, error = function(e) {
    stop(paste("错误：PCA 分析失败 -", e$message, "\\n请检查数据格式是否正确（第一列为组别，其余列为数值型数据）"))
})
# 记录PC1和PC2的解释度
pc1_Explained <- round(pca_summary$cont$importance[2, 1]*100, 2)
pc2_Explained <- round(pca_summary$cont$importance[2, 2]*100, 2)


# 3. 提取每个样本在PC轴上的坐标以及各变量对PC轴的贡献度信息
# sites 改为 coords, species 改为 var，group 改为coords$group（对比源代码）
# coords 数据框存储每个样本的坐标
coords <- data.frame(scores(rda_result, display="sites", choices=c(1,2))) %>% mutate(group = table_data[[1]])
# 设置group组别为因子型变量，并定义顺序
coords$group <- factor(coords$group, levels = unique(table_data[,1]))
# var 数据框存储变量信息, which is colnames of table_data
var <- data.frame(scores(rda_result, display="species", choices=c(1,2))) %>% mutate(func = rownames(scores(rda_result, display="species")))
var$func <- factor(var$func, levels = rownames(scores(rda_result, display="species")), labels = rownames(scores(rda_result, display="species")))


# 4. PERMANOVA分析
# 比如，对宏基因组检测的物种丰度数据进行PCA/NMDS/PCoA降维可视化后，
# 不同组的样品之间存在一些重叠，那怎么判断这些组之间的样品构成是否存在显著差别呢？
# 需要用到PERMANOVA检验了，检验不同组的样品中心点是否重叠。
# 具体方法如下：
# 进行多变量方差分析 PERMANOVA. 检验这些group变量是否在物种组成差异上有显著性影响。
# method可选：manhattan", "euclidean", "canberra", "clark", "bray", "kulczynski", "jaccard", "gower", "altGower", "morisita", "horn", "mountford", "raup", "binomial", "chao", "cao", "mahalanobis", "chisq", "chord", "hellinger", "aitchison", or "robust.aitchison".
if (permanova){
    # nova <- adonis2(vegdist(dplyr::select(table_data, colnames(table_data)[-1]), method=method) ~ table_data[,1], data = table_data)  # 二审
    nova <- adonis2(vegdist(data_matrix, method = method) ~ table_data[,1], data = table_data)  # 二审
    R2 <- round(nova$R2[1], 3)
    Pr <- round(nova$`Pr(>F)`[1], 4)
    Pr_show <- ifelse(is.na(Pr), "NA", round(Pr, 4))  # 二审
    significance_stars <- get_stars(Pr)  # star
}
# if (permanova){
#     nova <- adonis2(vegdist(dplyr::select(table_data, colnames(table_data)[-1]), method=method) ~ Group, data = table_data)
#     R2 <- round(nova$R2[1], 3)
#     Pr <- round(nova$`Pr(>F)`[1], 4)
#     significance_stars <- get_stars(Pr)  # 显著性星号
# }



# 5. 计算样本在PC轴上的均值和协方差矩阵以确定置信椭圆大小和形状。
group_unique <- unique(coords$group)
oval_list <- lapply(group_unique, function(g){
  subset <- dplyr::filter(coords, group == g)
  # 至少需要 3 个点来画一个稳定的椭圆，否则跳过
  if (nrow(subset) < 3) {
    return(NULL)
  }
  cov_data <- cov(subset[, c("PC1", "PC2")])
  # 协方差矩阵不能含 NA，且必须是有限值
  if (any(!is.finite(cov_data))) {
    return(NULL)
  }
  mean_data <- colMeans(subset[, c("PC1", "PC2")])
  oval_point <- ellipse::ellipse(cov_data, centre = mean_data, level = confidence_level)
  data.frame(Group = g, oval_point)
})
oval_list <- Filter(Negate(is.null), oval_list)
oval_data <- if (length(oval_list) > 0) do.call(rbind, oval_list) else NULL

# ellipse::ellipse 返回的列名通常是 "x" 和 "y"，而后续作图使用的是 "PC1"/"PC2"。
# 如果有椭圆数据，则重命名列；如果没有椭圆数据，则构造一个空数据框，
# 以避免 ggplot 在映射 PC1/PC2 时找不到列名而报错。
if (!is.null(oval_data) && nrow(oval_data) > 0) {
  if ("x" %in% colnames(oval_data)) {
    colnames(oval_data)[colnames(oval_data) == "x"] <- "PC1"
  }
  if ("y" %in% colnames(oval_data)) {
    colnames(oval_data)[colnames(oval_data) == "y"] <- "PC2"
  }
} else {
  oval_data <- data.frame(Group = factor(), PC1 = numeric(), PC2 = numeric())
}
# group_unique <- unique(coords$group)
# # 对每个组别进行处理，生成每个组别的椭圆数据
# oval_data <- lapply(group_unique, function(g){
#     # 筛选出特定组的数据子集
#     subset <- dplyr::filter(coords, group == g)
#     # 计算特定组数据子集的PC1和PC2的均值
#     mean_data <- colMeans(subset[, c("PC1", "PC2")])
#     # 计算特定组数据子集的PC1和PC2的协方差矩阵
#     cov_data <- cov(subset[, c("PC1", "PC2")])
#     # 创建椭圆数据
#     oval_point <- ellipse::ellipse(cov_data, centre = mean_data, level = confidence_level)
#     data.frame(Group = g, oval_point)

# })
# # 合并所有组别的椭圆数据框成为一个数据框
# oval_data <- do.call(rbind, oval_data)



# 6. 绘制PCA图
# 6.1 箭头和置信椭圆的
# p1 <- ggplot()+
#   geom_point(data = coords, aes(x = PC1, y = PC2, fill = group), size = 3, color = "transparent", shape = 21)+  # 散点图
#   geom_segment(data = var, aes(x = 0, y = 0, xend = -1.25 * PC1, yend = 1.25 * PC2),  # 添加线段层
#                 arrow = arrow(angle = 22.5, length = unit(0.25, "cm"), type = "closed")) +  # 添加箭头
#   geom_text_repel(data = var, aes(x = -1.275 * PC1, y = 1.275 * PC2, label = func), size = 3.8) +  # 添加标签层(LeafC, AP等, 坐标轴标签)
#   geom_hline(yintercept = 0, linetype = "dashed", color = "grey") +  # 添加水平虚线
#   geom_vline(xintercept = 0, linetype = "dashed", color = "grey") +  # 添加垂直虚线
#   geom_path(data = oval_data, aes(x = PC1, y = PC2, group = Group, color = Group), show.legend = FALSE, linetype = "dashed") +  # 添加椭圆
#   geom_polygon(data = oval_data, aes(x = PC1, y = PC2, group = Group, fill = Group), alpha = 0.2) +  # 填充椭圆
#   scale_color_manual(values = c("#1F77B4FF", "#FF7F0EFF", "#2CA02CFF")) +  # 椭圆边缘线条颜色
#   scale_fill_manual(values = c("#1F77B4FF", "#FF7F0EFF", "#2CA02CFF")) +  # 椭圆填充颜色
# 修改：根据实际分组数动态生成颜色向量，避免分组数 > 固定颜色数时报错。 二审
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
  # 如果分组非常多，超出预设颜色数，用 rainbow 兜底，保证不会再因颜色数量不足报错
  group_colors <- grDevices::rainbow(n_groups)
}
names(group_colors) <- group_levels

p1 <- ggplot()+
  geom_point(data = coords, aes(x = PC1, y = PC2, fill = group), size = 3, color = "transparent", shape = 21)+
  geom_segment(data = var, aes(x = 0, y = 0, xend = -1.25 * PC1, yend = 1.25 * PC2),
                arrow = arrow(angle = 22.5, length = unit(0.25, "cm"), type = "closed")) + 
  geom_text_repel(data = var, aes(x = -1.275 * PC1, y = 1.275 * PC2, label = func), size = 3.8) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "grey") +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey") +
  geom_path(data = oval_data, aes(x = PC1, y = PC2, group = Group, color = Group), show.legend = FALSE, linetype = "dashed") +
  geom_polygon(data = oval_data, aes(x = PC1, y = PC2, group = Group, fill = Group), alpha = 0.2) + 
  scale_color_manual(values = group_colors, breaks = group_levels) +
  scale_fill_manual(values = group_colors, breaks = group_levels) +
  labs(x = paste("PC1 (", pc1_Explained, "%)",sep=""), y = paste("PC2 (", pc2_Explained, "%)",sep="")) +  # label
  scale_x_continuous(limits = c(min(coords$PC1)-1.5, max(coords$PC1)+1.5)) +  # 自定义 x 轴范围
  scale_y_continuous(limits = c(min(coords$PC2)-1.5, max(coords$PC2)+1.9)) +  # 自定义 y 轴范围
  theme_classic2() +  # 应用经典主题
  theme(legend.title = element_blank(),  # 设置图例标题为空
        legend.key.size = unit(35, "pt"),  # 设置图例大小
        axis.line = element_line(color = "black"),  # 设置坐标轴线颜色
        axis.ticks = element_blank())  # 隐藏坐标轴刻度

if (permanova){
    p1 <- p1 + annotate("text", label = paste0("PERMANOVA", "\n", "R^2", " = ", R2, "\n","p = ", Pr_show, significance_stars), x = -1.7, y = 2.5)  # 添加PERMANOVA结果
}

if (boundary){
    legend <- get_legend(p1) # 提取图例，后面有用
    legend <- as_ggplot(legend)
    p1 <- p1 + theme(legend.position = "none")  # 在 p1 的基础上移除图例位置

    # PC1轴边际分布曲线
    p2 <- ggplot(data = coords) +  # 创建一个基础的 ggplot 对象，并将数据源设为 coords 数据框
    geom_density(aes(x = PC1, fill=group), alpha = 0.2, 
                color = 'black', position = 'identity', show.legend = FALSE) +  # 添加密度图层，x轴为 PC1，根据 Position 变量填充颜色，设定透明度为 0.2，边界颜色为黑色，堆叠显示，隐藏图例
    # scale_fill_manual(values=c("#1F77B4FF","#FF7F0EFF","#2CA02CFF")) +  # 手动设置填充颜色，分别对应不同的位置（"Top"、"Middle"、"Bottom"）
    scale_fill_manual(values = group_colors, breaks = group_levels) +
    scale_x_continuous(limits = c(min(coords$PC1)-1.5, max(coords$PC1)+1.5)) +  # 自定义 x 轴的数值范围和PCA图里的x轴一致
    theme_classic() +  # 使用经典主题样式
    theme(legend.title = element_blank(),  # 隐藏图例标题
            axis.title = element_blank(),  # 隐藏坐标轴标题
            axis.text = element_blank(),  # 隐藏坐标轴文本
            axis.ticks = element_blank())  # 隐藏坐标轴刻度


    # PC2轴边际分布曲线
    p3 <- ggplot(data = coords) +  # 创建一个基础的 ggplot 对象，并将数据源设为 coords 数据框
    geom_density(aes(x = PC2, fill=group), alpha = 0.2, 
                color = 'black', position = 'identity', show.legend = FALSE) +  # 添加密度图层，x轴为 PC1，根据 Position 变量填充颜色，设定透明度为 0.2，边界颜色为黑色，堆叠显示，隐藏图例
    # scale_fill_manual(values=c("#1F77B4FF","#FF7F0EFF","#2CA02CFF")) +  # 手动设置填充颜色，分别对应不同的位置（"Top"、"Middle"、"Bottom"）
    scale_fill_manual(values = group_colors, breaks = group_levels) +
    scale_x_continuous(limits = c(min(coords$PC2)-1.5, max(coords$PC2)+1.9)) +  # 自定义 x 轴的数值范围和PCA图里的y轴一致
    theme_classic() +  # 使用经典主题样式
    theme(legend.title = element_blank(),  # 隐藏图例标题
            axis.title = element_blank(),  # 隐藏坐标轴标题
            axis.text = element_blank(),  # 隐藏坐标轴文本
            axis.ticks = element_blank()) +  # 隐藏坐标轴刻度
    coord_flip()  # 翻转坐标轴，使得密度图的方向从竖直变为水平


    # 自定义布局结构
    design <- "224
               113
               113"
    p1 <- p1 + p2 + p3 + legend + plot_layout(design = design)  # 组合三个图形

}


# 保存图片
result_path <- automata_job_file(opt$jobID, "result/result")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width = 8.8, height = 6)

}
