"""
设备和微信账号管理模型
这是系统稳定运行的核心，负责管理托管的微信账号状态
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from app.core.database import Base


class DeviceStatus(str, enum.Enum):
    """设备状态枚举"""
    ONLINE = "online"                    # 在线正常
    OFFLINE = "offline"                  # 离线
    INITIALIZING = "initializing"        # 初始化中（首次扫码）
    AWAITING_RELOGIN = "awaiting_relogin"  # 等待重新登录（首夜掉线）
    RISK_CONTROLLED = "risk_controlled"  # 风控状态
    BANNED = "banned"                    # 账号被封
    MAINTENANCE = "maintenance"          # 维护中
    ERROR = "error"                      # 错误状态


class DeviceType(str, enum.Enum):
    """设备类型枚举"""
    ANDROID = "android"          # Android设备
    IOS = "ios"                 # iOS设备
    VIRTUAL = "virtual"         # 虚拟设备
    CLOUD = "cloud"             # 云端设备


class WeChatAccount(Base):
    """微信账号模型"""
    __tablename__ = "wechat_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 微信基本信息
    wxid = Column(String(100), unique=True, nullable=False, comment="微信ID")
    nickname = Column(String(100), nullable=True, comment="微信昵称")
    avatar = Column(Text, nullable=True, comment="头像URL")
    phone = Column(String(20), nullable=True, comment="绑定手机号")
    
    # GeWe平台信息
    gewe_token_id = Column(String(100), nullable=True, comment="GeWe Token ID")
    gewe_app_id = Column(String(100), nullable=True, comment="GeWe App ID (用于重连)")
    gewe_device_id = Column(String(100), nullable=True, comment="GeWe设备ID")
    
    # 状态信息
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.OFFLINE, comment="设备状态")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_primary = Column(Boolean, default=False, comment="是否为主账号")
    
    # 连接信息
    last_seen_at = Column(DateTime(timezone=True), nullable=True, comment="最后在线时间")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    last_ip = Column(String(45), nullable=True, comment="最后登录IP")
    login_location = Column(String(100), nullable=True, comment="登录地点")
    
    # 设备信息
    device_info = Column(JSONB, nullable=True, default={}, comment="设备详细信息")
    
    # 配置信息
    ai_enabled = Column(Boolean, default=True, comment="是否启用AI")
    auto_reply_enabled = Column(Boolean, default=True, comment="是否启用自动回复")
    workflow_id = Column(String(100), nullable=True, comment="关联的AI工作流ID")
    
    # 限制配置
    daily_message_limit = Column(Integer, default=1000, comment="每日消息限制")
    daily_message_count = Column(Integer, default=0, comment="今日已发消息数")
    friend_limit = Column(Integer, default=5000, comment="好友数量限制")
    group_limit = Column(Integer, default=500, comment="群聊数量限制")
    
    # 风控信息
    risk_level = Column(String(20), default="low", comment="风险等级: low/medium/high")
    risk_events = Column(JSONB, nullable=True, default=[], comment="风控事件记录")
    
    # 统计信息
    total_friends = Column(Integer, default=0, comment="好友总数")
    total_groups = Column(Integer, default=0, comment="群聊总数")
    total_messages_sent = Column(Integer, default=0, comment="总发送消息数")
    total_messages_received = Column(Integer, default=0, comment="总接收消息数")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    activated_at = Column(DateTime(timezone=True), nullable=True, comment="激活时间")
    
    # 关系
    organization = relationship("Organization", back_populates="wechat_accounts")
    user = relationship("User", back_populates="wechat_accounts")
    device_logs = relationship("DeviceLog", back_populates="wechat_account", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="wechat_account")
    
    def __repr__(self):
        return f"<WeChatAccount(id={self.id}, wxid='{self.wxid}', status='{self.status}')>"
    
    @property
    def is_online(self) -> bool:
        """是否在线"""
        return self.status == DeviceStatus.ONLINE
    
    @property
    def is_available(self) -> bool:
        """是否可用（在线且未被风控）"""
        return self.status == DeviceStatus.ONLINE and self.risk_level != "high"
    
    @property
    def uptime_hours(self) -> float:
        """在线时长（小时）"""
        if not self.last_login_at:
            return 0.0
        if self.status != DeviceStatus.ONLINE:
            return 0.0
        return (datetime.utcnow() - self.last_login_at).total_seconds() / 3600
    
    @property
    def is_message_limit_reached(self) -> bool:
        """是否达到每日消息限制"""
        return self.daily_message_count >= self.daily_message_limit
    
    @property
    def message_usage_percentage(self) -> float:
        """消息使用率百分比"""
        if self.daily_message_limit <= 0:
            return 0.0
        return (self.daily_message_count / self.daily_message_limit) * 100
    
    def update_last_seen(self) -> None:
        """更新最后在线时间"""
        self.last_seen_at = datetime.utcnow()
    
    def increment_message_count(self, count: int = 1) -> None:
        """增加消息计数"""
        self.daily_message_count += count
        self.total_messages_sent += count
    
    def reset_daily_counters(self) -> None:
        """重置每日计数器"""
        self.daily_message_count = 0
    
    def add_risk_event(self, event_type: str, description: str, severity: str = "medium") -> None:
        """添加风控事件"""
        if not self.risk_events:
            self.risk_events = []
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "description": description,
            "severity": severity
        }
        
        self.risk_events.append(event)
        
        # 更新风险等级
        high_risk_events = [e for e in self.risk_events if e.get("severity") == "high"]
        medium_risk_events = [e for e in self.risk_events if e.get("severity") == "medium"]
        
        if len(high_risk_events) >= 1:
            self.risk_level = "high"
        elif len(medium_risk_events) >= 3:
            self.risk_level = "medium"
        else:
            self.risk_level = "low"


class Device(Base):
    """物理设备模型"""
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # 设备基本信息
    device_name = Column(String(100), nullable=False, comment="设备名称")
    device_type = Column(SQLEnum(DeviceType), nullable=False, comment="设备类型")
    device_model = Column(String(100), nullable=True, comment="设备型号")
    device_brand = Column(String(50), nullable=True, comment="设备品牌")
    
    # 系统信息
    os_version = Column(String(50), nullable=True, comment="操作系统版本")
    app_version = Column(String(50), nullable=True, comment="微信版本")
    
    # 网络信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    location = Column(String(100), nullable=True, comment="地理位置")
    network_type = Column(String(20), nullable=True, comment="网络类型")
    
    # 硬件信息
    hardware_info = Column(JSONB, nullable=True, default={}, comment="硬件信息")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_heartbeat = Column(DateTime(timezone=True), nullable=True, comment="最后心跳时间")
    
    # 配置信息
    max_accounts = Column(Integer, default=1, comment="最大账号数")
    current_accounts = Column(Integer, default=0, comment="当前账号数")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.device_name}', type='{self.device_type}')>"
    
    @property
    def is_online(self) -> bool:
        """是否在线（基于心跳时间）"""
        if not self.last_heartbeat:
            return False
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() < 300  # 5分钟内


class DeviceLog(Base):
    """设备操作日志"""
    __tablename__ = "device_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wechat_account_id = Column(UUID(as_uuid=True), ForeignKey("wechat_accounts.id"), nullable=False)
    
    # 日志信息
    log_type = Column(String(50), nullable=False, comment="日志类型")
    log_level = Column(String(20), default="info", comment="日志级别")
    message = Column(Text, nullable=False, comment="日志消息")
    details = Column(JSONB, nullable=True, default={}, comment="详细信息")
    
    # 操作信息
    operation = Column(String(100), nullable=True, comment="操作类型")
    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="操作者")
    
    # 状态变化
    old_status = Column(String(50), nullable=True, comment="变更前状态")
    new_status = Column(String(50), nullable=True, comment="变更后状态")
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    wechat_account = relationship("WeChatAccount", back_populates="device_logs")
    operator = relationship("User")
    
    def __repr__(self):
        return f"<DeviceLog(id={self.id}, type='{self.log_type}', level='{self.log_level}')>"


class DeviceGroup(Base):
    """设备分组"""
    __tablename__ = "device_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # 分组信息
    name = Column(String(100), nullable=False, comment="分组名称")
    description = Column(Text, nullable=True, comment="分组描述")
    color = Column(String(7), default="#1890ff", comment="分组颜色")
    
    # 配置信息
    settings = Column(JSONB, nullable=True, default={}, comment="分组配置")
    
    # 统计信息
    account_count = Column(Integer, default=0, comment="账号数量")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<DeviceGroup(id={self.id}, name='{self.name}')>"


class DeviceQRCode(Base):
    """设备二维码管理"""
    __tablename__ = "device_qr_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wechat_account_id = Column(UUID(as_uuid=True), ForeignKey("wechat_accounts.id"), nullable=False)
    
    # 二维码信息
    qr_code_data = Column(Text, nullable=False, comment="二维码数据")
    qr_code_url = Column(Text, nullable=True, comment="二维码图片URL")
    qr_type = Column(String(20), default="login", comment="二维码类型: login/relogin")
    
    # 状态信息
    is_used = Column(Boolean, default=False, comment="是否已使用")
    is_expired = Column(Boolean, default=False, comment="是否已过期")
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    used_at = Column(DateTime(timezone=True), nullable=True, comment="使用时间")
    
    # 关系
    wechat_account = relationship("WeChatAccount")
    
    def __repr__(self):
        return f"<DeviceQRCode(id={self.id}, type='{self.qr_type}', is_used={self.is_used})>"
    
    @property
    def is_valid(self) -> bool:
        """是否有效"""
        return not self.is_used and not self.is_expired and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self) -> None:
        """标记为已使用"""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    def mark_as_expired(self) -> None:
        """标记为已过期"""
        self.is_expired = True


# 常用查询方法
class DeviceQueries:
    """设备相关查询方法"""
    
    @staticmethod
    def get_online_accounts_count(organization_id: str) -> int:
        """获取在线账号数量"""
        # 这里应该实现具体的查询逻辑
        pass
    
    @staticmethod
    def get_accounts_by_status(organization_id: str, status: DeviceStatus) -> List[WeChatAccount]:
        """根据状态获取账号列表"""
        # 这里应该实现具体的查询逻辑
        pass
    
    @staticmethod
    def get_risk_accounts(organization_id: str, risk_level: str = "high") -> List[WeChatAccount]:
        """获取风险账号"""
        # 这里应该实现具体的查询逻辑
        pass

