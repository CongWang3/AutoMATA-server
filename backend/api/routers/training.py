"""
模型训练路由：训练任务管理与文件上传接口

注意：
- 路由前缀为 /api/v1/training，与数据处理模块保持一致风格
- 文件上传路径为 /api/v1/training/files/upload
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session

from config.database import get_db
from config.settings import settings
from api.dependencies.auth import get_current_active_user
from api.models.user import User
from api.models.job import Job, JobType, JobStatus
from api.schemas.training import TrainingTaskCreate, TrainingTaskResponse
from api.schemas.file import FileUploadRequest
from api.services.file_service import FileUploadService
from api.services.training_service import TrainingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/training", tags=["模型训练"])


def _create_response(job: Job, message: str = "训练任务已提交") -> TrainingTaskResponse:
    """创建统一的响应对象（基于 Job 对象）"""
    import json
    
    # 从 input_params 中提取训练参数
    task_name = ""
    model_type = ""
    parameters = {}
    
    if job.input_params:
        try:
            params = json.loads(job.input_params)
            task_name = params.get("task_name", "")
            model_type = params.get("model_type", "")
            parameters = params.get("parameters", {})
        except (json.JSONDecodeError, TypeError):
            pass
    
    return TrainingTaskResponse(
        task_name=task_name,
        model_type=model_type,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        job_id=job.job_id,
        created_at=job.created_at,
        message=message,
        parameters=parameters,
        progress=job.progress or 0,
        current_step=job.current_step,
        result_file=job.result_file,
        error_message=job.error_message
    )


@router.post("/tasks", response_model=TrainingTaskResponse)
async def create_training_task(
    payload: TrainingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建训练任务（通用入口，当前等价于监督学习训练）
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：利用Pydantic模型的自动验证，简化参数处理逻辑
    # - 已知局限：依赖Pydantic的验证机制，需要确保schema定义完整
    # - 业务背景：统一的训练任务创建入口，支持多种训练类型
    # - 测试重点：验证各种非法输入的拒绝和正确输入的处理
    # -->
    service = TrainingService(db, current_user)

    task = await service.create_supervised_task(
        task_name=payload.task_name,
        model_type=payload.model_type,
        parameters=payload.parameters,
        dataset_path=payload.dataset_path,
        email=payload.email,
    )

    return _create_response(task)


@router.post("/supervised", response_model=TrainingTaskResponse)
async def train_supervised(
    payload: TrainingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    监督学习训练专用入口
    """
    service = TrainingService(db, current_user)

    task = await service.create_supervised_task(
        task_name=payload.task_name,
        model_type=payload.model_type,
        parameters=payload.parameters,
        dataset_path=payload.dataset_path,
        email=payload.email,
    )

    return _create_response(task, "监督学习训练任务已提交")


@router.post("/unsupervised", response_model=TrainingTaskResponse)
async def train_unsupervised(
    payload: TrainingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    无监督学习训练专用入口
    """
    service = TrainingService(db, current_user)

    task = await service.create_unsupervised_task(
        task_name=payload.task_name,
        model_type=payload.model_type,
        parameters=payload.parameters,
        dataset_path=payload.dataset_path,
        email=payload.email,
    )

    return _create_response(task, "无监督学习训练任务已提交")


@router.post("/semi-supervised", response_model=TrainingTaskResponse)
async def train_semi_supervised(
    payload: TrainingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    半监督学习训练专用入口
    """
    service = TrainingService(db, current_user)

    task = await service.create_semi_supervised_task(
        task_name=payload.task_name,
        model_type=payload.model_type,
        parameters=payload.parameters,
        dataset_path=payload.dataset_path,
        email=payload.email,
    )

    return _create_response(task, "半监督学习训练任务已提交")


@router.get("/tasks", response_model=List[TrainingTaskResponse])
async def list_training_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户的训练任务列表（从 jobs 表查询 MODEL_TRAIN 类型）
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：使用统一的 jobs 表查询，不再使用 training_tasks 表
    # - 已知局限：批量处理时可能会有性能考虑，但目前可接受
    # - 业务背景：为用户提供历史训练任务的查询功能
    # - 测试重点：验证分页功能和大量数据的处理能力
    # -->
    jobs = (
        db.query(Job)
        .filter(
            Job.user_id == current_user.id,
            Job.job_type == JobType.MODEL_TRAIN
        )
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [_create_response(job) for job in jobs]


@router.get("/tasks/{task_id}", response_model=TrainingTaskResponse)
async def get_training_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取单个训练任务详情（通过 job_id 查询）
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：保持与列表接口一致的响应格式
    # - 已知局限：单个查询的权限验证逻辑较为简单
    # - 业务背景：提供训练任务的详细信息查看
    # - 测试重点：验证权限控制和不存在任务的处理
    # -->
    job = (
        db.query(Job)
        .filter(
            Job.job_id == task_id,
            Job.user_id == current_user.id,
            Job.job_type == JobType.MODEL_TRAIN
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Training task does not exist")

    return _create_response(job)


@router.post("/files/upload")
async def upload_training_file(
    file: UploadFile = File(...),
    file_type: str = Form("dataset"),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    训练相关文件上传接口

    与前端 trainingApi.uploadFile 保持兼容：
    - URL:  /training/files/upload
    - 返回: { "file_id": "...", "file_path": "..." }
    """
    service = FileUploadService(db, current_user)
    request = FileUploadRequest(file_type=file_type, description=description)

    def progress_callback(uploaded_bytes: int, total_bytes: int):
        # 当前训练文件上传不做进度 WebSocket 推送，仅记录日志
        if total_bytes > 0:
            percent = uploaded_bytes / total_bytes * 100
            logger.debug(f"[TRAIN UPLOAD] 进度: {percent:.1f}%")

    db_file = service.upload_file(file, request, progress_callback)
    return {
        "file_id": db_file.id,
        "file_path": db_file.file_path,
    }


# ---------------- 任务状态与下载链接（与数据处理模块风格类似） ----------------

import re
import hmac
import hashlib
import time
from pydantic import BaseModel

JOB_ID_PATTERN = re.compile(r"^\d{14}_[a-zA-Z0-9]{8}$")


class TrainingDownloadUrlResponse(BaseModel):
    """训练任务结果下载链接响应模型"""

    download_url: str
    expires_in: int


@router.get("/status/{job_id}")
async def get_training_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    查询训练任务状态（仅限 MODEL_TRAIN 类型）
    """
    if not JOB_ID_PATTERN.match(job_id):
        raise HTTPException(status_code=400, detail="Task ID format is incorrect")

    job = (
        db.query(Job)
        .filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id,
            Job.job_type == JobType.MODEL_TRAIN,
        )
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Training task does not exist")

    return {
        "job_id": job.job_id,
        "status": job.status.value if hasattr(job.status, "value") else str(job.status),
        "progress": job.progress or 0,
        "current_step": job.current_step,
        "result_file": job.result_file,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.get("/jobs")
async def get_training_jobs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户的训练任务列表（仅 MODEL_TRAIN）
    """
    total = (
        db.query(Job)
        .filter(Job.user_id == current_user.id, Job.job_type == JobType.MODEL_TRAIN)
        .count()
    )

    jobs = (
        db.query(Job)
        .filter(Job.user_id == current_user.id, Job.job_type == JobType.MODEL_TRAIN)
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    job_items = [
        {
            "job_id": job.job_id,
            "job_type": job.job_type.value
            if hasattr(job.job_type, "value")
            else str(job.job_type),
            "status": job.status.value
            if hasattr(job.status, "value")
            else str(job.status),
            "progress": job.progress or 0,
            "current_step": job.current_step,
            "input_params": job.input_params,
            "result_file": job.result_file,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
        for job in jobs
    ]

    return {"total": total, "jobs": job_items}


@router.get("/download-url/{job_id}", response_model=TrainingDownloadUrlResponse)
async def get_training_download_url(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取训练任务结果下载链接（带签名）
    """
    if not JOB_ID_PATTERN.match(job_id):
        raise HTTPException(status_code=400, detail="Task ID format is incorrect")

    job = (
        db.query(Job)
        .filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id,
            Job.job_type == JobType.MODEL_TRAIN,
        )
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Training task does not exist")

    if (hasattr(job.status, "value") and job.status.value != JobStatus.COMPLETED.value) or (
        not hasattr(job.status, "value") and job.status != "Completed"
    ):
        raise HTTPException(status_code=400, detail="Training task is not completed")

    if not job.result_file:
        raise HTTPException(status_code=404, detail="Result file does not exist")

    timestamp = int(time.time())
    uid = current_user.id
    secret = settings.SECRET_KEY.encode()
    message = f"{job_id}:{uid}:{timestamp}".encode()
    token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]

    download_url = settings.download_public_url(
        f"/job-result/{job_id}?uid={uid}&t={timestamp}&token={token}"
    )

    return TrainingDownloadUrlResponse(download_url=download_url, expires_in=300)

