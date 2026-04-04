"""
数据库初始化脚本
"""
import logging
import time
from typing import Optional

from sqlalchemy.exc import OperationalError

from config.database import engine, Base, ensure_database_schema

logger = logging.getLogger(__name__)

_INIT_RETRIES = 3
_INIT_RETRY_SLEEP_SEC = 15


def _after_schema():
    from reference_data.bootstrap import ensure_reference_annotation_tables

    ensure_reference_annotation_tables(engine)


def init_db():
    """
    初始化数据库表
    
    <!-- 
    审查上下文：
    - 设计意图：创建所有数据库表，用于首次部署
    - 已知局限：简单粗暴创建所有表，生产环境应使用 Alembic 迁移
    - 业务背景：docs/database/DATABASE_DESIGN.md - 表结构设计
    - 测试重点：请验证所有表是否正确创建，索引是否生效
    -->
    """
    last_err: Optional[Exception] = None
    for attempt in range(1, _INIT_RETRIES + 1):
        try:
            logger.info("开始创建数据库表... (attempt %s/%s)", attempt, _INIT_RETRIES)
            ensure_database_schema()
            _after_schema()
            logger.info("数据库表创建成功")
            return
        except OperationalError as e:
            last_err = e
            logger.warning(
                "创建数据库表失败（可重试）: %s — %s 秒后重试",
                e,
                _INIT_RETRY_SLEEP_SEC if attempt < _INIT_RETRIES else 0,
            )
            if attempt < _INIT_RETRIES:
                time.sleep(_INIT_RETRY_SLEEP_SEC)
        except Exception as e:
            logger.error(f"创建数据库表失败：{e}")
            raise
    if last_err is not None:
        raise last_err


def drop_db():
    """删除所有表（谨慎使用）"""
    try:
        logger.warning("开始删除所有数据库表...")
        import api.models  # noqa: F401

        Base.metadata.drop_all(bind=engine)
        logger.warning("数据库表已删除")
    except Exception as e:
        logger.error(f"删除数据库表失败：{e}")
        raise


if __name__ == "__main__":
    import logging as _logging
    import sys

    # CI/SSH 部署需实时看到进度；默认无 basicConfig 时 INFO 不会输出
    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    init_db()
    print("数据库初始化完成！", flush=True)
