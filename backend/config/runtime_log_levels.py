"""
运行时调整第三方库的日志级别（仅依赖 settings，避免与 database 循环导入）。
"""
import logging

from config.settings import settings


def apply_production_third_party_log_levels() -> None:
    """
    生产环境降低 SQLAlchemy 引擎/连接池日志，避免每次启动打印大量 SQL（刷屏）。

    开发环境（DEBUG=True）不修改，便于排查；ORM 层 echo 仍由 config.database 的 echo=settings.DEBUG 控制。
    """
    if not settings.is_production:
        return
    for name in ("sqlalchemy.engine", "sqlalchemy.pool"):
        logging.getLogger(name).setLevel(logging.WARNING)
