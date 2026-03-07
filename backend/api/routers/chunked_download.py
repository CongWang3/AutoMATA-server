"""
分片下载API路由 - 基于HTTP Range请求的简单实现
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
import logging
from pathlib import Path

from config.database import get_db
from api.dependencies.auth import get_current_active_user
from api.models.user import User
from api.services.file_service import FileUploadService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["分片下载"])

@router.get("/chunked/session/{file_id}")
def get_file_info(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文件基本信息用于分片下载
    """
    try:
        service = FileUploadService(db, current_user)
        db_file = service.get_file_by_id(file_id)
        
        if not db_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "file_id": file_id,
            "file_name": db_file.original_name,
            "file_size": db_file.file_size,
            "chunk_size": 5 * 1024 * 1024,  # 5MB默认分片大小
            "support_range": True
        }
        
    except Exception as e:
        logger.error(f"获取文件信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunked/download/{file_id}")
def download_file_chunk(
    file_id: str,
    range: str = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    基于Range请求的文件分片下载
    支持标准HTTP Range请求头: bytes=start-end
    """
    try:
        service = FileUploadService(db, current_user)
        db_file = service.get_file_by_id(file_id)
        
        if not db_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = Path(db_file.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件在磁盘上不存在")
        
        file_size = file_path.stat().st_size
        
        # 解析Range请求头
        start, end = 0, file_size - 1
        if range and range.startswith('bytes='):
            range_value = range[6:]  # 移除 'bytes=' 前缀
            if '-' in range_value:
                start_str, end_str = range_value.split('-', 1)
                if start_str:
                    start = int(start_str)
                if end_str:
                    end = min(int(end_str), file_size - 1)
                else:
                    end = file_size - 1
        
        # 验证范围有效性
        if start >= file_size or start < 0 or end < start:
            return Response(
                status_code=416,
                headers={
                    "Content-Range": f"bytes */{file_size}"
                }
            )
        
        # 计算实际内容长度
        content_length = end - start + 1
        
        def file_iterator():
            """流式读取文件指定范围"""
            with open(file_path, 'rb') as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data
                    remaining -= len(data)
        
        # 设置响应头
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'attachment; filename="{db_file.original_name}"'
        }
        
        logger.info(f"分片下载: {file_id}, 范围 {start}-{end}/{file_size}")
        
        return StreamingResponse(
            file_iterator(),
            status_code=206,  # Partial Content
            headers=headers,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分片下载失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))