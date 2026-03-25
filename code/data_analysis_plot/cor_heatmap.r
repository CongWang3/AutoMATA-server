# This code is used to generate correlation heatmap for multi-omics data.
# https://mp.weixin.qq.com/s/LxfqLZ7423nl5kIPApNr0g
# 使用devtool安装github的包时，需要设置代理，重新开启一个R terminal，安装完成后再取消代理：https://zhuanlan.zhihu.com/p/636418854
rm(list=ls())
# 安装包的方法
# 1. install.packages("pkgload",type="binary")
# 2. install.packages("pkgload")
# 3. 下载source文件，在Rstudio中的GUI安装（没成功）

# “可修改”表示：用户可以根据自己的实际情况自己设置。
setwd("/xp/www/AutoMATA/code/data_analysis_plot")
library(linkET)
library(ggplot2)
library(RColorBrewer)
library(ggnewscale)
library(optparse)  # 命令行

option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", action="store", help="This argument is jobID")
)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw correlation heatmap!"))
opt$input <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/", opt$jobID, "_data.txt", sep = "")

# 加载数据
data <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)

# 二审 过滤非数值列（保留数值列）
data <- data[, sapply(data, is.numeric), drop = FALSE]

# # 网络相关性热图版本2, 没有Mantel's test
# p1 <- qcorrplot(correlate(data), 
#           grid_col = "grey50",
#           grid_size = 0.25,  # 已改
#           type = "upper", 
#           diag = FALSE) +
#   geom_square() +
#   geom_mark(size = 4,
#             only_mark = T,
#             sig_level = c(0.05, 0.01, 0.001),
#             sig_thres = 0.05,
#             colour = 'white') +  
#   scale_fill_gradientn(limits = c(-0.8,0.8),
#                        breaks = seq(-0.8,0.8,0.4),
#                        colors = rev(brewer.pal(11, "PiYG"))) +  # RdBu颜色调色盘已改
#   scale_size_manual(values = c(0.5, 1.5, 3)) +
#   guides(fill = guide_colorbar(title = "Pearson's r", 
#                 keyheight = unit(2.2, "cm"),
#                 keywidth = unit(0.5, "cm"),
#                 order = 3)) + 
#   theme(legend.box.spacing = unit(0, "pt"))
# 修改方案：根据“样本量”自动决定是否加显著性标记
#   - 若样本量较小（这里以行数 < 10 为例），只画基础热图，不加显著性标记，避免 geom_mark 报错；
#   - 若样本量较大（行数 >= 10），在基础热图上叠加显著性标记。
#   你可以根据需要调整这个阈值（例如改成 < 5 或 < 20）。
p_base <- qcorrplot(correlate(data), 
          grid_col = "grey50",
          grid_size = 0.25,
          type = "upper", 
          diag = FALSE) +
  geom_square()

# 样本量阈值：当前用 nrow(data) < 10 判定为“小样本”
sample_n <- nrow(data)

if (sample_n < 10) {
  # 小样本：只用基础热图 + 颜色/图例等设置
  p1 <- p_base
} else {
  # 大样本：基础热图 + 显著性标记
  p1 <- p_base +
    geom_mark(size = 4,
              only_mark = TRUE,
              sig_level = c(0.05, 0.01, 0.001),
              sig_thres = 0.05,
              colour = "white")
}

# 无论是否加显著性标记，统一叠加颜色渐变和图例等设置
p1 <- p1 +
  scale_fill_gradientn(limits = c(-1,1),  # scale_fill_gradientn
                       breaks = seq(-1,1,0.5),
                       colors = rev(brewer.pal(11, "PiYG"))) + # palette
  scale_size_manual(values = c(0.5, 1.5, 3)) +
  guides(fill = guide_colorbar(title = "Pearson's r", 
                keyheight = unit(2.2, "cm"),
                keywidth = unit(0.5, "cm"),
                order = 3)) + 
  theme(legend.box.spacing = unit(0, "pt"))



# 终端输入p1查看图片

result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/Corr_heatmap", sep="")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){  # 
  ggsave(paste(result_path, dev, sep = "."), plot=last_plot(), device = dev, width = 8.8, height = 6)

}







