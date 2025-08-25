"""
通知服务
负责系统通知、邮件发送、短信发送等功能
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from app.core.config import settings
from app.core.redis import redis_client
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知类型枚举"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """通知渠道枚举"""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.enabled_channels = [NotificationChannel.WEBSOCKET]
        
        # 根据配置启用其他通知渠道
        if settings.SMTP_HOST:
            self.enabled_channels.append(NotificationChannel.EMAIL)
        
        if settings.SMS_PROVIDER:
            self.enabled_channels.append(NotificationChannel.SMS)
    
    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        target_type: str = "broadcast",
        target_id: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None,
        action_url: Optional[str] = None,
        auto_close: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """发送通知"""
        try:
            # 默认使用WebSocket通知
            channels = channels or [NotificationChannel.WEBSOCKET]
            
            # 过滤可用的通知渠道
            available_channels = [ch for ch in channels if ch in self.enabled_channels]
            
            if not available_channels:
                logger.warning("没有可用的通知渠道")
                return {}
            
            # 创建通知数据
            notification_data = {
                "id": f"notify_{datetime.utcnow().timestamp()}",
                "title": title,
                "message": message,
                "type": notification_type.value,
                "target_type": target_type,
                "target_id": target_id,
                "action_url": action_url,
                "auto_close": auto_close,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "channels": [ch.value for ch in available_channels]
            }
            
            # 存储通知记录
            await self._store_notification(notification_data)
            
            # 并发发送到各个渠道
            tasks = []
            for channel in available_channels:
                if channel == NotificationChannel.WEBSOCKET:
                    task = asyncio.create_task(
                        self._send_websocket_notification(notification_data)
                    )
                elif channel == NotificationChannel.EMAIL:
                    task = asyncio.create_task(
                        self._send_email_notification(notification_data)
                    )
                elif channel == NotificationChannel.SMS:
                    task = asyncio.create_task(
                        self._send_sms_notification(notification_data)
                    )
                
                tasks.append((channel, task))
            
            # 等待所有任务完成
            results = {}
            for channel, task in tasks:
                try:
                    success = await task
                    results[channel.value] = success
                except Exception as e:
                    logger.error(f"通知发送失败 ({channel.value}): {str(e)}")
                    results[channel.value] = False
            
            logger.info(f"通知发送完成: {title} -> {results}")
            return results
            
        except Exception as e:
            logger.error(f"发送通知异常: {str(e)}")
            return {}
    
    async def _send_websocket_notification(self, notification_data: Dict[str, Any]) -> bool:
        """通过WebSocket发送通知"""
        try:
            ws_message = {
                "type": "notification",
                "notification": notification_data
            }
            
            target_type = notification_data["target_type"]
            target_id = notification_data["target_id"]
            
            if target_type == "broadcast":
                success_count = await websocket_manager.broadcast(ws_message)
                return success_count > 0
            elif target_type == "user" and target_id:
                return await websocket_manager.send_to_user(target_id, ws_message)
            elif target_type == "session" and target_id:
                return await websocket_manager.send_to_session(target_id, ws_message)
            
            return False
            
        except Exception as e:
            logger.error(f"WebSocket通知发送失败: {str(e)}")
            return False
    
    async def _send_email_notification(self, notification_data: Dict[str, Any]) -> bool:
        """通过邮件发送通知"""
        try:
            # 这里实现邮件发送逻辑
            # 可以使用fastapi-mail或其他邮件库
            
            # 示例实现（需要实际的邮件发送逻辑）
            logger.info(f"邮件通知: {notification_data['title']}")
            return True
            
        except Exception as e:
            logger.error(f"邮件通知发送失败: {str(e)}")
            return False
    
    async def _send_sms_notification(self, notification_data: Dict[str, Any]) -> bool:
        """通过短信发送通知"""
        try:
            # 这里实现短信发送逻辑
            # 可以集成阿里云短信、腾讯云短信等服务
            
            # 示例实现（需要实际的短信发送逻辑）
            logger.info(f"短信通知: {notification_data['title']}")
            return True
            
        except Exception as e:
            logger.error(f"短信通知发送失败: {str(e)}")
            return False
    
    async def _store_notification(self, notification_data: Dict[str, Any]):
        """存储通知记录"""
        try:
            # 存储到Redis，保留7天
            key = f"notifications:{notification_data['id']}"
            await redis_client.setex(key, 604800, json.dumps(notification_data))  # 7天
            
            # 添加到用户通知列表
            if notification_data.get("target_id") and notification_data["target_type"] == "user":
                user_key = f"user_notifications:{notification_data['target_id']}"
                await redis_client.lpush(user_key, notification_data["id"])
                await redis_client.ltrim(user_key, 0, 99)  # 只保留最近100条
                await redis_client.expire(user_key, 604800)  # 7天过期
            
        except Exception as e:
            logger.error(f"存储通知记录失败: {str(e)}")
    
    # ==================== 快捷通知方法 ====================
    
    async def send_info_notification(
        self,
        title: str,
        message: str,
        target_type: str = "broadcast",
        target_id: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> Dict[str, bool]:
        """发送信息通知"""
        return await self.send_notification(
            title=title,
            message=message,
            notification_type=NotificationType.INFO,
            target_type=target_type,
            target_id=target_id,
            action_url=action_url
        )
    
    async def send_success_notification(
        self,
        title: str,
        message: str,
        target_type: str = "user",
        target_id: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> Dict[str, bool]:
        """发送成功通知"""
        return await self.send_notification(
            title=title,
            message=message,
            notification_type=NotificationType.SUCCESS,
            target_type=target_type,
            target_id=target_id,
            action_url=action_url
        )
    
    async def send_warning_notification(
        self,
        title: str,
        message: str,
        target_type: str = "broadcast",
        target_id: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> Dict[str, bool]:
        """发送警告通知"""
        return await self.send_notification(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            target_type=target_type,
            target_id=target_id,
            action_url=action_url,
            auto_close=False  # 警告通知不自动关闭
        )
    
    async def send_error_notification(
        self,
        title: str,
        message: str,
        target_type: str = "broadcast",
        target_id: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> Dict[str, bool]:
        """发送错误通知"""
        return await self.send_notification(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            target_type=target_type,
            target_id=target_id,
            action_url=action_url,
            auto_close=False  # 错误通知不自动关闭
        )
    
    async def send_urgent_notification(
        self,
        title: str,
        message: str,
        target_type: str = "broadcast",
        target_id: Optional[str] = None,
        action_url: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[str, bool]:
        """发送紧急通知（多渠道）"""
        # 紧急通知使用所有可用渠道
        if not channels:
            channels = self.enabled_channels
        
        return await self.send_notification(
            title=title,
            message=message,
            notification_type=NotificationType.URGENT,
            target_type=target_type,
            target_id=target_id,
            action_url=action_url,
            channels=channels,
            auto_close=False
        )
    
    # ==================== 业务特定通知 ====================
    
    async def send_device_status_notification(
        self,
        account_id: str,
        account_name: str,
        old_status: str,
        new_status: str
    ) -> Dict[str, bool]:
        """发送设备状态变化通知"""
        status_descriptions = {
            "online": "在线",
            "offline": "离线",
            "risk_controlled": "风控",
            "banned": "被封",
            "awaiting_relogin": "等待重新登录"
        }
        
        old_desc = status_descriptions.get(old_status, old_status)
        new_desc = status_descriptions.get(new_status, new_status)
        
        # 根据状态严重程度选择通知类型
        if new_status in ["banned", "risk_controlled"]:
            notification_type = NotificationType.ERROR
        elif new_status == "offline":
            notification_type = NotificationType.WARNING
        else:
            notification_type = NotificationType.INFO
        
        return await self.send_notification(
            title="设备状态变化",
            message=f"设备 {account_name} 状态从 {old_desc} 变更为 {new_desc}",
            notification_type=notification_type,
            target_type="broadcast",
            action_url=f"/devices/{account_id}",
            metadata={
                "account_id": account_id,
                "old_status": old_status,
                "new_status": new_status
            }
        )
    
    async def send_ai_processing_notification(
        self,
        session_id: str,
        message_id: str,
        status: str,
        processing_time: Optional[int] = None
    ) -> Dict[str, bool]:
        """发送AI处理状态通知"""
        status_messages = {
            "processing": "AI正在处理消息...",
            "completed": f"AI处理完成" + (f"，耗时{processing_time}ms" if processing_time else ""),
            "failed": "AI处理失败",
            "skipped": "AI处理已跳过"
        }
        
        message = status_messages.get(status, f"AI处理状态: {status}")
        notification_type = NotificationType.SUCCESS if status == "completed" else NotificationType.INFO
        
        return await self.send_notification(
            title="AI处理状态",
            message=message,
            notification_type=notification_type,
            target_type="session",
            target_id=session_id,
            metadata={
                "session_id": session_id,
                "message_id": message_id,
                "ai_status": status,
                "processing_time": processing_time
            }
        )
    
    async def send_cost_warning_notification(
        self,
        user_id: str,
        current_usage: float,
        quota_limit: float,
        usage_percentage: float
    ) -> Dict[str, bool]:
        """发送成本预警通知"""
        if usage_percentage >= 95:
            title = "算力配额即将耗尽"
            notification_type = NotificationType.ERROR
        elif usage_percentage >= 80:
            title = "算力配额使用警告"
            notification_type = NotificationType.WARNING
        else:
            title = "算力配额使用提醒"
            notification_type = NotificationType.INFO
        
        return await self.send_notification(
            title=title,
            message=f"您的算力配额已使用 {usage_percentage:.1f}% ({current_usage:.2f}/{quota_limit:.2f})",
            notification_type=notification_type,
            target_type="user",
            target_id=user_id,
            action_url="/cost-management",
            metadata={
                "user_id": user_id,
                "current_usage": current_usage,
                "quota_limit": quota_limit,
                "usage_percentage": usage_percentage
            }
        )
    
    async def send_message_status_notification(
        self,
        session_id: str,
        message_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Dict[str, bool]:
        """发送消息状态通知"""
        status_messages = {
            "sent": "消息发送成功",
            "delivered": "消息已送达",
            "failed": f"消息发送失败" + (f": {error_message}" if error_message else ""),
            "pending": "消息发送中..."
        }
        
        message = status_messages.get(status, f"消息状态: {status}")
        notification_type = NotificationType.ERROR if status == "failed" else NotificationType.INFO
        
        return await self.send_notification(
            title="消息状态更新",
            message=message,
            notification_type=notification_type,
            target_type="session",
            target_id=session_id,
            metadata={
                "session_id": session_id,
                "message_id": message_id,
                "message_status": status,
                "error_message": error_message
            }
        )
    
    async def send_system_maintenance_notification(
        self,
        title: str,
        message: str,
        maintenance_start: datetime,
        maintenance_end: datetime
    ) -> Dict[str, bool]:
        """发送系统维护通知"""
        return await self.send_notification(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            target_type="broadcast",
            channels=self.enabled_channels,  # 使用所有可用渠道
            auto_close=False,
            metadata={
                "maintenance_start": maintenance_start.isoformat(),
                "maintenance_end": maintenance_end.isoformat(),
                "duration_minutes": int((maintenance_end - maintenance_start).total_seconds() / 60)
            }
        )
    
    # ==================== 通知查询和管理 ====================
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户通知列表"""
        try:
            user_key = f"user_notifications:{user_id}"
            
            # 从Redis获取通知ID列表
            notification_ids = await redis_client.lrange(user_key, offset, offset + limit - 1)
            
            notifications = []
            for notification_id in notification_ids:
                notification_key = f"notifications:{notification_id.decode()}"
                notification_data = await redis_client.get(notification_key)
                
                if notification_data:
                    notifications.append(json.loads(notification_data))
            
            return notifications
            
        except Exception as e:
            logger.error(f"获取用户通知失败: {str(e)}")
            return []
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """标记通知为已读"""
        try:
            key = f"notification_read:{user_id}:{notification_id}"
            await redis_client.setex(key, 604800, "1")  # 7天过期
            return True
            
        except Exception as e:
            logger.error(f"标记通知已读失败: {str(e)}")
            return False
    
    async def get_unread_notification_count(self, user_id: str) -> int:
        """获取未读通知数量"""
        try:
            user_key = f"user_notifications:{user_id}"
            notification_ids = await redis_client.lrange(user_key, 0, -1)
            
            unread_count = 0
            for notification_id in notification_ids:
                read_key = f"notification_read:{user_id}:{notification_id.decode()}"
                is_read = await redis_client.exists(read_key)
                if not is_read:
                    unread_count += 1
            
            return unread_count
            
        except Exception as e:
            logger.error(f"获取未读通知数量失败: {str(e)}")
            return 0


# 全局通知服务实例
notification_service = NotificationService()

