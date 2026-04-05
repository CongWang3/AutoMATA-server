# 安装 pca.R 等绘图脚本常用 CRAN 依赖（含 ggpubr 及其传递依赖）。
#
# 本机开发：团队以 deploy/conda-r442.yml（环境名 R_442）为准，一般无需再跑本脚本。
# 适用场景：无 conda 的环境、仅缺少数包时补齐；后端 Docker 镜像的 R 亦从同文件用 micromamba 创建，再另装 Bioc/少量 CRAN。
#
# 用法：在 shell 中执行
#   Rscript code/data_analysis_plot/install_plot_deps.R
# 或在 R 里 source() 本文件。

cran <- "https://cloud.r-project.org"
pkgs <- c(
  "ggplot2", "vegan", "dplyr", "ggrepel", "ggpubr",
  "patchwork", "optparse", "permute"
)
need <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(need)) {
  install.packages(need, repos = cran, dependencies = TRUE)
} else {
  message("所需 CRAN 包均已安装。")
}
# ggpubr 建议显式再装一层，避免批量安装时偶发缺传递依赖
if (!requireNamespace("ggpubr", quietly = TRUE)) {
  install.packages("ggpubr", repos = cran, dependencies = TRUE)
}
