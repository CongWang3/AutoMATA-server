"""
LangGraph Agent 核心框架
使用 StateGraph 实现的 Agent 执行图
"""
import logging
import json
from typing import TypedDict, Annotated, Any, Optional, List, AsyncGenerator
from operator import add

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from config.settings import settings
from api.agent.llm_provider import get_chat_model

logger = logging.getLogger(__name__)


# Agent 系统提示词
SYSTEM_PROMPT = """你是 AutoMATA 生物信息学分析平台的 AI 助手。

你可以帮助用户：
1. 查询和管理用户上传的文件
2. 查询和管理分析任务（作业）
3. 执行各种生物信息学分析（PCA、火山图、差异表达分析等）

在执行分析任务时，请：
- 先确认用户已有的数据文件
- 询问必要的分析参数
- 清晰地解释分析结果

请用中文与用户交流，保持专业、友好的语气。"""


class AgentState(TypedDict):
    """
    Agent 状态定义
    
    包含消息历史、用户信息和数据库会话等上下文
    """
    # 消息历史，使用 add 操作符累加新消息
    messages: Annotated[List[BaseMessage], add]
    # 当前用户 ID
    user_id: str
    # 数据库会话引用（存储为字符串形式的标识）
    db_session_id: Optional[str]
    # 工具执行上下文（用于工具函数访问用户信息）
    tool_context: Optional[dict]


def _should_continue(state: AgentState) -> str:
    """
    判断是否需要继续执行工具调用
    
    检查最后一条消息是否包含工具调用请求
    
    Args:
        state: 当前 Agent 状态
        
    Returns:
        "continue" 如果需要执行工具调用，否则 "end"
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    # 检查是否有工具调用
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.debug(f"[Agent Graph] 检测到工具调用: {[tc['name'] for tc in last_message.tool_calls]}")
        return "continue"
    
    return "end"


def create_call_model_node(model: BaseChatModel, tools: list):
    """
    创建调用 LLM 的节点函数
    
    Args:
        model: 绑定工具后的 LLM 模型
        tools: 工具列表
        
    Returns:
        节点函数
    """
    # 绑定工具到模型
    model_with_tools = model.bind_tools(tools) if tools else model
    
    async def call_model(state: AgentState) -> dict:
        """
        调用 LLM 模型处理消息
        
        Args:
            state: 当前 Agent 状态
            
        Returns:
            包含新消息的状态更新
        """
        messages = state.get("messages", [])
        
        # 确保有系统提示
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        logger.debug(f"[Agent Graph] 调用 LLM，消息数量: {len(messages)}")
        
        try:
            response = await model_with_tools.ainvoke(messages)
            logger.debug(f"[Agent Graph] LLM 响应类型: {type(response).__name__}")
            
            if hasattr(response, "tool_calls") and response.tool_calls:
                logger.info(f"[Agent Graph] LLM 请求调用工具: {[tc['name'] for tc in response.tool_calls]}")
            
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"[Agent Graph] LLM 调用失败: {e}")
            # 返回错误消息而不是抛出异常
            error_message = AIMessage(content=f"抱歉，处理请求时出错: {str(e)}")
            return {"messages": [error_message]}
    
    return call_model


def create_agent_graph(
    provider: str = None,
    tools: list = None,
    user_id: Optional[str] = None,
) -> StateGraph:
    """
    创建 Agent 执行图
    
    使用 LangGraph 的 StateGraph 构建包含 LLM 调用和工具执行的执行流程
    
    Args:
        provider: LLM 提供商 (openai/qwen/deepseek)
        tools: 可用工具列表
        user_id: 当前用户 ID（BYOK 解析用，可为 None）
        
    Returns:
        编译后的 StateGraph
    
    Examples:
        >>> from api.agent.tools import get_all_tools
        >>> graph = create_agent_graph("openai", get_all_tools())
    """
    tools = tools or []
    
    # 获取 LLM 模型
    model = get_chat_model(provider, user_id=user_id)
    logger.info(f"[Agent Graph] 使用模型提供商: {provider or settings.AGENT_DEFAULT_PROVIDER}")
    logger.info(f"[Agent Graph] 注册工具数量: {len(tools)}")
    
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    # 1. LLM 调用节点
    call_model_node = create_call_model_node(model, tools)
    workflow.add_node("agent", call_model_node)
    
    # 2. 工具执行节点
    if tools:
        tool_node = ToolNode(tools)
        workflow.add_node("tools", tool_node)
    
    # 设置入口点
    workflow.set_entry_point("agent")
    
    # 添加条件边
    if tools:
        workflow.add_conditional_edges(
            "agent",
            _should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        # 工具执行后回到 agent
        workflow.add_edge("tools", "agent")
    else:
        # 没有工具时直接结束
        workflow.add_edge("agent", END)
    
    # 编译图
    # 使用内存检查点保存器（支持对话状态持久化）
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)
    
    logger.info("[Agent Graph] Agent 执行图创建完成")
    return compiled_graph


async def run_agent(
    graph,
    user_message: str,
    user_id: str,
    db_session_id: str = None,
    conversation_history: List[BaseMessage] = None,
    tool_context: dict = None,
    thread_id: str = None
) -> AsyncGenerator[dict, None]:
    """
    运行 Agent 处理用户消息
    
    这是一个异步生成器，会 yield 各种事件供前端展示
    
    Args:
        graph: 编译后的 Agent 执行图
        user_message: 用户输入的消息
        user_id: 用户 ID
        db_session_id: 数据库会话标识
        conversation_history: 历史消息列表
        tool_context: 工具执行上下文（包含 db session 等）
        thread_id: 对话线程 ID（用于状态持久化）
        
    Yields:
        dict: 事件字典，格式如下：
            - {"event": "agent_thinking", "content": "..."}  LLM 正在思考
            - {"event": "agent_tool_call", "tool": "...", "args": {...}}  开始调用工具
            - {"event": "agent_tool_result", "tool": "...", "result": "..."}  工具结果
            - {"event": "agent_response", "content": "...", "done": True}  最终回复
            - {"event": "error", "message": "..."}  错误
    """
    logger.info(f"[Agent Run] 开始处理用户消息, user_id={user_id}")
    
    # 构建初始状态
    messages = []
    
    # 添加系统提示
    messages.append(SystemMessage(content=SYSTEM_PROMPT))
    
    # 添加历史消息
    if conversation_history:
        messages.extend(conversation_history)
    
    # 添加当前用户消息
    messages.append(HumanMessage(content=user_message))
    
    initial_state: AgentState = {
        "messages": messages,
        "user_id": user_id,
        "db_session_id": db_session_id,
        "tool_context": tool_context or {}
    }
    
    # 配置运行参数
    config = {
        "configurable": {
            "thread_id": thread_id or f"thread_{user_id}",
            "user_id": user_id,
        }
    }
    
    # 如果有工具上下文，注入到 config 中
    if tool_context:
        config["configurable"]["tool_context"] = tool_context
    
    try:
        # 追踪已处理的消息数量
        processed_message_count = len(messages)
        turn_count = 0
        max_turns = settings.AGENT_MAX_TURNS
        
        # 流式执行
        async for event in graph.astream(initial_state, config=config, stream_mode="updates"):
            logger.debug(f"[Agent Run] 收到事件: {list(event.keys())}")
            
            # 处理 agent 节点的输出
            if "agent" in event:
                agent_output = event["agent"]
                new_messages = agent_output.get("messages", [])
                
                for msg in new_messages:
                    if isinstance(msg, AIMessage):
                        # 检查是否有工具调用
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                yield {
                                    "event": "agent_tool_call",
                                    "tool": tool_call["name"],
                                    "args": tool_call["args"],
                                    "tool_call_id": tool_call["id"]
                                }
                        else:
                            # 普通文本响应
                            if msg.content:
                                yield {
                                    "event": "agent_thinking",
                                    "content": msg.content
                                }
            
            # 处理 tools 节点的输出
            if "tools" in event:
                tools_output = event["tools"]
                new_messages = tools_output.get("messages", [])
                
                for msg in new_messages:
                    if isinstance(msg, ToolMessage):
                        yield {
                            "event": "agent_tool_result",
                            "tool": msg.name,
                            "result": msg.content,
                            "tool_call_id": msg.tool_call_id
                        }
            
            # 检查轮数限制
            turn_count += 1
            if turn_count >= max_turns * 2:  # 每轮可能有 agent 和 tools 两个事件
                logger.warning(f"[Agent Run] 达到最大轮数限制: {max_turns}")
                yield {
                    "event": "error",
                    "message": f"对话轮数达到上限（{max_turns}轮），请开始新对话"
                }
                break
        
        # 获取最终状态
        final_state = await graph.aget_state(config)
        if final_state and final_state.values:
            final_messages = final_state.values.get("messages", [])
            if final_messages:
                last_msg = final_messages[-1]
                if isinstance(last_msg, AIMessage) and last_msg.content:
                    # 检查这个消息是否已经作为 thinking 发送过
                    if not (hasattr(last_msg, "tool_calls") and last_msg.tool_calls):
                        # 移除 Markdown 标题标记
                        cleaned_content = strip_markdown_headers(last_msg.content)
                        yield {
                            "event": "agent_response",
                            "content": cleaned_content,
                            "done": True
                        }
                        return
        
        # 如果没有最终响应，发送完成标记
        yield {
            "event": "agent_response",
            "content": "",
            "done": True
        }
        
    except Exception as e:
        logger.error(f"[Agent Run] Agent 执行失败: {e}", exc_info=True)
        yield {
            "event": "error",
            "message": f"处理请求时发生错误: {str(e)}"
        }


def strip_markdown_headers(text: str) -> str:
    """
    将 Markdown 格式的标题转换为纯文本格式
    
    Args:
        text: 包含 Markdown 的文本
        
    Returns:
        转换后的文本（## 标题 → 标题）
    """
    if not text:
        return text
    
    # 移除行首的 # 符号及其后的空格
    import re
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # 移除开头的 # 和紧随的空格，保留标题文字
        cleaned_line = re.sub(r'^#+\s*', '', line)
        cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)


def get_conversation_messages(state_messages: List[BaseMessage]) -> List[dict]:
    """
    将 LangChain 消息转换为可序列化的格式
    
    Args:
        state_messages: LangChain 消息列表
        
    Returns:
        可序列化的消息字典列表
    """
    result = []
    for msg in state_messages:
        if isinstance(msg, SystemMessage):
            continue  # 跳过系统消息
        
        msg_dict = {
            "type": type(msg).__name__,
            "content": msg.content
        }
        
        if isinstance(msg, AIMessage):
            msg_dict["role"] = "assistant"
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
        elif isinstance(msg, HumanMessage):
            msg_dict["role"] = "user"
        elif isinstance(msg, ToolMessage):
            msg_dict["role"] = "tool"
            msg_dict["tool_name"] = msg.name
        
        result.append(msg_dict)
    
    return result
