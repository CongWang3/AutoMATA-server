"""POST /api/v1/analysis-train/tasks"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_active_user
from api.models.job import Job
from api.models.user import User
from api.schemas.analysis_train import AnalysisTrainTaskCreate, AnalysisTrainTaskResponse
from api.services.analysis_train_service import AnalysisTrainService
from config.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis-train", tags=["分析并训练"])


def _to_response(job: Job, message: str = "任务已提交") -> AnalysisTrainTaskResponse:
    task_name = ""
    model_type = ""
    parameters = {}
    if job.input_params:
        try:
            p = json.loads(job.input_params)
            task_name = p.get("task_name", "")
            model_type = p.get("model_type", "")
            parameters = p.get("parameters", {})
        except (json.JSONDecodeError, TypeError):
            pass
    return AnalysisTrainTaskResponse(
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
        error_message=job.error_message,
    )


@router.post("/tasks", response_model=AnalysisTrainTaskResponse)
async def create_analysis_train_task(
    payload: AnalysisTrainTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AnalysisTrainService(db, current_user)
    try:
        job = svc.create_task(
            task_name=payload.task_name,
            model_type=payload.model_type,
            parameters=payload.parameters,
            analysis=payload.analysis.model_dump(),
            group_info_file_id=payload.group_info_file_id,
            dataset_path=payload.dataset_path,
            email=payload.email,
        )
        return _to_response(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("创建分析并训练任务失败")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
