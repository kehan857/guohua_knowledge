"""
外部服务集成监控
负责监控外部服务的健康状态、性能指标和告警
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

from app.core.redis import redis_client
from app.services.gewe_service import gewe_service
from app.services.fastgpt_service import fastgpt_service
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """服务状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """告警严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ServiceMetrics:
    """服务指标"""
    service_name: str
    timestamp: datetime
    status: ServiceStatus
    response_time: float
    success_rate: float
    error_rate: float
    total_requests: int
    active_connections: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    custom_metrics: Dict[str, Any] = None


@dataclass
class ServiceAlert:
    """服务告警"""
    alert_id: str
    service_name: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class IntegrationMonitor:
    """集成监控器"""
    
    def __init__(self):
        self.monitoring_interval = 30  # 30秒监控间隔
        self.metrics_retention = timedelta(days=7)  # 指标保留7天
        self.alert_retention = timedelta(days=30)   # 告警保留30天
        
        # 告警阈值配置
        self.alert_thresholds = {
            "response_time": {
                "warning": 5.0,     # 5秒
                "critical": 10.0    # 10秒
            },
            "success_rate": {
                "warning": 90.0,    # 90%
                "critical": 80.0    # 80%
            },
            "error_rate": {
                "warning": 5.0,     # 5%
                "critical": 10.0    # 10%
            }
        }
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_task = None
        
        # 缓存
        self.metrics_cache = {}
        self.alerts_cache = {}
    
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("集成服务监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("集成服务监控已停止")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集所有服务指标
                await self._collect_all_metrics()
                
                # 检查告警条件
                await self._check_alerts()
                
                # 清理过期数据
                await self._cleanup_old_data()
                
                # 发送监控数据到WebSocket
                await self._broadcast_monitoring_data()
                
            except Exception as e:
                logger.error(f"监控循环异常: {str(e)}")
            
            # 等待下一个监控周期
            await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_all_metrics(self):
        """收集所有服务指标"""
        try:
            # 并发收集所有服务指标
            tasks = [
                self._collect_gewe_metrics(),
                self._collect_fastgpt_metrics()
            ]
            
            metrics_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 存储指标
            for metrics in metrics_list:
                if isinstance(metrics, ServiceMetrics):
                    await self._store_metrics(metrics)
                elif isinstance(metrics, Exception):
                    logger.error(f"收集指标失败: {str(metrics)}")
        
        except Exception as e:
            logger.error(f"收集服务指标失败: {str(e)}")
    
    async def _collect_gewe_metrics(self) -> ServiceMetrics:
        """收集GeWe服务指标"""
        try:
            # 获取GeWe健康状态和统计信息
            health_data = await gewe_service.health_check()
            stats = gewe_service.get_stats()
            
            # 计算状态
            if health_data["healthy"]:
                if stats["success_rate"] >= 95:
                    status = ServiceStatus.HEALTHY
                elif stats["success_rate"] >= 80:
                    status = ServiceStatus.DEGRADED
                else:
                    status = ServiceStatus.DOWN
            else:
                status = ServiceStatus.DOWN
            
            # 计算错误率
            error_rate = 100 - stats["success_rate"]
            
            return ServiceMetrics(
                service_name="GeWe",
                timestamp=datetime.utcnow(),
                status=status,
                response_time=health_data.get("response_time", 0.0),
                success_rate=stats["success_rate"],
                error_rate=error_rate,
                total_requests=stats["total_requests"],
                custom_metrics={
                    "rate_limited_requests": stats.get("rate_limited_requests", 0),
                    "active_rate_limits": stats.get("active_rate_limits", 0),
                    "average_response_time": stats.get("average_response_time", 0.0)
                }
            )
        
        except Exception as e:
            logger.error(f"收集GeWe指标失败: {str(e)}")
            return ServiceMetrics(
                service_name="GeWe",
                timestamp=datetime.utcnow(),
                status=ServiceStatus.UNKNOWN,
                response_time=0.0,
                success_rate=0.0,
                error_rate=100.0,
                total_requests=0
            )
    
    async def _collect_fastgpt_metrics(self) -> ServiceMetrics:
        """收集FastGPT服务指标"""
        try:
            # 获取FastGPT健康状态和统计信息
            health_data = await fastgpt_service.health_check()
            stats = fastgpt_service.get_stats()
            
            # 计算状态
            if health_data["healthy"]:
                if stats["success_rate"] >= 95:
                    status = ServiceStatus.HEALTHY
                elif stats["success_rate"] >= 80:
                    status = ServiceStatus.DEGRADED
                else:
                    status = ServiceStatus.DOWN
            else:
                status = ServiceStatus.DOWN
            
            # 计算错误率
            error_rate = 100 - stats["success_rate"]
            
            return ServiceMetrics(
                service_name="FastGPT",
                timestamp=datetime.utcnow(),
                status=status,
                response_time=health_data.get("response_time", 0.0),
                success_rate=stats["success_rate"],
                error_rate=error_rate,
                total_requests=stats["total_requests"],
                custom_metrics={
                    "total_tokens": stats.get("total_tokens", 0),
                    "total_cost": stats.get("total_cost", 0.0),
                    "average_tokens_per_request": stats.get("average_tokens_per_request", 0.0),
                    "timeout_requests": stats.get("timeout_requests", 0),
                    "queue_size": health_data.get("queue_size", 0),
                    "processing_requests": health_data.get("processing_requests", 0)
                }
            )
        
        except Exception as e:
            logger.error(f"收集FastGPT指标失败: {str(e)}")
            return ServiceMetrics(
                service_name="FastGPT",
                timestamp=datetime.utcnow(),
                status=ServiceStatus.UNKNOWN,
                response_time=0.0,
                success_rate=0.0,
                error_rate=100.0,
                total_requests=0
            )
    
    async def _store_metrics(self, metrics: ServiceMetrics):
        """存储指标到Redis"""
        try:
            # 存储最新指标
            latest_key = f"metrics:latest:{metrics.service_name}"
            await redis_client.setex(
                latest_key, 
                300,  # 5分钟过期
                json.dumps(asdict(metrics), default=str)
            )
            
            # 存储历史指标（时间序列）
            timestamp_key = f"metrics:history:{metrics.service_name}:{int(metrics.timestamp.timestamp())}"
            await redis_client.setex(
                timestamp_key,
                int(self.metrics_retention.total_seconds()),
                json.dumps(asdict(metrics), default=str)
            )
            
            # 更新缓存
            self.metrics_cache[metrics.service_name] = metrics
            
        except Exception as e:
            logger.error(f"存储指标失败: {str(e)}")
    
    async def _check_alerts(self):
        """检查告警条件"""
        try:
            for service_name, metrics in self.metrics_cache.items():
                await self._check_service_alerts(metrics)
        
        except Exception as e:
            logger.error(f"检查告警失败: {str(e)}")
    
    async def _check_service_alerts(self, metrics: ServiceMetrics):
        """检查单个服务的告警"""
        try:
            alerts = []
            
            # 检查服务状态
            if metrics.status == ServiceStatus.DOWN:
                alerts.append(ServiceAlert(
                    alert_id=f"{metrics.service_name}_down_{int(metrics.timestamp.timestamp())}",
                    service_name=metrics.service_name,
                    alert_type="service_down",
                    severity=AlertSeverity.CRITICAL,
                    title=f"{metrics.service_name}服务异常",
                    message=f"{metrics.service_name}服务当前状态为DOWN，请立即检查",
                    timestamp=metrics.timestamp,
                    metadata={"status": metrics.status}
                ))
            
            # 检查响应时间
            if metrics.response_time > self.alert_thresholds["response_time"]["critical"]:
                alerts.append(ServiceAlert(
                    alert_id=f"{metrics.service_name}_response_time_{int(metrics.timestamp.timestamp())}",
                    service_name=metrics.service_name,
                    alert_type="high_response_time",
                    severity=AlertSeverity.CRITICAL,
                    title=f"{metrics.service_name}响应时间过长",
                    message=f"{metrics.service_name}响应时间{metrics.response_time:.2f}秒，超过临界阈值",
                    timestamp=metrics.timestamp,
                    metadata={"response_time": metrics.response_time}
                ))
            elif metrics.response_time > self.alert_thresholds["response_time"]["warning"]:
                alerts.append(ServiceAlert(
                    alert_id=f"{metrics.service_name}_response_time_{int(metrics.timestamp.timestamp())}",
                    service_name=metrics.service_name,
                    alert_type="high_response_time",
                    severity=AlertSeverity.MEDIUM,
                    title=f"{metrics.service_name}响应时间较长",
                    message=f"{metrics.service_name}响应时间{metrics.response_time:.2f}秒，超过警告阈值",
                    timestamp=metrics.timestamp,
                    metadata={"response_time": metrics.response_time}
                ))
            
            # 检查成功率
            if metrics.success_rate < self.alert_thresholds["success_rate"]["critical"]:
                alerts.append(ServiceAlert(
                    alert_id=f"{metrics.service_name}_success_rate_{int(metrics.timestamp.timestamp())}",
                    service_name=metrics.service_name,
                    alert_type="low_success_rate",
                    severity=AlertSeverity.CRITICAL,
                    title=f"{metrics.service_name}成功率过低",
                    message=f"{metrics.service_name}成功率{metrics.success_rate:.1f}%，低于临界阈值",
                    timestamp=metrics.timestamp,
                    metadata={"success_rate": metrics.success_rate}
                ))
            elif metrics.success_rate < self.alert_thresholds["success_rate"]["warning"]:
                alerts.append(ServiceAlert(
                    alert_id=f"{metrics.service_name}_success_rate_{int(metrics.timestamp.timestamp())}",
                    service_name=metrics.service_name,
                    alert_type="low_success_rate",
                    severity=AlertSeverity.MEDIUM,
                    title=f"{metrics.service_name}成功率较低",
                    message=f"{metrics.service_name}成功率{metrics.success_rate:.1f}%，低于警告阈值",
                    timestamp=metrics.timestamp,
                    metadata={"success_rate": metrics.success_rate}
                ))
            
            # 处理新告警
            for alert in alerts:
                await self._process_alert(alert)
        
        except Exception as e:
            logger.error(f"检查服务告警失败: {str(e)}")
    
    async def _process_alert(self, alert: ServiceAlert):
        """处理告警"""
        try:
            # 检查是否是重复告警
            if await self._is_duplicate_alert(alert):
                return
            
            # 存储告警
            await self._store_alert(alert)
            
            # 发送通知
            await self._send_alert_notification(alert)
            
            # 更新缓存
            self.alerts_cache[alert.alert_id] = alert
            
        except Exception as e:
            logger.error(f"处理告警失败: {str(e)}")
    
    async def _is_duplicate_alert(self, alert: ServiceAlert) -> bool:
        """检查是否是重复告警"""
        try:
            # 检查最近5分钟内是否有相同类型的告警
            five_minutes_ago = alert.timestamp - timedelta(minutes=5)
            
            pattern = f"alert:{alert.service_name}:{alert.alert_type}:*"
            keys = await redis_client.keys(pattern)
            
            for key in keys:
                alert_data = await redis_client.get(key)
                if alert_data:
                    existing_alert = json.loads(alert_data.decode())
                    existing_timestamp = datetime.fromisoformat(existing_alert["timestamp"])
                    
                    if existing_timestamp > five_minutes_ago and not existing_alert.get("resolved", False):
                        return True
            
            return False
        
        except Exception as e:
            logger.error(f"检查重复告警失败: {str(e)}")
            return False
    
    async def _store_alert(self, alert: ServiceAlert):
        """存储告警"""
        try:
            alert_key = f"alert:{alert.service_name}:{alert.alert_type}:{int(alert.timestamp.timestamp())}"
            await redis_client.setex(
                alert_key,
                int(self.alert_retention.total_seconds()),
                json.dumps(asdict(alert), default=str)
            )
        
        except Exception as e:
            logger.error(f"存储告警失败: {str(e)}")
    
    async def _send_alert_notification(self, alert: ServiceAlert):
        """发送告警通知"""
        try:
            # 根据严重程度选择通知方式
            if alert.severity == AlertSeverity.CRITICAL:
                # 严重告警：多渠道通知
                await notification_service.send_error_notification(
                    title=alert.title,
                    message=alert.message,
                    target_type="broadcast"
                )
            elif alert.severity == AlertSeverity.HIGH:
                # 高级告警：WebSocket + 邮件
                await notification_service.send_warning_notification(
                    title=alert.title,
                    message=alert.message,
                    target_type="broadcast"
                )
            else:
                # 中低级告警：WebSocket通知
                await notification_service.send_info_notification(
                    title=alert.title,
                    message=alert.message,
                    target_type="broadcast"
                )
            
            # 发送到监控WebSocket频道
            await websocket_manager.broadcast({
                "type": "service_alert",
                "data": asdict(alert)
            }, channel="monitoring")
            
        except Exception as e:
            logger.error(f"发送告警通知失败: {str(e)}")
    
    async def _cleanup_old_data(self):
        """清理过期数据"""
        try:
            now = datetime.utcnow()
            
            # 清理过期指标
            metrics_cutoff = now - self.metrics_retention
            metrics_pattern = "metrics:history:*"
            
            keys = await redis_client.keys(metrics_pattern)
            for key in keys:
                # 从key中提取时间戳
                try:
                    timestamp_str = key.decode().split(":")[-1]
                    timestamp = datetime.fromtimestamp(int(timestamp_str))
                    
                    if timestamp < metrics_cutoff:
                        await redis_client.delete(key)
                except:
                    pass
            
            # 清理过期告警
            alert_cutoff = now - self.alert_retention
            alert_pattern = "alert:*"
            
            keys = await redis_client.keys(alert_pattern)
            for key in keys:
                try:
                    timestamp_str = key.decode().split(":")[-1]
                    timestamp = datetime.fromtimestamp(int(timestamp_str))
                    
                    if timestamp < alert_cutoff:
                        await redis_client.delete(key)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"清理过期数据失败: {str(e)}")
    
    async def _broadcast_monitoring_data(self):
        """广播监控数据"""
        try:
            # 准备监控数据
            monitoring_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "services": {},
                "summary": {
                    "total_services": len(self.metrics_cache),
                    "healthy_services": 0,
                    "degraded_services": 0,
                    "down_services": 0
                }
            }
            
            # 添加各服务的指标
            for service_name, metrics in self.metrics_cache.items():
                monitoring_data["services"][service_name] = {
                    "status": metrics.status,
                    "response_time": metrics.response_time,
                    "success_rate": metrics.success_rate,
                    "error_rate": metrics.error_rate,
                    "total_requests": metrics.total_requests,
                    "custom_metrics": metrics.custom_metrics or {}
                }
                
                # 更新统计
                if metrics.status == ServiceStatus.HEALTHY:
                    monitoring_data["summary"]["healthy_services"] += 1
                elif metrics.status == ServiceStatus.DEGRADED:
                    monitoring_data["summary"]["degraded_services"] += 1
                elif metrics.status == ServiceStatus.DOWN:
                    monitoring_data["summary"]["down_services"] += 1
            
            # 发送到WebSocket
            await websocket_manager.broadcast({
                "type": "monitoring_update",
                "data": monitoring_data
            }, channel="monitoring")
        
        except Exception as e:
            logger.error(f"广播监控数据失败: {str(e)}")
    
    # ==================== 公共API ====================
    
    async def get_service_metrics(self, service_name: str, hours: int = 24) -> List[ServiceMetrics]:
        """获取服务指标历史"""
        try:
            metrics = []
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # 从Redis获取历史数据
            pattern = f"metrics:history:{service_name}:*"
            keys = await redis_client.keys(pattern)
            
            for key in keys:
                try:
                    timestamp_str = key.decode().split(":")[-1]
                    timestamp = datetime.fromtimestamp(int(timestamp_str))
                    
                    if start_time <= timestamp <= end_time:
                        data = await redis_client.get(key)
                        if data:
                            metrics_data = json.loads(data.decode())
                            metrics_data["timestamp"] = timestamp
                            metrics.append(ServiceMetrics(**metrics_data))
                except:
                    continue
            
            # 按时间排序
            metrics.sort(key=lambda x: x.timestamp)
            return metrics
        
        except Exception as e:
            logger.error(f"获取服务指标失败: {str(e)}")
            return []
    
    async def get_active_alerts(self, service_name: Optional[str] = None) -> List[ServiceAlert]:
        """获取活跃告警"""
        try:
            alerts = []
            
            # 构建搜索模式
            if service_name:
                pattern = f"alert:{service_name}:*"
            else:
                pattern = "alert:*"
            
            keys = await redis_client.keys(pattern)
            
            for key in keys:
                try:
                    data = await redis_client.get(key)
                    if data:
                        alert_data = json.loads(data.decode())
                        alert_data["timestamp"] = datetime.fromisoformat(alert_data["timestamp"])
                        if alert_data.get("resolved_at"):
                            alert_data["resolved_at"] = datetime.fromisoformat(alert_data["resolved_at"])
                        
                        alert = ServiceAlert(**alert_data)
                        if not alert.resolved:  # 只返回未解决的告警
                            alerts.append(alert)
                except:
                    continue
            
            # 按时间倒序排序
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            return alerts
        
        except Exception as e:
            logger.error(f"获取活跃告警失败: {str(e)}")
            return []
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        try:
            # 查找告警
            pattern = f"alert:*"
            keys = await redis_client.keys(pattern)
            
            for key in keys:
                try:
                    data = await redis_client.get(key)
                    if data:
                        alert_data = json.loads(data.decode())
                        if alert_data.get("alert_id") == alert_id:
                            # 更新告警状态
                            alert_data["resolved"] = True
                            alert_data["resolved_at"] = datetime.utcnow().isoformat()
                            
                            await redis_client.setex(
                                key,
                                int(self.alert_retention.total_seconds()),
                                json.dumps(alert_data)
                            )
                            
                            # 更新缓存
                            if alert_id in self.alerts_cache:
                                self.alerts_cache[alert_id].resolved = True
                                self.alerts_cache[alert_id].resolved_at = datetime.utcnow()
                            
                            return True
                except:
                    continue
            
            return False
        
        except Exception as e:
            logger.error(f"解决告警失败: {str(e)}")
            return False
    
    async def get_service_status_summary(self) -> Dict[str, Any]:
        """获取服务状态摘要"""
        try:
            summary = {
                "total_services": 0,
                "healthy_services": 0,
                "degraded_services": 0,
                "down_services": 0,
                "unknown_services": 0,
                "services": {},
                "last_update": datetime.utcnow().isoformat()
            }
            
            for service_name, metrics in self.metrics_cache.items():
                summary["total_services"] += 1
                summary["services"][service_name] = {
                    "status": metrics.status,
                    "last_check": metrics.timestamp.isoformat(),
                    "response_time": metrics.response_time,
                    "success_rate": metrics.success_rate
                }
                
                if metrics.status == ServiceStatus.HEALTHY:
                    summary["healthy_services"] += 1
                elif metrics.status == ServiceStatus.DEGRADED:
                    summary["degraded_services"] += 1
                elif metrics.status == ServiceStatus.DOWN:
                    summary["down_services"] += 1
                else:
                    summary["unknown_services"] += 1
            
            return summary
        
        except Exception as e:
            logger.error(f"获取服务状态摘要失败: {str(e)}")
            return {}


# 全局监控器实例
integration_monitor = IntegrationMonitor()

