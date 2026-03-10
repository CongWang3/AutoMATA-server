"""
数据处理路由：处理基因组、转录组等生物数据处理接口
"""
import re
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Optional, List
import os
from pathlib import Path as FilePath

from config.database import get_db
from api.dependencies.auth import get_current_active_user
from api.services.data_process_service import DataProcessService
from api.models.user import User
from api.models.job import Job
from api.schemas.data_process import (
    GenomeProcessRequest, 
    GenomeProcessResponse,
    TranscriptomeProcessRequest,
    TranscriptomeProcessResponse,
    DataProcessStatusResponse,
    JobListItem,
    JobListResponse
)

logger = logging.getLogger(__name__)

# Job ID 格式验证：YYYYMMDDHHMMSS_8 位随机字符
JOB_ID_PATTERN = re.compile(r'^\d{14}_[a-zA-Z0-9]{8}$')

router = APIRouter(prefix="/api/v1/data-process", tags=["数据处理"])

# <!-- 
# 审查上下文：
# - 设计意图：提供统一的数据处理API接口，支持基因组和转录组数据标准化处理
# - 已知局限：目前仅支持有限的物种和数据格式，后续需扩展更多处理选项
# - 业务背景：替代原有的PHP数据处理功能，提供现代化的RESTful API
# - 测试重点：请重点关注文件上传验证、参数校验、R脚本调用和异步任务处理
# -->

@router.post("/genome", response_model=GenomeProcessResponse)
async def process_genome_data(
    file: UploadFile = File(...),
    gene_nomenclature: str = Form(...),
    data_type: str = Form(...),
    organism: str = Form(...),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    基因组数据处理接口
    
    将基因表达数据（FPKM、TPM、ReadCounts等）转换为log2(TPM+1)格式
    
    Args:
        file: 上传的基因表达数据文件
        gene_nomenclature: 基因命名方式 (GeneID, EnsemblID, Symbol)
        data_type: 数据类型 (FPKM, TPM, ReadCounts, RPKM, RPM)
        organism: 物种 (homo_sapiens, mus_musculus, drosophila_melanogaster等)
        email: 可选的用户邮箱，用于结果通知
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        处理任务信息
        
    Raises:
        HTTPException: 文件格式错误、参数无效或其他处理错误
    """
    try:
        # 验证文件类型
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(
                status_code=400, 
                detail="只支持 txt、csv、tsv 格式的文件"
            )
        
        # 验证参数
        valid_nomenclatures = ["GeneID", "EnsemblID", "Symbol"]
        valid_data_types = ["FPKM", "TPM", "ReadCounts", "RPKM", "RPM"]
        valid_organisms = [
            "homo_sapiens", "mus_musculus", "drosophila_melanogaster", 
            "arabidopsis_thaliana", "bos_taurus"
        ]
        
        if gene_nomenclature not in valid_nomenclatures:
            raise HTTPException(
                status_code=400, 
                detail=f"基因命名方式必须是: {', '.join(valid_nomenclatures)}"
            )
            
        if data_type not in valid_data_types:
            raise HTTPException(
                status_code=400, 
                detail=f"数据类型必须是: {', '.join(valid_data_types)}"
            )
            
        if organism not in valid_organisms:
            raise HTTPException(
                status_code=400, 
                detail=f"支持的物种: {', '.join(valid_organisms)}"
            )
        
        # 调用服务层处理
        service = DataProcessService(db, current_user)
        result = await service.process_genome_data(
            file=file,
            gene_nomenclature=gene_nomenclature,
            data_type=data_type,
            organism=organism,
            email=email
        )
        
        logger.info(f"基因组数据处理任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库操作失败")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败：{str(e)}")

@router.post("/transcriptome", response_model=TranscriptomeProcessResponse)
async def process_transcriptome_data(
    file: UploadFile = File(...),
    mrna_nomenclature: str = Form(...),
    data_type: str = Form(...),
    organism: str = Form(...),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    转录组数据处理接口
    
    将mRNA表达数据转换为log2(TPM+1)格式
    
    Args:
        file: 上传的mRNA表达数据文件
        mrna_nomenclature: mRNA命名方式 (Refseq, EnsemblID, Transcript_name)
        data_type: 数据类型 (FPKM, TPM, ReadCounts, RPKM, RPM)
        organism: 物种 (homo_sapiens, mus_musculus, drosophila_melanogaster, bos_taurus)
        email: 可选的用户邮箱
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        处理任务信息
    """
    try:
        # 验证文件类型
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(
                status_code=400, 
                detail="只支持 txt、csv、tsv 格式的文件"
            )
        
        # 验证参数
        valid_nomenclatures = ["Refseq", "EnsemblID", "Transcript_name"]
        valid_data_types = ["FPKM", "TPM", "ReadCounts", "RPKM", "RPM"]
        valid_organisms = [
            "homo_sapiens", "mus_musculus", "drosophila_melanogaster", "bos_taurus"
        ]
        
        if mrna_nomenclature not in valid_nomenclatures:
            raise HTTPException(
                status_code=400, 
                detail=f"mRNA命名方式必须是: {', '.join(valid_nomenclatures)}"
            )
            
        if data_type not in valid_data_types:
            raise HTTPException(
                status_code=400, 
                detail=f"数据类型必须是: {', '.join(valid_data_types)}"
            )
            
        if organism not in valid_organisms:
            raise HTTPException(
                status_code=400, 
                detail=f"支持的物种: {', '.join(valid_organisms)}"
            )
        
        # 调用服务层处理
        service = DataProcessService(db, current_user)
        result = await service.process_transcriptome_data(
            file=file,
            mrna_nomenclature=mrna_nomenclature,
            data_type=data_type,
            organism=organism,
            email=email
        )
        
        logger.info(f"转录组数据处理任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库操作失败")
    except Exception as e:
        logger.error(f"转录组数据处理失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败：{str(e)}")

@router.get("/status/{job_id}", response_model=DataProcessStatusResponse)
async def get_process_status(
    job_id: str = Path(..., pattern=JOB_ID_PATTERN.pattern, description="任务 ID 格式：YYYYMMDDHHMMSS_8 位随机字符"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询数据处理任务状态
    
    Args:
        job_id: 任务ID
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        任务状态信息
    """
    try:
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return DataProcessStatusResponse(
            job_id=job.job_id,
            status=job.status.value,
            progress=getattr(job, 'progress', None),
            result_file=job.result_file,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    except Exception as e:
        logger.error(f"查询任务状态失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")

@router.get("/jobs", response_model=JobListResponse)
async def get_user_jobs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的任务列表
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        任务列表
    """
    try:
        # 查询总数
        total = db.query(Job).filter(Job.user_id == current_user.id).count()
        
        # 查询任务列表
        jobs = db.query(Job).filter(
            Job.user_id == current_user.id
        ).order_by(
            Job.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        job_items = [
            JobListItem(
                job_id=job.job_id,
                job_type=job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type),
                status=job.status.value if hasattr(job.status, 'value') else str(job.status),
                input_params=job.input_params,
                result_file=job.result_file,
                error_message=job.error_message,
                created_at=job.created_at,
                updated_at=job.updated_at
            )
            for job in jobs
        ]
        
        return JobListResponse(total=total, jobs=job_items)
        
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库查询失败")

@router.get("/download/{job_id}")
async def download_result(
    job_id: str = Path(..., pattern=JOB_ID_PATTERN.pattern),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    下载处理结果文件
    
    Args:
        job_id: 任务ID
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        结果文件
    """
    try:
        # 查询任务
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if job.status.value != 'COMPLETED' and job.status != 'Completed':
            raise HTTPException(status_code=400, detail="任务尚未完成")
        
        if not job.result_file:
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        # 检查文件是否存在
        result_path = FilePath(job.result_file)
        if not result_path.exists():
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        # 返回文件
        return FileResponse(
            path=str(result_path),
            filename=f"{job_id}_processed.txt",
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载结果失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败：{str(e)}")


import hmac
import hashlib
import time
from pydantic import BaseModel

class DownloadUrlResponse(BaseModel):
    """下载链接响应模型"""
    download_url: str
    expires_in: int

@router.get("/download-url/{job_id}", response_model=DownloadUrlResponse)
async def get_download_url(
    job_id: str = Path(..., pattern=JOB_ID_PATTERN.pattern),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务结果下载链接（带签名）
    
    Args:
        job_id: 任务ID
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        带签名的下载链接
    """
    try:
        # 查询任务
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if job.status.value != 'COMPLETED' and job.status != 'Completed':
            raise HTTPException(status_code=400, detail="任务尚未完成")
        
        if not job.result_file:
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        # 生成签名
        from config.settings import settings
        timestamp = int(time.time())
        uid = current_user.id
        secret = settings.SECRET_KEY.encode()
        message = f"{job_id}:{uid}:{timestamp}".encode()
        token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]
        
        # 构建下载链接
        download_url = f"http://localhost:8001/job-result/{job_id}?uid={uid}&t={timestamp}&token={token}"
        
        return DownloadUrlResponse(
            download_url=download_url,
            expires_in=300  # 5分钟有效期
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成下载链接失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"生成下载链接失败：{str(e)}")