"""
WebSocket聊天路由
提供实时聊天功能的WebSocket端点
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.chat import ChatSession
from app.services.websocket_manager import websocket_manager
from app.services.chat_processor import chat_processor

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """从JWT token获取用户信息"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
        
    except JWTError:
        return None


async def verify_session_access(session_id: str, user: User, db: AsyncSession) -> Optional[ChatSession]:
    """验证用户是否有权访问指定会话"""
    try:
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.id == session_id,
                ChatSession.organization_id == user.organization_id
            )
        )
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.websocket("/chat")
async def websocket_chat_global(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
    db: AsyncSession = Depends(get_db)
):
    """全局聊天WebSocket连接（支持多会话切换）"""
    connection_id = None
    
    try:
        # 验证用户身份
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
        
        # 建立WebSocket连接
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=str(user.id),
            metadata={
                "username": user.username,
                "organization_id": str(user.organization_id),
                "role": user.role.value
            }
        )
        
        logger.info(f"全局聊天连接建立: {connection_id} (用户: {user.username})")
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                message = await websocket.receive_text()
                
                # 处理消息
                await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: {connection_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket消息处理异常: {connection_id}, {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "消息处理失败",
                    "error": str(e)
                }))
    
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    
    finally:
        # 清理连接
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@router.websocket("/chat/session/{session_id}")
async def websocket_chat_session(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(..., description="JWT认证令牌"),
    db: AsyncSession = Depends(get_db)
):
    """会话专用WebSocket连接"""
    connection_id = None
    
    try:
        # 验证用户身份
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
        
        # 验证会话访问权限
        session = await verify_session_access(session_id, user, db)
        if not session:
            await websocket.close(code=4003, reason="Session not found or access denied")
            return
        
        # 建立WebSocket连接
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=str(user.id),
            session_id=session_id,
            metadata={
                "username": user.username,
                "organization_id": str(user.organization_id),
                "role": user.role.value,
                "session_name": session.session_name
            }
        )
        
        logger.info(f"会话聊天连接建立: {connection_id} (用户: {user.username}, 会话: {session_id})")
        
        # 发送会话初始信息
        await websocket.send_text(json.dumps({
            "type": "session_info",
            "session": {
                "id": str(session.id),
                "name": session.session_name,
                "chat_type": session.chat_type.value,
                "unread_count": session.unread_count,
                "ai_enabled": session.ai_enabled,
                "auto_reply_enabled": session.auto_reply_enabled
            }
        }))
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                message = await websocket.receive_text()
                
                # 处理消息
                await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket会话连接断开: {connection_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket会话消息处理异常: {connection_id}, {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "消息处理失败",
                    "error": str(e)
                }))
    
    except Exception as e:
        logger.error(f"WebSocket会话连接异常: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    
    finally:
        # 清理连接
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@router.websocket("/admin/monitor")
async def websocket_admin_monitor(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
    db: AsyncSession = Depends(get_db)
):
    """管理员监控WebSocket连接"""
    connection_id = None
    
    try:
        # 验证管理员身份
        user = await get_user_from_token(token, db)
        if not user or not user.is_admin:
            await websocket.close(code=4003, reason="Admin access required")
            return
        
        # 建立WebSocket连接
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=str(user.id),
            metadata={
                "username": user.username,
                "role": user.role.value,
                "monitor_mode": True
            }
        )
        
        logger.info(f"管理员监控连接建立: {connection_id} (用户: {user.username})")
        
        # 定期发送统计信息
        async def send_stats():
            while True:
                try:
                    stats = websocket_manager.get_stats()
                    await websocket.send_text(json.dumps({
                        "type": "stats_update",
                        "stats": stats,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    await asyncio.sleep(10)  # 每10秒更新一次
                except:
                    break
        
        # 启动统计任务
        stats_task = asyncio.create_task(send_stats())
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                message = await websocket.receive_text()
                
                # 处理管理员命令
                try:
                    data = json.loads(message)
                    command = data.get("command")
                    
                    if command == "get_stats":
                        stats = websocket_manager.get_stats()
                        await websocket.send_text(json.dumps({
                            "type": "stats_response",
                            "stats": stats
                        }))
                    
                    elif command == "get_connections":
                        connections_info = []
                        for conn_id, conn_info in websocket_manager.connections.items():
                            connections_info.append({
                                "connection_id": conn_id,
                                "user_id": conn_info.user_id,
                                "session_id": conn_info.session_id,
                                "connected_at": conn_info.connected_at.isoformat(),
                                "is_alive": conn_info.is_alive,
                                "metadata": conn_info.metadata
                            })
                        
                        await websocket.send_text(json.dumps({
                            "type": "connections_response",
                            "connections": connections_info
                        }))
                    
                    elif command == "disconnect_user":
                        target_user_id = data.get("user_id")
                        if target_user_id:
                            user_connections = websocket_manager.get_user_connections(target_user_id)
                            for conn_id in user_connections:
                                await websocket_manager.disconnect(conn_id, code=1000, reason="Admin disconnect")
                            
                            await websocket.send_text(json.dumps({
                                "type": "command_response",
                                "command": "disconnect_user",
                                "success": True,
                                "message": f"断开用户 {target_user_id} 的 {len(user_connections)} 个连接"
                            }))
                    
                    elif command == "broadcast_message":
                        broadcast_msg = data.get("message", {})
                        if broadcast_msg:
                            count = await websocket_manager.broadcast(broadcast_msg)
                            await websocket.send_text(json.dumps({
                                "type": "command_response",
                                "command": "broadcast_message",
                                "success": True,
                                "message": f"消息已广播给 {count} 个连接"
                            }))
                
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "无效的JSON格式"
                    }))
                
            except WebSocketDisconnect:
                logger.info(f"管理员监控连接断开: {connection_id}")
                break
            except Exception as e:
                logger.error(f"管理员监控异常: {connection_id}, {str(e)}")
    
    except Exception as e:
        logger.error(f"管理员监控连接异常: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    
    finally:
        # 清理连接
        if connection_id:
            await websocket_manager.disconnect(connection_id)
        
        # 取消统计任务
        if 'stats_task' in locals():
            stats_task.cancel()


# WebSocket事件处理器
async def handle_chat_message_event(data: Dict[str, Any]):
    """处理聊天消息事件"""
    try:
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        message_data = data.get("message", {})
        
        logger.info(f"处理聊天消息事件: 用户 {user_id}, 会话 {session_id}")
        
        # 这里可以添加更多的消息处理逻辑
        # 例如：保存消息到数据库、触发AI回复等
        
    except Exception as e:
        logger.error(f"处理聊天消息事件失败: {str(e)}")


async def handle_user_connected_event(data: Dict[str, Any]):
    """处理用户连接事件"""
    try:
        user_id = data.get("user_id")
        connection_id = data.get("connection_id")
        
        logger.info(f"用户连接事件: {user_id} ({connection_id})")
        
        # 可以在这里添加用户上线通知等逻辑
        
    except Exception as e:
        logger.error(f"处理用户连接事件失败: {str(e)}")


async def handle_user_disconnected_event(data: Dict[str, Any]):
    """处理用户断开连接事件"""
    try:
        user_id = data.get("user_id")
        connection_id = data.get("connection_id")
        
        logger.info(f"用户断开连接事件: {user_id} ({connection_id})")
        
        # 可以在这里添加用户下线通知等逻辑
        
    except Exception as e:
        logger.error(f"处理用户断开连接事件失败: {str(e)}")


# 注册事件处理器
websocket_manager.add_event_handler("chat_message", handle_chat_message_event)
websocket_manager.add_event_handler("user_connected", handle_user_connected_event)
websocket_manager.add_event_handler("user_disconnected", handle_user_disconnected_event)


# 集成聊天处理器的消息广播
async def broadcast_new_message(session_id: str, message_data: Dict[str, Any]):
    """广播新消息到WebSocket"""
    await websocket_manager.send_to_session(session_id, {
        "type": "new_message",
        "message": message_data
    })


async def broadcast_message_status_update(message_id: str, status: str, session_id: str):
    """广播消息状态更新"""
    await websocket_manager.send_to_session(session_id, {
        "type": "message_status_update",
        "message_id": message_id,
        "status": status
    })


async def broadcast_ai_processing_status(session_id: str, message_id: str, status: str):
    """广播AI处理状态"""
    await websocket_manager.send_to_session(session_id, {
        "type": "ai_processing_status",
        "session_id": session_id,
        "message_id": message_id,
        "status": status
    })


async def broadcast_session_update(session_id: str, update_data: Dict[str, Any]):
    """广播会话更新"""
    await websocket_manager.send_to_session(session_id, {
        "type": "session_update",
        "session_id": session_id,
        "update": update_data
    })


async def broadcast_user_status(user_id: str, status: str, metadata: Optional[Dict[str, Any]] = None):
    """广播用户状态"""
    await websocket_manager.send_to_user(user_id, {
        "type": "user_status_update",
        "status": status,
        "metadata": metadata or {}
    })


# 导出用于其他模块使用的广播函数
__all__ = [
    "router",
    "broadcast_new_message",
    "broadcast_message_status_update", 
    "broadcast_ai_processing_status",
    "broadcast_session_update",
    "broadcast_user_status"
]

