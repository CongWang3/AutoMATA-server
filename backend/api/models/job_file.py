"""
作业文件关联模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from config.database import Base


class FileRole(str, enum.Enum):
    """文件角色枚举"""
    INPUT = "input"
    OUTPUT = "output"
    MODEL = "model"
    CONFIG = "config"
    LOG = "log"


class JobFile(Base):
    """作业文件关联表"""
    
    __tablename__ = "job_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID")
    job_id = Column(
        Integer, 
        ForeignKey("jobs.id"), 
        nullable=False, 
        index=True, 
        comment="任务 ID"
    )
    file_id = Column(
        String(50), 
        ForeignKey("files.id"), 
        nullable=False, 
        index=True, 
        comment="文件 ID"
    )
    file_role = Column(
        Enum(FileRole), 
        nullable=False, 
        index=True, 
        comment="文件角色"
    )
    file_category = Column(String(50), comment="文件分类")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关联关系
    job = relationship("Job", back_populates="files")
    file = relationship("File", back_populates="job_files")
    
    def __repr__(self):
        return f"<JobFile(job_id={self.job_id}, file_id={self.file_id})>"
