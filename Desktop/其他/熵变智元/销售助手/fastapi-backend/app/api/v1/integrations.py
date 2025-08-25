"""
外部服务集成API接口
负责管理和监控外部服务的集成状态
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, require_permissions
from app.models.user import User
from app.services.gewe_service import gewe_service, WorkflowConfig
from app.services.fastgpt_service import fastgpt_service, ChatContext
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


# ==================== 请求/响应模型 ====================

class ServiceHealthResponse(BaseModel):
    """服务健康状态响应"""
    service_name: str
    healthy: bool
    response_time: float
    last_check: str
    error: Optional[str] = None
    stats: Dict[str, Any]


class IntegrationOverviewResponse(BaseModel):
    """集成概览响应"""
    gewe_status: ServiceHealthResponse
    fastgpt_status: ServiceHealthResponse
    total_integrations: int
    active_integrations: int
    last_sync: str


class GeWeTestRequest(BaseModel):
    """GeWe测试请求"""
    token_id: str = Field(..., description="GeWe Token ID")
    test_type: str = Field("health_check", description="测试类型")
    target_wxid: Optional[str] = Field(None, description="目标微信ID")
    message: Optional[str] = Field(None, description="测试消息")


class FastGPTTestRequest(BaseModel):
    """FastGPT测试请求"""
    workflow_id: str = Field(..., description="工作流ID")
    user_input: str = Field(..., description="用户输入")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文")


class WorkflowRegistrationRequest(BaseModel):
    """工作流注册请求"""
    workflow_id: str
    name: str
    description: str
    api_endpoint: str
    api_key: str
    model_config: Dict[str, Any]
    variables: Optional[Dict[str, Any]] = None


class WebhookSetupRequest(BaseModel):
    """Webhook设置请求"""
    token_id: str
    webhook_url: str
    events: List[str] = Field(default_factory=list)


# ==================== 集成概览 ====================

@router.get("/overview", response_model=IntegrationOverviewResponse)
async def get_integration_overview(
    current_user: User = Depends(get_current_user)
):
    """获取外部服务集成概览"""
    try:
        # 获取GeWe状态
        gewe_health = await gewe_service.health_check()
        gewe_status = ServiceHealthResponse(
            service_name="GeWe",
            healthy=gewe_health["healthy"],
            response_time=gewe_health.get("response_time", 0.0),
            last_check=gewe_health["last_check"],
            error=gewe_health.get("error"),
            stats=gewe_health.get("stats", {})
        )
        
        # 获取FastGPT状态
        fastgpt_health = await fastgpt_service.health_check()
        fastgpt_status = ServiceHealthResponse(
            service_name="FastGPT",
            healthy=fastgpt_health["healthy"],
            response_time=fastgpt_health.get("response_time", 0.0),
            last_check=fastgpt_health["last_check"],
            error=fastgpt_health.get("error"),
            stats=fastgpt_health.get("stats", {})
        )
        
        # 计算集成统计
        total_integrations = 2
        active_integrations = sum([
            1 if gewe_status.healthy else 0,
            1 if fastgpt_status.healthy else 0
        ])
        
        return IntegrationOverviewResponse(
            gewe_status=gewe_status,
            fastgpt_status=fastgpt_status,
            total_integrations=total_integrations,
            active_integrations=active_integrations,
            last_sync=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"获取集成概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取集成概览失败: {str(e)}")


# ==================== GeWe集成管理 ====================

@router.get("/gewe/health")
async def get_gewe_health(
    current_user: User = Depends(get_current_user)
):
    """获取GeWe服务健康状态"""
    try:
        health_data = await gewe_service.health_check()
        return health_data
    except Exception as e:
        logger.error(f"获取GeWe健康状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/gewe/stats")
async def get_gewe_stats(
    current_user: User = Depends(get_current_user)
):
    """获取GeWe服务统计信息"""
    try:
        stats = gewe_service.get_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取GeWe统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/gewe/test")
async def test_gewe_integration(
    request: GeWeTestRequest,
    current_user: User = Depends(get_current_user)
):
    """测试GeWe集成"""
    try:
        if request.test_type == "health_check":
            # 健康检查测试
            result = await gewe_service.health_check()
            
        elif request.test_type == "account_status":
            # 账号状态测试
            result = await gewe_service.get_account_list(request.token_id)
            
        elif request.test_type == "send_message":
            # 发送消息测试
            if not request.target_wxid or not request.message:
                raise HTTPException(status_code=400, detail="发送消息测试需要target_wxid和message参数")
            
            result = await gewe_service.send_text_message(
                token_id=request.token_id,
                wxid=request.target_wxid,
                message=request.message
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"不支持的测试类型: {request.test_type}")
        
        return {
            "success": True,
            "test_type": request.test_type,
            "result": result.__dict__ if hasattr(result, '__dict__') else result
        }
    
    except Exception as e:
        logger.error(f"GeWe集成测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/gewe/webhook")
async def setup_gewe_webhook(
    request: WebhookSetupRequest,
    current_user: User = Depends(get_current_user)
):
    """设置GeWe Webhook"""
    try:
        result = await gewe_service.setup_webhook(
            token_id=request.token_id,
            webhook_url=request.webhook_url
        )
        
        if result.success:
            return {
                "success": True,
                "message": "Webhook设置成功",
                "data": result.data
            }
        else:
            raise HTTPException(status_code=400, detail=result.error)
    
    except Exception as e:
        logger.error(f"设置GeWe Webhook失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")


@router.post("/gewe/webhook/callback")
async def gewe_webhook_callback(
    message_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """处理GeWe Webhook回调"""
    try:
        # 异步处理webhook消息
        background_tasks.add_task(
            gewe_service.process_webhook_message,
            message_data
        )
        
        return {"success": True, "message": "消息已接收"}
    
    except Exception as e:
        logger.error(f"处理GeWe Webhook失败: {str(e)}")
        return {"success": False, "error": str(e)}


# ==================== FastGPT集成管理 ====================

@router.get("/fastgpt/health")
async def get_fastgpt_health(
    current_user: User = Depends(get_current_user)
):
    """获取FastGPT服务健康状态"""
    try:
        health_data = await fastgpt_service.health_check()
        return health_data
    except Exception as e:
        logger.error(f"获取FastGPT健康状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/fastgpt/stats")
async def get_fastgpt_stats(
    current_user: User = Depends(get_current_user)
):
    """获取FastGPT服务统计信息"""
    try:
        stats = fastgpt_service.get_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取FastGPT统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/fastgpt/test")
async def test_fastgpt_integration(
    request: FastGPTTestRequest,
    current_user: User = Depends(get_current_user)
):
    """测试FastGPT集成"""
    try:
        # 构建测试上下文
        context = ChatContext(
            user_id=str(current_user.id),
            contact_wxid="test_wxid",
            account_id="test_account",
            session_id="test_session",
            metadata=request.context or {
                "organization_id": str(current_user.organization_id),
                "test_mode": True
            }
        )
        
        # 发送测试请求
        result = await fastgpt_service.process_chat_message(
            workflow_id=request.workflow_id,
            context=context,
            user_input=request.user_input
        )
        
        return {
            "success": result.success,
            "result": {
                "response": result.data,
                "tokens_used": result.tokens_used,
                "cost": result.cost,
                "response_time": result.response_time,
                "error": result.error
            }
        }
    
    except Exception as e:
        logger.error(f"FastGPT集成测试失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/fastgpt/workflows")
async def register_workflow(
    request: WorkflowRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """注册FastGPT工作流"""
    try:
        # 创建工作流配置
        config = WorkflowConfig(
            workflow_id=request.workflow_id,
            name=request.name,
            description=request.description,
            api_endpoint=request.api_endpoint,
            api_key=request.api_key,
            model_config=request.model_config,
            variables=request.variables
        )
        
        # 注册工作流
        success = await fastgpt_service.register_workflow(config)
        
        if success:
            return {
                "success": True,
                "message": "工作流注册成功",
                "workflow_id": request.workflow_id
            }
        else:
            raise HTTPException(status_code=400, detail="工作流注册失败")
    
    except Exception as e:
        logger.error(f"注册工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.get("/fastgpt/workflows")
async def get_workflows(
    current_user: User = Depends(get_current_user)
):
    """获取工作流列表"""
    try:
        workflows = []
        for workflow_id, config in fastgpt_service.workflow_configs.items():
            workflows.append({
                "workflow_id": config.workflow_id,
                "name": config.name,
                "description": config.description,
                "is_active": config.is_active,
                "model_config": config.model_config
            })
        
        return {
            "success": True,
            "data": workflows,
            "total": len(workflows)
        }
    
    except Exception as e:
        logger.error(f"获取工作流列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete("/fastgpt/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除工作流"""
    try:
        if workflow_id in fastgpt_service.workflow_configs:
            del fastgpt_service.workflow_configs[workflow_id]
            return {
                "success": True,
                "message": "工作流删除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="工作流不存在")
    
    except Exception as e:
        logger.error(f"删除工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 服务管理操作 ====================

@router.post("/services/restart")
async def restart_services(
    service_names: List[str],
    current_user: User = Depends(require_permissions(["admin"]))
):
    """重启服务"""
    try:
        results = {}
        
        for service_name in service_names:
            if service_name == "gewe":
                # 重启GeWe服务（清空缓存等）
                gewe_service.rate_limits.clear()
                gewe_service.stats = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "rate_limited_requests": 0,
                    "average_response_time": 0.0,
                    "last_request_time": None
                }
                results[service_name] = "重启成功"
                
            elif service_name == "fastgpt":
                # 重启FastGPT服务
                await fastgpt_service.clear_cache()
                await fastgpt_service.reload_workflows()
                results[service_name] = "重启成功"
                
            else:
                results[service_name] = "未知服务"
        
        return {
            "success": True,
            "message": "服务重启完成",
            "results": results
        }
    
    except Exception as e:
        logger.error(f"重启服务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重启失败: {str(e)}")


@router.post("/services/sync")
async def sync_services(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """同步服务状态"""
    try:
        # 异步执行同步任务
        background_tasks.add_task(_sync_all_services)
        
        return {
            "success": True,
            "message": "服务同步已开始"
        }
    
    except Exception as e:
        logger.error(f"同步服务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


async def _sync_all_services():
    """同步所有服务的后台任务"""
    try:
        # 同步GeWe服务
        gewe_health = await gewe_service.health_check()
        
        # 同步FastGPT服务
        fastgpt_health = await fastgpt_service.health_check()
        
        # 发送同步完成通知
        await notification_service.send_info_notification(
            title="服务同步完成",
            message=f"GeWe: {'正常' if gewe_health['healthy'] else '异常'}, FastGPT: {'正常' if fastgpt_health['healthy'] else '异常'}",
            target_type="broadcast"
        )
        
        logger.info("服务同步完成")
        
    except Exception as e:
        logger.error(f"同步服务任务失败: {str(e)}")


# ==================== 监控和告警 ====================

@router.get("/monitoring/alerts")
async def get_integration_alerts(
    current_user: User = Depends(get_current_user)
):
    """获取集成服务告警"""
    try:
        alerts = []
        
        # 检查GeWe服务状态
        gewe_stats = gewe_service.get_stats()
        if not gewe_stats["is_healthy"]:
            alerts.append({
                "service": "GeWe",
                "type": "service_down",
                "severity": "high",
                "message": "GeWe服务异常",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if gewe_stats["success_rate"] < 80:
            alerts.append({
                "service": "GeWe",
                "type": "low_success_rate",
                "severity": "medium",
                "message": f"GeWe成功率过低: {gewe_stats['success_rate']}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # 检查FastGPT服务状态
        fastgpt_stats = fastgpt_service.get_stats()
        if not fastgpt_stats["is_healthy"]:
            alerts.append({
                "service": "FastGPT",
                "type": "service_down",
                "severity": "high",
                "message": "FastGPT服务异常",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if fastgpt_stats["success_rate"] < 80:
            alerts.append({
                "service": "FastGPT",
                "type": "low_success_rate",
                "severity": "medium",
                "message": f"FastGPT成功率过低: {fastgpt_stats['success_rate']}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {
            "success": True,
            "data": alerts,
            "total": len(alerts)
        }
    
    except Exception as e:
        logger.error(f"获取集成告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取告警失败: {str(e)}")

