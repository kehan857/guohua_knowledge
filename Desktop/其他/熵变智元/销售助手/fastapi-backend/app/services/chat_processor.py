"""
聊天消息处理服务
负责处理收到的消息，AI自动回复，消息路由等核心逻辑
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.device import WeChatAccount, DeviceStatus
from app.models.chat import (
    Contact, ChatSession, ChatMessage, 
    ChatType, MessageType, MessageDirection, MessageStatus, AIProcessStatus
)
from app.models.user import User
from app.services.ai_service import AIService, AIServiceError
from app.services.gewe_service import GeWeService
from app.services.websocket_manager import WebSocketManager
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ChatProcessor:
    """聊天消息处理器"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.gewe_service = GeWeService()
        self.ws_manager = WebSocketManager()
        self.notification_service = NotificationService()
        self.is_running = False
        
        # 处理队列
        self.message_queue = asyncio.Queue()
        self.processing_tasks = []
    
    async def start(self):
        """启动消息处理服务"""
        if self.is_running:
            logger.warning("聊天处理服务已在运行")
            return
        
        self.is_running = True
        logger.info("启动聊天消息处理服务")
        
        # 启动处理任务
        for i in range(3):  # 启动3个并发处理任务
            task = asyncio.create_task(self._process_message_queue())
            self.processing_tasks.append(task)
        
        # 启动定期任务
        asyncio.create_task(self._process_pending_messages())
        asyncio.create_task(self._cleanup_old_messages())
    
    async def stop(self):
        """停止消息处理服务"""
        self.is_running = False
        logger.info("停止聊天消息处理服务")
        
        # 取消所有处理任务
        for task in self.processing_tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
    
    async def handle_incoming_message(self, callback_data: Dict[str, Any]) -> bool:
        """处理来自GeWe的消息回调"""
        try:
            logger.debug(f"收到GeWe消息回调: {callback_data.get('messageId', 'unknown')}")
            
            # 解析消息数据
            message_data = self._parse_gewe_callback(callback_data)
            if not message_data:
                return False
            
            # 查找或创建联系人和会话
            async with get_db() as db:
                contact, session = await self._get_or_create_contact_session(db, message_data)
                
                # 创建消息记录
                message = await self._create_message_record(db, session, message_data)
                
                # 更新会话和联系人统计
                session.update_last_message(message)
                session.increment_unread()
                contact.update_message_stats(MessageDirection.INCOMING)
                
                await db.commit()
                await db.refresh(message)
            
            # 推送到WebSocket
            await self._broadcast_new_message(session.id, message)
            
            # 加入AI处理队列
            if self._should_process_with_ai(message, session):
                await self.message_queue.put({
                    "message_id": str(message.id),
                    "type": "ai_process"
                })
            
            logger.info(f"消息处理完成: {message.id}")
            return True
            
        except Exception as e:
            logger.error(f"处理消息回调失败: {str(e)}")
            return False
    
    def _parse_gewe_callback(self, callback_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析GeWe回调数据"""
        try:
            message_info = callback_data.get("message", {})
            
            # 提取基本信息
            message_data = {
                "gewe_message_id": callback_data.get("messageId"),
                "gewe_timestamp": callback_data.get("timestamp"),
                "app_id": callback_data.get("appId"),
                
                # 消息内容
                "message_type": self._map_gewe_message_type(message_info.get("type")),
                "content": message_info.get("content"),
                "media_url": message_info.get("mediaUrl"),
                "media_type": message_info.get("mediaType"),
                
                # 发送者信息
                "sender_wxid": message_info.get("fromWxid"),
                "sender_nickname": message_info.get("fromNickname"),
                
                # 接收者信息
                "receiver_wxid": message_info.get("toWxid"),
                "chat_type": ChatType.GROUP if message_info.get("isGroup") else ChatType.PRIVATE
            }
            
            return message_data
            
        except Exception as e:
            logger.error(f"解析GeWe回调数据失败: {str(e)}")
            return None
    
    def _map_gewe_message_type(self, gewe_type: str) -> MessageType:
        """映射GeWe消息类型到系统消息类型"""
        type_mapping = {
            "text": MessageType.TEXT,
            "image": MessageType.IMAGE,
            "video": MessageType.VIDEO,
            "voice": MessageType.VOICE,
            "file": MessageType.FILE,
            "link": MessageType.LINK,
            "location": MessageType.LOCATION,
            "system": MessageType.SYSTEM
        }
        
        return type_mapping.get(gewe_type, MessageType.TEXT)
    
    async def _get_or_create_contact_session(
        self,
        db: AsyncSession,
        message_data: Dict[str, Any]
    ) -> Tuple[Contact, ChatSession]:
        """获取或创建联系人和会话"""
        
        # 查找微信账号
        account_result = await db.execute(
            select(WeChatAccount)
            .where(WeChatAccount.gewe_app_id == message_data["app_id"])
        )
        account = account_result.scalar_one_or_none()
        
        if not account:
            raise ValueError(f"未找到对应的微信账号: {message_data['app_id']}")
        
        # 确定联系人微信ID
        contact_wxid = message_data["sender_wxid"]
        if message_data["chat_type"] == ChatType.GROUP:
            # 群聊时，联系人是群
            contact_wxid = message_data["receiver_wxid"]
        
        # 查找或创建联系人
        contact_result = await db.execute(
            select(Contact)
            .where(
                Contact.wechat_account_id == account.id,
                Contact.wxid == contact_wxid
            )
        )
        contact = contact_result.scalar_one_or_none()
        
        if not contact:
            contact = Contact(
                organization_id=account.organization_id,
                wechat_account_id=account.id,
                wxid=contact_wxid,
                nickname=message_data.get("sender_nickname") if message_data["chat_type"] == ChatType.PRIVATE else None,
                contact_type="group" if message_data["chat_type"] == ChatType.GROUP else "friend",
                first_contact_at=datetime.utcnow()
            )
            db.add(contact)
            await db.flush()  # 获取ID但不提交
        
        # 查找或创建会话
        session_result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.wechat_account_id == account.id,
                ChatSession.contact_id == contact.id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            session = ChatSession(
                organization_id=account.organization_id,
                wechat_account_id=account.id,
                contact_id=contact.id,
                chat_type=message_data["chat_type"],
                session_name=contact.display_name
            )
            db.add(session)
            await db.flush()
        
        return contact, session
    
    async def _create_message_record(
        self,
        db: AsyncSession,
        session: ChatSession,
        message_data: Dict[str, Any]
    ) -> ChatMessage:
        """创建消息记录"""
        
        message = ChatMessage(
            session_id=session.id,
            message_type=message_data["message_type"],
            direction=MessageDirection.INCOMING,
            content=message_data.get("content"),
            sender_wxid=message_data["sender_wxid"],
            sender_nickname=message_data.get("sender_nickname"),
            media_url=message_data.get("media_url"),
            media_type=message_data.get("media_type"),
            gewe_message_id=message_data.get("gewe_message_id"),
            gewe_timestamp=message_data.get("gewe_timestamp"),
            status=MessageStatus.DELIVERED
        )
        
        db.add(message)
        return message
    
    def _should_process_with_ai(self, message: ChatMessage, session: ChatSession) -> bool:
        """判断是否需要AI处理"""
        # 检查基本条件
        if not session.ai_enabled or not session.auto_reply_enabled:
            return False
        
        # 只处理文本消息
        if message.message_type != MessageType.TEXT:
            return False
        
        # 检查消息内容
        if not message.content or len(message.content.strip()) == 0:
            return False
        
        # 检查是否在工作时间（可配置）
        current_hour = datetime.now().hour
        if current_hour < 8 or current_hour > 22:  # 晚上10点到早上8点不自动回复
            return False
        
        return True
    
    async def _broadcast_new_message(self, session_id: str, message: ChatMessage):
        """广播新消息到WebSocket"""
        try:
            message_data = {
                "type": "new_message",
                "session_id": session_id,
                "message": {
                    "id": str(message.id),
                    "content": message.content,
                    "sender_wxid": message.sender_wxid,
                    "sender_nickname": message.sender_nickname,
                    "message_type": message.message_type.value,
                    "direction": message.direction.value,
                    "created_at": message.created_at.isoformat()
                }
            }
            
            await self.ws_manager.broadcast_to_session(session_id, message_data)
            
        except Exception as e:
            logger.error(f"广播新消息失败: {str(e)}")
    
    async def _process_message_queue(self):
        """处理消息队列"""
        while self.is_running:
            try:
                # 从队列获取消息
                task_data = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=5.0
                )
                
                if task_data["type"] == "ai_process":
                    await self._process_ai_message(task_data["message_id"])
                
                # 标记任务完成
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"处理消息队列异常: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_ai_message(self, message_id: str):
        """AI处理单条消息"""
        try:
            async with get_db() as db:
                # 获取消息和相关信息
                message_result = await db.execute(
                    select(ChatMessage)
                    .options(
                        selectinload(ChatMessage.session)
                        .selectinload(ChatSession.contact),
                        selectinload(ChatMessage.session)
                        .selectinload(ChatSession.wechat_account)
                    )
                    .where(ChatMessage.id == message_id)
                )
                message = message_result.scalar_one_or_none()
                
                if not message or message.ai_process_status != AIProcessStatus.PENDING:
                    return
                
                # 标记为处理中
                message.mark_ai_processing()
                await db.commit()
                
                session = message.session
                contact = session.contact
                account = session.wechat_account
                
                # 检查账号状态
                if account.status != DeviceStatus.ONLINE:
                    logger.warning(f"微信账号离线，跳过AI处理: {account.wxid}")
                    message.mark_ai_skipped()
                    await db.commit()
                    return
                
                # 获取聊天历史
                chat_history = await self._get_chat_history(db, session.id)
                
                # 构建AI处理上下文
                context = {
                    "contact_wxid": contact.wxid,
                    "contact_nickname": contact.nickname,
                    "account_id": str(account.id),
                    "chat_history": chat_history,
                    "role": "销售助手"
                }
                
                # 如果有图片，添加图片URL
                if message.media_url and message.message_type == MessageType.IMAGE:
                    context["image_url"] = message.media_url
                
                # 调用AI服务
                ai_result = await self.ai_service.process_message(
                    user_message=message.content,
                    context=context,
                    workflow_id=contact.workflow_id or account.workflow_id
                )
                
                if ai_result["success"]:
                    # 发送AI回复
                    response_message = await self._send_ai_response(
                        db, session, account, contact, ai_result["response"]
                    )
                    
                    # 更新消息处理状态
                    message.mark_ai_completed(
                        response_message_id=str(response_message.id),
                        processing_time=ai_result["processing_time"],
                        cost=str(ai_result["cost"])
                    )
                    
                    # 更新分析结果
                    message.intent_classification = ai_result.get("intent")
                    message.sentiment_score = ai_result.get("sentiment")
                    message.keywords = ai_result.get("keywords", [])
                    
                    # 更新统计
                    session.ai_messages_count += 1
                    
                    logger.info(f"AI处理成功: {message.id} -> {response_message.id}")
                    
                else:
                    message.mark_ai_failed()
                    logger.error(f"AI处理失败: {message.id}")
                
                await db.commit()
                
        except AIServiceError as e:
            logger.error(f"AI服务错误: {message_id}, {str(e)}")
            async with get_db() as db:
                await db.execute(
                    update(ChatMessage)
                    .where(ChatMessage.id == message_id)
                    .values(ai_process_status=AIProcessStatus.FAILED)
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"AI消息处理异常: {message_id}, {str(e)}")
            async with get_db() as db:
                await db.execute(
                    update(ChatMessage)
                    .where(ChatMessage.id == message_id)
                    .values(ai_process_status=AIProcessStatus.FAILED)
                )
                await db.commit()
    
    async def _get_chat_history(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取聊天历史"""
        try:
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            
            history = []
            for msg in reversed(messages):  # 按时间正序
                history.append({
                    "direction": msg.direction.value,
                    "content": msg.content,
                    "message_type": msg.message_type.value,
                    "created_at": msg.created_at.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"获取聊天历史失败: {str(e)}")
            return []
    
    async def _send_ai_response(
        self,
        db: AsyncSession,
        session: ChatSession,
        account: WeChatAccount,
        contact: Contact,
        response_text: str
    ) -> ChatMessage:
        """发送AI回复消息"""
        
        # 创建回复消息记录
        response_message = ChatMessage(
            session_id=session.id,
            message_type=MessageType.TEXT,
            direction=MessageDirection.OUTGOING,
            content=response_text,
            sender_wxid=account.wxid,
            sender_nickname=account.nickname,
            status=MessageStatus.PENDING
        )
        
        db.add(response_message)
        await db.flush()
        
        try:
            # 发送到GeWe
            await self.gewe_service.send_text_message(
                app_id=account.gewe_app_id,
                to_wxid=contact.wxid,
                content=response_text
            )
            
            # 更新消息状态
            response_message.status = MessageStatus.SENT
            
            # 更新会话和联系人统计
            session.update_last_message(response_message)
            contact.update_message_stats(MessageDirection.OUTGOING)
            
            # 广播到WebSocket
            await self._broadcast_new_message(session.id, response_message)
            
            logger.info(f"AI回复发送成功: {response_message.id}")
            
        except Exception as e:
            logger.error(f"AI回复发送失败: {response_message.id}, {str(e)}")
            response_message.status = MessageStatus.FAILED
        
        return response_message
    
    async def _process_pending_messages(self):
        """处理待处理的消息（定期任务）"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # 1分钟检查一次
                
                async with get_db() as db:
                    # 查询待处理的消息
                    result = await db.execute(
                        select(ChatMessage)
                        .where(
                            ChatMessage.ai_process_status == AIProcessStatus.PENDING,
                            ChatMessage.direction == MessageDirection.INCOMING,
                            ChatMessage.message_type == MessageType.TEXT,
                            ChatMessage.created_at > datetime.utcnow() - timedelta(hours=1)  # 只处理1小时内的消息
                        )
                        .limit(50)
                    )
                    pending_messages = result.scalars().all()
                    
                    for message in pending_messages:
                        await self.message_queue.put({
                            "message_id": str(message.id),
                            "type": "ai_process"
                        })
                
            except Exception as e:
                logger.error(f"处理待处理消息异常: {str(e)}")
    
    async def _cleanup_old_messages(self):
        """清理旧消息（定期任务）"""
        while self.is_running:
            try:
                # 每天清理一次
                await asyncio.sleep(24 * 60 * 60)
                
                async with get_db() as db:
                    # 删除30天前的消息（可配置）
                    cutoff_date = datetime.utcnow() - timedelta(days=30)
                    
                    await db.execute(
                        update(ChatMessage)
                        .where(ChatMessage.created_at < cutoff_date)
                        .values(is_archived=True)  # 软删除，标记为归档
                    )
                    
                    await db.commit()
                    logger.info("旧消息清理完成")
                
            except Exception as e:
                logger.error(f"清理旧消息异常: {str(e)}")
    
    async def manual_takeover(self, session_id: str, user_id: str) -> bool:
        """人工接管会话"""
        try:
            async with get_db() as db:
                # 暂停AI自动回复
                await db.execute(
                    update(ChatSession)
                    .where(ChatSession.id == session_id)
                    .values(
                        auto_reply_enabled=False,
                        manual_takeover_count=ChatSession.manual_takeover_count + 1,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # 发送通知
                await self.notification_service.send_takeover_notification(
                    session_id=session_id,
                    user_id=user_id
                )
                
                logger.info(f"人工接管会话: {session_id} by user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"人工接管失败: {str(e)}")
            return False
    
    async def resume_ai_mode(self, session_id: str, user_id: str) -> bool:
        """恢复AI模式"""
        try:
            async with get_db() as db:
                # 重新启用AI自动回复
                await db.execute(
                    update(ChatSession)
                    .where(ChatSession.id == session_id)
                    .values(
                        auto_reply_enabled=True,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                logger.info(f"恢复AI模式: {session_id} by user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"恢复AI模式失败: {str(e)}")
            return False


# 全局聊天处理器实例
chat_processor = ChatProcessor()

