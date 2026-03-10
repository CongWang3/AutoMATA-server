"""
认证依赖项：FastAPI 依赖注入函数
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config.database import get_db
from api.models.user import User
from api.services.auth_service import AuthService


# HTTP Bearer 认证方案
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    获取认证服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        AuthService 实例
    """
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    获取当前认证用户（依赖注入）
    
    Args:
        credentials: HTTP Bearer 凭证
        auth_service: 认证服务实例
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        token = credentials.credentials
        logger.debug(f"开始验证token: {token[:20]}...")
        user = auth_service.get_current_user(token)
        logger.debug(f"Token验证成功，用户ID: {user.id}")
        return user
    except HTTPException as e:
        logger.warning(f"Token验证失败: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Token验证过程中发生未预期错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证服务异常",
            headers={"WWW-Authenticate": "Bearer"}
        ) from e


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前活跃用户对象
        
    Raises:
        HTTPException: 用户被禁用时抛出 400 错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账户已被禁用"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取当前管理员用户
    
    Args:
        current_user: 当前活跃用户对象
        
    Returns:
        当前管理员用户对象
        
    Raises:
        HTTPException: 用户不是管理员时抛出 403 错误
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def get_current_user_from_websocket(token: str, db: Session) -> User:
    """
    从 WebSocket 连接中获取当前认证用户
    
    Args:
        token: JWT 认证令牌
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：为 WebSocket 连接提供认证支持，复用现有的认证逻辑
    # - 已知局限：与 HTTP 认证共享相同的 AuthService，保持一致性
    # - 业务背景：WebSocket 连接需要与 HTTP API 相同的认证机制
    # - 测试重点：请验证 WebSocket 认证流程、token 解析、用户查询
    # -->
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.debug(f"[WS Auth] 开始验证token: {token[:20]}...")
        auth_service = AuthService(db)
        user = auth_service.get_current_user(token)
        logger.debug(f"[WS Auth] Token验证成功，用户ID: {user.id}")
        return user
    except HTTPException as e:
        logger.warning(f"[WS Auth] Token验证失败: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[WS Auth] Token验证过程中发生未预期错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证服务异常"
        ) from e