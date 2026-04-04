"""
仓库根目录与常用路径：与后端 settings 一致，优先读环境变量（开发/生产/Docker 通用）。

环境变量（与 backend/config/settings.py 对齐）：
  REPO_ROOT 或 AUTOMATA_REPO_ROOT — 仓库根（含 code/、download_data/）
未设置时：以本文件所在目录为 code/，父目录为仓库根（适用于本地从仓库根运行脚本）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_CODE_DIR = Path(__file__).resolve().parent


def _paths_config_path() -> Path:
    return _CODE_DIR / "automata_paths.config.json"


def _repo_from_optional_json() -> Path | None:
    p = _paths_config_path()
    if not p.is_file():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        root = (raw or {}).get("REPO_ROOT") or (raw or {}).get("AUTOMATA_REPO_ROOT")
        if root and str(root).strip():
            return Path(str(root).strip()).expanduser().resolve()
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


def repo_root() -> Path:
    env = (os.environ.get("REPO_ROOT") or os.environ.get("AUTOMATA_REPO_ROOT") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    j = _repo_from_optional_json()
    if j is not None:
        return j
    return _CODE_DIR.parent


def path_code() -> Path:
    return repo_root() / "code"


def path_jobs() -> Path:
    return repo_root() / "download_data" / "Jobs"


def path_data_analysis_plot() -> Path:
    return path_code() / "data_analysis_plot"


def path_download_data() -> Path:
    return repo_root() / "download_data"
