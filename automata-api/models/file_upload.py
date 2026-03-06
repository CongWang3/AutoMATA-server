"""
文件上传功能的数据模型
"""
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import Optional
from config.database import Base

class TrainingFile(Base):
    """训练文件信息模型"""
    __tablename__ = "training_files"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    upload_time = Column(DateTime, default=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # 关系
    task_associations = relationship("TaskFile", back_populates="file", cascade="all, delete-orphan")

class TaskFile(Base):
    """任务与文件关联模型"""
    __tablename__ = "task_files"
    
    task_id = Column(Integer, ForeignKey('training_tasks.id'), primary_key=True)
    file_id = Column(String(36), ForeignKey('training_files.id'), primary_key=True)
    file_type = Column(Enum('dataset', 'train', 'validation', 'test', 'kfold_dataset'), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    file = relationship("TrainingFile", back_populates="task_associations")