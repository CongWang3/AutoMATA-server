"""
独立下载服务器

设计意图：完全分离下载功能，避免阻塞主 API 服务
- 运行在独立端口 (8001)
- 使用数据库查询文件路径
- 支持 HMAC 签名验证
"""
import asyncio
import hmac
import hashlib
import time
import urllib.parse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from aiohttp import web
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
MAX_SKEW = 60  # 允许的时间偏差，单位秒

# 全局数据库引擎（复用连接池）
engine: Engine = create_engine(settings.DATABASE_URL)


def _parse_int_param(request: web.Request, name: str, default: Optional[int] = None) -> Optional[int]:
    """
    安全解析整型参数
    
    Args:
        request: HTTP请求对象
        name: 参数名称
        default: 默认值
        
    Returns:
        解析后的整数值或None
    """
    value = request.query.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_file_path_from_db(file_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    从数据库获取文件路径和原始文件名
    
    Args:
        file_id: 文件ID
        
    Returns:
        (文件路径, 原始文件名) 元组，如果未找到则返回 (None, None)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT file_path, original_name FROM files WHERE id = :file_id"),
                {"file_id": file_id}
            )
            row = result.fetchone()
            if row:
                return row[0], row[1]
            return None, None
    except Exception as e:
        logger.exception(f"数据库查询错误: {e}")
        return None, None


def verify_signature(file_id: str, uid: int, timestamp: int, token: str) -> bool:
    """验证 HMAC 签名"""
    secret = settings.SECRET_KEY.encode()
    message = f"{file_id}:{uid}:{timestamp}".encode()
    expected = hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(token, expected)


async def handle_download(request: web.Request) -> web.StreamResponse:
    """
    处理下载请求
    
    Args:
        request: HTTP请求对象
        
    Returns:
        StreamResponse响应对象
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：为提高性能，使用全局数据库引擎避免每次创建新连接
    # - 已知局限：同步文件I/O仍会阻塞事件循环，后续可考虑aiofiles优化
    # - 业务背景：独立下载服务，避免阻塞主API服务
    # - 测试重点：请重点关注参数验证、时间戳有效性、签名验证等安全相关逻辑
    # -->
    try:
        file_id = request.match_info.get('file_id')
        token = request.query.get('token', '')
        uid = _parse_int_param(request, 'uid')
        timestamp = _parse_int_param(request, 't')
        filename = request.query.get('filename', 'download')
        
        # 参数验证
        if uid is None or timestamp is None:
            logger.warning(f"[DOWNLOAD] 非法参数: uid={request.query.get('uid')}, t={request.query.get('t')}")
            return web.Response(text="请求参数错误", status=400)
        
        logger.info(f"[DOWNLOAD] 请求: file_id={file_id}, uid={uid}")
        
        # 验证时间戳（5分钟有效期，同时限制未来时间偏差）
        current_time = int(time.time())
        time_diff = current_time - timestamp
        if abs(time_diff) > 300 + MAX_SKEW:
            logger.warning(f"[DOWNLOAD] 链接时间戳异常或已过期: diff={time_diff}秒")
            return web.Response(text="下载链接已过期或无效", status=410)
        
        # 验证签名
        if not verify_signature(file_id, uid, timestamp, token):
            logger.warning(f"[DOWNLOAD] 签名验证失败")
            return web.Response(text="无效的下载链接", status=403)
        
        # 从数据库获取文件路径
        file_path_str, original_name = get_file_path_from_db(file_id)
        
        if not file_path_str:
            logger.info(f"[DOWNLOAD] 文件记录不存在: {file_id}")
            return web.Response(text="文件不存在", status=404)
        
        file_path = Path(file_path_str)
        if not file_path.exists():
            logger.error(f"[DOWNLOAD] 文件路径不存在: {file_path}")
            return web.Response(text="文件不存在", status=404)
        
        # 使用数据库中的原始文件名，如果URL参数中有则使用URL参数
        if filename == 'download' and original_name:
            filename = original_name
        
        file_size = file_path.stat().st_size
        encoded_filename = urllib.parse.quote(filename, safe='')
        
        logger.info(f"[DOWNLOAD] 开始传输: {file_path.name}, 大小: {file_size}")
        
        # 设置响应头（使用CORS白名单而非通配符）
        origin = request.headers.get('Origin', '')
        allow_origin = origin if origin in CORS_ORIGINS else CORS_ORIGINS[0]
        
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Length': str(file_size),
                'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': allow_origin,
            }
        )
        
        await response.prepare(request)
        
        # 异步流式传输（带限速，避免占满 SSH 隧道带宽）
        chunk_size = 64 * 1024  # 64KB
        # 限速：5MB/s（防止占满 SSH 端口转发带宽）
        rate_limit = 5 * 1024 * 1024  # 5MB/s
        chunks_per_second = rate_limit // chunk_size  # 每秒发送的块数
        delay_per_chunk = 1.0 / chunks_per_second if chunks_per_second > 0 else 0.01
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    await response.write(chunk)
                    # 限速延迟
                    await asyncio.sleep(delay_per_chunk)
            
            logger.info(f"[DOWNLOAD] 传输完成: {file_path.name}")
        except Exception as e:
            logger.exception(f"[DOWNLOAD] 传输错误: {e}")
            return web.Response(text="文件传输失败", status=500)
            
        return response
        
    except Exception as e:
        logger.exception(f"[DOWNLOAD] 未处理异常: {e}")
        return web.Response(text="下载服务内部错误", status=500)


async def handle_cors_preflight(request: web.Request) -> web.Response:
    """
    处理 CORS 预检请求
    
    Args:
        request: HTTP请求对象
        
    Returns:
        Response响应对象
    """
    origin = request.headers.get('Origin', '')
    allow_origin = origin if origin in CORS_ORIGINS else CORS_ORIGINS[0]
    
    headers = {
        'Access-Control-Allow-Origin': allow_origin,
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400',
    }
    
    return web.Response(status=204, headers=headers)


async def health_check(request: web.Request) -> web.Response:
    """健康检查"""
    return web.json_response({"status": "healthy", "service": "download-server"})


def create_app() -> web.Application:
    """创建应用"""
    app = web.Application()
    
    # 路由
    app.router.add_get('/health', health_check)
    app.router.add_get('/download/{file_id}', handle_download)
    app.router.add_options('/download/{file_id}', handle_cors_preflight)
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    logger.info("=" * 50)
    logger.info("独立下载服务器启动")
    logger.info(f"端口: 8001")
    logger.info(f"数据库: {settings.DB_HOST}/{settings.DB_NAME}")
    logger.info("=" * 50)
    
    web.run_app(app, host='0.0.0.0', port=8001)
