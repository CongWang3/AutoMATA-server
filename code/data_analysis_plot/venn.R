# invisible(local({
#   if (!"automata:paths" %in% search()) {
#     ca <- commandArgs(trailingOnly = FALSE)
#     ff <- ca[grepl("^--file=", ca)]
#     ap <- NA_character_
#     if (length(ff)) {
#       sp <- suppressWarnings(tryCatch(
#         normalizePath(sub("^--file=", "", ff[1]), winslash = "/", mustWork = TRUE),
#         error = function(e) NA_character_))
#       if (!is.na(sp) && nzchar(sp)) {
#         d <- dirname(sp)
#         for (i in 1:16) {
#           cand <- file.path(d, "automata_paths.R")
#           if (file.exists(cand)) { ap <- cand; break }
#           p <- dirname(d)
#           if (p == d) break
#           d <- p
#         }
#       }
#     }
#     if ((is.na(ap) || !nzchar(ap)) && nzchar(Sys.getenv("AUTOMATA_REPO_ROOT", unset = "")))
#       ap <- file.path(Sys.getenv("AUTOMATA_REPO_ROOT"), "code", "automata_paths.R")
#     if (!is.na(ap) && nzchar(ap) && file.exists(ap)) source(ap, local = FALSE) else
#       stop("找不到 code/automata_paths.R；请设置 AUTOMATA_REPO_ROOT。", call. = FALSE)
#   }
# }))
# rm(list=ls())
# setwd(automata_path_data_analysis_plot())
# library(VennDetail)
# library(ggplot2)
# library(dplyr)
# library(UpSetR) #Upset图（upset 包，适用样本数 2-7）
# library(VennDiagram) 
# # library(ggupset)
# library(optparse)  # 命令行

# # https://mp.weixin.qq.com/s/9oAx78QMZozOUGKe3plgCQ
# # https://mp.weixin.qq.com/s/_q74iQx4ksKWdHLNeeZJOA
# # https://www.bioladder.cn/R/chapter/Upset.html

# # 有问题！！upset图不能保存！！！！

# # 参数
# option_list <- list(
#   make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
#   make_option(c("-j", "--jobID"), type="character", action="store", help="This argument is jobID"),
#   make_option(c("-t", "--type"), type="character", default="venn", action="store", help="This argument is type of plot")
# )
# opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw Venn Plot!"))
# opt$input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt"))


# type <- opt$type # 可选"venn", "vennpie", 这俩不行！"upset", "barplot"
# # any_num <- 1 # venn饼图要使用的参数，vennpie，确定要显示在组数中的子集（1，仅包含在一个组中的子集）

# # VennDetail可以处理大于5维的数据
# # 读取数据
# gene_dataset <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)

# # 得到列数, 循环遍历, 删除空数据（"" / NA / 纯空白）
# final_list <- list()
# for (col_idx in 1:ncol(gene_dataset)){
#     print(col_idx)
#     gene_list <- gene_dataset[, col_idx]
#     new_list <- character()
#     for (row_idx in 1:length(gene_list)){
#         raw_val <- gene_list[row_idx]
#         if (is.na(raw_val)) next
#         gene_name <- trimws(as.character(raw_val))
#         if (!nzchar(gene_name)) next
#         new_list <- append(new_list, gene_name)
#     }
#     print(new_list)
#     final_list <- append(final_list, list(new_list))
# }

# # 画出Venn图
# ven <- venndetail(final_list)



# result_path <- automata_job_file(opt$jobID, "result/venn")

# save_base_plot <- function(dev, draw_fn, width = 8, height = 8, dpi = 100) {
#     out_file <- paste(result_path, dev, sep = ".")
#     tryCatch({
#         if (dev == "pdf") {
#             pdf(out_file, width = width, height = height, bg = "white")
#         } else if (dev == "jpeg") {
#             jpeg(out_file, width = width * dpi, height = height * dpi, res = dpi, bg = "white")
#         } else if (dev == "tiff") {
#             tiff(out_file, width = width * dpi, height = height * dpi, res = dpi, bg = "white")
#         } else if (dev == "png") {
#             png(out_file, width = width * dpi, height = height * dpi, res = dpi, bg = "white")
#         } else if (dev == "bmp") {
#             bmp(out_file, width = width * dpi, height = height * dpi, res = dpi, bg = "white")
#         } else if (dev == "svg") {
#             svg(out_file, width = width, height = height, bg = "white")
#         } else {
#             stop(paste("unsupported device:", dev))
#         }
#         draw_fn()
#         dev.off()
#         message("saved: ", out_file)
#         TRUE
#     }, error = function(e) {
#         # 单个格式失败不影响其它格式，避免任务整体失败
#         if (dev.cur() > 1) {
#             try(dev.off(), silent = TRUE)
#         }
#         warning(paste("save failed for", dev, ":", conditionMessage(e)))
#         FALSE
#     })
# }

# if (type=="venn"){
#     # 传统venn图
#     draw_venn <- function() {
#         plot(ven, type="venn", col="black", cat.cex=ncol(gene_dataset), alpha=0.5, cex=3)
#     }
#     for (dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")) {
#         save_base_plot(dev, draw_venn, width = 8, height = 8)
#     }
# }else if (type=="vennpie"){
#     # Venn饼图
#     draw_vennpie <- function() {
#         plot(ven, type="vennpie")
#     }
#     for (dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")) {
#         save_base_plot(dev, draw_vennpie, width = 8, height = 8)
#     }
# }else if (type=="barplot") {
#     # barplot
#     p1 <- dplot(ven, order = TRUE, textsize = 4)
#     for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
#         tryCatch({
#             ggsave(
#                 paste(result_path, dev, sep = "."),
#                 p1,
#                 device = dev,
#                 width = 10,
#                 height = 8,
#                 bg = "white"
#             )
#         }, error = function(e) {
#             warning(paste("save failed for", dev, ":", conditionMessage(e)))
#         })

#     }
#     # ggsave(paste(".barplot",dev,sep="."), width = 10, height = 8, device = dev)
# }else{
#     # upset plot
#     plot(ven, type="upset",cat.cex=ncol(gene_dataset),cex=3)
#     dev.off()  # 关闭设备以保存文件
# }

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
library(VennDetail)
library(ggplot2)
library(dplyr)
library(UpSetR) #Upset图（upset 包，适用样本数 2-7）
library(VennDiagram) 
# library(ggupset)
library(optparse)  # 命令行

# https://mp.weixin.qq.com/s/9oAx78QMZozOUGKe3plgCQ
# https://mp.weixin.qq.com/s/_q74iQx4ksKWdHLNeeZJOA
# https://www.bioladder.cn/R/chapter/Upset.html

# 有问题！！upset图不能保存！！！！

# 参数
option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", action="store", help="This argument is jobID"),
  make_option(c("-t", "--type"), type="character", default="venn", action="store", help="This argument is type of plot")
)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw Venn Plot!"))
opt$input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt"))


type <- opt$type # 可选"venn", "vennpie", 这俩不行！"upset", "barplot"
# any_num <- 1 # venn饼图要使用的参数，vennpie，确定要显示在组数中的子集（1，仅包含在一个组中的子集）

# VennDetail可以处理大于5维的数据
# 读取数据
gene_dataset <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)

# 得到列数, 循环遍历, 删除空数据（"" / NA / 纯空白）
final_list <- list()
for (col_idx in 1:ncol(gene_dataset)){
    print(col_idx)
    gene_list <- gene_dataset[, col_idx]
    new_list <- character()
    for (row_idx in 1:length(gene_list)){
        raw_val <- gene_list[row_idx]
        if (is.na(raw_val)) next
        gene_name <- trimws(as.character(raw_val))
        if (!nzchar(gene_name)) next
        new_list <- append(new_list, gene_name)
    }
    print(new_list)
    final_list <- append(final_list, list(new_list))
}

# 给集合命名，避免在部分环境下出现空图
names(final_list) <- colnames(gene_dataset)

# 画出Venn图
ven <- venndetail(final_list)



result_path <- automata_job_file(opt$jobID, "result/venn")

# VennDetail::plot.Venn 在 filename=NULL 时返回 ggplot 对象；与 barplot 分支一致用 ggsave 保存各格式。
save_ggplot_all_formats <- function(p, result_path, width_in = 8, height_in = 8, dpi = 100) {
    for (dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")) {
        out_file <- paste(result_path, dev, sep = ".")
        tryCatch({
            ggsave(
                filename = out_file,
                plot = p,
                device = dev,
                width = width_in,
                height = height_in,
                dpi = dpi,
                bg = "white"
            )
            message("saved: ", out_file)
        }, error = function(e) {
            warning(paste("save failed for", dev, ":", conditionMessage(e)))
        })
    }
}

# 与 VennDetail 1.22.x 及更早版本中 setcolor() 的调色板一致（新版包默认调色已扩展，需显式传入才能对齐旧图）。
setcolor_bioc_legacy_1_22 <- function(x) {
    mycolor <- c(
        "#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C", "#FB9A99", "#E31A1C",
        "#1B9E77", "brown", "#7570B3", "#E7298A", "#7FC97F", "#A6761D",
        "#BEAED4", "#FDC086", "chartreuse1", "cyan3", "purple", "pink4",
        "cyan", "royalblue", "violet", "springgreen2", "gold3",
        "darkseagreen4", "#E5D8BD",
        "#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4",
        "#91D1C2", "#DC0000", "#7E6148", "#B09C85", "#008B45", "#631879",
        "#008280", "#BB0021", "#5F559B", "#A20056", "#808180", "#1B1919",
        "#374E55", "#DF8F44", "#00A1D5", "#B24745", "#79AF97", "#6A6599",
        "#80796B", "#0073C2", "#EFC000", "#868686", "#CD534C", "#7AA6DC",
        "#003C67", "#8F7700", "#3B3B3B", "#A73030", "#4A6990",
        "#00AFBB", "#FC4E07", "#9999FF", "#FF9326",
        "#984EA3", "#F781BF", "#B3B3B3",
        "#CCCCCC", "#666666", "#01665E", "#542788"
    )
    if (x < length(mycolor)) {
        res <- mycolor[seq_len(x)]
    } else {
        res <- c(mycolor, sample(colors(), x - length(mycolor), replace = FALSE))
    }
    res
}

# 与 VennDetail::vennpie 内部一致地得到 plot 实际使用的 subset_counts（顺序与名称须一致，否则
# show.number=TRUE 时会把 color 改名为「子集: 计数」，若多出不参与绘图的 @detail 名称会产生 NA 名，
# scale_fill_manual 对不上，几乎全部扇区退成 revcolor 的灰色）。
vennpie_subset_counts <- function(object, top = 31, min = 0, sep = "_") {
    result_wide <- result(object, wide = TRUE)
    filtered_details <- result_wide %>% dplyr::filter(SharedSets >= min) %>% dplyr::select(Detail)
    element_details <- as.vector(filtered_details[, 1])
    result_long <- result(object)
    filtered_subsets <- result_long %>% dplyr::filter(Detail %in% element_details) %>%
        dplyr::select(Subset)
    unique_subsets <- unique(as.vector(filtered_subsets[, 1]))
    subset_counts <- object@detail[unique_subsets]
    if (length(subset_counts) > top) {
        top_subsets <- names(sort(subset_counts, decreasing = TRUE))[seq_len(top)]
        subset_counts <- subset_counts[top_subsets]
    }
    subset_counts
}

if (type=="venn"){
    # 传统韦恩图：先取 ggplot 对象再 ggsave（与 VennDetail 内部、barplot 分支一致）
    p_venn <- plot(ven, type = "venn", col = "black", cat.cex = ncol(gene_dataset), alpha = 0.5, cex = 3)
    save_ggplot_all_formats(p_venn, result_path, width_in = 8, height_in = 8, dpi = 100)
}else if (type=="vennpie"){
    # 调色向量必须与 vennpie 内部 subset_counts 同名同集合（见 vennpie_subset_counts 注释）
    sc <- vennpie_subset_counts(ven)
    pie_color <- setcolor_bioc_legacy_1_22(length(sc))
    names(pie_color) <- names(sc)
    sim_renamed <- paste(names(pie_color), sc[names(pie_color)], sep = ": ")
    pie_color_scaled <- pie_color
    names(pie_color_scaled) <- sim_renamed
    p_pie <- plot(ven, type = "vennpie", color = pie_color, revcolor = "lightgrey")
    # ggplot2 >= 4.0：vennpie 内置 scale_fill_manual(命名向量) 在 coord_polar+堆叠柱中只映射 1 类，其余为 revcolor；显式 breaks/limits 对齐。
    if (utils::packageVersion("ggplot2") >= "4.0.0") {
        rng <- sort(names(pie_color_scaled))
        p_pie <- p_pie + ggplot2::scale_fill_manual(
            values = pie_color_scaled[rng],
            breaks = rng,
            limits = rng,
            name = "Subsets"
        )
    }
    save_ggplot_all_formats(p_pie, result_path, width_in = 8, height_in = 8, dpi = 100)
}else if (type=="barplot") {
    # barplot
    p1 <- dplot(ven, order = TRUE, textsize = 4)
    for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
        tryCatch({
            ggsave(
                paste(result_path, dev, sep = "."),
                p1,
                device = dev,
                width = 10,
                height = 8,
                bg = "white"
            )
        }, error = function(e) {
            warning(paste("save failed for", dev, ":", conditionMessage(e)))
        })

    }
    # ggsave(paste(".barplot",dev,sep="."), width = 10, height = 8, device = dev)
}else{
    # upset plot
    plot(ven, type="upset",cat.cex=ncol(gene_dataset),cex=3)
    dev.off()  # 关闭设备以保存文件
}




# # 传统venn图
# plot(ven, type="venn", col="black", cat.cex=ncol(gene_dataset), alpha=0.5,cex=3)

# # Venn饼图
# plot(ven, type="vennpie")
# vennpie(ven,any=any_num,revcolor = "lightgrey")  # any=确定要显示在组数中的子集（1，仅包含在一个组中的子集）


# barplot
# dplot(ven, order = TRUE, textsize = 4)
# ggsave(".barplot.pdf", width = 20, height = 15)

# 解决问题： "upset",不能保存！
# upset plot
# plot(ven, type="upset",cat.cex=ncol(gene_dataset),cex=3)
# ggsave(".upset_ggsave.png", width = 8, height = 6, limitsize = FALSE)  # 只能存左边的条条




# # 保存为PNG格式
# png("plot_image.png", width = 800, height = 600)  # 设置文件名、宽度和高度
# plot(1:10, 1:10, main="Plot saved as PNG")        # 生成图像
# dev.off()  # 关闭设备以保存文件

# https://www.bioladder.cn/R/chapter/Upset.html
# # 加载R包，没有安装请先安装  install.packages("包名") 
# library(UpSetR)         #Upset图（upset 包，适用样本数 2-7）
# library(VennDiagram) 
# library(Cairo)         # 用于保存图片
# # 读取数据文件
# upset_dat <- read.delim('https://www.bioladder.cn/shiny/zyp/bioladder2/demoData/Venn/flower.txt')                      # 这里读取了网络上的demo数据，将此处换成你自己电脑里的文件
# upset_list <- list(upset_dat[,1], upset_dat[,2], upset_dat[,3], upset_dat[,4], upset_dat[,5], upset_dat[,6], upset_dat[,7])   # 制作Upset图搜所需要的列表文件
# names(upset_list) <- colnames(upset_dat[1:7])    # 把列名赋值给列表的key值

# #作图
# upset(fromList(upset_list),  # fromList一个函数，用于将列表转换为与UpSetR兼容的数据形式。
#       nsets = 100,     # 绘制的最大集合个数
#       nintersects = 40, #绘制的最大交集个数，NA则全部绘制
#       order.by = "freq", # 矩阵中的交点是如何排列的。 "freq"根据交集个数排序，"degree"根据
#       keep.order = F, # 保持设置与使用sets参数输入的顺序一致。默认值是FALSE，它根据集合的大小排序。
#       mb.ratio = c(0.6,0.4),   # 左侧和上方条形图的比例关系
#       text.scale = 2 # 文字标签的大小
#       )

# 保存图片 存不了啊啊啊啊啊啊

# 更多参数 ?upset查看

# # 查看交集详情,并导出结果
# inter <- get.venn.partitions(upset_list)
# for (i in 1:nrow(inter)) inter[i,'values'] <- paste(inter[[i,'..values..']], collapse = '|')
# inter <- subset(inter, select = -..values.. )
# inter <- subset(inter, select = -..set.. )
# write.table(inter, "result.csv", row.names = FALSE, sep = ',', quote = FALSE)
