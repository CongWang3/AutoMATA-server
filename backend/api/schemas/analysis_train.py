"""分析并训练请求/响应"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

_SUP = frozenset(
    ("cnn", "lstm", "rnn", "mlp", "autoencoder", "transformer", "rbfn", "som", "all")
)


class AnalysisTrainAnalysisParams(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    organism: str = Field(...)
    data_type: str = Field(...)
    gene_nomenclature: str = Field(...)
    fc: float = Field(1.0, ge=0)
    padj: float = Field(0.05, ge=0, le=1)
    correction: str = Field("BH")

    @field_validator("data_type")
    @classmethod
    def _dt(cls, v: str) -> str:
        s = str(v).strip().lower()
        if s in ("read_counts", "read count", "counts"):
            return "read_counts"
        if s == "fpkm":
            return "fpkm"
        raise ValueError("data_type 须为 read_counts 或 fpkm")

    @field_validator("gene_nomenclature")
    @classmethod
    def _gn(cls, v: str) -> str:
        s = str(v).strip().lower()
        m = {
            "symbol": "symbol",
            "gene_symbol": "symbol",
            "ensembl": "ensembl",
            "ensembl_id": "ensembl",
            "gene_id": "gene_id",
            "ncbi": "gene_id",
        }
        if s not in m:
            raise ValueError("gene_nomenclature 须为 symbol / ensembl / gene_id")
        return m[s]

    @field_validator("organism")
    @classmethod
    def _org(cls, v: str) -> str:
        ok = {
            "Homo_sapiens",
            "Bovine",
            "Mus_musculus",
            "Drosophila_melanogaster",
        }
        if v not in ok:
            raise ValueError(f"organism 须为之一: {sorted(ok)}")
        return v

    @field_validator("correction")
    @classmethod
    def _corr(cls, v: str) -> str:
        ok = {"BH", "BY", "holm", "hochberg", "hommel", "bonferroni", "none"}
        if v not in ok:
            raise ValueError(f"correction 须为之一: {sorted(ok)}")
        return v


class AnalysisTrainTaskCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    task_name: str = Field(..., min_length=1, max_length=200)
    model_type: str = Field(...)
    parameters: Dict[str, Any] = Field(...)
    dataset_path: Optional[str] = Field(None, max_length=500)
    group_info_file_id: str = Field(..., min_length=1)
    analysis: AnalysisTrainAnalysisParams
    email: Optional[str] = Field(None, max_length=200)

    @field_validator("dataset_path")
    @classmethod
    def _dsp(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v.startswith("file://"):
            p = v[7:]
            if not re.match(r"^[\w\-_.]+$", p):
                raise ValueError("file:// 后的路径包含非法字符")
        else:
            if not re.match(r"^[/\w\-_.]+$", v):
                raise ValueError("数据集路径包含非法字符")
        if ".." in v or "~" in v:
            raise ValueError("数据集路径不能包含相对路径符号")
        return v

    @field_validator("model_type")
    @classmethod
    def _mt(cls, v: str) -> str:
        lv = v.lower()
        if lv not in _SUP:
            raise ValueError(f"仅支持监督模型: {sorted(_SUP)}")
        return lv

    @field_validator("parameters", mode="before")
    @classmethod
    def _params(cls, v: Any) -> Dict[str, Any]:
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError("parameters 须为合法 JSON 对象") from e
        if not isinstance(v, dict):
            raise ValueError("parameters 须为字典")
        return v

    @field_validator("group_info_file_id")
    @classmethod
    def _gid(cls, v: str) -> str:
        s = str(v).strip()
        if not re.match(r"^[\w\-_.]+$", s):
            raise ValueError("group_info_file_id 无效")
        return s


class AnalysisTrainTaskResponse(BaseModel):
    task_name: str
    model_type: str
    status: str
    job_id: str
    created_at: datetime
    message: str
    parameters: Dict[str, Any]
    progress: int = 0
    current_step: Optional[str] = None
    result_file: Optional[str] = None
    error_message: Optional[str] = None
