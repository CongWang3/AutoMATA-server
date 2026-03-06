from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json


class TrainingJobBase(BaseModel):
    task_name: str
    model_type: str  # 'supervised', 'unsupervised'
    language: str    # 'python', 'r'
    parameters: Optional[str] = None  # JSON string storage
    dataset_path: Optional[str] = None
    result_path: Optional[str] = None
    created_by: Optional[int] = None  # User ID


class TrainingJobCreate(TrainingJobBase):
    pass


class TrainingJobUpdate(BaseModel):
    task_name: Optional[str] = None
    model_type: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = None  # 'pending', 'running', 'completed', 'failed'
    parameters: Optional[str] = None
    dataset_path: Optional[str] = None
    result_path: Optional[str] = None


class TrainingJob(TrainingJobBase):
    id: int
    status: str = 'pending'  # 'pending', 'running', 'completed', 'failed'
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    class Config:
        orm_mode = True


class TrainingLogBase(BaseModel):
    task_id: int
    log_level: Optional[str] = None  # 'INFO', 'WARNING', 'ERROR'
    message: str


class TrainingLogCreate(BaseModel):
    log_level: Optional[str] = None
    message: str


class TrainingLog(TrainingLogBase):
    id: int
    timestamp: datetime
    
    class Config:
        orm_mode = True