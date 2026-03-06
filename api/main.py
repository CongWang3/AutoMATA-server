from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import training_jobs, users, file_upload
import uvicorn

app = FastAPI(
    title="AutoMATA 训练任务管理系统 API",
    description="API for managing machine learning model training tasks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allows frontend (Vue) to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Vue frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(training_jobs.router, tags=["training-tasks"])
app.include_router(users.router, tags=["users"])
app.include_router(file_upload.router, tags=["file-upload"])

# 挂载静态文件目录用于文件下载
app.mount("/files", StaticFiles(directory="/xp/www/AutoMATA/uploaded_files"), name="uploaded_files")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    from config.database import init_db
    init_db()

@app.get("/")
def read_root():
    return {"message": "AutoMATA Training Task Management API"}

@app.get("/api-docs")
def api_docs():
    return {"message": "API Documentation available at /static/api_docs.html"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)