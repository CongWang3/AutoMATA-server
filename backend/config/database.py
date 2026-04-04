"""
数据库配置模块
"""
import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.runtime_log_levels import apply_production_third_party_log_levels
from config.settings import settings

logger = logging.getLogger(__name__)


def _pymysql_connect_args() -> dict:
    """长 DDL（create_all）时避免默认短超时导致 Lost connection / 1317 interrupted。"""
    url = settings.DATABASE_URL
    if not url.startswith("mysql+pymysql"):
        return {}
    return {
        "connect_timeout": 60,
        "read_timeout": 600,
        "write_timeout": 600,
    }


# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG,
    connect_args=_pymysql_connect_args(),
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def ensure_database_schema() -> None:
    """
    确保 ORM 定义的所有表存在（幂等，等价于缺失表时执行 CREATE TABLE）。

    Docker / 生产镜像入口仅 uvicorn，不跑 init_db.py 时，用此函数在进程启动时补全
    job_files、job_logs 等表，避免功能残缺。
    """
    import api.models  # noqa: F401 — 将各模型注册到 Base.metadata

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表结构已校验（create_all，缺失表已创建）")
    except Exception:
        logger.exception("数据库表结构创建失败")
        raise


def get_db():
    """
    获取数据库会话依赖
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


apply_production_third_party_log_levels()
