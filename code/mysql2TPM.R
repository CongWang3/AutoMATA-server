# 打不开mysql的解决方法链接
# https://blog.csdn.net/m0_60721514/article/details/123676327?spm=1001.2101.3001.6650.5&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7Ebaidujs_utm_term%7ECtr-5-123676327-blog-122294814.235%5Ev43%5Epc_blog_bottom_relevance_base3&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7Ebaidujs_utm_term%7ECtr-5-123676327-blog-122294814.235%5Ev43%5Epc_blog_bottom_relevance_base3&utm_relevant_index=8
# 运行此脚本前需要先打开mysql：命令行终端用管理员打开 连接mysql：net start mysql，端口占用：netstat -ano，关闭连接：net stop mysql
rm(list = ls())
setwd("/xp/www/AutoMATA/code")
library("RMySQL")
getOption('timeout')  # 解决超时
options(timeout=100000)
library(optparse)  # 命令行

countToTpm <- function(counts, effLen){
  # rate <- log(counts) - log(effLen)
  # denom <- log(sum(exp(rate)))
  # log2(exp(rate - denom + log(1e6)))  # log2
  # 一审
  counts[is.na(counts)] <- 0
  rate <- log(counts) - log(effLen)
  denom <- log(sum(exp(rate)))
  log2(exp(rate - denom + log(1e6)) + 1)  # log2
}

countToFpkm <- function(counts, effLen){
  N <- sum(counts)
  exp( log(counts) + log(1e9) - log(effLen) - log(N) )
}

fpkmToTpm <- function(fpkm){
  # log2(exp(log(fpkm) - log(sum(fpkm)) + log(1e6)))
  # 一审
  fpkm[is.na(fpkm)] <- 0  # 技术缺失视为零
  log2(exp(log(fpkm) - log(sum(fpkm)) + log(1e6)) + 1)
}

countToEffCounts <- function(counts, len, effLen){
  counts * (len / effLen)
}

tpmToTPM <- function(tpm){
  # log2(tpm)
   # 一审
  tpm[is.na(tpm)] <- 0
  log2(tpm + 1)
}

# 一审 注释searchLengthSymbolFromGeneID函数，新增searchLengthSymbolFromGeneID_batch函数.
# searchLengthSymbolFromGeneID <- function(geneIDs, sqlconnection, table){
#   lengths <- c()
#   symbolss <- c()
#   for (gene in geneIDs){
#     # sqlSentence = "select Length from homo_sapiens where GeneID=653635"
#     sqlSentence = paste("select Length,Symbol from ", table, " where GeneID=", gene, sep = "")
#     result = dbSendQuery(sqlconnection, sqlSentence)
#     data = fetch(result, n = -1)
#     lengths <- append(lengths, data$Length)
#     symbolss <- append(symbolss, data$Symbol)
#     # 关闭查询结果
#     dbClearResult(dbListResults(mysqlconnection)[[1]])
#   }
  
#   out <- list(lengths=lengths, symbolss=symbolss)
#   return (out)
# }

searchLengthSymbolFromGeneID_batch <- function(geneIDs, sqlconnection, table){
  
  # 将GeneID列表转换为字符串
  geneIDs_str <- paste(geneIDs, collapse = ",")
  
  # 如果表中没有ID字段，使用其他方法去重
  # 这里假设表有一个自增ID字段，如果没有，可以使用以下替代方案
  # SELECT * FROM (
  #   SELECT GeneID, Length, Symbol, ROW_NUMBER() OVER (PARTITION BY GeneID ORDER BY (SELECT NULL)) as rn 
  #   FROM  multi_omics.gene_homo_sapiens
  #   WHERE GeneID IN ("100288069") 	)  t WHERE rn = 1;
  alternative_sql <- paste(
    "SELECT * FROM (",
    "  SELECT GeneID, Length, Symbol, ",
    "  ROW_NUMBER() OVER (PARTITION BY GeneID ORDER BY (SELECT NULL)) as rn ",
    "  FROM ", table, 
    "  WHERE GeneID IN (", geneIDs_str, ")",
    ") t WHERE rn = 1"  # 这里可以根据需要修改排序条件
  )
  
  tryCatch({  


    result <- dbSendQuery(sqlconnection, alternative_sql)
    data <- fetch(result, n = -1)
    dbClearResult(result)

    
    # 找到的GeneID
    found_genes <- data$GeneID
    
    # 未找到的GeneID
    missing_genes <- setdiff(geneIDs, found_genes)
    
    # 按原始geneIDs顺序整理数据
    lengths <- sapply(geneIDs, function(gene) {
      if (gene %in% found_genes) {
        data$Length[data$GeneID == gene]
      } else {
        NA
      }
    })
    
    symbolss <- sapply(geneIDs, function(gene) {
      if (gene %in% found_genes) {
        data$Symbol[data$GeneID == gene]
      } else {
        NA
      }
    })
    
    # 输出未找到的GeneID
    if (length(missing_genes) > 0) {
      message("No data found for the following GeneIDs: ", paste(missing_genes, collapse = ", "))
    }
    
    # 检查是否有重复的GeneID在结果中（理论上不应该有）
    duplicates <- found_genes[duplicated(found_genes)]
    if (length(duplicates) > 0) {
      message("Warning: The following GeneIDs are still duplicated in the results: ", paste(duplicates, collapse = ", ")) 
    }
    
    out <- list(
      lengths = unname(lengths),  # 移除名称
      symbolss = unname(symbolss),
      missing_genes = missing_genes,
      found_genes = found_genes
    )
    

    return(out)
    
  }, error = function(e) {
    warning("Batch query failed: ", e$message)  # 批量出错

    # exit(0)
  })
}



searchLengthSymbolFromEnsembl_batch <- function(EnsemblIDs, sqlconnection, table){
  
  # 确保EnsemblIDs是字符向量（因为Ensembl ID通常包含字母和数字）
  EnsemblIDs <- as.character(EnsemblIDs)
  
  # 将EnsemblIDs列表转换为带引号的字符串（因为是字符串类型）
  EnsemblIDs_quoted <- paste0("'", EnsemblIDs, "'")
  EnsemblIDs_str <- paste(EnsemblIDs_quoted, collapse = ",")
  
  
  # 替代方案：如果表中没有ID字段，使用ROW_NUMBER
  alternative_sql <- paste(
    "SELECT * FROM (",
    "  SELECT Ensembl_ID, Length, Symbol, ",
    "  ROW_NUMBER() OVER (PARTITION BY Ensembl_ID ORDER BY (SELECT NULL)) as rn ",
    "  FROM ", table, 
    "  WHERE Ensembl_ID IN (", EnsemblIDs_str, ")",
    ") t WHERE rn = 1",
    sep = ""
  )
  
  tryCatch({

    result <- dbSendQuery(sqlconnection, alternative_sql)
    data <- fetch(result, n = -1)
    dbClearResult(result)

    
    # 找到的Ensembl_ID
    found_ids <- data$Ensembl_ID
    
    # 未找到的Ensembl_ID
    missing_ids <- setdiff(EnsemblIDs, found_ids)
    
    # 按原始EnsemblIDs顺序整理数据
    lengths <- sapply(EnsemblIDs, function(id) {
      if (id %in% found_ids) {
        data$Length[data$Ensembl_ID == id]
      } else {
        NA
      }
    })
    
    symbolss <- sapply(EnsemblIDs, function(id) {
      if (id %in% found_ids) {
        data$Symbol[data$Ensembl_ID == id]
      } else {
        NA
      }
    })
    
    # 输出未找到的Ensembl_ID
    if (length(missing_ids) > 0) {
      message("No data found for the following Ensembl_IDs: ", paste(missing_ids, collapse = ", "))  # 
    }
    
    # 检查是否有重复的Ensembl_ID在结果中
    duplicates <- found_ids[duplicated(found_ids)]
    if (length(duplicates) > 0) {
      message("Warning: The following Ensembl_IDs are still duplicated in the results: ", paste(duplicates, collapse = ", "))  
    }
    
    out <- list(
      lengths = unname(lengths),  # 移除名称
      symbolss = unname(symbolss),
      missing_ids = missing_ids,
      found_ids = found_ids
    )
    
    return(out)
    
  }, error = function(e) {
    warning("Batch query failed: ", e$message)
    
    # exit(0)
  })
}


# 一审 注释searchLengthFromSymbol函数，新增searchLengthFromSymbol_batch函数.
# searchLengthFromSymbol <- function(symbolNames, sqlconnection, table){
#   # 考虑别名
#   # 查询了content字段中包含“全文搜索”关键词的所有文章
#   # SELECT * FROM articles WHERE content LIKE '%全文搜索%';
#   # select Length,Symbol from multi_omics.homo_sapiens where Synonyms like '%FAM39F%';
#   lengths <- c()
#   symbolss <- c()
#   for (name in symbolNames){
#     sqlSentence = paste("select Length,Symbol from ", table, " where Symbol='", name, "';",sep = "")
#     # print(sqlSentence)
#     result = dbSendQuery(sqlconnection, sqlSentence)
#     data = fetch(result, n = -1)

#     if (dim(data)[1] == 0){  # 获取查询结果的行数。fetch()返回data frame数据框，判断数据框行数是否==0
#       # 在Symbol列中没找到数据
#       # 在别名 Synonyms 中找
#       dbClearResult(result)  # 先关闭symbol查询的查询结果
#       sqlSentence = paste("select Length,Symbol from ", table, " where Synonyms like '%,", name, ",%';",sep = "")
#       result = dbSendQuery(sqlconnection, sqlSentence)
#       data = fetch(result, n = -1)
#     }
    
#     lengths <- append(lengths, data$Length)
#     symbolss <- append(symbolss, data$Symbol)
#     # 关闭查询结果
#     dbClearResult(dbListResults(mysqlconnection)[[1]])
#   }

#   out <- list(lengths=lengths, symbolss=symbolss)
#   return (out)
# }

searchLengthFromSymbol_batch <- function(symbolNames, sqlconnection, table){
  
  # 确保symbolNames是字符向量
  symbolNames <- as.character(symbolNames)
  
  # 将symbolNames列表转换为带引号的字符串
  symbolNames_quoted <- paste0("'", symbolNames, "'")
  symbolNames_str <- paste(symbolNames_quoted, collapse = ",")
  
  # 替代方案：如果表中没有ID字段
  alternative_sql1 <- paste(
    "SELECT * FROM (",
    "  SELECT Symbol, Length, ",
    "  ROW_NUMBER() OVER (PARTITION BY Symbol ORDER BY (SELECT NULL)) as rn ",
    "  FROM ", table, 
    "  WHERE Symbol IN (", symbolNames_str, ")",
    ") t WHERE rn = 1",
    sep = ""
  )
  
  tryCatch({
    # 执行Symbol字段的批量查询
    result1 <- dbSendQuery(sqlconnection, alternative_sql1)
    data1 <- fetch(result1, n = -1)
    dbClearResult(result1)

    
    # 找到的Symbol
    found_symbols <- data1$Symbol
    
    # 未找到的Symbol
    missing_symbols <- setdiff(symbolNames, found_symbols)
    
    # 如果有未找到的Symbol，在Synonyms字段中查询
    if (length(missing_symbols) > 0) {
      message("The following symbols were not found in the Symbol field: ", paste(missing_symbols, collapse = ", "))  # 在Symbol字段中未找到以下符号
      message("Try searching in the Synonyms field ...")  # 尝试在Synonyms字段中查询...
      
      # 构建Synonyms字段的批量查询
      synonyms_conditions <- paste0("Synonyms LIKE '%,", missing_symbols, ",%'")
      synonyms_where_clause <- paste(synonyms_conditions, collapse = " OR ")
      
      
      # Synonyms字段的替代查询方案
      alternative_sql2 <- paste(
        "SELECT * FROM (",
        "  SELECT Symbol, Length, ",
        "  ROW_NUMBER() OVER (PARTITION BY Symbol ORDER BY (SELECT NULL)) as rn ",
        "  FROM ", table, 
        "  WHERE ", synonyms_where_clause,
        ") t WHERE rn = 1",
        sep = ""
      )
      
      tryCatch({
        result2 <- dbSendQuery(sqlconnection, alternative_sql2)
        data2 <- fetch(result2, n = -1)
        dbClearResult(result2)

        
        # 合并Symbol字段和Synonyms字段的查询结果
        if (nrow(data2) > 0) {
          # 找到在Synonyms中的Symbol
          found_in_synonyms <- data2$Symbol
          still_missing <- setdiff(missing_symbols, found_in_synonyms)
          
          # 输出在Synonyms中找到的符号
          if (length(found_in_synonyms) > 0) {
            message("Find the following symbols in the Synonyms field: ", paste(found_in_synonyms, collapse = ", "))  # 在Synonyms字段中找到以下符号:
          }
          
          # 更新数据
          data1 <- rbind(data1, data2)
          found_symbols <- c(found_symbols, found_in_synonyms)
          missing_symbols <- still_missing
        }
        
      }, error = function(e) {
        warning("Synonyms field batch query error: ", e$message)
        # 如果批量查询失败，回退到单个查询Synonyms
        # message("Synonyms批量查询失败，使用逐个查询方式...")
        # data2 <- searchSymbolsFromSynonyms_single(missing_symbols, sqlconnection, table)
        # if (nrow(data2) > 0) {
        #   data1 <- rbind(data1, data2)
        #   found_in_synonyms <- data2$Symbol
        #   found_symbols <- c(found_symbols, found_in_synonyms)
        #   missing_symbols <- setdiff(missing_symbols, found_in_synonyms)
        # }
      })
    }
    
    # 按原始symbolNames顺序整理数据
    lengths <- sapply(symbolNames, function(symbol) {
      if (symbol %in% found_symbols) {
        data1$Length[data1$Symbol == symbol]
      } else {
        NA
      }
    })
    
    symbolss <- sapply(symbolNames, function(symbol) {
      if (symbol %in% found_symbols) {
        data1$Symbol[data1$Symbol == symbol]
      } else {
        NA
      }
    })
    
    # 输出最终未找到的Symbol
    if (length(missing_symbols) > 0) {
      message("No data was found for the following Symbols: ", paste(missing_symbols, collapse = ", "))  # 以下符号未找到数据
    }
    
    out <- list(
      lengths = unname(lengths),
      symbolss = unname(symbolss),
      missing_symbols = missing_symbols,
      found_symbols = found_symbols
    )
    
    return(out)
    
  }, error = function(e) {
    warning("Symbol field batch query error: ", e$message)
    # 关键：异常情况下也必须返回结构化 list，避免上层 out$xxx 触发 `$ operator is invalid for atomic vectors`
    out <- list(
      lengths = rep(NA_real_, length(symbolNames)),
      symbolss = rep(NA_character_, length(symbolNames)),
      missing_symbols = symbolNames,
      found_symbols = character(0),
      error = e$message
    )
    return(out)

  })
}




# cmd: Rscript mysql2TPM.R -i hello -o R (-h输出帮助命令)
# cmd: /xp/www/AutoMATA# /opt/anaconda/envs/R_442/bin/Rscript --no-save  code/mysql2TPM.R -g GeneID -d ReadCounts
# ID, dataType, organism, inputfile, outputfile, 


mysqlconnection = dbConnect(MySQL(), user = 'automata', password = '123456', dbname = 'automata', host = 'localhost')

option_list <- list(
  make_option(c("-g", "--gene_nomenclature"), type="character", default="GeneID", action="store", help="This argument is gene nomenclature, which can be GeneID, EnsemblID or Symbol"),
  make_option(c("-d", "--data_type"), type="character", default="FPKM", action="store", help="This argument is the type of input data, which can be FPKM, RPM, RPKM, ReadCounts or TPM"),
  make_option(c("-r", "--organism"), type="character", default="homo_sapiens", action="store", help="This argument is the organism of the input data, which can be homo_sapiens, bos_taurus, mus_musculus, or drosophila_melanogaster"),
  make_option(c("-i", "--input"), type="character", default="/xp/www/AutoMATA/code/test_fpkm_gene.txt", action="store", help="This argument is input path"),
  make_option(c("-o", "--output"), type="character", default="/xp/www/AutoMATA/code/combined_test_1.txt", action="store", help="This argument is output path"),
  make_option(c("-h", "--type"), type="character", default="none", action="store", help="none for ID conversion and log transformation, GeneID just for GeneID to Symbol conversion, EnsemblID just for EnsemblID to Symbol conversion"),
  make_option(c("-a", "--jobID"), type="character", default="20250424170634_6q6Iq1v7", action="store", help="This argument is jobID")
)
opt = parse_args(OptionParser(option_list = option_list, add_help_option=FALSE, usage = "This Script is for gene data process!"))



# 改变数据库表名
if (opt$organism == "homo_sapiens"){
  opt$organism <- "gene_homo_sapiens"
}else if (opt$organism == "bos_taurus"){
  opt$organism <- "gene_bos_taurus"
}else if (opt$organism == "mus_musculus"){
  opt$organism <- "gene_mus"
}else if (opt$organism == "drosophila_melanogaster"){
  opt$organism <- "gene_dm"
}else if (opt$organism == "arabidopsis_thaliana"){
  opt$organism <- "gene_at"
}



if (opt$type != "none"){
  opt$input <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/",opt$jobID, "_data.txt", sep="")
  data <- read.table(opt$input, sep = "\t", header = FALSE)
  file.remove(opt$input)  # 因为analysis_train_2.php中的输入和输出文件名称相同，为了确定输出文件到磁盘中，先删除输入文件
  subset_data <- data[1, 2:(ncol(data) - 1)]
  IDs <- as.character(subset_data)
  IDs <- gsub("\\..*", "", IDs)  # 一审

  if (opt$gene_nomenclature == "GeneID"){
    out <- searchLengthSymbolFromGeneID_batch(IDs, mysqlconnection, table = opt$organism)
  }else{
    out <- searchLengthSymbolFromEnsembl_batch(IDs, mysqlconnection, table = opt$organism)
  }

  symbolss <- out$symbolss
  data[1, 2:(ncol(data)-1)] <- symbolss

  # filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/",opt$jobID, "_data.txt", sep="")  # 必须有这个才可以 必须把结果文件所在的目录权限设置为0777才可以保存
  write.table(data, opt$output, sep = "\t", 
            row.names = FALSE, col.names = FALSE, quote = FALSE)

  if (!dbDisconnect(mysqlconnection)){
    print('Close DataBase failed!')
  }
  print('ID conversion finish')
  
}else{
  opt$input <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/", "origin.txt", sep="")
  # 提取文件表达矩阵
  # 某些输入包含未成对的引号会触发 scan 警告并导致列错位；这里禁用引号解析并允许不齐列填充
  file_matrix <- read.table(opt$input, header = T, sep = "\t", check.names=F, quote = "", comment.char = "", fill = TRUE)
  IDs <- file_matrix[,1]  # 只取第一列数据：GeneID

  # 根据不同ID类型查询基因长度和Symbol
  print(opt$gene_nomenclature)
  if (opt$gene_nomenclature == "GeneID"){
    print("enter")
    out <- suppressWarnings(suppressMessages(searchLengthSymbolFromGeneID_batch(IDs, mysqlconnection, table = opt$organism)))

  }else if (opt$gene_nomenclature == "EnsemblID"){
    out <- suppressWarnings(suppressMessages(searchLengthSymbolFromEnsembl_batch(IDs, mysqlconnection, table = opt$organism)))

  }else if (opt$gene_nomenclature == "Symbol"){
    # 静默查询过程中的 message/warning（否则会被后端捕获并在前端显示大量红字）
    out <- suppressWarnings(suppressMessages(searchLengthFromSymbol_batch(IDs, mysqlconnection, table = opt$organism)))

  }else{
    print(paste("Only gene nomenclatures you can enter are GeneID, EnsemblID or Symbol"))
    # exit(0)
  }

  # Symbol 分支：数据库找不到的 symbol 行直接丢弃；用找到的 found_symbols + lengths 继续做 TPM 与 log 转换
  # 同时把 missing_symbols 写入 Jobs/<jobID>/missing_symbols.txt 便于追溯
  if (opt$gene_nomenclature == "Symbol") {
    jobs_dir <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, sep = "")
    missing_path <- paste(jobs_dir, "/missing_symbols.txt", sep = "")
    if (!is.null(out$missing_symbols) && length(out$missing_symbols) > 0) {
      writeLines(as.character(out$missing_symbols), con = missing_path, sep = "\n")
    } else {
      # 若全部命中，仍写一个空文件避免前端/运维误判
      writeLines(character(0), con = missing_path)
    }

    # out$lengths / out$symbolss 已按输入 symbolNames 顺序对齐（未命中为 NA）
    # 直接用 lengths 的有效性做过滤即可，保证 lengths 与表达矩阵行一一对应
    if (is.null(out$lengths) || length(out$lengths) != nrow(file_matrix)) {
      stop("Unexpected output from searchLengthFromSymbol_batch: lengths not aligned to input rows.", call. = FALSE)
    }
    lengths_vec <- suppressWarnings(as.numeric(out$lengths))
    keep_mask <- !is.na(lengths_vec) & lengths_vec > 0
    if (!any(keep_mask)) {
      stop("No symbols were found in the database (or all found lengths are invalid).", call. = FALSE)
    }

    file_matrix <- file_matrix[keep_mask, , drop = FALSE]
    IDs <- file_matrix[, 1]
    lengths <- lengths_vec[keep_mask]

    # Symbol 分支下，第二列 Symbol 与第一列一致（输入即 Symbol）
    symbolss <- as.character(IDs)
  } else {
    lengths <- out$lengths
    symbolss <- out$symbolss
  }



  # 根据不同数据类型(FPKM, ReadCounts, RPM, RPKM, TPM等)调用不同函数得出log2(TPM)
  expression_data <- file_matrix[, -1]  # 忽略第一列数据：ID
  if (opt$data_type == "FPKM"){
    tpms <- apply(expression_data, 2, fpkmToTpm)
  }else if (opt$data_type == "ReadCounts"){
    lengths_l <- list(lengths)
    tpms <- mapply(countToTpm, expression_data, lengths_l)

  }else if (opt$data_type == "RPM"){
    # RPM*1000==RPKM. RPKM==FPKM.
    tpms <- apply(expression_data * 1000, 2, fpkmToTpm)

  }else if (opt$data_type == "RPKM"){
    tpms <- apply(expression_data, 2, fpkmToTpm)

  }else if (opt$data_type == "TPM"){
    tpms <- apply(expression_data, 2, tpmToTPM)

  }else{
    print(paste("Only data types you can enter are FPKM, RPM, RPKM, ReadCounts or TPM"))
    # exit(0)
  }

  # 拼接ID，Symbol和log2(TPM), 保存为文件
  combined <- cbind(symbolss, tpms)
  combined <- cbind(IDs, combined)
  colnames(combined)[1] <-  opt$gene_nomenclature # 修改列名
  colnames(combined)[2] <- "Symbol"  # Symbol是我们数据库里寸的正统Symbol
  # 保存拼接的矩阵 这里报错
  # filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/result/GO_enrichment_result.txt", sep="")
# write.table(GO, file = filename, sep = "\t", row.names = FALSE)
  # filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/processed.txt", sep="")  # 必须有这个才可以 必须把结果文件所在的目录权限设置为0777才可以保存
  write.table(combined, opt$output, sep = "\t", row.names = FALSE, col.names = TRUE, quote = FALSE)  # 去除引号quote = FALSE

  # 关闭数据库连接
  # dbClearResult(dbListResults(mysqlconnection)[[1]])
  if (!dbDisconnect(mysqlconnection)){
    print('Close DataBase failed!')
  }
  print('finish')
}
# [1] "D:\\app\\R\\R-4.3.1\\bin\\x64\\Rterm.exe"  # R所在的路径
# [2] "--no-echo"
# [3] "--no-restore"
# [4] "--file=mysql2TPM.R"
# [5] "--args"
# [6] "hello"
# [7] "R"

# 
# # # 清除单个变量
# # rm(object) #变量名
# # gc()
# 清除所有变量
# rm(list = ls())  # rm(geneIDs_fpkm_Matrix, sqlSentence)
# gc()