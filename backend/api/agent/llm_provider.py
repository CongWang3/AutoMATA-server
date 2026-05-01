"""
LLM 模型提供者工厂模块
支持 OpenAI、通义千问（Qwen）、DeepSeek 等模型

Qwen/DeepSeek：若提供 user_id，则优先读取该用户本地 BYOK（data/agent_byok/<id>.json），
否则使用环境变量中的平台 Key。
"""
import logging
from typing import Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from config.settings import settings
from api.services.agent_byok_store import load_byok

logger = logging.getLogger(__name__)


def _byok_for_user(user_id: Optional[str]) -> Dict[str, str]:
    if not user_id:
        return {}
    try:
        return load_byok(settings.path_repo, settings.AGENT_BYOK_DIR, str(user_id))
    except (TypeError, ValueError):
        return {}


def _resolve_qwen_key(user_id: Optional[str]) -> Optional[str]:
    b = _byok_for_user(user_id).get("qwen")
    if b:
        return b
    s = (settings.AGENT_QWEN_API_KEY or "").strip()
    return s or None


def _resolve_deepseek_key(user_id: Optional[str]) -> Optional[str]:
    b = _byok_for_user(user_id).get("deepseek")
    if b:
        return b
    s = (settings.AGENT_DEEPSEEK_API_KEY or "").strip()
    return s or None


def get_chat_model(provider: Optional[str] = None, user_id: Optional[str] = None) -> BaseChatModel:
    """
    获取指定提供商的聊天模型实例

    Args:
        provider: openai / qwen / deepseek；None 时用 AGENT_DEFAULT_PROVIDER
        user_id: 当前用户 ID（字符串）；Qwen/DeepSeek 用于解析 BYOK
    """
    provider = provider or settings.AGENT_DEFAULT_PROVIDER
    provider = provider.lower()

    logger.info(f"[LLM Provider] 初始化模型提供商: {provider}")

    if provider == "openai":
        return _get_openai_model()
    elif provider == "qwen":
        return _get_qwen_model(user_id)
    elif provider == "deepseek":
        return _get_deepseek_model(user_id)
    else:
        raise ValueError(f"不支持的模型提供商: {provider}，支持的选项: openai, qwen, deepseek")


def _get_openai_model() -> BaseChatModel:
    api_key = settings.AGENT_OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API Key 未配置，请设置 AGENT_OPENAI_API_KEY 环境变量")

    model_kwargs = {
        "api_key": api_key,
        "model": settings.AGENT_OPENAI_MODEL,
        "temperature": 0,
        "streaming": True,
    }

    if settings.AGENT_OPENAI_BASE_URL:
        model_kwargs["base_url"] = settings.AGENT_OPENAI_BASE_URL
        logger.info(f"[LLM Provider] 使用 OpenAI 代理地址: {settings.AGENT_OPENAI_BASE_URL}")

    logger.info(f"[LLM Provider] 初始化 OpenAI 模型: {settings.AGENT_OPENAI_MODEL}")
    return ChatOpenAI(**model_kwargs)


def _get_qwen_model(user_id: Optional[str]) -> BaseChatModel:
    api_key = _resolve_qwen_key(user_id)
    if not api_key:
        raise ValueError("通义千问 API Key 未配置：请在设置中填写 BYOK，或由管理员配置 AGENT_QWEN_API_KEY")

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


def _get_deepseek_model(user_id: Optional[str]) -> BaseChatModel:
    api_key = _resolve_deepseek_key(user_id)
    if not api_key:
        raise ValueError("DeepSeek API Key 未配置：请在设置中填写 BYOK，或由管理员配置 AGENT_DEEPSEEK_API_KEY")

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


def validate_provider_config(
    provider: Optional[str] = None,
    user_id: Optional[str] = None,
) -> tuple[bool, str]:
    """
    验证指定提供商是否可调用。

    user_id 为 None 时（如 /status 公共探测）仅检查平台环境变量，不读 BYOK 文件。
    """
    provider = provider or settings.AGENT_DEFAULT_PROVIDER
    provider = provider.lower()

    if provider == "openai":
        if not settings.AGENT_OPENAI_API_KEY:
            return False, "OpenAI API Key 未配置"
        return True, ""
    elif provider == "qwen":
        if not _resolve_qwen_key(user_id):
            return False, "通义千问 API Key 未配置（BYOK 或 AGENT_QWEN_API_KEY）"
        return True, ""
    elif provider == "deepseek":
        if not _resolve_deepseek_key(user_id):
            return False, "DeepSeek API Key 未配置（BYOK 或 AGENT_DEEPSEEK_API_KEY）"
        return True, ""
    else:
        return False, f"不支持的模型提供商: {provider}"
