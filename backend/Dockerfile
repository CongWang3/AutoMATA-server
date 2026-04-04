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

# Install R package manager first, then core CRAN/Bioconductor packages
RUN R -e "install.packages(c('BiocManager','optparse','dplyr','tidyr','ggplot2','ggrepel','ggpubr','patchwork','VennDiagram','UpSetR','RMySQL','igraph','ggraph','pheatmap','vegan','RColorBrewer','ggnewscale','GOplot'), repos='https://cloud.r-project.org')" \
    && R -e "BiocManager::install(c('DESeq2','ComplexHeatmap','clusterProfiler','DOSE','org.Hs.eg.db','STRINGdb','impute','ggplotify','KEGG.db','ActivePathways','DEFormats','yulab.utils'), ask=FALSE, update=FALSE)"

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# 如果 code/ 目录存在（通过构建 context 或挂载传入），则复制到镜像内
# 在 CI 构建时通过 GitHub Actions 预先复制到 backend/code/
COPY code/ /app/code/

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
