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
# 百度云存了此文件
# Load necessary libraries
library(ggplot2)
library(dplyr)
library(patchwork)
library(optparse)  # 命令行
# NOTE: data_dumbbell数据列数必须和dumbbell_example的列数一致
option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", action="store", help="This argument is jobID"),
  make_option(c("-a", "--x_label"), type="character", action="store", help="This argument is the y label of dumbbell plot"),
  make_option(c("-b", "--mark_fams"), type="character", default="", action="store", help="This argument is term that will be marked"),
  make_option(c("-c", "--data_bar"), type="character", default="", action="store", help="This argument is data path of bar plot")

)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw dumbbell with bar plot!"))
opt$input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data1.txt"))
opt$data_bar <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data2.txt"))

x_label <- opt$x_label  # dumbbell 和 dumbbell_stacked_bar需要的y轴标签
if (opt$mark_fams != ""){
  mark_fams <- unlist(strsplit(opt$mark_fams, ","))  # 需要标记的基因家族 c("Notothenioid", "Sebastidae", "Liparidae", "Zoarcidae", "Pleuronectidae")
}else{
  mark_fams <- opt$mark_fams
}

data_dumbbell <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)
data_bar <- read.table(opt$data_bar, header = TRUE, sep = "\t", check.names = FALSE)
colnames(data_bar) <- c("family", "tridepth", "nsp")  # 修改列名（这样就不用改代码了！不用改成这个：把列名修改为数字形式[,1]）
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

# 开始画图
barcolors <- c("#DDF7FF","#C0DBFF","#93AFF8" ,"#5E7DC2", "#2C5494")
# family sort in bar plot
data_bar$family <- factor(data_bar$family, levels = order)
data_bar_sorted <- data_bar[order(data_bar$family), ]

# set text colors
famcol <- ifelse(levels(as.factor(data_bar$family)) %in% mark_fams, "#F8766D", "grey30")  # mark_fams标记的颜色(柱状图左边字体颜色)

# stacked bar plot
p1 <- ggplot(data_bar_sorted, 
    aes(x = family, y = nsp, fill = factor(tridepth, levels = unique(data_bar[, 2])))) +
    geom_bar(position = "fill", stat = "identity", width = 0.7) +
    scale_fill_manual(values = barcolors[1:length(unique(data_bar[, 2]))]) +  # 自定义一列有多少种值就用多少个颜色
    coord_flip() +
    labs(x = NULL, y = NULL) + 
    theme_classic() +
    theme(axis.text.y = element_text(colour = famcol), 
            axis.text.x = element_blank(),
            axis.ticks = element_blank(),
            axis.line = element_blank(),
            legend.margin = margin(1, -8, 1, 1),
            legend.title = element_blank(),
            legend.text = element_text(size = 9, colour = 'grey30', margin = margin(r = 10)),
            legend.key.size = unit(0.45,'cm'),
            legend.key.spacing.x = unit(-1, 'cm'),
            legend.key.spacing.y = unit(0, 'cm'),
            legend.position = c(-0.8, -0.03), 
            legend.background = element_rect(fill = 'white', colour = 'grey50',
                                            linewidth = 0.3)) + 
    guides(fill = guide_legend(ncol = 2))


# dumbbell plot
data_dumbbell_sorted$family <- factor(data_dumbbell_sorted$family, levels = order)
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
                      axis.text.y = element_blank(),
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

p1 <- p1 + p2 + plot_layout(widths = c(1, 9))


result_path <- automata_job_file(opt$jobID, "result/dumbbell_bar")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width = 5, height = 6.2)

}