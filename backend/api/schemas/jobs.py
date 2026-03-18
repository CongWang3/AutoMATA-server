"""
统一任务 Schema：跨模块任务的统一响应模型
"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class UnifiedJobResponse(BaseModel):
    """统一任务响应模型"""
    job_id: str
    job_type: str
    job_type_display: str  # 中文显示名
    status: str
    status_display: str    # 中文显示名
    progress: int = 0
    current_step: Optional[str] = None
    input_params: Optional[Any] = None  # 解析后的 dict
    result_file: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UnifiedJobListResponse(BaseModel):
    """统一任务列表响应模型"""
    total: int
    jobs: List[UnifiedJobResponse]


class JobTypeInfo(BaseModel):
    """任务类型信息（含数量统计）"""
    value: str
    display_name: str
    count: int = 0


class DownloadUrlResponse(BaseModel):
    """下载链接响应模型"""
    download_url: str
    expires_in: int = 300  # 默认 5 分钟有效期
