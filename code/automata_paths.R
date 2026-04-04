# AutoMATA 路径：附着到 search()，调用方在 rm(list = ls()) 之后仍可使用 automata_* 函数。
# 优先级：环境变量 AUTOMATA_REPO_ROOT → 从 Rscript --file= 脚本路径向上查找含 download_data/ 与 code/ 的目录。
if ("automata:paths" %in% search()) {
  invisible(TRUE)
} else {
  .automata_paths_env <- local({
    e <- new.env(parent = emptyenv())
    e$automata_repo_root <- function() {
      r <- Sys.getenv("AUTOMATA_REPO_ROOT", unset = "")
      if (nzchar(r)) return(r)
      ca <- commandArgs(trailingOnly = FALSE)
      ff <- ca[grepl("^--file=", ca)]
      if (length(ff) < 1) {
        stop("未设置 AUTOMATA_REPO_ROOT，且无法从 Rscript --file= 推断仓库根目录。", call. = FALSE)
      }
      sp <- normalizePath(sub("^--file=", "", ff[1]), winslash = "/", mustWork = TRUE)
      d <- dirname(sp)
      for (i in 1:16) {
        if (dir.exists(file.path(d, "download_data")) && dir.exists(file.path(d, "code"))) return(d)
        p <- dirname(d)
        if (p == d) break
        d <- p
      }
      stop("无法从脚本路径推断仓库根目录，请设置环境变量 AUTOMATA_REPO_ROOT。", call. = FALSE)
    }
    e$automata_path_jobs <- function() file.path(e$automata_repo_root(), "download_data", "Jobs")
    e$automata_path_code <- function() file.path(e$automata_repo_root(), "code")
    e$automata_path_data_analysis_plot <- function() file.path(e$automata_path_code(), "data_analysis_plot")
    e$automata_job_file <- function(job_id, filename) file.path(e$automata_path_jobs(), job_id, filename)
    e
  })
  attach(.automata_paths_env, name = "automata:paths", warn.conflicts = FALSE)
}
