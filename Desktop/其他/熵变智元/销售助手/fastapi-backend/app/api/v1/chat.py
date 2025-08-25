"""
聊天管理API路由
提供聊天会话、消息收发、AI处理等核心功能
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, validator
import logging
import uuid
import json

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.user import User
from app.models.device import WeChatAccount, DeviceStatus
from app.models.chat import (
    Contact, ChatSession, ChatMessage, MessageTemplate, ConversationSummary,
    ChatType, MessageType, MessageDirection, MessageStatus, AIProcessStatus
)
from app.api.deps import get_current_user, get_current_active_user
from app.services.gewe_service import GeWeService
from app.services.ai_service import AIService
from app.services.websocket_manager import WebSocketManager
from app.utils.permissions import require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Pydantic模型 ====================

class ContactResponse(BaseModel):
    """联系人响应模型"""
    id: str
    wxid: str
    nickname: Optional[str]
    remark: Optional[str]
    avatar: Optional[str]
    contact_type: str
    tags: List[str]
    group_name: Optional[str]
    
    # 统计信息
    total_messages_received: int
    total_messages_sent: int
    last_message_at: Optional[datetime]
    
    # AI配置
    ai_enabled: bool
    auto_reply_enabled: bool
    
    # 状态
    is_active: bool
    is_blocked: bool
    is_muted: bool
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """聊天会话响应模型"""
    id: str
    session_name: Optional[str]
    chat_type: ChatType
    
    # 联系人信息
    contact: ContactResponse
    
    # 会话状态
    is_active: bool
    is_pinned: bool
    is_archived: bool
    
    # 消息统计
    total_messages: int
    unread_count: int
    last_message_preview: Optional[str]
    last_message_at: Optional[datetime]
    
    # AI统计
    ai_messages_count: int
    manual_takeover_count: int
    
    # 配置
    ai_enabled: bool
    auto_reply_enabled: bool
    notification_enabled: bool
    
    last_activity_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    """聊天消息响应模型"""
    id: str
    message_type: MessageType
    direction: MessageDirection
    content: Optional[str]
    
    # 发送者信息
    sender_wxid: str
    sender_nickname: Optional[str]
    
    # 媒体信息
    media_url: Optional[str]
    media_type: Optional[str]
    thumbnail_url: Optional[str]
    
    # 状态
    status: MessageStatus
    is_recalled: bool
    
    # AI处理
    ai_process_status: AIProcessStatus
    ai_response_message_id: Optional[str]
    ai_processing_time: Optional[int]
    
    # 分析结果
    intent_classification: Optional[str]
    sentiment_score: Optional[str]
    keywords: List[str]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    session_id: str = Field(..., description="会话ID")
    message_type: MessageType = Field(MessageType.TEXT, description="消息类型")
    content: Optional[str] = Field(None, description="消息内容")
    media_url: Optional[str] = Field(None, description="媒体URL")
    template_id: Optional[str] = Field(None, description="消息模板ID")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="模板变量")


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    is_pinned: Optional[bool] = Field(None, description="是否置顶")
    is_archived: Optional[bool] = Field(None, description="是否归档")
    ai_enabled: Optional[bool] = Field(None, description="是否启用AI")
    auto_reply_enabled: Optional[bool] = Field(None, description="是否启用自动回复")
    notification_enabled: Optional[bool] = Field(None, description="是否启用通知")


class UpdateContactRequest(BaseModel):
    """更新联系人请求"""
    remark: Optional[str] = Field(None, description="备注名")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    group_name: Optional[str] = Field(None, description="分组名称")
    ai_enabled: Optional[bool] = Field(None, description="是否启用AI")
    auto_reply_enabled: Optional[bool] = Field(None, description="是否启用自动回复")
    is_blocked: Optional[bool] = Field(None, description="是否拉黑")
    is_muted: Optional[bool] = Field(None, description="是否静音")


class ChatStatsResponse(BaseModel):
    """聊天统计响应"""
    total_sessions: int
    active_sessions: int
    total_messages_today: int
    ai_messages_today: int
    ai_usage_rate: float
    
    # 消息类型分布
    message_type_distribution: Dict[str, int]
    
    # 响应时间统计
    avg_ai_response_time: float
    avg_manual_response_time: float


class MessageTemplateResponse(BaseModel):
    """消息模板响应"""
    id: str
    name: str
    category: Optional[str]
    description: Optional[str]
    content: str
    variables: List[str]
    usage_count: int
    last_used_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class CreateTemplateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., max_length=100, description="模板名称")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    description: Optional[str] = Field(None, description="模板描述")
    content: str = Field(..., description="模板内容")
    variables: List[str] = Field(default=[], description="变量列表")
    is_shared: bool = Field(False, description="是否共享")


# ==================== API路由 ====================

@router.get("/stats", response_model=ChatStatsResponse)
async def get_chat_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取聊天统计信息"""
    try:
        # 获取用户的微信账号
        account_result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.is_active == True
            )
        )
        account_ids = [acc.id for acc in account_result.scalars().all()]
        
        if not account_ids:
            return ChatStatsResponse(
                total_sessions=0,
                active_sessions=0,
                total_messages_today=0,
                ai_messages_today=0,
                ai_usage_rate=0.0,
                message_type_distribution={},
                avg_ai_response_time=0.0,
                avg_manual_response_time=0.0
            )
        
        # 总会话数
        total_sessions_result = await db.execute(
            select(func.count(ChatSession.id))
            .where(
                ChatSession.wechat_account_id.in_(account_ids),
                ChatSession.is_active == True
            )
        )
        total_sessions = total_sessions_result.scalar() or 0
        
        # 活跃会话数（今日有消息）
        today = datetime.utcnow().date()
        active_sessions_result = await db.execute(
            select(func.count(ChatSession.id.distinct()))
            .where(
                ChatSession.wechat_account_id.in_(account_ids),
                ChatSession.is_active == True,
                ChatSession.last_message_at >= today
            )
        )
        active_sessions = active_sessions_result.scalar() or 0
        
        # 今日消息总数
        today_messages_result = await db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession)
            .where(
                ChatSession.wechat_account_id.in_(account_ids),
                ChatMessage.created_at >= today
            )
        )
        total_messages_today = today_messages_result.scalar() or 0
        
        # 今日AI处理消息数
        ai_messages_result = await db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession)
            .where(
                ChatSession.wechat_account_id.in_(account_ids),
                ChatMessage.created_at >= today,
                ChatMessage.ai_process_status == AIProcessStatus.COMPLETED
            )
        )
        ai_messages_today = ai_messages_result.scalar() or 0
        
        # AI使用率
        ai_usage_rate = (ai_messages_today / total_messages_today * 100) if total_messages_today > 0 else 0
        
        # 消息类型分布
        type_distribution_result = await db.execute(
            select(ChatMessage.message_type, func.count(ChatMessage.id))
            .join(ChatSession)
            .where(
                ChatSession.wechat_account_id.in_(account_ids),
                ChatMessage.created_at >= today
            )
            .group_by(ChatMessage.message_type)
        )
        message_type_distribution = {
            msg_type.value: count for msg_type, count in type_distribution_result.all()
        }
        
        # 平均响应时间（简化计算）
        ai_response_time_result = await db.execute(
            select(func.avg(ChatMessage.ai_processing_time))
            .join(ChatSession)
            .where(
                ChatSession.wechat_account_id.in_(account_ids),
                ChatMessage.created_at >= today,
                ChatMessage.ai_processing_time.isnot(None)
            )
        )
        avg_ai_response_time = ai_response_time_result.scalar() or 0
        
        return ChatStatsResponse(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            total_messages_today=total_messages_today,
            ai_messages_today=ai_messages_today,
            ai_usage_rate=round(ai_usage_rate, 2),
            message_type_distribution=message_type_distribution,
            avg_ai_response_time=round(avg_ai_response_time / 1000, 2) if avg_ai_response_time else 0,
            avg_manual_response_time=0.0  # 需要更复杂的逻辑计算
        )
        
    except Exception as e:
        logger.error(f"获取聊天统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    account_id: Optional[str] = Query(None, description="微信账号ID筛选"),
    chat_type: Optional[ChatType] = Query(None, description="聊天类型筛选"),
    unread_only: bool = Query(False, description="仅显示未读"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取聊天会话列表"""
    try:
        # 构建查询条件
        query = select(ChatSession).options(
            joinedload(ChatSession.contact)
        ).where(
            ChatSession.organization_id == current_user.organization_id,
            ChatSession.is_active == True
        )
        
        # 应用筛选条件
        if account_id:
            query = query.where(ChatSession.wechat_account_id == account_id)
        
        if chat_type:
            query = query.where(ChatSession.chat_type == chat_type)
        
        if unread_only:
            query = query.where(ChatSession.unread_count > 0)
        
        if search:
            query = query.join(Contact).where(
                or_(
                    Contact.nickname.ilike(f"%{search}%"),
                    Contact.remark.ilike(f"%{search}%"),
                    Contact.wxid.ilike(f"%{search}%"),
                    ChatSession.last_message_preview.ilike(f"%{search}%")
                )
            )
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(
            desc(ChatSession.is_pinned),  # 置顶优先
            desc(ChatSession.last_message_at)  # 按最后消息时间排序
        )
        
        result = await db.execute(query)
        sessions = result.unique().scalars().all()
        
        return [ChatSessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"获取聊天会话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败"
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str = Path(..., description="会话ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取聊天会话详情"""
    try:
        result = await db.execute(
            select(ChatSession)
            .options(joinedload(ChatSession.contact))
            .where(
                ChatSession.id == session_id,
                ChatSession.organization_id == current_user.organization_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        return ChatSessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天会话详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话详情失败"
        )


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: str = Path(..., description="会话ID"),
    update_data: UpdateSessionRequest = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新聊天会话配置"""
    try:
        result = await db.execute(
            select(ChatSession)
            .options(joinedload(ChatSession.contact))
            .where(
                ChatSession.id == session_id,
                ChatSession.organization_id == current_user.organization_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(session, field):
                setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"会话配置更新成功: {session_id}")
        return ChatSessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新会话配置失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新会话配置失败"
        )


@router.post("/sessions/{session_id}/mark-read")
async def mark_session_as_read(
    session_id: str = Path(..., description="会话ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """标记会话为已读"""
    try:
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.id == session_id,
                ChatSession.organization_id == current_user.organization_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        session.mark_as_read()
        await db.commit()
        
        return {"message": "会话已标记为已读"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记会话已读失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="标记已读失败"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str = Path(..., description="会话ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页数量"),
    message_type: Optional[MessageType] = Query(None, description="消息类型筛选"),
    direction: Optional[MessageDirection] = Query(None, description="消息方向筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话消息列表"""
    try:
        # 验证会话存在且属于当前组织
        session_result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.id == session_id,
                ChatSession.organization_id == current_user.organization_id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 构建消息查询
        query = select(ChatMessage).where(ChatMessage.session_id == session_id)
        
        # 应用筛选条件
        if message_type:
            query = query.where(ChatMessage.message_type == message_type)
        
        if direction:
            query = query.where(ChatMessage.direction == direction)
        
        # 分页（按时间倒序，最新消息在前）
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(ChatMessage.created_at))
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return [ChatMessageResponse.from_orm(msg) for msg in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取消息失败"
        )


@router.post("/send", response_model=ChatMessageResponse)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """发送消息"""
    try:
        # 获取会话信息
        session_result = await db.execute(
            select(ChatSession)
            .options(
                joinedload(ChatSession.contact),
                joinedload(ChatSession.wechat_account)
            )
            .where(
                ChatSession.id == request.session_id,
                ChatSession.organization_id == current_user.organization_id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 检查微信账号状态
        if session.wechat_account.status != DeviceStatus.ONLINE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="微信账号未在线，无法发送消息"
            )
        
        # 处理消息内容
        content = request.content
        if request.template_id and request.template_variables:
            # 使用模板
            template_result = await db.execute(
                select(MessageTemplate)
                .where(
                    MessageTemplate.id == request.template_id,
                    MessageTemplate.organization_id == current_user.organization_id,
                    MessageTemplate.is_active == True
                )
            )
            template = template_result.scalar_one_or_none()
            
            if template:
                content = template.render(request.template_variables)
                template.increment_usage()
        
        # 创建消息记录
        message = ChatMessage(
            session_id=session.id,
            message_type=request.message_type,
            direction=MessageDirection.OUTGOING,
            content=content,
            media_url=request.media_url,
            sender_wxid=session.wechat_account.wxid,
            sender_nickname=session.wechat_account.nickname,
            status=MessageStatus.PENDING
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        # 异步发送消息到GeWe
        background_tasks.add_task(
            send_message_to_gewe,
            message_id=str(message.id),
            app_id=session.wechat_account.gewe_app_id,
            to_wxid=session.contact.wxid,
            content=content,
            message_type=request.message_type.value,
            media_url=request.media_url
        )
        
        # 更新会话信息
        session.update_last_message(message)
        session.total_messages += 1
        
        # 更新联系人统计
        session.contact.update_message_stats(MessageDirection.OUTGOING)
        
        await db.commit()
        
        logger.info(f"消息创建成功: {message.id}")
        return ChatMessageResponse.from_orm(message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送消息失败"
        )


@router.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页数量"),
    account_id: Optional[str] = Query(None, description="微信账号ID筛选"),
    contact_type: Optional[str] = Query(None, description="联系人类型筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取联系人列表"""
    try:
        # 构建查询条件
        query = select(Contact).where(
            Contact.organization_id == current_user.organization_id,
            Contact.is_active == True
        )
        
        # 应用筛选条件
        if account_id:
            query = query.where(Contact.wechat_account_id == account_id)
        
        if contact_type:
            query = query.where(Contact.contact_type == contact_type)
        
        if search:
            query = query.where(
                or_(
                    Contact.nickname.ilike(f"%{search}%"),
                    Contact.remark.ilike(f"%{search}%"),
                    Contact.wxid.ilike(f"%{search}%")
                )
            )
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(Contact.last_message_at))
        
        result = await db.execute(query)
        contacts = result.scalars().all()
        
        return [ContactResponse.from_orm(contact) for contact in contacts]
        
    except Exception as e:
        logger.error(f"获取联系人列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取联系人列表失败"
        )


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str = Path(..., description="联系人ID"),
    update_data: UpdateContactRequest = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新联系人信息"""
    try:
        result = await db.execute(
            select(Contact)
            .where(
                Contact.id == contact_id,
                Contact.organization_id == current_user.organization_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="联系人不存在"
            )
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(contact, field):
                setattr(contact, field, value)
        
        contact.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(contact)
        
        logger.info(f"联系人信息更新成功: {contact_id}")
        return ContactResponse.from_orm(contact)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新联系人信息失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新联系人信息失败"
        )


@router.get("/templates", response_model=List[MessageTemplateResponse])
async def get_message_templates(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取消息模板列表"""
    try:
        # 构建查询条件
        query = select(MessageTemplate).where(
            or_(
                MessageTemplate.organization_id == current_user.organization_id,
                MessageTemplate.is_shared == True
            ),
            MessageTemplate.is_active == True
        )
        
        # 应用筛选条件
        if category:
            query = query.where(MessageTemplate.category == category)
        
        if search:
            query = query.where(
                or_(
                    MessageTemplate.name.ilike(f"%{search}%"),
                    MessageTemplate.content.ilike(f"%{search}%")
                )
            )
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(
            desc(MessageTemplate.usage_count),
            desc(MessageTemplate.created_at)
        )
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return [MessageTemplateResponse.from_orm(template) for template in templates]
        
    except Exception as e:
        logger.error(f"获取消息模板列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模板列表失败"
        )


@router.post("/templates", response_model=MessageTemplateResponse)
async def create_message_template(
    template_data: CreateTemplateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建消息模板"""
    try:
        template = MessageTemplate(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            name=template_data.name,
            category=template_data.category,
            description=template_data.description,
            content=template_data.content,
            variables=template_data.variables,
            is_shared=template_data.is_shared
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"消息模板创建成功: {template.id}")
        return MessageTemplateResponse.from_orm(template)
        
    except Exception as e:
        logger.error(f"创建消息模板失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建模板失败"
        )


# ==================== WebSocket处理 ====================

@router.websocket("/ws/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket聊天连接"""
    await websocket.accept()
    
    try:
        # 验证会话
        session_result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            await websocket.close(code=4004, reason="会话不存在")
            return
        
        # 添加到WebSocket管理器
        ws_manager = WebSocketManager()
        await ws_manager.connect(websocket, session_id)
        
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 处理不同类型的消息
                if message_data.get("type") == "typing":
                    # 广播打字状态
                    await ws_manager.broadcast_to_session(
                        session_id,
                        {"type": "typing", "user": message_data.get("user")}
                    )
                elif message_data.get("type") == "heartbeat":
                    # 心跳响应
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket, session_id)
            
    except Exception as e:
        logger.error(f"WebSocket连接错误: {str(e)}")
        await websocket.close(code=1000)


# ==================== 后台任务函数 ====================

async def send_message_to_gewe(
    message_id: str,
    app_id: str,
    to_wxid: str,
    content: str,
    message_type: str,
    media_url: str = None
):
    """发送消息到GeWe（后台任务）"""
    try:
        gewe_service = GeWeService()
        
        # 根据消息类型发送
        if message_type == "text":
            result = await gewe_service.send_text_message(app_id, to_wxid, content)
        elif message_type == "image" and media_url:
            result = await gewe_service.send_image_message(app_id, to_wxid, media_url)
        elif message_type == "file" and media_url:
            result = await gewe_service.send_file_message(app_id, to_wxid, media_url)
        else:
            raise ValueError(f"不支持的消息类型: {message_type}")
        
        # 更新消息状态
        async with get_db() as db:
            await db.execute(
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(
                    status=MessageStatus.SENT,
                    gewe_message_id=result.get("messageId"),
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
        
        logger.info(f"消息发送成功: {message_id}")
        
    except Exception as e:
        logger.error(f"消息发送失败: {message_id}, {str(e)}")
        
        # 更新消息状态为失败
        async with get_db() as db:
            await db.execute(
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(
                    status=MessageStatus.FAILED,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()

