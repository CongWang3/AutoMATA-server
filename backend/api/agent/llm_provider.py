"""
LLM 模型提供者工厂模块
支持 OpenAI、通义千问（Qwen）、DeepSeek 等模型
"""
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from config.settings import settings

logger = logging.getLogger(__name__)


def get_chat_model(provider: Optional[str] = None) -> BaseChatModel:
    """
    获取指定提供商的聊天模型实例
    
    根据 provider 参数（或默认配置）返回对应的 ChatModel 实例。
    所有模型都通过 OpenAI 兼容接口实现。
    
    Args:
        provider: 模型提供商，可选值：openai / qwen / deepseek
                  如果为 None，使用 settings.AGENT_DEFAULT_PROVIDER
    
    Returns:
        BaseChatModel: LangChain 聊天模型实例
    
    Raises:
        ValueError: 当提供商不支持或 API Key 未配置时抛出
    
    Examples:
        >>> model = get_chat_model("openai")
        >>> model = get_chat_model()  # 使用默认配置
    """
    # 确定使用的提供商
    provider = provider or settings.AGENT_DEFAULT_PROVIDER
    provider = provider.lower()
    
    logger.info(f"[LLM Provider] 初始化模型提供商: {provider}")
    
    if provider == "openai":
        return _get_openai_model()
    elif provider == "qwen":
        return _get_qwen_model()
    elif provider == "deepseek":
        return _get_deepseek_model()
    else:
        raise ValueError(f"不支持的模型提供商: {provider}，支持的选项: openai, qwen, deepseek")


def _get_openai_model() -> BaseChatModel:
    """
    获取 OpenAI 模型实例
    
    Returns:
        ChatOpenAI 实例
        
    Raises:
        ValueError: 当 API Key 未配置时抛出
    """
    api_key = settings.AGENT_OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API Key 未配置，请设置 AGENT_OPENAI_API_KEY 环境变量")
    
    model_kwargs = {
        "api_key": api_key,
        "model": settings.AGENT_OPENAI_MODEL,
        "temperature": 0,  # 保持输出稳定性
        "streaming": True,  # 启用流式输出
    }
    
    # 如果配置了代理地址，使用代理
    if settings.AGENT_OPENAI_BASE_URL:
        model_kwargs["base_url"] = settings.AGENT_OPENAI_BASE_URL
        logger.info(f"[LLM Provider] 使用 OpenAI 代理地址: {settings.AGENT_OPENAI_BASE_URL}")
    
    logger.info(f"[LLM Provider] 初始化 OpenAI 模型: {settings.AGENT_OPENAI_MODEL}")
    return ChatOpenAI(**model_kwargs)


def _get_qwen_model() -> BaseChatModel:
    """
    获取通义千问模型实例
    
    通过 OpenAI 兼容接口连接阿里云 DashScope
    
    Returns:
        ChatOpenAI 实例（配置为 Qwen）
        
    Raises:
        ValueError: 当 API Key 未配置时抛出
    """
    api_key = settings.AGENT_QWEN_API_KEY
    if not api_key:
        raise ValueError("通义千问 API Key 未配置，请设置 AGENT_QWEN_API_KEY 环境变量")
    
    # 通义千问通过 OpenAI 兼容接口（支持环境变量覆盖，默认 DashScope）
    qwen_base_url = settings.AGENT_QWEN_BASE_URL or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    logger.info(f"[LLM Provider] 初始化通义千问模型: {settings.AGENT_QWEN_MODEL}")
    logger.info(f"[LLM Provider] 使用通义千问地址: {qwen_base_url}")
    
    return ChatOpenAI(
        api_key=api_key,
        base_url=qwen_base_url,
        model=settings.AGENT_QWEN_MODEL,
        temperature=0,
        streaming=True,
    )


def _get_deepseek_model() -> BaseChatModel:
    """
    获取 DeepSeek 模型实例
    
    通过 OpenAI 兼容接口连接 DeepSeek API
    
    Returns:
        ChatOpenAI 实例（配置为 DeepSeek）
        
    Raises:
        ValueError: 当 API Key 未配置时抛出
    """
    api_key = settings.AGENT_DEEPSEEK_API_KEY
    if not api_key:
        raise ValueError("DeepSeek API Key 未配置，请设置 AGENT_DEEPSEEK_API_KEY 环境变量")
    
    base_url = settings.AGENT_DEEPSEEK_BASE_URL or "https://api.deepseek.com/v1"
    
    logger.info(f"[LLM Provider] 初始化 DeepSeek 模型: {settings.AGENT_DEEPSEEK_MODEL}")
    logger.info(f"[LLM Provider] 使用 DeepSeek 地址: {base_url}")
    
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=settings.AGENT_DEEPSEEK_MODEL,
        temperature=0,
        streaming=True,
    )


def validate_provider_config(provider: Optional[str] = None) -> tuple[bool, str]:
    """
    验证指定提供商的配置是否完整
    
    Args:
        provider: 模型提供商，如果为 None 使用默认配置
        
    Returns:
        (is_valid, error_message) 元组
    """
    provider = provider or settings.AGENT_DEFAULT_PROVIDER
    provider = provider.lower()
    
    if provider == "openai":
        if not settings.AGENT_OPENAI_API_KEY:
            return False, "OpenAI API Key 未配置"
        return True, ""
    elif provider == "qwen":
        if not settings.AGENT_QWEN_API_KEY:
            return False, "通义千问 API Key 未配置"
        return True, ""
    elif provider == "deepseek":
        if not settings.AGENT_DEEPSEEK_API_KEY:
            return False, "DeepSeek API Key 未配置"
        return True, ""
    else:
        return False, f"不支持的模型提供商: {provider}"
