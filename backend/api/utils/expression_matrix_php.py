"""
将表达矩阵转为 R 差异分析脚本期望的形态：制表符矩阵转置后删去最后一行
（与历史 PHP 流水线语义一致；实现以矩形矩阵与可测试性为准）。
"""
from __future__ import annotations

from pathlib import Path


def transpose_expression_file_like_php(path: Path) -> None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        raise ValueError(f"表达矩阵文件为空或不可读: {path}")
    matrix = [ln.split("\t") for ln in lines]
    if not matrix or not matrix[0]:
        raise ValueError(f"表达矩阵无有效行列: {path}")
    width = len(matrix[0])
    for i, row in enumerate(matrix):
        if len(row) != width:
            raise ValueError(
                f"表达矩阵行宽不一致（第 {i + 1} 行），无法安全转置"
            )
    transposed = [list(col) for col in zip(*matrix)]
    if transposed:
        transposed.pop()
    out = "\n".join("\t".join(row) for row in transposed)
    path.write_text(out, encoding="utf-8")
