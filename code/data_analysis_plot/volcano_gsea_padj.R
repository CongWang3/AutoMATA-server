rm(list=ls())
# 百度云存了此文件
# Load necessary libraries
library(ggplot2)
library(dplyr)
library(ggrepel)
getOption('timeout')  # 解决超时
options(timeout=100000)
library(optparse)  # 命令行
setwd("/xp/www/AutoMATA/code/data_analysis_plot")

# Note: 把-log10(padj)作为了-log10(adj.p-value), 我们进行了这个操作。保持dataset的logFC, padj,external_gene_name列名一致
# 虚线框内是top200的基因，蓝紫框内是筛选后的基因
# 由于TOP200/SIGNALING_UP/SIGNALING_UP/UP/DOWN这些注释会随着不同数据而浮动在不同位置。我设置相对位置也会因为值的大小变化幅度也不同，所以删掉TOP200/SIGNALING_UP/SIGNALING_UP注释，UP/DOWN可能会出现
# 记得把volcano_gsea的界面修改为：是否需要gmt（GSEA），需要的话则出现gmt选择框，并上传gmt文件
# 结直肠癌COAD的关键基因：CRC——https://m.medsci.cn/article/show_article.do?id=239683549293，COAD——https://pharmacol.csu.edu.cn/info/1029/1201.htm
# case2的BLCA，没有logFC < -0.5的数据，padj < 0.05的数据只有77条。没有满足padj < 0.05和|log2FC| > 1条件的数据，所以不能花火山图

# 参数
option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-g", "--gmt"), type="character", default="none", action="store", help="This argument is gmt file path"),  # 分为none和gmt, none表示没有GSEA分析
  make_option(c("-j", "--jobID"), type="character", default="volcano_case2_PAAD", action="store", help="This argument is jobID"),  # volcano_example  volcano_case1 volcano_case2_BLCA volcano_case2_PAAD
  make_option(c("-a", "--fc_thr"), type="double", default=0.1, action="store", help="This argument is the threshold of logFC"),  # 0.5  1   1.5   0.1  0.1
  make_option(c("-b", "--padj_thr"), type="double", default=0.2, action="store", help="This argument is the threshold of padj (adjusted p-value)"),  # 0.05  0.05  0.2  0.2
  make_option(c("-c", "--top"), type="integer", default=30, action="store", help="This parameter shows the higher-order gene that needs to be displayed"),  # 200  200  30  30
  make_option(c("-d", "--top_fc_thr"), type="double", default=0.09, action="store", help="This parameter is the threshold of logFC for the higher-order gene"),  # 0  2  0.09  0.09
  make_option(c("-e", "--top_padj_thr"), type="double", default=0.15, action="store", help="This parameter shows is the threshold of padj for the higher-order gene"),  # 0.01  0.01 0.15  0.15
  make_option(c("-f", "--gene_sig"), type="character", default="",action="store", help="This argument is showing marked genes")  # KRAS,FOSL1,MYC  B2M  CXCL3,CXCL8
  # BLCA: all_sig: CDK6,WNT5A,SFRP1,HPSE  up_genes：CDK6,HPSE
  # PAAD: all_sig: TGFB2,NKX3–1,TNFSF18,CDK6,WNT11,GCG,WNT7A,DKK1,KLK7,AXL,CTSV,CCND1  up_genes：DKK1,AXL,CTSV,CCND1,CDK6,NKX3-1
  # STAD: all_sig: CDKN2A,DLD,GLS,MTF1  up_genes：DKK1,CST6
)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw volcano with or without GSEA plot!"))
print("opt done")
# for webserver
opt$input <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/", opt$jobID, "_data.txt", sep = "")
print("read data done")
# 读取数据
data <- read.table(opt$input,header = TRUE, sep = "\t", check.names = FALSE)  # "\t"   ,
data <- na.omit(data)

# print(data$logFC)
# print(data$padj)
# exit(0)


#  处理为c("KRAS", "FOSL1", "MYC")
if (opt$gene_sig != ""){
  gene_sig <- unlist(strsplit(opt$gene_sig, ","))  # 特征基因. datasetz中需要标记的基因 
}else{
  gene_sig <- opt$gene_sig
}
# logFC和padj的阈值fc_thr和padj_thr
fc_thr <- opt$fc_thr  # 0.5
padj_thr <- opt$padj_thr  # 0.05
# 过滤前200个基因的阈值：-top的阈值top_fc_thr和top_padj_thr
top <- opt$top  # 200
if (top != 0){
  top_fc_thr <- opt$top_fc_thr  # 0
  top_padj_thr <- opt$top_padj_thr  # 0.01
}



# Extract gene sets
if (opt$gmt != "none"){
  opt$gmt <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/", opt$jobID, "_data2.gmt", sep = "")
  gmt <- readLines(opt$gmt)
  gene_set1 <- strsplit(gmt[1], "\t")[[1]][-c(1,2)]  # 取出行所在的元素，不要第一和第二个元素
  gene_set2 <- strsplit(gmt[2], "\t")[[1]][-c(1,2)]
  # 1. Filter data based on gene sets.
  # 选择基因子集 data_gene_set
  data_gene_set <- data %>%
  filter(gene %in% c(gene_set1, gene_set2, gene_sig)) %>%
  mutate(gene_set = case_when(
    gene %in% gene_set1 ~ "gene_set1",
    gene %in% gene_set2 ~ "gene_set2",
    gene %in% gene_sig ~ "gene_sig"
  ))
  # 基因子集data_gene_set外的其他基因集合
  data_other_genes <- data %>%
    filter(!gene %in% c(gene_set1, gene_set2, gene_sig))
} else{
  # 1. Filter data based on gene sets.
  # 选择基因子集 data_gene_set

    data_gene_set <- data %>%
    filter(gene %in% c(gene_sig)) %>%
    mutate(gene_set = case_when(
        gene %in% gene_sig ~ "gene_sig"
    ))
    # 基因子集data_gene_set外的其他基因集合
    data_other_genes <- data %>%
    filter(!gene %in% c(gene_sig))

}


# 2. Filter DOWN/UP DEGs （紫色/蓝色）
# 可修改（用户传入参数）：logFC和padj的阈值fc_thr和padj_thr
down_genes <- data %>% filter(padj < padj_thr, logFC < -fc_thr)
up_genes <- data %>% filter(padj < padj_thr, logFC > fc_thr)

# 3. Filter DOWN/UP && top200 DEGs  (虚线框)
# 可修改（用户传入参数）：前200个-top的阈值top_fc_thr和top_padj_thr （top阈值应该比正常阈值更严格）
if (top != 0){
  top_down200_genes <- data %>% 
  filter(padj < top_padj_thr, logFC < -top_fc_thr) %>% 
  arrange(logFC) %>% 
  head(top)

  top_up200_genes <- data %>% 
    filter(padj < top_padj_thr, logFC > top_fc_thr) %>% 
    arrange(desc(logFC)) %>% 
    head(top)
}



# volcano

p1 <- ggplot(data, aes(x = logFC, y = -log10(padj))) + 
  annotate("rect", xmin = sort(down_genes$logFC)[1], xmax = max(down_genes$logFC), 
    ymin = -log10(padj_thr), ymax = ifelse(-log10(min(down_genes$padj)) >= -log10(min(up_genes$padj)), -log10(min(down_genes$padj)), -log10(min(up_genes$padj))), fill = "#CCDFF1") + #文章颜色#E6E7FC DOWN
  annotate("rect", xmin = min(up_genes$logFC), xmax = max(up_genes$logFC), 
    ymin = -log10(padj_thr), ymax = ifelse(-log10(min(down_genes$padj)) >= -log10(min(up_genes$padj)), -log10(min(down_genes$padj)), -log10(min(up_genes$padj))), fill = "#cfc6fe") + #文章颜色#FDE7E9 #DCEABB  #ffe7ff(浅粉)  #cfc6fe(浅紫) UP
  
  annotate("text", x = (sort(down_genes$logFC)[1] + max(down_genes$logFC)) / 2, y = ifelse(-log10(min(down_genes$padj)) >= -log10(min(up_genes$padj)), -log10(min(down_genes$padj)), -log10(min(up_genes$padj)))+0.1, label = "DOWN", color = "#5EA7D3", size = 5, lineheight = 0.8, vjust = 0) + #文章颜色#857CD9  # DOWN label
  annotate("text", x = (min(up_genes$logFC) + max(up_genes$logFC)) / 2, y = ifelse(-log10(min(down_genes$padj)) >= -log10(min(up_genes$padj)), -log10(min(down_genes$padj)), -log10(min(up_genes$padj)))+0.1, label = "UP", color = "#b285b2", size = 5, lineheight = 0.8, vjust = 0) + #文章颜色#FF7D81  # UP label
  # annotate("text", x = sort(down_genes$logFC)[1]+1, y = -log10(min(up_genes$padj))-4, label = paste("Top", top, sep = " "), color = "black", size = 5) +  # Top 200 label
  # annotate("text", x = max(up_genes$logFC)-1, y = -log10(min(up_genes$padj))-4, label = paste("Top", top, sep = " "), color = "black", size = 5) +  # Top 200 label
  annotate("text", x = max(up_genes$logFC)+0.1, y = -log10(0.05), label = "α = 0.05", color = "#b285b2", size = 4.5) +


  geom_vline(xintercept = 0, color = "grey60", linewidth = 0.6) +
  geom_hline(yintercept = 0, color = "grey60", linewidth = 0.6) +
  geom_hline(yintercept = -log10(0.05), linetype = "dotted", color = "#b285b2", linewidth = 0.6) +  # α的线
  geom_point(data = data_other_genes, shape = 21, color = "black", alpha = 0.1, size = 1.2, stroke = 0.7) +
  geom_point(data = data_gene_set, aes(fill = gene_set), shape = 21, color = "black", size = 1.8, stroke = 0.8) +
  geom_label_repel(data = filter(data_gene_set, gene_set == "gene_sig"), aes(label = gene), size = 5, box.padding=unit(0.35, "lines"), segment.colour = "grey30") +
  # scale_fill_manual(values = c("gene_set2" = "#FFBF00", "gene_set1" = "#C6C6C6", "gene_sig" = "#07F1F9")) + # 黄色 灰色 蓝色 新删
  scale_fill_manual(values = c("gene_sig" = "#07F1F9")) +
  
  annotate("rect", xmin = min(top_up200_genes$logFC), xmax = max(top_up200_genes$logFC), ymin = -log10(top_padj_thr), ymax = -log10(min(top_up200_genes$padj)), fill = "transparent", linetype = ifelse(top==0, "blank", "dotted"), color = "black", linewidth = 0.6) +  # 矩形虚线方块
  annotate("rect", xmin = sort(top_down200_genes$logFC)[1], xmax = max(top_down200_genes$logFC), ymin = -log10(top_padj_thr), ymax = -log10(min(top_down200_genes$padj)), fill = "transparent", linetype = ifelse(top==0, "blank", "dotted"), color = "black", linewidth = 0.6) +
  

  # scale_x_continuous(limits = c(min(floor(min(up_genes$logFC)), floor(sort(down_genes$logFC)[1])), max(ceiling(max(up_genes$logFC)), ceiling(sort(down_genes$logFC))))) +
  scale_x_continuous(limits = c(floor(sort(down_genes$logFC)[1]), ceiling(max(up_genes$logFC)))) +
  
  labs(x = expression(paste(log[2],"FC",sep="")), y = expression(paste(-log[10]," adj.p-value",sep=""))) + # y轴：-log10(genes$padj)
  theme_classic(base_size = 15) + 
  theme (legend.position = "none")


if (opt$gmt == "none"){
  # 保存图片
  result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/volcano", sep="")
  for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
    ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width = 7.5, height = 6)
  }
} else {
# ——如果要加GSEA富集分析的话——
# add signature enrichment bar
p2 <- p1 + 
  # scale_y_continuous(limits = c(-2, 7), breaks = seq(0, 6, 2), expand = c(0, 0)) +
  scale_y_continuous(limits = c(-2, -log10(min(up_genes$padj))), expand = c(0, 0)) +
  geom_linerange(data = filter(data_gene_set, gene_set == "gene_set2"), aes(x = logFC, ymin = -1, ymax = -0.35), color = "#FFBF00", size = 0.5, linewidth = 0.1) +
  geom_linerange(data = filter(data_gene_set, gene_set == "gene_set1"), aes(x = logFC, ymin = -1.75, ymax = -1.1), color = "#C6C6C6", size = 0.5, linewidth = 0.1) + 
  scale_fill_manual(values = c("gene_set2" = "#FFBF00", "gene_set1" = "#C6C6C6", "gene_sig" = "#07F1F9")) + # 黄色 灰色 蓝色  新加
  annotate("text", x = -2.5, y = -0.7, label = "SIGNALING_UP", color = "#FFBF00", size = 4.5) +
  annotate("text", x = -2.5, y = -1.4, label = "SIGNALING_DN", color = "#C6C6C6", size = 4.5)


# 保存图片labelfdr
result_path <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID,"/result/volcano", sep="")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
  ggsave(paste(result_path, dev, sep = "."), p2, device = dev, width = 7.5, height = 6)
}

}


