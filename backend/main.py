"""
AutoMATA 后端应用入口
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

# 导入路由
from api.routers import auth, files, chunked_download

# 导入定时任务
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from config.database import get_db
from api.services.file_service import FileUploadService
from api.models.user import User

# 配置日志到项目目录
import os
from pathlib import Path

# 创建日志目录
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "fastapi.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AutoMATA 生物信息学多组学分析平台 API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
# 审查上下文：
# - 设计意图：使用配置化的 CORS 来源，避免生产环境使用 "*" 带来的安全问题
# - 已知局限：开发环境默认允许 localhost:5173（Vue Vite 默认端口）
# - 业务背景：docs/architecture/DESIGN.md - 前后端分离架构需要跨域配置
# - 测试重点：请验证不同环境下 CORS 配置是否正确，特别是前端携带认证请求时
# 增加请求体大小限制以支持大文件上传
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

# 注册路由
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(chunked_download.router, prefix="/api/v1/files", tags=["分片下载"])


# 创建全局调度器
scheduler = BackgroundScheduler()

def cleanup_marked_files_task():
    """定时清理标记删除的文件（带重试机制）"""
    # <!-- 
    # 审查上下文：
    # - 设计意图：实现带重试机制的定时清理任务，提高任务执行可靠性
    # - 已知局限：使用简单的退避重试策略，复杂场景可考虑专业任务队列
    # - 业务背景：确保文件系统垃圾回收的稳定执行
    # - 测试重点：请验证重试逻辑、失败告警、任务状态监控
    # -->
    
    import time
    import logging
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        db_gen = None
        try:
            # 获取数据库会话
            db_gen = get_db()
            db = next(db_gen)
            
            # 查找系统清理用户
            system_user = db.query(User).filter(User.username == "system_cleaner").first()
            if not system_user:
                logger.error("系统清理用户不存在")
                return
                
            # 创建文件服务实例
            file_service = FileUploadService(db, system_user)
            
            result = file_service.cleanup_marked_files()
            logger.info(f"定时清理任务完成: {result}")
            return  # 成功执行后退出
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                # 指数退避：1秒, 2秒, 4秒
                sleep_time = 2 ** (retry_count - 1)
                logger.warning(f"定时清理任务第{retry_count}次失败，{sleep_time}秒后重试: {e}")
                time.sleep(sleep_time)
            else:
                logger.error(f"定时清理任务连续失败{max_retries}次，需要人工干预: {e}")
                # 这里可以添加告警通知机制
        finally:
            # 确保数据库会话正确关闭
            if db_gen is not None:
                db_gen.close()

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("=" * 60)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"环境：{'开发' if settings.DEBUG else '生产'}")
    logger.info(f"CORS 配置：{settings.CORS_ORIGINS}")
    logger.info(f"API 文档：http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 60)
    
    # 验证 CORS 配置
    if settings.is_production:
        logger.warning(f"生产环境 CORS 配置：{settings.CORS_ORIGINS}")
        settings.validate_cors_config()
    
    # 启动定时清理任务（每小时执行一次）
    scheduler.add_job(
        cleanup_marked_files_task,
        IntervalTrigger(hours=1),
        id='file_cleanup_job',
        name='文件清理任务',
        replace_existing=True
    )
    scheduler.start()
    logger.info("定时清理任务已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    scheduler.shutdown()
    logger.info(f"{settings.APP_NAME} 已关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# 审查上下文：
# - 设计意图：先创建基础框架，后续逐步添加路由模块
# - 已知局限：CORS 设置为允许所有来源，生产环境需要修改为具体域名
# - 业务背景：docs/architecture/DESIGN.md - 前后端分离架构
# - 测试重点：请重点关注 CORS 配置和健康检查接口

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False  # 禁用文件重载避免监视器冲突
    )
