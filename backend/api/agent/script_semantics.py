"""
脚本语义卡 + 规则检查器（映射表驱动）
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Set

SCRIPT_PATH_RE = re.compile(r"(?P<path>[A-Za-z0-9_./\\-]+\.(?:py|r|R))")


def _script_basename(path: str) -> str:
    p = (path or "").replace("\\", "/").strip()
    return p.rsplit("/", 1)[-1] if p else ""


def _normalize_script_key(path: str) -> str:
    return (path or "").replace("\\", "/").strip().lower()


def detect_script_from_context(config_summary: str, log_tail: str) -> Dict[str, Any]:
    text_sources = [config_summary or "", log_tail or ""]
    for idx, txt in enumerate(text_sources):
        for m in SCRIPT_PATH_RE.finditer(txt):
            p = m.group("path")
            if not p:
                continue
            base = _script_basename(p)
            lang = "r" if base.lower().endswith(".r") else "python"
            return {
                "script_path": p,
                "script_name": base,
                "script_path_key": _normalize_script_key(p),
                "language": lang,
                "source": "config_summary" if idx == 0 else "log_tail",
            }
    return {"script_path": "", "script_name": "", "script_path_key": "", "language": "", "source": ""}


def _append(checks: List[Dict[str, Any]], cid: str, level: str, title: str, detail: str, evidence: List[str]) -> None:
    checks.append({"id": cid, "level": level, "title": title, "detail": detail, "evidence": evidence[:5]})


def _rule_py_cuda(ctx: Dict[str, Any], checks: List[Dict[str, Any]]) -> None:
    log_text = ctx["log_text"]
    exc_msg = ctx["exc_msg"]
    if "torch not compiled with cuda enabled" in log_text or ("cuda" in exc_msg and "not compiled" in exc_msg):
        _append(checks, "py_cuda_unavailable", "critical", "CUDA 不可用", "运行环境不支持 CUDA，但脚本尝试使用 GPU。", ["torch not compiled with cuda enabled"])


def _rule_py_nameerror(ctx: Dict[str, Any], checks: List[Dict[str, Any]]) -> None:
    if "nameerror" in ctx["exc_type"] or "nameerror" in ctx["log_text"]:
        _append(checks, "py_name_error", "critical", "Python 变量未定义", "出现 NameError，通常是变量名错误或作用域问题。", [ctx["exc_raw"]])


def _rule_r_mapping(ctx: Dict[str, Any], checks: List[Dict[str, Any]]) -> None:
    if "no gene can be mapped" in ctx["log_text"]:
        _append(checks, "r_gene_mapping_failed", "critical", "基因映射失败", "输入基因未映射到注释库，常见原因为物种代码或符号体系不匹配。", ["No gene can be mapped"])


def _rule_r_pkg(ctx: Dict[str, Any], checks: List[Dict[str, Any]]) -> None:
    if "there is no package called" in ctx["log_text"]:
        _append(checks, "r_pkg_missing", "critical", "R 依赖包缺失", "运行环境缺少 R 包，需要先安装依赖。", ["there is no package called"])


def _rule_param_dropout(ctx: Dict[str, Any], checks: List[Dict[str, Any]]) -> None:
    params = ctx["input_params"] if isinstance(ctx["input_params"], dict) else {}
    if "dropout" not in params:
        return
    try:
        dv = float(params["dropout"])
        if dv < 0 or dv > 1:
            _append(checks, "param_dropout_range", "warning", "dropout 参数超范围", "dropout 合法范围通常是 [0, 1]。", [f"dropout={params['dropout']}"])
    except Exception:
        _append(checks, "param_dropout_type", "warning", "dropout 参数非数值", "dropout 需要可解析为数值。", [f"dropout={params.get('dropout')}"])


def _rule_kegg_specific(ctx: Dict[str, Any], checks: List[Dict[str, Any]]) -> None:
    log_text = ctx["log_text"]
    if "kegg" in log_text and "no gene can be mapped" in log_text:
        _append(
            checks,
            "kegg_specific_mapping",
            "critical",
            "KEGG 映射率为 0",
            "kegg_enrichment 会尝试 SYMBOL2EG，但当前输入仍未映射到 KEGG 所需 ID。",
            ["kegg_enrichment.R", "No gene can be mapped"],
        )


RULE_HANDLERS: Dict[str, Callable[[Dict[str, Any], List[Dict[str, Any]]], None]] = {
    "py_cuda_unavailable": _rule_py_cuda,
    "py_name_error": _rule_py_nameerror,
    "r_gene_mapping_failed": _rule_r_mapping,
    "r_pkg_missing": _rule_r_pkg,
    "param_dropout": _rule_param_dropout,
    "kegg_specific_mapping": _rule_kegg_specific,
}


# 每个脚本对应语义卡与规则，后续新增脚本仅需增补此映射表
SCRIPT_SEMANTIC_MAP: Dict[str, Dict[str, Any]] = {
    # R: data analysis
    "kegg_enrichment.r": {
        "job_type": "data_analysis",
        "summary": "KEGG 富集分析，含 SYMBOL2EG 映射。",
        "required_inputs": ["gene list", "species", "pvalue/padj"],
        "common_failure_patterns": ["kegg_mapping_failed", "species_code_mismatch"],
        "result_hints": ["先看映射率和有效基因数", "再解读显著通路"],
        "rules": ["r_gene_mapping_failed", "r_pkg_missing", "kegg_specific_mapping"],
    },
    "go_enrichment.r": {
        "job_type": "data_analysis",
        "summary": "GO 富集（BP/CC/MF）分析。",
        "required_inputs": ["gene list", "annotation db", "padj cutoff"],
        "common_failure_patterns": ["id_mapping_failed", "annotation_db_not_available"],
        "result_hints": ["分 BP/CC/MF 解读", "关注显著条目数量"],
        "rules": ["r_gene_mapping_failed", "r_pkg_missing"],
    },
    "venn.r": {"job_type": "data_analysis", "summary": "Venn 集合交并分析与作图。", "required_inputs": ["group lists"], "common_failure_patterns": ["empty_group", "plot_save_failed"], "result_hints": ["关注交集大小与生物意义"], "rules": ["r_pkg_missing"]},
    "ppi.r": {"job_type": "data_analysis", "summary": "PPI 网络构建。", "required_inputs": ["gene/protein list", "species"], "common_failure_patterns": ["stringdb_query_failed"], "result_hints": ["结合 hub 节点解释"], "rules": ["r_pkg_missing"]},
    "pca.r": {"job_type": "data_analysis", "summary": "PCA 降维可视化。", "required_inputs": ["expression matrix", "sample labels"], "common_failure_patterns": ["non_numeric_matrix"], "result_hints": ["关注 PC1/PC2 分离度"], "rules": ["r_pkg_missing"]},
    "dumbbell.r": {"job_type": "data_analysis", "summary": "哑铃图可视化。", "required_inputs": ["two-condition values"], "common_failure_patterns": ["missing_columns"], "result_hints": ["比较差值方向与幅度"], "rules": ["r_pkg_missing"]},
    "dumbbell_bar.r": {"job_type": "data_analysis", "summary": "条形+哑铃组合图。", "required_inputs": ["group values"], "common_failure_patterns": ["missing_columns"], "result_hints": ["看组间差异趋势"], "rules": ["r_pkg_missing"]},
    "df_cluster_heatmap.r": {"job_type": "data_analysis", "summary": "聚类热图分析。", "required_inputs": ["numeric matrix"], "common_failure_patterns": ["distance_calc_failed"], "result_hints": ["关注聚类分群与模式"], "rules": ["r_pkg_missing"]},
    "df_count_normalized.r": {"job_type": "data_analysis", "summary": "count 标准化处理。", "required_inputs": ["count matrix"], "common_failure_patterns": ["normalization_failed"], "result_hints": ["确认归一化后分布"], "rules": ["r_pkg_missing"]},
    "cor_heatmap.r": {"job_type": "data_analysis", "summary": "相关性热图。", "required_inputs": ["numeric matrix"], "common_failure_patterns": ["cor_failed"], "result_hints": ["关注高相关模块"], "rules": ["r_pkg_missing"]},
    "volcano_gsea_padj.r": {"job_type": "data_analysis", "summary": "差异 + GSEA/富集综合输出。", "required_inputs": ["DE results", "thresholds"], "common_failure_patterns": ["all_filtered", "gsea_empty"], "result_hints": ["先看火山图分布"], "rules": ["r_pkg_missing"]},
    "deseq2_read_count.r": {"job_type": "data_analysis", "summary": "DESeq2 差异分析。", "required_inputs": ["raw count", "group design"], "common_failure_patterns": ["design_invalid"], "result_hints": ["看 padj 与 fold change"], "rules": ["r_pkg_missing"]},
    "limma_fpkm_df.r": {"job_type": "data_analysis", "summary": "limma 差异分析。", "required_inputs": ["expression matrix", "group info"], "common_failure_patterns": ["design_invalid"], "result_hints": ["结合阈值解释上下调"], "rules": ["r_pkg_missing"]},
    "integration_pvalue.r": {"job_type": "data_analysis", "summary": "多结果 p 值整合。", "required_inputs": ["multiple p-value tables"], "common_failure_patterns": ["merge_failed"], "result_hints": ["关注综合显著项"], "rules": ["r_pkg_missing"]},
    "mrna_mysql2tpm.r": {"job_type": "data_processing", "summary": "mRNA 数据转 TPM。", "required_inputs": ["raw matrix"], "common_failure_patterns": ["input_format_invalid"], "result_hints": ["检查 TPM 分布"], "rules": ["r_pkg_missing"]},
    "mysql2tpm.r": {"job_type": "data_processing", "summary": "表达矩阵转 TPM。", "required_inputs": ["raw matrix"], "common_failure_patterns": ["input_format_invalid"], "result_hints": ["检查归一化结果"], "rules": ["r_pkg_missing"]},
    "automata_paths.r": {"job_type": "infra", "summary": "R 路径工具脚本。", "required_inputs": [], "common_failure_patterns": ["path_not_found"], "result_hints": [], "rules": []},
    "check_container_r_packages.r": {"job_type": "infra", "summary": "容器依赖检查脚本。", "required_inputs": [], "common_failure_patterns": ["missing_packages"], "result_hints": [], "rules": ["r_pkg_missing"]},
    "install_plot_deps.r": {"job_type": "infra", "summary": "绘图依赖安装脚本。", "required_inputs": [], "common_failure_patterns": ["install_failed"], "result_hints": [], "rules": []},
    "predownload_stringdb_cache.r": {"job_type": "infra", "summary": "预下载 STRINGDB 缓存。", "required_inputs": [], "common_failure_patterns": ["network_failed"], "result_hints": [], "rules": []},
    "test_prot_id_converse.r": {"job_type": "test", "summary": "蛋白 ID 转换测试脚本。", "required_inputs": ["protein ids"], "common_failure_patterns": ["mapping_failed"], "result_hints": [], "rules": ["r_gene_mapping_failed"]},
    # Python: train/use model + utils
    "general.py": {"job_type": "model_use", "summary": "通用模型应用评估逻辑。", "required_inputs": ["test dataset", "model output"], "common_failure_patterns": ["name_error_or_shape_mismatch"], "result_hints": ["解释 acc/precision/recall/f1"], "rules": ["py_name_error", "param_dropout"]},
    "autoencoder.py": {"job_type": "model_train", "summary": "自编码器训练脚本。", "required_inputs": ["train data", "hyper params"], "common_failure_patterns": ["shape_mismatch", "loss_nan"], "result_hints": ["关注重构误差"], "rules": ["py_name_error", "py_cuda_unavailable", "param_dropout"]},
    "cnn.py": {"job_type": "model_train", "summary": "CNN 训练脚本。", "required_inputs": ["train data", "hyper params"], "common_failure_patterns": ["shape_mismatch", "cuda_not_available"], "result_hints": ["关注过拟合"], "rules": ["py_name_error", "py_cuda_unavailable", "param_dropout"]},
    "deepcluster.py": {"job_type": "model_train", "summary": "DeepCluster 无监督训练。", "required_inputs": ["input features", "cluster params"], "common_failure_patterns": ["cuda_not_available", "cluster_instability"], "result_hints": ["关注聚类分布"], "rules": ["py_cuda_unavailable", "py_name_error"]},
    "vae.py": {"job_type": "model_train", "summary": "VAE 训练脚本。", "required_inputs": ["train data"], "common_failure_patterns": ["loss_nan"], "result_hints": ["关注重构与 KL 平衡"], "rules": ["py_cuda_unavailable", "param_dropout"]},
    "ladder.py": {"job_type": "model_train", "summary": "Ladder 半监督训练。", "required_inputs": ["labeled+unlabeled data"], "common_failure_patterns": ["pseudo_label_instability"], "result_hints": ["关注半监督提升幅度"], "rules": ["py_cuda_unavailable", "param_dropout"]},
    "pseudo.py": {"job_type": "model_train", "summary": "Pseudo-label 半监督训练。", "required_inputs": ["labeled+unlabeled data"], "common_failure_patterns": ["pseudo_label_noise"], "result_hints": ["关注伪标签质量"], "rules": ["py_cuda_unavailable", "param_dropout"]},
    "rbfn.py": {"job_type": "model_train", "summary": "RBFN 训练脚本。", "required_inputs": ["train data"], "common_failure_patterns": ["center_init_failed"], "result_hints": ["关注核中心设置"], "rules": ["py_name_error"]},
    "som.py": {"job_type": "model_task", "summary": "SOM 训练/应用脚本。", "required_inputs": ["features"], "common_failure_patterns": ["topology_mismatch"], "result_hints": ["关注聚类拓扑"], "rules": ["py_name_error"]},
    "lstm.py": {"job_type": "model_train", "summary": "LSTM 训练脚本。", "required_inputs": ["sequence data"], "common_failure_patterns": ["sequence_shape_mismatch"], "result_hints": ["关注时序模式"], "rules": ["py_cuda_unavailable", "param_dropout"]},
    "rnn.py": {"job_type": "model_train", "summary": "RNN 训练脚本。", "required_inputs": ["sequence data"], "common_failure_patterns": ["gradient_issue"], "result_hints": ["关注梯度稳定性"], "rules": ["py_cuda_unavailable", "param_dropout"]},
    "transformer.py": {"job_type": "model_train", "summary": "Transformer 训练脚本。", "required_inputs": ["token/feature sequence"], "common_failure_patterns": ["memory_oom", "shape_mismatch"], "result_hints": ["关注注意力与泛化"], "rules": ["py_cuda_unavailable", "param_dropout"]},
    "mlp.py": {"job_type": "model_train", "summary": "MLP 训练脚本。", "required_inputs": ["tabular features"], "common_failure_patterns": ["shape_mismatch"], "result_hints": ["关注基线表现"], "rules": ["py_cuda_unavailable", "param_dropout"]},
    "integration.py": {"job_type": "model_train", "summary": "集成训练流程。", "required_inputs": ["multi-model artifacts"], "common_failure_patterns": ["merge_failed"], "result_hints": ["关注融合收益"], "rules": ["py_name_error"]},
    "predict_ladder.py": {"job_type": "model_use", "summary": "Ladder 模型应用脚本。", "required_inputs": ["model file", "test data"], "common_failure_patterns": ["model_load_failed"], "result_hints": ["关注预测分布"], "rules": ["py_name_error"]},
    "predict_pseudo.py": {"job_type": "model_use", "summary": "Pseudo 模型应用脚本。", "required_inputs": ["model file", "test data"], "common_failure_patterns": ["model_load_failed"], "result_hints": ["关注预测分布"], "rules": ["py_name_error"]},
    "predict_deepcluster.py": {"job_type": "model_use", "summary": "DeepCluster 模型应用脚本。", "required_inputs": ["model file", "test data"], "common_failure_patterns": ["model_load_failed"], "result_hints": ["关注簇分配"], "rules": ["py_name_error"]},
    "predict_vae.py": {"job_type": "model_use", "summary": "VAE 模型应用脚本。", "required_inputs": ["model file", "test data"], "common_failure_patterns": ["model_load_failed"], "result_hints": ["关注重构质量"], "rules": ["py_name_error"]},
    "dataprocess.py": {"job_type": "model_task", "summary": "模型数据预处理脚本。", "required_inputs": ["raw dataset"], "common_failure_patterns": ["column_missing", "type_cast_failed"], "result_hints": ["确认预处理后样本数"], "rules": []},
    "earlystopping.py": {"job_type": "model_utils", "summary": "EarlyStopping 工具。", "required_inputs": [], "common_failure_patterns": ["state_tracking_error"], "result_hints": [], "rules": []},
    "regularization.py": {"job_type": "model_utils", "summary": "正则化工具。", "required_inputs": [], "common_failure_patterns": ["nan_loss"], "result_hints": [], "rules": []},
    "focalloss.py": {"job_type": "model_utils", "summary": "FocalLoss 工具。", "required_inputs": [], "common_failure_patterns": ["target_shape_invalid"], "result_hints": [], "rules": []},
    "plot_utils.py": {"job_type": "model_utils", "summary": "训练绘图工具。", "required_inputs": [], "common_failure_patterns": ["save_failed"], "result_hints": [], "rules": []},
    "minisom.py": {"job_type": "model_utils", "summary": "MiniSom 工具脚本。", "required_inputs": [], "common_failure_patterns": ["topology_error"], "result_hints": [], "rules": []},
    "mega_case_study.py": {"job_type": "model_utils", "summary": "SOM 案例脚本。", "required_inputs": [], "common_failure_patterns": ["example_data_missing"], "result_hints": [], "rules": []},
    "ann.py": {"job_type": "model_utils", "summary": "ANN 辅助脚本。", "required_inputs": [], "common_failure_patterns": ["shape_mismatch"], "result_hints": [], "rules": ["py_name_error"]},
    "automata_paths.py": {"job_type": "infra", "summary": "Python 路径工具脚本。", "required_inputs": [], "common_failure_patterns": ["path_not_found"], "result_hints": [], "rules": []},
}


def _generic_semantic_card(script_name: str, language: str, job_type: str) -> Dict[str, Any]:
    return {
        "script_name": script_name or "unknown",
        "language": language or "unknown",
        "job_type": job_type or "unknown",
        "summary": "通用脚本语义卡（未命中映射表）",
        "required_inputs": [],
        "common_failure_patterns": ["input_file_missing", "invalid_parameter_range", "runtime_dependency_missing"],
        "result_hints": [],
        "rules": [],
    }


@lru_cache(maxsize=1)
def _semantic_map_by_basename() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for k, v in SCRIPT_SEMANTIC_MAP.items():
        key = _normalize_script_key(k)
        base = _script_basename(key)
        if base and base not in out:
            out[base] = v
    return out


def _resolve_semantic_item(script_path: str, script_name: str) -> Dict[str, Any]:
    # 1) 路径优先（支持相对路径/绝对路径中包含 code/... 的后缀）
    pkey = _normalize_script_key(script_path)
    if pkey:
        for key, item in SCRIPT_SEMANTIC_MAP.items():
            k = _normalize_script_key(key)
            if pkey == k or pkey.endswith("/" + k) or ("/code/" + k) in pkey:
                return item

    # 2) basename 兜底
    base = _script_basename(_normalize_script_key(script_name))
    if base:
        by_base = _semantic_map_by_basename()
        if base in by_base:
            return by_base[base]

    return {}


def _build_semantic_card(script_path: str, script_name: str, language: str, job_type: str) -> Dict[str, Any]:
    item = _resolve_semantic_item(script_path, script_name)
    if not item:
        return _generic_semantic_card(script_name, language, job_type)
    lang_guess = "r" if _normalize_script_key(script_name).endswith(".r") else "python"
    return {
        "script_name": script_name,
        "language": language or lang_guess,
        "job_type": item.get("job_type") or job_type or "unknown",
        "summary": item.get("summary", ""),
        "required_inputs": item.get("required_inputs", []),
        "common_failure_patterns": item.get("common_failure_patterns", []),
        "result_hints": item.get("result_hints", []),
        "rules": item.get("rules", []),
    }


def _run_rule_checker(*, card: Dict[str, Any], language: str, log_tail: str, root_cause: Dict[str, Any], input_params: Any) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    ctx = {
        "log_text": (log_tail or "").lower(),
        "exc_type": str((root_cause or {}).get("exception_type") or "").lower(),
        "exc_msg": str((root_cause or {}).get("exception_message") or "").lower(),
        "exc_raw": str((root_cause or {}).get("exception_message") or ""),
        "input_params": input_params,
    }

    selected_rules: List[str] = []
    if language == "python":
        selected_rules += ["py_cuda_unavailable", "py_name_error"]
    elif language == "r":
        selected_rules += ["r_gene_mapping_failed", "r_pkg_missing"]
    selected_rules += card.get("rules", [])
    selected_rules += ["param_dropout"]

    dedup_rules: List[str] = []
    seen = set()
    for rid in selected_rules:
        if rid in seen:
            continue
        seen.add(rid)
        dedup_rules.append(rid)

    for rid in dedup_rules:
        handler = RULE_HANDLERS.get(rid)
        if handler:
            handler(ctx, checks)

    if not checks:
        _append(checks, "checker_no_hit", "info", "未命中显式规则", "未匹配到确定性规则，请结合 root_cause 与代码片段继续分析。", [card.get("summary", "")])
    return checks


def build_semantic_context(*, job_type: str, config_summary: str, log_tail: str, root_cause: Dict[str, Any], input_params: Any) -> Dict[str, Any]:
    script_info = detect_script_from_context(config_summary, log_tail)
    script_path = str(script_info.get("script_path") or "")
    script_name = str(script_info.get("script_name") or "")
    language = str(script_info.get("language") or "") or str((root_cause or {}).get("language") or "")
    if language == "python" and not script_name:
        script_name = "unknown.py"
    if language == "r" and not script_name:
        script_name = "unknown.R"

    card = _build_semantic_card(script_path, script_name, language, job_type)
    checks = _run_rule_checker(card=card, language=language, log_tail=log_tail, root_cause=root_cause, input_params=input_params)
    return {"script_detection": script_info, "semantic_card": card, "checker_results": checks}


@lru_cache(maxsize=1)
def get_semantic_coverage(repo_root: str = "/xp/www/AutoMATA") -> Dict[str, Any]:
    """
    统计 code 目录下 R/Python 脚本的语义卡覆盖情况。
    """
    root = Path(repo_root)
    code_dir = root / "code"
    if not code_dir.exists():
        return {
            "enabled": False,
            "reason": f"code_dir_not_found: {code_dir}",
            "mapped_total": len(SCRIPT_SEMANTIC_MAP),
            "detected_total": 0,
            "covered_total": 0,
            "uncovered_total": 0,
            "uncovered_examples": [],
        }

    detected: Set[str] = set()
    for ext in ("*.py", "*.R", "*.r"):
        for p in code_dir.rglob(ext):
            rel = _normalize_script_key(str(p.relative_to(code_dir)))
            detected.add(rel)

    covered: Set[str] = set()
    uncovered: List[str] = []
    for rel in sorted(detected):
        item = _resolve_semantic_item(rel, _script_basename(rel))
        if item:
            covered.add(rel)
        else:
            uncovered.append(rel)

    return {
        "enabled": True,
        "mapped_total": len(SCRIPT_SEMANTIC_MAP),
        "detected_total": len(detected),
        "covered_total": len(covered),
        "uncovered_total": len(uncovered),
        "coverage_ratio": round((len(covered) / len(detected)) if detected else 1.0, 4),
        "uncovered_examples": uncovered[:30],
    }
