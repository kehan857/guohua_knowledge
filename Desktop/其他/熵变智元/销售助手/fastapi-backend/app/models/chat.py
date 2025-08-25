"""
聊天管理模型
包含聊天会话、消息记录、联系人管理等核心模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.core.database import Base


class ChatType(str, enum.Enum):
    """聊天类型枚举"""
    PRIVATE = "private"      # 私聊
    GROUP = "group"          # 群聊


class MessageType(str, enum.Enum):
    """消息类型枚举"""
    TEXT = "text"           # 文本消息
    IMAGE = "image"         # 图片消息
    VIDEO = "video"         # 视频消息
    VOICE = "voice"         # 语音消息
    FILE = "file"           # 文件消息
    LINK = "link"           # 链接消息
    LOCATION = "location"   # 位置消息
    SYSTEM = "system"       # 系统消息
    RECALL = "recall"       # 撤回消息


class MessageDirection(str, enum.Enum):
    """消息方向枚举"""
    INCOMING = "incoming"   # 收到的消息
    OUTGOING = "outgoing"   # 发送的消息


class MessageStatus(str, enum.Enum):
    """消息状态枚举"""
    PENDING = "pending"     # 待发送
    SENT = "sent"          # 已发送
    DELIVERED = "delivered" # 已送达
    READ = "read"          # 已读
    FAILED = "failed"      # 发送失败


class AIProcessStatus(str, enum.Enum):
    """AI处理状态枚举"""
    PENDING = "pending"     # 待处理
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed" # 已完成
    FAILED = "failed"      # 处理失败
    SKIPPED = "skipped"    # 跳过处理


class Contact(Base):
    """联系人模型"""
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    wechat_account_id = Column(UUID(as_uuid=True), ForeignKey("wechat_accounts.id"), nullable=False)
    
    # 联系人基本信息
    wxid = Column(String(100), nullable=False, comment="微信ID")
    nickname = Column(String(100), nullable=True, comment="微信昵称")
    remark = Column(String(100), nullable=True, comment="备注名")
    avatar = Column(Text, nullable=True, comment="头像URL")
    
    # 联系人类型
    contact_type = Column(String(20), default="friend", comment="联系人类型: friend/group/stranger")
    
    # 群聊信息（如果是群聊）
    group_owner_wxid = Column(String(100), nullable=True, comment="群主微信ID")
    group_member_count = Column(Integer, default=0, comment="群成员数量")
    
    # 标签和分组
    tags = Column(JSONB, nullable=True, default=[], comment="标签列表")
    group_name = Column(String(100), nullable=True, comment="分组名称")
    
    # 互动统计
    total_messages_received = Column(Integer, default=0, comment="收到消息总数")
    total_messages_sent = Column(Integer, default=0, comment="发送消息总数")
    last_message_at = Column(DateTime(timezone=True), nullable=True, comment="最后消息时间")
    
    # AI配置
    ai_enabled = Column(Boolean, default=True, comment="是否启用AI")
    auto_reply_enabled = Column(Boolean, default=True, comment="是否启用自动回复")
    workflow_id = Column(String(100), nullable=True, comment="专用AI工作流ID")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_blocked = Column(Boolean, default=False, comment="是否被拉黑")
    is_muted = Column(Boolean, default=False, comment="是否静音")
    
    # 扩展信息
    extra_info = Column(JSONB, nullable=True, default={}, comment="扩展信息")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    first_contact_at = Column(DateTime(timezone=True), nullable=True, comment="首次联系时间")
    
    # 关系
    organization = relationship("Organization")
    wechat_account = relationship("WeChatAccount")
    chat_sessions = relationship("ChatSession", back_populates="contact")
    
    # 索引
    __table_args__ = (
        Index('idx_contact_wxid_account', 'wxid', 'wechat_account_id'),
        Index('idx_contact_last_message', 'last_message_at'),
        Index('idx_contact_type', 'contact_type'),
    )
    
    def __repr__(self):
        return f"<Contact(id={self.id}, wxid='{self.wxid}', nickname='{self.nickname}')>"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.remark or self.nickname or self.wxid
    
    @property
    def is_group(self) -> bool:
        """是否为群聊"""
        return self.contact_type == "group"
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def update_message_stats(self, direction: MessageDirection) -> None:
        """更新消息统计"""
        self.last_message_at = datetime.utcnow()
        if direction == MessageDirection.INCOMING:
            self.total_messages_received += 1
        else:
            self.total_messages_sent += 1


class ChatSession(Base):
    """聊天会话模型"""
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    wechat_account_id = Column(UUID(as_uuid=True), ForeignKey("wechat_accounts.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    
    # 会话基本信息
    session_name = Column(String(200), nullable=True, comment="会话名称")
    chat_type = Column(SQLEnum(ChatType), nullable=False, comment="聊天类型")
    
    # 会话状态
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    is_archived = Column(Boolean, default=False, comment="是否归档")
    
    # 消息统计
    total_messages = Column(Integer, default=0, comment="消息总数")
    unread_count = Column(Integer, default=0, comment="未读消息数")
    last_message_id = Column(UUID(as_uuid=True), nullable=True, comment="最后一条消息ID")
    last_message_preview = Column(Text, nullable=True, comment="最后消息预览")
    last_message_at = Column(DateTime(timezone=True), nullable=True, comment="最后消息时间")
    
    # AI处理统计
    ai_messages_count = Column(Integer, default=0, comment="AI处理消息数")
    manual_takeover_count = Column(Integer, default=0, comment="人工接管次数")
    
    # 会话配置
    ai_enabled = Column(Boolean, default=True, comment="是否启用AI")
    auto_reply_enabled = Column(Boolean, default=True, comment="是否启用自动回复")
    notification_enabled = Column(Boolean, default=True, comment="是否启用通知")
    
    # 扩展配置
    settings = Column(JSONB, nullable=True, default={}, comment="会话配置")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), comment="最后活跃时间")
    
    # 关系
    organization = relationship("Organization")
    wechat_account = relationship("WeChatAccount", back_populates="chat_sessions")
    contact = relationship("Contact", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_session_account_contact', 'wechat_account_id', 'contact_id'),
        Index('idx_session_last_message', 'last_message_at'),
        Index('idx_session_unread', 'unread_count'),
    )
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, type='{self.chat_type}', unread={self.unread_count})>"
    
    def mark_as_read(self) -> None:
        """标记为已读"""
        self.unread_count = 0
        self.last_activity_at = datetime.utcnow()
    
    def increment_unread(self) -> None:
        """增加未读数"""
        self.unread_count += 1
    
    def update_last_message(self, message: 'ChatMessage') -> None:
        """更新最后消息信息"""
        self.last_message_id = message.id
        self.last_message_preview = message.content[:100] if message.content else f"[{message.message_type.value}]"
        self.last_message_at = message.created_at
        self.total_messages += 1
        self.last_activity_at = datetime.utcnow()


class ChatMessage(Base):
    """聊天消息模型"""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    # 消息基本信息
    message_type = Column(SQLEnum(MessageType), nullable=False, comment="消息类型")
    direction = Column(SQLEnum(MessageDirection), nullable=False, comment="消息方向")
    content = Column(Text, nullable=True, comment="消息内容")
    
    # 发送者信息
    sender_wxid = Column(String(100), nullable=False, comment="发送者微信ID")
    sender_nickname = Column(String(100), nullable=True, comment="发送者昵称")
    
    # 媒体信息（图片、视频、文件等）
    media_url = Column(Text, nullable=True, comment="媒体文件URL")
    media_type = Column(String(50), nullable=True, comment="媒体类型")
    media_size = Column(Integer, nullable=True, comment="媒体文件大小")
    thumbnail_url = Column(Text, nullable=True, comment="缩略图URL")
    
    # 消息状态
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.SENT, comment="消息状态")
    is_recalled = Column(Boolean, default=False, comment="是否被撤回")
    
    # GeWe相关
    gewe_message_id = Column(String(100), nullable=True, comment="GeWe消息ID")
    gewe_timestamp = Column(DateTime(timezone=True), nullable=True, comment="GeWe时间戳")
    
    # AI处理相关
    ai_process_status = Column(SQLEnum(AIProcessStatus), default=AIProcessStatus.PENDING, comment="AI处理状态")
    ai_response_message_id = Column(UUID(as_uuid=True), nullable=True, comment="AI回复消息ID")
    ai_processing_time = Column(Integer, nullable=True, comment="AI处理耗时(毫秒)")
    ai_cost = Column(String(20), nullable=True, comment="AI处理成本")
    
    # 意图分析
    intent_classification = Column(String(100), nullable=True, comment="意图分类")
    sentiment_score = Column(String(10), nullable=True, comment="情感评分")
    keywords = Column(JSONB, nullable=True, default=[], comment="关键词列表")
    
    # 扩展信息
    extra_data = Column(JSONB, nullable=True, default={}, comment="扩展数据")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    session = relationship("ChatSession", back_populates="messages")
    ai_response = relationship("ChatMessage", remote_side=[id], post_update=True)
    
    # 索引
    __table_args__ = (
        Index('idx_message_session_time', 'session_id', 'created_at'),
        Index('idx_message_direction', 'direction'),
        Index('idx_message_ai_status', 'ai_process_status'),
        Index('idx_message_gewe_id', 'gewe_message_id'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, type='{self.message_type}', direction='{self.direction}')>"
    
    @property
    def is_incoming(self) -> bool:
        """是否为收到的消息"""
        return self.direction == MessageDirection.INCOMING
    
    @property
    def is_outgoing(self) -> bool:
        """是否为发送的消息"""
        return self.direction == MessageDirection.OUTGOING
    
    @property
    def needs_ai_processing(self) -> bool:
        """是否需要AI处理"""
        return (
            self.is_incoming and 
            self.ai_process_status == AIProcessStatus.PENDING and
            self.message_type == MessageType.TEXT
        )
    
    def mark_ai_processing(self) -> None:
        """标记为AI处理中"""
        self.ai_process_status = AIProcessStatus.PROCESSING
    
    def mark_ai_completed(self, response_message_id: str = None, processing_time: int = None, cost: str = None) -> None:
        """标记AI处理完成"""
        self.ai_process_status = AIProcessStatus.COMPLETED
        if response_message_id:
            self.ai_response_message_id = response_message_id
        if processing_time:
            self.ai_processing_time = processing_time
        if cost:
            self.ai_cost = cost
    
    def mark_ai_failed(self) -> None:
        """标记AI处理失败"""
        self.ai_process_status = AIProcessStatus.FAILED
    
    def mark_ai_skipped(self) -> None:
        """标记跳过AI处理"""
        self.ai_process_status = AIProcessStatus.SKIPPED


class MessageTemplate(Base):
    """消息模板模型"""
    __tablename__ = "message_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 模板基本信息
    name = Column(String(100), nullable=False, comment="模板名称")
    category = Column(String(50), nullable=True, comment="模板分类")
    description = Column(Text, nullable=True, comment="模板描述")
    
    # 模板内容
    content = Column(Text, nullable=False, comment="模板内容")
    variables = Column(JSONB, nullable=True, default=[], comment="变量列表")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime(timezone=True), nullable=True, comment="最后使用时间")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_shared = Column(Boolean, default=False, comment="是否共享")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User")
    
    def __repr__(self):
        return f"<MessageTemplate(id={self.id}, name='{self.name}')>"
    
    def render(self, variables: Dict[str, Any]) -> str:
        """渲染模板"""
        content = self.content
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{var_name}}}", str(var_value))
        return content
    
    def increment_usage(self) -> None:
        """增加使用次数"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()


class ConversationSummary(Base):
    """对话摘要模型"""
    __tablename__ = "conversation_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    # 摘要信息
    summary_date = Column(DateTime(timezone=True), nullable=False, comment="摘要日期")
    message_count = Column(Integer, nullable=False, comment="消息数量")
    summary_content = Column(Text, nullable=False, comment="摘要内容")
    
    # 分析结果
    key_topics = Column(JSONB, nullable=True, default=[], comment="关键话题")
    sentiment_analysis = Column(JSONB, nullable=True, default={}, comment="情感分析")
    action_items = Column(JSONB, nullable=True, default=[], comment="行动项")
    
    # 统计信息
    ai_messages_ratio = Column(String(10), nullable=True, comment="AI消息占比")
    avg_response_time = Column(Integer, nullable=True, comment="平均响应时间")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    session = relationship("ChatSession")
    
    def __repr__(self):
        return f"<ConversationSummary(id={self.id}, date={self.summary_date})>"


# 索引优化
# 在messages表上创建复合索引以优化查询性能
Index('idx_messages_session_direction_time', 
      ChatMessage.session_id, 
      ChatMessage.direction, 
      ChatMessage.created_at)

Index('idx_messages_ai_pending', 
      ChatMessage.ai_process_status, 
      ChatMessage.created_at,
      postgresql_where=ChatMessage.ai_process_status == AIProcessStatus.PENDING)

