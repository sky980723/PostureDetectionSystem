"""
FastAPI 主应用

整合所有 API 端点和 WebSocket 连接
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.deps import (
    get_pose_detector,
    get_posture_analyzer,
    get_alert_manager,
    cleanup_detector
)
from src.api.routes import records, statistics, settings
from src.api.websocket.posture_stream import handle_posture_websocket
from src.models.database import init_db, close_db
from config.api_settings import api_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO if not api_settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 应用生命周期管理
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化资源，关闭时清理资源
    """
    # 启动
    logger.info("Initializing application...")

    # 初始化数据库
    await init_db()
    logger.info("Database initialized")

    yield

    # 关闭
    logger.info("Shutting down application...")

    # 清理资源
    cleanup_detector()
    await close_db()
    logger.info("Resources cleaned up")


# ============================================================================
# 创建应用
# ============================================================================

app = FastAPI(
    title=api_settings.app_name,
    version=api_settings.app_version,
    debug=api_settings.debug,
    lifespan=lifespan
)


# ============================================================================
# CORS 中间件
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_origins,
    allow_credentials=api_settings.cors_allow_credentials,
    allow_methods=api_settings.cors_allow_methods,
    allow_headers=api_settings.cors_allow_headers,
)


# ============================================================================
# 注册路由
# ============================================================================

# REST API 路由
app.include_router(records.router)
app.include_router(statistics.router)
app.include_router(settings.router)


# ============================================================================
# WebSocket 端点
# ============================================================================

@app.websocket("/ws/posture")
async def websocket_posture_endpoint(
    websocket: WebSocket,
    pose_detector = Depends(get_pose_detector),
    posture_analyzer = Depends(get_posture_analyzer),
    alert_manager = Depends(get_alert_manager)
):
    """
    WebSocket 端点：实时姿态检测

    接收视频帧，返回姿态分析结果和提醒
    """
    await handle_posture_websocket(
        websocket=websocket,
        pose_detector=pose_detector,
        posture_analyzer=posture_analyzer,
        alert_manager=alert_manager
    )


# ============================================================================
# 根路径和健康检查
# ============================================================================

@app.get("/")
async def root():
    """根路径 - API 信息"""
    return {
        "name": api_settings.app_name,
        "version": api_settings.app_version,
        "status": "running",
        "endpoints": {
            "websocket": "/ws/posture",
            "records": "/api/records",
            "statistics": "/api/statistics",
            "settings": "/api/settings"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: 实际检查数据库连接
        "detector": "ready"
    }


# ============================================================================
# 全局异常处理
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if api_settings.debug else "An unexpected error occurred"
        }
    )


# ============================================================================
# 开发服务器启动（仅用于测试）
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=api_settings.debug,
        log_level="debug" if api_settings.debug else "info"
    )
