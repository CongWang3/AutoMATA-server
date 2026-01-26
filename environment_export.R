all_packages <- installed.packages()
non_base_packages <- all_packages[is.na(all_packages[, "Priority"]), "Package"]

# # 获取包来源（CRAN/Bioconductor/GitHub等）
# package_source <- sapply(non_base_packages, function(pkg) {
#   desc <- packageDescription(pkg)
#   if (!is.null(desc$Repository)) {
#     if (grepl("CRAN", desc$Repository)) return("CRAN")
#   } else if (!is.null(desc$biocViews)) {
#     return("Bioconductor")
#   } else {
#     return("Other")
#   }
# })

# # 保存到CSV文件
# write.csv(data.frame(Package = non_base_packages, Source = package_source),
#           "package_list.csv", row.names = FALSE)

# 获取包来源（使用安全的逻辑判断）
package_source <- vapply(non_base_packages, function(pkg) {
  desc <- packageDescription(pkg)
  
  # 判断CRAN来源
  if (!is.null(desc$Repository)) {
    if (grepl("CRAN", desc$Repository)) {
      return("CRAN")
    }
  }
  
  # 判断Bioconductor来源
  if (!is.null(desc$biocViews)) {
    return("Bioconductor")
  }
  
  # 判断GitHub来源
  if (!is.null(desc$GithubRepo)) {
    return("GitHub")
  }
  
  # 其他来源统一标记为Other
  return("Other")
}, FUN.VALUE = character(1))  # 强制返回长度为1的字符向量

# 构建数据框时确保维度一致
package_df <- data.frame(
  Package = names(package_source),
  Source = unname(package_source),
  stringsAsFactors = FALSE
)

# 保存到CSV文件
write.csv(package_df, "package_list.csv", row.names = FALSE)