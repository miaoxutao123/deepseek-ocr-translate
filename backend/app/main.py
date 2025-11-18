from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import time

from .config import settings
from .database import init_db
from .routers import auth, ocr, translate, correction, history

# 配置日志
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="OCR and Translation System with AI-powered corrections",
    version="1.0.0"
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求
    logger.info(f"📥 收到请求: {request.method} {request.url.path}")
    if request.query_params:
        logger.info(f"   查询参数: {dict(request.query_params)}")

    # 处理请求
    response = await call_next(request)

    # 记录响应
    elapsed_time = time.time() - start_time
    logger.info(f"📤 响应: {request.method} {request.url.path} - 状态码: {response.status_code} - 耗时: {elapsed_time:.3f}秒")

    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(ocr.router)
app.include_router(translate.router)
app.include_router(correction.router)
app.include_router(history.router)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    logger.info("=" * 60)
    logger.info("应用启动中...")
    logger.info(f"应用名称: {settings.APP_NAME}")
    logger.info(f"监听地址: {settings.HOST}:{settings.PORT}")
    logger.info("=" * 60)

    init_db()
    logger.info("数据库初始化完成")

    logger.info("✅ 应用启动完成")
    logger.info("=" * 60)


@app.get("/")
def root():
    return {"message": "OCR and Translate API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
