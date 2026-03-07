"""
文件分片下载管理器
支持大文件分片下载和断点续传
"""

import asyncio
import logging
import math
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FileChunk:
    """文件分片信息"""
    chunk_index: int
    start_byte: int
    end_byte: int
    size: int
    checksum: str = ""

@dataclass
class ChunkDownloadTask:
    """分片下载任务"""
    file_id: str
    chunk: FileChunk
    file_path: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ChunkedDownloadManager:
    """分片下载管理器"""
    
    def __init__(self, chunk_size: int = 5 * 1024 * 1024):  # 默认5MB分片
        self.chunk_size = chunk_size
        self.active_chunks: Dict[str, List[ChunkDownloadTask]] = {}
        self.completed_chunks: Dict[str, List[FileChunk]] = {}
        self.max_concurrent_chunks = 4  # 最大并发分片数
        
    def calculate_chunks(self, file_size: int) -> List[FileChunk]:
        """计算文件分片"""
        chunks = []
        num_chunks = math.ceil(file_size / self.chunk_size)
        
        for i in range(num_chunks):
            start_byte = i * self.chunk_size
            end_byte = min((i + 1) * self.chunk_size - 1, file_size - 1)
            chunk_size = end_byte - start_byte + 1
            
            chunk = FileChunk(
                chunk_index=i,
                start_byte=start_byte,
                end_byte=end_byte,
                size=chunk_size
            )
            chunks.append(chunk)
            
        logger.info(f"文件分片计算完成: 总大小 {file_size} bytes, 分片数 {len(chunks)}")
        return chunks
    
    def get_file_checksum(self, file_path: str, start_byte: int, end_byte: int) -> str:
        """计算文件分片的MD5校验和"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                f.seek(start_byte)
                remaining = end_byte - start_byte + 1
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    hasher.update(data)
                    remaining -= len(data)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"计算分片校验和失败: {str(e)}")
            return ""
    
    def verify_chunk(self, file_path: str, chunk: FileChunk) -> bool:
        """验证分片完整性"""
        if not chunk.checksum:
            return True  # 没有校验和时不验证
            
        actual_checksum = self.get_file_checksum(file_path, chunk.start_byte, chunk.end_byte)
        return actual_checksum == chunk.checksum
    
    async def download_chunk(self, task: ChunkDownloadTask) -> bool:
        """下载单个分片"""
        try:
            file_path = Path(task.file_path)
            if not file_path.exists():
                logger.error(f"文件不存在: {task.file_path}")
                return False
                
            # 读取分片数据
            with open(file_path, 'rb') as f:
                f.seek(task.chunk.start_byte)
                data = f.read(task.chunk.size)
                
            # 这里应该是实际的网络传输逻辑
            # 为了演示，我们只是模拟下载过程
            await asyncio.sleep(0.1)  # 模拟网络延迟
            
            logger.info(f"分片下载完成: 索引 {task.chunk.chunk_index}, 大小 {task.chunk.size}")
            return True
            
        except Exception as e:
            logger.error(f"分片下载失败: {str(e)}")
            return False
    
    def create_download_session(self, file_id: str, file_path: str, file_size: int) -> Dict:
        """创建下载会话"""
        chunks = self.calculate_chunks(file_size)
        
        # 为每个分片创建任务
        tasks = []
        for chunk in chunks:
            task = ChunkDownloadTask(
                file_id=file_id,
                chunk=chunk,
                file_path=file_path
            )
            tasks.append(task)
            
        self.active_chunks[file_id] = tasks
        self.completed_chunks[file_id] = []
        
        return {
            "file_id": file_id,
            "total_chunks": len(chunks),
            "chunk_size": self.chunk_size,
            "file_size": file_size,
            "chunks": [
                {
                    "index": chunk.chunk_index,
                    "start_byte": chunk.start_byte,
                    "end_byte": chunk.end_byte,
                    "size": chunk.size
                }
                for chunk in chunks
            ]
        }
    
    def get_next_chunk(self, file_id: str) -> Optional[ChunkDownloadTask]:
        """获取下一个待下载的分片"""
        if file_id not in self.active_chunks:
            return None
            
        tasks = self.active_chunks[file_id]
        if not tasks:
            return None
            
        # 返回第一个任务
        return tasks[0]
    
    def complete_chunk(self, file_id: str, chunk_index: int):
        """标记分片下载完成"""
        if file_id not in self.active_chunks:
            return
            
        # 移除已完成的任务
        tasks = self.active_chunks[file_id]
        completed_task = None
        
        for i, task in enumerate(tasks):
            if task.chunk.chunk_index == chunk_index:
                completed_task = tasks.pop(i)
                break
                
        if completed_task:
            self.completed_chunks[file_id].append(completed_task.chunk)
            logger.info(f"分片标记完成: 文件 {file_id}, 分片 {chunk_index}")
    
    def get_download_progress(self, file_id: str) -> Dict:
        """获取下载进度"""
        if file_id not in self.active_chunks:
            return {"completed": True, "progress": 100}
            
        total_chunks = len(self.active_chunks[file_id]) + len(self.completed_chunks.get(file_id, []))
        completed_chunks = len(self.completed_chunks.get(file_id, []))
        
        if total_chunks == 0:
            progress = 100
        else:
            progress = int((completed_chunks / total_chunks) * 100)
            
        return {
            "completed": len(self.active_chunks[file_id]) == 0,
            "progress": progress,
            "completed_chunks": completed_chunks,
            "total_chunks": total_chunks,
            "remaining_chunks": len(self.active_chunks[file_id])
        }
    
    def cancel_download(self, file_id: str):
        """取消下载"""
        if file_id in self.active_chunks:
            del self.active_chunks[file_id]
        if file_id in self.completed_chunks:
            del self.completed_chunks[file_id]
        logger.info(f"下载已取消: {file_id}")

# 全局分片下载管理器实例
chunked_download_manager = ChunkedDownloadManager(chunk_size=5 * 1024 * 1024)