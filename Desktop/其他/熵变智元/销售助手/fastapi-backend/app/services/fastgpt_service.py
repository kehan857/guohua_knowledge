"""
FastGPT AI服务集成
负责与FastGPT平台的工作流集成，提供AI对话功能
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import httpx
import uuid
from urllib.parse import urljoin

from app.core.config import settings
from app.core.redis import redis_client
from app.services.cost_calculator import cost_calculator, CostCalculationRequest
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class FastGPTModelType(str, Enum):
    """FastGPT模型类型"""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_35_TURBO = "gpt-3.5-turbo"
    DOUBAO_PRO = "doubao-pro-32k"
    DOUBAO_LITE = "doubao-lite-32k"
    CLAUDE_3 = "claude-3-opus"
    CLAUDE_35 = "claude-3.5-sonnet"


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class FastGPTResponse:
    """FastGPT API响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 200
    response_time: float = 0.0
    request_id: Optional[str] = None
    tokens_used: int = 0
    cost: float = 0.0


@dataclass
class WorkflowConfig:
    """工作流配置"""
    workflow_id: str
    name: str
    description: str
    api_endpoint: str
    api_key: str
    model_config: Dict[str, Any]
    variables: Dict[str, Any] = None
    is_active: bool = True


@dataclass
class ChatContext:
    """聊天上下文"""
    user_id: str
    contact_wxid: str
    account_id: str
    session_id: str
    histories: List[Dict[str, Any]] = None
    variables: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


class FastGPTService:
    """FastGPT服务"""
    
    def __init__(self):
        self.base_url = settings.FASTGPT_BASE_URL
        self.default_api_key = settings.FASTGPT_API_KEY
        self.timeout = 60.0  # FastGPT需要更长的超时时间
        
        # 工作流配置缓存
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        self.config_cache_ttl = 300  # 5分钟缓存
        
        # 请求队列管理
        self.request_queue = asyncio.Queue()
        self.max_concurrent_requests = 10
        self.processing_requests = 0
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2.0
        self.backoff_factor = 2.0
        
        # 健康检查
        self.health_check_interval = 120  # 2分钟
        self.last_health_check = None
        self.is_healthy = True
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_response_time": 0.0,
            "average_tokens_per_request": 0.0,
            "last_request_time": None
        }
        
        # 启动请求处理器
        asyncio.create_task(self._start_request_processor())
    
    async def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> FastGPTResponse:
        """发送HTTP请求到FastGPT API"""
        try:
            url = urljoin(self.base_url, endpoint)
            headers = {
                "Authorization": f"Bearer {api_key or self.default_api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"AI-Sales-Assistant/{settings.APP_VERSION}"
            }
            
            request_id = str(uuid.uuid4())
            start_time = time.time()
            
            # 记录请求统计
            self.stats["total_requests"] += 1
            self.stats["last_request_time"] = datetime.utcnow()
            
            # 发送请求
            async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
                response = await client.post(
                    url=url,
                    headers=headers,
                    json=data,
                    **kwargs
                )
            
            response_time = time.time() - start_time
            
            # 处理响应
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # 提取token和成本信息
                    tokens_used = self._extract_tokens(response_data)
                    cost = self._extract_cost(response_data)
                    
                    # 更新统计
                    self._update_stats(response_time, True, tokens_used, cost)
                    
                    return FastGPTResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status_code,
                        response_time=response_time,
                        request_id=request_id,
                        tokens_used=tokens_used,
                        cost=cost
                    )
                except json.JSONDecodeError:
                    self._update_stats(response_time, False, 0, 0.0)
                    return FastGPTResponse(
                        success=False,
                        error="响应JSON解析失败",
                        status_code=response.status_code,
                        response_time=response_time,
                        request_id=request_id
                    )
            else:
                error_msg = f"API请求失败: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except:
                    pass
                
                self._update_stats(response_time, False, 0, 0.0)
                return FastGPTResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code,
                    response_time=response_time,
                    request_id=request_id
                )
        
        except httpx.TimeoutException:
            self.stats["failed_requests"] += 1
            self.stats["timeout_requests"] += 1
            return FastGPTResponse(
                success=False,
                error="请求超时",
                status_code=408,
                request_id=request_id
            )
        except httpx.RequestError as e:
            self.stats["failed_requests"] += 1
            return FastGPTResponse(
                success=False,
                error=f"网络请求错误: {str(e)}",
                status_code=0,
                request_id=request_id
            )
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"FastGPT API请求异常: {str(e)}")
            return FastGPTResponse(
                success=False,
                error=f"未知错误: {str(e)}",
                status_code=500,
                request_id=request_id
            )
    
    def _extract_tokens(self, response_data: Dict[str, Any]) -> int:
        """从响应中提取token使用量"""
        try:
            # FastGPT可能在不同位置返回token信息
            usage = response_data.get("usage", {})
            if usage:
                return usage.get("total_tokens", 0)
            
            # 检查其他可能的位置
            tokens = response_data.get("tokens", 0)
            if tokens:
                return tokens
            
            # 从响应文本长度估算
            response_text = response_data.get("data", {}).get("text", "")
            if response_text:
                # 粗略估算：中文1字符≈1.5token，英文1单词≈1.3token
                return int(len(response_text) * 1.5)
            
            return 0
            
        except Exception as e:
            logger.warning(f"提取token信息失败: {str(e)}")
            return 0
    
    def _extract_cost(self, response_data: Dict[str, Any]) -> float:
        """从响应中提取成本信息"""
        try:
            # FastGPT可能直接返回成本信息
            cost = response_data.get("cost", 0.0)
            if cost:
                return float(cost)
            
            # 或者从usage中获取
            usage = response_data.get("usage", {})
            if usage and "cost" in usage:
                return float(usage["cost"])
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"提取成本信息失败: {str(e)}")
            return 0.0
    
    def _update_stats(self, response_time: float, success: bool, tokens: int, cost: float):
        """更新统计信息"""
        if success:
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += tokens
            self.stats["total_cost"] += cost
        else:
            self.stats["failed_requests"] += 1
        
        # 更新平均响应时间
        total_requests = self.stats["successful_requests"] + self.stats["failed_requests"]
        current_avg = self.stats["average_response_time"]
        self.stats["average_response_time"] = (current_avg * (total_requests - 1) + response_time) / total_requests
        
        # 更新平均token数
        if self.stats["successful_requests"] > 0:
            self.stats["average_tokens_per_request"] = self.stats["total_tokens"] / self.stats["successful_requests"]
    
    async def _start_request_processor(self):
        """启动请求处理器"""
        while True:
            try:
                if self.processing_requests >= self.max_concurrent_requests:
                    await asyncio.sleep(0.1)
                    continue
                
                # 等待队列中的请求
                request_item = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                
                # 并发处理请求
                asyncio.create_task(self._process_request(request_item))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"请求处理器异常: {str(e)}")
                await asyncio.sleep(1.0)
    
    async def _process_request(self, request_item: Dict[str, Any]):
        """处理单个请求"""
        self.processing_requests += 1
        try:
            # 执行实际请求
            response = await self._make_request(**request_item["request_args"])
            
            # 设置结果
            request_item["future"].set_result(response)
            
        except Exception as e:
            request_item["future"].set_exception(e)
        finally:
            self.processing_requests -= 1
    
    # ==================== 工作流管理 ====================
    
    async def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置"""
        try:
            # 先从缓存获取
            if workflow_id in self.workflow_configs:
                config = self.workflow_configs[workflow_id]
                # 检查缓存是否过期
                cache_key = f"workflow_config:{workflow_id}"
                cached_time = await redis_client.get(cache_key)
                if cached_time:
                    cached_dt = datetime.fromisoformat(cached_time.decode())
                    if (datetime.utcnow() - cached_dt).total_seconds() < self.config_cache_ttl:
                        return config
            
            # 从数据库或配置文件获取
            # 这里应该从数据库查询工作流配置
            # 暂时返回默认配置
            config = WorkflowConfig(
                workflow_id=workflow_id,
                name="默认销售工作流",
                description="默认的AI销售对话工作流",
                api_endpoint="/api/v1/chat/completions",
                api_key=self.default_api_key,
                model_config={
                    "model": "doubao-pro-32k",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            # 更新缓存
            self.workflow_configs[workflow_id] = config
            cache_key = f"workflow_config:{workflow_id}"
            await redis_client.setex(cache_key, self.config_cache_ttl, datetime.utcnow().isoformat())
            
            return config
            
        except Exception as e:
            logger.error(f"获取工作流配置失败: {str(e)}")
            return None
    
    async def register_workflow(self, config: WorkflowConfig) -> bool:
        """注册工作流"""
        try:
            # 验证工作流配置
            if not await self._validate_workflow_config(config):
                return False
            
            # 保存到缓存
            self.workflow_configs[config.workflow_id] = config
            
            # 保存到数据库
            # 这里应该保存到数据库
            
            logger.info(f"工作流注册成功: {config.workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"注册工作流失败: {str(e)}")
            return False
    
    async def _validate_workflow_config(self, config: WorkflowConfig) -> bool:
        """验证工作流配置"""
        try:
            # 基本字段检查
            if not config.workflow_id or not config.name or not config.api_endpoint:
                return False
            
            # 测试API连接
            test_response = await self._make_request(
                endpoint="/api/health",
                data={},
                api_key=config.api_key,
                timeout=10.0
            )
            
            return test_response.success
            
        except Exception as e:
            logger.error(f"验证工作流配置失败: {str(e)}")
            return False
    
    # ==================== AI对话处理 ====================
    
    async def process_chat_message(
        self,
        workflow_id: str,
        context: ChatContext,
        user_input: str,
        **kwargs
    ) -> FastGPTResponse:
        """处理聊天消息"""
        try:
            # 获取工作流配置
            workflow_config = await self.get_workflow_config(workflow_id)
            if not workflow_config:
                return FastGPTResponse(
                    success=False,
                    error=f"工作流配置不存在: {workflow_id}"
                )
            
            # 构建请求数据
            request_data = await self._build_chat_request(
                workflow_config, context, user_input, **kwargs
            )
            
            # 记录成本（预估）
            estimated_tokens = await self._estimate_tokens(request_data)
            cost_request = CostCalculationRequest(
                organization_id=context.metadata.get("organization_id", ""),
                user_id=context.user_id,
                model_name=workflow_config.model_config.get("model", "fastgpt"),
                provider="fastgpt",
                request_type="chat_completion",
                input_units=estimated_tokens.get("input", 0),
                output_units=estimated_tokens.get("output", 0),
                metadata={
                    "workflow_id": workflow_id,
                    "session_id": context.session_id,
                    "user_input": user_input[:100]  # 只记录前100字符
                }
            )
            
            # 检查配额
            cost_result = await cost_calculator.calculate_cost(cost_request)
            if not cost_result.success:
                return FastGPTResponse(
                    success=False,
                    error=cost_result.error_message or "配额检查失败"
                )
            
            # 发送AI请求
            future = asyncio.Future()
            request_item = {
                "request_args": {
                    "endpoint": workflow_config.api_endpoint,
                    "data": request_data,
                    "api_key": workflow_config.api_key
                },
                "future": future
            }
            
            await self.request_queue.put(request_item)
            response = await future
            
            # 如果成功，记录实际成本
            if response.success:
                actual_cost_request = CostCalculationRequest(
                    organization_id=context.metadata.get("organization_id", ""),
                    user_id=context.user_id,
                    model_name=workflow_config.model_config.get("model", "fastgpt"),
                    provider="fastgpt",
                    request_type="chat_completion",
                    input_units=response.tokens_used,  # 使用实际token数
                    metadata={
                        "workflow_id": workflow_id,
                        "session_id": context.session_id,
                        "response_time": response.response_time,
                        "request_id": response.request_id
                    }
                )
                
                await cost_calculator.calculate_cost(actual_cost_request)
                
                # 发送WebSocket通知
                await websocket_manager.send_to_user(context.user_id, {
                    "type": "ai_response",
                    "session_id": context.session_id,
                    "response": response.data,
                    "tokens_used": response.tokens_used,
                    "cost": response.cost
                })
            
            return response
            
        except Exception as e:
            logger.error(f"处理聊天消息失败: {str(e)}")
            return FastGPTResponse(
                success=False,
                error=f"处理失败: {str(e)}"
            )
    
    async def _build_chat_request(
        self,
        workflow_config: WorkflowConfig,
        context: ChatContext,
        user_input: str,
        **kwargs
    ) -> Dict[str, Any]:
        """构建聊天请求数据"""
        try:
            # 基础请求数据
            request_data = {
                "userChatInput": user_input,
                "variables": {
                    # 基础变量
                    "role": context.metadata.get("role", "销售助手"),
                    "nickName": context.metadata.get("contact_nickname", "客户"),
                    "accountNo": context.metadata.get("account_no", ""),
                    "nickId": context.contact_wxid,
                    
                    # 聊天历史
                    "histories": context.histories or [],
                    
                    # 自定义变量
                    **(context.variables or {}),
                    **(workflow_config.variables or {})
                },
                "chatConfig": workflow_config.model_config,
                "metadata": {
                    "sessionId": context.session_id,
                    "userId": context.user_id,
                    "accountId": context.account_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # 添加图片URL（如果有）
            if "picture" in kwargs:
                request_data["variables"]["picture"] = kwargs["picture"]
            
            # 添加其他扩展参数
            for key, value in kwargs.items():
                if key not in ["picture"]:
                    request_data["variables"][key] = value
            
            return request_data
            
        except Exception as e:
            logger.error(f"构建聊天请求失败: {str(e)}")
            return {}
    
    async def _estimate_tokens(self, request_data: Dict[str, Any]) -> Dict[str, int]:
        """估算token使用量"""
        try:
            # 简单的token估算
            user_input = request_data.get("userChatInput", "")
            variables = request_data.get("variables", {})
            histories = variables.get("histories", [])
            
            # 输入token估算
            input_text = user_input
            for history in histories[-5:]:  # 只考虑最近5条历史
                input_text += history.get("content", "")
            
            input_tokens = int(len(input_text) * 1.5)  # 粗略估算
            
            # 输出token估算（根据模型配置）
            chat_config = request_data.get("chatConfig", {})
            max_tokens = chat_config.get("max_tokens", 2000)
            output_tokens = min(max_tokens, input_tokens * 2)  # 估算输出为输入的2倍
            
            return {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }
            
        except Exception as e:
            logger.error(f"估算token失败: {str(e)}")
            return {"input": 1000, "output": 2000, "total": 3000}  # 默认估算
    
    # ==================== 批量处理 ====================
    
    async def process_batch_messages(
        self,
        workflow_id: str,
        messages: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> List[FastGPTResponse]:
        """批量处理消息"""
        try:
            responses = []
            
            # 分批处理
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                # 并发处理批次
                tasks = []
                for message_data in batch:
                    context = ChatContext(**message_data["context"])
                    user_input = message_data["user_input"]
                    
                    task = asyncio.create_task(
                        self.process_chat_message(workflow_id, context, user_input)
                    )
                    tasks.append(task)
                
                # 等待批次完成
                batch_responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                for response in batch_responses:
                    if isinstance(response, Exception):
                        responses.append(FastGPTResponse(
                            success=False,
                            error=str(response)
                        ))
                    else:
                        responses.append(response)
                
                # 批次间延迟
                if i + batch_size < len(messages):
                    await asyncio.sleep(1.0)
            
            return responses
            
        except Exception as e:
            logger.error(f"批量处理消息失败: {str(e)}")
            return []
    
    # ==================== 意图分析 ====================
    
    async def analyze_intent(
        self,
        user_input: str,
        context: Optional[ChatContext] = None
    ) -> FastGPTResponse:
        """分析用户意图"""
        try:
            # 构建意图分析请求
            request_data = {
                "userChatInput": user_input,
                "variables": {
                    "analysisType": "intent_classification",
                    "context": context.metadata if context else {}
                },
                "chatConfig": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            }
            
            return await self._make_request(
                endpoint="/api/v1/intent/analyze",
                data=request_data
            )
            
        except Exception as e:
            logger.error(f"意图分析失败: {str(e)}")
            return FastGPTResponse(
                success=False,
                error=f"意图分析失败: {str(e)}"
            )
    
    async def analyze_sentiment(
        self,
        user_input: str,
        context: Optional[ChatContext] = None
    ) -> FastGPTResponse:
        """分析情感倾向"""
        try:
            # 构建情感分析请求
            request_data = {
                "userChatInput": user_input,
                "variables": {
                    "analysisType": "sentiment_analysis",
                    "context": context.metadata if context else {}
                },
                "chatConfig": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.1,
                    "max_tokens": 300
                }
            }
            
            return await self._make_request(
                endpoint="/api/v1/sentiment/analyze",
                data=request_data
            )
            
        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            return FastGPTResponse(
                success=False,
                error=f"情感分析失败: {str(e)}"
            )
    
    # ==================== 健康检查和监控 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = time.time()
            
            # 发送健康检查请求
            response = await self._make_request(
                endpoint="/api/health",
                data={}
            )
            
            response_time = time.time() - start_time
            
            self.last_health_check = datetime.utcnow()
            self.is_healthy = response.success
            
            return {
                "healthy": response.success,
                "response_time": response_time,
                "last_check": self.last_health_check.isoformat(),
                "queue_size": self.request_queue.qsize(),
                "processing_requests": self.processing_requests,
                "stats": self.get_stats()
            }
            
        except Exception as e:
            logger.error(f"FastGPT健康检查失败: {str(e)}")
            self.is_healthy = False
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self.stats["total_requests"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["total_requests"]) * 100
        
        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "is_healthy": self.is_healthy,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "workflow_count": len(self.workflow_configs),
            "queue_size": self.request_queue.qsize(),
            "processing_requests": self.processing_requests
        }
    
    async def clear_cache(self):
        """清空缓存"""
        self.workflow_configs.clear()
        logger.info("FastGPT服务缓存已清空")
    
    async def reload_workflows(self):
        """重新加载工作流配置"""
        await self.clear_cache()
        # 这里应该从数据库重新加载所有工作流配置
        logger.info("工作流配置已重新加载")


# 全局FastGPT服务实例
fastgpt_service = FastGPTService()

