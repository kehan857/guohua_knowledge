"""
SOP任务管理模型
包含SOP模板、任务实例、执行记录等核心模型
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


class SOPType(str, enum.Enum):
    """SOP类型枚举"""
    WELCOME = "welcome"           # 新好友欢迎
    FOLLOW_UP = "follow_up"       # 跟进流程
    PROMOTION = "promotion"       # 推广营销
    NURTURING = "nurturing"       # 客户培育
    CONVERSION = "conversion"     # 转化流程
    RETENTION = "retention"       # 客户保留
    CUSTOM = "custom"            # 自定义流程


class SOPStatus(str, enum.Enum):
    """SOP状态枚举"""
    DRAFT = "draft"              # 草稿
    ACTIVE = "active"            # 活跃
    PAUSED = "paused"            # 暂停
    ARCHIVED = "archived"        # 归档
    DELETED = "deleted"          # 已删除


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 待执行
    SCHEDULED = "scheduled"      # 已调度
    EXECUTING = "executing"      # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 执行失败
    SKIPPED = "skipped"         # 已跳过
    CANCELLED = "cancelled"      # 已取消


class TriggerType(str, enum.Enum):
    """触发类型枚举"""
    IMMEDIATE = "immediate"      # 立即执行
    DELAY = "delay"             # 延时执行
    CONDITION = "condition"      # 条件触发
    SCHEDULE = "schedule"        # 定时执行
    MANUAL = "manual"           # 手动触发


class ActionType(str, enum.Enum):
    """动作类型枚举"""
    SEND_MESSAGE = "send_message"       # 发送消息
    SEND_IMAGE = "send_image"          # 发送图片
    SEND_FILE = "send_file"            # 发送文件
    POST_MOMENTS = "post_moments"       # 发朋友圈
    ADD_TAG = "add_tag"                # 添加标签
    REMOVE_TAG = "remove_tag"          # 移除标签
    UPDATE_REMARK = "update_remark"    # 更新备注
    NOTIFY_MANUAL = "notify_manual"    # 通知人工
    WAIT_REPLY = "wait_reply"          # 等待回复
    CONDITION_CHECK = "condition_check" # 条件检查


class SOPTemplate(Base):
    """SOP模板模型"""
    __tablename__ = "sop_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 基本信息
    name = Column(String(200), nullable=False, comment="SOP名称")
    description = Column(Text, nullable=True, comment="SOP描述")
    sop_type = Column(SQLEnum(SOPType), nullable=False, comment="SOP类型")
    category = Column(String(100), nullable=True, comment="分类")
    tags = Column(JSONB, nullable=True, default=[], comment="标签列表")
    
    # 状态信息
    status = Column(SQLEnum(SOPStatus), default=SOPStatus.DRAFT, comment="SOP状态")
    version = Column(String(20), default="1.0", comment="版本号")
    
    # 配置信息
    config = Column(JSONB, nullable=True, default={}, comment="配置信息")
    steps = Column(JSONB, nullable=True, default=[], comment="步骤定义")
    
    # 触发条件
    trigger_config = Column(JSONB, nullable=True, default={}, comment="触发配置")
    target_config = Column(JSONB, nullable=True, default={}, comment="目标配置")
    
    # 统计信息
    total_instances = Column(Integer, default=0, comment="总实例数")
    active_instances = Column(Integer, default=0, comment="活跃实例数")
    success_rate = Column(String(10), default="0%", comment="成功率")
    
    # 设置
    is_template = Column(Boolean, default=True, comment="是否为模板")
    is_shared = Column(Boolean, default=False, comment="是否共享")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_used_at = Column(DateTime(timezone=True), nullable=True, comment="最后使用时间")
    
    # 关系
    organization = relationship("Organization")
    user = relationship("User")
    instances = relationship("SOPInstance", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SOPTemplate(id={self.id}, name='{self.name}', type='{self.sop_type}')>"
    
    def get_step_by_id(self, step_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取步骤"""
        if not self.steps:
            return None
        return next((step for step in self.steps if step.get("id") == step_id), None)
    
    def get_next_step(self, current_step_id: str) -> Optional[Dict[str, Any]]:
        """获取下一步骤"""
        if not self.steps:
            return None
        
        current_index = -1
        for i, step in enumerate(self.steps):
            if step.get("id") == current_step_id:
                current_index = i
                break
        
        if current_index >= 0 and current_index < len(self.steps) - 1:
            return self.steps[current_index + 1]
        
        return None
    
    def validate_steps(self) -> List[str]:
        """验证步骤配置"""
        errors = []
        
        if not self.steps:
            errors.append("至少需要一个步骤")
            return errors
        
        step_ids = set()
        for i, step in enumerate(self.steps):
            # 检查必需字段
            if not step.get("id"):
                errors.append(f"步骤 {i+1} 缺少ID")
            elif step["id"] in step_ids:
                errors.append(f"步骤ID '{step['id']}' 重复")
            else:
                step_ids.add(step["id"])
            
            if not step.get("name"):
                errors.append(f"步骤 {i+1} 缺少名称")
            
            if not step.get("action_type"):
                errors.append(f"步骤 {i+1} 缺少动作类型")
            
            # 检查动作配置
            action_type = step.get("action_type")
            if action_type in ["send_message", "send_image", "send_file"]:
                if not step.get("content") and not step.get("material_id"):
                    errors.append(f"步骤 {i+1} 缺少内容或物料ID")
        
        return errors


class SOPInstance(Base):
    """SOP实例模型"""
    __tablename__ = "sop_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("sop_templates.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    wechat_account_id = Column(UUID(as_uuid=True), ForeignKey("wechat_accounts.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    
    # 实例信息
    instance_name = Column(String(200), nullable=True, comment="实例名称")
    current_step_id = Column(String(100), nullable=True, comment="当前步骤ID")
    current_step_index = Column(Integer, default=0, comment="当前步骤索引")
    
    # 状态信息
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, comment="实例状态")
    progress = Column(Integer, default=0, comment="进度百分比")
    
    # 执行信息
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    next_execution_at = Column(DateTime(timezone=True), nullable=True, comment="下次执行时间")
    
    # 结果信息
    result = Column(JSONB, nullable=True, default={}, comment="执行结果")
    error_message = Column(Text, nullable=True, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    
    # 上下文数据
    context_data = Column(JSONB, nullable=True, default={}, comment="上下文数据")
    variables = Column(JSONB, nullable=True, default={}, comment="变量数据")
    
    # 配置
    config = Column(JSONB, nullable=True, default={}, comment="实例配置")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    template = relationship("SOPTemplate", back_populates="instances")
    organization = relationship("Organization")
    wechat_account = relationship("WeChatAccount")
    contact = relationship("Contact")
    tasks = relationship("SOPTask", back_populates="instance", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SOPInstance(id={self.id}, status='{self.status}', progress={self.progress})>"
    
    @property
    def is_active(self) -> bool:
        """是否为活跃状态"""
        return self.status in [TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.EXECUTING]
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """执行时长（分钟）"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() / 60)
        return None
    
    def get_current_step(self) -> Optional[Dict[str, Any]]:
        """获取当前步骤"""
        if self.template and self.current_step_id:
            return self.template.get_step_by_id(self.current_step_id)
        return None
    
    def advance_to_next_step(self) -> bool:
        """前进到下一步骤"""
        if not self.template or not self.current_step_id:
            return False
        
        next_step = self.template.get_next_step(self.current_step_id)
        if next_step:
            self.current_step_id = next_step["id"]
            self.current_step_index += 1
            self.progress = min(100, int((self.current_step_index / len(self.template.steps)) * 100))
            return True
        else:
            # 已到最后一步
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            self.progress = 100
            return False
    
    def set_variable(self, key: str, value: Any) -> None:
        """设置变量"""
        if not self.variables:
            self.variables = {}
        self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        if not self.variables:
            return default
        return self.variables.get(key, default)


class SOPTask(Base):
    """SOP任务模型（步骤执行记录）"""
    __tablename__ = "sop_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("sop_instances.id"), nullable=False)
    
    # 任务信息
    step_id = Column(String(100), nullable=False, comment="步骤ID")
    step_name = Column(String(200), nullable=False, comment="步骤名称")
    action_type = Column(SQLEnum(ActionType), nullable=False, comment="动作类型")
    
    # 状态信息
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 执行信息
    scheduled_at = Column(DateTime(timezone=True), nullable=True, comment="调度时间")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    
    # 任务数据
    input_data = Column(JSONB, nullable=True, default={}, comment="输入数据")
    output_data = Column(JSONB, nullable=True, default={}, comment="输出数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 配置
    config = Column(JSONB, nullable=True, default={}, comment="任务配置")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    instance = relationship("SOPInstance", back_populates="tasks")
    
    def __repr__(self):
        return f"<SOPTask(id={self.id}, step='{self.step_name}', status='{self.status}')>"
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """执行时长（秒）"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    @property
    def is_retryable(self) -> bool:
        """是否可重试"""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries
    
    def mark_started(self) -> None:
        """标记为开始"""
        self.status = TaskStatus.EXECUTING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, output_data: Dict[str, Any] = None) -> None:
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if output_data:
            self.output_data = output_data
    
    def mark_failed(self, error_message: str) -> None:
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1
    
    def mark_skipped(self, reason: str = None) -> None:
        """标记为跳过"""
        self.status = TaskStatus.SKIPPED
        self.completed_at = datetime.utcnow()
        if reason:
            self.error_message = reason


class SOPStatistics(Base):
    """SOP统计模型"""
    __tablename__ = "sop_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("sop_templates.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # 统计日期
    date = Column(DateTime(timezone=True), nullable=False, comment="统计日期")
    
    # 实例统计
    instances_created = Column(Integer, default=0, comment="创建实例数")
    instances_completed = Column(Integer, default=0, comment="完成实例数")
    instances_failed = Column(Integer, default=0, comment="失败实例数")
    instances_cancelled = Column(Integer, default=0, comment="取消实例数")
    
    # 任务统计
    tasks_executed = Column(Integer, default=0, comment="执行任务数")
    tasks_succeeded = Column(Integer, default=0, comment="成功任务数")
    tasks_failed = Column(Integer, default=0, comment="失败任务数")
    
    # 性能统计
    avg_completion_time = Column(Integer, default=0, comment="平均完成时间（分钟）")
    success_rate = Column(String(10), default="0%", comment="成功率")
    
    # 消息统计
    messages_sent = Column(Integer, default=0, comment="发送消息数")
    images_sent = Column(Integer, default=0, comment="发送图片数")
    files_sent = Column(Integer, default=0, comment="发送文件数")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    template = relationship("SOPTemplate")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<SOPStatistics(template_id={self.template_id}, date={self.date})>"


class SOPSchedule(Base):
    """SOP调度模型"""
    __tablename__ = "sop_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("sop_templates.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # 调度信息
    name = Column(String(200), nullable=False, comment="调度名称")
    description = Column(Text, nullable=True, comment="调度描述")
    
    # 调度配置
    cron_expression = Column(String(100), nullable=True, comment="Cron表达式")
    trigger_conditions = Column(JSONB, nullable=True, default={}, comment="触发条件")
    target_filter = Column(JSONB, nullable=True, default={}, comment="目标筛选")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_execution_at = Column(DateTime(timezone=True), nullable=True, comment="最后执行时间")
    next_execution_at = Column(DateTime(timezone=True), nullable=True, comment="下次执行时间")
    
    # 统计信息
    execution_count = Column(Integer, default=0, comment="执行次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    template = relationship("SOPTemplate")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<SOPSchedule(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100

