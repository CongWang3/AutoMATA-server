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
varechem <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)

# 可修改：用户传入参数
# dev <- "png"  # 可选"eps", "ps", "tex" (pictex), "pdf", "jpeg", "tiff", "png", "bmp", "svg" or "wmf" (windows only). 

# 网络相关性热图版本2, 没有Mantel's test
p1 <- qcorrplot(correlate(varechem), 
          grid_col = "grey50",
          grid_size = 0.25,  # 已改
          type = "upper", 
          diag = FALSE) +
  geom_square() +
  geom_mark(size = 4,
            only_mark = T,
            sig_level = c(0.05, 0.01, 0.001),
            sig_thres = 0.05,
            colour = 'white') +  
  scale_fill_gradientn(limits = c(-0.8,0.8),
                       breaks = seq(-0.8,0.8,0.4),
                       colors = rev(brewer.pal(11, "PiYG"))) +  # RdBu颜色调色盘已改
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







