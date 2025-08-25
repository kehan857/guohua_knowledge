"""
算力管理模型
包含成本计量、配额管理、预算控制等核心模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer, JSON, DECIMAL, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal

from app.core.database import Base


class CostType(str, enum.Enum):
    """成本类型枚举"""
    AI_API = "ai_api"                # AI API调用
    STORAGE = "storage"              # 存储费用
    BANDWIDTH = "bandwidth"          # 带宽费用
    GEWE_API = "gewe_api"           # GeWe API调用
    SYSTEM = "system"               # 系统运营费用
    OTHER = "other"                 # 其他费用


class BillingUnit(str, enum.Enum):
    """计费单位枚举"""
    TOKEN = "token"                 # Token数量
    REQUEST = "request"             # 请求次数
    MINUTE = "minute"               # 分钟
    HOUR = "hour"                   # 小时
    DAY = "day"                     # 天
    GB = "gb"                       # GB
    MB = "mb"                       # MB
    COUNT = "count"                 # 数量


class AlertType(str, enum.Enum):
    """告警类型枚举"""
    QUOTA_WARNING = "quota_warning"      # 配额预警
    QUOTA_EXCEEDED = "quota_exceeded"    # 配额超出
    BUDGET_WARNING = "budget_warning"    # 预算预警
    BUDGET_EXCEEDED = "budget_exceeded"  # 预算超出
    ANOMALY = "anomaly"                  # 异常消费
    THRESHOLD = "threshold"              # 阈值告警


class CostModel(Base):
    """成本定价模型"""
    __tablename__ = "cost_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # 基本信息
    name = Column(String(200), nullable=False, comment="模型名称")
    description = Column(Text, nullable=True, comment="模型描述")
    provider = Column(String(100), nullable=False, comment="服务提供商")
    model_type = Column(String(100), nullable=False, comment="模型类型")
    
    # 定价配置
    cost_type = Column(SQLEnum(CostType), nullable=False, comment="成本类型")
    billing_unit = Column(SQLEnum(BillingUnit), nullable=False, comment="计费单位")
    
    # 价格设置
    input_price = Column(DECIMAL(10, 6), nullable=True, comment="输入价格")
    output_price = Column(DECIMAL(10, 6), nullable=True, comment="输出价格")
    base_price = Column(DECIMAL(10, 6), nullable=True, comment="基础价格")
    unit_size = Column(Integer, default=1000, comment="计费单位大小")
    
    # 配置信息
    config = Column(JSONB, nullable=True, default={}, comment="配置信息")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    cost_records = relationship("CostRecord", back_populates="cost_model")
    
    def __repr__(self):
        return f"<CostModel(id={self.id}, name='{self.name}', provider='{self.provider}')>"
    
    def calculate_cost(self, input_units: int = 0, output_units: int = 0, base_units: int = 0) -> Decimal:
        """计算成本"""
        total_cost = Decimal('0.00')
        
        if self.input_price and input_units > 0:
            total_cost += (Decimal(str(input_units)) / Decimal(str(self.unit_size))) * self.input_price
        
        if self.output_price and output_units > 0:
            total_cost += (Decimal(str(output_units)) / Decimal(str(self.unit_size))) * self.output_price
        
        if self.base_price and base_units > 0:
            total_cost += (Decimal(str(base_units)) / Decimal(str(self.unit_size))) * self.base_price
        
        return total_cost.quantize(Decimal('0.000001'))


class CostRecord(Base):
    """成本记录模型"""
    __tablename__ = "cost_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cost_model_id = Column(UUID(as_uuid=True), ForeignKey("cost_models.id"), nullable=False)
    
    # 关联信息
    wechat_account_id = Column(UUID(as_uuid=True), ForeignKey("wechat_accounts.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True)
    sop_instance_id = Column(UUID(as_uuid=True), ForeignKey("sop_instances.id"), nullable=True)
    
    # 请求信息
    request_id = Column(String(100), nullable=True, comment="请求ID")
    request_type = Column(String(50), nullable=False, comment="请求类型")
    request_data = Column(JSONB, nullable=True, default={}, comment="请求数据")
    
    # 计量信息
    input_units = Column(Integer, default=0, comment="输入单位数")
    output_units = Column(Integer, default=0, comment="输出单位数")
    base_units = Column(Integer, default=0, comment="基础单位数")
    total_units = Column(Integer, default=0, comment="总单位数")
    
    # 成本信息
    input_cost = Column(DECIMAL(10, 6), default=0, comment="输入成本")
    output_cost = Column(DECIMAL(10, 6), default=0, comment="输出成本")
    base_cost = Column(DECIMAL(10, 6), default=0, comment="基础成本")
    total_cost = Column(DECIMAL(10, 6), default=0, comment="总成本")
    
    # 元数据
    model_name = Column(String(100), nullable=True, comment="模型名称")
    provider_name = Column(String(100), nullable=True, comment="提供商名称")
    metadata = Column(JSONB, nullable=True, default={}, comment="元数据")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User")
    cost_model = relationship("CostModel", back_populates="cost_records")
    wechat_account = relationship("WeChatAccount")
    session = relationship("ChatSession")
    sop_instance = relationship("SOPInstance")
    
    def __repr__(self):
        return f"<CostRecord(id={self.id}, user_id={self.user_id}, cost={self.total_cost})>"


class CostQuota(Base):
    """成本配额模型"""
    __tablename__ = "cost_quotas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 配额信息
    name = Column(String(200), nullable=False, comment="配额名称")
    description = Column(Text, nullable=True, comment="配额描述")
    quota_type = Column(String(50), nullable=False, comment="配额类型")  # user, organization, department
    
    # 额度设置
    total_quota = Column(DECIMAL(10, 2), nullable=False, comment="总配额")
    used_quota = Column(DECIMAL(10, 2), default=0, comment="已用配额")
    remaining_quota = Column(DECIMAL(10, 2), nullable=False, comment="剩余配额")
    
    # 时间范围
    period_type = Column(String(20), nullable=False, comment="周期类型")  # daily, weekly, monthly, yearly
    period_start = Column(DateTime(timezone=True), nullable=False, comment="周期开始")
    period_end = Column(DateTime(timezone=True), nullable=False, comment="周期结束")
    
    # 限制配置
    daily_limit = Column(DECIMAL(10, 2), nullable=True, comment="日限额")
    hourly_limit = Column(DECIMAL(10, 2), nullable=True, comment="小时限额")
    
    # 告警阈值
    warning_threshold = Column(Float, default=0.8, comment="预警阈值")
    critical_threshold = Column(Float, default=0.95, comment="严重阈值")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_exceeded = Column(Boolean, default=False, comment="是否超出")
    
    # 配置
    config = Column(JSONB, nullable=True, default={}, comment="配置信息")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User")
    alerts = relationship("CostAlert", back_populates="quota")
    
    def __repr__(self):
        return f"<CostQuota(id={self.id}, name='{self.name}', used={self.used_quota}/{self.total_quota})>"
    
    @property
    def usage_percentage(self) -> float:
        """使用百分比"""
        if self.total_quota == 0:
            return 0.0
        return float(self.used_quota / self.total_quota * 100)
    
    @property
    def is_warning(self) -> bool:
        """是否达到预警阈值"""
        return self.usage_percentage >= (self.warning_threshold * 100)
    
    @property
    def is_critical(self) -> bool:
        """是否达到严重阈值"""
        return self.usage_percentage >= (self.critical_threshold * 100)
    
    def add_usage(self, amount: Decimal) -> bool:
        """增加使用量"""
        new_used = self.used_quota + amount
        if new_used > self.total_quota:
            self.is_exceeded = True
            return False
        
        self.used_quota = new_used
        self.remaining_quota = self.total_quota - new_used
        return True
    
    def reset_quota(self):
        """重置配额"""
        self.used_quota = Decimal('0.00')
        self.remaining_quota = self.total_quota
        self.is_exceeded = False


class CostBudget(Base):
    """成本预算模型"""
    __tablename__ = "cost_budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 预算信息
    name = Column(String(200), nullable=False, comment="预算名称")
    description = Column(Text, nullable=True, comment="预算描述")
    budget_type = Column(String(50), nullable=False, comment="预算类型")
    
    # 预算金额
    total_budget = Column(DECIMAL(10, 2), nullable=False, comment="总预算")
    used_budget = Column(DECIMAL(10, 2), default=0, comment="已用预算")
    remaining_budget = Column(DECIMAL(10, 2), nullable=False, comment="剩余预算")
    
    # 时间范围
    period_type = Column(String(20), nullable=False, comment="周期类型")
    period_start = Column(DateTime(timezone=True), nullable=False, comment="周期开始")
    period_end = Column(DateTime(timezone=True), nullable=False, comment="周期结束")
    
    # 分配配置
    allocations = Column(JSONB, nullable=True, default={}, comment="分配配置")
    
    # 告警设置
    warning_threshold = Column(Float, default=0.8, comment="预警阈值")
    critical_threshold = Column(Float, default=0.95, comment="严重阈值")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_exceeded = Column(Boolean, default=False, comment="是否超出")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User")
    
    def __repr__(self):
        return f"<CostBudget(id={self.id}, name='{self.name}', used={self.used_budget}/{self.total_budget})>"
    
    @property
    def usage_percentage(self) -> float:
        """使用百分比"""
        if self.total_budget == 0:
            return 0.0
        return float(self.used_budget / self.total_budget * 100)


class CostAlert(Base):
    """成本告警模型"""
    __tablename__ = "cost_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    quota_id = Column(UUID(as_uuid=True), ForeignKey("cost_quotas.id"), nullable=True)
    
    # 告警信息
    alert_type = Column(SQLEnum(AlertType), nullable=False, comment="告警类型")
    title = Column(String(200), nullable=False, comment="告警标题")
    message = Column(Text, nullable=False, comment="告警消息")
    level = Column(String(20), nullable=False, comment="告警级别")  # info, warning, error, critical
    
    # 触发条件
    trigger_condition = Column(JSONB, nullable=True, default={}, comment="触发条件")
    trigger_value = Column(DECIMAL(10, 6), nullable=True, comment="触发值")
    threshold_value = Column(DECIMAL(10, 6), nullable=True, comment="阈值")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    
    # 处理信息
    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="解决时间")
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text, nullable=True, comment="解决备注")
    
    # 通知配置
    notification_sent = Column(Boolean, default=False, comment="是否已发送通知")
    notification_channels = Column(JSONB, nullable=True, default=[], comment="通知渠道")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    quota = relationship("CostQuota", back_populates="alerts")
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f"<CostAlert(id={self.id}, type='{self.alert_type}', level='{self.level}')>"


class CostStatistics(Base):
    """成本统计模型"""
    __tablename__ = "cost_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 统计维度
    dimension_type = Column(String(50), nullable=False, comment="统计维度")  # daily, weekly, monthly, user, model
    dimension_value = Column(String(200), nullable=False, comment="维度值")
    
    # 统计日期
    stat_date = Column(DateTime(timezone=True), nullable=False, comment="统计日期")
    
    # 成本统计
    total_cost = Column(DECIMAL(10, 6), default=0, comment="总成本")
    ai_cost = Column(DECIMAL(10, 6), default=0, comment="AI成本")
    gewe_cost = Column(DECIMAL(10, 6), default=0, comment="GeWe成本")
    storage_cost = Column(DECIMAL(10, 6), default=0, comment="存储成本")
    other_cost = Column(DECIMAL(10, 6), default=0, comment="其他成本")
    
    # 使用量统计
    total_requests = Column(Integer, default=0, comment="总请求数")
    total_tokens = Column(Integer, default=0, comment="总Token数")
    input_tokens = Column(Integer, default=0, comment="输入Token数")
    output_tokens = Column(Integer, default=0, comment="输出Token数")
    
    # 效率统计
    avg_cost_per_request = Column(DECIMAL(10, 6), default=0, comment="每请求平均成本")
    avg_cost_per_token = Column(DECIMAL(10, 6), default=0, comment="每Token平均成本")
    cost_trend = Column(Float, default=0, comment="成本趋势")
    
    # 元数据
    metadata = Column(JSONB, nullable=True, default={}, comment="元数据")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User")
    
    def __repr__(self):
        return f"<CostStatistics(dimension='{self.dimension_type}', date={self.stat_date}, cost={self.total_cost})>"


class CostOptimization(Base):
    """成本优化建议模型"""
    __tablename__ = "cost_optimizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 优化信息
    title = Column(String(200), nullable=False, comment="优化标题")
    description = Column(Text, nullable=False, comment="优化描述")
    optimization_type = Column(String(50), nullable=False, comment="优化类型")
    
    # 分析数据
    current_cost = Column(DECIMAL(10, 6), nullable=False, comment="当前成本")
    potential_savings = Column(DECIMAL(10, 6), nullable=False, comment="潜在节省")
    savings_percentage = Column(Float, nullable=False, comment="节省百分比")
    
    # 实施建议
    recommendations = Column(JSONB, nullable=True, default=[], comment="建议列表")
    implementation_effort = Column(String(20), nullable=False, comment="实施难度")  # low, medium, high
    priority = Column(String(20), nullable=False, comment="优先级")  # low, medium, high, critical
    
    # 状态
    status = Column(String(20), default="pending", comment="状态")  # pending, in_progress, completed, dismissed
    is_implemented = Column(Boolean, default=False, comment="是否已实施")
    
    # 实施信息
    implemented_at = Column(DateTime(timezone=True), nullable=True, comment="实施时间")
    implemented_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actual_savings = Column(DECIMAL(10, 6), nullable=True, comment="实际节省")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    implementer = relationship("User", foreign_keys=[implemented_by])
    
    def __repr__(self):
        return f"<CostOptimization(id={self.id}, title='{self.title}', savings={self.potential_savings})>"

