#!/usr/bin/env Rscript
# 对照 code/ 下 R 脚本的 library()/requireNamespace() 依赖，检查当前 R 环境是否齐全。
# 在容器内：  Rscript /app/code/check_container_r_packages.R
# 本机：      Rscript code/check_container_r_packages.R
#
# 退出码 0 = 全部可加载；非 0 = 有缺失（标准输出会列出包名）。

# 与 code/**/*.R 中显式加载的包一致，并含生产常用 KEGG.db（kegg_enrichment.R 离线模式）。
required <- sort(unique(c(
  "ActivePathways",
  "clusterProfiler",
  "ComplexHeatmap",
  "DEFormats",
  "DESeq2",
  "DOSE",
  "dplyr",
  "ggplot2",
  "ggplotify",
  "ggnewscale",
  "ggpubr",
  "ggrepel",
  "GOplot",
  "ggraph",
  "igraph",
  "KEGG.db",
  "limma",
  "linkET",
  "optparse",
  "org.Hs.eg.db",
  "patchwork",
  "pheatmap",
  "RColorBrewer",
  "RMySQL",
  "STRINGdb",
  "tidyr",
  "tidyverse",
  "UpSetR",
  "vegan",
  "VennDetail",
  "VennDiagram",
  "yulab.utils"
)))

ok <- vapply(required, function(p) requireNamespace(p, quietly = TRUE), logical(1))
missing <- names(ok)[!ok]

cat("R version:", getRversion(), "\n")
cat(".libPaths():\n")
print(.libPaths())
cat("\n检查", length(required), "个包（与仓库脚本 + KEGG.db 对齐）…\n")

if (length(missing)) {
  cat("\n缺失（requireNamespace 失败）:\n")
  cat(paste(" -", missing, collapse = "\n"), "\n", sep = "")
  quit(status = 1)
}

cat("\n全部已安装并可加载。\n")
quit(status = 0)
