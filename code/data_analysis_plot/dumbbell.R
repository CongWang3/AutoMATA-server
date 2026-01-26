rm(list=ls())
# 百度云存了此文件
# Load necessary libraries
library(ggplot2)
library(dplyr)
library(patchwork)
library(optparse)  # 命令行

option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", action="store", help="This argument is jobID"),
  make_option(c("-a", "--x_label"), type="character", default="", action="store", help="This argument is the y label of dumbbell plot"),
  make_option(c("-b", "--mark_fams"), type="character", default="", action="store", help="This argument is term that will be marked")

)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw dumbbell plot!"))
opt$input <- paste("D:/wamp/www/multi_omics_own/download_data/Jobs/", opt$jobID, "/", opt$jobID, "_data.txt", sep = "")

x_label <- opt$x_label  # dumbbell 和 dumbbell_stacked_bar需要的y轴标签
if (opt$mark_fams != ""){
  mark_fams <- unlist(strsplit(opt$mark_fams, ","))  # 需要标记的基因家族 c("Notothenioid", "Sebastidae", "Liparidae", "Zoarcidae", "Pleuronectidae")
}else{
  mark_fams <- opt$mark_fams
  }

data_dumbbell <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)
colnames(data_dumbbell) <- c("family", "observed_num", "expected_median", "expected_quartile0.05", "expected_quartile0.95")
# family sort according diff in dumbbell
# 按照observed_num-expected_median大小排序
data_dumbbell_sorted <- data_dumbbell %>%
arrange(observed_num-expected_median) %>%
mutate(col = case_when(
        observed_num >= expected_quartile0.05 & observed_num <= expected_quartile0.95 ~ "Within expectation",
        observed_num > expected_quartile0.95 ~ "Above expectation",
        observed_num < expected_quartile0.05 ~ "Below expectation"))

order <- data_dumbbell_sorted$family

# dumbbell plot
data_dumbbell_sorted$family <- factor(data_dumbbell_sorted$family, levels = order)
famcol <- ifelse(levels(as.factor(data_dumbbell_sorted$family)) %in% mark_fams, "#F8766D", "grey30")

p2 <- ggplot(data_dumbbell_sorted, aes(x = family, y = observed_num)) +
geom_segment(aes(x = family, xend = family,   # 灰色粗线条
                y = expected_quartile0.05, yend = expected_quartile0.95),
            col = "grey90", lwd = 3, lineend = "round") +
geom_segment(aes(x = family, xend = family, # 黑色细线条
                y = expected_median, yend = observed_num),
            col = "grey50", lwd = 0.6) +
geom_point(aes(x = family, y = expected_median),  # 白色圆点
            pch = 21, fill = "white", col = "grey50", size = 3, stroke = 1) +
geom_point(aes(col = factor(col, levels = c("Above expectation", "Within expectation", "Below expectation"))), size = 3.3) +  # 彩色圆点
coord_flip() +
ylab(x_label) +
#scale_color_manual(values = c("#00A08A", "grey40","#F2AD00")) + #文章中的颜色
scale_color_manual(values = c("#D65DB1", "grey40","#F2AD00")) +
theme_classic() +
theme(plot.margin = unit(c(0, 0.4, 0, 0), "cm"),
        panel.grid.major.x = element_blank(),
        panel.border = element_blank(),
        panel.grid.major.y = element_line(size = 0.4),
        # axis.text.y = element_blank(),
        axis.text.y = element_text(colour = famcol), 
        axis.line.x = element_line(size = 0.2),
        axis.line.y = element_blank(),
        axis.ticks.x = element_line(size = 0.1),
        axis.ticks.y = element_blank(),
        axis.title = element_text(size = 12),
        axis.title.y = element_blank(),
        legend.margin = margin(1, 5, 1, 1),
        legend.title = element_blank(),
        legend.text = element_text(size = 9, color = "grey30"),
        legend.key.spacing.y = unit(-0.15, 'cm'),
        legend.position = c(0.75, 0.15), 
        legend.background = element_rect(fill = 'white', color = "grey50",
                                        linewidth = 0.3))

# p2
# ggsave(paste("dumbbell", dev, sep="."), width = 5, height = 8, device = dev)

result_path <- paste("D:/wamp/www/multi_omics_own/download_data/Jobs/", opt$jobID,"/result/dumbbell", sep="")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p2, device = dev, width = 5, height = 8)

}