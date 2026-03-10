"""
任务状态 WebSocket 路由
处理任务状态的实时推送连接
"""
from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.orm import Session
import json
import asyncio
import logging

from config.database import get_db
from api.dependencies.auth import get_current_user_from_websocket
from api.websocket.task_manager import task_status_manager
from api.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["任务状态"])

@router.websocket("/ws/status")
async def task_status_websocket(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    任务状态 WebSocket 连接端点
    
    客户端需要发送认证消息格式：
    {
        "type": "auth",
        "token": "your_jwt_token"
    }
    
    服务端会推送任务状态更新消息格式：
    {
        "event": "task_status",
        "data": {
            "job_id": "任务ID",
            "status": "任务状态",
            "progress": 进度百分比,
            "result_file": "结果文件路径",
            "error_message": "错误信息",
            "created_at": "创建时间",
            "updated_at": "更新时间"
        },
        "timestamp": 时间戳
    }
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供任务状态的实时 WebSocket 推送，替代轮询机制
    # - 已知局限：单节点部署适用，集群环境需要考虑消息广播
    # - 业务背景：与现有的文件上传 WebSocket 共享认证机制
    # - 测试重点：连接认证、消息格式、连接管理、异常处理
    # -->
    
    try:
        # 首先接受WebSocket连接
        await websocket.accept()
        logger.info("[Task WS] WebSocket连接已接受")
        
        # 等待客户端发送认证消息
        try:
            logger.info("[Task WS] 等待任务状态连接的认证消息...")
            auth_message = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=30.0  # 30秒超时
            )
            logger.info(f"[Task WS] 收到认证消息: {auth_message[:100]}...")
        except asyncio.TimeoutError:
            logger.warning("[Task WS] 等待认证消息超时")
            await websocket.close(code=4002, reason="Authentication timeout")
            return
        
        auth_data = json.loads(auth_message)
        
        if auth_data.get('type') == 'auth' and 'token' in auth_data:
            # 验证token
            token = auth_data['token']
            logger.info(f"[Task WS] 收到认证请求，token长度: {len(token)}")
            
            try:
                # 验证用户身份
                user = get_current_user_from_websocket(token, db)
                user_id = str(user.id)
                logger.info(f"[Task WS] 认证成功，用户ID: {user_id}")
                
                # 连接认证成功，加入任务状态管理器
                await task_status_manager.connect(websocket, user_id)
                websocket._user_id = user_id  # 设置用户ID属性用于连接清理
                
                # 发送连接确认消息
                await websocket.send_text(json.dumps({
                    "event": "connected",
                    "user_id": user_id,
                    "message": "任务状态 WebSocket 连接已建立",
                    "timestamp": int(asyncio.get_event_loop().time())
                }, ensure_ascii=False))
                
                # 保持连接活跃，等待客户端断开
                while True:
                    try:
                        # 接收客户端心跳或其他消息（可选）
                        message = await websocket.receive_text()
                        logger.debug(f"[Task WS] 收到来自用户 {user_id} 的消息: {message}")
                        
                        # 回复心跳确认
                        await websocket.send_text(json.dumps({
                            "event": "pong",
                            "message": "alive",
                            "timestamp": int(asyncio.get_event_loop().time())
                        }, ensure_ascii=False))
                        
                    except Exception as e:
                        logger.info(f"[Task WS] 用户 {user_id} 断开连接: {str(e)}")
                        break
                        
            except Exception as e:
                # 认证失败
                logger.error(f"[Task WS] 认证失败: {str(e)}")
                await websocket.send_text(json.dumps({
                    "event": "auth_failed",
                    "error": str(e),
                    "timestamp": int(asyncio.get_event_loop().time())
                }, ensure_ascii=False))
                await websocket.close(code=4001, reason="Authentication failed")
                
        else:
            # 无效的认证消息格式
            logger.warning("[Task WS] 无效的认证消息格式")
            await websocket.send_text(json.dumps({
                "event": "auth_required",
                "error": "Invalid authentication message format",
                "timestamp": int(asyncio.get_event_loop().time())
            }, ensure_ascii=False))
            await websocket.close(code=4000, reason="Invalid authentication format")
            
    except Exception as e:
        logger.error(f"[Task WS] WebSocket连接处理异常: {e}")
    finally:
        # 清理连接
        try:
            user_id = getattr(websocket, '_user_id', None)
            if user_id:
                await task_status_manager.disconnect(user_id, websocket)
                logger.info(f"[Task WS] 用户 {user_id} 的任务状态连接已清理")
        except Exception as e:
            logger.debug(f"[Task WS] 连接清理异常: {e}")
