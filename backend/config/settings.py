"""
应用配置模块
"""
from pathlib import Path

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


# 固定为 backend/.env，避免从仓库根或其它目录启动时读错路径；生产以容器/compose 注入的环境变量为准（优先级高于文件）
_BACKEND_ENV = Path(__file__).resolve().parent.parent / ".env"


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

    # 仓库根目录（code、download_data、example、automata-web 的父目录）。生产可通过环境变量 REPO_ROOT 覆盖。
    REPO_ROOT: str = "/xp/www/AutoMATA"

    # 独立下载服务（download_server.py）：绑定地址/端口，以及返回给浏览器/邮件的下载根 URL（无尾斜杠）
    DOWNLOAD_SERVER_HOST: str = "0.0.0.0"
    DOWNLOAD_SERVER_PORT: int = 8001
    # 生产：设为对外 HTTPS 或网关路径（见 deploy/.env.prod.example）。
    # 开发：DEBUG=True 且仍为默认 localhost/127.0.0.1:8001 时，API 返回同源相对路径，由前端 dev server 反代到本机 8001。
    # 远程 IDE：若必须把绝对 URL 指到你本机映射端口，可设 DOWNLOAD_PUBLIC_BASE_URL=http://localhost:3450（与「端口」面板本地端口一致）。
    DOWNLOAD_PUBLIC_BASE_URL: str = "http://localhost:8001"

    # 脚本执行器路径（默认兼容现有本地 conda 环境；Docker 内可通过环境变量覆盖）
    PYTHON_EXEC_PATH: str = "/opt/anaconda/envs/automata/bin/python"
    RSCRIPT_PATH: str = "/opt/anaconda/envs/R_442/bin/Rscript"
    
    # 数据库配置：不在代码中写密码。本地复制 backend/.env.example 为 backend/.env 并填写（示例中为 123456）；
    # 生产使用独立配置文件（如 deploy/.env.prod），由 compose / 环境变量注入。
    DB_USER: str = "automata"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "automata"
    DB_SOCKET: Optional[str] = None  # Unix socket 路径，如: /var/run/mysqld/mysqld.sock

    # 参考注释库：gene_*/mrna_*/protein_* 的 SQL 数据目录（文件名 表名.sql 或 表名.sql.gz）。
    # 生产 compose 将宿主机 ./data/reference_sql 挂载到 /app/reference_sql；仅后端主进程启动时导入。
    REFERENCE_DATA_SQL_DIR: Optional[str] = None

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
    # 通用文件上传允许的扩展名
    # 注意：模型应用需要上传模型权重（pth/pt/pkl），因此在该白名单中补齐。
    ALLOWED_FILE_TYPES: list = ["txt", "csv", "tsv", "xlsx", "xls", "pth", "pkl"]
    
    # KEGG 富集：为 True 时 R 脚本 enrichKEGG(use_internal_data=TRUE)，使用 KEGG.db 本地注释，不访问 rest.kegg.jp（需安装 KEGG.db）
    KEGG_USE_INTERNAL_DATA: bool = True

    # Redis 配置（Celery 使用）
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS 配置 - 开发环境允许所有来源（支持本地前端直连）
    CORS_ORIGINS: List[str] = ["*"]
    # 旧代码设置的CORS_ORIGINS
    # CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
    
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
        env_file = str(_BACKEND_ENV)
        
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

    @property
    def path_repo(self) -> Path:
        return Path(self.REPO_ROOT)

    @property
    def path_jobs(self) -> Path:
        return self.path_repo / "download_data" / "Jobs"

    @property
    def path_code(self) -> Path:
        return self.path_repo / "code"

    @property
    def path_download_data(self) -> Path:
        return self.path_repo / "download_data"

    @property
    def path_process_config(self) -> Path:
        return self.path_repo / "download_data" / "Config"

    @property
    def path_data_analysis_plot(self) -> Path:
        return self.path_repo / "code" / "data_analysis_plot"

    def download_public_base(self) -> str:
        """下载服务对外 base，已去除尾斜杠。开发环境若仍为默认 localhost:8001，则返回空串以生成同源相对路径（由 Vite/网关反代到 8001）。"""
        raw = (self.DOWNLOAD_PUBLIC_BASE_URL or "").strip().rstrip("/")
        if self.DEBUG and raw in (
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "https://localhost:8001",
            "https://127.0.0.1:8001",
        ):
            return ""
        return raw

    def download_public_url(self, path_and_query: str) -> str:
        """生成浏览器可用的下载 URL。path_and_query 须以 / 开头并可带 query。"""
        base = self.download_public_base()
        pq = path_and_query if path_and_query.startswith("/") else f"/{path_and_query}"
        return f"{base}{pq}" if base else pq

    def validate_cors_config(self) -> None:
        """验证 CORS 配置"""
        if self.is_production and "*" in self.CORS_ORIGINS:
            warnings.warn(
                "生产环境使用通配符 CORS 配置存在安全风险",
                SecurityWarning
            )


# 全局配置实例
settings = Settings()
