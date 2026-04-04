"""
认证路由：处理用户注册、登录、获取用户信息等接口
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from config.database import get_db
from config.settings import settings
from api.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from api.services.auth_service import AuthService
from api.dependencies.auth import get_current_active_user
from api.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


def _user_to_response(user: User) -> UserResponse:
    """从 ORM 显式构造响应，避免 NULL/类型边缘情况导致 model_validate 抛错。"""
    created = user.created_at
    if created is None:
        created = datetime.now(timezone.utc)
    return UserResponse(
        id=int(user.id),
        username=user.username or "",
        email=(user.email or "").strip(),
        is_active=True if user.is_active is None else bool(user.is_active),
        is_admin=bool(user.is_admin) if user.is_admin is not None else False,
        created_at=created,
        last_login_at=user.last_login_at,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册接口
    
    Args:
        request: 注册请求数据
        db: 数据库会话
        
    Returns:
        创建的用户信息
        
    Raises:
        HTTPException: 
            - 400: 用户名或邮箱已存在
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供用户自助注册功能，返回创建的用户信息
    # - 已知局限：未实现邮箱验证机制，注册即激活
    # - 业务背景：docs/api/API_SPECIFICATION.md - POST /api/v1/auth/register
    # - 测试重点：请验证用户名/邮箱唯一性约束、密码哈希存储、返回数据格式
    # -->
    
    service = AuthService(db)
    user = service.register_user(request)
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录接口
    
    Args:
        request: 登录请求数据
        db: 数据库会话
        
    Returns:
        访问令牌和用户信息
        
    Raises:
        HTTPException:
            - 401: 用户名或密码错误
            - 401: 账户被禁用
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：支持用户名或邮箱登录，返回 JWT token 和用户信息
    # - 已知局限：暂未实现登录失败次数限制和锁定机制
    # - 业务背景：docs/api/API_SPECIFICATION.md - POST /api/v1/auth/login
    # - 测试重点：请验证用户名/邮箱登录、密码验证、token 生成、最后登录时间更新
    # -->
    try:
        service = AuthService(db)
        user, access_token = service.authenticate_user(request)
        user_out = _user_to_response(user)
    except HTTPException:
        raise
    except ValidationError:
        logger.exception(
            "登录响应序列化失败: username=%s",
            request.username,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户信息格式异常，请联系管理员",
        ) from None
    except Exception as e:
        logger.exception("登录接口未预期异常: username=%s", request.username)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) if settings.DEBUG else "Internal server error",
        ) from e

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_out,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前认证用户（通过依赖注入获取）
        
    Returns:
        当前用户信息
        
    Raises:
        HTTPException:
            - 401: 未提供有效认证凭证
            - 400: 账户被禁用
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供获取当前登录用户信息的接口
    # - 已知局限：无
    # - 业务背景：docs/api/API_SPECIFICATION.md - GET /api/v1/auth/me
    # - 测试重点：请验证 Token 认证、用户信息返回格式
    # -->
    
    return current_user


@router.post("/logout")
def logout_user():
    """
    用户登出接口
    
    Returns:
        登出成功消息
        
    Note:
        客户端应清除本地存储的 token
        服务端为无状态设计，不存储 token 黑名单
    """
    # <!-- 
    # 审查上下文：
    # - 设计意图：提供登出接口，客户端负责清除 token
    # - 已知局限：JWT 为无状态 token，服务端无法强制失效，安全性依赖过期时间
    # - 业务背景：docs/api/API_SPECIFICATION.md - POST /api/v1/auth/logout
    # - 测试重点：请验证接口返回格式
    # -->
    
    return {"message": "登出成功"}
