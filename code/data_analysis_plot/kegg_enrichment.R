# https://www.bilibili.com/video/BV1T1421274d/?spm_id_from=333.788&vd_source=057f1ccccc12750f57f6d28b9c852bbd
# https://www.xiaohongshu.com/explore/64304200000000001203f68b?xsec_token=ABu9DTNwBViFC9nBMEouhsRYUsZzcXyqfcAprfi6LglTY=&xsec_source=pc_search&source=web_search_result_notes
# 工作目录
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
setwd(automata_path_data_analysis_plot())

# ===== KEGG 联网说明（默认 enrichKEGG use_internal_data=FALSE）=====
# clusterProfiler 通过 KEGGREST 访问 https://rest.kegg.jp ，典型包括：
#   - 物种通路 ID 列表（如 list/pathway/hsa）
#   - 基因 ID 与 KEGG 通路的对应关系（用于超几何检验的背景集与注释）
#   - 通路标题/描述等元数据
# 上述数据会随 KEGG 官网更新，与「本地 org.xx.eg.db 只做 Entrez 映射」是两层：后者离线，前者仍要联网。
# 离线替代：本脚本支持 use_internal_data=TRUE，使用 Bioconductor 包 KEGG.db 内置旧版快照，不访问外网（注释较旧，需安装 KEGG.db）。
# 启用方式：环境变量 KEGG_USE_INTERNAL_DATA=1，或增加命令行参数 --use_local_kegg（由后端传入）。

library(clusterProfiler)
if (!requireNamespace("org.Hs.eg.db", quietly=TRUE)) {
    message("Installing org.Hs.eg.db from Bioconductor (persistent cache: R_LIBS_USER)...")
    BiocManager::install("org.Hs.eg.db", ask=FALSE, update=FALSE)
}
library(org.Hs.eg.db)  # 人类的包 待修改为其他物种的包
library(dplyr)
library(GOplot)
library(DOSE)  # yulab.utils最新包下载https://cran.rstudio.com/web/packages/yulab.utils/index.html
library(ggplot2)
library(tidyr)
getOption('timeout')  # 解决超时
options(timeout=100000)

# --- 访问 rest.kegg.jp 时出现 SSL connect error 时的处理 ---
# 根因多为系统/OpenSSL 证书链或网络环境；建议先：apt-get install -y ca-certificates && update-ca-certificates
# 未设置 CURL_CA_BUNDLE 时，常见 Linux 默认 CA 包路径：
if (Sys.getenv("CURL_CA_BUNDLE", "") == "" && file.exists("/etc/ssl/certs/ca-certificates.crt")) {
  Sys.setenv(CURL_CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt")
}
# 仅内网/调试：设置环境变量 KEGG_INSECURE_SSL=1 关闭 HTTPS 校验（存在安全风险，勿用于公网暴露环境）
if (Sys.getenv("KEGG_INSECURE_SSL", "") == "1") {
  if (requireNamespace("httr", quietly = TRUE)) {
    httr::set_config(httr::config(ssl_verifypeer = FALSE, ssl_verifyhost = FALSE))
  }
}

library(yulab.utils)
library(optparse)  # 命令行

# 还未实现：选择特别感兴趣的KEGGID进行分析 报错Error in (function (cl, name, valueClass)  : 'result' is not a slot in class "data.frame"
# 还未实现：把图片下面的GO Term标签改为KEGG Pathway
# KEGG annotation包每半年更新一次。就用在线读取KEGG annotaion包吧。以防万一我下载了2024.10.8最新版KEGG annotaion包, 在f盘的chromeDownload文件夹下：KEGG.db_2.4.5.zip（win）,KEGG.db_2.4.5.tar.gz(package source)。

# NOTE: bubble图, 按照Count排列表格,按照GeneRatio排序呈现图片
# NOTE: 如果要使用chord或cluster，请确保上传的文件有列名为logFC的数值型数据，用来根据数值大小进行排序。同时保证第一列为gene name（symbol）

option_list <- list(
  make_option(c("-i", "--input"), type="character", default="", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character",default="20260328215654_b781fdb3", action="store", help="This argument is jobID"),
  make_option(c("-a", "--type"), type="character", default="chord", action="store", help="This argument is the type of figure"),
  make_option(c("-b", "--organism"), type="character", default="hsa", action="store", help="This argument defines organism"),
  make_option(c("-c", "--pvalue"), type="double", default=0.05, action="store", help="This argument defines pvalue threshold for GO enrichment analysis"),
  make_option(c("-d", "--qvalue"), type="double", default=0.05, action="store", help="This argument defines qvalue threshold for GO enrichment analysis"),
  make_option(c("-e", "--termNum"), type="integer", default=5, action="store", help="This argument is the number of terms for each ontology to be displayed"),
  make_option(c("-f", "--type_analysis"), default="none", type="character", action="store", help="up, down, all, or none. All analysis need this parameter, otherwise set it to none."),
  make_option(c("-g", "--adjust"), type="character", default="BH", action="store", help="This argument is the pvalue adjustment method for KEGG enrichment analysis, one of holm, hochberg, hommel, bonferroni, BH, BY, fdr, none"),  # 一审
  # 默认 online：clusterProfiler::enrichKEGG 经 KEGGREST 访问 rest.kegg.jp 获取最新通路注释（gene↔pathway、通路名称等）
  # local：use_internal_data=TRUE，改用 Bioconductor 包 KEGG.db 内置快照，不联网；注释较旧，需先安装 KEGG.db（BiocManager::install("KEGG.db")）
  make_option(c("--use_local_kegg"), action="store_true", default=TRUE, help="Offline: use KEGG.db instead of rest.kegg.jp (requires KEGG.db package)")

)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw KEGG Enrichment!", add_help_option=FALSE))
org <- opt$organism  # https://www.genome.jp/kegg/tables/br08606.html。Mus musculus, Bovine, Homo_sapiens ->"hsa", "bos", "mmu"
# 按需安装 KEGG 物种对应注释包（org.Hs.eg.db 已在上方加载；其余首次使用时下载到持久卷 R_LIBS_USER）
local({
    pkg_map <- c(hsa="org.Hs.eg.db", mmu="org.Mm.eg.db", bos="org.Bt.eg.db", dme="org.Dm.eg.db")
    pkg <- pkg_map[org]
    if (!is.na(pkg) && pkg != "org.Hs.eg.db") {
        if (!requireNamespace(pkg, quietly=TRUE)) {
            message("Installing R package: ", pkg, " from Bioconductor...")
            BiocManager::install(pkg, ask=FALSE, update=FALSE)
        }
        library(package=pkg, character.only=TRUE)
    }
})


# 参数
# KEGG富集分析参数
pvalue <- opt$pvalue  # 显著性水平
qvalue <- opt$qvalue   # 显著性水平
# 筛选KEGG富集结果
# pval <- 0.05  # 显著性水平
# adj <- 0.05
termNum <- opt$termNum  # 呈现几个通路,显示的KEGG条数。bubble/和弦图和聚类图要用到
# show <- opt$show  # 显示的KEGG条数。bubble图用到 这俩不是一个意思吗！ show和termNum 用一个参数就行
type <- opt$type # 气泡图bubble，和弦图chord，聚类图cluser
adjust <- opt$adjust  # 调整方法，默认使用BH 一审

# interesting <- c()  # 还未实现：选择特别感兴趣的KEGG术语
# interesting <- c(
#     "hsa05235", "hsa05142", "hsa04660"
# )

# read data
# opt$input <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/", opt$jobID, "_data.txt", sep = "")
# table_data <- read.table(opt$input, header = TRUE, sep = ",", check.names = FALSE)  # 不检查列名是否存在  \t
if (opt$type_analysis == "none"){
    opt$input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt"))
    table_data <- read.table(opt$input, header = TRUE, sep = "\t", check.names = FALSE)  # 不检查列名是否存在 \t
}else{
    # 读取up, down, all数据
    table_data <- read.table(automata_job_file(opt$jobID, paste0("result/select_", opt$type_analysis, ".txt")), header = TRUE, sep = "\t", check.names = FALSE)  # 不检查列名是否存在 \t
}
# 提取表格第一列，即基因名称列
gene_column <- table_data[[1]]
# 存储基因的EntrezID
entrez_ids <- c()

# 遍历基因名称列中的每个基因，获取gene的EntrezID
for (gene in gene_column){
    # 使用try catch捕获错误
    id <- tryCatch({
        # 用match函数尝试将基因名称匹配到EntrezID
        if (org == "hsa"){
            mget(gene, org.Hs.egSYMBOL2EG)[[1]][1] 
        }else if(org == "mmu"){
            mget(gene, org.Mm.egSYMBOL2EG)[[1]][1] 
        }else if (org == "bos"){
            mget(gene, org.Bt.egSYMBOL2EG)[[1]][1] 
        }else if (org == "dme"){
            mget(gene, org.Dm.egSYMBOL2EG)[[1]][1] 
        }else if (org == "ath"){
            mget(gene, org.At.tairSYMBOL)
        }
    }, error = function(e) {
        # 如果匹配不到，则返回NA
        NA
        # return(NA)
    })

    # 将匹配到的EntrezID添加到entrez_ids向量中
    entrez_ids <- c(entrez_ids, id)
}



# 处理entrez_ids
# 将entrez_ids向量转换为字符向量
entrez_ids <- as.character(entrez_ids)
# 将entrez_ids添加到原始数据表格中，生成新列entrezID
table_data$entrezID <- entrez_ids
# table_data <- cbind(table_data, entrezID=entrez_ids)
# 删除entrezID为空的行
table_data <- table_data[!is.na(table_data$entrezID), ]




# 提取表格中的entrezID列
gene <- table_data$entrezID

# 是否使用本地 KEGG.db（不访问 rest.kegg.jp）：命令行 --use_local_kegg 或环境变量 KEGG_USE_INTERNAL_DATA=1
use_internal_data <- isTRUE(opt$use_local_kegg) || (Sys.getenv("KEGG_USE_INTERNAL_DATA", "") == "1")
if (use_internal_data) {
  message("KEGG enrichment: use_internal_data=TRUE (KEGG.db local). No rest.kegg.jp access.")
  if (!requireNamespace("KEGG.db", quietly = TRUE)) {
    stop("离线 KEGG 需要 Bioconductor 包 KEGG.db。安装：BiocManager::install('KEGG.db')")
  }
} else {
  message("KEGG enrichment: use_internal_data=FALSE (online via KEGGREST → rest.kegg.jp).")
}

# 进行KEGG富集分析, 设置pvalue和qvalue阈值
KEGG <- enrichKEGG(
  gene = gene,
  organism = org,
  pvalueCutoff = pvalue,
  qvalueCutoff = qvalue,
  pAdjustMethod = adjust,
  use_internal_data = use_internal_data
)
# 将KEGG富集分析结果转换为data frame
KEGG <- as.data.frame(KEGG)
# 筛选数据
# KEGG <- KEGG[KEGG$pvalue < pval & KEGG$p.adjust < adj, ]
# 将KEGG术语中的基因ID转换为字符串，合并相同的基因ID
KEGG$geneID <- as.character(sapply(KEGG$geneID, function(x) {
    # 将geneID中可能存在的多个entrezID分割，返回一个字符向量
    ids = strsplit(x, split = "/")[[1]]
    # 根据enterzID在table_data的entrezID列中找到对应的位置，返回一个数值向量
    idx = match(ids, as.character(table_data$entrezID))
    # 根据位置在table_data的symbol列（gene列）中找到对应的symbol，返回一个字符向量
    symbols = table_data$gene[idx]
    # 将多个symbol连接成一个字符串，并返回
    paste(symbols, collapse = "/")
}))

# 写入文件
filename <- automata_job_file(opt$jobID, "result/KEGG_enrichment_result.txt")
write.table(KEGG, file = filename, sep = "\t", row.names = FALSE, quote = FALSE)

# 若没有任何富集结果，后续绘图/表格构建会报错（长度不一致）。
# 此时保留空表输出并正常退出，避免任务失败。
if (is.null(KEGG) || nrow(KEGG) == 0) {
    message("No KEGG enrichment result. KEGG_enrichment_result.txt has been written (empty). Skip plotting.")
    empty_plot <- ggplot() + theme_void()
    for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
        ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
    }
    quit(save = "no", status = 0)
}


# if (length(interesting) != 0){
#     # 选择感兴趣的GO分类
#     selected_KEGG <- subset(KEGG, KEGG$ID %in% interesting)
#     print("1")
#     KEGG@result <- selected_KEGG  # 报错：Error in (function (cl, name, valueClass)  : 'result' is not a slot in class "data.frame"
#     print("2")
#     write.table(KEGG, file = "KEGG_interesting.txt", sep = "\t", row.names = FALSE, quote = FALSE)
# }
KEGG <- KEGG[order(KEGG$Count, decreasing = TRUE), ]  # 按照Count降序排列
# 创建dataframe
kegg <- data.frame(
    Category ="ALL",
    ID = KEGG$ID,
    Term = KEGG$Description,
    Genes = gsub("/", ", ", KEGG$geneID),
    adj_pval = KEGG$p.adjust
)
# 从原始数据中提取geneID和logFC，创建数据框genelist
genelist <- data.frame(
    ID = table_data$gene,
    logFC = table_data$logFC
)

termNum <- ifelse(nrow(kegg) < termNum, nrow(kegg), termNum)
# 获取genelist中的基因数量
geneNum <- nrow(genelist)

# 保存图片
result_path <- automata_job_file(opt$jobID, "result/kegg_enrichment")

# 和弦图chord
# 绘制和弦图
if (type == "chord"){
    # 使用circle_dat函数创建圆形布局的数据
    KEGGcirc <- circle_dat(kegg, genelist)

    # kegg$Term[1:termNum]为需要展示的KEGG条目
    chord <- chord_dat(KEGGcirc, genelist[1:geneNum, ], kegg$Term[1:termNum])
    # 检查chord对象是否创建成功，如果成功则绘制圆形图
    if (!is.null(chord)){
        # 绘制和弦图
        # 设置基因之间的距离、基因排序、基因大小、边框大小和处理标签
        gochord <- GOChord(chord,
                space=0.02,
                gene.order="logFC",
                gene.space=0.25,  # 基因在圆周上的间距
                gene.size = 5,  # 基因名大小
                # border.size = 0.1,  # 基因节点边框大小
                process.label = 10  # 处理标签大小？
                ) 

        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), gochord, device = dev, width = 15, height = 15)
        }
    }else{
        print("No created chord object")
        empty_plot <- ggplot() + theme_void()
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
        }
    }
    
    # ggsave(paste("KEGG_chord", dev, sep="."), gochord, width = 15, height = 15, device = dev)
    # ggsave("GO_chord.pdf", gochord, width = 15, height = 10)
}

# 绘制GO聚类图
if (type == "cluster"){
    # 使用circle_dat函数创建圆形布局的数据
    KEGGcirc <- circle_dat(kegg, genelist)

    # 如果GO数据不为空且行数大于0，则绘制GO聚类图，使用前termNum个术语
    chord <- chord_dat(KEGGcirc, genelist[1:geneNum, ], kegg$Term[1:termNum])
    if (!is.null(KEGG) && nrow(KEGG) > 0){
        keggcluster <- GOCluster(KEGGcirc, as.character(KEGG[1:termNum, 3]))
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), keggcluster, device = dev, width = 15, height = 8)
        }
    }else{
        print("No KEGG enrichment data found, we can not draw KEGG cluster plot")
        empty_plot <- ggplot() + theme_void()
        for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
            ggsave(paste(result_path, dev, sep = "."), empty_plot, device = dev, width = 15, height = 8)
        }
    }
    
    # ggsave(paste("KEGG_cluster", dev, sep="."), keggcluster, width = 15, height = 8, device = dev)
    # ggsave("GO_cluster.pdf", gocluster, width = 15, height = 8)
}


# 气泡图
if (type == "bubble"){
    # # 按照Count降序对表格排列
    # KEGG <- KEGG[order(KEGG$Count, decreasing = TRUE), ]
    # # 选择前30行
    # KEGG.top <- head(KEGG, n = termNum)
    # # 使画出的KEGG PATHWAY的顺序与输入一致
    # KEGG.top$Description <- factor(KEGG.top$Description, levels = c(KEGG.top$Description %>% as.data.frame() %>% pull()))
    # # KEGG.top数据框中的GeneRatio列进行四舍五入（保留三位小数）
    # ev = function(x) {eval(parse(text=x))}
    # KEGG.top$GeneRatio <- round(sapply(KEGG.top$GeneRatio, ev), 3)

    # 绘制气泡图
    KEGG.top <- head(KEGG, n = termNum)
    # 使画出的KEGG PATHWAY的顺序与输入一致
    KEGG.top$Description <- factor(KEGG.top$Description, levels = c(KEGG.top$Description %>% as.data.frame() %>% pull()))
    # KEGG.top数据框中的GeneRatio列进行四舍五入（保留三位小数）
    ev = function(x) {eval(parse(text=x))}
    KEGG.top$GeneRatio <- round(sapply(KEGG.top$GeneRatio, ev), 3)
    bubble <- ggplot(KEGG.top, aes(x=GeneRatio, y=Description, color = -log10(pvalue))) +
        geom_point(aes(size=Count)) +
        theme_bw() + # 白色主题
        scale_y_discrete(labels = function(y) str_wrap(y, width = 50)) + # 自动换行
        labs(size = "Counts", x = "GeneRatio", y = NULL, title=NULL) +
        # scale_color_gradient(low = "red", high = "blue", guide = "colorbar", name = "log10(p-value)")+ # 颜色渐变设置
        scale_color_gradient(low = "#a392fa", high = "#fee153", guide = "colorbar", name = "log10(p-value)")+ # 颜色渐变设置  紫色——黄色
        theme(axis.text = element_text(size = 16, color = "black"), # 坐标轴文字大小
              axis.title = element_text(size = 16, color = "black"), # 坐标轴标题大小
              title = element_text(size = 18, color = "black")) + # 图标题大小
        guides(color = guide_colorbar(reverse = TRUE))  # 颜色渐变设置。高值在下方，低值在上方

    for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
        ggsave(paste(result_path, dev, sep = "."), bubble, device = dev, width = 15, height = 8)
    }
    # ggsave(paste("KEGG_bubble", dev, sep="."), bubble, width = 15, height = 8, device = dev)
}




