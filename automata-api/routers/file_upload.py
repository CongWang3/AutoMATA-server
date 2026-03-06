"""
文件上传API路由
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os

from config.database import get_db
from services.file_upload_service import (
    upload_training_file, get_file_download_info, delete_training_file,
    associate_file_with_task, get_task_files, dissociate_file_from_task
)
from schemas.file_upload import (
    FileUploadResponse, FileDownloadResponse, FileDeleteResponse,
    TaskFilesResponse, TaskFileAssociation
)

router = APIRouter(prefix="/training/files", tags=["file-upload"])

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    上传训练数据文件
    
    - **file**: 要上传的文件
    - **file_type**: 文件类型 (dataset, train, validation, test, kfold_dataset)
    - **user_id**: 上传用户的ID（可选）
    """
    return await upload_training_file(db, file, file_type, user_id)

@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    下载文件
    
    - **file_id**: 文件ID
    """
    try:
        file_info = get_file_download_info(db, file_id)
        
        if not os.path.exists(file_info["file_path"]):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_info["file_path"],
            filename=file_info["filename"],
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    删除已上传的文件
    
    - **file_id**: 文件ID
    - **user_id**: 用户ID（用于权限验证，可选）
    """
    try:
        result = delete_training_file(db, file_id, user_id)
        return FileDeleteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/associate/{file_id}")
async def associate_file(
    task_id: int,
    file_id: str,
    file_type: str,
    db: Session = Depends(get_db)
):
    """
    将文件关联到训练任务
    
    - **task_id**: 训练任务ID
    - **file_id**: 文件ID
    - **file_type**: 文件类型
    """
    try:
        association = associate_file_with_task(db, task_id, file_id, file_type)
        return association
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}/files", response_model=TaskFilesResponse)
async def get_task_associated_files(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取任务关联的所有文件
    
    - **task_id**: 训练任务ID
    """
    try:
        files = get_task_files(db, task_id)
        return TaskFilesResponse(task_id=task_id, files=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}/dissociate/{file_id}")
async def dissociate_file(
    task_id: int,
    file_id: str,
    file_type: str,
    db: Session = Depends(get_db)
):
    """
    解除文件与任务的关联
    
    - **task_id**: 训练任务ID
    - **file_id**: 文件ID
    - **file_type**: 文件类型
    """
    try:
        success = dissociate_file_from_task(db, task_id, file_id, file_type)
        return {"message": "文件关联已解除", "success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_uploaded_files(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    列出已上传的文件
    
    - **user_id**: 用户ID（可选，用于筛选特定用户的文件）
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数限制
    """
    from models.file_upload import TrainingFile
    
    query = db.query(TrainingFile)
    
    if user_id:
        query = query.filter(TrainingFile.created_by == user_id)
    
    files = query.offset(skip).limit(limit).all()
    
    return [FileUploadResponse.from_orm(file) for file in files]

@router.get("/{file_id}/info", response_model=FileUploadResponse)
async def get_file_info(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文件详细信息
    
    - **file_id**: 文件ID
    """
    from models.file_upload import TrainingFile
    
    file_record = db.query(TrainingFile).filter(TrainingFile.id == file_id).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileUploadResponse.from_orm(file_record)