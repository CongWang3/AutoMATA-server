from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from config.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class TrainingJob(Base):
    __tablename__ = "training_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False)
    model_type = Column(String(50), nullable=False)  # 'supervised', 'unsupervised'
    language = Column(String(20), nullable=False)   # 'python', 'r'
    status = Column(String(20), default='pending')  # 'pending', 'running', 'completed', 'failed'
    parameters = Column(JSON)  # MySQL native JSON support
    dataset_path = Column(String(500))
    result_path = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationship
    logs = relationship("TrainingLog", back_populates="training_task")


class TrainingLog(Base):
    __tablename__ = "training_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("training_tasks.id"), nullable=False)
    log_level = Column(String(20))  # 'INFO', 'WARNING', 'ERROR'
    message = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationship
    training_task = relationship("TrainingJob", back_populates="logs")