"""
文件管理相关工具
提供查询用户文件列表和文件详情的功能
"""
import logging
import json
from typing import Optional, Annotated
from langchain_core.tools import tool, InjectedToolArg
from langchain_core.runnables import RunnableConfig
from pathlib import Path

from config.database import SessionLocal
from api.models.file import File

logger = logging.getLogger(__name__)


@tool
def list_user_files(
    page: int = 1,
    size: int = 20,
    file_type: Optional[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = {}
) -> str:
    """
    列出用户上传的文件。
    
    返回用户上传的文件列表，支持分页和按文件类型筛选。
    
    参数说明：
    - page: 页码，从 1 开始
    - size: 每页大小，默认 20
    - file_type: 文件类型过滤（可选）
    
    返回：JSON 格式的文件列表，包含文件名、原始名称、大小、类型等信息
    
    Args:
        page: 页码
        size: 每页大小
        file_type: 文件类型过滤
        config: LangChain 运行配置
        
    Returns:
        JSON 格式的文件列表字符串
    """
    logger.info(f"[File Tools] list_user_files 调用, page={page}, size={size}, file_type={file_type}")
    
    db = None
    try:
        # 从配置中获取用户 ID
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id")
        tool_context = configurable.get("tool_context", {})
        
        if not user_id:
            logger.warning("[File Tools] user_id 为空，config 内容: %s", configurable)
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 确保 user_id 为整数（数据库字段为 Integer）
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"[File Tools] user_id 类型转换失败: {user_id}")
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 获取或创建数据库会话
        db = SessionLocal()
        should_close_db = True
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 构建查询 - 只查询未删除的文件
        query = db.query(File).filter(
            File.uploaded_by == user_id,
            File.delete_marked_at.is_(None)  # 排除已标记删除的文件
        )
        
        # 文件类型过滤
        if file_type:
            query = query.filter(File.file_type == file_type)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        files = query.order_by(File.created_at.desc()).offset(offset).limit(size).all()
        
        # 转换为可序列化格式
        result = {
            "total": total,
            "page": page,
            "size": size,
            "files": []
        }
        
        for file in files:
            file_dict = {
                "id": file.id,
                "filename": file.filename,
                "original_name": file.original_name,
                "file_size": file.file_size,
                "file_size_display": _format_file_size(file.file_size),
                "file_type": file.file_type,
                "created_at": file.created_at.isoformat() if file.created_at else None,
            }
            result["files"].append(file_dict)
        
        logger.info(f"[File Tools] 查询到 {len(files)} 个文件，共 {total} 个")
        
        if should_close_db:
            db.close()
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[File Tools] list_user_files 失败: {e}")
        if db:
            db.close()
        return json.dumps({"error": f"查询文件列表失败: {str(e)}"}, ensure_ascii=False)


@tool
def get_file_info(
    file_id: str,
    config: Annotated[RunnableConfig, InjectedToolArg] = {}
) -> str:
    """
    获取指定文件的详细信息。
    
    返回文件的完整信息，包括文件路径、MD5 哈希值等。
    可用于在分析前确认文件信息。
    
    Args:
        file_id: 文件 ID
        config: LangChain 运行配置
        
    Returns:
        JSON 格式的文件详情字符串
    """
    logger.info(f"[File Tools] get_file_info 调用, file_id={file_id}")
    
    db = None
    try:
        # 从配置中获取用户 ID
        configurable = config.get("configurable", {}) if config else {}
        user_id = configurable.get("user_id")
        tool_context = configurable.get("tool_context", {})
        
        if not user_id:
            logger.warning("[File Tools] user_id 为空，config 内容: %s", configurable)
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 确保 user_id 为整数（数据库字段为 Integer）
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"[File Tools] user_id 类型转换失败: {user_id}")
            return json.dumps({"error": "未找到用户信息，请重新登录"}, ensure_ascii=False)
        
        # 创建数据库会话
        db = SessionLocal()
        should_close_db = True
        
        # 查询文件
        file = db.query(File).filter(
            File.id == file_id,
            File.uploaded_by == user_id,
            File.delete_marked_at.is_(None)
        ).first()
        
        if not file:
            if should_close_db:
                db.close()
            return json.dumps({"error": f"文件不存在: {file_id}"}, ensure_ascii=False)
        
        # 检查文件物理存在
        file_exists = Path(file.file_path).exists() if file.file_path else False
        
        # 构建详细信息
        result = {
            "id": file.id,
            "filename": file.filename,
            "original_name": file.original_name,
            "file_path": file.file_path,
            "file_size": file.file_size,
            "file_size_display": _format_file_size(file.file_size),
            "file_type": file.file_type,
            "mime_type": file.mime_type,
            "md5_hash": file.md5_hash,
            "storage_type": file.storage_type,
            "download_count": file.download_count,
            "file_exists": file_exists,
            "created_at": file.created_at.isoformat() if file.created_at else None,
            "updated_at": file.updated_at.isoformat() if file.updated_at else None,
        }
        
        logger.info(f"[File Tools] 获取文件详情成功: {file_id}")
        
        if should_close_db:
            db.close()
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[File Tools] get_file_info 失败: {e}")
        if db:
            db.close()
        return json.dumps({"error": f"获取文件详情失败: {str(e)}"}, ensure_ascii=False)


def _format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的字符串，如 "1.5 MB"
    """
    if size_bytes is None:
        return "未知"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} PB"
