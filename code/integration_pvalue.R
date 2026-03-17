# merge P-values from different sources using directional and non-directional methods

library(optparse)
library(ActivePathways)
library(dplyr)

# 选择上传几个组学：2、3（转录组、蛋白质组、表型组、基因组？） 设置上传3个组学文件
# 注意：上传的组学文件列名必须有pvalue，如果选择方法（Strube_directional、Stouffer_directional、DPM、Fisher_directional）必须包含logFC列, constraints_vector = c(1,1,-1
# method有很多种，用户可选择某一个方法，或者选择None（拼接pvalue）。
# 输出：merge_p_values方法的结果文件merged
# pvalue空值设置为1，logFC空值设置为0
# Strube_directional、Stouffer_directional、DPM、Fisher_directional方法需要正负方向，所以需要正负方向的logFC

# options list for parser options
option_list <- list(
    make_option(c("-a","--omics_1_file"), type="character", default="", dest="omics_1_file"),
    make_option(c("-b","--omics_2_file"), type="character", default="", dest="omics_2_file"),
    make_option(c("-c","--omics_3_file"), type="character", default="", dest="omics_3_file"),
    make_option(c("-d","--method"), type="character", default="Stouffer_directional", help="This argument defines method to merge p-values: Fisher, Fisher_directional, Brown, DPM, Stouffer, Stouffer_directional, Strube, Strube_directional, or None", dest="method"),
    make_option(c("-j", "--jobID"), type="character", action="store", default="omics_integration" ,help="This argument is jobID"),
    make_option(c("-e","--output_file"), type="character", default="",help="",dest="output_file")
)

# get the parse information and assign to groups in the opt variable
opt = parse_args(OptionParser(usage = "This Script is to conduct multi omics integration by merging pvalues using different methods", option_list=option_list))

# 注意：这里不再重写 omics_1_file / omics_2_file / omics_3_file / output_file，
# 而是直接使用命令行传入的参数，便于在 FastAPI 环境中通过绝对路径调用。



# load the dfs
gene_expression = read.csv(opt$omics_1_file, sep='\t', row.names=1, quote = "", comment.char = "")
protein_expression = read.csv(opt$omics_2_file, sep='\t', row.names=1, quote = "", comment.char = "")
methylation = read.csv(opt$omics_3_file, sep='\t', row.names=1, quote = "", comment.char = "")


# Identify common row names across all data frames
common_rows <- Reduce(intersect, list(rownames(gene_expression), rownames(protein_expression), rownames(methylation)))

# subset to common_rows
gene_expression = gene_expression[common_rows,]
protein_expression = protein_expression[common_rows,]
methylation = methylation[common_rows,]

# separate into p_value and fold_change dfs
# pval_df = gene_expression[,'pvalue',drop=FALSE]
pval_df = gene_expression[,'pvalue',drop=FALSE]  # 改为文件中的列名
colnames(pval_df) = 'omics1'
pval_df$omics2 = protein_expression$pvalue
pval_df$omics3 = methylation$pvalue


# 空值处理
pval_df[is.na(pval_df)] = 1

# merge pvals using method
if (opt$method == "Fisher" || opt$method == "Brown" || opt$method == "Stouffer" || opt$method == "Strube") {
        merge_df = merge_p_values(as.matrix(pval_df), method=opt$method)
        # 设置列名
        merge_df = as.data.frame(merge_df)
        colnames(merge_df) = opt$method

}else if (opt$method == "Fisher_directional" || opt$method == "DPM" ||opt$method == "Stouffer_directional" || opt$method == "Strube_directional") {
        fc_df = gene_expression[,'logFC',drop=FALSE]  # 改为文件中的列名
        colnames(fc_df) = 'omics1'
        fc_df$omics2 = protein_expression$logFC
        fc_df$omics3 = methylation$logFC
        fc_df[is.na(fc_df)] = 0  # 空值处理
        merge_df = merge_p_values(as.matrix(pval_df), method=opt$method, scores_direction = as.matrix(fc_df), constraints_vector = c(1,1,-1))
        # 给 merge_df 设置列名
        merge_df = as.data.frame(merge_df)
        colnames(merge_df) = opt$method

}else{
        merge_df = pval_df
}

write.table(merge_df, file=opt$output_file, sep='\t', quote=FALSE)




