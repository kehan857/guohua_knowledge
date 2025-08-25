"""
熵变智元AI销售助手后端服务 - 集成版本
FastAPI主应用入口，包含外部服务集成和监控
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from typing import Optional

# 内部模块导入
from app.core.config import settings
from app.core.startup import lifespan, get_system_health
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
from app.api.v1.integrations import router as integrations_router
from app.api.v1.monitoring import router as monitoring_router

# WebSocket路由
from app.api.ws.chat import router as ws_chat_router

# 设置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 创建FastAPI应用实例
app = FastAPI(
    title="熵变智元AI销售助手API",
    description="基于AI的智能销售助手后端服务，包含外部服务集成和监控",
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
    """系统健康检查"""
    health_data = await get_system_health()
    return {
        "status": "ok" if health_data["healthy"] else "error",
        "version": "1.0.0",
        "health": health_data
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
            "gewe_endpoint": getattr(settings, 'GEWE_BASE_URL', 'not_configured'),
            "fastgpt_endpoint": getattr(settings, 'FASTGPT_BASE_URL', 'not_configured')
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
    integrations_router,
    prefix=f"{api_v1_prefix}/integrations",
    tags=["外部服务集成"]
)

app.include_router(
    monitoring_router,
    prefix=f"{api_v1_prefix}/monitoring",
    tags=["系统监控"]
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
                "base_url": getattr(settings, 'GEWE_BASE_URL', 'not_configured'),
                "api_key_masked": "configured" if getattr(settings, 'GEWE_API_KEY', None) else "not_configured"
            },
            "fastgpt_config": {
                "base_url": getattr(settings, 'FASTGPT_BASE_URL', 'not_configured'),
                "api_key_masked": "configured" if getattr(settings, 'FASTGPT_API_KEY', None) else "not_configured"
            }
        }


if __name__ == "__main__":
    import uvicorn
    
    # 运行服务器
    uvicorn.run(
        "main_integrated:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )

