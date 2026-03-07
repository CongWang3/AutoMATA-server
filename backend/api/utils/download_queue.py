"""
文件下载队列管理器
用于控制大文件下载的并发数量，避免服务器资源耗尽
"""

import asyncio
import logging
from collections import deque
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class DownloadTask:
    """下载任务数据结构"""
    file_id: str
    user_id: int
    file_path: str
    file_name: str
    file_size: int
    priority: int = 0  # 优先级，数字越大优先级越高
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class DownloadQueueManager:
    """下载队列管理器"""
    
    def __init__(self, max_concurrent: int = 3, max_queue_size: int = 20):
        self.max_concurrent = max_concurrent  # 最大并发下载数
        self.max_queue_size = max_queue_size  # 队列最大长度
        self.active_downloads: Dict[str, DownloadTask] = {}  # 正在下载的任务
        self.download_queue: deque = deque()  # 等待队列
        self.user_download_counts: Dict[int, int] = {}  # 每个用户的下载计数
        self.max_user_concurrent = 2  # 每个用户最大并发下载数
        
    def can_start_download(self, user_id: int) -> bool:
        """检查是否可以开始新的下载"""
        # 检查总体并发限制
        if len(self.active_downloads) >= self.max_concurrent:
            return False
            
        # 检查用户并发限制
        user_active = self.user_download_counts.get(user_id, 0)
        if user_active >= self.max_user_concurrent:
            return False
            
        return True
    
    def add_to_queue(self, task: DownloadTask) -> bool:
        """添加下载任务到队列"""
        # 检查队列是否已满
        if len(self.download_queue) >= self.max_queue_size:
            logger.warning(f"下载队列已满，拒绝任务: {task.file_id}")
            return False
            
        # 检查是否已在队列中
        if any(t.file_id == task.file_id for t in self.download_queue):
            logger.info(f"任务已在队列中: {task.file_id}")
            return True
            
        # 按优先级插入队列
        inserted = False
        for i, existing_task in enumerate(self.download_queue):
            if task.priority > existing_task.priority:
                self.download_queue.insert(i, task)
                inserted = True
                break
                
        if not inserted:
            self.download_queue.append(task)
            
        logger.info(f"任务加入队列: {task.file_id}, 优先级: {task.priority}, 队列长度: {len(self.download_queue)}")
        return True
    
    def start_download(self, task: DownloadTask) -> bool:
        """开始下载任务"""
        if not self.can_start_download(task.user_id):
            return False
            
        # 更新计数器
        self.active_downloads[task.file_id] = task
        self.user_download_counts[task.user_id] = self.user_download_counts.get(task.user_id, 0) + 1
        
        logger.info(f"开始下载: {task.file_id}, 当前活跃下载: {len(self.active_downloads)}, "
                   f"用户 {task.user_id} 的并发数: {self.user_download_counts[task.user_id]}")
        return True
    
    def finish_download(self, file_id: str):
        """完成下载任务"""
        if file_id in self.active_downloads:
            task = self.active_downloads.pop(file_id)
            user_id = task.user_id
            
            # 更新用户计数
            if user_id in self.user_download_counts:
                self.user_download_counts[user_id] -= 1
                if self.user_download_counts[user_id] <= 0:
                    del self.user_download_counts[user_id]
            
            logger.info(f"下载完成: {file_id}, 剩余活跃下载: {len(self.active_downloads)}")
            
            # 尝试启动队列中的下一个任务
            self._process_queue()
    
    def cancel_download(self, file_id: str):
        """取消下载任务"""
        # 从活跃下载中移除
        if file_id in self.active_downloads:
            task = self.active_downloads.pop(file_id)
            user_id = task.user_id
            if user_id in self.user_download_counts:
                self.user_download_counts[user_id] -= 1
                if self.user_download_counts[user_id] <= 0:
                    del self.user_download_counts[user_id]
            logger.info(f"取消活跃下载: {file_id}")
        
        # 从队列中移除
        self.download_queue = deque([t for t in self.download_queue if t.file_id != file_id])
        logger.info(f"取消队列中的下载任务: {file_id}")
    
    def _process_queue(self):
        """处理队列中的等待任务"""
        while self.download_queue and len(self.active_downloads) < self.max_concurrent:
            # 找到可以开始下载的任务
            task_to_start = None
            remaining_tasks = deque()
            
            while self.download_queue:
                task = self.download_queue.popleft()
                if self.can_start_download(task.user_id):
                    task_to_start = task
                    break
                else:
                    remaining_tasks.append(task)
            
            # 将不能立即执行的任务放回队列前面
            while remaining_tasks:
                self.download_queue.appendleft(remaining_tasks.pop())
            
            if task_to_start:
                if self.start_download(task_to_start):
                    logger.info(f"从队列启动下载: {task_to_start.file_id}")
                else:
                    # 如果启动失败，重新放入队列
                    self.download_queue.appendleft(task_to_start)
                    break
            else:
                break
    
    def get_queue_status(self) -> Dict:
        """获取队列状态信息"""
        return {
            "active_count": len(self.active_downloads),
            "queue_length": len(self.download_queue),
            "max_concurrent": self.max_concurrent,
            "user_downloads": dict(self.user_download_counts),
            "active_tasks": [
                {
                    "file_id": task.file_id,
                    "user_id": task.user_id,
                    "file_name": task.file_name,
                    "file_size": task.file_size,
                    "started_at": task.created_at.isoformat()
                }
                for task in self.active_downloads.values()
            ],
            "queued_tasks": [
                {
                    "file_id": task.file_id,
                    "user_id": task.user_id,
                    "file_name": task.file_name,
                    "file_size": task.file_size,
                    "priority": task.priority,
                    "queued_at": task.created_at.isoformat()
                }
                for task in list(self.download_queue)[:5]  # 只返回前5个排队任务
            ]
        }

# 全局下载队列管理器实例
download_queue_manager = DownloadQueueManager(max_concurrent=3, max_queue_size=20)