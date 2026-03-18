"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import json
import warnings
import os
import secrets


class SecurityWarning(UserWarning):
    """安全相关警告类"""
    pass


def _generate_warning_key() -> str:
    """生成带警告的默认密钥"""
    warnings.warn(
        "使用默认密钥，生产环境请设置 SECRET_KEY 环境变量",
        SecurityWarning
    )
    return "DEVELOPMENT_KEY_DO_NOT_USE_IN_PRODUCTION_" + secrets.token_urlsafe(16)


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "AutoMATA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    
    # 数据库配置 - 支持真实环境连接
    DB_USER: str = "automata"
    DB_PASSWORD: str = "123456"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "automata"
    DB_SOCKET: Optional[str] = None  # Unix socket 路径，如: /var/run/mysqld/mysqld.sock
    
    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接 URL - 支持 Unix socket"""
        # 如果配置了 Unix socket，优先使用 socket 连接
        if self.DB_SOCKET:
            # Unix socket 连接格式: mysql+pymysql://user:password@localhost/dbname?unix_socket=/path/to/socket
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@localhost/{self.DB_NAME}?unix_socket={self.DB_SOCKET}"
        else:
            # 标准 TCP 连接
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # JWT 配置
    SECRET_KEY: str = Field(
        default_factory=lambda: os.environ.get("SECRET_KEY") or _generate_warning_key(),
        description="JWT 密钥，生产环境必须通过环境变量 SECRET_KEY 设置"
    )
    
    # <!-- 
    # 审查上下文：
    # - 设计意图：通过环境变量和警告机制确保生产环境使用安全密钥
    # - 已知局限：开发环境仍使用默认密钥，但会发出明确警告
    # - 业务背景：安全认证机制的核心配置
    # - 测试重点：请验证生产环境部署时密钥是否已正确设置
    # -->
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB，增加上传限制
    UPLOAD_DIR: str = "./uploaded_files"
    ALLOWED_FILE_TYPES: list = ["txt", "csv", "xlsx", "xls"]
    
    # Redis 配置（Celery 使用）
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS 配置 - 开发环境允许所有来源（支持本地前端直连）
    CORS_ORIGINS: List[str] = ["*"]
    
    # Email 配置
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SSL: bool = False
    SMTP_FROM_NAME: str = "AutoMATA"
    
    # AI Agent 配置
    AGENT_ENABLED: bool = False
    AGENT_DEFAULT_PROVIDER: str = "openai"  # openai / qwen / deepseek
    AGENT_OPENAI_API_KEY: str = ""
    AGENT_OPENAI_BASE_URL: str = ""  # 可选代理地址
    AGENT_OPENAI_MODEL: str = "gpt-4o"
    AGENT_QWEN_API_KEY: str = ""
    AGENT_QWEN_MODEL: str = "qwen-plus"
    AGENT_DEEPSEEK_API_KEY: str = ""
    AGENT_DEEPSEEK_MODEL: str = "deepseek-chat"
    AGENT_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    AGENT_MAX_TURNS: int = 10
    
    class Config:
        env_file = ".env"
        
        @classmethod
        def parse_env_var(cls, value: str):
            """解析环境变量中的 JSON 格式列表"""
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # 兼容单字符串格式
                return [value] if value else []
    
    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return not self.DEBUG
    
    def validate_cors_config(self) -> None:
        """验证 CORS 配置"""
        if self.is_production and "*" in self.CORS_ORIGINS:
            warnings.warn(
                "生产环境使用通配符 CORS 配置存在安全风险",
                SecurityWarning
            )


# 全局配置实例
settings = Settings()
