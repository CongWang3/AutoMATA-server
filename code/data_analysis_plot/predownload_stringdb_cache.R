#!/usr/bin/env Rscript
## One-time pre-download script for STRINGdb cache.
## Target versions (per user): R 4.4.2, STRINGdb 2.18.0
##
## It will populate the cache directory used by ppi.R:
##   file.path(automata_path_data_analysis_plot(), "stringdb_cache")
##
## After this cache is populated, ppi.R's:
##   - string_db$map(...)
##   - string_db$get_interactions(hit)
## should run offline (no downloads), as long as the cache directory is present.
##
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
      stop("找不到 code/automata_paths.R；请设置 AUTOMATA_REPO_ROOT。", call. = FALSE)
  }
}))
suppressPackageStartupMessages(library(STRINGdb))

cache_dir <- file.path(automata_path_data_analysis_plot(), "stringdb_cache")
dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)

options(timeout = 300000)

species_list <- c(
  Homo_sapiens = 9606,
  Mus_musculus = 10090,
  Bos_taurus = 9913,
  Drosophila_melanogaster = 7227
)

message("STRINGdb cache dir: ", cache_dir)

download_if_missing <- function(url, destfile) {
  if (file.exists(destfile)) {
    message("Exists: ", basename(destfile))
    return(invisible(TRUE))
  }
  message("Downloading: ", url)
  ok <- tryCatch(
    {
      utils::download.file(url, destfile = destfile, mode = "wb", quiet = FALSE)
      TRUE
    },
    error = function(e) {
      message("Download failed: ", conditionMessage(e))
      FALSE
    }
  )
  invisible(ok)
}

for (nm in names(species_list)) {
  sp <- unname(species_list[[nm]])
  message("\n=== Preloading STRINGdb cache files for ", nm, " (species=", sp, ") ===")

  # STRINGdb 2.18.0 downloads these on-demand:
  # - protein.info... via get_proteins()
  # - protein.aliases... via map()
  # - protein.links... via get_interactions()
  # We download all three explicitly into input_directory so ppi.R can run offline.
  base <- "https://stringdb-downloads.org/download"
  v <- "v12.0"

  files <- list(
    info = list(
      subdir = paste0("protein.info.", v),
      name = paste0(sp, ".protein.info.", v, ".txt.gz")
    ),
    aliases = list(
      subdir = paste0("protein.aliases.", v),
      name = paste0(sp, ".protein.aliases.", v, ".txt.gz")
    ),
    links = list(
      subdir = paste0("protein.links.", v),
      name = paste0(sp, ".protein.links.", v, ".txt.gz")
    )
  )

  for (f in files) {
    url <- paste0(base, "/", f$subdir, "/", f$name)
    dest <- file.path(cache_dir, f$name)
    download_if_missing(url, dest)
  }
}

message("\nAll done. Cache dir: ", cache_dir)

