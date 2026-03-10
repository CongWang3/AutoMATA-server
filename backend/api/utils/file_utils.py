"""
文件处理工具函数
"""
import os
from pathlib import Path
from typing import Union
import logging
from fastapi import UploadFile

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB 文件大小限制
CHUNK_SIZE = 8192  # 8KB 读取块大小

async def save_uploaded_file(
    file: UploadFile, 
    upload_dir: Union[str, Path], 
    prefix: str = ""
) -> Path:
    """
    保存上传的文件到指定目录（流式处理，支持大文件）
    
    Args:
        file: 上传的文件对象
        upload_dir: 上传目录路径
        prefix: 文件名前缀（通常使用 job_id）
        
    Returns:
        保存文件的完整路径
        
    Raises:
        ValueError: 文件名为空或目录不可写
        IOError: 文件保存失败
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：使用流式处理优化大文件上传，避免内存溢出
    # - 已知局限：对于超大文件可能需要进一步优化为分块上传
    # - 业务背景：支持数据处理模块的高性能文件上传需求
    # - 测试重点：文件大小限制、流式读写、异常处理、性能基准
    # -->
    
    if not file.filename:
        raise ValueError("文件名不能为空")
    
    # 检查文件大小
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise ValueError(f"文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)")
    
    # 确保目录存在
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    
    # 验证目录可写
    if not os.access(upload_path, os.W_OK):
        raise ValueError(f"上传目录不可写: {upload_path}")
    
    # 生成安全的文件名
    safe_filename = sanitize_filename(file.filename)
    if prefix:
        safe_filename = f"{prefix}_{safe_filename}"
    
    file_path = upload_path / safe_filename
    
    try:
        # 流式读写文件，避免大文件占用过多内存
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
        
        # 验证文件是否完整保存
        saved_size = file_path.stat().st_size
        if hasattr(file, 'size') and file.size and saved_size != file.size:
            raise IOError(f"文件保存不完整: 期望 {file.size} 字节，实际 {saved_size} 字节")
        
        logger.info(f"文件保存成功: {file_path} (大小: {saved_size} 字节)")
        return file_path
        
    except Exception as e:
        # 清理可能创建的不完整文件
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        logger.error(f"文件保存失败: {file_path}, error={str(e)}")
        raise IOError(f"文件保存失败: {str(e)}")

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的安全文件名
    """
    # 移除路径分隔符和危险字符
    unsafe_chars = ['/', '\\', '..', ':', '*', '?', '"', '<', '>', '|']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # 限制文件名长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节）
        
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    return path.stat().st_size

def is_valid_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    验证文件扩展名是否被允许
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表（如 ['.txt', '.csv']）
        
    Returns:
        是否有效
    """
    if not filename:
        return False
    
    _, ext = os.path.splitext(filename.lower())
    return ext in [ext.lower() for ext in allowed_extensions]