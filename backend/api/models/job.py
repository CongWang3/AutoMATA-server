"""
作业任务模型
"""
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from config.database import Base


class JobType(str, enum.Enum):
    """任务类型枚举"""
    # 大写字符串改为小写
    GENOME_PROCESS = "genome_process"
    TRANSCRIPTOME_PROCESS = "transcriptome_process"
    PROTEIN_PROCESS = "protein_process"
    INTEGRATION_PROCESS = "integration_process"
    MODEL_TRAIN = "model_train"
    DATA_ANALYSIS = "data_analysis"
    
    def __str__(self):
        return self.value


class JobStatus(str, enum.Enum):
    """任务状态枚举"""
    SUBMITTED = "Submitted"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class Job(Base):
    """作业任务表"""
    
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="任务ID (UUID)")
    job_id = Column(String(50), unique=True, nullable=False, index=True, comment="作业 ID")
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False,
        comment="用户 ID"
    )
    job_type = Column(
        Enum(JobType), 
        nullable=False, 
        index=True, 
        comment="任务类型"
    )
    status = Column(
        Enum(JobStatus), 
        default=JobStatus.SUBMITTED, 
        index=True, 
        comment="任务状态"
    )
    input_params = Column(Text, comment="输入参数配置 (JSON 字符串)")
    output_params = Column(Text, comment="输出参数 (JSON 字符串)")
    result_file = Column(String(500), comment="结果文件路径")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        comment="更新时间"
    )
    started_at = Column(DateTime, comment="开始执行时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关联关系
    user = relationship("User", back_populates="jobs")
    files = relationship("JobFile", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(job_id={self.job_id}, status={self.status.value if self.status else 'None'})>"
