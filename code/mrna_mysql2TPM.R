# 打不开mysql的解决方法链接
# https://blog.csdn.net/m0_60721514/article/details/123676327?spm=1001.2101.3001.6650.5&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7Ebaidujs_utm_term%7ECtr-5-123676327-blog-122294814.235%5Ev43%5Epc_blog_bottom_relevance_base3&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7Ebaidujs_utm_term%7ECtr-5-123676327-blog-122294814.235%5Ev43%5Epc_blog_bottom_relevance_base3&utm_relevant_index=8
# 运行此脚本前需要先打开mysql：命令行终端用管理员打开 连接mysql：net start mysql，端口占用：netstat -ano，关闭连接：net stop mysql
# 加载 code/automata_paths.R（须先于 rm；附着 automata:paths）
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
      stop("找不到 code/automata_paths.R；请设置 AUTOMATA_REPO_ROOT 或从仓库内用 Rscript 调用。", call. = FALSE)
  }
}))
rm(list = ls())
repo_root <- automata_repo_root()
setwd(automata_path_code())
library("RMySQL")
getOption('timeout')  # 解决超时
options(timeout=100000)
library(optparse)  # 命令行
countToTpm <- function(counts, effLen){
  # # print(counts)
  # # print(effLen)
  # rate <- log(counts) - log(effLen)
  # # print(paste("rate =", rate))
  # # print(paste("exp(rate) =", exp(rate)))
  # # print(paste("sum(exp(rate)) =", sum(exp(rate))))
  # denom <- log(sum(exp(rate)))
  # log2(exp(rate - denom + log(1e6)))  # log2
  # # print("sum(counts) = ")  # 确实是一列一列传入的
  # # print(sum(counts))
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
  # 自己加了log2()函数
  # 不加log2时，算出的TPM每列加和都是1e+06，每列加和一致
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

# searchLengthSymbolFromRefseq <- function(refseqIDs, sqlconnection, table){
#   # print("enter searchLengthSymbolFromRefseq函数")
#   lengths <- c()
#   symbolss <- c()
  
# #   mrna  都为text类型
# #   dm Transcript_stable_ID, Transcript_name, FlyBase_transcript_ID, RefSeq_DNA_ID
# #   homo Transcript_stable_ID, RefSeq_match_transcript_MANE_Select, RefSeq_mRNA_ID, RefSeq_mRNA_predicted_ID, Transcript_name
# #   mus Transcript_stable_ID, Transcript_name, RefSeq_mRNA_ID, RefSeq_mRNA_predicted_ID
# #   bos Transcript_stable_ID, Transcript_name, RefSeq_mRNA_ID, RefSeq_mRNA_predicted_ID

#   for (refseqID in refseqIDs){
#     # sqlSentence = select Length, Transcript_name from mus_musculus where Transcript_stable_ID = 'XM_006495550' or RefSeq_mRNA_ID='XM_006495550' or RefSeq_mRNA_predicted_ID='XM_006495550'
#     if (table == "mrna_dm"){
#         sqlSentence = paste("select Length, Transcript_name from mrna_dm where RefSeq_DNA_ID='", refseqID,"'",sep="" )
#     }else if (table == "mrna_homo_sapiens"){
#         sqlSentence = paste("select Length, Transcript_name from mrna_homo_sapiens where RefSeq_match_transcript_MANE_Select ='", refseqID,"'", " or RefSeq_mRNA_ID='", refseqID,"'", " or RefSeq_mRNA_predicted_ID='", refseqID,"'",sep="" )
#     }else if (table == "mrna_mus"){
#         sqlSentence = paste("select Length, Transcript_name from mrna_mus where RefSeq_mRNA_ID='", refseqID,"'", " or RefSeq_mRNA_predicted_ID='", refseqID,"'",sep="" )
#     }else{
#         # bos_taurus
#         sqlSentence = paste("select Length, Transcript_name from mrna_bos_taurus where RefSeq_mRNA_ID='", refseqID,"'", " or RefSeq_mRNA_predicted_ID='", refseqID,"'",sep="" )
#     }
    
#     result = dbSendQuery(sqlconnection, sqlSentence)
#     data = fetch(result, n = 1)  # 只捕获查询到的第一条结果
#     lengths <- append(lengths, data$Length)
#     symbolss <- append(symbolss, data$Transcript_name)
#     # 关闭查询结果
#     dbClearResult(dbListResults(mysqlconnection)[[1]])
#   }
  
#   out <- list(lengths=lengths, symbolss=symbolss)
#   print("out =")
#   print(out)
#   return (out)
# }

# 一审 注释旧 searchLengthSymbolFromRefseq 函数，新增 searchLengthSymbolFromRefseq & find_matching_row 函数
searchLengthSymbolFromRefseq <- function(refseqIDs, sqlconnection, table){
  print("进入searchLengthSymbolFromRefseq函数")
  
  # 确保refseqIDs是字符向量
  refseqIDs <- as.character(refseqIDs)
  
  # 将refseqIDs列表转换为带引号的字符串
  refseqIDs_quoted <- paste0("'", refseqIDs, "'")
  refseqIDs_str <- paste(refseqIDs_quoted, collapse = ",")
  
  # 根据表名构建不同的查询条件
  if (table == "mrna_dm") {
    # dm表: RefSeq_DNA_ID
    sqlSentence <- paste(
      "SELECT * FROM (",
      "  SELECT RefSeq_DNA_ID, Length, Transcript_name, ",
      "  ROW_NUMBER() OVER (PARTITION BY RefSeq_DNA_ID ORDER BY (SELECT NULL)) as rn ",
      "  FROM ", table, 
      "  WHERE RefSeq_DNA_ID IN (", refseqIDs_str, ")",
      ") t WHERE rn = 1",
      sep = ""
    )
    match_field <- "RefSeq_DNA_ID"
    
  } else if (table == "mrna_homo_sapiens") {
    # homo表: 三个字段
    sqlSentence <- paste(
      "SELECT * FROM (",
      "  SELECT RefSeq_match_transcript_MANE_Select, RefSeq_mRNA_ID, RefSeq_mRNA_predicted_ID, Length, Transcript_name, ",
      "  ROW_NUMBER() OVER (",
      "    PARTITION BY ",
      "      CASE ",
      "        WHEN RefSeq_match_transcript_MANE_Select IN (", refseqIDs_str, ") THEN RefSeq_match_transcript_MANE_Select ",
      "        WHEN RefSeq_mRNA_ID IN (", refseqIDs_str, ") THEN RefSeq_mRNA_ID ",
      "        WHEN RefSeq_mRNA_predicted_ID IN (", refseqIDs_str, ") THEN RefSeq_mRNA_predicted_ID ",
      "      END ",
      "    ORDER BY (SELECT NULL)) as rn ",
      "  FROM ", table, 
      "  WHERE RefSeq_match_transcript_MANE_Select IN (", refseqIDs_str, ") ",
      "     OR RefSeq_mRNA_ID IN (", refseqIDs_str, ") ",
      "     OR RefSeq_mRNA_predicted_ID IN (", refseqIDs_str, ")",
      ") t WHERE rn = 1",
      sep = ""
    )
    match_field <- "multiple"
    
  } else if (table == "mrna_mus") {
    # mus表: 两个字段
    sqlSentence <- paste(
      "SELECT * FROM (",
      "  SELECT RefSeq_mRNA_ID, RefSeq_mRNA_predicted_ID, Length, Transcript_name, ",
      "  ROW_NUMBER() OVER (",
      "    PARTITION BY ",
      "      CASE ",
      "        WHEN RefSeq_mRNA_ID IN (", refseqIDs_str, ") THEN RefSeq_mRNA_ID ",
      "        WHEN RefSeq_mRNA_predicted_ID IN (", refseqIDs_str, ") THEN RefSeq_mRNA_predicted_ID ",
      "      END ",
      "    ORDER BY (SELECT NULL)) as rn ",
      "  FROM ", table, 
      "  WHERE RefSeq_mRNA_ID IN (", refseqIDs_str, ") ",
      "     OR RefSeq_mRNA_predicted_ID IN (", refseqIDs_str, ")",
      ") t WHERE rn = 1",
      sep = ""
    )
    match_field <- "multiple"
    
  } else {
    # bos_taurus表: 两个字段
    sqlSentence <- paste(
      "SELECT * FROM (",
      "  SELECT RefSeq_mRNA_ID, RefSeq_mRNA_predicted_ID, Length, Transcript_name, ",
      "  ROW_NUMBER() OVER (",
      "    PARTITION BY ",
      "      CASE ",
      "        WHEN RefSeq_mRNA_ID IN (", refseqIDs_str, ") THEN RefSeq_mRNA_ID ",
      "        WHEN RefSeq_mRNA_predicted_ID IN (", refseqIDs_str, ") THEN RefSeq_mRNA_predicted_ID ",
      "      END ",
      "    ORDER BY (SELECT NULL)) as rn ",
      "  FROM ", table, 
      "  WHERE RefSeq_mRNA_ID IN (", refseqIDs_str, ") ",
      "     OR RefSeq_mRNA_predicted_ID IN (", refseqIDs_str, ")",
      ") t WHERE rn = 1",
      sep = ""
    )
    match_field <- "multiple"
  }
  
  tryCatch({
    # 执行批量查询
    result <- dbSendQuery(sqlconnection, sqlSentence)
    data <- fetch(result, n = -1)
    dbClearResult(result)
    
    # 找到的refseqID
    found_ids <- c()
    if (match_field == "multiple") {
      # 对于多字段匹配的表，需要确定具体匹配的是哪个字段
      for (id in refseqIDs) {
        if (table == "mrna_homo_sapiens") {
          if (id %in% data$RefSeq_match_transcript_MANE_Select || 
              id %in% data$RefSeq_mRNA_ID || 
              id %in% data$RefSeq_mRNA_predicted_ID) {
            found_ids <- c(found_ids, id)
          }
        } else {
          # mus和bos表
          if (id %in% data$RefSeq_mRNA_ID || id %in% data$RefSeq_mRNA_predicted_ID) {
            found_ids <- c(found_ids, id)
          }
        }
      }
    } else {
      # 单字段匹配的表
      found_ids <- data[[match_field]]
    }
    
    # 未找到的refseqID
    missing_ids <- setdiff(refseqIDs, found_ids)
    
    # 按原始refseqIDs顺序整理数据，只取第一条结果
    lengths <- sapply(refseqIDs, function(id) {
      row_idx <- find_matching_row(data, id, table)
      if (length(row_idx) > 0) {
        data$Length[row_idx[1]]
      } else {
        NA
      }
    })
    
    symbolss <- sapply(refseqIDs, function(id) {
      row_idx <- find_matching_row(data, id, table)
      if (length(row_idx) > 0) {
        data$Transcript_name[row_idx[1]]
      } else {
        NA
      }
    })
    
    # 输出未找到的refseqID
    if (length(missing_ids) > 0) {
      message("No data found for the following RefSeqID: ", paste(missing_ids, collapse = ", "))
    }
    
    out <- list(
      lengths = unname(lengths),
      symbolss = unname(symbolss),
      missing_ids = missing_ids,
      found_ids = found_ids
    )
    
    print("out =")
    print(out)
    return(out)
    
  }, error = function(e) {
    warning("Batch query failed: ", e$message)
    
    exit(0)
  })
}


# 一审 辅助函数：根据表结构找到匹配的行
find_matching_row <- function(data, id, table) {
  if (table == "mrna_dm") {
    which(data$RefSeq_DNA_ID == id)
  } else if (table == "mrna_homo_sapiens") {
    which(data$RefSeq_match_transcript_MANE_Select == id | 
          data$RefSeq_mRNA_ID == id | 
          data$RefSeq_mRNA_predicted_ID == id)
  } else {
    # mus和bos表
    which(data$RefSeq_mRNA_ID == id | data$RefSeq_mRNA_predicted_ID == id)
  }
}





# 一审 注释旧 searchLengthSymbolFromEnsembl 函数，新增 searchLengthSymbolFromEnsembl 函数
searchLengthSymbolFromEnsembl <- function(EnsemblIDs, sqlconnection, table){
  
  # 确保EnsemblIDs是字符向量
  EnsemblIDs <- as.character(EnsemblIDs)
  
  # 将EnsemblIDs列表转换为带引号的字符串
  EnsemblIDs_quoted <- paste0("'", EnsemblIDs, "'")
  EnsemblIDs_str <- paste(EnsemblIDs_quoted, collapse = ",")
  
  # 构建批量查询SQL
  if (table == "mrna_dm") {
    # 对于mrna_dm表，有两个查询条件
    sqlSentence <- paste(
      "SELECT * FROM (",
      "  SELECT Transcript_stable_ID, FlyBase_transcript_ID, Length, Transcript_name, ",
      "  ROW_NUMBER() OVER (",
      "    PARTITION BY CASE ",
      "      WHEN Transcript_stable_ID IN (", EnsemblIDs_str, ") THEN Transcript_stable_ID ",
      "      WHEN FlyBase_transcript_ID IN (", EnsemblIDs_str, ") THEN FlyBase_transcript_ID ",
      "    END ",
      "    ORDER BY (SELECT NULL)) as rn ",
      "  FROM ", table, 
      "  WHERE Transcript_stable_ID IN (", EnsemblIDs_str, ") ",
      "     OR FlyBase_transcript_ID IN (", EnsemblIDs_str, ")",
      ") t WHERE rn = 1",
      sep = ""
    )
  } else {
    # 对于其他表，只有一个查询条件
    sqlSentence <- paste(
      "SELECT * FROM (",
      "  SELECT Transcript_stable_ID, Length, Transcript_name, ",
      "  ROW_NUMBER() OVER (PARTITION BY Transcript_stable_ID ORDER BY (SELECT NULL)) as rn ",
      "  FROM ", table, 
      "  WHERE Transcript_stable_ID IN (", EnsemblIDs_str, ")",
      ") t WHERE rn = 1",
      sep = ""
    )
  }
  
  tryCatch({
    result <- dbSendQuery(sqlconnection, sqlSentence)
    data <- fetch(result, n = -1)
    dbClearResult(result)
    
    # 找到的Ensembl_ID
    if (table == "mrna_dm") {
      # 对于mrna_dm表，需要确定匹配的是哪个字段
      found_ids <- c()
      for (id in EnsemblIDs) {
        if (id %in% data$Transcript_stable_ID) {
          found_ids <- c(found_ids, id)
        } else if (id %in% data$FlyBase_transcript_ID) {
          found_ids <- c(found_ids, id)
        }
      }
    } else {
      found_ids <- data$Transcript_stable_ID
    }
    
    # 未找到的Ensembl_ID
    missing_ids <- setdiff(EnsemblIDs, found_ids)
    
    # 按原始EnsemblIDs顺序整理数据，只取第一条结果
    lengths <- sapply(EnsemblIDs, function(id) {
      if (table == "mrna_dm") {
        # 对于mrna_dm表，检查两个字段
        row_idx <- which(data$Transcript_stable_ID == id | data$FlyBase_transcript_ID == id)
      } else {
        row_idx <- which(data$Transcript_stable_ID == id)
      }
      
      if (length(row_idx) > 0) {
        # 只取第一条结果
        data$Length[row_idx[1]]
      } else {
        NA
      }
    })
    
    symbolss <- sapply(EnsemblIDs, function(id) {
      if (table == "mrna_dm") {
        # 对于mrna_dm表，检查两个字段
        row_idx <- which(data$Transcript_stable_ID == id | data$FlyBase_transcript_ID == id)
      } else {
        row_idx <- which(data$Transcript_stable_ID == id)
      }
      
      if (length(row_idx) > 0) {
        # 只取第一条结果
        data$Transcript_name[row_idx[1]]
      } else {
        NA
      }
    })
    
    # 输出未找到的Ensembl_ID
    if (length(missing_ids) > 0) {
      message("No data found for the following Ensembl_ID: ", paste(missing_ids, collapse = ", "))
    }
    
    out <- list(
      lengths = unname(lengths),
      symbolss = unname(symbolss),
      missing_ids = missing_ids,
      found_ids = found_ids
    )
    return(out)
    
  }, error = function(e) {
    warning("Batch query failed: ", e$message)
    exit(0)

  })
}

# searchLengthSymbolFromEnsembl <- function(EnsemblIDs, sqlconnection, table){
  
#   lengths <- c()
#   symbolss <- c()
#   for (ID in EnsemblIDs){
#     # sqlSentence = "select Length from homo_sapiens where GeneID=653635"
#     if (table == "mrna_dm"){
#         sqlSentence = paste("select Length, Transcript_name from mrna_dm where Transcript_stable_ID ='", ID,"'", " or FlyBase_transcript_ID ='", ID,"'",sep="" )
#     }else{
#         sqlSentence = paste("select Length, Transcript_name from ",table," where Transcript_stable_ID ='", ID,"'",sep="" )
#     }
#     # sqlSentence = paste("select Length,Symbol from ", table, " where Ensembl_ID='", ID, "';",sep = "")
#     result = dbSendQuery(sqlconnection, sqlSentence)
#     data = fetch(result, n = 1)
#     lengths <- append(lengths, data$Length)
#     symbolss <- append(symbolss, data$Transcript_name)
#     # 关闭查询结果
#     dbClearResult(dbListResults(mysqlconnection)[[1]])
#   }
  
#   out <- list(lengths=lengths, symbolss=symbolss)
#   return (out)
# }

# 一审 注释旧 searchLengthFromSymbol 函数，新增 searchLengthFromSymbol 函数
# searchLengthFromSymbol <- function(symbolNames, sqlconnection, table){
#   # 考虑别名
#   # 查询了content字段中包含“全文搜索”关键词的所有文章
#   # SELECT * FROM articles WHERE content LIKE '%全文搜索%';
#   # select Length,Symbol from multi_omics.homo_sapiens where Synonyms like '%FAM39F%';
#   lengths <- c()
#   symbolss <- c()
#   for (name in symbolNames){
#     # sqlSentence = paste("select Length,Symbol from ", table, " where Symbol='", name, "';",sep = "")
#     sqlSentence = paste("select Length,Transcript_name from ", table, " where Transcript_name='", name, "';",sep = "")
#     # print(sqlSentence)
#     result = dbSendQuery(sqlconnection, sqlSentence)
#     data = fetch(result, n = 1)

#     # if (dim(data)[1] == 0){  # 获取查询结果的行数。fetch()返回data frame数据框，判断数据框行数是否==0
#     #   # 在Symbol列中没找到数据
#     #   # 在别名 Synonyms 中找
#     #   dbClearResult(result)  # 先关闭symbol查询的查询结果
#     #   sqlSentence = paste("select Length,Symbol from ", table, " where Synonyms like '%,", name, ",%';",sep = "")
#     #   result = dbSendQuery(sqlconnection, sqlSentence)
#     #   data = fetch(result, n = -1)
#     # }
    
#     lengths <- append(lengths, data$Length)
#     symbolss <- append(symbolss, data$Transcript_name)
#     # 关闭查询结果
#     dbClearResult(dbListResults(mysqlconnection)[[1]])
#   }

#   out <- list(lengths=lengths, symbolss=symbolss)
#   return (out)
# }

searchLengthFromSymbol <- function(symbolNames, sqlconnection, table){
  
  # 确保symbolNames是字符向量
  symbolNames <- as.character(symbolNames)
  
  # 将symbolNames列表转换为带引号的字符串
  symbolNames_quoted <- paste0("'", symbolNames, "'")
  symbolNames_str <- paste(symbolNames_quoted, collapse = ",")
  
  # 构建批量查询SQL，使用ROW_NUMBER确保每个Transcript_name只取第一条结果
  
  # 替代方案：如果表中没有ID字段
  alternative_sql <- paste(
    "SELECT * FROM (",
    "  SELECT Transcript_name, Length, ",
    "  ROW_NUMBER() OVER (PARTITION BY Transcript_name ORDER BY (SELECT NULL)) as rn ",
    "  FROM ", table, 
    "  WHERE Transcript_name IN (", symbolNames_str, ")",
    ") t WHERE rn = 1",
    sep = ""
  )
  
  tryCatch({
    # 执行批量查询
    result <- dbSendQuery(sqlconnection, alternative_sql)
    data <- fetch(result, n = -1)
    dbClearResult(result)

    
    # 找到的Transcript_name
    found_symbols <- data$Transcript_name
    
    # 未找到的Transcript_name
    missing_symbols <- setdiff(symbolNames, found_symbols)
    
    # 按原始symbolNames顺序整理数据，只取第一条结果
    lengths <- sapply(symbolNames, function(name) {
      row_idx <- which(data$Transcript_name == name)
      if (length(row_idx) > 0) {
        # 只取第一条结果
        data$Length[row_idx[1]]
      } else {
        NA
      }
    })
    
    symbolss <- sapply(symbolNames, function(name) {
      row_idx <- which(data$Transcript_name == name)
      if (length(row_idx) > 0) {
        # 只取第一条结果
        data$Transcript_name[row_idx[1]]
      } else {
        NA
      }
    })
    
    # 输出未找到的Transcript_name
    if (length(missing_symbols) > 0) {
      message("No data found for the following Transcript_name: ", paste(missing_symbols, collapse = ", "))
    }
    
    out <- list(
      lengths = unname(lengths),
      symbolss = unname(symbolss),
      missing_symbols = missing_symbols,
      found_symbols = found_symbols
    )
    
    return(out)
    
  }, error = function(e) {
    warning("Batch query failed: ", e$message)
    exit(0)

  })
}



# cmd: Rscript mysql2TPM.R -i hello -o R (-h输出帮助命令)
# ID, dataType, organism, inputfile, outputfile, 


db_user <- Sys.getenv("DB_USER", unset = "automata")
db_pass <- Sys.getenv("DB_PASSWORD", unset = "123456")
db_name <- Sys.getenv("DB_NAME", unset = "automata")
db_host <- Sys.getenv("DB_HOST", unset = "localhost")
db_port <- as.integer(Sys.getenv("DB_PORT", unset = "3306"))
mysqlconnection <- dbConnect(MySQL(), user = db_user, password = db_pass, dbname = db_name, host = db_host, port = db_port)
# dbListTables(mysqlconnection)  # 列出当前数据库中所有表

option_list <- list(
  make_option(c("-g", "--mrna_nomenclature"), type="character", default="EnsemblID", action="store", help="This argument is mRNA nomenclature, which can be Refseq, EnsemblID or Transcript_name"),
  make_option(c("-d", "--data_type"), type="character", default="FPKM", action="store", help="This argument is the type of input data, which can be FPKM, RPM, RPKM, ReadCounts or TPM"),
  make_option(c("-r", "--organism"), type="character", default="homo_sapiens", action="store", help="This argument is the organism of the input data, which can be homo_sapiens, bos_taurus, mus_musculus or drosophila_melanogaster"),
  make_option(c("-i", "--input"), type="character", default=file.path(repo_root, "code", "test_fpkm_mrna.txt"), action="store", help="This argument is input path"),
  make_option(c("-o", "--output"), type="character", default=file.path(repo_root, "code", "combined_test_mrna.txt"), action="store", help="This argument is output path"),
  make_option(c("-a", "--jobID"), type="character", default="20250424170634_6q6Iq1v7", action="store", help="This argument is jobID")
)
opt = parse_args(OptionParser(option_list = option_list, usage = "This Script is for gene data process!"))

# FastAPI 已通过 -i/-o 传入绝对路径，勿再用固定仓库路径覆盖

# 改变数据库表名
if (opt$organism == "homo_sapiens"){
  opt$organism <- "mrna_homo_sapiens"
}else if (opt$organism == "bos_taurus"){
  opt$organism <- "mrna_bos_taurus"
}else if (opt$organism == "mus_musculus"){
  opt$organism <- "mrna_mus"
}else if (opt$organism == "drosophila_melanogaster"){
  opt$organism <- "mrna_dm"
}


# 提取文件表达矩阵
file_matrix <- read.table(opt$input, header = T, sep = "\t")
IDs <- file_matrix[,1]  # 只取第一列数据：GeneID
IDs <- gsub("\\..*", "", IDs)  # 去除小数点后缀 一审

# 根据不同ID类型查询基因长度和Symbol
if (opt$mrna_nomenclature == "Refseq"){
  out <- searchLengthSymbolFromRefseq(IDs, mysqlconnection, table = opt$organism)

}else if (opt$mrna_nomenclature == "EnsemblID"){
  out <- searchLengthSymbolFromEnsembl(IDs, mysqlconnection, table = opt$organism)

}else if (opt$mrna_nomenclature == "Transcript_name"){
  out <- searchLengthFromSymbol(IDs, mysqlconnection, table = opt$organism)

}else{
  print(paste("Only mRNA nomenclatures you can enter are Refseq, EnsemblID or Transcript_name"))
  exit(0)
}

lengths <- out$lengths
symbolss <- out$symbolss

# 根据不同数据类型(FPKM, ReadCounts, RPM, RPKM, TPM等)调用不同函数得出log2(TPM)
expression_data <- file_matrix[, -1]  # 忽略第一列数据：GeneID
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
  exit(0)
}

# 拼接ID，Symbol和log2(TPM), 保存为文件
combined <- cbind(symbolss, tpms)
combined <- cbind(IDs, combined)
colnames(combined)[1] <-  opt$mrna_nomenclature # 修改列名
colnames(combined)[2] <- "Transcript_name"  # Symbol是我们数据库里寸的正统Symbol
# 保存拼接的矩阵
# filename <- paste("/xp/www/AutoMATA/download_data/Jobs/", opt$jobID, "/processed.txt", sep="")  # 必须有这个才可以 必须把结果文件所在的目录权限设置为0777才可以保存
write.table(combined, opt$output, sep = "\t", row.names = F, col.names = T, quote = F)  # 去除引号quote = F


# 关闭数据库连接
if (!dbDisconnect(mysqlconnection)){
  print('Close DataBase failed!')
}
print('finish')

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