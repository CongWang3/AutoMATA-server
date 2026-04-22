"""
AI Agent WebSocket 路由
提供 Agent 聊天的 WebSocket 端点
"""
import json
import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from config.database import get_db
from config.settings import settings
from api.dependencies.auth import get_current_user_from_websocket
from api.agent.llm_provider import validate_provider_config
from api.agent.graph import create_agent_graph, run_agent
from api.agent.script_semantics import build_semantic_context, get_semantic_coverage
from api.agent.tools import get_all_tools
from api.models.job import Job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["AI Agent"])


# 存储每个连接的对话历史（内存中）
# 格式: {user_id: {websocket_id: [messages]}}
conversation_histories: Dict[str, Dict[int, List[BaseMessage]]] = {}

# Agent 图实例缓存
# 格式: {provider: compiled_graph}
agent_graphs: Dict[str, any] = {}
JOB_ID_PATTERN = re.compile(r"\b\d{14}_[a-zA-Z0-9]{8}\b")
TRACEBACK_FILE_LINE_RE = re.compile(
    r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>.+?)\s*$'
)
R_ERROR_RE = re.compile(r"^\s*Error(?:\s+in\s+.+?)?:\s*(?P<msg>.+)\s*$", re.IGNORECASE)

# 跳过与平台业务无关的库路径（不尝试读源码窗口）
_SKIP_SNIPPET_SUBSTR = (
    "site-packages",
    "dist-packages",
    "/miniconda/",
    "/anaconda/",
    "lib/python",
    "Lib/python",
)


def _extract_job_id(message: str, explicit_job_id: Optional[str] = None) -> Optional[str]:
    """优先使用前端显式传入 job_id，否则从用户消息中提取。"""
    if explicit_job_id and JOB_ID_PATTERN.fullmatch(str(explicit_job_id).strip()):
        return str(explicit_job_id).strip()
    m = JOB_ID_PATTERN.search(message or "")
    return m.group(0) if m else None


def _read_tail_lines(path: Path, max_lines: int = 200) -> str:
    """读取文本文件最后 N 行（容错）。"""
    if not path.exists() or not path.is_file():
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:]).strip()
    except Exception:
        return ""


def _extract_root_cause(log_tail: str) -> Dict:
    """
    从日志尾部提取根因线索：
    - Python traceback 关键帧（file:line:function）
    - Python 最后一行异常类型/消息
    - R 的 Error in ... 消息
    """
    if not log_tail:
        return {
            "has_traceback": False,
            "language": None,
            "exception_type": None,
            "exception_message": None,
            "frames": [],
        }

    lines = [ln.rstrip("\n") for ln in log_tail.splitlines()]
    frames: List[Dict[str, str]] = []
    has_python_tb = any("Traceback (most recent call last):" in ln for ln in lines)

    if has_python_tb:
        for ln in lines:
            m = TRACEBACK_FILE_LINE_RE.match(ln)
            if not m:
                continue
            frames.append(
                {
                    "file": m.group("file"),
                    "line": m.group("line"),
                    "function": m.group("func").strip(),
                }
            )
        # 最后一行通常为异常类型和消息
        tail_line = ""
        for ln in reversed(lines):
            if ln.strip():
                tail_line = ln.strip()
                break
        exc_type = None
        exc_msg = None
        if ":" in tail_line:
            left, right = tail_line.split(":", 1)
            if left.strip().endswith(("Error", "Exception")):
                exc_type = left.strip()
                exc_msg = right.strip()
        return {
            "has_traceback": True,
            "language": "python",
            "exception_type": exc_type,
            "exception_message": exc_msg or (tail_line if tail_line else None),
            "frames": frames[-8:],
        }

    # 尝试提取 R 错误行
    r_msg = None
    for ln in reversed(lines):
        m = R_ERROR_RE.match(ln)
        if m:
            r_msg = m.group("msg").strip()
            break
    if r_msg:
        return {
            "has_traceback": False,
            "language": "r",
            "exception_type": "RRuntimeError",
            "exception_message": r_msg,
            "frames": [],
        }

    return {
        "has_traceback": False,
        "language": None,
        "exception_type": None,
        "exception_message": None,
        "frames": [],
    }


def _resolve_repo_script_path(raw_path: str, repo_root: Path) -> Optional[Path]:
    """
    将 traceback 中的路径解析为仓库内可读文件。
    兼容：本机绝对路径、Docker /app/...、仅含 code/ 或 backend/ 相对后缀。
    """
    if not (raw_path or "").strip():
        return None
    raw = raw_path.strip()
    norm = raw.replace("\\", "/")
    try:
        p = Path(raw)
        if p.is_file():
            return p.resolve()
    except OSError:
        pass
    for marker in ("code/", "backend/", "automata-web/"):
        idx = norm.find(marker)
        if idx >= 0:
            candidate = (repo_root / norm[idx:]).resolve()
            if candidate.is_file():
                return candidate
    if norm.startswith("/app/"):
        candidate = (repo_root / norm[5:].lstrip("/")).resolve()
        if candidate.is_file():
            return candidate
    return None


def _should_skip_snippet_path(file_str: str) -> bool:
    fs = (file_str or "").replace("\\", "/").lower()
    return any(s.lower() in fs for s in _SKIP_SNIPPET_SUBSTR)


def _read_code_window(
    path: Path,
    center_line: int,
    before: int = 20,
    after: int = 20,
) -> Optional[Dict[str, Any]]:
    """读取源码窗口（center_line 为 1-based），返回可 JSON 序列化的片段描述。"""
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return None
    n = len(lines)
    if n == 0:
        return None
    try:
        cl = int(center_line)
    except (TypeError, ValueError):
        return None
    cl = max(1, min(cl, n))
    start = max(1, cl - before)
    end = min(n, cl + after)
    numbered: List[str] = []
    for i in range(start - 1, end):
        text = lines[i].rstrip("\n\r")
        numbered.append(f"{i + 1:5d} | {text}")
    return {
        "resolved_path": str(path),
        "center_line": cl,
        "start_line": start,
        "end_line": end,
        "snippet": "\n".join(numbered),
    }


def _collect_code_snippets_from_frames(
    frames: List[Dict[str, str]],
    repo_root: Path,
    *,
    before: int = 20,
    after: int = 20,
    max_snippets: int = 3,
    max_total_chars: int = 15000,
) -> List[Dict[str, Any]]:
    """
    从 Python traceback frames 由内向外在仓库内解析源码片段（优先最内层调用帧）。
    """
    if not frames:
        return []
    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, int]] = set()
    total_chars = 0
    for frame in reversed(frames):
        if len(out) >= max_snippets:
            break
        fpath = (frame or {}).get("file") or ""
        line_s = (frame or {}).get("line")
        if not fpath or line_s is None or _should_skip_snippet_path(fpath):
            continue
        try:
            line_no = int(line_s)
        except (TypeError, ValueError):
            continue
        resolved = _resolve_repo_script_path(fpath, repo_root)
        if not resolved:
            continue
        key = (str(resolved), line_no)
        if key in seen:
            continue
        block = _read_code_window(resolved, line_no, before=before, after=after)
        if not block:
            continue
        seen.add(key)
        snip = block.get("snippet") or ""
        if total_chars + len(snip) + 200 > max_total_chars:
            if out:
                break
            block["snippet"] = snip[: max(0, max_total_chars - 500)] + "\n... (truncated)"
        item = {
            "original_file": fpath,
            "function": (frame or {}).get("function"),
            **block,
        }
        out.append(item)
        total_chars += len(block.get("snippet") or "") + 200
    return out


def _collect_result_artifacts(job_dir: Path, result_file: Optional[str], max_items: int = 30) -> List[str]:
    """收集任务目录与 result_file 指向路径下的结果文件清单。"""
    seen: set[str] = set()
    out: List[str] = []

    def _append_path(base: Path):
        nonlocal out
        if not base.exists():
            return
        if base.is_file():
            rel = str(base)
            if rel not in seen:
                seen.add(rel)
                out.append(rel)
            return
        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            rel = str(p)
            if rel in seen:
                continue
            seen.add(rel)
            out.append(rel)
            if len(out) >= max_items:
                return

    _append_path(job_dir / "result")
    if result_file:
        _append_path(Path(result_file))
    return out[:max_items]


def _load_job_context(db: Session, user_id: int, job_id: str) -> Dict:
    """
    读取任务上下文（数据库 + 任务目录），用于平台紧密相关诊断/解读。
    """
    job = db.query(Job).filter(Job.job_id == job_id, Job.user_id == user_id).first()
    if not job:
        return {
            "job_id": job_id,
            "found": False,
            "missing_fields": ["job_record"],
        }

    job_dir = settings.path_jobs / job_id
    candidates = [
        job_dir / "terminal_msg.txt",
        job_dir / "result" / "terminal.log",
        job_dir / "config.txt",
    ]
    logs_tail = ""
    for p in candidates[:2]:
        logs_tail = _read_tail_lines(p, max_lines=200)
        if logs_tail:
            break

    config_summary = _read_tail_lines(candidates[2], max_lines=120)
    artifacts = _collect_result_artifacts(job_dir, job.result_file)
    root_cause = _extract_root_cause(logs_tail)
    status_text = job.status.value if hasattr(job.status, "value") else str(job.status)
    job_type_text = job.job_type.value if hasattr(job.job_type, "value") else str(job.job_type)
    code_snippets: List[Dict[str, Any]] = []
    if root_cause.get("language") == "python" and root_cause.get("frames"):
        code_snippets = _collect_code_snippets_from_frames(
            root_cause["frames"], settings.path_repo
        )
    semantic_context = build_semantic_context(
        job_type=job_type_text,
        config_summary=config_summary,
        log_tail=logs_tail,
        root_cause=root_cause,
        input_params=job.input_params,
    )
    missing_fields = []
    if not logs_tail:
        missing_fields.append("terminal_log")
    if not config_summary:
        missing_fields.append("config_txt")
    if not artifacts:
        missing_fields.append("result_artifacts")

    return {
        "job_id": job_id,
        "found": True,
        "job_meta": {
            "job_type": job_type_text,
            "status": status_text,
            "progress": job.progress,
            "current_step": job.current_step,
            "created_at": str(job.created_at) if job.created_at else None,
            "updated_at": str(job.updated_at) if job.updated_at else None,
            "result_file": job.result_file,
            "error_message": job.error_message,
            "input_params": job.input_params,
        },
        "log_tail": logs_tail,
        "config_summary": config_summary,
        "root_cause": root_cause,
        "code_snippets": code_snippets,
        "semantic_context": semantic_context,
        "result_artifacts": artifacts,
        "diagnosis_ready": bool(logs_tail or artifacts),
        "missing_fields": missing_fields,
    }


def _classify_intent(message: str, requested_mode: Optional[str] = None) -> str:
    """
    自动识别用户意图（参数建议 / 失败诊断 / 结果解读）。
    优先使用前端显式传入 mode；否则走关键词规则分类。
    """
    allowed_modes = {"param_advice", "failure_diagnosis", "result_interpretation"}
    if requested_mode in allowed_modes:
        return requested_mode

    text = (message or "").lower()
    if not text:
        return "param_advice"

    if re.search(r"(traceback|error|报错|失败|terminal|terminal_msg|异常|堆栈|cannot|not found)", text):
        return "failure_diagnosis"
    if re.search(r"(结果|解读|报告|interpret|enrichment|通路|显著|p值|fdr|fold change)", text):
        return "result_interpretation"
    if re.search(r"(参数|padj|dropout|learning rate|epoch|batch|建议|怎么设|如何设置)", text):
        return "param_advice"
    return "param_advice"


def _detect_user_language(user_message: str) -> str:
    """
    根据用户输入粗略检测语言：
    - 含中文字符 -> zh
    - 含英文字符且无中文 -> en
    - 其他情况默认 zh
    """
    text = user_message or ""
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return "zh"


def _build_mode_prompt(intent: str, user_message: str, job_context: Optional[Dict] = None) -> Tuple[str, str]:
    """
    为不同意图构造面向普通生物学用户的响应约束提示。
    返回: (intent_display, wrapped_message)
    """
    user_lang = _detect_user_language(user_message)
    # 前端模式显示统一英文
    intent_display_map = {
        "param_advice": "Parameter Suggestion",
        "failure_diagnosis": "Failure Diagnosis",
        "result_interpretation": "Result Interpretation",
    }
    intent_display = intent_display_map.get(intent, "Parameter Suggestion")

    mode_instructions_zh = {
        "param_advice": (
            "你是生物信息平台助手。当前任务=参数建议。"
            "用户是普通生物学用户，请避免术语堆砌。"
            "输出顺序：1) 先给结论（最多3条）；2) 可执行步骤；3) 简短原因。"
            "请使用中文回答。"
        ),
        "failure_diagnosis": (
            "你是生物信息平台助手。当前任务=失败诊断。"
            "请先归类最可能的错误类型，再给排查步骤（按优先级）。"
            "如果有 root_cause.frames，请明确指出最关键 file:line:function 并解释其为何导致报错。"
            "若任务上下文中包含 code_snippets（平台从仓库自动回读的源码窗口），请必须结合片段中的实际逻辑解释根因，"
            "不要与代码行为相矛盾；不要臆测片段中不存在的逻辑。"
            "若任务上下文中包含 semantic_context（脚本语义卡+检查器结果），请优先引用 checker_results 作为事实依据。"
            "输出顺序：1) 最可能原因；2) 关键报错位置(file:line)；3) 立即可做的3步；4) 仍失败时提供下一步信息收集清单。"
            "请使用中文回答。"
        ),
        "result_interpretation": (
            "你是生物信息平台助手。当前任务=结果解读。"
            "面向普通生物学用户，先给生物学含义，再给风险提示和后续实验建议。"
            "若有 semantic_context.semantic_card/result_hints，请优先按其结构组织解读。"
            "输出顺序：1) 关键发现；2) 生物学解释；3) 下一步建议。"
            "请使用中文回答。"
        ),
    }
    mode_instructions_en = {
        "param_advice": (
            "You are a bioinformatics platform assistant. Task = parameter suggestion. "
            "The user is a non-technical biologist, avoid jargon-heavy wording. "
            "Output order: 1) concise conclusion (up to 3 items); 2) actionable steps; 3) brief rationale. "
            "Please answer in English."
        ),
        "failure_diagnosis": (
            "You are a bioinformatics platform assistant. Task = failure diagnosis. "
            "First classify the most likely error type, then provide prioritized troubleshooting steps. "
            "If root_cause.frames exists, identify the key file:line:function and explain why it causes failure. "
            "If code_snippets exist, explain based on real snippet logic and do not speculate beyond shown code. "
            "If semantic_context exists, treat checker_results as factual evidence. "
            "Output order: 1) most likely cause; 2) key error location (file:line); 3) immediate 3-step actions; "
            "4) if still failing, what additional info to collect. "
            "Please answer in English."
        ),
        "result_interpretation": (
            "You are a bioinformatics platform assistant. Task = result interpretation. "
            "For non-technical biologists, start with biological meaning, then risks/caveats, then next experiments. "
            "If semantic_context.semantic_card/result_hints exists, structure your interpretation around them. "
            "Output order: 1) key findings; 2) biological interpretation; 3) next-step suggestions. "
            "Please answer in English."
        ),
    }
    mode_instructions = mode_instructions_en if user_lang == "en" else mode_instructions_zh
    instruction = mode_instructions.get(intent, mode_instructions["param_advice"])
    context_block = ""
    if job_context:
        context_block = (
            "\n\n任务上下文（由平台自动读取，请优先据此判断）:\n"
            f"{json.dumps(job_context, ensure_ascii=False)}"
        )
    wrapped = f"{instruction}{context_block}\n\n用户问题：{user_message}"
    return intent_display, wrapped


def _get_or_create_graph(provider: str = None):
    """
    获取或创建 Agent 执行图
    
    使用缓存避免重复创建
    
    Args:
        provider: LLM 提供商
        
    Returns:
        编译后的 Agent 执行图
    """
    provider = provider or settings.AGENT_DEFAULT_PROVIDER
    
    if provider not in agent_graphs:
        logger.info(f"[Agent Router] 创建新的 Agent 图: provider={provider}")
        tools = get_all_tools()
        agent_graphs[provider] = create_agent_graph(provider, tools)
    
    return agent_graphs[provider]


def _get_conversation_history(user_id: str, ws_id: int) -> List[BaseMessage]:
    """
    获取用户的对话历史
    
    Args:
        user_id: 用户 ID
        ws_id: WebSocket 连接 ID
        
    Returns:
        对话历史消息列表
    """
    if user_id not in conversation_histories:
        conversation_histories[user_id] = {}
    
    if ws_id not in conversation_histories[user_id]:
        conversation_histories[user_id][ws_id] = []
    
    return conversation_histories[user_id][ws_id]


def _add_to_history(user_id: str, ws_id: int, message: BaseMessage):
    """
    添加消息到对话历史
    
    限制历史长度为最近 50 条消息
    
    Args:
        user_id: 用户 ID
        ws_id: WebSocket 连接 ID
        message: 要添加的消息
    """
    history = _get_conversation_history(user_id, ws_id)
    history.append(message)
    
    # 限制历史长度
    max_history = 50
    if len(history) > max_history:
        conversation_histories[user_id][ws_id] = history[-max_history:]


def _clear_history(user_id: str, ws_id: int):
    """
    清空用户的对话历史
    
    Args:
        user_id: 用户 ID
        ws_id: WebSocket 连接 ID
    """
    if user_id in conversation_histories and ws_id in conversation_histories[user_id]:
        conversation_histories[user_id][ws_id] = []


@router.websocket("/chat")
async def agent_chat_websocket(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    AI Agent 聊天 WebSocket 端点
    
    协议说明：
    
    1. 连接后需要先发送认证消息：
       {"type": "auth", "token": "your_jwt_token"}
    
    2. 认证成功后会收到：
       {"event": "connected", "message": "Agent ready"}
    
    3. 发送聊天消息：
       {"type": "chat", "message": "你好", "provider": "openai"}
       - provider 可选，不传则使用默认配置
    
    4. 服务端会流式返回：
       - {"event": "agent_thinking", "content": "..."}  LLM 正在思考
       - {"event": "agent_tool_call", "tool": "...", "args": {...}}  开始调用工具
       - {"event": "agent_tool_result", "tool": "...", "result": "..."}  工具执行结果
       - {"event": "agent_response", "content": "...", "done": true}  最终回复
       - {"event": "error", "message": "..."}  错误消息
    
    5. 心跳检测：
       发送 {"type": "heartbeat"}
       收到 {"event": "pong"}
    
    6. 清空对话历史：
       发送 {"type": "clear_history"}
       收到 {"event": "history_cleared"}
    """
    ws_id = id(websocket)
    user_id = None
    user = None
    
    try:
        # 接受 WebSocket 连接
        await websocket.accept()
        logger.info(f"[Agent WS] WebSocket 连接已接受, ws_id={ws_id}")
        
        # 等待认证消息
        try:
            logger.info("[Agent WS] 等待认证消息...")
            auth_message = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=30.0
            )
            logger.debug(f"[Agent WS] 收到消息: {auth_message[:100]}...")
        except asyncio.TimeoutError:
            logger.warning("[Agent WS] 认证超时")
            await websocket.close(code=4002, reason="Authentication timeout")
            return
        
        # 解析认证消息
        try:
            auth_data = json.loads(auth_message)
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({
                "event": "error",
                "message": "无效的 JSON 格式"
            }, ensure_ascii=False))
            await websocket.close(code=4000, reason="Invalid JSON")
            return
        
        # 验证认证
        if auth_data.get("type") != "auth" or "token" not in auth_data:
            await websocket.send_text(json.dumps({
                "event": "auth_required",
                "message": "请发送认证消息: {\"type\": \"auth\", \"token\": \"your_token\"}"
            }, ensure_ascii=False))
            await websocket.close(code=4000, reason="Invalid auth format")
            return
        
        # 验证 token
        try:
            token = auth_data["token"]
            user = get_current_user_from_websocket(token, db)
            user_id = str(user.id)
            logger.info(f"[Agent WS] 认证成功, user_id={user_id}, username={user.username}")
        except Exception as e:
            logger.warning(f"[Agent WS] 认证失败: {e}")
            await websocket.send_text(json.dumps({
                "event": "auth_failed",
                "message": str(e)
            }, ensure_ascii=False))
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # 检查 Agent 是否启用
        if not settings.AGENT_ENABLED:
            await websocket.send_text(json.dumps({
                "event": "error",
                "message": "AI Agent 功能未启用，请联系管理员配置"
            }, ensure_ascii=False))
            await websocket.close(code=4003, reason="Agent not enabled")
            return
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "event": "connected",
            "message": "Agent ready",
            "user_id": user_id,
            "timestamp": int(datetime.now().timestamp())
        }, ensure_ascii=False))
        
        # 主消息循环
        while True:
            try:
                message_text = await websocket.receive_text()
                logger.debug(f"[Agent WS] 收到消息: {message_text[:200]}...")
                
                try:
                    message_data = json.loads(message_text)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "event": "error",
                        "message": "无效的 JSON 格式"
                    }, ensure_ascii=False))
                    continue
                
                msg_type = message_data.get("type")
                
                # 心跳
                if msg_type == "heartbeat":
                    await websocket.send_text(json.dumps({
                        "event": "pong",
                        "timestamp": int(datetime.now().timestamp())
                    }, ensure_ascii=False))
                    continue
                
                # 清空历史
                if msg_type == "clear_history":
                    _clear_history(user_id, ws_id)
                    await websocket.send_text(json.dumps({
                        "event": "history_cleared",
                        "message": "对话历史已清空"
                    }, ensure_ascii=False))
                    continue
                
                # 聊天消息
                if msg_type == "chat":
                    user_message = message_data.get("message", "").strip()
                    provider = message_data.get("provider")
                    requested_mode = message_data.get("mode")
                    requested_job_id = message_data.get("job_id")
                    
                    if not user_message:
                        await websocket.send_text(json.dumps({
                            "event": "error",
                            "message": "消息内容不能为空"
                        }, ensure_ascii=False))
                        continue
                    
                    # 验证提供商配置
                    is_valid, error_msg = validate_provider_config(provider)
                    if not is_valid:
                        await websocket.send_text(json.dumps({
                            "event": "error",
                            "message": error_msg
                        }, ensure_ascii=False))
                        continue
                    
                    # 获取 Agent 图
                    try:
                        graph = _get_or_create_graph(provider)
                    except Exception as e:
                        logger.error(f"[Agent WS] 创建 Agent 图失败: {e}")
                        await websocket.send_text(json.dumps({
                            "event": "error",
                            "message": f"初始化 Agent 失败: {str(e)}"
                        }, ensure_ascii=False))
                        continue
                    
                    # 获取对话历史
                    history = _get_conversation_history(user_id, ws_id)
                    intent = _classify_intent(user_message, requested_mode)
                    detected_job_id = _extract_job_id(user_message, requested_job_id)
                    job_context = _load_job_context(db, user.id, detected_job_id) if detected_job_id else None
                    intent_display, wrapped_message = _build_mode_prompt(intent, user_message, job_context)
                    await websocket.send_text(json.dumps({
                        "event": "agent_intent",
                        "intent": intent,
                        "intent_display": intent_display
                    }, ensure_ascii=False))
                    if job_context:
                        await websocket.send_text(json.dumps({
                            "event": "agent_job_context",
                            "job_id": detected_job_id,
                            "found": bool(job_context.get("found")),
                            "diagnosis_ready": bool(job_context.get("diagnosis_ready")),
                            "missing_fields": job_context.get("missing_fields", [])
                        }, ensure_ascii=False))
                    
                    # 构建工具上下文（只存储可序列化的数据）
                    # 注意：不要存储 db session 对象，因为它无法被 msgpack 序列化
                    tool_context = {
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                    
                    # 运行 Agent
                    logger.info(f"[Agent WS] 开始处理用户消息, user_id={user_id}")
                    
                    final_response = ""
                    
                    try:
                        async for event in run_agent(
                            graph=graph,
                            user_message=wrapped_message,
                            user_id=user_id,
                            conversation_history=history,
                            tool_context=tool_context,
                            thread_id=f"ws_{ws_id}"
                        ):
                            # 转发事件到前端
                            await websocket.send_text(json.dumps(event, ensure_ascii=False))
                            
                            # 记录最终响应
                            if event.get("event") == "agent_response":
                                final_response = event.get("content", "")
                            elif event.get("event") == "agent_thinking":
                                # thinking 内容也可能是最终响应
                                final_response = event.get("content", "")
                        
                        # 更新对话历史
                        _add_to_history(user_id, ws_id, HumanMessage(content=user_message))
                        if final_response:
                            _add_to_history(user_id, ws_id, AIMessage(content=final_response))
                        
                    except Exception as e:
                        logger.error(f"[Agent WS] Agent 执行失败: {e}", exc_info=True)
                        await websocket.send_text(json.dumps({
                            "event": "error",
                            "message": f"处理请求失败: {str(e)}"
                        }, ensure_ascii=False))
                    
                    continue
                
                # 未知消息类型
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "message": f"未知的消息类型: {msg_type}"
                }, ensure_ascii=False))
                
            except WebSocketDisconnect:
                logger.info(f"[Agent WS] 客户端断开连接, user_id={user_id}")
                break
            except Exception as e:
                logger.error(f"[Agent WS] 消息处理异常: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "event": "error",
                        "message": f"消息处理异常: {str(e)}"
                    }, ensure_ascii=False))
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"[Agent WS] WebSocket 断开, ws_id={ws_id}")
    except Exception as e:
        logger.error(f"[Agent WS] WebSocket 连接异常: {e}", exc_info=True)
    finally:
        # 清理连接相关资源
        if user_id and ws_id in conversation_histories.get(user_id, {}):
            # 保留对话历史，用户可能会重新连接
            pass
        logger.info(f"[Agent WS] 连接清理完成, ws_id={ws_id}")


@router.get("/status")
async def get_agent_status():
    """
    获取 Agent 服务状态
    
    返回 Agent 是否启用、支持的提供商等信息
    """
    providers = []
    
    # 检查各提供商配置
    for provider in ["openai", "qwen", "deepseek"]:
        is_valid, _ = validate_provider_config(provider)
        providers.append({
            "name": provider,
            "configured": is_valid
        })
    
    return {
        "enabled": settings.AGENT_ENABLED,
        "default_provider": settings.AGENT_DEFAULT_PROVIDER,
        "providers": providers,
        "max_turns": settings.AGENT_MAX_TURNS,
        "semantic_coverage": get_semantic_coverage(str(settings.path_repo)),
    }
