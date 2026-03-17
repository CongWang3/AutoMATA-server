"""
训练任务模型：用于管理监督学习等模型训练任务
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from config.database import Base


class TrainingTask(Base):
    """训练任务表"""

    __tablename__ = "training_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_name = Column(String(200), nullable=False, comment="任务名称")
    model_type = Column(String(50), nullable=False, comment="模型类型，如 cnn、lstm、mlp 等")
    language = Column(String(20), nullable=False, default="python", comment="训练脚本语言")
    status = Column(String(20), nullable=False, default="pending", comment="任务状态")
    parameters = Column(Text, nullable=False, comment="训练参数(JSON 字符串)")
    dataset_path = Column(String(500), nullable=True, comment="主数据集路径或目录")
    result_path = Column(String(500), nullable=True, comment="训练结果文件或目录路径")
    job_id = Column(String(50), nullable=False, index=True, comment="关联的 JobID")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="创建者用户ID")
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<TrainingTask(id={self.id}, task_name={self.task_name}, status={self.status})>"

