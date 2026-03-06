"""
安全工具函数：密码加密、JWT 操作
"""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, DecodeError
from passlib.context import CryptContext
from config.settings import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    验证并解析 JWT token
    
    Args:
        token: JWT token 字符串
        
    Returns:
        解析后的载荷，如果验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token 过期
        return None
    except (jwt.InvalidTokenError, DecodeError):
        # Token 无效
        return None


def get_md5_hash(content: str) -> str:
    """
    计算 MD5 哈希值（用于文件去重）
    
    Args:
        content: 要计算哈希的内容
        
    Returns:
        32位十六进制 MD5 值
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


# <!-- 
# 审查上下文：
# - 设计意图：封装安全相关的底层操作，统一密码处理和 JWT 操作
# - 已知局限：JWT 使用 HS256 算法，生产环境可考虑 RS256
# - 业务背景：docs/architecture/DESIGN.md - 安全认证机制
# - 测试重点：请验证密码哈希的不可逆性、JWT 过期验证、MD5 哈希一致性
# -->