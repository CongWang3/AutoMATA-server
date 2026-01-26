# https://zhuanlan.zhihu.com/p/439002078

library("DESeq2")
library("ggplot2")
library("DEFormats")
library("dplyr")

##1.读入我们前面整理出的肿瘤和正常样本COUNT矩阵文件
normal <- read.csv("D:/wamp/www/multi_omics_own/download_data/Jobs/df_cluster_heatmap_case1/COAD_normal_matrix.csv",header = T, row.names = 1)
tumor <- read.csv("D:/wamp/www/multi_omics_own/download_data/Jobs/df_cluster_heatmap_case1/COAD_tumor_matrix.csv",header = T, row.names = 1)
#这里因为TCGA中结直肠癌的tumor样本有476个，而normal样只有41个。
#样本数差异过大可能对差异表达分析结果有影响，所以这里我只取40个tumor样本。
tumor <- tumor[1:40]
#合并
data <- merge(tumor,normal, by = "row.names", all = TRUE)
rownames(data) <- data$Row.names
data <- data[-1]

##数据预处理
#取值0值：移除那些在大于20%的样本中表达量为0的基因。
zero_counts <- apply(data == 0, 1, sum)
data <- data[-which(zero_counts>ncol(data)*0.2),]
#data <- data[-which(zero_counts>0),]  #仅保留那些在所有样本中都表达的基因

# 构建分组矩阵
group_list <- c(rep('tumor',ncol(tumor)),rep('normal',ncol(normal)))
condition <- factor(group_list)
coldata <- data.frame(row.names = colnames(data), condition)
View(coldata)

# 制作dds对象，构建差异基因分析所需的数据格式
dds <- DESeqDataSetFromMatrix(countData = data, colData = coldata, design = ~ condition)

# 4.进行差异分析
dds <- DESeq(dds)


df <- read.csv("D:/wamp/www/multi_omics_own/download_data/Jobs/df_cluster_heatmap_case1/deg_df.csv", header = T)
head(df)
df02 <- as.character(df$gene_name)  # 差异基因的名称
## 标准化(标准化Counts值) 
vsd <- vst(dds, blind = FALSE)
normalizeExp <- assay(vsd)
## 
## 差异基因的Count
diff_expr <- normalizeExp[df02,]
head(diff_expr)

write.csv(diff_expr, "D:/wamp/www/multi_omics_own/download_data/Jobs/df_cluster_heatmap_case1/df_count_normalized.csv")
