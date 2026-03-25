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
import json
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

# --- Debug logging (NDJSON) ---
DEBUG_LOG_PATH = "/xp/www/.cursor/debug-d7d881.log"
DEBUG_SESSION_ID = "d7d881"

def _debug_append_ndjson(hypothesis_id: str, location: str, message: str, data: Optional[dict] = None) -> None:
    """Append a single NDJSON line for debug mode."""
    if data is None:
        data = {}
    try:
        payload = {
            "sessionId": DEBUG_SESSION_ID,
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
            "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Never break download flow because of logging.
        return


# 示例文件根目录（用于 /example/{file_path} 下载）
EXAMPLE_DIR = (Path(__file__).resolve().parent.parent / "example").resolve()


async def handle_example_file(request: web.Request) -> web.FileResponse:
    """
    处理示例文件下载（/example/{file_path}）
    - 使用 EXAMPLE_DIR 受控目录
    - 防止路径遍历
    """
    file_path = request.match_info.get("file_path", "")

    try:
        target_path = (EXAMPLE_DIR / file_path).resolve()
    except Exception:
        raise web.HTTPNotFound(text="文件不存在")

    # 防止路径遍历：必须落在 EXAMPLE_DIR 内
    if not (target_path == EXAMPLE_DIR or EXAMPLE_DIR in target_path.parents):
        raise web.HTTPNotFound(text="文件不存在")

    if not target_path.exists() or not target_path.is_file():
        raise web.HTTPNotFound(text="文件不存在")

    origin = request.headers.get("Origin", "")
    allow_origin = origin if origin in CORS_ORIGINS else CORS_ORIGINS[0]

    return web.FileResponse(
        path=str(target_path),
        headers={
            "Content-Disposition": f'attachment; filename="{target_path.name}"',
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": allow_origin,
        },
    )


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


def get_job_result_path_from_db(job_id: str, uid: int) -> Tuple[Optional[str], Optional[str]]:
    """
    从数据库获取训练/数据处理任务结果文件路径

    Returns:
        (result_file_path, default_filename)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT result_file FROM jobs WHERE job_id = :job_id AND user_id = :uid"),
                {"job_id": job_id, "uid": uid},
            )
            row = result.fetchone()
            if not row:
                return None, None

            result_file = row[0]
            if not result_file:
                return None, None

            # 默认文件名：使用磁盘上的文件名（例如 result.zip）
            default_filename = Path(result_file).name
            return str(result_file), default_filename
    except Exception as e:
        logger.exception(f"数据库查询错误（job-result）：{e}")
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
        
        #region agent log
        _debug_append_ndjson(
            hypothesis_id="H6_route_or_param_issue_download",
            location="download_server.py:handle_download:entry",
            message="job download handler entered",
            data={
                "has_file_id": bool(file_id),
                "token_present": bool(token),
                "uid": uid,
                "timestamp": timestamp,
            },
        )
        #endregion
        
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
            #region agent log
            _debug_append_ndjson(
                hypothesis_id="H1_uid_or_fileid_db_mismatch",
                location="download_server.py:handle_download:db_not_found",
                message="file record not found in DB",
                data={"file_id": file_id, "uid": uid, "has_result": False},
            )
            #endregion
            logger.info(f"[DOWNLOAD] 文件记录不存在: {file_id}")
            return web.Response(text="文件不存在", status=404)
        
        file_path = Path(file_path_str)
        file_exists = file_path.exists()
        if not file_exists:
            #region agent log
            _debug_append_ndjson(
                hypothesis_id="H2_missing_file_on_disk",
                location="download_server.py:handle_download:file_missing_on_disk",
                message="file path does not exist on disk",
                data={"file_id": file_id, "uid": uid, "path_name": file_path.name, "exists": False},
            )
            #endregion
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


async def handle_job_result_download(request: web.Request) -> web.StreamResponse:
    """
    处理 job-result 下载请求（与前端训练/数据处理签名链接一致）
    """
    try:
        job_id = request.match_info.get("job_id")
        token = request.query.get("token", "")
        uid = _parse_int_param(request, "uid")
        timestamp = _parse_int_param(request, "t")

        # 可选：前端/调用方可传 filename，但我们以磁盘文件名为主
        filename = request.query.get("filename")

        if not job_id:
            return web.Response(text="请求参数错误", status=400)
        if uid is None or timestamp is None:
            logger.warning(f"[JOB-RESULT] 非法参数: uid={request.query.get('uid')}, t={request.query.get('t')}")
            return web.Response(text="请求参数错误", status=400)

        #region agent log
        _debug_append_ndjson(
            hypothesis_id="H5_db_mismatch",
            location="download_server.py:handle_job_result_download:entry",
            message="job-result handler entered",
            data={
                "job_id": job_id,
                "uid": uid,
                "timestamp": timestamp,
                "token_present": bool(token),
                # Avoid logging full DATABASE_URL (may contain secrets); only host/dbname.
                "db_host": getattr(settings, "DB_HOST", None),
                "db_name": getattr(settings, "DB_NAME", None),
            },
        )
        #endregion

        # 验证时间戳有效期（10分钟）
        current_time = int(time.time())
        time_diff = current_time - timestamp
        if abs(time_diff) > 600 + MAX_SKEW:
            logger.warning(f"[JOB-RESULT] 链接时间戳异常或已过期: diff={time_diff}秒")
            return web.Response(text="下载链接已过期或无效", status=410)

        # 验证签名：file_id 复用 job_id（与后端生成逻辑一致）
        sig_ok = verify_signature(job_id, uid, timestamp, token)
        #region agent log
        _debug_append_ndjson(
            hypothesis_id="H4_signature_validation",
            location="download_server.py:handle_job_result_download:signature_check",
            message="signature verification result",
            data={"job_id": job_id, "uid": uid, "timestamp": timestamp, "sig_ok": sig_ok},
        )
        #endregion
        if not sig_ok:
            logger.warning(f"[JOB-RESULT] 签名验证失败")
            return web.Response(text="无效的下载链接", status=403)

        result_file_path_str, default_filename = get_job_result_path_from_db(job_id, uid)
        #region agent log
        _debug_append_ndjson(
            hypothesis_id="H1_uid_or_jobid_db_mismatch",
            location="download_server.py:handle_job_result_download:db_lookup",
            message="DB lookup for result file",
            data={"job_id": job_id, "uid": uid, "has_result_file_path": bool(result_file_path_str), "default_filename": default_filename},
        )
        #endregion
        if not result_file_path_str:
            logger.info(f"[JOB-RESULT] 结果记录不存在: job_id={job_id}, uid={uid}")
            return web.Response(text="结果文件不存在", status=404)

        result_file_path = Path(result_file_path_str)
        file_exists = result_file_path.exists()
        if not file_exists:
            #region agent log
            _debug_append_ndjson(
                hypothesis_id="H2_missing_file_on_disk",
                location="download_server.py:handle_job_result_download:file_missing_on_disk",
                message="result file path missing on disk",
                data={"job_id": job_id, "uid": uid, "path_name": result_file_path.name, "exists": False},
            )
            #endregion
            logger.error(f"[JOB-RESULT] 文件路径不存在: {result_file_path}")
            return web.Response(text="结果文件不存在", status=404)

        final_filename = filename or default_filename or result_file_path.name

        file_size = result_file_path.stat().st_size
        encoded_filename = urllib.parse.quote(final_filename, safe="")

        origin = request.headers.get("Origin", "")
        allow_origin = origin if origin in CORS_ORIGINS else CORS_ORIGINS[0]

        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(file_size),
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": allow_origin,
            },
        )
        await response.prepare(request)

        # 64KB chunk + 5MB/s 限速
        chunk_size = 64 * 1024
        rate_limit = 5 * 1024 * 1024
        chunks_per_second = rate_limit // chunk_size
        delay_per_chunk = 1.0 / chunks_per_second if chunks_per_second > 0 else 0.01

        with open(result_file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                await response.write(chunk)
                await asyncio.sleep(delay_per_chunk)

        logger.info(f"[JOB-RESULT] 传输完成: {result_file_path}")
        return response

    except Exception as e:
        logger.exception(f"[JOB-RESULT] 下载服务内部错误: {e}")
        return web.Response(text="下载服务内部错误", status=500)


def _resolve_data_analysis_result_file(job_id: str, filename: str) -> Tuple[Optional[Path], Optional[str]]:
    """
    解析数据分析任务结果目录下的单个文件路径.
    - 仅允许 job_type = data_analysis
    - filename 必须为安全文件名（无路径分隔符）
    """
    if not job_id or not filename:
        return None, None
    name = urllib.parse.unquote(filename)
    if ".." in name or "/" in name or "\\" in name:
        return None, None
    safe_name = Path(name).name
    if not safe_name:
        return None, None
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT result_file FROM jobs WHERE job_id = :job_id "
                    "AND job_type = 'data_analysis'"
                ),
                {"job_id": job_id},
            ).fetchone()
        if not row or not row[0]:
            return None, None
        base = Path(row[0])
        if base.is_dir():
            result_dir = base.resolve()
            target = (result_dir / safe_name).resolve()
            if target.parent != result_dir:
                return None, None
            if not target.is_file():
                return None, None
            return target, safe_name
        if base.is_file():
            if safe_name != base.name:
                return None, None
            return base.resolve(), safe_name
        return None, None
    except Exception as e:
        logger.exception(f"[ANALYSIS-RESULT] 解析路径失败: {e}")
        return None, None


async def handle_analysis_result_download(request: web.Request) -> web.StreamResponse:
    """
    GET /analysis-result/{job_id}/{filename}
    供前端直接拉取数据分析产物（与 AnalysisAPI.getResultFileUrl 约定一致）。
    注意：当前实现不包含 uid/token 鉴权，仅适用于内网或后续由网关统一鉴权；
    公网部署请改为签名链接或走主 API。
    """
    try:
        job_id = request.match_info.get("job_id", "")
        filename = request.match_info.get("filename", "")
        file_path, out_name = _resolve_data_analysis_result_file(job_id, filename)
        if not file_path or not out_name:
            return web.Response(text="文件不存在", status=404)

        media_type_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".jpeg": "image/jpeg",
            ".jpg": "image/jpeg",
            ".bmp": "image/bmp",
            ".txt": "text/plain",
        }
        suffix = file_path.suffix.lower()
        content_type = media_type_map.get(suffix, "application/octet-stream")
        inline_types = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".webp"}
        disposition = "inline" if suffix in inline_types else "attachment"

        file_size = file_path.stat().st_size
        encoded_filename = urllib.parse.quote(out_name, safe="")
        origin = request.headers.get("Origin", "")
        allow_origin = origin if origin in CORS_ORIGINS else CORS_ORIGINS[0]

        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": content_type,
                "Content-Length": str(file_size),
                "Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": allow_origin,
            },
        )
        await response.prepare(request)

        chunk_size = 64 * 1024
        rate_limit = 5 * 1024 * 1024
        chunks_per_second = rate_limit // chunk_size
        delay_per_chunk = 1.0 / chunks_per_second if chunks_per_second > 0 else 0.01

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                await response.write(chunk)
                await asyncio.sleep(delay_per_chunk)

        logger.info(f"[ANALYSIS-RESULT] 传输完成: {file_path}")
        return response
    except Exception as e:
        logger.exception(f"[ANALYSIS-RESULT] 下载服务内部错误: {e}")
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
    app.router.add_get('/example/{file_path:.*}', handle_example_file)
    app.router.add_get('/download/{file_id}', handle_download)
    app.router.add_options('/download/{file_id}', handle_cors_preflight)
    app.router.add_get('/job-result/{job_id}', handle_job_result_download)
    app.router.add_options('/job-result/{job_id}', handle_cors_preflight)
    app.router.add_get('/analysis-result/{job_id}/{filename}', handle_analysis_result_download)
    app.router.add_options('/analysis-result/{job_id}/{filename}', handle_cors_preflight)
    return app


if __name__ == '__main__':
    app = create_app()
    
    logger.info("=" * 50)
    logger.info("独立下载服务器启动")
    logger.info(f"端口: 8001")
    logger.info(f"数据库: {settings.DB_HOST}/{settings.DB_NAME}")
    logger.info("=" * 50)
    
    web.run_app(app, host='0.0.0.0', port=8001)
