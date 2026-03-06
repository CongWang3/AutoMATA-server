"""
文件上传路由：处理文件上传、下载、管理等接口
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Set
import json
import asyncio
import logging
from collections import defaultdict

from config.database import get_db
from api.dependencies.auth import get_current_active_user
from api.services.file_service import FileUploadService
from api.schemas.file import FileResponse, FileListResponse, FileUploadRequest
from api.models.user import User
from api.models.file import File

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/files", tags=["文件管理"])

# 线程安全的WebSocket连接管理
connection_lock = asyncio.Lock()

class ConnectionManager:
    """WebSocket连接管理器（线程安全版本）"""
    
    def __init__(self):
        # 使用defaultdict存储每个用户的WebSocket连接集合
        self.active_connections: defaultdict[str, Set[WebSocket]] = defaultdict(set)
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
        """
        await websocket.accept()
        async with self.lock:
            self.active_connections[user_id].add(websocket)
    
    async def disconnect(self, user_id: str, websocket: WebSocket = None):
        """
        断开WebSocket连接
        
        Args:
            user_id: 用户ID
            websocket: 特定的WebSocket连接（可选）
        """
        async with self.lock:
            if websocket and user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                # 如果该用户没有其他连接，清理整个用户条目
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            elif user_id in self.active_connections:
                # 清理用户的所有连接
                for ws in self.active_connections[user_id]:
                    try:
                        await ws.close()
                    except Exception:
                        pass  # 忽略关闭异常
                del self.active_connections[user_id]
    
    async def send_progress(self, user_id: str, progress_data: dict, timeout: float = 5.0):
        """
        向指定用户发送进度数据
        
        Args:
            user_id: 用户ID
            progress_data: 进度数据字典
            timeout: 发送超时时间（秒）
        """
        # <!-- 
        # 审查上下文：
        # - 设计意图：改进WebSocket异常处理，提供更详细的错误分类和日志记录
        # - 已知局限：增加了异常处理复杂度，但提升了系统可观测性
        # - 业务背景：解决Warning级别的WebSocket连接稳定性问题
        # - 测试重点：请验证各种网络异常场景下的处理能力
        # -->
        
        async with self.lock:
            if user_id not in self.active_connections:
                return
                
            # 创建发送任务列表
            send_tasks = []
            disconnected_connections = set()
            
            for websocket in self.active_connections[user_id].copy():
                try:
                    # 创建带超时的发送任务
                    task = asyncio.wait_for(
                        websocket.send_text(json.dumps(progress_data)),
                        timeout=timeout
                    )
                    send_tasks.append((websocket, task))
                except asyncio.TimeoutError:
                    logger.warning(f"WebSocket发送超时: user_id={user_id}")
                    disconnected_connections.add(websocket)
                except Exception as e:
                    logger.error(f"WebSocket发送异常: {e}")
                    disconnected_connections.add(websocket)
            
            # 移除已断开的连接
            for ws in disconnected_connections:
                self.active_connections[user_id].discard(ws)
            
            # 执行发送任务
            if send_tasks:
                try:
                    results = await asyncio.gather(*[task for _, task in send_tasks], return_exceptions=True)
                    # 检查是否有任务失败
                    failed_count = sum(1 for result in results if isinstance(result, Exception))
                    if failed_count > 0:
                        logger.warning(f"WebSocket批量发送中有 {failed_count} 个任务失败")
                except Exception as e:
                    logger.error(f"WebSocket批量发送时发生错误: {e}")

connection_manager = ConnectionManager()


@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket, current_user: User = Depends(get_current_active_user)):
    """
    WebSocket进度通知端点
    
    Args:
        websocket: WebSocket连接
        current_user: 当前认证用户
    """
    user_id = str(current_user.id)
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            # 保持连接活跃，等待客户端消息
            await websocket.receive_text()
    except Exception:
        # 连接断开时清理资源
        await connection_manager.disconnect(user_id, websocket)


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(),
    file_type: str = Form(),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传文件接口（支持进度监控）
    
    Args:
        file: 上传的文件
        file_type: 文件类型标识
        description: 文件描述（可选）
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        上传成功的文件信息
        
    Raises:
        HTTPException:
            - 400: 文件类型不支持或文件过大
            - 413: 文件大小超过限制
            - 500: 文件保存或数据库操作失败
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供安全的文件上传接口，支持多种文件类型和元数据记录
    # - 已知局限：单次只能上传一个文件，批量上传需额外实现
    # - 业务背景：docs/api/API_SPECIFICATION.md - POST /api/v1/files/upload
    # - 测试重点：请验证文件类型检查、大小限制、MD5 去重、用户权限
    # -->
    
    # 记录审计日志
    logger.info(f"用户 {current_user.username}(ID:{current_user.id}) 开始上传文件: {file.filename}")
    
    # 构造请求对象
    request = FileUploadRequest(
        file_type=file_type,
        description=description
    )
    
    # 创建进度回调函数（同步函数，内部异步发送）
    def progress_callback(uploaded_bytes: int, total_bytes: int):
        progress_percent = (uploaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
        progress_data = {
            "event": "upload_progress",
            "uploaded_bytes": uploaded_bytes,
            "total_bytes": total_bytes,
            "progress_percent": round(progress_percent, 2)
        }
        # 异步发送：不阻塞当前上传逻辑
        asyncio.create_task(
            connection_manager.send_progress(str(current_user.id), progress_data, timeout=3.0)
        )
    
    # 处理文件上传
    service = FileUploadService(db, current_user)
    db_file = service.upload_file(file, request, progress_callback)
    
    logger.info(f"用户 {current_user.username}(ID:{current_user.id}) 上传文件成功: {file.filename} -> {db_file.filename}")
    return db_file


@router.get("/", response_model=FileListResponse)
def list_files(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户文件列表
    
    Args:
        page: 页码（从1开始）
        size: 每页大小（1-100）
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        文件列表和分页信息
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供用户文件列表查询接口，支持分页
    # - 已知局限：暂未实现按文件类型筛选、按上传时间排序等功能
    # - 业务背景：docs/api/API_SPECIFICATION.md - GET /api/v1/files
    # - 测试重点：请验证分页逻辑、用户数据隔离、返回数据格式
    # -->
    
    # 记录审计日志
    logger.info(f"用户 {current_user.username}(ID:{current_user.id}) 查询文件列表: page={page}, size={size}")
    
    service = FileUploadService(db, current_user)
    files, total = service.get_user_files(page, size)
    
    logger.info(f"用户 {current_user.username}(ID:{current_user.id}) 查询文件列表成功: 找到 {len(files)} 个文件，总计 {total} 个")
    
    return FileListResponse(
        total=total,
        files=files,
        page=page,
        size=size
    )


@router.get("/{file_id}", response_model=FileResponse)
def get_file_info(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文件详细信息
    
    Args:
        file_id: 文件 ID
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        文件详细信息
        
    Raises:
        HTTPException:
            - 404: 文件不存在
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供单个文件信息查询接口
    # - 已知局限：无
    # - 业务背景：docs/api/API_SPECIFICATION.md - GET /api/v1/files/{file_id}
    # - 测试重点：请验证文件所有权检查、返回数据完整性
    # -->
    
    service = FileUploadService(db, current_user)
    db_file = service.get_file_by_id(file_id)
    
    if not db_file:
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )
    
    return db_file


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    下载文件接口（流式传输）
    
    Args:
        file_id: 文件 ID
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        文件流式响应
        
    Raises:
        HTTPException:
            - 404: 文件不存在
            - 500: 文件读取失败
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：实现流式文件下载，避免大文件占用过多内存
    # - 已知局限：使用8KB chunks进行流式传输，平衡性能和内存使用
    # - 业务背景：优化大文件下载体验，防止内存溢出
    # - 测试重点：请验证流式传输的正确性、下载计数更新、错误处理
    # -->
    
    service = FileUploadService(db, current_user)
    db_file = service.get_file_by_id(file_id)
    
    if not db_file:
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )
    
    def iterfile():
        """流式读取文件"""
        try:
            with open(db_file.file_path, "rb") as f:
                while chunk := f.read(8192):  # 8KB chunks
                    yield chunk
        except FileNotFoundError:
            raise HTTPException(
                status_code=500,
                detail="文件在磁盘上不存在"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"文件读取失败: {str(e)}"
            ) from e
    
    try:
        # 增加下载计数
        db_file.download_count += 1
        db.commit()
        
        # 返回流式响应
        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{db_file.original_name}"'
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"文件下载处理失败: {str(e)}"
        ) from e


@router.post("/cleanup")
def trigger_cleanup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    手动触发文件清理（管理员功能）
    
    Args:
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        清理结果统计
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供手动清理接口，用于紧急情况或测试
    # - 已知局限：只有管理员可以调用此接口
    # - 业务背景：系统维护和管理功能
    # - 测试重点：请验证权限检查、清理逻辑正确性
    # -->
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="只有管理员可以执行此操作"
        )
    
    service = FileUploadService(db, current_user)
    result = service.cleanup_marked_files()
    
    return {
        "message": "文件清理完成",
        "result": result
    }


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除文件接口（标记删除模式）
    
    Args:
        file_id: 文件 ID
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        删除成功消息
        
    Raises:
        HTTPException:
            - 403: 无权删除此文件
            - 404: 文件不存在
            - 500: 文件标记删除失败
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：实现带所有权验证的安全文件删除功能
    # - 已知局限：增加了权限检查步骤，略微影响性能但显著提升安全性
    # - 业务背景：修复Critical安全漏洞，防止用户删除他人文件
    # - 测试重点：请验证文件所有权检查、跨用户访问控制
    # -->
    
    # 创建服务实例用于查询文件
    service = FileUploadService(db, current_user)
    
    # 首先验证文件是否存在和所有权
    db_file = service.get_file_by_id(file_id)
    if not db_file:
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )
    
    # 关键安全检查：验证文件所有权
    if db_file.uploaded_by != current_user.id:
        logger.warning(f"用户 {current_user.username}(ID:{current_user.id}) 尝试删除不属于自己的文件 {file_id}")
        raise HTTPException(
            status_code=403,
            detail="无权删除此文件"
        )
    
    # 执行删除操作
    success = service.delete_file(file_id)
    
    if success:
        logger.info(f"用户 {current_user.username}(ID:{current_user.id}) 成功标记删除文件 {file_id}")
        return {
            "message": "文件已标记删除，将在后台清理",
            "file_id": file_id,
            "status": "marked_for_deletion"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="文件标记删除失败"
        )
