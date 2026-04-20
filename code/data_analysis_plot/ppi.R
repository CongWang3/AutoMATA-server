# https://www.jianshu.com/p/5bfb94b0e250
# 得连外网才能下载，不连外网也能下载，只是很慢，多运行几次脚本就下载完成了
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
library(tidyverse)
library(clusterProfiler)


library(STRINGdb)  #  安装BiocManager::install("STRINGdb")，https://www.bioconductor.org/packages/release/bioc/vignettes/STRINGdb/inst/doc/STRINGdb.pdf
library(igraph)
library(ggraph)
# library(jsonlite)

getOption('timeout')  # 解决超时

## 解决外网下载（STRINGdb）超时问题：
## R 的 download.file 默认 timeout 较短，在弱网/慢速环境可能直接超时终止。
options(timeout=300000) # 300000s (~83.3h)
library(optparse)


# 参数
option_list <- list(
  make_option(c("-i", "--input"), type="character", default="D:\\wamp\\www\\multi_omics_own\\download_data\\Jobs\\protein_case\\ppi_data.txt", action="store", help="This argument is input path"),
  make_option(c("-j", "--jobID"), type="character", default="test_ppi", action="store", help="This argument is jobID"),  # 默认ppi_example
  make_option(c("-a", "--type"), type="character", default="SYMBOL", action="store", help="This argument is the type of data, inluding SYMBOL, ENTREZID, and ENSEMBL"), 
  make_option(c("-b", "--org"), type="character", default="Mus_musculus", action="store", help="This argument is the organism, inluding Mus_musculus, Homo_sapiens, Drosophila_melanogaster, and Bos_taurus"),   # 默认Mus_musculus
  make_option(c("-c", "--score_threshold"), type="double", default=400, action="store", help="The interaction results were filtered according to the protein interaction scores."), # 默认400
  make_option(c("-d", "--plot_type"), type="character", default="linear", action="store", help="This parameter is the type of plot, including linear, kk, and stress"), # 默认linear
  make_option(c("-e", "--show_num"), type="integer", default=5, action="store", help="Only gene names with more than <show_num> nodes are shown in the plot") # 默认5
)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is to draw PPI!"))
print("opt done")

# 创建STRINGdb对象
# species物种号（from NCBI），version数据库版本号(最新12.0)，score_threshold分数阈值
type = opt$type  # 基因列表类型，包含SYMBOL、ENSEMBL、ENTREZID。
score_threshold <- opt$score_threshold  # score_threshold是蛋白互作的得分，此值会用于筛选互作结果，400是默认分值，如果要求严格可以调高此值。根据蛋白互作的得分筛选互作结果
plot_type <- opt$plot_type  # linear, kk, stress
show_num <- opt$show_num # 绘图时只显示节点数大于5的基因名称
# input <- opt$input  # 输入文件
input <- automata_job_file(opt$jobID, paste0(opt$jobID, "_data.txt"))
# type = "SYMBOL"  # 基因列表类型，包含SYMBOL、ENSEMBL、ENTREZID。
# species <- 10090
# org <- "org.Mm.eg.db"
# score_threshold <- 400  # score_threshold是蛋白互作的得分，此值会用于筛选互作结果，400是默认分值，如果要求严格可以调高此值。根据蛋白互作的得分筛选互作结果
# plot_type <- "linear"  # linear, kk, stress
# show_num <- 5 # 绘图时只显示节点数大于5的基因名称
# input <- "D:\\wamp\\www\\multi_omics_own\\example\\draw_example\\ppi_example.txt"  # 输入文件
# jobID <- "ppi_example"  # 任务ID

# 按需安装物种注释包（首次运行时下载到持久卷 R_LIBS_USER，后续复用）
local({
    pkg_map <- c(
        Homo_sapiens         = "org.Hs.eg.db",
        Mus_musculus         = "org.Mm.eg.db",
        Bos_taurus           = "org.Bt.eg.db",
        Drosophila_melanogaster = "org.Dm.eg.db"
    )
    pkg <- pkg_map[opt$org]
    if (!is.na(pkg) && !requireNamespace(pkg, quietly=TRUE)) {
        message("Installing R package: ", pkg, " from Bioconductor...")
        BiocManager::install(pkg, ask=FALSE, update=FALSE)
    }
})

if (opt$org == "Homo_sapiens"){
    org <- "org.Hs.eg.db"  # 人类的包 待修改为其他物种的包
    species <- 9606
    library(org.Hs.eg.db)
}else if(opt$org == "Mus_musculus"){
    org <- "org.Mm.eg.db"
    species <- 10090
    library(org.Mm.eg.db)
}else if (opt$org == "Bos_taurus"){
    species <- 9913
    org <- "org.Bt.eg.db"
    library(org.Bt.eg.db)
}else if (opt$org == "Drosophila_melanogaster"){
    species <- 7227
    org <- "org.Dm.eg.db" 
    library(org.Dm.eg.db)
}

data <- read.table(input,header = TRUE, check.names = FALSE)
print("read data done")
data <- na.omit(data)



## STRINGdb 会在首次使用时下载物种数据库/互作数据；之后会从 input_directory 复用本地文件。
## 将在线下载改为“本地优先”：指定一个固定缓存目录（可用环境变量覆盖）。
stringdb_cache_dir <- Sys.getenv(
    "AUTOMATA_STRINGDB_CACHE_DIR",
    unset = file.path(automata_path_data_analysis_plot(), "stringdb_cache")
)
dir.create(stringdb_cache_dir, recursive = TRUE, showWarnings = FALSE)

# 只有当缓存缺文件时才会尝试下载；离线则会失败
string_db <- STRINGdb$new(
    version="12",
    species=species,
    score_threshold=score_threshold,
    input_directory=stringdb_cache_dir
)


if(type == "ENSEMBL"){
    # ENSEMBL-删除小数点后的数字
    data[,1] <- gsub("\\.\\d+", "", data[,1])  # 删除小数点后的数字
}

if(type != "ENTREZID") {
    # 将Gene Symbol / ENSEMBL 转换为Entrez ID
    # gene <- gene %>% bitr(fromType = type, toType = "ENTREZID", OrgDb = org, drop = T)  # drop NA or not
    data <- data[,1] %>% bitr(fromType = type, toType = "ENTREZID", OrgDb = org, drop = T)  # drop NA or not

}

if(type == "ENTREZID"){
    # 修改列名为 ENTREZID
    colnames(data)[1] <- "ENTREZID"
}


data_mapped <- tryCatch(
    {
        data %>% string_db$map(
            my_data_frame_id_col_names = "ENTREZID",
            removeUnmappedRows = TRUE
        )
    },
    error = function(e) {
        stop(
            paste0(
                # "STRINGdb mapping failed. If running offline, pre-download/cache STRINGdb files first.\n",
                # "Cache dir: ", stringdb_cache_dir, "\n",
                "Original error: ", conditionMessage(e)
            ),
            call. = FALSE
        )
    }
)  # data_mapped包含ENTREZID   SYMBOL   STRING_id三列
# # 报错schannel: CertGetCertificateChain trust error CERT_TRUST_IS_UNTRUSTED_ROOT
# # 解决：没解决
# string_db$plot_network( data_mapped$STRING_id )  # 和官网出图相同


# 使用get_interactions获取蛋白互作信息，以用于后续可视化
hit<-data_mapped$STRING_id
info <- tryCatch(
    {
        string_db$get_interactions(hit)
    },
    error = function(e) {
        stop(
            paste0(
                # "STRINGdb get_interactions failed. If running offline, ensure STRINGdb interaction files are cached.\n",
                # "Cache dir: ", stringdb_cache_dir, "\n",
                "Original error: ", conditionMessage(e)
            ),
            call. = FALSE
        )
    }
)  # info包含from to combined_score三列
# 可视化info表格 https://www.jianshu.com/p/5bfb94b0e250

# 转换stringID为Symbol，只取前两列和最后一列
links <- info %>%
  mutate(from = data_mapped[match(from, data_mapped$STRING_id), "SYMBOL"]) %>% 
  mutate(to = data_mapped[match(to, data_mapped$STRING_id), "SYMBOL"]) %>%  
  dplyr::select(from, to , last_col()) %>% 
  dplyr::rename(weight = combined_score)
# 节点数据
nodes <- links %>% { data.frame(data = c(.$from, .$to)) } %>% distinct()
# 创建网络图
# 根据links和nodes创建
net <- igraph::graph_from_data_frame(d=links,vertices=nodes,directed = F)
# 添加一些参数信息用于后续绘图
# V和E是igraph包的函数，分别用于修改网络图的节点（nodes）和连线(links)
igraph::V(net)$deg <- igraph::degree(net) # 每个节点连接的节点数
igraph::V(net)$size <- igraph::degree(net)/5 #
igraph::E(net)$width <- igraph::E(net)$weight/10



# 只显示节点数大于5(show_num)的基因名称。
# 这里的参数设置是节点的大小和其连接的线的数量有关，线数量越多则点越大；线的宽度和其蛋白互作的得分有关，得分越高则越宽。
cir <- FALSE
if(plot_type == "linear"){
    cir <- TRUE
}

plot_font_family <- "sans"
p1 <- ggraph(net, layout = plot_type, circular = cir)+
  geom_edge_arc(aes(edge_width=width), color = "lightblue", show.legend = F)+
  geom_node_point(aes(size=size), color="orange", alpha=0.7)+
  geom_node_text(aes(filter=deg>show_num, label=name), size = 1.5, repel = F, family = plot_font_family)+
  scale_edge_width(range = c(0.2,1))+
  scale_size_continuous(range = c(1,10) )+
  guides(size=F)+
  theme_graph(base_family = plot_font_family)


# 保存图片
result_path <- automata_job_file(opt$jobID, "result/ppi")
for(dev in c("pdf", "jpeg", "tiff", "png", "bmp", "svg")){
    ggsave(paste(result_path, dev, sep = "."), p1, device = dev, width = 7.5, height = 6)
}
