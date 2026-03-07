"""
文件上传路由：处理文件上传、下载、管理等接口
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, WebSocket, BackgroundTasks
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
from api.services.auth_service import AuthService
from api.schemas.file import FileResponse, FileListResponse, FileUploadRequest
from api.models.user import User
from api.models.file import File
from api.utils.download_queue import download_queue_manager, DownloadTask

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
    
    async def connect_without_accept(self, websocket: WebSocket, user_id: str):
        """
        建立WebSocket连接（不调用accept，适用于已经accept过的连接）
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
        """
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
                connections_to_close = list(self.active_connections[user_id])
                del self.active_connections[user_id]
                for ws in connections_to_close:
                    try:
                        if hasattr(ws, 'client_state') and ws.client_state.name == 'CONNECTED':
                            await ws.close()
                    except Exception:
                        pass  # 忽略关闭异常
    
    async def send_progress(self, user_id: str, progress_data: dict, timeout: float = 3.0):
        """
        向指定用户发送进度数据
        
        Args:
            user_id: 用户ID
            progress_data: 进度数据字典
            timeout: 发送超时时间（秒）
        """
        async with self.lock:
            if user_id not in self.active_connections or not self.active_connections[user_id]:
                return
                
            # 先清理已断开的连接
            active_connections = set()
            for websocket in self.active_connections[user_id].copy():
                try:
                    # 检查连接状态
                    if websocket.client_state.name != 'CONNECTED':
                        self.active_connections[user_id].discard(websocket)
                    else:
                        active_connections.add(websocket)
                except Exception:
                    # 连接已断开或出现异常
                    self.active_connections[user_id].discard(websocket)
            
            if not active_connections:
                # 没有活跃连接，清理用户条目
                if user_id in self.active_connections:
                    del self.active_connections[user_id]
                return
            
            # 为活跃连接创建发送任务
            send_tasks = []
            for websocket in active_connections:
                try:
                    task = asyncio.wait_for(
                        websocket.send_text(json.dumps(progress_data, ensure_ascii=False)),
                        timeout=timeout
                    )
                    send_tasks.append((websocket, task))
                except Exception as e:
                    logger.debug(f"准备发送时连接异常: user_id={user_id}, error={str(e)}")
                    self.active_connections[user_id].discard(websocket)
            
            # 执行发送任务
            if send_tasks:
                try:
                    results = await asyncio.gather(*[task for _, task in send_tasks], return_exceptions=True)
                    failed_count = 0
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            failed_count += 1
                            websocket = send_tasks[i][0]
                            self.active_connections[user_id].discard(websocket)
                            logger.debug(f"WebSocket发送失败: user_id={user_id}, error={str(result)}")
                    
                    # 只有当失败率超过50%时才记录警告
                    if failed_count > 0 and failed_count >= len(send_tasks) * 0.5:
                        logger.warning(f"WebSocket批量发送失败率过高: {failed_count}/{len(send_tasks)} 个任务失败, user_id={user_id}")
                    elif failed_count > 0:
                        logger.debug(f"WebSocket批量发送部分失败: {failed_count}/{len(send_tasks)} 个任务失败, user_id={user_id}")
                        
                except Exception as e:
                    logger.error(f"WebSocket批量发送时发生严重错误: {e}")
                    
            # 最终清理：如果用户没有任何连接了，移除用户条目
            if user_id in self.active_connections and not self.active_connections[user_id]:
                del self.active_connections[user_id]

connection_manager = ConnectionManager()


@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """
    WebSocket进度通知端点
    
    Args:
        websocket: WebSocket连接
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：为WebSocket连接实现独立的认证机制，避免与HTTP认证依赖冲突
    # - 已知局限：增加了认证复杂度，但解决了WebSocket依赖注入问题
    # - 业务背景：修复WebSocket连接的TypeError异常
    # - 测试重点：请验证WebSocket连接建立、认证、消息处理流程
    # -->
    
    await websocket.accept()
    
    try:
        # 等待客户端发送认证消息
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)
        
        if auth_data.get('type') == 'auth' and 'token' in auth_data:
            # 验证token
            token = auth_data['token']
            logger.info(f"收到认证请求，token长度: {len(token)}")
            db_gen = get_db()
            db = next(db_gen)
            try:
                auth_service = AuthService(db)
                user = auth_service.get_current_user(token)
                user_id = str(user.id)
                logger.info(f"认证成功，用户ID: {user_id}")
                
                # 连接认证成功，加入连接管理器（注意：websocket已经accept过了）
                await connection_manager.connect_without_accept(websocket, user_id)
                # 设置user_id属性用于连接清理
                websocket._user_id = user_id
                
                # 发送连接确认消息
                await websocket.send_text(json.dumps({
                    "event": "connected",
                    "user_id": user_id,
                    "timestamp": int(asyncio.get_event_loop().time())
                }))
                
                # 保持连接活跃
                while True:
                    try:
                        message = await websocket.receive_text()
                        # 处理客户端消息（如果需要）
                        await websocket.send_text(json.dumps({
                            "event": "pong",
                            "message": message,
                            "timestamp": int(asyncio.get_event_loop().time())
                        }))
                    except Exception:
                        # 客户端断开连接
                        break
                        
            except Exception as e:
                # 认证失败
                logger.error(f"认证失败: {str(e)}")
                await websocket.send_text(json.dumps({
                    "event": "auth_failed",
                    "error": str(e),
                    "timestamp": int(asyncio.get_event_loop().time())
                }))
                await websocket.close()
            finally:
                db_gen.close()
        else:
            # 无效的认证消息格式
            await websocket.send_text(json.dumps({
                "event": "auth_required",
                "error": "Invalid authentication message format",
                "timestamp": int(asyncio.get_event_loop().time())
            }))
            await websocket.close()
            
    except Exception as e:
        logger.error(f"WebSocket连接处理异常: {e}")
    finally:
        # 清理连接
        try:
            # 尝试从websocket对象中获取user_id（如果之前已设置）
            user_id = getattr(websocket, '_user_id', None)
            if user_id:
                await connection_manager.disconnect(user_id, websocket)
        except Exception as e:
            logger.debug(f"WebSocket连接清理异常: {e}")


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
    
    try:
        service = FileUploadService(db, current_user)
        files, total = service.get_user_files(page, size)
        
        # 添加调试日志
        logger.info(f"用户 {current_user.username}(ID:{current_user.id}) 查询文件列表成功: 找到 {len(files)} 个文件，总计 {total} 个")
        logger.debug(f"返回的文件列表: {[f.original_name for f in files]}")
        
        return FileListResponse(
            total=total,
            files=files,
            page=page,
            size=size
        )
    except Exception as e:
        logger.error(f"查询文件列表时发生错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询文件列表失败: {str(e)}"
        ) from e


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
async def download_file(
    file_id: str,
    background_tasks: BackgroundTasks,
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
    # - 设计意图：实现带队列管理的流式文件下载，控制并发数量避免资源耗尽
    # - 已知局限：使用下载队列限制并发，大文件下载需要排队等待
    # - 业务背景：优化大文件下载体验，防止服务器资源被大量下载请求占用
    # - 测试重点：请验证队列管理、并发控制、下载计数更新、错误处理
    # -->
    
    service = FileUploadService(db, current_user)
    db_file = service.get_file_by_id(file_id)
    
    if not db_file:
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )
    
    # 创建下载任务
    download_task = DownloadTask(
        file_id=file_id,
        user_id=current_user.id,
        file_path=db_file.file_path,
        file_name=db_file.original_name,
        file_size=db_file.file_size,
        priority=0  # 可以根据文件大小或其他因素调整优先级
    )
    
    # 尝试立即开始下载
    if download_queue_manager.start_download(download_task):
        logger.info(f"立即开始下载: {file_id}")
        return await _execute_download(db_file, background_tasks, file_id, db)
    else:
        # 加入队列等待
        if download_queue_manager.add_to_queue(download_task):
            logger.info(f"下载任务加入队列等待: {file_id}")
            # 返回排队状态响应
            from fastapi.responses import JSONResponse
            queue_position = len(download_queue_manager.download_queue)
            return JSONResponse(
                status_code=202,
                content={
                    "message": "下载任务已加入队列",
                    "file_id": file_id,
                    "queue_position": queue_position,
                    "estimated_wait_time": queue_position * 30  # 估算等待时间（秒）
                }
            )
        else:
            raise HTTPException(
                status_code=503,
                detail="下载队列已满，请稍后再试"
            )

async def _execute_download(db_file, background_tasks: BackgroundTasks, file_id: str, db: Session):
    """执行实际的文件下载"""
    
    def iterfile():
        """流式读取文件"""
        try:
            logger.info(f"开始读取文件: {db_file.file_path}")
            with open(db_file.file_path, "rb") as f:
                while chunk := f.read(8192):  # 8KB chunks
                    yield chunk
            logger.info(f"文件读取完成: {db_file.file_path}")
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {db_file.file_path}, 错误: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="文件在磁盘上不存在"
            )
        except PermissionError as e:
            logger.error(f"文件权限错误: {db_file.file_path}, 错误: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="文件访问权限不足"
            )
        except Exception as e:
            logger.error(f"文件读取异常: {db_file.file_path}, 错误: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"文件读取失败: {str(e)}"
            ) from e
    
    try:
        # 增加下载计数
        logger.info(f"准备增加文件 {file_id} 的下载计数")
        db_file.download_count += 1
        db.commit()
        logger.info(f"下载计数更新成功，当前计数: {db_file.download_count}")
        
        # 注册后台任务：下载完成后清理队列
        background_tasks.add_task(download_queue_manager.finish_download, file_id)
        
        # 返回流式响应 - 处理中文文件名编码问题
        logger.info(f"开始流式传输文件: {db_file.original_name}")
        
        # 处理Content-Disposition头部的编码问题
        try:
            # 首先尝试直接使用原始文件名
            content_disposition = f'attachment; filename="{db_file.original_name}"'
            headers = {
                "Content-Disposition": content_disposition
            }
        except UnicodeEncodeError:
            # 如果包含非ASCII字符，使用RFC 5987编码
            import urllib.parse
            encoded_filename = urllib.parse.quote(db_file.original_name, safe='')
            content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
            headers = {
                "Content-Disposition": content_disposition
            }
        
        try:
            response = StreamingResponse(
                iterfile(),
                media_type="application/octet-stream",
                headers=headers
            )
        except UnicodeEncodeError as encoding_error:
            logger.error(f"响应头编码错误: {str(encoding_error)}")
            # 使用安全的ASCII文件名作为后备方案
            safe_filename = ''.join(c if ord(c) < 128 else '_' for c in db_file.original_name)
            if not safe_filename or safe_filename == '_' * len(safe_filename):
                safe_filename = f"file_{db_file.id[:8]}.dat"
            
            headers = {
                "Content-Disposition": f'attachment; filename="{safe_filename}"'
            }
            response = StreamingResponse(
                iterfile(),
                media_type="application/octet-stream",
                headers=headers
            )
        logger.info(f"流式响应创建成功")
        return response
    except Exception as e:
        logger.error(f"文件下载处理失败: {str(e)}", exc_info=True)
        db.rollback()
        # 清理队列中的任务
        download_queue_manager.cancel_download(file_id)
        raise HTTPException(
            status_code=500,
            detail=f"文件下载处理失败: {str(e)}"
        ) from e


@router.get("/queue/status")
def get_download_queue_status():
    """
    获取下载队列状态
    
    Returns:
        队列状态信息
    """
    return download_queue_manager.get_queue_status()


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
