# 后端 Python 3.11；R 与团队本地一致：以 deploy/conda-r442.yml 为唯一来源（CRAN/conda-forge 栈），
# 再在镜像内补齐 yml 未列出的 Bioconductor 与少数 CRAN 包（见下方 Rscript）。
#
# 构建上下文为 backend/ 时，需先有 conda-r442.yml：
#   cp ../deploy/conda-r442.yml ./conda-r442.yml
# CI：.github/workflows/deploy.yml 在 docker build 前已拷贝。
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    MAMBA_ROOT_PREFIX=/opt/conda

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    bzip2 \
    wget \
    git \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C /tmp bin/micromamba \
    && install -m 755 /tmp/bin/micromamba /usr/local/bin/micromamba \
    && rm -rf /tmp/bin

COPY conda-r442.yml /tmp/conda-r442.yml

# 镜像内仅用 conda-forge，避免 yml 中的镜像站/defaults 在 CI 中不可用；依赖列表与 export 一致。
RUN awk 'BEGIN{print "name: R_442\nchannels:\n  - conda-forge\ndependencies:"} /^dependencies:/{f=1;next} f && !/^prefix:/{print}' /tmp/conda-r442.yml > /tmp/env.yml \
    && micromamba create -y -f /tmp/env.yml \
    && micromamba clean -a -y \
    && rm -f /tmp/conda-r442.yml /tmp/env.yml

ENV PATH="/opt/conda/envs/R_442/bin:${PATH}"

RUN Rscript -e "stopifnot(as.character(getRversion()) == '4.4.2'); cat('R ', as.character(getRversion()), ' OK\n', sep='')"

# conda-r442 为 ggplot2 3.5.x：aplot/enrichplot 需要 is_ggplot（3.5+）。
# install_github(..., dependencies=TRUE) 会装 Suggests，拉 sf/WGCNA/Hmisc 等需系统库或极重依赖，易失败且导致 ggtree 链不完整；仅用 Depends/Imports/LinkingTo。
# clusterProfiler 可能把 ggtree 换回 Bioc 旧版，装完后再覆盖一次 YuLab-SMU/ggtree。
# linkET：CRAN 对 R 4.4 可能无包，从 Hy4m/linkET；同样勿 dependencies=TRUE。
ARG R_PARALLEL_MAKE=2
RUN Rscript -e "install.packages(c(\
  'remotes','BiocManager','optparse','patchwork','VennDiagram','UpSetR','pheatmap','vegan','limma',\
  'ggnewscale','GOplot','VennDetail','ggraph'\
), repos='https://cloud.r-project.org', dependencies=c('Depends','Imports','LinkingTo'), Ncpus=${R_PARALLEL_MAKE})" \
 && Rscript -e "BiocManager::install(c(\
  'DESeq2','ComplexHeatmap','DOSE','org.Hs.eg.db','STRINGdb','impute','ggplotify','ActivePathways','DEFormats','yulab.utils',\
  'treeio','tidytree','aplot'\
  ), ask=FALSE, update=FALSE, Ncpus=${R_PARALLEL_MAKE})" \
 && Rscript -e "options(repos = BiocManager::repositories()); remotes::install_github('YuLab-SMU/ggtree', upgrade='never', dependencies=c('Depends','Imports','LinkingTo'), build_vignettes=FALSE)" \
 && Rscript -e "BiocManager::install(c('clusterProfiler'), ask=FALSE, update=FALSE, Ncpus=${R_PARALLEL_MAKE})" \
 && Rscript -e "options(repos = BiocManager::repositories()); remotes::install_github('YuLab-SMU/ggtree', upgrade='never', dependencies=c('Depends','Imports','LinkingTo'), build_vignettes=FALSE)" \
 && Rscript -e "options(repos = BiocManager::repositories()); remotes::install_github('Hy4m/linkET', upgrade='never', dependencies=c('Depends','Imports','LinkingTo'), build_vignettes=FALSE)" \
 && Rscript -e "stopifnot(requireNamespace('ggtree', quietly=TRUE), requireNamespace('clusterProfiler', quietly=TRUE), requireNamespace('linkET', quietly=TRUE))"

RUN Rscript -e 'for (p in c(\
  "ggpubr","ggplot2","vegan","dplyr","ggrepel","patchwork","optparse",\
  "linkET","VennDetail","tidyverse","VennDiagram","UpSetR","igraph","ggraph",\
  "RColorBrewer","ggnewscale","RMySQL","pheatmap","GOplot","tidyr",\
  "DESeq2","DEFormats","ComplexHeatmap","ggplotify","limma",\
  "clusterProfiler","DOSE","org.Hs.eg.db","STRINGdb","yulab.utils","BiocManager"\
)) if (!requireNamespace(p, quietly=TRUE)) stop("missing R package: ", p); cat("R packages verify OK\n")'

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir "torch>=2.1,<3" "torchvision>=0.16,<1" \
    --index-url https://download.pytorch.org/whl/cpu
RUN grep -vE '^[[:space:]]*torch(vision)?([[:space:]]|>=|==|>|<|\[)' /app/requirements.txt \
    | grep -vE '^[[:space:]]*pytest' \
    | grep -vE '^[[:space:]]*httpx' \
    > /app/requirements-rest.txt \
    && pip install --no-cache-dir -r /app/requirements-rest.txt \
    && rm /app/requirements-rest.txt
RUN pip list --format=freeze | grep -iE '^(nvidia-|triton)==' | cut -d= -f1 | xargs -r pip uninstall -y || true

# CI 已将仓库根目录 code/ 拷入 backend/code/，与本行一并进镜像；仅构建 backend 且无 code/ 时本镜像不含分析脚本。
COPY . /app

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
