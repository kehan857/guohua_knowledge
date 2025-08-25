"""
监控API接口
提供系统监控数据和告警管理
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, require_permissions
from app.models.user import User
from app.services.integration_monitor import integration_monitor, ServiceStatus, AlertSeverity

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


# ==================== 请求/响应模型 ====================

class MetricsQueryRequest(BaseModel):
    """指标查询请求"""
    service_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metrics: List[str] = Field(default_factory=list)


class AlertFilterRequest(BaseModel):
    """告警筛选请求"""
    service_name: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    resolved: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class AlertResolveRequest(BaseModel):
    """告警解决请求"""
    alert_id: str
    resolution_note: Optional[str] = None


class ServiceMetricsResponse(BaseModel):
    """服务指标响应"""
    service_name: str
    timestamp: datetime
    status: ServiceStatus
    response_time: float
    success_rate: float
    error_rate: float
    total_requests: int
    custom_metrics: Dict[str, Any]


class ServiceAlertResponse(BaseModel):
    """服务告警响应"""
    alert_id: str
    service_name: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any]


class MonitoringOverviewResponse(BaseModel):
    """监控概览响应"""
    total_services: int
    healthy_services: int
    degraded_services: int
    down_services: int
    unknown_services: int
    active_alerts: int
    critical_alerts: int
    services: Dict[str, Dict[str, Any]]
    last_update: str


# ==================== 监控概览 ====================

@router.get("/overview", response_model=MonitoringOverviewResponse)
async def get_monitoring_overview(
    current_user: User = Depends(get_current_user)
):
    """获取监控概览"""
    try:
        # 获取服务状态摘要
        status_summary = await integration_monitor.get_service_status_summary()
        
        # 获取活跃告警
        active_alerts = await integration_monitor.get_active_alerts()
        
        # 统计告警信息
        critical_alerts = sum(1 for alert in active_alerts if alert.severity == AlertSeverity.CRITICAL)
        
        return MonitoringOverviewResponse(
            total_services=status_summary.get("total_services", 0),
            healthy_services=status_summary.get("healthy_services", 0),
            degraded_services=status_summary.get("degraded_services", 0),
            down_services=status_summary.get("down_services", 0),
            unknown_services=status_summary.get("unknown_services", 0),
            active_alerts=len(active_alerts),
            critical_alerts=critical_alerts,
            services=status_summary.get("services", {}),
            last_update=status_summary.get("last_update", datetime.utcnow().isoformat())
        )
    
    except Exception as e:
        logger.error(f"获取监控概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取监控概览失败: {str(e)}")


# ==================== 服务指标 ====================

@router.get("/metrics")
async def get_service_metrics(
    service_name: Optional[str] = Query(None, description="服务名称"),
    hours: int = Query(24, description="查询时间范围（小时）", ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """获取服务指标"""
    try:
        if service_name:
            # 获取特定服务的指标
            metrics = await integration_monitor.get_service_metrics(service_name, hours)
            
            return {
                "success": True,
                "service_name": service_name,
                "data": [
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "status": metric.status,
                        "response_time": metric.response_time,
                        "success_rate": metric.success_rate,
                        "error_rate": metric.error_rate,
                        "total_requests": metric.total_requests,
                        "custom_metrics": metric.custom_metrics or {}
                    }
                    for metric in metrics
                ],
                "total": len(metrics)
            }
        else:
            # 获取所有服务的最新指标
            all_metrics = {}
            services = ["GeWe", "FastGPT"]  # 可以动态获取
            
            for svc_name in services:
                metrics = await integration_monitor.get_service_metrics(svc_name, 1)  # 最近1小时
                if metrics:
                    all_metrics[svc_name] = {
                        "latest": {
                            "timestamp": metrics[-1].timestamp.isoformat(),
                            "status": metrics[-1].status,
                            "response_time": metrics[-1].response_time,
                            "success_rate": metrics[-1].success_rate,
                            "error_rate": metrics[-1].error_rate,
                            "total_requests": metrics[-1].total_requests,
                            "custom_metrics": metrics[-1].custom_metrics or {}
                        },
                        "history_count": len(metrics)
                    }
            
            return {
                "success": True,
                "data": all_metrics,
                "query_range_hours": hours
            }
    
    except Exception as e:
        logger.error(f"获取服务指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务指标失败: {str(e)}")


@router.get("/metrics/{service_name}/trends")
async def get_service_trends(
    service_name: str,
    hours: int = Query(24, description="查询时间范围（小时）", ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """获取服务趋势分析"""
    try:
        metrics = await integration_monitor.get_service_metrics(service_name, hours)
        
        if not metrics:
            return {
                "success": True,
                "service_name": service_name,
                "message": "暂无数据",
                "trends": {}
            }
        
        # 计算趋势
        response_times = [m.response_time for m in metrics]
        success_rates = [m.success_rate for m in metrics]
        error_rates = [m.error_rate for m in metrics]
        
        # 计算平均值和趋势
        trends = {
            "response_time": {
                "current": response_times[-1] if response_times else 0,
                "average": sum(response_times) / len(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "trend": "stable"  # 简化处理，实际可以计算斜率
            },
            "success_rate": {
                "current": success_rates[-1] if success_rates else 0,
                "average": sum(success_rates) / len(success_rates) if success_rates else 0,
                "min": min(success_rates) if success_rates else 0,
                "max": max(success_rates) if success_rates else 0,
                "trend": "stable"
            },
            "error_rate": {
                "current": error_rates[-1] if error_rates else 0,
                "average": sum(error_rates) / len(error_rates) if error_rates else 0,
                "min": min(error_rates) if error_rates else 0,
                "max": max(error_rates) if error_rates else 0,
                "trend": "stable"
            }
        }
        
        # 简单趋势计算
        if len(metrics) >= 2:
            for metric_name in ["response_time", "success_rate", "error_rate"]:
                values = [getattr(m, metric_name) for m in metrics]
                if len(values) >= 2:
                    if values[-1] > values[-2]:
                        trends[metric_name]["trend"] = "increasing"
                    elif values[-1] < values[-2]:
                        trends[metric_name]["trend"] = "decreasing"
        
        return {
            "success": True,
            "service_name": service_name,
            "trends": trends,
            "data_points": len(metrics),
            "time_range": f"{hours} hours"
        }
    
    except Exception as e:
        logger.error(f"获取服务趋势失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取服务趋势失败: {str(e)}")


# ==================== 告警管理 ====================

@router.get("/alerts")
async def get_alerts(
    service_name: Optional[str] = Query(None, description="服务名称"),
    alert_type: Optional[str] = Query(None, description="告警类型"),
    severity: Optional[AlertSeverity] = Query(None, description="严重程度"),
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """获取告警列表"""
    try:
        # 获取所有活跃告警
        alerts = await integration_monitor.get_active_alerts(service_name)
        
        # 应用筛选条件
        filtered_alerts = []
        for alert in alerts:
            # 筛选告警类型
            if alert_type and alert.alert_type != alert_type:
                continue
            
            # 筛选严重程度
            if severity and alert.severity != severity:
                continue
            
            # 筛选解决状态
            if resolved is not None and alert.resolved != resolved:
                continue
            
            filtered_alerts.append(alert)
        
        # 限制返回数量
        filtered_alerts = filtered_alerts[:limit]
        
        # 转换为响应格式
        response_alerts = []
        for alert in filtered_alerts:
            response_alerts.append({
                "alert_id": alert.alert_id,
                "service_name": alert.service_name,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "metadata": alert.metadata or {}
            })
        
        return {
            "success": True,
            "data": response_alerts,
            "total": len(response_alerts),
            "filters": {
                "service_name": service_name,
                "alert_type": alert_type,
                "severity": severity,
                "resolved": resolved
            }
        }
    
    except Exception as e:
        logger.error(f"获取告警列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@router.get("/alerts/summary")
async def get_alerts_summary(
    current_user: User = Depends(get_current_user)
):
    """获取告警摘要"""
    try:
        all_alerts = await integration_monitor.get_active_alerts()
        
        # 统计各种告警
        summary = {
            "total_alerts": len(all_alerts),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "by_service": {},
            "by_type": {},
            "resolved_count": 0,
            "unresolved_count": 0,
            "last_24h_count": 0
        }
        
        now = datetime.utcnow()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        for alert in all_alerts:
            # 按严重程度统计
            summary["by_severity"][alert.severity] += 1
            
            # 按服务统计
            if alert.service_name not in summary["by_service"]:
                summary["by_service"][alert.service_name] = 0
            summary["by_service"][alert.service_name] += 1
            
            # 按类型统计
            if alert.alert_type not in summary["by_type"]:
                summary["by_type"][alert.alert_type] = 0
            summary["by_type"][alert.alert_type] += 1
            
            # 解决状态统计
            if alert.resolved:
                summary["resolved_count"] += 1
            else:
                summary["unresolved_count"] += 1
            
            # 最近24小时统计
            if alert.timestamp > twenty_four_hours_ago:
                summary["last_24h_count"] += 1
        
        return {
            "success": True,
            "data": summary
        }
    
    except Exception as e:
        logger.error(f"获取告警摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取告警摘要失败: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: AlertResolveRequest,
    current_user: User = Depends(get_current_user)
):
    """解决告警"""
    try:
        success = await integration_monitor.resolve_alert(alert_id)
        
        if success:
            return {
                "success": True,
                "message": "告警已解决",
                "alert_id": alert_id,
                "resolved_by": current_user.username,
                "resolved_at": datetime.utcnow().isoformat(),
                "resolution_note": request.resolution_note
            }
        else:
            raise HTTPException(status_code=404, detail="告警不存在或已解决")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")


# ==================== 监控配置 ====================

@router.get("/config")
async def get_monitoring_config(
    current_user: User = Depends(require_permissions(["admin"]))
):
    """获取监控配置"""
    try:
        config = {
            "monitoring_interval": integration_monitor.monitoring_interval,
            "metrics_retention_days": integration_monitor.metrics_retention.days,
            "alert_retention_days": integration_monitor.alert_retention.days,
            "alert_thresholds": integration_monitor.alert_thresholds,
            "is_monitoring": integration_monitor.is_monitoring
        }
        
        return {
            "success": True,
            "data": config
        }
    
    except Exception as e:
        logger.error(f"获取监控配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取监控配置失败: {str(e)}")


@router.put("/config")
async def update_monitoring_config(
    config_data: Dict[str, Any],
    current_user: User = Depends(require_permissions(["admin"]))
):
    """更新监控配置"""
    try:
        # 更新监控间隔
        if "monitoring_interval" in config_data:
            integration_monitor.monitoring_interval = config_data["monitoring_interval"]
        
        # 更新告警阈值
        if "alert_thresholds" in config_data:
            integration_monitor.alert_thresholds.update(config_data["alert_thresholds"])
        
        return {
            "success": True,
            "message": "监控配置已更新"
        }
    
    except Exception as e:
        logger.error(f"更新监控配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新监控配置失败: {str(e)}")


# ==================== 监控控制 ====================

@router.post("/start")
async def start_monitoring(
    current_user: User = Depends(require_permissions(["admin"]))
):
    """启动监控"""
    try:
        await integration_monitor.start_monitoring()
        
        return {
            "success": True,
            "message": "监控已启动"
        }
    
    except Exception as e:
        logger.error(f"启动监控失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动监控失败: {str(e)}")


@router.post("/stop")
async def stop_monitoring(
    current_user: User = Depends(require_permissions(["admin"]))
):
    """停止监控"""
    try:
        await integration_monitor.stop_monitoring()
        
        return {
            "success": True,
            "message": "监控已停止"
        }
    
    except Exception as e:
        logger.error(f"停止监控失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止监控失败: {str(e)}")


@router.get("/status")
async def get_monitoring_status(
    current_user: User = Depends(get_current_user)
):
    """获取监控状态"""
    try:
        status = {
            "is_monitoring": integration_monitor.is_monitoring,
            "monitoring_interval": integration_monitor.monitoring_interval,
            "cached_services": list(integration_monitor.metrics_cache.keys()),
            "cached_alerts": len(integration_monitor.alerts_cache),
            "uptime": "正在运行" if integration_monitor.is_monitoring else "已停止"
        }
        
        return {
            "success": True,
            "data": status
        }
    
    except Exception as e:
        logger.error(f"获取监控状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取监控状态失败: {str(e)}")

