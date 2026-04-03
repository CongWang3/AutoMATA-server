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
import os
import tempfile
import time
import urllib.parse
import json
import logging
import sys
import zipfile
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


def _download_cors_allow_origin(request: web.Request) -> str:
    """与 FastAPI settings.CORS_ORIGINS 对齐；含 * 时回显请求的 Origin。"""
    origin = request.headers.get("Origin") or request.headers.get("origin") or ""
    origins = list(settings.CORS_ORIGINS)
    if "*" in origins:
        return origin or "*"
    if origin in origins:
        return origin
    return origins[0] if origins else "*"


# 配置
MAX_SKEW = 60  # 允许的时间偏差，单位秒

# 下载限速（字节/秒）：0 表示不限速。默认不限速，避免大 zip 传输过久触发浏览器「无法完成下载」。
# 需要模拟弱网时可设置环境变量，例如：export DOWNLOAD_THROTTLE_BPS=5242880  （约 5MB/s）
DOWNLOAD_THROTTLE_BPS = int(os.environ.get("DOWNLOAD_THROTTLE_BPS", "0"))



# #endregion


async def _throttle_after_chunk(chunk_len: int) -> None:
    """按 DOWNLOAD_THROTTLE_BPS 在每次写出后休眠；chunk_len 为本次写入字节数。"""
    if DOWNLOAD_THROTTLE_BPS <= 0 or chunk_len <= 0:
        return
    await asyncio.sleep(chunk_len / DOWNLOAD_THROTTLE_BPS)


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

    allow_origin = _download_cors_allow_origin(request)

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


# ----- 以下为任务结果下载扩展：result.zip / result 目录（仅新增，不改动上方原有函数） -----

JOBS_DOWNLOAD_ROOT = settings.path_jobs


def fetch_job_result_file_field_for_user(job_id: str, uid: int) -> Tuple[bool, Optional[str]]:
    """
    查询任务是否属于该用户，并返回 result_file 列（可为 NULL）。

    Returns:
        (row_found, result_file)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT result_file FROM jobs WHERE job_id = :job_id AND user_id = :uid"),
                {"job_id": job_id, "uid": uid},
            )
            row = result.fetchone()
            if not row:
                return False, None
            return True, row[0]
    except Exception as e:
        logger.exception(f"数据库查询错误（fetch_job_result_file_field_for_user）：{e}")
        return False, None


def _path_under_jobs_download_root(path: Path, root: Path = JOBS_DOWNLOAD_ROOT) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


# result 目录打包进 result.zip 时允许的后缀（仅打包实际存在的文件；无 pkl 则 zip 中也不会有）
_RESULT_ZIP_SUFFIXES = frozenset({".png", ".txt", ".log", ".pth", ".pkl"})


def zip_result_directory_for_export(result_dir: Path, zip_path: Path) -> None:
    """
    将目录下指定类型文件（递归，大小写不敏感）打入 zip_path。
    类型：png、txt、log、pth、pkl；目录中不存在的扩展名自然不会出现。
    """
    result_dir = result_dir.resolve()
    zip_path = zip_path.resolve()
    parent = zip_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(suffix=".zip", dir=str(parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in result_dir.rglob("*"):
                if not file.is_file():
                    continue
                if file.suffix.lower() not in _RESULT_ZIP_SUFFIXES:
                    continue
                arcname = file.relative_to(result_dir)
                zf.write(file, arcname=str(arcname).replace("\\", "/"))
        os.replace(tmp_path, zip_path)
        logger.info(f"[JOB-RESULT] 已生成 result.zip（含 png/txt/log/pth/pkl）: {zip_path}")
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def resolve_job_result_download_file(job_id: str, result_file_db: Optional[str]) -> Tuple[Optional[Path], str]:
    """
    解析实际要下载的文件：
    1) DB result_file 指向 Jobs 下已存在文件 → 直接使用（分析并训练通常为 model_result.zip）
    2) Jobs/{job_id}/model_result.zip 存在 → 整包优先（Full result package）
    3) Jobs/{job_id}/result.zip 已存在则直接使用
    4) Jobs/{job_id}/result 为目录 → 按 png/txt/log/pth/pkl 规则生成 result.zip 再下载
    5) result_file 指向与 result 相同的目录则同 (4)
    """
    jobs_root = JOBS_DOWNLOAD_ROOT.resolve()
    job_dir = (jobs_root / job_id).resolve()
    if not _path_under_jobs_download_root(job_dir, jobs_root):
        return None, ""

    model_zip = job_dir / "model_result.zip"
    zip_path = job_dir / "result.zip"
    result_dir = job_dir / "result"

    if result_file_db:
        p = Path(str(result_file_db)).expanduser().resolve()
        if _path_under_jobs_download_root(p, jobs_root) and p.is_file():
            return p, p.name

    if model_zip.is_file():
        return model_zip, "model_result.zip"

    if zip_path.is_file():
        return zip_path, "result.zip"

    if result_dir.is_dir():
        zip_result_directory_for_export(result_dir, zip_path)
        if zip_path.is_file():
            return zip_path, "result.zip"

    if result_file_db:
        p = Path(str(result_file_db)).expanduser().resolve()
        if not _path_under_jobs_download_root(p, jobs_root):
            logger.warning(f"[JOB-RESULT] 拒绝 result_file（不在 Jobs 目录下）: {p}")
            return None, ""
        if p.is_dir() and p.resolve() == result_dir.resolve():
            zip_result_directory_for_export(result_dir, zip_path)
            if zip_path.is_file():
                return zip_path, "result.zip"

    return None, ""


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
        file_exists = file_path.exists()
        if not file_exists:
            logger.error(f"[DOWNLOAD] 文件路径不存在: {file_path}")
            return web.Response(text="文件不存在", status=404)
        
        # 使用数据库中的原始文件名，如果URL参数中有则使用URL参数
        if filename == 'download' and original_name:
            filename = original_name
        
        file_size = file_path.stat().st_size
        encoded_filename = urllib.parse.quote(filename, safe='')
        
        logger.info(f"[DOWNLOAD] 开始传输: {file_path.name}, 大小: {file_size}")
        
        # 设置响应头（使用CORS白名单而非通配符）
        allow_origin = _download_cors_allow_origin(request)
        
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
        
        chunk_size = 64 * 1024  # 64KB
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    await response.write(chunk)
                    await _throttle_after_chunk(len(chunk))
            
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

        
        # 验证时间戳有效期（10分钟）
        current_time = int(time.time())
        time_diff = current_time - timestamp
        if abs(time_diff) > 600 + MAX_SKEW:
            logger.warning(f"[JOB-RESULT] 链接时间戳异常或已过期: diff={time_diff}秒")
            return web.Response(text="下载链接已过期或无效", status=410)

        # 验证签名：file_id 复用 job_id（与后端生成逻辑一致）
        sig_ok = verify_signature(job_id, uid, timestamp, token)
        
        if not sig_ok:
            logger.warning(f"[JOB-RESULT] 签名验证失败")
            return web.Response(text="无效的下载链接", status=403)

        row_ok, result_file_field = fetch_job_result_file_field_for_user(job_id, uid)
        
        if not row_ok:
            logger.info(f"[JOB-RESULT] 结果记录不存在: job_id={job_id}, uid={uid}")
            return web.Response(text="结果文件不存在", status=404)

        result_file_path, default_filename = resolve_job_result_download_file(job_id, result_file_field)
        if not result_file_path or not result_file_path.is_file():
            logger.error(f"[JOB-RESULT] 无法解析可下载文件: job_id={job_id}")
            return web.Response(text="结果文件不存在", status=404)

        final_filename = filename or default_filename or result_file_path.name

        file_size = result_file_path.stat().st_size
        encoded_filename = urllib.parse.quote(final_filename, safe="")

        allow_origin = _download_cors_allow_origin(request)

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

        chunk_size = 64 * 1024
        with open(result_file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                await response.write(chunk)
                await _throttle_after_chunk(len(chunk))

        logger.info(f"[JOB-RESULT] 传输完成: {result_file_path}")
        return response

    except Exception as e:
        logger.exception(f"[JOB-RESULT] 下载服务内部错误: {e}")
        return web.Response(text="下载服务内部错误", status=500)


def _normalize_db_job_type(raw) -> str:
    """MySQL ENUM / 驱动可能返回 str、bytes 或与 Python 枚举不完全一致的值。"""
    if raw is None:
        return ""
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8", errors="replace")
        except Exception:
            return ""
    return str(raw).strip().lower()


def _try_result_dir_file(result_dir: Path, safe_name: str) -> Tuple[Optional[Path], Optional[str]]:
    """在已解析的 result 目录下取单个文件（防路径穿越）。"""
    try:
        result_dir = result_dir.resolve()
    except Exception:
        return None, None
    if not result_dir.is_dir():
        return None, None
    target = (result_dir / safe_name).resolve()
    if target.parent != result_dir:
        return None, None
    if not target.is_file():
        return None, None
    return target, safe_name


def _resolve_analysis_result_file(job_id: str, filename: str) -> Tuple[Optional[Path], Optional[str]]:
    """
    解析结果目录下的单个文件路径，供 GET /analysis-result 使用。
    - data_analysis：result_file 为目录（或单文件，与旧逻辑一致）
    - analysis_train：Jobs/<job_id>/result/（与 AnalysisService / analysis_train 流水线一致）
    - 兜底：若 DB 中 job_type 与约定不一致（例如 ENUM 未迁移），仍尝试标准 result 目录或 zip 同级的 result/
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
                    "SELECT job_type, result_file FROM jobs WHERE job_id = :job_id"
                ),
                {"job_id": job_id},
            ).fetchone()
        if not row:
            logger.info(f"[ANALYSIS-RESULT] 无此 job_id: {job_id}")
            
            return None, None
        job_type, result_file = row[0], row[1]
        jt = _normalize_db_job_type(job_type)

        if jt == "analysis_train":
            hit = _try_result_dir_file(JOBS_DOWNLOAD_ROOT / job_id / "result", safe_name)
            if hit[0]:
                return hit
            logger.debug(
                "[ANALYSIS-RESULT] analysis_train 标准目录未命中: job_id=%s file=%s",
                job_id,
                safe_name,
            )

        if jt == "data_analysis":
            if not result_file:
                logger.info(f"[ANALYSIS-RESULT] 结果文件不存在: job_id={job_id}")
                return None, None
            base = Path(str(result_file)).expanduser()
            if base.is_dir():
                hit = _try_result_dir_file(base, safe_name)
                if hit[0]:
                    return hit
            elif base.is_file():
                if safe_name != base.name:
                    return None, None
                return base.resolve(), safe_name

        # analysis_train 但 zip 路径在库中：.../Jobs/<id>/model_result.zip → 同级 result/
        if result_file:
            zip_or_path = Path(str(result_file)).expanduser()
            try:
                zip_or_path = zip_or_path.resolve()
            except Exception:
                zip_or_path = zip_or_path
            if zip_or_path.is_file() and zip_or_path.suffix.lower() == ".zip":
                hit = _try_result_dir_file(zip_or_path.parent / "result", safe_name)
                if hit[0]:
                    return hit

        # 最后兜底：标准 Jobs/<job_id>/result/（避免 job_type ENUM 未含 analysis_train 时整类 404）
        hit = _try_result_dir_file(JOBS_DOWNLOAD_ROOT / job_id / "result", safe_name)
        if hit[0]:
            return hit

        logger.info(
            "[ANALYSIS-RESULT] 未解析到文件 job_id=%s file=%s db_job_type=%r",
            job_id,
            safe_name,
            job_type,
        )
        
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
        
        file_path, out_name = _resolve_analysis_result_file(job_id, filename)
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
        allow_origin = _download_cors_allow_origin(request)

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
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                await response.write(chunk)
                await _throttle_after_chunk(len(chunk))

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
    allow_origin = _download_cors_allow_origin(request)

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
    logger.info(f"端口: {settings.DOWNLOAD_SERVER_PORT}")
    logger.info(f"数据库: {settings.DB_HOST}/{settings.DB_NAME}")
    logger.info("=" * 50)

    web.run_app(app, host=settings.DOWNLOAD_SERVER_HOST, port=settings.DOWNLOAD_SERVER_PORT)
