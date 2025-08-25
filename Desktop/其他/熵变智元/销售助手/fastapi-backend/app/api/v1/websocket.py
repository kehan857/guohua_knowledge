"""
WebSocket管理API路由
提供WebSocket连接状态查询、管理等功能
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user, get_current_active_user
from app.services.websocket_manager import websocket_manager
from app.utils.permissions import require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Pydantic模型 ====================

class WebSocketStatsResponse(BaseModel):
    """WebSocket统计响应"""
    total_connections: int
    active_connections: int
    messages_sent: int
    messages_received: int
    disconnections: int
    errors: int
    active_users: int
    active_sessions: int
    total_user_connections: int
    total_session_connections: int
    uptime_seconds: Optional[float] = None


class ConnectionInfo(BaseModel):
    """连接信息"""
    connection_id: str
    user_id: str
    session_id: Optional[str]
    connected_at: datetime
    last_ping: datetime
    last_pong: datetime
    is_alive: bool
    metadata: Dict[str, Any]


class UserConnectionsResponse(BaseModel):
    """用户连接响应"""
    user_id: str
    connection_count: int
    connections: List[ConnectionInfo]
    is_online: bool


class SessionConnectionsResponse(BaseModel):
    """会话连接响应"""
    session_id: str
    connection_count: int
    connections: List[ConnectionInfo]
    is_active: bool


class BroadcastMessageRequest(BaseModel):
    """广播消息请求"""
    message_type: str = Field(..., description="消息类型")
    message_data: Dict[str, Any] = Field(..., description="消息数据")
    target_type: str = Field("broadcast", description="目标类型: broadcast/user/session")
    target_id: Optional[str] = Field(None, description="目标ID")
    exclude_users: Optional[List[str]] = Field(None, description="排除的用户ID列表")


class DisconnectUserRequest(BaseModel):
    """断开用户连接请求"""
    user_id: str = Field(..., description="用户ID")
    reason: str = Field("Admin disconnect", description="断开原因")


class NotificationRequest(BaseModel):
    """通知请求"""
    title: str = Field(..., description="通知标题")
    message: str = Field(..., description="通知内容")
    notification_type: str = Field("info", description="通知类型: info/warning/error/success")
    target_type: str = Field("broadcast", description="目标类型")
    target_id: Optional[str] = Field(None, description="目标ID")
    action_url: Optional[str] = Field(None, description="操作链接")
    auto_close: bool = Field(True, description="是否自动关闭")


# ==================== API路由 ====================

@router.get("/stats", response_model=WebSocketStatsResponse)
async def get_websocket_stats(
    current_user: User = Depends(get_current_active_user)
):
    """获取WebSocket统计信息"""
    try:
        stats = websocket_manager.get_stats()
        
        return WebSocketStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"获取WebSocket统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )


@router.get("/connections", response_model=List[ConnectionInfo])
async def get_all_connections(
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """获取所有WebSocket连接信息（需要管理员权限）"""
    try:
        # 检查权限
        require_permission(current_user, "system.monitor")
        
        connections = []
        count = 0
        
        for connection_id, connection_info in websocket_manager.connections.items():
            if count >= limit:
                break
            
            connections.append(ConnectionInfo(
                connection_id=connection_id,
                user_id=connection_info.user_id,
                session_id=connection_info.session_id,
                connected_at=connection_info.connected_at,
                last_ping=connection_info.last_ping,
                last_pong=connection_info.last_pong,
                is_alive=connection_info.is_alive,
                metadata=connection_info.metadata
            ))
            count += 1
        
        return connections
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取连接信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取连接信息失败"
        )


@router.get("/users/{user_id}/connections", response_model=UserConnectionsResponse)
async def get_user_connections(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取指定用户的WebSocket连接"""
    try:
        # 只允许查看自己的连接或管理员查看任意用户
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限查看其他用户的连接"
            )
        
        connection_ids = websocket_manager.get_user_connections(user_id)
        connections = []
        
        for connection_id in connection_ids:
            connection_info = websocket_manager.connections.get(connection_id)
            if connection_info:
                connections.append(ConnectionInfo(
                    connection_id=connection_id,
                    user_id=connection_info.user_id,
                    session_id=connection_info.session_id,
                    connected_at=connection_info.connected_at,
                    last_ping=connection_info.last_ping,
                    last_pong=connection_info.last_pong,
                    is_alive=connection_info.is_alive,
                    metadata=connection_info.metadata
                ))
        
        return UserConnectionsResponse(
            user_id=user_id,
            connection_count=len(connections),
            connections=connections,
            is_online=websocket_manager.is_user_online(user_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户连接失败"
        )


@router.get("/sessions/{session_id}/connections", response_model=SessionConnectionsResponse)
async def get_session_connections(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取指定会话的WebSocket连接"""
    try:
        connection_ids = websocket_manager.get_session_connections(session_id)
        connections = []
        
        for connection_id in connection_ids:
            connection_info = websocket_manager.connections.get(connection_id)
            if connection_info:
                connections.append(ConnectionInfo(
                    connection_id=connection_id,
                    user_id=connection_info.user_id,
                    session_id=connection_info.session_id,
                    connected_at=connection_info.connected_at,
                    last_ping=connection_info.last_ping,
                    last_pong=connection_info.last_pong,
                    is_alive=connection_info.is_alive,
                    metadata=connection_info.metadata
                ))
        
        return SessionConnectionsResponse(
            session_id=session_id,
            connection_count=len(connections),
            connections=connections,
            is_active=websocket_manager.is_session_active(session_id)
        )
        
    except Exception as e:
        logger.error(f"获取会话连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话连接失败"
        )


@router.post("/broadcast")
async def broadcast_message(
    request: BroadcastMessageRequest,
    current_user: User = Depends(get_current_active_user)
):
    """广播消息（需要管理员权限）"""
    try:
        # 检查权限
        require_permission(current_user, "system.broadcast")
        
        message = {
            "type": request.message_type,
            **request.message_data,
            "sender": {
                "user_id": str(current_user.id),
                "username": current_user.username
            }
        }
        
        success_count = 0
        
        if request.target_type == "broadcast":
            # 广播给所有用户
            exclude_users = set(request.exclude_users) if request.exclude_users else None
            success_count = await websocket_manager.broadcast(message, exclude_users)
            
        elif request.target_type == "user" and request.target_id:
            # 发送给指定用户
            success = await websocket_manager.send_to_user(request.target_id, message)
            success_count = 1 if success else 0
            
        elif request.target_type == "session" and request.target_id:
            # 发送给指定会话
            success = await websocket_manager.send_to_session(request.target_id, message)
            success_count = 1 if success else 0
        
        return {
            "success": True,
            "message": f"消息已发送给 {success_count} 个目标",
            "target_count": success_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"广播消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="广播消息失败"
        )


@router.post("/users/disconnect")
async def disconnect_user(
    request: DisconnectUserRequest,
    current_user: User = Depends(get_current_active_user)
):
    """断开指定用户的所有连接（需要管理员权限）"""
    try:
        # 检查权限
        require_permission(current_user, "system.manage")
        
        # 不能断开自己的连接
        if request.user_id == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能断开自己的连接"
            )
        
        connection_ids = websocket_manager.get_user_connections(request.user_id)
        
        # 断开所有连接
        for connection_id in connection_ids:
            await websocket_manager.disconnect(
                connection_id,
                code=1000,
                reason=request.reason
            )
        
        return {
            "success": True,
            "message": f"已断开用户 {request.user_id} 的 {len(connection_ids)} 个连接",
            "disconnected_count": len(connection_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"断开用户连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="断开用户连接失败"
        )


@router.post("/notify")
async def send_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """发送通知消息"""
    try:
        # 构建通知消息
        notification = {
            "type": "notification",
            "notification": {
                "id": f"notify_{datetime.utcnow().timestamp()}",
                "title": request.title,
                "message": request.message,
                "notification_type": request.notification_type,
                "action_url": request.action_url,
                "auto_close": request.auto_close,
                "timestamp": datetime.utcnow().isoformat(),
                "sender": {
                    "user_id": str(current_user.id),
                    "username": current_user.username
                }
            }
        }
        
        success_count = 0
        
        if request.target_type == "broadcast":
            # 广播通知
            success_count = await websocket_manager.broadcast(notification)
            
        elif request.target_type == "user" and request.target_id:
            # 发送给指定用户
            success = await websocket_manager.send_to_user(request.target_id, notification)
            success_count = 1 if success else 0
            
        elif request.target_type == "session" and request.target_id:
            # 发送给指定会话
            success = await websocket_manager.send_to_session(request.target_id, notification)
            success_count = 1 if success else 0
        
        logger.info(f"通知发送: {request.title} -> {success_count} 个目标")
        
        return {
            "success": True,
            "message": f"通知已发送给 {success_count} 个目标",
            "target_count": success_count
        }
        
    except Exception as e:
        logger.error(f"发送通知失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送通知失败"
        )


@router.get("/health")
async def websocket_health_check():
    """WebSocket服务健康检查"""
    try:
        stats = websocket_manager.get_stats()
        is_healthy = websocket_manager.is_running
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "is_running": is_healthy,
            "active_connections": stats["active_connections"],
            "active_users": stats["active_users"],
            "total_messages": stats["messages_sent"] + stats["messages_received"],
            "error_rate": stats["errors"] / max(stats["messages_received"], 1),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"WebSocket健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/ping/{user_id}")
async def ping_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """向指定用户发送ping消息"""
    try:
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat(),
            "from_user": {
                "user_id": str(current_user.id),
                "username": current_user.username
            }
        }
        
        success = await websocket_manager.send_to_user(user_id, ping_message)
        
        return {
            "success": success,
            "message": "Ping发送成功" if success else "用户不在线或发送失败"
        }
        
    except Exception as e:
        logger.error(f"发送Ping失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送Ping失败"
        )


@router.get("/online-users")
async def get_online_users(
    current_user: User = Depends(get_current_active_user)
):
    """获取在线用户列表"""
    try:
        online_users = []
        
        for user_id, connection_ids in websocket_manager.user_connections.items():
            if connection_ids:  # 有活跃连接
                # 获取用户元数据
                user_metadata = None
                for connection_id in connection_ids:
                    connection_info = websocket_manager.connections.get(connection_id)
                    if connection_info and connection_info.is_alive:
                        user_metadata = connection_info.metadata
                        break
                
                online_users.append({
                    "user_id": user_id,
                    "connection_count": len(connection_ids),
                    "metadata": user_metadata or {},
                    "is_online": True
                })
        
        return {
            "total_online_users": len(online_users),
            "users": online_users
        }
        
    except Exception as e:
        logger.error(f"获取在线用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取在线用户失败"
        )

