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
from api.dependencies.auth import get_current_active_user
from api.models.user import User
from api.models.training import TrainingTask
from api.models.job import Job
from api.schemas.training import TrainingTaskCreate, TrainingTaskResponse
from api.schemas.file import FileUploadRequest
from api.services.file_service import FileUploadService
from api.services.training_service import TrainingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/training", tags=["模型训练"])


def _create_response(task: TrainingTask, message: str = "训练任务已提交") -> TrainingTaskResponse:
    """创建统一的响应对象"""
    resp = TrainingTaskResponse.model_validate(task)
    try:
        resp.parameters = json.loads(task.parameters)
    except Exception:
        resp.parameters = task.parameters
    resp.message = message
    return resp


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

    与 /tasks 逻辑相同，仅路由更语义化，便于前端区分不同训练类型。
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：复用相同的验证和处理逻辑，保持API一致性
    # - 已知局限：与/tasks端点功能重复，可考虑合并或明确区分用途
    # - 业务背景：为前端提供语义化的训练接口
    # - 测试重点：验证专用路由的功能正确性
    # -->
    service = TrainingService(db, current_user)

    task = await service.create_supervised_task(
        task_name=payload.task_name,
        model_type=payload.model_type,
        parameters=payload.parameters,
        dataset_path=payload.dataset_path,
    )

    return _create_response(task, "监督学习训练任务已提交")


@router.get("/tasks", response_model=List[TrainingTaskResponse])
async def list_training_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户的训练任务列表
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：使用统一的响应处理函数，减少代码重复
    # - 已知局限：批量处理时可能会有性能考虑，但目前可接受
    # - 业务背景：为用户提供历史训练任务的查询功能
    # - 测试重点：验证分页功能和大量数据的处理能力
    # -->
    tasks = (
        db.query(TrainingTask)
        .filter(TrainingTask.created_by == current_user.id)
        .order_by(TrainingTask.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [_create_response(task) for task in tasks]


@router.get("/tasks/{task_id}", response_model=TrainingTaskResponse)
async def get_training_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取单个训练任务详情
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：保持与列表接口一致的响应格式
    # - 已知局限：单个查询的权限验证逻辑较为简单
    # - 业务背景：提供训练任务的详细信息查看
    # - 测试重点：验证权限控制和不存在任务的处理
    # -->
    task = (
        db.query(TrainingTask)
        .filter(
            TrainingTask.id == task_id,
            TrainingTask.created_by == current_user.id,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="训练任务不存在")

    return _create_response(task)


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
        raise HTTPException(status_code=400, detail="任务 ID 格式不正确")

    job = (
        db.query(Job)
        .filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id,
            Job.job_type == "model_train",
        )
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")

    return {
        "job_id": job.job_id,
        "status": job.status.value if hasattr(job.status, "value") else str(job.status),
        "progress": getattr(job, "progress", None),
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
        .filter(Job.user_id == current_user.id, Job.job_type == "model_train")
        .count()
    )

    jobs = (
        db.query(Job)
        .filter(Job.user_id == current_user.id, Job.job_type == "model_train")
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
        raise HTTPException(status_code=400, detail="任务 ID 格式不正确")

    job = (
        db.query(Job)
        .filter(
            Job.job_id == job_id,
            Job.user_id == current_user.id,
            Job.job_type == "model_train",
        )
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")

    if (hasattr(job.status, "value") and job.status.value != "COMPLETED") or (
        not hasattr(job.status, "value") and job.status != "Completed"
    ):
        raise HTTPException(status_code=400, detail="训练任务尚未完成")

    if not job.result_file:
        raise HTTPException(status_code=404, detail="结果文件不存在")

    from config.settings import settings

    timestamp = int(time.time())
    uid = current_user.id
    secret = settings.SECRET_KEY.encode()
    message = f"{job_id}:{uid}:{timestamp}".encode()
    token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]

    download_url = (
        f"http://localhost:8001/job-result/{job_id}?uid={uid}&t={timestamp}&token={token}"
    )

    return TrainingDownloadUrlResponse(download_url=download_url, expires_in=300)

