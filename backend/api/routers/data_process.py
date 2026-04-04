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
from config.settings import settings
from api.dependencies.auth import get_current_active_user
from api.services.data_process_service import DataProcessService
from api.models.user import User
from api.models.job import Job
from api.schemas.data_process import (
    GenomeProcessRequest, 
    GenomeProcessResponse,
    TranscriptomeProcessRequest,
    TranscriptomeProcessResponse,
    PvalueIntegrationProcessRequest,
    PvalueIntegrationProcessResponse,
    ProteinProcessRequest,
    ProteinProcessResponse,
    IntegrationProcessRequest,
    IntegrationProcessResponse,
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
                detail="Only txt format files are supported"
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
                detail=f"Gene nomenclature must be: {', '.join(valid_nomenclatures)}"
            )
            
        if data_type not in valid_data_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Data type must be: {', '.join(valid_data_types)}"
            )
            
        if organism not in valid_organisms:
            raise HTTPException(
                status_code=400, 
                detail=f"Supported species: {', '.join(valid_organisms)}"
            )
        
        # 调用服务层处理 执行脚本
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
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

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
                detail="Only txt format files are supported"
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
                detail=f"mRNA nomenclature must be: {', '.join(valid_nomenclatures)}"
            )
            
        if data_type not in valid_data_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Data type must be: {', '.join(valid_data_types)}"
            )
            
        if organism not in valid_organisms:
            raise HTTPException(
                status_code=400, 
                detail=f"Supported species: {', '.join(valid_organisms)}"
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
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"转录组数据处理失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/protein", response_model=ProteinProcessResponse)
async def process_protein_data(
    file: UploadFile = File(...),
    protein_nomenclature: str = Form(...),
    organism: str = Form(...),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    蛋白质数据处理接口
    
    将蛋白质表达数据转换为log2(表达值+1)格式，并提供对应的基因符号
    
    Args:
        file: 上传的蛋白质表达数据文件
        protein_nomenclature: 蛋白质命名方式 (Entry, RefSeq, AlphaFoldDB, Ensembl)
        organism: 物种 (homo_sapiens, bos_taurus, mus_musculus, drosophila_melanogaster)
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
                detail="Only txt format files are supported"
            )
        
        # 验证参数
        valid_nomenclatures = ["Entry", "RefSeq", "AlphaFoldDB", "Ensembl"]
        valid_organisms = [
            "homo_sapiens", "bos_taurus", "mus_musculus", "drosophila_melanogaster"
        ]
        
        if protein_nomenclature not in valid_nomenclatures:
            raise HTTPException(
                status_code=400, 
                detail=f"Protein nomenclature must be: {', '.join(valid_nomenclatures)}"
            )
            
        if organism not in valid_organisms:
            raise HTTPException(
                status_code=400, 
                detail=f"Supported species: {', '.join(valid_organisms)}"
            )
        
        # 调用服务层处理
        service = DataProcessService(db, current_user)
        result = await service.process_protein_data(
            file=file,
            protein_nomenclature=protein_nomenclature,
            organism=organism,
            email=email
        )
        
        logger.info(f"蛋白质数据处理任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"蛋白质数据处理失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/integration", response_model=IntegrationProcessResponse)
async def process_integration_data(
    pheno_file: UploadFile = File(...),
    file_1: UploadFile = File(...),
    file_2: UploadFile = File(...),
    file_3: UploadFile = File(...),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    多组学数据整合接口
    
    将基因组 / 转录组 / 蛋白质等多组学数据按样本名进行整合，缺失值填充为 0
    
    Args:
        pheno_file: 表型数据文件
        file_1: 组学数据文件1
        file_2: 组学数据文件2
        file_3: 组学数据文件3
        email: 可选邮箱，用于结果通知
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        处理任务信息
    """
    try:
        # 基本文件类型校验（后端仍保留安全兜底）
        files = [pheno_file, file_1, file_2, file_3]
        for f in files:
            if not f.filename or not f.filename.endswith(('.txt', '.csv', '.tsv')):
                raise HTTPException(
                    status_code=400,
                    detail="All files must support txt format",
                )
        
        service = DataProcessService(db, current_user)
        result = await service.process_integration_data(
            pheno_file=pheno_file,
            file_1=file_1,
            file_2=file_2,
            file_3=file_3,
            email=email,
        )
        
        logger.info(
            f"多组学数据整合任务已提交: job_id={result.job_id}, user={current_user.username}"
        )
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"多组学数据整合失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/pvalue-integration", response_model=PvalueIntegrationProcessResponse)
async def process_pvalue_integration_data(
    file_1: UploadFile = File(...),
    file_2: UploadFile = File(...),
    file_3: UploadFile = File(...),
    method: str = Form(...),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    pvalue 多组学整合接口

    调用 R 脚本 integration_pvalue.R，对三个组学的 pvalue 进行整合
    """
    try:
        # 基本文件类型校验
        files = [file_1, file_2, file_3]
        for f in files:
            if not f.filename or not f.filename.endswith(('.txt', '.csv', '.tsv')):
                raise HTTPException(
                    status_code=400,
                    detail="All files must support txt format",
                )

        # 方法校验（与 R 脚本中说明保持一致）
        valid_methods = [
            "Fisher",
            "Fisher_directional",
            "Brown",
            "DPM",
            "Stouffer",
            "Stouffer_directional",
            "Strube",
            "Strube_directional",
            "None"
        ]
        if method not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"method must be: {', '.join(valid_methods)}",
            )

        service = DataProcessService(db, current_user)
        result = await service.process_pvalue_integration(
            file_1=file_1,
            file_2=file_2,
            file_3=file_3,
            method=method,
            email=email,
        )

        logger.info(
            f"pvalue 多组学整合任务已提交: job_id={result.job_id}, user={current_user.username}"
        )
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"pvalue 多组学整合失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

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
            raise HTTPException(status_code=404, detail="The task does not exist")
        
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
        raise HTTPException(status_code=500, detail="Database query failed")
    except Exception as e:
        logger.error(f"查询任务状态失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to query the task status: {str(e)}")

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
        raise HTTPException(status_code=500, detail="Database query failed")

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
            raise HTTPException(status_code=404, detail="The task does not exist")
        
        status_text = job.status.value if hasattr(job.status, "value") else str(job.status)
        # 放宽条件：
        # 1) 若状态已 Completed → 正常放行
        # 2) 若状态尚未标记为 Completed，但 Jobs/<id>/ 下已存在 processed.txt 或其它可下载结果 → 也允许下载
        jobs_root = settings.path_jobs
        job_dir = jobs_root / job_id
        processed_txt = job_dir / "processed.txt"
        has_db_result = bool(job.result_file and str(job.result_file).strip())
        db_result_path = Path(str(job.result_file)).expanduser() if has_db_result else None

        is_completed = str(status_text).strip().lower() == 'completed'
        has_physical_result = (
            processed_txt.is_file()
            or (db_result_path is not None and db_result_path.is_file())
        )

        if not (is_completed or has_physical_result):
            raise HTTPException(status_code=400, detail="The task is not completed")
        
        # 检查文件是否存在
        result_path = FilePath(job.result_file)
        if not result_path.exists():
            raise HTTPException(status_code=404, detail="The result file does not exist")
        
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
        raise HTTPException(status_code=500, detail=f"Failed to download the result: {str(e)}")


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
            raise HTTPException(status_code=404, detail="The task does not exist")

        status_text = job.status.value if hasattr(job.status, "value") else str(job.status)
        jobs_root = FilePath(settings.path_jobs)
        job_dir = jobs_root / job_id
        processed_txt = job_dir / "processed.txt"
        # Integration 任务的默认输出位置：Jobs/<id>/result/<id>_result.txt
        integration_result_txt = job_dir / "result" / f"{job_id}_result.txt"
        has_db_result = bool(job.result_file and str(job.result_file).strip())
        db_result_path = FilePath(str(job.result_file)).expanduser() if has_db_result else None
        is_completed = str(status_text).strip().lower() == "completed"
        has_physical_result = (
            processed_txt.is_file()
            or integration_result_txt.is_file()
            or (db_result_path is not None and db_result_path.is_file())
        )

        # 放宽条件与 /download/{job_id} 对齐：Completed 或物理结果存在即可生成下载链接
        if not (is_completed or has_physical_result):
            raise HTTPException(status_code=400, detail="The task is not completed")

        # 若 DB 未写 result_file，但磁盘已有结果文件，则补写 result_file（不影响本次返回；写回失败也不阻断）
        if not has_db_result:
            if processed_txt.is_file():
                job.result_file = str(processed_txt)
            elif integration_result_txt.is_file():
                job.result_file = str(integration_result_txt)
            try:
                db.add(job)
                db.commit()
            except Exception:
                db.rollback()
        
        # 生成签名
        timestamp = int(time.time())
        uid = current_user.id
        secret = settings.SECRET_KEY.encode()
        message = f"{job_id}:{uid}:{timestamp}".encode()
        token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]
        
        # 构建下载链接
        download_url = settings.download_public_url(
            f"/job-result/{job_id}?uid={uid}&t={timestamp}&token={token}"
        )
        
        return DownloadUrlResponse(
            download_url=download_url,
            expires_in=600  # 10分钟有效期
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成下载链接失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate the download link: {str(e)}")


# ---------------- 示例数据下载（多组学整合） ----------------

# @router.get("/examples/integration/{file_type}")
# async def download_integration_example(file_type: str):
#     """
#     下载多组学整合示例数据文件
    
#     file_type 取值：
#     - pheno   -> jobID_pheno.txt
#     - omics1  -> jobID_omics_1.txt
#     - omics2  -> jobID_omics_2.txt
#     - omics3  -> jobID_omics_3.txt
#     """
#     base_dir = FilePath("/xp/www/AutoMATA/example/train_example")
#     mapping = {
#         "pheno": "jobID_pheno.txt",
#         "omics1": "jobID_omics_1.txt",
#         "omics2": "jobID_omics_2.txt",
#         "omics3": "jobID_omics_3.txt",
#     }
    
#     if file_type not in mapping:
#         raise HTTPException(status_code=400, detail="不支持的示例文件类型")
    
#     file_path = base_dir / mapping[file_type]
#     if not file_path.exists():
#         logger.error(f"示例文件不存在：{file_path}")
#         raise HTTPException(status_code=404, detail="示例文件不存在")
    
#     return FileResponse(
#         path=str(file_path),
#         filename=mapping[file_type],
#         media_type="text/plain"
#     )


# ---------------- 示例数据下载（数据分析模块） ----------------

@router.get("/examples/draw/{analysis_type}")
async def download_draw_example(analysis_type: str):
    """
    下载数据分析模块示例数据文件
    
    analysis_type 取值：
    - pca               -> pca_example.txt
    - cor_heatmap       -> cor_heatmap_example.txt
    - volcano           -> volcano_example.txt
    - venn              -> venn_example.txt
    - df_cluster        -> df_cluster_example.txt
    - go_enrichment     -> go_enrichment_example.txt
    - kegg_enrichment   -> kegg_enrichment_example.txt
    - dumbbell          -> dumbbell_example.txt
    - dumbbell_bar      -> dumbbell_bar_example.txt
    - ppi               -> ppi_example.txt
    """
    base_dir = FilePath(settings.path_repo / "example" / "draw_example")
    
    # 示例文件映射
    example_files = {
        "pca": "pca_example.txt",
        "cor_heatmap": "cor_heatmap_example.txt",
        "volcano": "volcano_example.txt",
        "venn": "venn_example.txt",
        "df_cluster": "df_cluster_example.txt",
        "go_enrichment": "go_enrichment_example.txt",
        "kegg_enrichment": "kegg_enrichment_example.txt",
        "dumbbell": "dumbbell_example.txt",
        "dumbbell_bar": "dumbbell_bar_example.txt",
        "ppi": "ppi_example.txt",
    }
    
    if analysis_type not in example_files:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported example type: {analysis_type}. Supported types: {', '.join(example_files.keys())}"
        )
    
    file_name = example_files[analysis_type]
    file_path = base_dir / file_name
    
    if not file_path.exists():
        logger.error(f"示例文件不存在：{file_path}")
        raise HTTPException(status_code=404, detail=f"The example file does not exist: {file_name}")
    
    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type="text/plain"
    )