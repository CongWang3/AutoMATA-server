from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from models.training_job import TrainingJob, TrainingLog
from schemas.training_job import TrainingJobCreate, TrainingJobUpdate, TrainingJob, TrainingLogCreate, TrainingLog
from services import training_job_service

router = APIRouter(prefix="/api/training")


@router.get("/tasks", response_model=List[TrainingJob])
def get_training_tasks(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    获取训练任务列表，支持分页
    """
    tasks = training_job_service.get_training_tasks(db, skip=skip, limit=limit)
    return tasks


@router.get("/tasks/{task_id}", response_model=TrainingJob)
def get_training_task(task_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个训练任务
    """
    task = training_job_service.get_training_task(db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Training task not found")
    return task


@router.post("/tasks", response_model=TrainingJob)
def create_training_task(task: TrainingJobCreate, db: Session = Depends(get_db)):
    """
    创建新的训练任务
    """
    return training_job_service.create_training_task(db=db, task=task)


@router.put("/tasks/{task_id}", response_model=TrainingJob)
def update_training_task(
    task_id: int, 
    task_update: TrainingJobUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新训练任务信息
    """
    updated_task = training_job_service.update_training_task(
        db, 
        task_id=task_id, 
        task_update=task_update
    )
    if not updated_task:
        raise HTTPException(status_code=404, detail="Training task not found")
    return updated_task


@router.delete("/tasks/{task_id}")
def delete_training_task(task_id: int, db: Session = Depends(get_db)):
    """
    删除训练任务
    """
    deleted = training_job_service.delete_training_task(db, task_id=task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Training task not found")
    return {"message": "Task deleted successfully"}


@router.get("/tasks/{task_id}/logs", response_model=List[TrainingLog])
def get_training_logs(task_id: int, db: Session = Depends(get_db)):
    """
    获取训练任务的日志
    """
    logs = training_job_service.get_training_logs(db, task_id=task_id)
    return logs


@router.post("/tasks/{task_id}/logs")
def add_training_log(
    task_id: int, 
    log: TrainingLogCreate, 
    db: Session = Depends(get_db)
):
    """
    为训练任务添加日志
    """
    # Create a new log object with task_id
    from schemas.training_job import TrainingLogBase
    log_data = TrainingLogBase(
        task_id=task_id,
        log_level=log.log_level,
        message=log.message
    )
    result = training_job_service.create_training_log(db, log=log_data)
    return {"message": "Log added successfully"}


@router.get("/models/available")
def get_available_models():
    """
    获取可用的模型列表
    """
    models_info = training_job_service.get_available_models_info()
    return {
        "models": models_info,
        "count": len(models_info)
    }