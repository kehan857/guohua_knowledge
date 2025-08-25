"""
用户模型定义
包含用户、组织、角色权限等核心模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime
from typing import Optional, List

from app.core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"          # 系统管理员
    MANAGER = "manager"      # 业务管理员
    OPERATOR = "operator"    # 操作员
    USER = "user"           # 普通用户
    READONLY = "readonly"    # 只读用户


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"        # 活跃
    INACTIVE = "inactive"    # 未激活
    SUSPENDED = "suspended"  # 暂停
    DELETED = "deleted"      # 已删除


class Organization(Base):
    """组织/企业模型"""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="组织名称")
    display_name = Column(String(200), nullable=True, comment="显示名称")
    description = Column(Text, nullable=True, comment="组织描述")
    
    # 联系信息
    contact_email = Column(String(100), nullable=True, comment="联系邮箱")
    contact_phone = Column(String(20), nullable=True, comment="联系电话")
    address = Column(Text, nullable=True, comment="地址")
    
    # 配置信息
    settings = Column(JSONB, nullable=True, default={}, comment="组织配置")
    subscription_plan = Column(String(50), default="basic", comment="订阅计划")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    wechat_accounts = relationship("WeChatAccount", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # 基本信息
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    
    # 个人信息
    full_name = Column(String(100), nullable=True, comment="姓名")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar = Column(Text, nullable=True, comment="头像URL")
    
    # 角色和权限
    role = Column(SQLEnum(UserRole), default=UserRole.USER, comment="用户角色")
    permissions = Column(JSONB, nullable=True, default=[], comment="额外权限")
    
    # 状态字段
    status = Column(SQLEnum(UserStatus), default=UserStatus.INACTIVE, comment="用户状态")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_verified = Column(Boolean, default=False, comment="是否验证")
    
    # 登录相关
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")
    login_count = Column(Integer, default=0, comment="登录次数")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    email_verified_at = Column(DateTime(timezone=True), nullable=True, comment="邮箱验证时间")
    
    # 软删除
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间")
    
    # 关系
    organization = relationship("Organization", back_populates="users")
    wechat_accounts = relationship("WeChatAccount", back_populates="user")
    sop_tasks = relationship("SOPTask", back_populates="user")
    cost_records = relationship("CostLedger", back_populates="user")
    
    # 用户配额和限制
    monthly_quota = Column(Integer, default=1000, comment="月度算力配额")
    used_quota = Column(Integer, default=0, comment="已用配额")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_manager(self) -> bool:
        """是否为管理员或业务管理员"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    @property
    def quota_usage_percentage(self) -> float:
        """配额使用百分比"""
        if self.monthly_quota <= 0:
            return 0.0
        return (self.used_quota / self.monthly_quota) * 100
    
    @property
    def is_quota_exceeded(self) -> bool:
        """是否超出配额"""
        return self.used_quota > self.monthly_quota
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有特定权限"""
        # 管理员拥有所有权限
        if self.is_admin:
            return True
        
        # 检查角色权限
        role_permissions = ROLE_PERMISSIONS.get(self.role, [])
        if permission in role_permissions:
            return True
        
        # 检查额外权限
        if self.permissions and permission in self.permissions:
            return True
        
        return False
    
    def update_quota_usage(self, tokens_used: int) -> None:
        """更新配额使用量"""
        self.used_quota += tokens_used
    
    def reset_monthly_quota(self) -> None:
        """重置月度配额"""
        self.used_quota = 0


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 会话信息
    session_token = Column(String(255), unique=True, nullable=False, comment="会话令牌")
    refresh_token = Column(String(255), unique=True, nullable=True, comment="刷新令牌")
    
    # 设备信息
    device_id = Column(String(100), nullable=True, comment="设备ID")
    device_name = Column(String(100), nullable=True, comment="设备名称")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), comment="最后活跃时间")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否活跃")
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        return datetime.utcnow() > self.expires_at


class UserLoginLog(Base):
    """用户登录日志"""
    __tablename__ = "user_login_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 登录信息
    login_type = Column(String(20), default="web", comment="登录类型")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    location = Column(String(100), nullable=True, comment="登录地点")
    
    # 状态
    success = Column(Boolean, default=True, comment="是否成功")
    failure_reason = Column(String(200), nullable=True, comment="失败原因")
    
    # 时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="登录时间")
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserLoginLog(id={self.id}, user_id={self.user_id}, success={self.success})>"


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "users.create", "users.read", "users.update", "users.delete",
        "organizations.create", "organizations.read", "organizations.update", "organizations.delete",
        "devices.create", "devices.read", "devices.update", "devices.delete",
        "chat.read", "chat.manage",
        "sop.create", "sop.read", "sop.update", "sop.delete", "sop.execute",
        "cost.read", "cost.manage", "cost.configure",
        "materials.create", "materials.read", "materials.update", "materials.delete",
        "system.configure", "system.monitor"
    ],
    UserRole.MANAGER: [
        "users.read", "users.update",
        "devices.create", "devices.read", "devices.update",
        "chat.read", "chat.manage",
        "sop.create", "sop.read", "sop.update", "sop.execute",
        "cost.read", "cost.manage",
        "materials.create", "materials.read", "materials.update"
    ],
    UserRole.OPERATOR: [
        "devices.read", "devices.update",
        "chat.read", "chat.manage",
        "sop.read", "sop.execute",
        "cost.read",
        "materials.read"
    ],
    UserRole.USER: [
        "chat.read",
        "sop.read",
        "cost.read",
        "materials.read"
    ],
    UserRole.READONLY: [
        "chat.read",
        "sop.read",
        "cost.read",
        "materials.read"
    ]
}

