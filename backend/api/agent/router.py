"""
AI Agent WebSocket 路由
提供 Agent 聊天的 WebSocket 端点
"""
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from config.database import get_db
from config.settings import settings
from api.dependencies.auth import get_current_user_from_websocket
from api.agent.llm_provider import validate_provider_config
from api.agent.graph import create_agent_graph, run_agent
from api.agent.tools import get_all_tools

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["AI Agent"])


# 存储每个连接的对话历史（内存中）
# 格式: {user_id: {websocket_id: [messages]}}
conversation_histories: Dict[str, Dict[int, List[BaseMessage]]] = {}

# Agent 图实例缓存
# 格式: {provider: compiled_graph}
agent_graphs: Dict[str, any] = {}


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
                    
                    # 构建工具上下文
                    tool_context = {
                        "db": db,
                        "user": user,
                        "user_id": user.id
                    }
                    
                    # 运行 Agent
                    logger.info(f"[Agent WS] 开始处理用户消息, user_id={user_id}")
                    
                    final_response = ""
                    
                    try:
                        async for event in run_agent(
                            graph=graph,
                            user_message=user_message,
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
        "max_turns": settings.AGENT_MAX_TURNS
    }
