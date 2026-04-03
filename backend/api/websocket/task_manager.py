"""
任务状态 WebSocket 服务
提供实时任务状态推送功能
"""
import json
import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict, Set, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# #region debug ndjson logging
DEBUG_LOG_PATH = "/xp/www/.cursor/debug-7c3296.log"
DEBUG_SESSION_ID = "7c3296"

def _dbg_append_ndjson(
    hypothesis_id: str,
    location: str,
    message: str,
    data: Optional[Dict] = None,
    run_id: str = "pre-fix",
) -> None:
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
        "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
    }
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion

class TaskStatusManager:
    """任务状态 WebSocket 连接管理器"""
    
    def __init__(self):
        # 存储每个用户的任务状态 WebSocket 连接
        self.task_connections: defaultdict[str, Set[WebSocket]] = defaultdict(set)
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        建立任务状态 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
            user_id: 用户ID
        """
        # 注意：WebSocket 已在路由中 accept，这里不再重复 accept
        async with self.lock:
            self.task_connections[user_id].add(websocket)
            logger.info(f"[Task WS] 用户 {user_id} 建立任务状态连接")
    
    async def disconnect(self, user_id: str, websocket: WebSocket = None):
        """
        断开任务状态 WebSocket 连接
        
        Args:
            user_id: 用户ID
            websocket: 特定的 WebSocket 连接（可选）
        """
        async with self.lock:
            if websocket and user_id in self.task_connections:
                self.task_connections[user_id].discard(websocket)
                if not self.task_connections[user_id]:
                    del self.task_connections[user_id]
            elif user_id in self.task_connections:
                # 清理用户的所有连接
                connections_to_close = list(self.task_connections[user_id])
                del self.task_connections[user_id]
                for ws in connections_to_close:
                    try:
                        if hasattr(ws, 'client_state') and ws.client_state.name == 'CONNECTED':
                            await ws.close()
                    except Exception:
                        pass  # 忽略关闭异常
    
    async def send_task_status(self, user_id: str, task_data: dict, timeout: float = 3.0):
        """
        向指定用户发送任务状态更新
        
        Args:
            user_id: 用户ID
            task_data: 任务状态数据
            timeout: 发送超时时间（秒）
        """
        # <!-- 
        # 审查上下文：
        # - 设计意图：实现实时任务状态推送，替代轮询机制，提高系统效率
        # - 已知局限：使用内存存储连接信息，集群部署时需要考虑分布式方案
        # - 业务背景：为数据处理任务提供实时状态更新功能
        # - 测试重点：连接管理、消息广播、异常处理、资源清理
        # -->
        
        async with self.lock:
            status = (task_data or {}).get("status")
            should_log = status in ("Completed", "Failed")
            if should_log:
                _dbg_append_ndjson(
                    hypothesis_id="H3_ws_send_completed_or_failed",
                    location="task_manager.py:send_task_status:entry",
                    message="send_task_status called",
                    data={"user_id": user_id, "job_id": (task_data or {}).get("job_id"), "status": status},
                    run_id="pre-fix",
                )
            if user_id not in self.task_connections or not self.task_connections[user_id]:
                if should_log:
                    _dbg_append_ndjson(
                        hypothesis_id="H3_ws_send_completed_or_failed",
                        location="task_manager.py:send_task_status:no_connections",
                        message="no active WS connections for user",
                        data={"user_id": user_id, "job_id": (task_data or {}).get("job_id"), "status": status},
                        run_id="pre-fix",
                    )
                logger.debug(f"[Task WS] 用户 {user_id} 没有活跃的任务状态连接")
                return
            
            # 清理已断开的连接
            active_connections = set()
            for websocket in self.task_connections[user_id].copy():
                try:
                    if websocket.client_state.name != 'CONNECTED':
                        self.task_connections[user_id].discard(websocket)
                    else:
                        active_connections.add(websocket)
                except Exception:
                    self.task_connections[user_id].discard(websocket)
            
            if not active_connections:
                if user_id in self.task_connections:
                    del self.task_connections[user_id]
                return
            
            # 为活跃连接创建发送任务
            send_tasks = []
            message_data = {
                "event": "task_status",
                "data": task_data,
                "timestamp": int(asyncio.get_event_loop().time())
            }
            
            for websocket in active_connections:
                try:
                    task = asyncio.wait_for(
                        websocket.send_text(json.dumps(message_data, ensure_ascii=False)),
                        timeout=timeout
                    )
                    send_tasks.append((websocket, task))
                except Exception as e:
                    logger.debug(f"[Task WS] 准备发送时连接异常: user_id={user_id}, error={str(e)}")
                    self.task_connections[user_id].discard(websocket)
            
            # 执行发送任务
            if send_tasks:
                try:
                    results = await asyncio.gather(
                        *[task for _, task in send_tasks], 
                        return_exceptions=True
                    )
                    failed_count = 0
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            failed_count += 1
                            websocket = send_tasks[i][0]
                            self.task_connections[user_id].discard(websocket)
                            logger.debug(f"[Task WS] 发送失败: user_id={user_id}, error={str(result)}")
                    
                    if failed_count > 0:
                        logger.debug(f"[Task WS] 部分发送失败: {failed_count}/{len(send_tasks)}, user_id={user_id}")
                    
                    if should_log:
                        _dbg_append_ndjson(
                            hypothesis_id="H3_ws_send_completed_or_failed",
                            location="task_manager.py:send_task_status:after_send",
                            message="WS batch send finished",
                            data={
                                "user_id": user_id,
                                "job_id": (task_data or {}).get("job_id"),
                                "status": status,
                                "active_connections_count": len(active_connections),
                                "failed_count": failed_count,
                                "send_tasks_count": len(send_tasks),
                            },
                            run_id="pre-fix",
                        )
                        
                except Exception as e:
                    logger.error(f"[Task WS] 批量发送时发生严重错误: {e}")
            
            # 最终清理
            if user_id in self.task_connections and not self.task_connections[user_id]:
                del self.task_connections[user_id]
                logger.info(f"[Task WS] 用户 {user_id} 的所有任务状态连接已清理")

# 全局任务状态管理器实例
task_status_manager = TaskStatusManager()
