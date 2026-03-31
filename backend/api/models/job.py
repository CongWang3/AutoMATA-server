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
    PVALUE_INTEGRATION = "pvalue_integration"
    MODEL_TRAIN = "model_train"
    DATA_ANALYSIS = "data_analysis"
    ANALYSIS_TRAIN = "analysis_train"
    
    def __str__(self):
        return self.value
    
    @property
    def display_name(self) -> str:
        """获取任务类型的中文显示名称"""
        names = {
            'genome_process': '基因组处理',
            'transcriptome_process': '转录组处理',
            'protein_process': '蛋白质处理',
            'integration_process': '多组学整合',
            'pvalue_integration': 'P值整合分析',
            'model_train': '模型训练',
            'data_analysis': '数据分析',
            'analysis_train': '分析并训练',
        }
        return names.get(self.value, self.value)


class JobStatus(str, enum.Enum):
    """任务状态枚举"""
    SUBMITTED = "Submitted"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    
    @property
    def display_name(self) -> str:
        """获取任务状态的中文显示名称"""
        names = {
            'Submitted': '已提交',
            'Processing': '处理中',
            'Completed': '已完成',
            'Failed': '失败',
            'Cancelled': '已取消',
        }
        return names.get(self.value, self.value)


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
    progress = Column(Integer, default=0, comment="进度百分比 (0-100)")
    current_step = Column(String(255), comment="当前执行步骤描述")
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
