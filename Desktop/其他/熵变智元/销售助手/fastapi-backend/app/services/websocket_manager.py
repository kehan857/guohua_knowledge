"""
WebSocket连接管理服务
负责管理所有WebSocket连接、消息广播、连接状态维护等
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """WebSocket连接信息"""
    websocket: WebSocket
    user_id: str
    session_id: Optional[str] = None
    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    last_pong: datetime = field(default_factory=datetime.utcnow)
    is_alive: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageEvent:
    """消息事件"""
    event_type: str
    data: Dict[str, Any]
    target_type: str = "user"  # user, session, broadcast
    target_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 连接存储
        self.connections: Dict[str, ConnectionInfo] = {}  # connection_id -> ConnectionInfo
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        self.session_connections: Dict[str, Set[str]] = defaultdict(set)  # session_id -> connection_ids
        
        # 消息队列和事件处理
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # 统计信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "disconnections": 0,
            "errors": 0
        }
        
        # 心跳配置
        self.heartbeat_interval = settings.WS_HEARTBEAT_INTERVAL
        self.heartbeat_timeout = self.heartbeat_interval * 2
        
        # 任务管理
        self.background_tasks: List[asyncio.Task] = []
        self.is_running = False
    
    async def start(self):
        """启动WebSocket管理器"""
        if self.is_running:
            logger.warning("WebSocket管理器已在运行")
            return
        
        self.is_running = True
        logger.info("启动WebSocket管理器")
        
        # 启动后台任务
        self.background_tasks = [
            asyncio.create_task(self._heartbeat_checker()),
            asyncio.create_task(self._message_processor()),
            asyncio.create_task(self._connection_cleaner()),
            asyncio.create_task(self._stats_reporter())
        ]
    
    async def stop(self):
        """停止WebSocket管理器"""
        self.is_running = False
        logger.info("停止WebSocket管理器")
        
        # 关闭所有连接
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
        
        # 取消后台任务
        for task in self.background_tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """建立WebSocket连接"""
        try:
            # 接受连接
            await websocket.accept()
            
            # 创建连接信息
            connection_info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {}
            )
            
            connection_id = connection_info.connection_id
            
            # 检查用户连接数限制
            if len(self.user_connections[user_id]) >= settings.WS_MAX_CONNECTIONS_PER_USER:
                logger.warning(f"用户 {user_id} 连接数超限，关闭最旧连接")
                await self._close_oldest_user_connection(user_id)
            
            # 存储连接
            self.connections[connection_id] = connection_info
            self.user_connections[user_id].add(connection_id)
            
            if session_id:
                self.session_connections[session_id].add(connection_id)
            
            # 更新统计
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)
            
            # 发送连接确认
            await self._send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "server_time": datetime.utcnow().isoformat(),
                "heartbeat_interval": self.heartbeat_interval
            })
            
            # 触发连接事件
            await self._emit_event("user_connected", {
                "user_id": user_id,
                "connection_id": connection_id,
                "session_id": session_id
            })
            
            logger.info(f"WebSocket连接建立: {connection_id} (用户: {user_id})")
            return connection_id
            
        except Exception as e:
            logger.error(f"建立WebSocket连接失败: {str(e)}")
            raise
    
    async def disconnect(self, connection_id: str, code: int = 1000, reason: str = "Normal closure"):
        """断开WebSocket连接"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return
            
            # 从索引中移除
            user_id = connection_info.user_id
            session_id = connection_info.session_id
            
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
            
            if session_id:
                self.session_connections[session_id].discard(connection_id)
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]
            
            # 关闭WebSocket连接
            try:
                await connection_info.websocket.close(code=code, reason=reason)
            except:
                pass  # 连接可能已经关闭
            
            # 移除连接
            del self.connections[connection_id]
            
            # 更新统计
            self.stats["disconnections"] += 1
            self.stats["active_connections"] = len(self.connections)
            
            # 触发断开事件
            await self._emit_event("user_disconnected", {
                "user_id": user_id,
                "connection_id": connection_id,
                "session_id": session_id
            })
            
            logger.info(f"WebSocket连接断开: {connection_id} (用户: {user_id})")
            
        except Exception as e:
            logger.error(f"断开WebSocket连接失败: {connection_id}, {str(e)}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给指定用户的所有连接"""
        try:
            connection_ids = self.user_connections.get(user_id, set())
            if not connection_ids:
                logger.debug(f"用户 {user_id} 没有活跃连接")
                return False
            
            # 并发发送给所有连接
            tasks = []
            for connection_id in list(connection_ids):
                task = asyncio.create_task(
                    self._send_to_connection(connection_id, message)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计成功数量
            success_count = sum(1 for result in results if result is True)
            
            self.stats["messages_sent"] += success_count
            
            logger.debug(f"消息发送给用户 {user_id}: {success_count}/{len(connection_ids)} 成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"发送消息给用户失败: {user_id}, {str(e)}")
            self.stats["errors"] += 1
            return False
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给指定会话的所有连接"""
        try:
            connection_ids = self.session_connections.get(session_id, set())
            if not connection_ids:
                logger.debug(f"会话 {session_id} 没有活跃连接")
                return False
            
            # 并发发送给所有连接
            tasks = []
            for connection_id in list(connection_ids):
                task = asyncio.create_task(
                    self._send_to_connection(connection_id, message)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计成功数量
            success_count = sum(1 for result in results if result is True)
            
            self.stats["messages_sent"] += success_count
            
            logger.debug(f"消息发送给会话 {session_id}: {success_count}/{len(connection_ids)} 成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"发送消息给会话失败: {session_id}, {str(e)}")
            self.stats["errors"] += 1
            return False
    
    async def broadcast(self, message: Dict[str, Any], exclude_users: Optional[Set[str]] = None) -> int:
        """广播消息给所有连接"""
        try:
            exclude_users = exclude_users or set()
            
            # 获取所有需要发送的连接
            target_connections = []
            for connection_id, connection_info in self.connections.items():
                if connection_info.user_id not in exclude_users and connection_info.is_alive:
                    target_connections.append(connection_id)
            
            if not target_connections:
                logger.debug("没有目标连接进行广播")
                return 0
            
            # 并发发送
            tasks = []
            for connection_id in target_connections:
                task = asyncio.create_task(
                    self._send_to_connection(connection_id, message)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计成功数量
            success_count = sum(1 for result in results if result is True)
            
            self.stats["messages_sent"] += success_count
            
            logger.debug(f"广播消息: {success_count}/{len(target_connections)} 成功")
            return success_count
            
        except Exception as e:
            logger.error(f"广播消息失败: {str(e)}")
            self.stats["errors"] += 1
            return 0
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给指定连接"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info or not connection_info.is_alive:
                return False
            
            # 添加时间戳
            message_with_timestamp = {
                **message,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": connection_id
            }
            
            # 发送消息
            await connection_info.websocket.send_text(json.dumps(message_with_timestamp))
            return True
            
        except WebSocketDisconnect:
            # 连接已断开，标记为不活跃
            if connection_id in self.connections:
                self.connections[connection_id].is_alive = False
            return False
        except Exception as e:
            logger.error(f"发送消息到连接失败: {connection_id}, {str(e)}")
            # 标记连接为不活跃
            if connection_id in self.connections:
                self.connections[connection_id].is_alive = False
            return False
    
    async def handle_message(self, connection_id: str, message: str):
        """处理来自WebSocket的消息"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return
            
            # 解析消息
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.warning(f"收到无效JSON消息: {connection_id}")
                return
            
            message_type = data.get("type")
            self.stats["messages_received"] += 1
            
            # 处理不同类型的消息
            if message_type == "ping":
                await self._handle_ping(connection_id, data)
            elif message_type == "pong":
                await self._handle_pong(connection_id, data)
            elif message_type == "typing":
                await self._handle_typing(connection_id, data)
            elif message_type == "join_session":
                await self._handle_join_session(connection_id, data)
            elif message_type == "leave_session":
                await self._handle_leave_session(connection_id, data)
            elif message_type == "chat_message":
                await self._handle_chat_message(connection_id, data)
            else:
                # 触发自定义事件处理
                await self._emit_event(f"ws_{message_type}", {
                    "connection_id": connection_id,
                    "user_id": connection_info.user_id,
                    "data": data
                })
            
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {connection_id}, {str(e)}")
            self.stats["errors"] += 1
    
    async def _handle_ping(self, connection_id: str, data: Dict[str, Any]):
        """处理ping消息"""
        connection_info = self.connections.get(connection_id)
        if connection_info:
            connection_info.last_ping = datetime.utcnow()
            
            # 发送pong响应
            await self._send_to_connection(connection_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_pong(self, connection_id: str, data: Dict[str, Any]):
        """处理pong消息"""
        connection_info = self.connections.get(connection_id)
        if connection_info:
            connection_info.last_pong = datetime.utcnow()
    
    async def _handle_typing(self, connection_id: str, data: Dict[str, Any]):
        """处理打字状态消息"""
        connection_info = self.connections.get(connection_id)
        if not connection_info or not connection_info.session_id:
            return
        
        # 广播打字状态给同一会话的其他用户
        typing_message = {
            "type": "typing",
            "user_id": connection_info.user_id,
            "session_id": connection_info.session_id,
            "is_typing": data.get("is_typing", False)
        }
        
        # 发送给会话中的其他连接（排除发送者）
        session_connections = self.session_connections.get(connection_info.session_id, set())
        for other_connection_id in session_connections:
            if other_connection_id != connection_id:
                await self._send_to_connection(other_connection_id, typing_message)
    
    async def _handle_join_session(self, connection_id: str, data: Dict[str, Any]):
        """处理加入会话消息"""
        connection_info = self.connections.get(connection_id)
        if not connection_info:
            return
        
        session_id = data.get("session_id")
        if not session_id:
            return
        
        # 如果已经在其他会话中，先离开
        if connection_info.session_id:
            await self._handle_leave_session(connection_id, {"session_id": connection_info.session_id})
        
        # 加入新会话
        connection_info.session_id = session_id
        self.session_connections[session_id].add(connection_id)
        
        # 发送确认消息
        await self._send_to_connection(connection_id, {
            "type": "session_joined",
            "session_id": session_id
        })
        
        # 通知会话中的其他用户
        await self.send_to_session(session_id, {
            "type": "user_joined_session",
            "user_id": connection_info.user_id,
            "session_id": session_id
        })
    
    async def _handle_leave_session(self, connection_id: str, data: Dict[str, Any]):
        """处理离开会话消息"""
        connection_info = self.connections.get(connection_id)
        if not connection_info or not connection_info.session_id:
            return
        
        session_id = connection_info.session_id
        
        # 从会话中移除
        self.session_connections[session_id].discard(connection_id)
        if not self.session_connections[session_id]:
            del self.session_connections[session_id]
        
        # 通知会话中的其他用户
        await self.send_to_session(session_id, {
            "type": "user_left_session",
            "user_id": connection_info.user_id,
            "session_id": session_id
        })
        
        # 清除连接的会话ID
        connection_info.session_id = None
        
        # 发送确认消息
        await self._send_to_connection(connection_id, {
            "type": "session_left",
            "session_id": session_id
        })
    
    async def _handle_chat_message(self, connection_id: str, data: Dict[str, Any]):
        """处理聊天消息"""
        connection_info = self.connections.get(connection_id)
        if not connection_info:
            return
        
        # 触发聊天消息事件
        await self._emit_event("chat_message", {
            "connection_id": connection_id,
            "user_id": connection_info.user_id,
            "session_id": connection_info.session_id,
            "message": data
        })
    
    async def _heartbeat_checker(self):
        """心跳检查任务"""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                dead_connections = []
                
                # 检查所有连接的心跳
                for connection_id, connection_info in self.connections.items():
                    if not connection_info.is_alive:
                        continue
                    
                    # 检查是否超时
                    last_activity = max(connection_info.last_ping, connection_info.last_pong)
                    if (current_time - last_activity).total_seconds() > self.heartbeat_timeout:
                        dead_connections.append(connection_id)
                        logger.warning(f"连接心跳超时: {connection_id}")
                    
                    # 发送心跳ping
                    elif (current_time - connection_info.last_ping).total_seconds() > self.heartbeat_interval:
                        await self._send_to_connection(connection_id, {
                            "type": "ping",
                            "timestamp": current_time.isoformat()
                        })
                
                # 清理死连接
                for connection_id in dead_connections:
                    await self.disconnect(connection_id, code=1001, reason="Heartbeat timeout")
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"心跳检查异常: {str(e)}")
                await asyncio.sleep(5)
    
    async def _message_processor(self):
        """消息处理器任务"""
        while self.is_running:
            try:
                # 从队列获取消息事件
                event = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # 根据目标类型发送消息
                if event.target_type == "user" and event.target_id:
                    await self.send_to_user(event.target_id, {
                        "type": event.event_type,
                        **event.data
                    })
                elif event.target_type == "session" and event.target_id:
                    await self.send_to_session(event.target_id, {
                        "type": event.event_type,
                        **event.data
                    })
                elif event.target_type == "broadcast":
                    await self.broadcast({
                        "type": event.event_type,
                        **event.data
                    })
                
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"消息处理异常: {str(e)}")
    
    async def _connection_cleaner(self):
        """连接清理任务"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # 5分钟清理一次
                
                dead_connections = []
                current_time = datetime.utcnow()
                
                # 查找需要清理的连接
                for connection_id, connection_info in self.connections.items():
                    if not connection_info.is_alive:
                        dead_connections.append(connection_id)
                    elif (current_time - connection_info.connected_at).total_seconds() > 86400:  # 24小时
                        logger.info(f"清理长时间连接: {connection_id}")
                        dead_connections.append(connection_id)
                
                # 清理连接
                for connection_id in dead_connections:
                    await self.disconnect(connection_id, code=1000, reason="Connection cleanup")
                
                if dead_connections:
                    logger.info(f"清理了 {len(dead_connections)} 个无效连接")
                
            except Exception as e:
                logger.error(f"连接清理异常: {str(e)}")
    
    async def _stats_reporter(self):
        """统计信息报告任务"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # 1分钟报告一次
                
                # 存储统计信息到Redis
                stats_data = {
                    **self.stats,
                    "active_users": len(self.user_connections),
                    "active_sessions": len(self.session_connections),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await redis_client.setex(
                    "websocket_stats",
                    300,  # 5分钟过期
                    json.dumps(stats_data)
                )
                
                logger.debug(f"WebSocket统计: {stats_data}")
                
            except Exception as e:
                logger.error(f"统计报告异常: {str(e)}")
    
    async def _close_oldest_user_connection(self, user_id: str):
        """关闭用户最旧的连接"""
        connection_ids = self.user_connections.get(user_id, set())
        if not connection_ids:
            return
        
        # 找到最旧的连接
        oldest_connection_id = None
        oldest_time = datetime.utcnow()
        
        for connection_id in connection_ids:
            connection_info = self.connections.get(connection_id)
            if connection_info and connection_info.connected_at < oldest_time:
                oldest_time = connection_info.connected_at
                oldest_connection_id = connection_id
        
        if oldest_connection_id:
            await self.disconnect(oldest_connection_id, code=1000, reason="Connection limit exceeded")
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        handlers = self.event_handlers.get(event_type, [])
        if handlers:
            for handler in handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"事件处理器异常: {event_type}, {str(e)}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """添加事件处理器"""
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable):
        """移除事件处理器"""
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    async def queue_message(self, event_type: str, data: Dict[str, Any], target_type: str = "broadcast", target_id: Optional[str] = None):
        """将消息加入队列"""
        event = MessageEvent(
            event_type=event_type,
            data=data,
            target_type=target_type,
            target_id=target_id
        )
        await self.message_queue.put(event)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_users": len(self.user_connections),
            "active_sessions": len(self.session_connections),
            "total_user_connections": sum(len(connections) for connections in self.user_connections.values()),
            "total_session_connections": sum(len(connections) for connections in self.session_connections.values())
        }
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """获取用户的所有连接ID"""
        return list(self.user_connections.get(user_id, set()))
    
    def get_session_connections(self, session_id: str) -> List[str]:
        """获取会话的所有连接ID"""
        return list(self.session_connections.get(session_id, set()))
    
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0
    
    def is_session_active(self, session_id: str) -> bool:
        """检查会话是否有活跃连接"""
        return session_id in self.session_connections and len(self.session_connections[session_id]) > 0


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()

