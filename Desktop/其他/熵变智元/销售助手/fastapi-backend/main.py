"""
熵变智元AI销售助手后端服务
FastAPI主应用入口
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Optional

# 内部模块导入
from app.core.config import settings
from app.core.database import engine, create_all_tables
from app.core.redis import redis_client
from app.core.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware
)
from app.api.deps import get_current_user
from app.models.user import User

# API路由导入
from app.api.v1.auth import router as auth_router
from app.api.v1.devices import router as devices_router
from app.api.v1.chat import router as chat_router
from app.api.v1.sop import router as sop_router
from app.api.v1.cost import router as cost_router
from app.api.v1.materials import router as materials_router
from app.api.v1.admin import router as admin_router

# WebSocket路由
from app.api.ws.chat import router as ws_chat_router

# 外部服务
from app.services.gewe_service import GeWeService
from app.services.ai_service import AIService
from app.services.websocket_manager import WebSocketManager

# 任务调度
from app.tasks.scheduler import start_scheduler, stop_scheduler

# 设置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动熵变智元AI销售助手后端服务...")
    
    try:
        # 初始化数据库
        logger.info("📊 初始化数据库连接...")
        await create_all_tables()
        
        # 初始化Redis连接
        logger.info("🔴 初始化Redis连接...")
        await redis_client.ping()
        
        # 初始化外部服务
        logger.info("🔌 初始化外部服务连接...")
        gewe_service = GeWeService()
        ai_service = AIService()
        
        # 测试外部服务连接
        await gewe_service.test_connection()
        await ai_service.test_connection()
        
        # 启动WebSocket管理器
        logger.info("🌐 启动WebSocket管理器...")
        websocket_manager = WebSocketManager()
        app.state.websocket_manager = websocket_manager
        
        # 启动任务调度器
        logger.info("⏰ 启动任务调度器...")
        await start_scheduler()
        
        logger.info("✅ 所有服务启动成功!")
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {str(e)}")
        raise
    
    yield
    
    # 关闭时清理资源
    logger.info("🛑 正在关闭服务...")
    try:
        await stop_scheduler()
        await redis_client.close()
        logger.info("✅ 服务已安全关闭")
    except Exception as e:
        logger.error(f"❌ 服务关闭时发生错误: {str(e)}")


# 创建FastAPI应用实例
app = FastAPI(
    title="熵变智元AI销售助手API",
    description="基于AI的智能销售助手后端服务",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 添加中间件
# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可信主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# 自定义中间件
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": int(time.time())
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "timestamp": int(time.time())
        }
    )


# 根路径
@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "service": "熵变智元AI销售助手",
        "version": "1.0.0",
        "status": "running",
        "timestamp": int(time.time())
    }


# 健康检查端点
@app.get("/health")
async def health_check():
    """详细健康检查"""
    checks = {}
    
    try:
        # 检查数据库连接
        from app.core.database import get_db
        async with get_db() as db:
            await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    try:
        # 检查Redis连接
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    try:
        # 检查外部服务
        gewe_service = GeWeService()
        ai_service = AIService()
        
        await gewe_service.test_connection()
        checks["gewe"] = "healthy"
        
        await ai_service.test_connection()
        checks["ai_service"] = "healthy"
        
    except Exception as e:
        checks["external_services"] = f"unhealthy: {str(e)}"
    
    # 判断整体状态
    is_healthy = all("healthy" in status for status in checks.values())
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "checks": checks,
        "timestamp": int(time.time())
    }


# 系统信息端点
@app.get("/info")
async def system_info(current_user: User = Depends(get_current_user)):
    """系统信息（需要认证）"""
    import psutil
    import platform
    
    return {
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent
        },
        "application": {
            "name": "熵变智元AI销售助手",
            "version": "1.0.0",
            "debug_mode": settings.DEBUG,
            "environment": settings.ENVIRONMENT
        },
        "services": {
            "database_url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else "masked",
            "redis_url": settings.REDIS_URL.split('@')[1] if '@' in settings.REDIS_URL else "masked",
            "gewe_endpoint": settings.GEWE_API_ENDPOINT,
            "ai_service_endpoint": settings.AI_SERVICE_ENDPOINT
        }
    }


# 注册API路由
# v1 API路由
api_v1_prefix = "/api/v1"

app.include_router(
    auth_router,
    prefix=f"{api_v1_prefix}/auth",
    tags=["认证"]
)

app.include_router(
    devices_router,
    prefix=f"{api_v1_prefix}/devices",
    tags=["设备管理"]
)

app.include_router(
    chat_router,
    prefix=f"{api_v1_prefix}/chat",
    tags=["聊天管理"]
)

app.include_router(
    sop_router,
    prefix=f"{api_v1_prefix}/sop",
    tags=["SOP任务"]
)

app.include_router(
    cost_router,
    prefix=f"{api_v1_prefix}/cost",
    tags=["算力管理"]
)

app.include_router(
    materials_router,
    prefix=f"{api_v1_prefix}/materials",
    tags=["物料管理"]
)

app.include_router(
    admin_router,
    prefix=f"{api_v1_prefix}/admin",
    tags=["系统管理"]
)

# WebSocket路由
app.include_router(
    ws_chat_router,
    prefix="/ws",
    tags=["WebSocket"]
)


# 开发环境特殊端点
if settings.DEBUG:
    @app.get("/debug/routes")
    async def debug_routes():
        """调试：显示所有路由"""
        routes = []
        for route in app.routes:
            if hasattr(route, 'methods'):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name
                })
        return {"routes": routes}
    
    @app.get("/debug/config")
    async def debug_config(current_user: User = Depends(get_current_user)):
        """调试：显示配置信息（需要管理员权限）"""
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        return {
            "database_url": settings.DATABASE_URL,
            "redis_url": settings.REDIS_URL,
            "gewe_config": {
                "endpoint": settings.GEWE_API_ENDPOINT,
                "token_masked": settings.GEWE_TOKEN_ID[:8] + "..." if settings.GEWE_TOKEN_ID else None
            },
            "ai_config": {
                "endpoint": settings.AI_SERVICE_ENDPOINT,
                "key_masked": settings.AI_SERVICE_KEY[:8] + "..." if settings.AI_SERVICE_KEY else None
            }
        }


if __name__ == "__main__":
    import uvicorn
    
    # 运行服务器
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )

