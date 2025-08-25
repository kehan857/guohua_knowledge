"""
GeWe微信自动化服务
负责与GeWe平台的API集成，提供微信自动化功能
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


class GeWeMessageType(str, Enum):
    """GeWe消息类型"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VIDEO = "video"
    AUDIO = "audio"
    LOCATION = "location"
    LINK = "link"
    MINIPROGRAM = "miniprogram"
    EMOJI = "emoji"
    CONTACT = "contact"


class GeWeAccountStatus(str, Enum):
    """GeWe账号状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    LOGIN_REQUIRED = "login_required"
    RISK_CONTROL = "risk_control"
    BANNED = "banned"
    UNKNOWN = "unknown"


@dataclass
class GeWeResponse:
    """GeWe API响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 200
    response_time: float = 0.0
    request_id: Optional[str] = None


@dataclass
class RateLimitInfo:
    """限流信息"""
    requests_per_minute: int = 40
    current_count: int = 0
    reset_time: datetime = None
    blocked_until: Optional[datetime] = None


class GeWeService:
    """GeWe服务"""
    
    def __init__(self):
        self.base_url = settings.GEWE_BASE_URL
        self.timeout = 30.0
        
        # 限流配置
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.global_rate_limit = RateLimitInfo()
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_factor = 2.0
        
        # 健康检查
        self.health_check_interval = 60  # 60秒
        self.last_health_check = None
        self.is_healthy = True
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "average_response_time": 0.0,
            "last_request_time": None
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        token_id: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> GeWeResponse:
        """发送HTTP请求到GeWe API"""
        try:
            # 检查限流
            await self._check_rate_limit(token_id)
            
            # 准备请求
            url = urljoin(self.base_url, endpoint)
            headers = {
                "Authorization": f"Bearer {token_id}",
                "Content-Type": "application/json",
                "User-Agent": f"AI-Sales-Assistant/{settings.APP_VERSION}"
            }
            
            request_id = str(uuid.uuid4())
            start_time = time.time()
            
            # 记录请求统计
            self.stats["total_requests"] += 1
            self.stats["last_request_time"] = datetime.utcnow()
            
            # 发送请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if files:
                    # 文件上传请求
                    headers.pop("Content-Type", None)  # 让httpx自动设置
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data,
                        files=files,
                        **kwargs
                    )
                else:
                    # 普通JSON请求
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        **kwargs
                    )
            
            response_time = time.time() - start_time
            
            # 更新统计
            self._update_stats(response_time, response.status_code < 400)
            
            # 更新限流计数
            await self._update_rate_limit(token_id)
            
            # 处理响应
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return GeWeResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status_code,
                        response_time=response_time,
                        request_id=request_id
                    )
                except json.JSONDecodeError:
                    return GeWeResponse(
                        success=False,
                        error="响应JSON解析失败",
                        status_code=response.status_code,
                        response_time=response_time,
                        request_id=request_id
                    )
            elif response.status_code == 429:
                # 限流响应
                self.stats["rate_limited_requests"] += 1
                await self._handle_rate_limit(token_id, response)
                return GeWeResponse(
                    success=False,
                    error="请求频率过高，已被限流",
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
                
                return GeWeResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code,
                    response_time=response_time,
                    request_id=request_id
                )
        
        except httpx.TimeoutException:
            self.stats["failed_requests"] += 1
            return GeWeResponse(
                success=False,
                error="请求超时",
                status_code=408,
                request_id=request_id
            )
        except httpx.RequestError as e:
            self.stats["failed_requests"] += 1
            return GeWeResponse(
                success=False,
                error=f"网络请求错误: {str(e)}",
                status_code=0,
                request_id=request_id
            )
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"GeWe API请求异常: {str(e)}")
            return GeWeResponse(
                success=False,
                error=f"未知错误: {str(e)}",
                status_code=500,
                request_id=request_id
            )
    
    async def _check_rate_limit(self, token_id: str):
        """检查限流"""
        now = datetime.utcnow()
        
        # 检查全局限流
        if self.global_rate_limit.blocked_until and now < self.global_rate_limit.blocked_until:
            wait_time = (self.global_rate_limit.blocked_until - now).total_seconds()
            logger.warning(f"全局限流中，等待 {wait_time:.1f} 秒")
            await asyncio.sleep(wait_time)
        
        # 检查账号限流
        if token_id in self.rate_limits:
            rate_limit = self.rate_limits[token_id]
            if rate_limit.blocked_until and now < rate_limit.blocked_until:
                wait_time = (rate_limit.blocked_until - now).total_seconds()
                logger.warning(f"账号 {token_id} 限流中，等待 {wait_time:.1f} 秒")
                await asyncio.sleep(wait_time)
    
    async def _update_rate_limit(self, token_id: str):
        """更新限流计数"""
        now = datetime.utcnow()
        
        # 更新全局限流
        if not self.global_rate_limit.reset_time or now >= self.global_rate_limit.reset_time:
            self.global_rate_limit.current_count = 0
            self.global_rate_limit.reset_time = now + timedelta(minutes=1)
        
        self.global_rate_limit.current_count += 1
        
        # 更新账号限流
        if token_id not in self.rate_limits:
            self.rate_limits[token_id] = RateLimitInfo()
        
        rate_limit = self.rate_limits[token_id]
        if not rate_limit.reset_time or now >= rate_limit.reset_time:
            rate_limit.current_count = 0
            rate_limit.reset_time = now + timedelta(minutes=1)
        
        rate_limit.current_count += 1
        
        # 检查是否需要主动限流
        if rate_limit.current_count >= rate_limit.requests_per_minute:
            rate_limit.blocked_until = rate_limit.reset_time
            logger.warning(f"账号 {token_id} 达到限流阈值，暂停到下个周期")
    
    async def _handle_rate_limit(self, token_id: str, response: httpx.Response):
        """处理限流响应"""
        try:
            # 尝试从响应头获取重试时间
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                wait_time = int(retry_after)
            else:
                wait_time = 60  # 默认等待1分钟
            
            # 设置限流时间
            blocked_until = datetime.utcnow() + timedelta(seconds=wait_time)
            
            if token_id in self.rate_limits:
                self.rate_limits[token_id].blocked_until = blocked_until
            
            logger.warning(f"账号 {token_id} 被服务器限流，等待 {wait_time} 秒")
            
        except Exception as e:
            logger.error(f"处理限流响应失败: {str(e)}")
    
    def _update_stats(self, response_time: float, success: bool):
        """更新统计信息"""
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        # 更新平均响应时间
        total_requests = self.stats["successful_requests"] + self.stats["failed_requests"]
        current_avg = self.stats["average_response_time"]
        self.stats["average_response_time"] = (current_avg * (total_requests - 1) + response_time) / total_requests
    
    # ==================== 账号管理 ====================
    
    async def get_account_status(self, token_id: str, account_id: str) -> GeWeResponse:
        """获取账号状态"""
        return await self._make_request(
            method="GET",
            endpoint=f"/api/account/{account_id}/status",
            token_id=token_id
        )
    
    async def get_account_list(self, token_id: str) -> GeWeResponse:
        """获取账号列表"""
        return await self._make_request(
            method="GET",
            endpoint="/api/accounts",
            token_id=token_id
        )
    
    async def get_login_qrcode(self, token_id: str, app_id: Optional[str] = None) -> GeWeResponse:
        """获取登录二维码"""
        data = {}
        if app_id:
            data["appId"] = app_id
        
        return await self._make_request(
            method="POST",
            endpoint="/api/account/qrcode",
            token_id=token_id,
            data=data
        )
    
    async def logout_account(self, token_id: str, account_id: str) -> GeWeResponse:
        """账号登出"""
        return await self._make_request(
            method="POST",
            endpoint=f"/api/account/{account_id}/logout",
            token_id=token_id
        )
    
    # ==================== 消息发送 ====================
    
    async def send_text_message(
        self,
        token_id: str,
        wxid: str,
        message: str,
        account_id: Optional[str] = None
    ) -> GeWeResponse:
        """发送文本消息"""
        data = {
            "wxid": wxid,
            "message": message
        }
        if account_id:
            data["accountId"] = account_id
        
        # 记录成本
        await self._record_message_cost(token_id, "send_text", len(message))
        
        response = await self._make_request(
            method="POST",
            endpoint="/api/message/text",
            token_id=token_id,
            data=data
        )
        
        # 智能延迟，模拟人的行为
        await self._intelligent_delay()
        
        return response
    
    async def send_image_message(
        self,
        token_id: str,
        wxid: str,
        image_path: str,
        account_id: Optional[str] = None
    ) -> GeWeResponse:
        """发送图片消息"""
        data = {
            "wxid": wxid
        }
        if account_id:
            data["accountId"] = account_id
        
        # 记录成本
        await self._record_message_cost(token_id, "send_image", 1)
        
        # 准备文件
        try:
            with open(image_path, 'rb') as f:
                files = {"image": (image_path, f, "image/jpeg")}
                response = await self._make_request(
                    method="POST",
                    endpoint="/api/message/image",
                    token_id=token_id,
                    data=data,
                    files=files
                )
        except FileNotFoundError:
            return GeWeResponse(
                success=False,
                error=f"图片文件不存在: {image_path}"
            )
        
        await self._intelligent_delay()
        return response
    
    async def send_file_message(
        self,
        token_id: str,
        wxid: str,
        file_path: str,
        account_id: Optional[str] = None
    ) -> GeWeResponse:
        """发送文件消息"""
        data = {
            "wxid": wxid
        }
        if account_id:
            data["accountId"] = account_id
        
        # 记录成本
        await self._record_message_cost(token_id, "send_file", 1)
        
        try:
            with open(file_path, 'rb') as f:
                files = {"file": (file_path, f, "application/octet-stream")}
                response = await self._make_request(
                    method="POST",
                    endpoint="/api/message/file",
                    token_id=token_id,
                    data=data,
                    files=files
                )
        except FileNotFoundError:
            return GeWeResponse(
                success=False,
                error=f"文件不存在: {file_path}"
            )
        
        await self._intelligent_delay()
        return response
    
    # ==================== 联系人管理 ====================
    
    async def get_contact_list(self, token_id: str, account_id: str) -> GeWeResponse:
        """获取联系人列表"""
        return await self._make_request(
            method="GET",
            endpoint=f"/api/account/{account_id}/contacts",
            token_id=token_id
        )
    
    async def get_contact_info(self, token_id: str, account_id: str, wxid: str) -> GeWeResponse:
        """获取联系人信息"""
        return await self._make_request(
            method="GET",
            endpoint=f"/api/account/{account_id}/contact/{wxid}",
            token_id=token_id
        )
    
    async def add_contact(
        self,
        token_id: str,
        account_id: str,
        wxid: str,
        verify_message: str = ""
    ) -> GeWeResponse:
        """添加联系人"""
        data = {
            "wxid": wxid,
            "verifyMessage": verify_message
        }
        
        return await self._make_request(
            method="POST",
            endpoint=f"/api/account/{account_id}/contact/add",
            token_id=token_id,
            data=data
        )
    
    async def delete_contact(self, token_id: str, account_id: str, wxid: str) -> GeWeResponse:
        """删除联系人"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/api/account/{account_id}/contact/{wxid}",
            token_id=token_id
        )
    
    async def update_contact_remark(
        self,
        token_id: str,
        account_id: str,
        wxid: str,
        remark: str
    ) -> GeWeResponse:
        """更新联系人备注"""
        data = {
            "remark": remark
        }
        
        return await self._make_request(
            method="PUT",
            endpoint=f"/api/account/{account_id}/contact/{wxid}/remark",
            token_id=token_id,
            data=data
        )
    
    # ==================== 群聊管理 ====================
    
    async def get_group_list(self, token_id: str, account_id: str) -> GeWeResponse:
        """获取群聊列表"""
        return await self._make_request(
            method="GET",
            endpoint=f"/api/account/{account_id}/groups",
            token_id=token_id
        )
    
    async def get_group_members(self, token_id: str, account_id: str, group_wxid: str) -> GeWeResponse:
        """获取群成员列表"""
        return await self._make_request(
            method="GET",
            endpoint=f"/api/account/{account_id}/group/{group_wxid}/members",
            token_id=token_id
        )
    
    async def invite_to_group(
        self,
        token_id: str,
        account_id: str,
        group_wxid: str,
        member_wxids: List[str]
    ) -> GeWeResponse:
        """邀请加入群聊"""
        data = {
            "memberWxids": member_wxids
        }
        
        return await self._make_request(
            method="POST",
            endpoint=f"/api/account/{account_id}/group/{group_wxid}/invite",
            token_id=token_id,
            data=data
        )
    
    async def remove_from_group(
        self,
        token_id: str,
        account_id: str,
        group_wxid: str,
        member_wxids: List[str]
    ) -> GeWeResponse:
        """移除群成员"""
        data = {
            "memberWxids": member_wxids
        }
        
        return await self._make_request(
            method="POST",
            endpoint=f"/api/account/{account_id}/group/{group_wxid}/remove",
            token_id=token_id,
            data=data
        )
    
    # ==================== 朋友圈管理 ====================
    
    async def post_moments(
        self,
        token_id: str,
        account_id: str,
        content: str,
        images: Optional[List[str]] = None
    ) -> GeWeResponse:
        """发布朋友圈"""
        data = {
            "content": content
        }
        
        files = {}
        if images:
            for i, image_path in enumerate(images):
                try:
                    with open(image_path, 'rb') as f:
                        files[f"image_{i}"] = (image_path, f.read(), "image/jpeg")
                except FileNotFoundError:
                    logger.warning(f"朋友圈图片文件不存在: {image_path}")
        
        # 记录成本
        await self._record_message_cost(token_id, "post_moments", len(content))
        
        response = await self._make_request(
            method="POST",
            endpoint=f"/api/account/{account_id}/moments",
            token_id=token_id,
            data=data,
            files=files if files else None
        )
        
        await self._intelligent_delay()
        return response
    
    async def get_moments_timeline(self, token_id: str, account_id: str, limit: int = 20) -> GeWeResponse:
        """获取朋友圈时间线"""
        params = {"limit": limit}
        
        return await self._make_request(
            method="GET",
            endpoint=f"/api/account/{account_id}/moments",
            token_id=token_id,
            params=params
        )
    
    async def like_moments(
        self,
        token_id: str,
        account_id: str,
        moments_id: str
    ) -> GeWeResponse:
        """点赞朋友圈"""
        return await self._make_request(
            method="POST",
            endpoint=f"/api/account/{account_id}/moments/{moments_id}/like",
            token_id=token_id
        )
    
    async def comment_moments(
        self,
        token_id: str,
        account_id: str,
        moments_id: str,
        comment: str
    ) -> GeWeResponse:
        """评论朋友圈"""
        data = {
            "comment": comment
        }
        
        # 记录成本
        await self._record_message_cost(token_id, "comment_moments", len(comment))
        
        return await self._make_request(
            method="POST",
            endpoint=f"/api/account/{account_id}/moments/{moments_id}/comment",
            token_id=token_id,
            data=data
        )
    
    # ==================== 辅助功能 ====================
    
    async def _intelligent_delay(self):
        """智能延迟，模拟人的行为"""
        # 随机延迟 1-3 秒
        import random
        delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(delay)
    
    async def _record_message_cost(self, token_id: str, action_type: str, units: int):
        """记录消息成本"""
        try:
            # 这里应该根据实际的成本模型计算
            # 暂时使用固定成本
            base_cost = {
                "send_text": 0.001,
                "send_image": 0.005,
                "send_file": 0.01,
                "post_moments": 0.002,
                "comment_moments": 0.001
            }
            
            cost_per_unit = base_cost.get(action_type, 0.001)
            
            # 创建成本计算请求
            cost_request = CostCalculationRequest(
                organization_id="",  # 需要从token_id获取
                user_id="",          # 需要从token_id获取
                model_name="gewe_api",
                provider="gewe",
                request_type=action_type,
                base_units=units,
                metadata={
                    "action_type": action_type,
                    "units": units,
                    "token_id": token_id
                }
            )
            
            # 计算成本（这里简化处理）
            # await cost_calculator.calculate_cost(cost_request)
            
        except Exception as e:
            logger.error(f"记录消息成本失败: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            start_time = time.time()
            
            # 发送健康检查请求
            response = await self._make_request(
                method="GET",
                endpoint="/api/health",
                token_id="health_check"  # 使用特殊token
            )
            
            response_time = time.time() - start_time
            
            self.last_health_check = datetime.utcnow()
            self.is_healthy = response.success
            
            return {
                "healthy": response.success,
                "response_time": response_time,
                "last_check": self.last_health_check.isoformat(),
                "stats": self.get_stats()
            }
            
        except Exception as e:
            logger.error(f"GeWe健康检查失败: {str(e)}")
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
            "active_rate_limits": len(self.rate_limits)
        }
    
    async def setup_webhook(self, token_id: str, webhook_url: str) -> GeWeResponse:
        """设置webhook回调地址"""
        data = {
            "webhookUrl": webhook_url
        }
        
        return await self._make_request(
            method="POST",
            endpoint="/api/webhook/setup",
            token_id=token_id,
            data=data
        )
    
    async def process_webhook_message(self, message_data: Dict[str, Any]) -> bool:
        """处理webhook消息"""
        try:
            message_type = message_data.get("type")
            account_id = message_data.get("accountId")
            
            # 根据消息类型进行处理
            if message_type == "message":
                await self._handle_incoming_message(message_data)
            elif message_type == "contact_change":
                await self._handle_contact_change(message_data)
            elif message_type == "account_status":
                await self._handle_account_status_change(message_data)
            else:
                logger.warning(f"未知的webhook消息类型: {message_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"处理webhook消息失败: {str(e)}")
            return False
    
    async def _handle_incoming_message(self, message_data: Dict[str, Any]):
        """处理收到的消息"""
        try:
            # 提取消息信息
            account_id = message_data.get("accountId")
            from_wxid = message_data.get("fromWxid")
            content = message_data.get("content", "")
            message_type = message_data.get("messageType", "text")
            
            # 广播消息到WebSocket
            await websocket_manager.broadcast({
                "type": "incoming_message",
                "data": {
                    "account_id": account_id,
                    "from_wxid": from_wxid,
                    "content": content,
                    "message_type": message_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            # 触发SOP或AI回复逻辑
            # 这里可以集成SOP调度器
            
        except Exception as e:
            logger.error(f"处理收到消息失败: {str(e)}")
    
    async def _handle_contact_change(self, message_data: Dict[str, Any]):
        """处理联系人变化"""
        try:
            change_type = message_data.get("changeType")  # added, deleted, updated
            contact_info = message_data.get("contact", {})
            
            # 发送通知
            await notification_service.send_info_notification(
                title="联系人变化",
                message=f"联系人{contact_info.get('nickname', '')}已{change_type}",
                target_type="broadcast"
            )
            
        except Exception as e:
            logger.error(f"处理联系人变化失败: {str(e)}")
    
    async def _handle_account_status_change(self, message_data: Dict[str, Any]):
        """处理账号状态变化"""
        try:
            account_id = message_data.get("accountId")
            old_status = message_data.get("oldStatus")
            new_status = message_data.get("newStatus")
            
            # 发送状态变化通知
            await notification_service.send_device_status_notification(
                account_id=account_id,
                account_name=message_data.get("accountName", account_id),
                old_status=old_status,
                new_status=new_status
            )
            
        except Exception as e:
            logger.error(f"处理账号状态变化失败: {str(e)}")


# 全局GeWe服务实例
gewe_service = GeWeService()