"""
文件上传服务实现
"""
import os
import uuid
import shutil
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import mimetypes
from datetime import datetime, timedelta

from models.file_upload import TrainingFile, TaskFile
from models.training_job import TrainingJob
from schemas.file_upload import FileUploadResponse, TaskFileAssociation

# 文件存储配置
UPLOAD_BASE_DIR = "/xp/www/AutoMATA/uploaded_files"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.txt', '.csv', '.tsv', '.json', '.yaml', '.yml'}

def init_upload_directory():
    """初始化上传目录"""
    os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
    print(f"📁 文件上传目录已初始化: {UPLOAD_BASE_DIR}")

def validate_file(file: UploadFile) -> tuple:
    """验证上传文件"""
    # 检查文件扩展名
    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件类型: {ext}. 支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置文件指针
    
    if file_size > MAX_FILE_SIZE:
        return False, f"文件大小超过限制: {file_size} bytes. 最大允许: {MAX_FILE_SIZE} bytes"
    
    return True, ""

def generate_secure_filename(original_filename: str) -> str:
    """生成安全的文件名"""
    # 移除危险字符
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
    safe_filename = "".join(c if c in safe_chars else "_" for c in original_filename)
    
    # 添加UUID避免重复
    file_uuid = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(safe_filename)
    
    return f"{name}_{file_uuid}{ext}"

async def upload_training_file(
    db: Session,
    file: UploadFile,
    file_type: str,
    user_id: Optional[int] = None
) -> FileUploadResponse:
    """上传训练数据文件"""
    try:
        # 验证文件
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 生成安全文件名
        secure_filename = generate_secure_filename(file.filename or "unnamed_file")
        file_path = os.path.join(UPLOAD_BASE_DIR, secure_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file.filename or "")
        
        # 创建数据库记录
        db_file = TrainingFile(
            original_filename=file.filename or "unnamed_file",
            stored_filename=secure_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            created_by=user_id
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return FileUploadResponse.from_orm(db_file)
        
    except Exception as e:
        db.rollback()
        # 清理已上传的文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

def get_file_download_info(db: Session, file_id: str) -> dict:
    """获取文件下载信息"""
    db_file = db.query(TrainingFile).filter(TrainingFile.id == file_id).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="文件在磁盘上不存在")
    
    # 生成临时下载链接（这里可以集成对象存储或生成临时令牌）
    download_url = f"/api/training/files/{file_id}/download"
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    return {
        "download_url": download_url,
        "expires_at": expires_at,
        "filename": db_file.original_filename,
        "file_path": db_file.file_path
    }

def delete_training_file(db: Session, file_id: str, user_id: Optional[int] = None) -> dict:
    """删除已上传的文件"""
    db_file = db.query(TrainingFile).filter(TrainingFile.id == file_id).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查权限（如果指定了用户ID）
    if user_id and db_file.created_by != user_id:
        raise HTTPException(status_code=403, detail="无权删除此文件")
    
    try:
        # 删除物理文件
        if os.path.exists(db_file.file_path):
            os.remove(db_file.file_path)
        
        # 删除数据库记录
        file_id = db_file.id
        db.delete(db_file)
        db.commit()
        
        return {
            "message": "文件删除成功",
            "deleted_file_id": file_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")

def associate_file_with_task(
    db: Session,
    task_id: int,
    file_id: str,
    file_type: str
) -> TaskFileAssociation:
    """将文件关联到训练任务"""
    # 验证任务存在
    task = db.query(TrainingJob).filter(TrainingJob.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    # 验证文件存在
    file_record = db.query(TrainingFile).filter(TrainingFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查是否已有关联
    existing_assoc = db.query(TaskFile).filter(
        TaskFile.task_id == task_id,
        TaskFile.file_id == file_id,
        TaskFile.file_type == file_type
    ).first()
    
    if existing_assoc:
        raise HTTPException(status_code=400, detail="文件已关联到此任务")
    
    # 创建关联记录
    task_file = TaskFile(
        task_id=task_id,
        file_id=file_id,
        file_type=file_type
    )
    
    db.add(task_file)
    db.commit()
    
    return TaskFileAssociation(
        task_id=task_id,
        file_id=file_id,
        file_type=file_type,
        original_filename=file_record.original_filename,
        file_size=file_record.file_size,
        upload_time=file_record.upload_time
    )

def get_task_files(db: Session, task_id: int) -> List[TaskFileAssociation]:
    """获取任务关联的所有文件"""
    task = db.query(TrainingJob).filter(TrainingJob.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    associations = db.query(TaskFile).filter(TaskFile.task_id == task_id).all()
    
    result = []
    for assoc in associations:
        file_record = db.query(TrainingFile).filter(TrainingFile.id == assoc.file_id).first()
        if file_record:
            result.append(TaskFileAssociation(
                task_id=assoc.task_id,
                file_id=assoc.file_id,
                file_type=assoc.file_type,
                original_filename=file_record.original_filename,
                file_size=file_record.file_size,
                upload_time=file_record.upload_time
            ))
    
    return result

def dissociate_file_from_task(db: Session, task_id: int, file_id: str, file_type: str) -> bool:
    """解除文件与任务的关联"""
    assoc = db.query(TaskFile).filter(
        TaskFile.task_id == task_id,
        TaskFile.file_id == file_id,
        TaskFile.file_type == file_type
    ).first()
    
    if not assoc:
        raise HTTPException(status_code=404, detail="文件关联记录不存在")
    
    db.delete(assoc)
    db.commit()
    return True

# 初始化上传目录
init_upload_directory()