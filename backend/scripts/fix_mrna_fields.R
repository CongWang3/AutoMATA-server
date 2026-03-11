#!/usr/bin/env Rscript
# 转录组数据处理包装脚本
# 解决mus_musculus表字段名不匹配问题

# 加载必要的包
library(RMySQL)
library(optparse)

# 设置工作目录
setwd("/xp/www/AutoMATA/code")

# 解析命令行参数
option_list <- list(
  make_option(c("-a", "--jobID"), type="character", default="", action="store", 
              help="Job ID for this processing task"),
  make_option(c("-g", "--mrna_nomenclature"), type="character", default="EnsemblID", action="store", 
              help="mRNA nomenclature: Refseq, EnsemblID or Transcript_name"),
  make_option(c("-d", "--data_type"), type="character", default="FPKM", action="store", 
              help="Data type: FPKM, TPM, ReadCounts, RPKM, or RPM"),
  make_option(c("-r", "--organism"), type="character", default="homo_sapiens", action="store", 
              help="Organism: homo_sapiens, bos_taurus, mus_musculus or drosophila_melanogaster"),
  make_option(c("-i", "--input"), type="character", default="/xp/www/AutoMATA/download_data/Jobs/test/origin.txt", action="store", 
              help="Input file path"),
  make_option(c("-o", "--output"), type="character", default="/tmp/processed.txt", action="store", 
              help="Output file path")
)

opt_parser <- OptionParser(option_list=option_list)
opt <- parse_args(opt_parser)

# 建立数据库连接
mysqlconnection <- dbConnect(MySQL(), user='automata', password='123456', dbname='automata', host='localhost')

# 处理mus_musculus的特殊情况
if (opt$organism == "mus_musculus") {
  # 对于mus_musculus，我们需要修正字段名查询
  
  # 读取输入文件
  if (!file.exists(opt$input)) {
    stop(paste("Input file not found:", opt$input))
  }
  
  file_matrix <- read.table(opt$input, header=TRUE, sep="\t")
  IDs <- file_matrix[,1]
  IDs <- gsub("\\..*", "", IDs)  # 去除小数点后缀
  
  # 构造正确的SQL查询（使用反引号包围带空格的字段名）
  ids_quoted <- paste0("'", IDs, "'")
  ids_str <- paste(ids_quoted, collapse=",")
  
  sql_query <- paste(
    "SELECT `RefSeq mRNA ID`, `RefSeq mRNA predicted ID`, Length, `Transcript name` ",
    "FROM mrna_mus ",
    "WHERE `RefSeq mRNA ID` IN (", ids_str, ") ",
    "OR `RefSeq mRNA predicted ID` IN (", ids_str, ")"
  )
  
  # 执行查询
  result <- tryCatch({
    dbSendQuery(mysqlconnection, sql_query)
  }, error = function(e) {
    message("Database query failed: ", e$message)
    return(NULL)
  })
  
  if (!is.null(result)) {
    data <- fetch(result, n=-1)
    dbClearResult(result)
    
    # 处理查询结果
    if (nrow(data) > 0) {
      # 匹配ID并获取长度和转录本名称
      lengths <- rep(NA, length(IDs))
      transcript_names <- rep(NA, length(IDs))
      
      for (i in seq_along(IDs)) {
        id <- IDs[i]
        # 查找匹配的行
        matching_rows <- which(data$`RefSeq mRNA ID` == id | data$`RefSeq mRNA predicted ID` == id)
        if (length(matching_rows) > 0) {
          lengths[i] <- data$Length[matching_rows[1]]
          transcript_names[i] <- data$`Transcript name`[matching_rows[1]]
        }
      }
      
      # 处理表达数据
      expression_data <- file_matrix[,-1]
      
      # 根据数据类型进行转换
      if (opt$data_type == "FPKM") {
        tpms <- apply(expression_data, 2, function(x) {
          x[is.na(x)] <- 0
          log2(exp(log(x) - log(sum(x)) + log(1e6)) + 1)
        })
      } else if (opt$data_type == "TPM") {
        tpms <- apply(expression_data, 2, function(x) {
          x[is.na(x)] <- 0
          log2(x + 1)
        })
      } else {
        # 对于其他类型，简单处理
        tpms <- log2(expression_data + 1)
      }
      
      # 构建输出数据
      combined <- cbind(IDs, transcript_names, tpms)
      colnames(combined)[1] <- opt$mrna_nomenclature
      colnames(combined)[2] <- "Transcript_name"
      
      # 写入输出文件
      write.table(combined, opt$output, sep="\t", row.names=FALSE, col.names=TRUE, quote=FALSE)
      cat("Processing completed successfully\n")
    } else {
      cat("No matching records found in database\n")
    }
  }
} else {
  # 对于其他物种，调用原始脚本
  original_script <- "/xp/www/AutoMATA/code/mrna_mysql2TPM.R"
  cmd_args <- c(
    "--no-save", original_script,
    "-a", opt$jobID,
    "-g", opt$mrna_nomenclature,
    "-d", opt$data_type,
    "-r", opt$organism,
    "-o", opt$output
  )
  
  # 执行原始脚本
  system2_result <- system2("/opt/anaconda/envs/R_442/bin/Rscript", args=cmd_args, stdout=TRUE, stderr=TRUE)
  if (length(system2_result) > 0 && any(grepl("Error", system2_result))) {
    stop("Original script execution failed")
  }
}

# 关闭数据库连接
dbDisconnect(mysqlconnection)
cat("Script execution completed\n")