"""
应用启动配置
负责初始化外部服务连接和监控服务
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.services.integration_monitor import integration_monitor
from app.services.gewe_service import gewe_service  
from app.services.fastgpt_service import fastgpt_service
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    
    # 启动时的初始化
    logger.info("开始初始化应用...")
    
    try:
        # 1. 初始化WebSocket管理器
        logger.info("初始化WebSocket管理器...")
        # WebSocket管理器已经在导入时初始化
        
        # 2. 初始化通知服务
        logger.info("初始化通知服务...")
        # 通知服务已经在导入时初始化
        
        # 3. 测试外部服务连接
        logger.info("测试外部服务连接...")
        await _test_external_services()
        
        # 4. 启动监控服务
        logger.info("启动集成监控服务...")
        await integration_monitor.start_monitoring()
        
        # 5. 初始化定时任务
        logger.info("启动后台任务...")
        await _start_background_tasks()
        
        logger.info("应用初始化完成！")
        
        yield  # 应用运行期间
        
    except Exception as e:
        logger.error(f"应用初始化失败: {str(e)}")
        raise
    
    finally:
        # 关闭时的清理
        logger.info("开始关闭应用...")
        
        try:
            # 1. 停止监控服务
            logger.info("停止监控服务...")
            await integration_monitor.stop_monitoring()
            
            # 2. 停止后台任务
            logger.info("停止后台任务...")
            await _stop_background_tasks()
            
            # 3. 清理WebSocket连接
            logger.info("清理WebSocket连接...")
            await websocket_manager.disconnect_all()
            
            logger.info("应用关闭完成！")
            
        except Exception as e:
            logger.error(f"应用关闭异常: {str(e)}")


async def _test_external_services():
    """测试外部服务连接"""
    try:
        # 测试GeWe服务连接
        if settings.GEWE_BASE_URL:
            logger.info("测试GeWe服务连接...")
            gewe_health = await gewe_service.health_check()
            if gewe_health["healthy"]:
                logger.info("✅ GeWe服务连接正常")
            else:
                logger.warning(f"⚠️ GeWe服务连接异常: {gewe_health.get('error', '未知错误')}")
        else:
            logger.warning("⚠️ GeWe服务URL未配置，跳过连接测试")
        
        # 测试FastGPT服务连接
        if settings.FASTGPT_BASE_URL:
            logger.info("测试FastGPT服务连接...")
            fastgpt_health = await fastgpt_service.health_check()
            if fastgpt_health["healthy"]:
                logger.info("✅ FastGPT服务连接正常")
            else:
                logger.warning(f"⚠️ FastGPT服务连接异常: {fastgpt_health.get('error', '未知错误')}")
        else:
            logger.warning("⚠️ FastGPT服务URL未配置，跳过连接测试")
        
    except Exception as e:
        logger.error(f"测试外部服务连接失败: {str(e)}")


# 全局后台任务存储
_background_tasks = []


async def _start_background_tasks():
    """启动后台任务"""
    try:
        # 1. WebSocket心跳任务
        websocket_heartbeat_task = asyncio.create_task(_websocket_heartbeat_task())
        _background_tasks.append(("websocket_heartbeat", websocket_heartbeat_task))
        
        # 2. 服务状态检查任务
        service_check_task = asyncio.create_task(_service_health_check_task())
        _background_tasks.append(("service_check", service_check_task))
        
        # 3. 缓存清理任务
        cache_cleanup_task = asyncio.create_task(_cache_cleanup_task())
        _background_tasks.append(("cache_cleanup", cache_cleanup_task))
        
        # 4. 统计数据聚合任务
        stats_aggregation_task = asyncio.create_task(_stats_aggregation_task())
        _background_tasks.append(("stats_aggregation", stats_aggregation_task))
        
        logger.info(f"已启动 {len(_background_tasks)} 个后台任务")
        
    except Exception as e:
        logger.error(f"启动后台任务失败: {str(e)}")


async def _stop_background_tasks():
    """停止后台任务"""
    try:
        logger.info(f"正在停止 {len(_background_tasks)} 个后台任务...")
        
        for task_name, task in _background_tasks:
            try:
                if not task.done():
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"任务 {task_name} 停止超时")
                    except asyncio.CancelledError:
                        logger.info(f"任务 {task_name} 已取消")
                
            except Exception as e:
                logger.error(f"停止任务 {task_name} 失败: {str(e)}")
        
        _background_tasks.clear()
        logger.info("所有后台任务已停止")
        
    except Exception as e:
        logger.error(f"停止后台任务失败: {str(e)}")


async def _websocket_heartbeat_task():
    """WebSocket心跳任务"""
    logger.info("WebSocket心跳任务已启动")
    
    try:
        while True:
            try:
                # 清理死连接
                disconnected_count = await websocket_manager.cleanup_dead_connections()
                if disconnected_count > 0:
                    logger.info(f"清理了 {disconnected_count} 个死连接")
                
                # 发送心跳包
                await websocket_manager.broadcast({
                    "type": "heartbeat",
                    "timestamp": asyncio.get_event_loop().time()
                })
                
            except Exception as e:
                logger.error(f"WebSocket心跳任务异常: {str(e)}")
            
            # 每30秒执行一次
            await asyncio.sleep(30)
    
    except asyncio.CancelledError:
        logger.info("WebSocket心跳任务已取消")
    except Exception as e:
        logger.error(f"WebSocket心跳任务失败: {str(e)}")


async def _service_health_check_task():
    """服务健康检查任务"""
    logger.info("服务健康检查任务已启动")
    
    try:
        while True:
            try:
                # 检查GeWe服务健康状态
                gewe_health = await gewe_service.health_check()
                if not gewe_health["healthy"]:
                    await notification_service.send_warning_notification(
                        title="GeWe服务异常",
                        message="GeWe服务健康检查失败，请检查服务状态",
                        target_type="broadcast"
                    )
                
                # 检查FastGPT服务健康状态
                fastgpt_health = await fastgpt_service.health_check()
                if not fastgpt_health["healthy"]:
                    await notification_service.send_warning_notification(
                        title="FastGPT服务异常",
                        message="FastGPT服务健康检查失败，请检查服务状态",
                        target_type="broadcast"
                    )
                
            except Exception as e:
                logger.error(f"服务健康检查异常: {str(e)}")
            
            # 每2分钟检查一次
            await asyncio.sleep(120)
    
    except asyncio.CancelledError:
        logger.info("服务健康检查任务已取消")
    except Exception as e:
        logger.error(f"服务健康检查任务失败: {str(e)}")


async def _cache_cleanup_task():
    """缓存清理任务"""
    logger.info("缓存清理任务已启动")
    
    try:
        while True:
            try:
                # 清理FastGPT工作流缓存
                await fastgpt_service.clear_cache()
                
                # 可以添加其他缓存清理逻辑
                logger.debug("缓存清理完成")
                
            except Exception as e:
                logger.error(f"缓存清理异常: {str(e)}")
            
            # 每小时清理一次
            await asyncio.sleep(3600)
    
    except asyncio.CancelledError:
        logger.info("缓存清理任务已取消")
    except Exception as e:
        logger.error(f"缓存清理任务失败: {str(e)}")


async def _stats_aggregation_task():
    """统计数据聚合任务"""
    logger.info("统计数据聚合任务已启动")
    
    try:
        while True:
            try:
                # 获取各服务统计数据
                gewe_stats = gewe_service.get_stats()
                fastgpt_stats = fastgpt_service.get_stats()
                
                # 聚合统计数据
                aggregated_stats = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "gewe": gewe_stats,
                    "fastgpt": fastgpt_stats,
                    "websocket": {
                        "total_connections": websocket_manager.get_connection_count(),
                        "active_users": websocket_manager.get_user_count()
                    }
                }
                
                # 广播统计数据
                await websocket_manager.broadcast({
                    "type": "stats_update",
                    "data": aggregated_stats
                }, channel="admin")
                
                logger.debug("统计数据聚合完成")
                
            except Exception as e:
                logger.error(f"统计数据聚合异常: {str(e)}")
            
            # 每5分钟聚合一次
            await asyncio.sleep(300)
    
    except asyncio.CancelledError:
        logger.info("统计数据聚合任务已取消")
    except Exception as e:
        logger.error(f"统计数据聚合任务失败: {str(e)}")


# 健康检查端点的辅助函数
async def get_system_health() -> dict:
    """获取系统整体健康状态"""
    try:
        # 获取各服务状态
        gewe_health = await gewe_service.health_check()
        fastgpt_health = await fastgpt_service.health_check()
        
        # 获取监控状态
        monitoring_status = integration_monitor.is_monitoring
        
        # 获取WebSocket状态
        websocket_connections = websocket_manager.get_connection_count()
        
        # 计算整体健康状态
        services_healthy = gewe_health["healthy"] and fastgpt_health["healthy"]
        system_healthy = services_healthy and monitoring_status
        
        return {
            "healthy": system_healthy,
            "services": {
                "gewe": gewe_health["healthy"],
                "fastgpt": fastgpt_health["healthy"],
                "monitoring": monitoring_status,
                "websocket": websocket_connections > 0
            },
            "details": {
                "gewe_response_time": gewe_health.get("response_time", 0),
                "fastgpt_response_time": fastgpt_health.get("response_time", 0),
                "websocket_connections": websocket_connections,
                "background_tasks": len(_background_tasks)
            },
            "timestamp": asyncio.get_event_loop().time()
        }
    
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {str(e)}")
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }

