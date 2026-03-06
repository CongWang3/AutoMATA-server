"""
文件上传相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FileUploadRequest(BaseModel):
    """文件上传请求"""
    file_type: str = Field(..., description="文件类型标识")
    description: Optional[str] = Field(None, max_length=500, description="文件描述")


class FileResponse(BaseModel):
    """文件信息响应"""
    id: str
    filename: str
    original_name: str
    file_path: str
    file_size: int
    file_type: str
    md5_hash: str
    download_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """文件列表响应"""
    total: int
    files: List[FileResponse]
    page: int
    size: int


class FileDownloadResponse(BaseModel):
    """文件下载响应"""
    download_url: str
    expires_at: datetime


# <!-- 
# 审查上下文：
# - 设计意图：定义文件上传和管理的 API 数据结构，确保前后端数据格式一致
# - 已知局限：暂未实现分页参数的详细验证，后续可添加更严格的分页限制
# - 业务背景：docs/api/API_SPECIFICATION.md - 文件上传相关接口规范
# - 测试重点：请关注文件大小限制、类型验证、MD5 哈希计算准确性
# -->