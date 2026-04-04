"""
MySQL 参考注释表（gene_*/mrna_*/protein_*）：与 code/mysql2TPM.R、mrna_mysql2TPM.R、
data_process_service 中的查询字段对齐。

- 启动时若表不存在则创建空表（幂等）。
- 若配置 REFERENCE_DATA_SQL_DIR 且表行数为 0，则用 mysql 客户端导入同名 .sql / .sql.gz。
  数据文件建议为 mysqldump 导出的 INSERT 片段，或仅含 INSERT 的脚本。
"""
from __future__ import annotations

import gzip
import logging
import subprocess
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from config.settings import settings

logger = logging.getLogger(__name__)

# 与 R 脚本、Python 查询一致；含拟南芥 gene_at（mysql2TPM.R）
REFERENCE_ANNOTATION_TABLES: tuple[str, ...] = (
    "gene_bos_taurus",
    "gene_dm",
    "gene_homo_sapiens",
    "gene_mus",
    "gene_at",
    "mrna_bos_taurus",
    "mrna_dm",
    "mrna_homo_sapiens",
    "mrna_mus",
    "protein_bos_taurus",
    "protein_dm",
    "protein_homo_sapiens",
    "protein_mus",
)


# 与 mysqldump / Release 中 gene_*.sql 的 INSERT 列一致（避免 Unknown column 'Description' 等）
_GENE_LIKE_COLUMN_DEFS: tuple[tuple[str, str], ...] = (
    ("GeneID", "BIGINT UNSIGNED DEFAULT NULL"),
    ("Symbol", "VARCHAR(512) DEFAULT NULL"),
    ("Description", "TEXT"),
    ("Feature", "VARCHAR(64) DEFAULT NULL"),
    ("Start", "BIGINT DEFAULT NULL"),
    ("End", "BIGINT DEFAULT NULL"),
    ("Chromosomes", "VARCHAR(64) DEFAULT NULL"),
    ("Nomenclature_ID", "VARCHAR(128) DEFAULT NULL"),
    ("Ensembl_ID", "VARCHAR(128) DEFAULT NULL"),
    ("OMIM_ID", "VARCHAR(128) DEFAULT NULL"),
    ("Taxonomic_ID", "BIGINT DEFAULT NULL"),
    ("SwissProt_Access", "VARCHAR(256) DEFAULT NULL"),
    ("Length", "DOUBLE DEFAULT NULL"),
    ("Synonyms", "TEXT"),
)


def _gene_like_ddl(table: str) -> str:
    cols = ",\n  ".join(f"`{name}` {typ}" for name, typ in _GENE_LIKE_COLUMN_DEFS)
    return f"""
CREATE TABLE IF NOT EXISTS `{table}` (
  {cols},
  KEY `ix_{table}_geneid` (`GeneID`),
  KEY `ix_{table}_ensembl` (`Ensembl_ID`),
  KEY `ix_{table}_symbol` (`Symbol`(128))
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


def _sync_gene_like_columns(engine: Engine, table: str) -> None:
    """已存在旧版空壳表时补齐列，以便导入与 dump 列集一致的 INSERT。"""
    if not _table_exists(engine, table):
        return
    have = _existing_mysql_columns(engine, table)
    adds = [
        f"ADD COLUMN `{name}` {typ}"
        for name, typ in _GENE_LIKE_COLUMN_DEFS
        if name not in have
    ]
    if not adds:
        return
    stmt = f"ALTER TABLE `{table}` {', '.join(adds)}"
    logger.info("补齐参考表 `%s` 列（%s 个新列）", table, len(adds))
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _mrna_homo_ddl() -> str:
    return """
CREATE TABLE IF NOT EXISTS `mrna_homo_sapiens` (
  `RefSeq_match_transcript_MANE_Select` VARCHAR(128) DEFAULT NULL,
  `RefSeq_mRNA_ID` VARCHAR(128) DEFAULT NULL,
  `RefSeq_mRNA_predicted_ID` VARCHAR(128) DEFAULT NULL,
  `Length` DOUBLE DEFAULT NULL,
  `Transcript_name` VARCHAR(1024) DEFAULT NULL,
  KEY `ix_mrna_hs_mane` (`RefSeq_match_transcript_MANE_Select`),
  KEY `ix_mrna_hs_id` (`RefSeq_mRNA_ID`),
  KEY `ix_mrna_hs_pred` (`RefSeq_mRNA_predicted_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""".strip()


def _mrna_other_ddl(table: str) -> str:
    return f"""
CREATE TABLE IF NOT EXISTS `{table}` (
  `RefSeq_mRNA_ID` VARCHAR(128) DEFAULT NULL,
  `RefSeq_mRNA_predicted_ID` VARCHAR(128) DEFAULT NULL,
  `Length` DOUBLE DEFAULT NULL,
  `Transcript_name` VARCHAR(1024) DEFAULT NULL,
  KEY `ix_{table}_id` (`RefSeq_mRNA_ID`),
  KEY `ix_{table}_pred` (`RefSeq_mRNA_predicted_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""".strip()


def _protein_ddl(table: str) -> str:
    return f"""
CREATE TABLE IF NOT EXISTS `{table}` (
  `RefSeq` TEXT,
  `Symbol` VARCHAR(512) DEFAULT NULL,
  `Entry` VARCHAR(128) DEFAULT NULL,
  `Protein_stable_ID` VARCHAR(128) DEFAULT NULL,
  `AlphaFoldDB` VARCHAR(128) DEFAULT NULL,
  `Ensembl` VARCHAR(128) DEFAULT NULL,
  KEY `ix_{table}_entry` (`Entry`),
  KEY `ix_{table}_ensembl` (`Ensembl`),
  KEY `ix_{table}_symbol` (`Symbol`(128))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
""".strip()


def _ddl_for_table(name: str) -> str:
    if name == "mrna_homo_sapiens":
        return _mrna_homo_ddl()
    if name.startswith("mrna_"):
        return _mrna_other_ddl(name)
    if name.startswith("protein_"):
        return _protein_ddl(name)
    if name.startswith("gene_"):
        return _gene_like_ddl(name)
    raise ValueError(f"未知参考表: {name}")


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


def _mysql_cli_import(sql_path: Path) -> None:
    """使用 mysql 非交互导入；密码经环境变量 MYSQL_PWD 传入。"""
    import os

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
        fobj = gzip.open(sql_path, "rb")
    else:
        fobj = open(sql_path, "rb")

    try:
        subprocess.run(
            cmd,
            stdin=fobj,
            env=env,
            check=True,
            capture_output=True,
            timeout=86400,
        )
    finally:
        fobj.close()


def ensure_reference_annotation_tables(engine: Engine) -> None:
    """
    仅针对 MySQL：创建注释表空壳；可选从 REFERENCE_DATA_SQL_DIR 导入数据。
    """
    if engine.dialect.name != "mysql":
        logger.info("当前数据库非 MySQL，跳过参考注释表（gene/mrna/protein）初始化")
        return

    try:
        missing = [t for t in REFERENCE_ANNOTATION_TABLES if not _table_exists(engine, t)]
        if missing:
            logger.info("创建缺失的参考注释表: %s", ", ".join(missing))
            _apply_ddl(engine, missing)

        for t in REFERENCE_ANNOTATION_TABLES:
            if t.startswith("gene_"):
                _sync_gene_like_columns(engine, t)

        sql_dir = settings.REFERENCE_DATA_SQL_DIR
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
            try:
                logger.info("导入参考数据: %s <- %s", table, sql_file.name)
                _mysql_cli_import(sql_file)
                after = _table_row_count(engine, table)
                logger.info("表 `%s` 导入后行数: %s", table, after)
            except FileNotFoundError:
                logger.error(
                    "未找到 mysql 客户端，无法导入 %s。请在镜像中安装 default-mysql-client，"
                    "或在主机上导入后再启动。",
                    sql_file,
                )
                raise
            except subprocess.CalledProcessError as e:
                logger.error(
                    "导入 %s 失败: %s",
                    sql_file,
                    (e.stderr or e.stdout or b"").decode("utf-8", errors="replace")[:2000],
                )
                raise

    except Exception:
        logger.exception("参考注释表初始化失败")
        raise
