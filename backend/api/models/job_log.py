"""
作业日志模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from config.database import Base


class LogLevel(str, enum.Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JobLog(Base):
    """作业日志表"""
    
    __tablename__ = "job_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志 ID")
    job_id = Column(
        String(36), 
        ForeignKey("jobs.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True, 
        comment="任务 ID"
    )
    log_level = Column(
        Enum(LogLevel), 
        default=LogLevel.INFO, 
        index=True, 
        comment="日志级别"
    )
    message = Column(Text, nullable=False, comment="日志内容")
    source = Column(String(100), comment="日志来源")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
    
    # 关联关系
    job = relationship("Job", back_populates="logs")
    
    def __repr__(self):
        return f"<JobLog(id={self.id}, level={self.log_level})>"
