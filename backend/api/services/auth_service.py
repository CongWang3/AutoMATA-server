"""
认证服务：处理用户注册、登录、Token 验证等业务逻辑
"""
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from api.models.user import User
from api.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from api.utils.security import get_password_hash, verify_password, create_access_token
from config.settings import settings

logger = logging.getLogger(__name__)


def mask_sensitive_info(info: str, show_chars: int = 3) -> str:
    """
    对敏感信息进行脱敏处理
    
    Args:
        info: 需要脱敏的信息
        show_chars: 保留的字符数
        
    Returns:
        脱敏后的信息
    """
    if not info:
        return ""
    if len(info) <= show_chars * 2:
        return "*" * len(info)
    return info[:show_chars] + "*" * (len(info) - show_chars * 2) + info[-show_chars:]

def validate_password_complexity(password: str) -> bool:
    """
    验证密码复杂度
    要求：至少8位，包含大小写字母和数字
    """
    if len(password) < 8:
        return False
    
    # 使用单个正则表达式检查所有要求，提高性能
    # ^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$
    # - ^ : 字符串开始
    # - (?=.*[a-z]) : 至少包含一个小写字母
    # - (?=.*[A-Z]) : 至少包含一个大写字母  
    # - (?=.*\d) : 至少包含一个数字
    # - .{8,} : 至少8个字符
    # - $ : 字符串结束
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    return bool(re.match(pattern, password))

# <!-- 
# 审查上下文：
# - 设计意图：优化密码验证性能，使用单个正则表达式替代多次匹配
# - 已知局限：正则表达式虽然高效但可读性略差，已在注释中说明
# - 业务背景：用户认证安全策略的性能优化
# - 测试重点：请验证各种密码组合的验证准确性，包括边界情况
# -->


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # <!-- 
    # 审查上下文：
    # - 设计意图：将认证业务逻辑集中到服务层，便于复用和测试
    # - 已知局限：暂未实现刷新令牌机制和登录失败次数限制
    # - 业务背景：docs/api/API_SPECIFICATION.md - 用户认证接口规范
    # - 测试重点：请关注用户名/邮箱冲突处理、密码验证、token 生成与验证、用户状态检查
    # -->
    
    def register_user(self, request: UserRegisterRequest) -> User:
        """
        用户注册
        
        Args:
            request: 注册请求数据
            
        Returns:
            创建的用户对象
            
        Raises:
            HTTPException: 用户名或邮箱已存在时抛出 400 错误
        """
        logger.info(f"开始注册用户: username={mask_sensitive_info(request.username)}, email={mask_sensitive_info(request.email, 2)}")
        
        # 合并查询检查用户名和邮箱唯一性，减少数据库访问次数
        existing_user = self.db.query(User).filter(
            (User.username == request.username) | (User.email == request.email)
        ).first()
        
        if existing_user:
            if existing_user.username == request.username:
                logger.warning(f"注册失败 - 用户名已存在: {mask_sensitive_info(request.username)}")
                detail = "用户名已存在"
            else:
                logger.warning(f"注册失败 - 邮箱已被注册: {mask_sensitive_info(request.email, 2)}")
                detail = "邮箱已被注册"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )
        
        # 验证密码复杂度
        if not validate_password_complexity(request.password):
            logger.warning(f"注册失败 - 密码不符合复杂度要求: {mask_sensitive_info(request.username)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码必须至少8位，且包含大小写字母和数字"
            )
        
        # 创建新用户
        logger.info("正在创建新用户记录")
        user = User(
            username=request.username,
            email=request.email,
            password_hash=get_password_hash(request.password)
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"用户注册成功: user_id={user.id}, username={mask_sensitive_info(user.username)}")
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"用户注册数据库错误: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户注册失败，请稍后重试"
            ) from e
    
    def authenticate_user(self, request: UserLoginRequest) -> Tuple[User, str]:
        """
        用户认证（登录）
        
        Args:
            request: 登录请求数据
            
        Returns:
            (用户对象, 访问令牌)
            
        Raises:
            HTTPException: 用户不存在或密码错误时抛出 401 错误
        """
        logger.info(f"用户尝试登录: {mask_sensitive_info(request.username)}")
        
        # 查找用户（支持用户名或邮箱登录）
        user = self.db.query(User).filter(
            (User.username == request.username) | (User.email == request.username)
        ).first()
        
        if not user:
            logger.warning(f"登录失败 - 用户不存在: {mask_sensitive_info(request.username)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"登录失败 - 账户被禁用: user_id={user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 验证密码
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"登录失败 - 密码错误: user_id={user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        
        # 生成访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        logger.info(f"用户登录成功: user_id={user.id}, username={mask_sensitive_info(user.username)}")
        return user, access_token
    
    def get_current_user(self, token: str) -> User:
        """
        根据 Token 获取当前用户
        
        Args:
            token: JWT 访问令牌
            
        Returns:
            用户对象
            
        Raises:
            HTTPException: Token 无效或用户不存在时抛出 401 错误
        """
        from api.utils.security import verify_token
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"开始验证token: {token[:20]}...")
        payload = verify_token(token)
        logger.info(f"Token解析结果: {payload}")
        
        if payload is None:
            logger.error("Token验证失败：payload为None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: str = payload.get("sub")
        logger.info(f"从payload中提取用户ID: {user_id}")
        
        if user_id is None:
            logger.error("Token验证失败：sub字段为空")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"查询用户ID: {user_id}")
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        logger.info(f"查询结果: {user}")
        
        if user is None:
            logger.error(f"用户不存在: ID={user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.error(f"账户被禁用: user_id={user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"认证成功: user_id={user.id}")
        return user


# <!-- 
# 审查上下文：
# - 设计意图：将认证业务逻辑集中到服务层，便于复用和测试
# - 已知局限：暂未实现刷新令牌机制，后续可添加
# - 业务背景：docs/api/API_SPECIFICATION.md - 用户认证接口规范
# - 测试重点：请关注用户名/邮箱冲突处理、密码验证、token 生成与验证、用户状态检查
# -->