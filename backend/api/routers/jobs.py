"""
统一任务路由：跨模块的任务查询、详情、取消和下载端点
"""
import json
import hmac
import hashlib
import time
import logging
import pathlib
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from config.database import get_db
from config.settings import settings
from api.dependencies.auth import get_current_active_user
from api.models.user import User
from api.models.job import Job, JobType, JobStatus
from api.schemas.jobs import (
    UnifiedJobResponse,
    UnifiedJobListResponse,
    JobTypeInfo,
    DownloadUrlResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 与 download_server 中任务产物目录一致（须用 pathlib.Path，勿与 fastapi.Path 混淆）
_JOBS_DOWNLOAD_ROOT = settings.path_jobs


def _has_result_zip_or_folder(job_id: str) -> bool:
    """磁盘上是否存在可打包下载的产物：model_result.zip、result.zip 或 result/ 目录"""
    jd = _JOBS_DOWNLOAD_ROOT / job_id
    return (
        (jd / "model_result.zip").is_file()
        or (jd / "result.zip").is_file()
        or (jd / "result").is_dir()
    )


def _result_file_points_to_downloadable(job: Job) -> bool:
    """数据库中的 result_file 是否指向存在的文件或目录"""
    if not job.result_file or not str(job.result_file).strip():
        return False
    p = pathlib.Path(job.result_file)
    return p.is_file() or p.is_dir()


def _user_job_has_downloadable_result(
    job_id: str,
    result_file: Optional[str],
    allow_standard_disk_products: bool = False,
) -> bool:
    """
    是否具备可下载结果：DB 中 result_file 指向存在的文件/目录，
    或磁盘上已有 Jobs/{job_id}/model_result.zip、result.zip 或 result/（仅允许在模型训练任务中使用）。
    """
    if result_file and str(result_file).strip():
        p = pathlib.Path(result_file)
        if p.is_file() or p.is_dir():
            return True
    if not allow_standard_disk_products:
        return False

    jd = _JOBS_DOWNLOAD_ROOT / job_id
    return (
        (jd / "model_result.zip").is_file()
        or (jd / "result.zip").is_file()
        or (jd / "result").is_dir()
    )


def _escape_sql_like(text: str) -> str:
    """转义 LIKE 通配符，避免用户输入的 %、_ 被当作模式字符。"""
    return (
        text.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _job_to_response(job: Job) -> UnifiedJobResponse:
    """
    将 Job 数据库模型转换为统一响应对象
    
    Args:
        job: Job 数据库模型对象
        
    Returns:
        UnifiedJobResponse 响应对象
    """
    # 解析 job_type 的 display_name
    job_type_value = job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type)
    job_type_display = job.job_type.display_name if hasattr(job.job_type, 'display_name') else job_type_value
    
    # 解析 status 的 display_name
    status_value = job.status.value if hasattr(job.status, 'value') else str(job.status)
    status_display = job.status.display_name if hasattr(job.status, 'display_name') else status_value
    
    # 尝试 JSON 解析 input_params
    input_params = None
    if job.input_params:
        try:
            input_params = json.loads(job.input_params)
        except (json.JSONDecodeError, TypeError):
            input_params = job.input_params  # 保持原始字符串
    
    return UnifiedJobResponse(
        job_id=job.job_id,
        job_type=job_type_value,
        job_type_display=job_type_display,
        status=status_value,
        status_display=status_display,
        progress=job.progress or 0,
        current_step=job.current_step,
        input_params=input_params,
        result_file=job.result_file,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/", response_model=UnifiedJobListResponse)
async def get_user_jobs(
    job_type: Optional[str] = Query(None, description="任务类型过滤"),
    status: Optional[str] = Query(None, description="任务状态过滤"),
    keyword: Optional[str] = Query(None, description="关键词：按 job_id 模糊匹配（不区分大小写）"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向 (asc/desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户所有任务列表
    
    支持按任务类型、状态过滤；关键词仅匹配任务 ID（job_id），支持分页
    """
    try:
        # 基础查询：当前用户的任务
        query = db.query(Job).filter(Job.user_id == current_user.id)
        
        # 任务类型过滤
        if job_type:
            try:
                job_type_enum = JobType(job_type)
                query = query.filter(Job.job_type == job_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的任务类型: {job_type}")
        
        # 状态过滤
        if status:
            try:
                status_enum = JobStatus(status)
                query = query.filter(Job.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的任务状态: {status}")
        
        # 关键词：仅按 job_id 模糊搜索（不区分大小写，转义 LIKE 特殊字符）
        if keyword and keyword.strip():
            pat = f"%{_escape_sql_like(keyword.strip().lower())}%"
            query = query.filter(func.lower(Job.job_id).like(pat, escape="\\"))
        
        # 查询总数
        total = query.count()
        
        # 排序
        sort_column = getattr(Job, sort_by, Job.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # 分页
        jobs = query.offset(offset).limit(limit).all()
        
        # 转换为响应对象
        job_responses = [_job_to_response(job) for job in jobs]
        
        return UnifiedJobListResponse(total=total, jobs=job_responses)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    except Exception as e:
        logger.error(f"获取任务列表失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败：{str(e)}")


@router.get("/types", response_model=List[JobTypeInfo])
async def get_job_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取任务类型列表（含各类型数量统计）
    
    返回所有任务类型及当前用户在每种类型下的任务数量
    """
    try:
        # 统计当前用户各类型任务数量
        type_counts = (
            db.query(Job.job_type, func.count(Job.id).label("count"))
            .filter(Job.user_id == current_user.id)
            .group_by(Job.job_type)
            .all()
        )
        
        # 构建类型数量映射
        count_map = {str(t.job_type.value if hasattr(t.job_type, 'value') else t.job_type): t.count for t in type_counts}
        
        # 返回所有类型（包括数量为 0 的）
        result = []
        for job_type in JobType:
            result.append(JobTypeInfo(
                value=job_type.value,
                display_name=job_type.display_name,
                count=count_map.get(job_type.value, 0)
            ))
        
        return result
        
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    except Exception as e:
        logger.error(f"获取任务类型统计失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务类型统计失败：{str(e)}")


@router.get("/{job_id}", response_model=UnifiedJobResponse)
async def get_job_detail(
    job_id: str = Path(..., description="任务 ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取单个任务详情
    
    验证任务属于当前用户后返回详细信息
    """
    try:
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return _job_to_response(job)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    except Exception as e:
        logger.error(f"获取任务详情失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败：{str(e)}")


@router.post("/{job_id}/cancel", response_model=UnifiedJobResponse)
async def cancel_job(
    job_id: str = Path(..., description="任务 ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    取消任务
    
    只能取消 Submitted 或 Processing 状态的任务
    """
    try:
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        current_status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        cancelable_statuses = [JobStatus.SUBMITTED.value, JobStatus.PROCESSING.value]
        
        if current_status not in cancelable_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"只能取消 '已提交' 或 '处理中' 状态的任务，当前状态: {current_status}"
            )
        
        # 更新状态为已取消
        job.status = JobStatus.CANCELLED
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        
        logger.info(f"任务已取消: job_id={job_id}, user={current_user.username}")
        
        return _job_to_response(job)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库操作失败")
    except Exception as e:
        db.rollback()
        logger.error(f"取消任务失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败：{str(e)}")


@router.get("/{job_id}/download-url", response_model=DownloadUrlResponse)
async def get_job_download_url(
    job_id: str = Path(..., description="任务 ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取任务结果下载链接
    
    验证任务已完成且有结果文件后，生成带 HMAC 签名的下载链接
    """
    try:
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        current_status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        zip_ready = (
            job.job_type == JobType.ANALYSIS_TRAIN
            and job.result_file
            and str(job.result_file).lower().endswith('.zip')
            and pathlib.Path(job.result_file).is_file()
        )
        if current_status != JobStatus.COMPLETED.value and not zip_ready:
            raise HTTPException(status_code=400, detail="任务尚未完成，无法下载结果")
        
        # 检查结果文件：
        # - 数据处理/数据分析：不参与“标准磁盘产物存在即可下载”的宽松条件
        # - 模型训练：允许 job-result 在 DB 写入滞后时，基于磁盘标准产物兜底可下载
        allow_standard_disk_products = job.job_type in {
            JobType.MODEL_TRAIN,
            JobType.ANALYSIS_TRAIN,
        }
        if not _user_job_has_downloadable_result(
            job_id,
            job.result_file,
            allow_standard_disk_products=allow_standard_disk_products,
        ):
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        # 生成 HMAC 签名
        timestamp = int(time.time())
        uid = current_user.id
        secret = settings.SECRET_KEY.encode()
        message = f"{job_id}:{uid}:{timestamp}".encode()
        token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]
        
        # 构建下载链接
        base = settings.download_public_base()
        download_url = f"{base}/job-result/{job_id}?uid={uid}&t={timestamp}&token={token}"
        
        return DownloadUrlResponse(
            download_url=download_url,
            expires_in=300  # 5 分钟有效期
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库查询失败")
    except Exception as e:
        logger.error(f"生成下载链接失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"生成下载链接失败：{str(e)}")


@router.delete("/{job_id}")
async def delete_job(
    job_id: str = Path(..., description="任务 ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除任务记录
    
    只能删除 Completed、Failed 或 Cancelled 状态的任务
    """
    try:
        job = db.query(Job).filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        current_status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        deletable_statuses = [
            JobStatus.COMPLETED.value, 
            JobStatus.FAILED.value, 
            JobStatus.CANCELLED.value
        ]
        
        if current_status not in deletable_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"只能删除 '已完成'、'失败' 或 '已取消' 状态的任务，当前状态: {current_status}"
            )
        
        # 物理删除记录
        db.delete(job)
        db.commit()
        
        logger.info(f"任务已删除: job_id={job_id}, user={current_user.username}")
        
        return {"message": "任务已删除", "job_id": job_id}
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="数据库操作失败")
    except Exception as e:
        db.rollback()
        logger.error(f"删除任务失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"删除任务失败：{str(e)}")

