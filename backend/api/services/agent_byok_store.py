"""
用户级 Agent BYOK（Qwen / DeepSeek）本地 JSON 存储，无 MySQL 新表。

路径：{AGENT_BYOK_DIR 或 REPO_ROOT/data/agent_byok}/{user_id}.json
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    import fcntl  # type: ignore
except ImportError:  # Windows 等环境
    fcntl = None  # type: ignore


def _byok_root(repo_root: Path, override_dir: str) -> Path:
    raw = (override_dir or "").strip()
    if raw:
        return Path(raw)
    return repo_root / "data" / "agent_byok"


def _user_file(repo_root: Path, override_dir: str, user_id: str) -> Path:
    # user_id 来自已认证用户，仅允许数字主键
    safe = str(int(user_id))
    return _byok_root(repo_root, override_dir) / f"{safe}.json"


def load_byok(repo_root: Path, override_dir: str, user_id: str) -> Dict[str, str]:
    """返回 {qwen?, deepseek?}，仅包含非空字符串。"""
    path = _user_file(repo_root, override_dir, user_id)
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            if fcntl:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                except OSError:
                    pass
            try:
                raw = f.read()
            finally:
                if fcntl:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except OSError:
                        pass
    except OSError as e:
        logger.warning("[agent_byok] 读取失败 user_id=%s: %s", user_id, type(e).__name__)
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("[agent_byok] JSON 无效 user_id=%s", user_id)
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, str] = {}
    for k in ("qwen", "deepseek"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out


def save_byok_partial(
    repo_root: Path,
    override_dir: str,
    user_id: str,
    partial: Dict[str, Any],
) -> None:
    """
    合并写入。partial 仅处理键 qwen / deepseek：
    - 值为非空 str：写入
    - 值为空 str：删除该键
    """
    root = _byok_root(repo_root, override_dir)
    root.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(root, 0o700)
    except OSError:
        pass

    path = _user_file(repo_root, override_dir, user_id)
    current = load_byok(repo_root, override_dir, user_id)

    for key in ("qwen", "deepseek"):
        if key not in partial:
            continue
        val = partial[key]
        if val is None:
            continue
        if not isinstance(val, str):
            continue
        s = val.strip()
        if not s:
            current.pop(key, None)
        else:
            current[key] = s

    tmp = path.with_suffix(path.suffix + ".tmp")
    content = json.dumps(current, ensure_ascii=False, indent=2)
    with open(tmp, "w", encoding="utf-8") as f:
        if fcntl:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            except OSError:
                pass
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
        if fcntl:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    tmp.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass

    if not current and path.is_file():
        try:
            path.unlink()
        except OSError:
            pass
