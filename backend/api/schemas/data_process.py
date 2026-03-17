"""
数据处理相关的Pydantic模型定义
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# <!-- 
# 审查上下文：
# - 设计意图：定义数据处理API的请求和响应数据结构，确保类型安全和数据验证
# - 已知局限：模型相对简单，后续可根据需要添加更多字段和验证规则
# - 业务背景：对应前端数据处理表单的数据结构
# - 测试重点：请验证必填字段验证、枚举值验证、可选字段处理
# -->

class GenomeProcessRequest(BaseModel):
    """基因组数据处理请求模型"""
    gene_nomenclature: str  # GeneID, EnsemblID, Symbol
    data_type: str  # FPKM, TPM, ReadCounts, RPKM, RPM
    organism: str  # homo_sapiens, mus_musculus等
    email: Optional[str] = None

class GenomeProcessResponse(BaseModel):
    """基因组数据处理响应模型"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TranscriptomeProcessRequest(BaseModel):
    """转录组数据处理请求模型"""
    mrna_nomenclature: str  # Refseq, EnsemblID, Transcript_name
    data_type: str  # FPKM, TPM, ReadCounts, RPKM, RPM
    organism: str  # homo_sapiens, mus_musculus等
    email: Optional[str] = None

class TranscriptomeProcessResponse(BaseModel):
    """转录组数据处理响应模型"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class IntegrationProcessRequest(BaseModel):
    """多组学数据整合请求模型"""
    email: Optional[str] = None


class IntegrationProcessResponse(BaseModel):
    """多组学数据整合响应模型"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PvalueIntegrationProcessRequest(BaseModel):
    """pvalue 多组学整合请求模型"""
    method: str
    email: Optional[str] = None


class PvalueIntegrationProcessResponse(BaseModel):
    """pvalue 多组学整合响应模型"""
    job_id: str
    status: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProteinProcessRequest(BaseModel):
    """蛋白质数据处理请求模型"""
    protein_nomenclature: str  # Entry, RefSeq, AlphaFoldDB, Ensembl
    organism: str  # homo_sapiens, bos_taurus, mus_musculus, drosophila_melanogaster
    email: Optional[str] = None

class ProteinProcessResponse(BaseModel):
    """蛋白质数据处理响应模型"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DataProcessStatusResponse(BaseModel):
    """数据处理状态查询响应模型"""
    job_id: str
    status: str  # Submitted, Processing, Completed, Failed
    progress: Optional[int] = None  # 0-100
    result_file: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobListItem(BaseModel):
    """任务列表项模型"""
    job_id: str
    job_type: str
    status: str
    input_params: Optional[str] = None
    result_file: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    """任务列表响应模型"""
    total: int
    jobs: List[JobListItem]
    
    class Config:
        from_attributes = True