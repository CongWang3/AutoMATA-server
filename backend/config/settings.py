"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import json
import warnings


class SecurityWarning(UserWarning):
    """安全相关警告类"""
    pass


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "AutoMATA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DB_USER: str = "automata"
    DB_PASSWORD: str = "123456"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "automata"
    
    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接 URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "./uploaded_files"
    ALLOWED_FILE_TYPES: list = ["txt", "csv", "xlsx", "xls"]
    
    # Redis 配置（Celery 使用）
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS 配置 - 支持多环境
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
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
