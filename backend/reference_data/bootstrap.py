"""
MySQL 参考注释表（gene_*/mrna_*/protein_*）：与 Navicat 导出结构、R 脚本及 Python 查询列名一致。

- 启动时若表不存在：按 REFERENCE_TABLE_SPECS 建空表（CREATE TABLE IF NOT EXISTS）。
- 表已存在时：对照 SPECS 用 ALTER TABLE 补齐缺失列（不删列、不改类型），便于仅含 INSERT 的 SQL 导入。
- 若配置 REFERENCE_DATA_SQL_DIR 且表行数为 0，则用 mysql 客户端导入同名 .sql / .sql.gz。
"""
from __future__ import annotations

import gzip
import logging
import subprocess
import time
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from config.settings import settings

logger = logging.getLogger(__name__)

# 与 R 脚本、Python 查询一致。拟南芥 gene_at 不由本流程建表/导数（需用时自行建表灌数）。
REFERENCE_ANNOTATION_TABLES: tuple[str, ...] = (
    "gene_bos_taurus",
    "gene_dm",
    "gene_homo_sapiens",
    "gene_mus",
    "mrna_bos_taurus",
    "mrna_dm",
    "mrna_homo_sapiens",
    "mrna_mus",
    "protein_bos_taurus",
    "protein_dm",
    "protein_homo_sapiens",
    "protein_mus",
)

# 与开发库 Navicat 结构导出一致（仅参考注释表）；列名须与 INSERT 脚本一致（含空格等特殊名）
REFERENCE_TABLE_SPECS: dict[str, tuple[tuple[str, str], ...]] = {
    "gene_bos_taurus": (
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "TEXT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
    ),
    "gene_dm": (
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "TEXT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
    ),
    "gene_homo_sapiens": (
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "INT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
    ),
    "gene_mus": (
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "TEXT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
    ),
    "mrna_bos_taurus": (
        ("MyUnknownColumn", "INT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "TEXT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
        ("Gene_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Transcript_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Transcript_name", "TEXT NULL DEFAULT NULL"),
        ("Gene_name", "TEXT NULL DEFAULT NULL"),
        ("Transcript_type", "TEXT NULL DEFAULT NULL"),
        ("RefSeq_mRNA_ID", "TEXT NULL DEFAULT NULL"),
        ("RefSeq_mRNA_predicted_ID", "TEXT NULL DEFAULT NULL"),
    ),
    "mrna_dm": (
        ("MyUnknownColumn", "INT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "TEXT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
        ("Gene_ stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Transcript_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Gene_name", "TEXT NULL DEFAULT NULL"),
        ("Transcript_name", "TEXT NULL DEFAULT NULL"),
        ("Transcript_type", "TEXT NULL DEFAULT NULL"),
        ("FlyBase_ transcript_ID", "TEXT NULL DEFAULT NULL"),
        ("RefSeq_DNA_ID", "TEXT NULL DEFAULT NULL"),
    ),
    "mrna_homo_sapiens": (
        ("MyUnknownColumn", "INT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "TEXT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
        ("Gene_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Transcript_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("RefSeq_match_transcript_MANE_Select", "TEXT NULL DEFAULT NULL"),
        ("RefSeq_mRNA_ID", "TEXT NULL DEFAULT NULL"),
        ("RefSeq_mRNA_predicted_ID", "TEXT NULL DEFAULT NULL"),
        ("Gene_name", "TEXT NULL DEFAULT NULL"),
        ("Transcript_type", "TEXT NULL DEFAULT NULL"),
        ("Transcript_name", "TEXT NULL DEFAULT NULL"),
    ),
    "mrna_mus": (
        ("MyUnknownColumn", "INT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Description", "TEXT NULL DEFAULT NULL"),
        ("Feature", "TEXT NULL DEFAULT NULL"),
        ("Start", "INT NULL DEFAULT NULL"),
        ("End", "INT NULL DEFAULT NULL"),
        ("Chromosomes", "INT NULL DEFAULT NULL"),
        ("Nomenclature_ID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl_ID", "TEXT NULL DEFAULT NULL"),
        ("OMIM_ID", "TEXT NULL DEFAULT NULL"),
        ("Taxonomic_ID", "INT NULL DEFAULT NULL"),
        ("SwissProt_Access", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("Synonyms", "TEXT NULL DEFAULT NULL"),
        ("Gene stable ID", "TEXT NULL DEFAULT NULL"),
        ("Transcript stable ID", "TEXT NULL DEFAULT NULL"),
        ("Transcript name", "TEXT NULL DEFAULT NULL"),
        ("Gene name", "TEXT NULL DEFAULT NULL"),
        ("Transcript type", "TEXT NULL DEFAULT NULL"),
        ("RefSeq mRNA ID", "TEXT NULL DEFAULT NULL"),
        ("RefSeq mRNA predicted ID", "TEXT NULL DEFAULT NULL"),
    ),
    "protein_bos_taurus": (
        ("Entry", "TEXT NULL DEFAULT NULL"),
        ("Reviewed", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Protein names", "TEXT NULL DEFAULT NULL"),
        ("Gene Names", "TEXT NULL DEFAULT NULL"),
        ("Organism", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("RefSeq", "TEXT NULL DEFAULT NULL"),
        ("EMBL", "TEXT NULL DEFAULT NULL"),
        ("AlphaFoldDB", "TEXT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl", "TEXT NULL DEFAULT NULL"),
        ("Transcript stable ID", "TEXT NULL DEFAULT NULL"),
        ("Protein_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Protein stable ID version", "TEXT NULL DEFAULT NULL"),
        ("RefSeq peptide ID biomart", "TEXT NULL DEFAULT NULL"),
        ("RefSeq peptide predicted ID biomart", "TEXT NULL DEFAULT NULL"),
    ),
    "protein_dm": (
        ("Entry", "TEXT NULL DEFAULT NULL"),
        ("Reviewed", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Protein names", "TEXT NULL DEFAULT NULL"),
        ("Gene Names", "TEXT NULL DEFAULT NULL"),
        ("Organism", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("EMBL", "TEXT NULL DEFAULT NULL"),
        ("AlphaFoldDB", "TEXT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("RefSeq", "TEXT NULL DEFAULT NULL"),
        ("Protein_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("FlyBase transcript ID", "TEXT NULL DEFAULT NULL"),
        ("FlyBase gene ID", "TEXT NULL DEFAULT NULL"),
    ),
    "protein_homo_sapiens": (
        ("Entry", "TEXT NULL DEFAULT NULL"),
        ("Reviewed", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Protein names", "TEXT NULL DEFAULT NULL"),
        ("Gene Names", "TEXT NULL DEFAULT NULL"),
        ("Organism", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("RefSeq", "TEXT NULL DEFAULT NULL"),
        ("EMBL", "TEXT NULL DEFAULT NULL"),
        ("AlphaFoldDB", "TEXT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl", "TEXT NULL DEFAULT NULL"),
        ("Transcript stable ID", "TEXT NULL DEFAULT NULL"),
        ("Protein_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Protein stable ID version", "TEXT NULL DEFAULT NULL"),
    ),
    "protein_mus": (
        ("Entry", "TEXT NULL DEFAULT NULL"),
        ("Reviewed", "TEXT NULL DEFAULT NULL"),
        ("Symbol", "TEXT NULL DEFAULT NULL"),
        ("Protein names", "TEXT NULL DEFAULT NULL"),
        ("Gene Names", "TEXT NULL DEFAULT NULL"),
        ("Organism", "TEXT NULL DEFAULT NULL"),
        ("Length", "INT NULL DEFAULT NULL"),
        ("RefSeq", "TEXT NULL DEFAULT NULL"),
        ("EMBL", "TEXT NULL DEFAULT NULL"),
        ("AlphaFoldDB", "TEXT NULL DEFAULT NULL"),
        ("GeneID", "TEXT NULL DEFAULT NULL"),
        ("Ensembl", "TEXT NULL DEFAULT NULL"),
        ("Transcript stable ID", "TEXT NULL DEFAULT NULL"),
        ("Protein_stable_ID", "TEXT NULL DEFAULT NULL"),
        ("Protein stable ID version", "TEXT NULL DEFAULT NULL"),
    ),
}


def _bt_ident(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def _ddl_index_suffix(table: str) -> str:
    """CREATE TABLE 末尾索引（与常见查询/R 脚本一致）。"""
    if table in (
        "gene_bos_taurus",
        "gene_dm",
        "gene_homo_sapiens",
        "gene_mus",
    ):
        return (
            f",\n  KEY `ix_{table}_geneid` (`GeneID`(128)),\n"
            f"  KEY `ix_{table}_ensembl` (`Ensembl_ID`(128)),\n"
            f"  KEY `ix_{table}_symbol` (`Symbol`(128))"
        )
    if table in ("mrna_bos_taurus", "mrna_homo_sapiens"):
        return (
            f",\n  KEY `ix_{table}_refseq` (`RefSeq_mRNA_ID`(128)),\n"
            f"  KEY `ix_{table}_refseq_pred` (`RefSeq_mRNA_predicted_ID`(128))"
        )
    if table == "mrna_dm":
        return (
            ",\n  KEY `ix_mrna_dm_refseq_dna` (`RefSeq_DNA_ID`(128)),\n"
            "  KEY `ix_mrna_dm_fb_tx` (`FlyBase_ transcript_ID`(128))"
        )
    if table == "mrna_mus":
        return (
            ",\n  KEY `ix_mrna_mus_rna` (`RefSeq mRNA ID`(128)),\n"
            "  KEY `ix_mrna_mus_rna_pred` (`RefSeq mRNA predicted ID`(128))"
        )
    if table == "protein_dm":
        return (
            ",\n  KEY `ix_protein_dm_entry` (`Entry`(128)),\n"
            "  KEY `ix_protein_dm_symbol` (`Symbol`(128)),\n"
            "  KEY `ix_protein_dm_fb_gene` (`FlyBase gene ID`(128))"
        )
    if table.startswith("protein_"):
        return (
            f",\n  KEY `ix_{table}_entry` (`Entry`(128)),\n"
            f"  KEY `ix_{table}_ensembl` (`Ensembl`(128)),\n"
            f"  KEY `ix_{table}_symbol` (`Symbol`(128))"
        )
    return ""


def _ddl_for_table(name: str) -> str:
    spec = REFERENCE_TABLE_SPECS.get(name)
    if not spec:
        raise ValueError(f"未知参考表: {name}")
    col_sql = ",\n  ".join(f"{_bt_ident(cn)} {ct}" for cn, ct in spec)
    idx = _ddl_index_suffix(name)
    return f"""
CREATE TABLE IF NOT EXISTS `{name}` (
  {col_sql}{idx}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""".strip()


def _existing_mysql_columns(engine: Engine, table: str) -> set[str]:
    db = settings.DB_NAME
    with engine.connect() as conn:
        r = conn.execute(
            text(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :t"
            ),
            {"db": db, "t": table},
        )
        return {row[0] for row in r}


def _sync_reference_columns(engine: Engine, table: str) -> None:
    """按 REFERENCE_TABLE_SPECS 为已存在的表补齐缺失列（不删除、不修改已有列类型）。"""
    spec = REFERENCE_TABLE_SPECS.get(table)
    if not spec or not _table_exists(engine, table):
        return
    have = _existing_mysql_columns(engine, table)
    have_ci = {c.lower() for c in have}
    to_add = [(cn, ct) for cn, ct in spec if cn.lower() not in have_ci]
    if not to_add:
        return
    logger.info("补齐参考表 `%s` 列（%s 个新列）", table, len(to_add))
    with engine.begin() as conn:
        for cn, ct in to_add:
            conn.execute(
                text(
                    f"ALTER TABLE `{table}` ADD COLUMN {_bt_ident(cn)} {ct}"
                )
            )


def _apply_ddl(engine: Engine, tables: Iterable[str]) -> None:
    with engine.begin() as conn:
        for t in tables:
            conn.execute(text(_ddl_for_table(t)))


def _table_exists(engine: Engine, table: str) -> bool:
    return inspect(engine).has_table(table)


def _table_row_count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        r = conn.execute(text(f"SELECT COUNT(*) AS c FROM `{table}`")).scalar()
        return int(r or 0)


def _find_sql_file(base_dir: Path, table: str) -> Optional[Path]:
    for ext in (".sql", ".sql.gz"):
        p = base_dir / f"{table}{ext}"
        if p.is_file():
            return p
    return None


def _normalize_sql_line_endings(raw: bytes) -> bytes:
    """Windows CRLF / 旧式 CR → LF，减轻 mysql 客户端解析大批量 INSERT 时的异常。"""
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _mysql_cli_import(sql_path: Path) -> None:
    """使用 mysql 非交互导入；密码经环境变量 MYSQL_PWD 传入。"""
    import os
    import sys

    env = os.environ.copy()
    env["MYSQL_PWD"] = settings.DB_PASSWORD

    host = settings.DB_HOST
    port = str(settings.DB_PORT)
    user = settings.DB_USER
    db = settings.DB_NAME

    cmd = [
        "mysql",
        f"-h{host}",
        f"-P{port}",
        f"-u{user}",
        "--protocol=tcp",
        db,
    ]

    if sql_path.suffix == ".gz":
        with gzip.open(sql_path, "rb") as zf:
            raw = zf.read()
    else:
        raw = sql_path.read_bytes()

    payload = _normalize_sql_line_endings(raw)
    size_mb = len(payload) / (1024 * 1024)
    t0 = time.monotonic()
    
    # 输出进度提示到 stdout，让 CI/CD 能看到进度
    print(f"\n[导入进度] 开始导入: {sql_path.name} ({size_mb:.1f} MB)", flush=True)
    print(f"[导入进度] 预计耗时: {size_mb/10:.1f}~{size_mb/5:.1f} 分钟（取决于表大小和服务器性能）", flush=True)
    
    logger.info(
        "mysql 导入开始: %s（约 %.1f MB，大表可能需数分钟）",
        sql_path.name,
        size_mb,
    )
    
    # 勿用 BytesIO 作 stdin：部分环境下 fileno() 不可用会导致 Popen 失败
    subprocess.run(
        cmd,
        input=payload,
        env=env,
        check=True,
        capture_output=True,
        timeout=86400,
    )
    
    elapsed = time.monotonic() - t0
    print(f"[导入进度] 完成: {sql_path.name}（耗时 {elapsed:.1f} 秒）", flush=True)
    
    logger.info(
        "mysql 导入完成: %s（耗时 %.1f 秒）",
        sql_path.name,
        elapsed,
    )


def ensure_reference_annotation_tables(engine: Engine) -> None:
    """
    仅针对 MySQL：按 SPECS 建表/补列；可选从 REFERENCE_DATA_SQL_DIR 导入仅 INSERT 的 SQL。
    """
    if engine.dialect.name != "mysql":
        logger.info("当前数据库非 MySQL，跳过参考注释表（gene/mrna/protein）初始化")
        return

    try:
        sql_dir = settings.REFERENCE_DATA_SQL_DIR
        logger.info(
            "参考注释表：REFERENCE_DATA_SQL_DIR=%s",
            sql_dir or "(未设置，仅建表/补列，不自动导入 SQL)",
        )

        missing = [t for t in REFERENCE_ANNOTATION_TABLES if not _table_exists(engine, t)]
        if missing:
            logger.info("创建缺失的参考注释表: %s", ", ".join(missing))
            _apply_ddl(engine, missing)

        logger.info("参考注释表：按 SPECS 校验并补齐缺失列…")
        for t in REFERENCE_ANNOTATION_TABLES:
            _sync_reference_columns(engine, t)

        if not sql_dir:
            empty_or_unknown = [
                t
                for t in REFERENCE_ANNOTATION_TABLES
                if _table_row_count(engine, t) == 0
            ]
            if empty_or_unknown:
                logger.warning(
                    "以下参考注释表尚无数据，基因组/转录组/蛋白数据处理会失败：%s。"
                    "请将 mysqldump 导出的 SQL（或仅 INSERT）放入目录，"
                    "并设置环境变量 REFERENCE_DATA_SQL_DIR 为该目录（文件名：表名.sql 或 表名.sql.gz）",
                    ", ".join(empty_or_unknown),
                )
            return

        base = Path(sql_dir).expanduser().resolve()
        if not base.is_dir():
            logger.error("REFERENCE_DATA_SQL_DIR 不是目录: %s", base)
            return

        logger.info("参考 SQL 目录: %s（空表将依次导入，日志会显示每文件耗时）", base)

        # 统计需要导入的表数量
        tables_to_import = [
            table for table in REFERENCE_ANNOTATION_TABLES
            if _table_row_count(engine, table) == 0 and _find_sql_file(base, table)
        ]
        total_tables = len(tables_to_import)
        current_index = 0
        
        if total_tables > 0:
            print(f"\n[整体进度] 发现 {total_tables} 个参考数据表需要导入", flush=True)
            logger.info("需要导入的表数量: %d", total_tables)

        for table in REFERENCE_ANNOTATION_TABLES:
            n = _table_row_count(engine, table)
            if n > 0:
                continue
            sql_file = _find_sql_file(base, table)
            if not sql_file:
                logger.warning(
                    "表 `%s` 为空且未找到 %s.sql / %s.sql.gz（目录 %s）",
                    table,
                    table,
                    table,
                    base,
                )
                continue
            
            current_index += 1
            print(f"\n{'='*60}", flush=True)
            print(f"[整体进度] 正在导入第 {current_index}/{total_tables} 个表: {table}", flush=True)
            print(f"{'='*60}\n", flush=True)
            
            try:
                logger.info("导入参考数据: %s <- %s", table, sql_file.name)
                _sync_reference_columns(engine, table)
                _mysql_cli_import(sql_file)
                after = _table_row_count(engine, table)
                logger.info("表 `%s` 导入后行数: %s", table, after)
                print(f"[整体进度] 表 {table} 导入完成，共 {after} 行\n", flush=True)
            except FileNotFoundError:
                logger.error(
                    "未找到 mysql 客户端，无法导入 %s。请在镜像中安装 default-mysql-client，"
                    "或在主机上导入后再启动。",
                    sql_file,
                )
                raise
            except subprocess.CalledProcessError as e:
                err_txt = (e.stderr or e.stdout or b"").decode(
                    "utf-8", errors="replace"
                )[:4000]
                if "Unknown column" in err_txt and "42S22" in err_txt:
                    logger.warning(
                        "表 `%s` 导入因列不匹配失败，按 SPECS 再次补齐列后重试一次",
                        table,
                    )
                    _sync_reference_columns(engine, table)
                    _mysql_cli_import(sql_file)
                    after = _table_row_count(engine, table)
                    logger.info("表 `%s` 导入后行数: %s", table, after)
                else:
                    logger.error("导入 %s 失败: %s", sql_file, err_txt[:2000])
                    raise

    except Exception:
        logger.exception("参考注释表初始化失败")
        raise
