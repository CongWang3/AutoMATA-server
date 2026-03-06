"""
文件上传功能的Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: str
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    upload_time: datetime
    created_by: Optional[int]
    
    class Config:
        orm_mode = True

class FileDownloadResponse(BaseModel):
    """文件下载响应"""
    download_url: str
    expires_at: datetime

class FileDeleteResponse(BaseModel):
    """文件删除响应"""
    message: str
    deleted_file_id: str

class TaskFileAssociation(BaseModel):
    """任务文件关联信息"""
    task_id: int
    file_id: str
    file_type: str
    original_filename: str
    file_size: int
    upload_time: datetime

class TaskFilesResponse(BaseModel):
    """任务关联文件列表响应"""
    task_id: int
    files: List[TaskFileAssociation]

class FileUploadRequest(BaseModel):
    """文件上传请求"""
    file_type: str = Field(..., description="文件类型: dataset, train, validation, test, kfold_dataset")
    
    class Config:
        schema_extra = {
            "example": {
                "file_type": "train"
            }
        }