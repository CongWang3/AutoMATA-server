"""
AutoMATA 后端应用入口
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
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
        reload=settings.DEBUG
    )
