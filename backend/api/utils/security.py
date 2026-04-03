"""
安全工具模块：提供统一的安全验证和防护功能

包含路径验证、输入清理、密码加密、JWT操作等通用安全功能。
"""
import logging
import re
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, DecodeError
from passlib.context import CryptContext
from config.settings import settings
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

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
        JWT 令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码访问令牌
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        解码后的数据字典
        
    Raises:
        HTTPException: 当令牌无效或过期时
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, DecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_md5_hash(content: str) -> str:
    """
    计算字符串的 MD5 哈希值
    
    Args:
        content: 要计算哈希的字符串
        
    Returns:
        MD5 哈希值（十六进制字符串）
    """
    return hashlib.md5(content.encode()).hexdigest()


def verify_token(token: str) -> Optional[dict]:
    """
    验证并解码访问令牌
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        解码后的载荷字典，如果验证失败返回None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (ExpiredSignatureError, InvalidTokenError, DecodeError):
        return None


class SecurityValidator:
    """安全验证器类"""
    
    @classmethod
    def allowed_base_paths(cls) -> list:
        """允许的基础目录（防止路径遍历）；仓库根目录来自 settings.REPO_ROOT。"""
        return [str(settings.path_repo), "/tmp", "/var/tmp"]
    
    # 危险字符模式
    DANGEROUS_PATTERNS = [
        '..', '~', ';', '&', '|', '`', '$', 
        '{', '}', '\n', '\r', '\t', '\\'
    ]
    
    @classmethod
    def validate_file_path(cls, file_path: str, allowed_extensions: Optional[list] = None) -> Path:
        """
        验证文件路径的安全性
        
        Args:
            file_path: 待验证的文件路径
            allowed_extensions: 允许的文件扩展名列表（可选）
            
        Returns:
            验证通过的Path对象
            
        Raises:
            ValueError: 当路径不安全或无效时
        """
        # <!-- 
        # 审查上下文：
        # - 设计意图：提供集中化的文件路径安全验证，避免重复实现
        # - 已知局限：ALLOWED_BASE_PATHS目前是硬编码的，后续可配置化
        # - 业务背景：确保所有文件操作都在安全范围内进行
        # - 测试重点：验证各种路径遍历攻击向量的防御能力
        # -->
        
        if not file_path:
            raise ValueError("文件路径不能为空")
            
        # 基本格式检查
        if not re.match(r'^[a-zA-Z0-9/_\-\.]+$', file_path):
            raise ValueError("文件路径包含非法字符")
            
        # 检查危险模式
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern in file_path:
                logger.warning(f"检测到潜在危险字符: {pattern} in {file_path}")
                raise ValueError(f"文件路径包含非法字符序列: {pattern}")
                
        try:
            # 解析并规范化路径
            path = Path(file_path).resolve()
            
            # 检查是否在允许的目录范围内
            is_allowed = False
            for base_path in cls.allowed_base_paths():
                base = Path(base_path).resolve()
                if str(path).startswith(str(base)):
                    is_allowed = True
                    break
                    
            if not is_allowed:
                logger.warning(f"路径超出允许范围: {file_path}")
                raise ValueError("文件路径超出系统允许范围")
                
            # 检查文件是否存在且是文件
            if not path.exists():
                raise ValueError("指定的文件不存在")
                
            if not path.is_file():
                raise ValueError("指定的路径不是文件")
                
            # 检查文件扩展名（如果指定了允许的扩展名）
            if allowed_extensions:
                suffix = path.suffix.lower()
                if suffix not in [ext.lower() for ext in allowed_extensions]:
                    raise ValueError(f"不允许的文件类型: {suffix}")
                    
            logger.debug(f"文件路径验证通过: {path}")
            return path
            
        except Exception as e:
            logger.error(f"文件路径验证失败: {file_path}, error: {e}")
            raise ValueError(f"无效的文件路径: {str(e)}")

    @classmethod
    def sanitize_input(cls, user_input: str, max_length: int = 1000) -> str:
        """
        清理用户输入，移除潜在危险字符
        
        Args:
            user_input: 用户输入的字符串
            max_length: 最大允许长度
            
        Returns:
            清理后的安全字符串
        """
        # <!-- 
        # 审查上下文：
        # - 设计意图：提供通用的输入清理功能，防止XSS等注入攻击
        # - 已知局限：清理规则可能需要根据不同场景调整
        # - 业务背景：为所有用户输入提供基础的安全防护
        # - 测试重点：验证各种恶意输入的清理效果
        # -->
        
        if not user_input:
            return ""
            
        if len(user_input) > max_length:
            logger.warning(f"输入长度超限: {len(user_input)} > {max_length}")
            user_input = user_input[:max_length]
            
        # 移除危险字符
        for pattern in cls.DANGEROUS_PATTERNS:
            user_input = user_input.replace(pattern, '')
            
        # 移除HTML标签
        user_input = re.sub(r'<[^>]+>', '', user_input)
        
        return user_input.strip()

    @classmethod
    def validate_model_parameters(cls, parameters: dict) -> dict:
        """
        验证模型训练参数的安全性
        
        Args:
            parameters: 训练参数字典
            
        Returns:
            验证后的参数字典
            
        Raises:
            ValueError: 当参数不安全时
        """
        # <!-- 
        # 审查上下文：
        # - 设计意图：专门针对模型训练参数进行安全验证
        # - 已知局限：验证规则可能需要根据具体模型要求调整
        # - 业务背景：防止恶意参数影响训练过程或系统安全
        # - 测试重点：验证各种边界参数值的安全性
        # -->
        
        if not isinstance(parameters, dict):
            raise ValueError("参数必须是字典类型")
            
        # 检查必需参数
        required_params = ['strategy', 'epochs', 'batch_size', 'learning_rate']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"缺少必需参数: {param}")
                
        # 验证数值参数范围
        numeric_params = {
            'epochs': (1, 1000),
            'batch_size': (1, 1024),
            'learning_rate': (0.0001, 1.0),
            'kfold': (2, 10)
        }
        
        for param, (min_val, max_val) in numeric_params.items():
            if param in parameters:
                try:
                    value = float(parameters[param])
                    if not (min_val <= value <= max_val):
                        raise ValueError(f"参数 {param} 超出有效范围 [{min_val}, {max_val}]")
                except (ValueError, TypeError):
                    raise ValueError(f"参数 {param} 必须是数值类型")
                    
        # 验证策略参数
        valid_strategies = ['split', 'upload', 'kfold']
        strategy = parameters.get('strategy')
        if strategy not in valid_strategies:
            raise ValueError(f"strategy 必须是 {valid_strategies} 中的一个")
            
        # 清理字符串参数
        string_params = ['loss_function', 'optimizer_function']
        for param in string_params:
            if param in parameters and isinstance(parameters[param], str):
                parameters[param] = cls.sanitize_input(parameters[param], 50)
                
        return parameters


# 创建全局验证器实例
security_validator = SecurityValidator()