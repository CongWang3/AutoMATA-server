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


# <!-- 
# 审查上下文：
# - 设计意图：使用 FastAPI 依赖注入系统，实现声明式认证
# - 已知局限：HTTPBearer 方案较简单，生产环境可考虑 OAuth2PasswordBearer
# - 业务背景：docs/architecture/DESIGN.md - 前后端分离的认证架构
# - 测试重点：请验证各种认证场景（普通用户、管理员、禁用用户、无效token）
# -->