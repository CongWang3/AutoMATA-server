FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    build-essential \
    default-mysql-client \
    default-libmysqlclient-dev \
    r-base \
    r-base-dev \
    libxml2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# RcppEigen 等在单线程下可能长时间无新日志像「卡住」；并行 make + 压制 Eigen 模板告警（仍合法 C++）
# 构建时可覆盖：docker build --build-arg R_PARALLEL_MAKE=4 ...
ARG R_PARALLEL_MAKE=2
ENV MAKEFLAGS=-j${R_PARALLEL_MAKE}
RUN mkdir -p /root/.R \
    && printf '%s\n' 'CXXFLAGS += -Wno-ignored-attributes' 'CXX17FLAGS += -Wno-ignored-attributes' >> /root/.R/Makevars

# R 依赖与 code/data_analysis_plot 下脚本的 library() 对齐（后端通过 RSCRIPT_PATH 调用 Rscript，见 config/settings.py、docker-compose.prod.yml）。
# - pca.R：ggplot2 vegan dplyr ggrepel ggpubr patchwork optparse
# - volcano_gsea_padj.R / dumbbell*.R：ggplot2 dplyr ggrepel|patchwork optparse
# - venn.R：VennDetail ggplot2 dplyr UpSetR VennDiagram optparse
# - cor_heatmap.r：linkET ggplot2 RColorBrewer ggnewscale optparse
# - ppi.R：tidyverse clusterProfiler STRINGdb igraph ggraph optparse
# - go/kegg_enrichment.R：clusterProfiler org.Hs.eg.db dplyr GOplot DOSE ggplot2 tidyr（kegg 另需 yulab.utils）
# - df_cluster_heatmap.R：ComplexHeatmap ggplot2 ggplotify optparse
# - df_count_normalized.R：DESeq2 ggplot2 DEFormats dplyr
# - limma_fpkm_df.R（code/）：limma dplyr pheatmap ggplot2 ComplexHeatmap optparse
# dependencies=TRUE：避免 ggpubr 等仅装主包、传递依赖缺失却构建仍“成功”的情况。
RUN Rscript -e "install.packages(c(\
  'BiocManager','optparse','dplyr','tidyr','ggplot2','ggrepel','ggpubr','patchwork',\
  'VennDiagram','UpSetR','RMySQL','igraph','ggraph','pheatmap','vegan','limma',\
  'RColorBrewer','ggnewscale','GOplot','tidyverse','VennDetail','linkET'\
), repos='https://cloud.r-project.org', dependencies=TRUE, Ncpus=${R_PARALLEL_MAKE})" \
 && Rscript -e "BiocManager::install(c('DESeq2','ComplexHeatmap','clusterProfiler','DOSE','org.Hs.eg.db','STRINGdb','impute','ggplotify','KEGG.db','ActivePathways','DEFormats','yulab.utils'), ask=FALSE, update=FALSE, Ncpus=${R_PARALLEL_MAKE})"

# 构建期校验：任一关键包不可加载则 docker build 失败，避免运行时才报 there is no package
RUN Rscript -e 'for (p in c(\
  "ggpubr","ggplot2","vegan","dplyr","ggrepel","patchwork","optparse",\
  "linkET","VennDetail","tidyverse","VennDiagram","UpSetR","igraph","ggraph",\
  "RColorBrewer","ggnewscale","RMySQL","pheatmap","GOplot","tidyr",\
  "DESeq2","DEFormats","ComplexHeatmap","ggplotify","limma",\
  "clusterProfiler","DOSE","org.Hs.eg.db","STRINGdb","KEGG.db","yulab.utils","BiocManager"\
)) if (!requireNamespace(p, quietly=TRUE)) stop("missing R package: ", p); cat("R packages verify OK\n")'

# R 包已编译完成，卸掉编译链与 *-dev 头文件，可省数百 MB（运行期仍保留 r-base 与动态库）
RUN apt-get update && apt-get purge -y --auto-remove \
    build-essential \
    r-base-dev \
    default-libmysqlclient-dev \
    libxml2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
# PyPI 默认 Linux torch 会安装 nvidia-*、triton 等（约 3GB+）；子进程训练/推理仅需 CPU wheel。
RUN pip install --no-cache-dir "torch>=2.1,<3" "torchvision>=0.16,<1" \
    --index-url https://download.pytorch.org/whl/cpu
# 生产镜像不装 pytest/httpx（仅测试用）；torch 已由 CPU wheel 安装
RUN grep -vE '^[[:space:]]*torch(vision)?([[:space:]]|>=|==|>|<|\[)' /app/requirements.txt \
    | grep -vE '^[[:space:]]*pytest' \
    | grep -vE '^[[:space:]]*httpx' \
    > /app/requirements-rest.txt \
    && pip install --no-cache-dir -r /app/requirements-rest.txt \
    && rm /app/requirements-rest.txt
# 若某依赖误装 CUDA 栈，统一卸掉（CPU 镜像不需要）
RUN pip list --format=freeze | grep -iE '^(nvidia-|triton)==' | cut -d= -f1 | xargs -r pip uninstall -y || true

COPY . /app

# 如果 code/ 目录存在（通过构建 context 或挂载传入），则复制到镜像内
# 在 CI 构建时通过 GitHub Actions 预先复制到 backend/code/
COPY code/ /app/code/

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
