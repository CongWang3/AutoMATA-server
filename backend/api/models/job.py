"""
作业任务模型
"""
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from config.database import Base


class JobType(str, enum.Enum):
    """任务类型枚举"""
    DATA_PROCESS = "data_process"
    MODEL_TRAIN = "model_train"
    DATA_ANALYSIS = "data_analysis"


class JobStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    """作业任务表"""
    
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="任务ID (UUID)")
    job_id = Column(String(50), unique=True, nullable=False, index=True, comment="作业 ID")
    job_type = Column(
        Enum(JobType), 
        nullable=False, 
        index=True, 
        comment="任务类型"
    )
    status = Column(
        Enum(JobStatus), 
        default=JobStatus.PENDING, 
        index=True, 
        comment="任务状态"
    )
    progress = Column(Integer, default=0, comment="进度百分比 (0-100)")
    current_step = Column(String(255), comment="当前执行步骤描述")
    parameters = Column(Text, comment="任务参数配置 (JSON 字符串)")
    result_path = Column(String(500), comment="结果文件路径")
    error_message = Column(Text, comment="错误信息")
    # 用户删除后作业历史仍需保留，因此使用 SET NULL
    created_by = Column(
        Integer, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        index=True, 
        nullable=True,
        comment="创建用户 ID"
    )
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
    started_at = Column(DateTime, comment="开始执行时间")
    completed_at = Column(DateTime, comment="完成时间")
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        comment="更新时间"
    )
    
    # 关联关系
    creator = relationship("User", back_populates="jobs")
    files = relationship("JobFile", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        # <!-- 
        # 审查上下文：
        # - 设计意图：使用 status.value 而非 status 本身，确保显示小写状态字符串
        # - 已知局限：无
        # - 业务背景：与数据库存储格式一致，status 字段在数据库中存储为小写字符串
        # - 测试重点：请验证 repr 输出包含小写的状态值而非枚举类名
        # -->
        status_value = self.status.value if self.status is not None else None
        return f"<Job(job_id={self.job_id}, status={status_value})>"
