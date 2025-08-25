"""
SOP任务管理API路由
提供SOP模板管理、实例执行、任务调度等功能
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
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
from app.models.chat import Contact
from app.models.sop import (
    SOPTemplate, SOPInstance, SOPTask, SOPStatistics, SOPSchedule,
    SOPType, SOPStatus, TaskStatus, TriggerType, ActionType
)
from app.api.deps import get_current_user, get_current_active_user
from app.services.sop_executor import SOPExecutor
from app.services.websocket_manager import websocket_manager
from app.utils.permissions import require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Pydantic模型 ====================

class SOPStepCreate(BaseModel):
    """SOP步骤创建模型"""
    id: str = Field(..., description="步骤ID")
    name: str = Field(..., max_length=200, description="步骤名称")
    description: Optional[str] = Field(None, description="步骤描述")
    action_type: ActionType = Field(..., description="动作类型")
    
    # 动作配置
    content: Optional[str] = Field(None, description="消息内容")
    material_id: Optional[str] = Field(None, description="物料ID")
    delay_minutes: Optional[int] = Field(0, ge=0, description="延迟分钟数")
    
    # 条件配置
    conditions: Optional[Dict[str, Any]] = Field(None, description="执行条件")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量设置")
    
    # 下一步配置
    next_steps: Optional[List[str]] = Field(None, description="下一步骤ID列表")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "step_001",
                "name": "发送欢迎消息",
                "description": "向新好友发送欢迎消息",
                "action_type": "send_message",
                "content": "你好，欢迎添加我的微信！",
                "delay_minutes": 0,
                "conditions": {"user_type": "new_friend"},
                "next_steps": ["step_002"]
            }
        }


class SOPTemplateCreate(BaseModel):
    """SOP模板创建请求"""
    name: str = Field(..., max_length=200, description="SOP名称")
    description: Optional[str] = Field(None, description="SOP描述")
    sop_type: SOPType = Field(..., description="SOP类型")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    tags: Optional[List[str]] = Field([], description="标签列表")
    
    # 步骤定义
    steps: List[SOPStepCreate] = Field(..., min_items=1, description="步骤列表")
    
    # 触发配置
    trigger_config: Optional[Dict[str, Any]] = Field({}, description="触发配置")
    target_config: Optional[Dict[str, Any]] = Field({}, description="目标配置")
    
    # 设置
    is_shared: bool = Field(False, description="是否共享")
    
    @validator("steps")
    def validate_steps(cls, v):
        """验证步骤配置"""
        if not v:
            raise ValueError("至少需要一个步骤")
        
        step_ids = set()
        for step in v:
            if step.id in step_ids:
                raise ValueError(f"步骤ID '{step.id}' 重复")
            step_ids.add(step.id)
        
        return v


class SOPTemplateUpdate(BaseModel):
    """SOP模板更新请求"""
    name: Optional[str] = Field(None, max_length=200, description="SOP名称")
    description: Optional[str] = Field(None, description="SOP描述")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    steps: Optional[List[SOPStepCreate]] = Field(None, description="步骤列表")
    trigger_config: Optional[Dict[str, Any]] = Field(None, description="触发配置")
    target_config: Optional[Dict[str, Any]] = Field(None, description="目标配置")
    is_shared: Optional[bool] = Field(None, description="是否共享")
    status: Optional[SOPStatus] = Field(None, description="状态")


class SOPTemplateResponse(BaseModel):
    """SOP模板响应模型"""
    id: str
    name: str
    description: Optional[str]
    sop_type: SOPType
    category: Optional[str]
    tags: List[str]
    status: SOPStatus
    version: str
    
    # 统计信息
    total_instances: int
    active_instances: int
    success_rate: str
    
    # 配置
    steps: List[Dict[str, Any]]
    trigger_config: Dict[str, Any]
    target_config: Dict[str, Any]
    
    # 设置
    is_template: bool
    is_shared: bool
    is_active: bool
    
    # 时间
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SOPInstanceCreate(BaseModel):
    """SOP实例创建请求"""
    template_id: str = Field(..., description="模板ID")
    wechat_account_id: str = Field(..., description="微信账号ID")
    contact_id: str = Field(..., description="联系人ID")
    instance_name: Optional[str] = Field(None, description="实例名称")
    variables: Optional[Dict[str, Any]] = Field({}, description="初始变量")
    config: Optional[Dict[str, Any]] = Field({}, description="实例配置")


class SOPInstanceResponse(BaseModel):
    """SOP实例响应模型"""
    id: str
    template_id: str
    instance_name: Optional[str]
    current_step_id: Optional[str]
    current_step_index: int
    status: TaskStatus
    progress: int
    
    # 执行信息
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    next_execution_at: Optional[datetime]
    duration_minutes: Optional[int]
    
    # 结果信息
    result: Dict[str, Any]
    error_message: Optional[str]
    retry_count: int
    
    # 上下文
    context_data: Dict[str, Any]
    variables: Dict[str, Any]
    
    # 关联信息
    template_name: Optional[str] = None
    contact_name: Optional[str] = None
    account_nickname: Optional[str] = None
    
    # 时间
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SOPTaskResponse(BaseModel):
    """SOP任务响应模型"""
    id: str
    instance_id: str
    step_id: str
    step_name: str
    action_type: ActionType
    status: TaskStatus
    retry_count: int
    max_retries: int
    
    # 执行信息
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    
    # 数据
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    
    # 时间
    created_at: datetime
    
    class Config:
        from_attributes = True


class SOPStatsResponse(BaseModel):
    """SOP统计响应"""
    total_templates: int
    active_templates: int
    total_instances: int
    active_instances: int
    completed_instances: int
    failed_instances: int
    
    # 今日统计
    today_instances_created: int
    today_instances_completed: int
    today_tasks_executed: int
    today_success_rate: float
    
    # 类型分布
    type_distribution: Dict[str, int]
    
    # 状态分布
    instance_status_distribution: Dict[str, int]
    task_status_distribution: Dict[str, int]


class BatchCreateInstanceRequest(BaseModel):
    """批量创建实例请求"""
    template_id: str = Field(..., description="模板ID")
    targets: List[Dict[str, str]] = Field(..., description="目标列表")
    variables: Optional[Dict[str, Any]] = Field({}, description="公共变量")
    config: Optional[Dict[str, Any]] = Field({}, description="公共配置")
    
    @validator("targets")
    def validate_targets(cls, v):
        """验证目标列表"""
        if not v:
            raise ValueError("目标列表不能为空")
        
        required_fields = ["wechat_account_id", "contact_id"]
        for target in v:
            for field in required_fields:
                if field not in target:
                    raise ValueError(f"目标缺少必需字段: {field}")
        
        return v


# ==================== API路由 ====================

@router.get("/stats", response_model=SOPStatsResponse)
async def get_sop_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取SOP统计信息"""
    try:
        org_id = current_user.organization_id
        
        # 模板统计
        total_templates_result = await db.execute(
            select(func.count(SOPTemplate.id))
            .where(SOPTemplate.organization_id == org_id, SOPTemplate.is_active == True)
        )
        total_templates = total_templates_result.scalar() or 0
        
        active_templates_result = await db.execute(
            select(func.count(SOPTemplate.id))
            .where(
                SOPTemplate.organization_id == org_id,
                SOPTemplate.status == SOPStatus.ACTIVE,
                SOPTemplate.is_active == True
            )
        )
        active_templates = active_templates_result.scalar() or 0
        
        # 实例统计
        total_instances_result = await db.execute(
            select(func.count(SOPInstance.id))
            .where(SOPInstance.organization_id == org_id)
        )
        total_instances = total_instances_result.scalar() or 0
        
        active_instances_result = await db.execute(
            select(func.count(SOPInstance.id))
            .where(
                SOPInstance.organization_id == org_id,
                SOPInstance.status.in_([TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.EXECUTING])
            )
        )
        active_instances = active_instances_result.scalar() or 0
        
        completed_instances_result = await db.execute(
            select(func.count(SOPInstance.id))
            .where(
                SOPInstance.organization_id == org_id,
                SOPInstance.status == TaskStatus.COMPLETED
            )
        )
        completed_instances = completed_instances_result.scalar() or 0
        
        failed_instances_result = await db.execute(
            select(func.count(SOPInstance.id))
            .where(
                SOPInstance.organization_id == org_id,
                SOPInstance.status == TaskStatus.FAILED
            )
        )
        failed_instances = failed_instances_result.scalar() or 0
        
        # 今日统计
        today = datetime.utcnow().date()
        today_instances_created_result = await db.execute(
            select(func.count(SOPInstance.id))
            .where(
                SOPInstance.organization_id == org_id,
                SOPInstance.created_at >= today
            )
        )
        today_instances_created = today_instances_created_result.scalar() or 0
        
        today_instances_completed_result = await db.execute(
            select(func.count(SOPInstance.id))
            .where(
                SOPInstance.organization_id == org_id,
                SOPInstance.status == TaskStatus.COMPLETED,
                SOPInstance.completed_at >= today
            )
        )
        today_instances_completed = today_instances_completed_result.scalar() or 0
        
        # 计算今日成功率
        today_success_rate = 0.0
        if today_instances_created > 0:
            today_success_rate = (today_instances_completed / today_instances_created) * 100
        
        # 类型分布
        type_distribution_result = await db.execute(
            select(SOPTemplate.sop_type, func.count(SOPTemplate.id))
            .where(SOPTemplate.organization_id == org_id, SOPTemplate.is_active == True)
            .group_by(SOPTemplate.sop_type)
        )
        type_distribution = {sop_type.value: count for sop_type, count in type_distribution_result.all()}
        
        # 实例状态分布
        instance_status_result = await db.execute(
            select(SOPInstance.status, func.count(SOPInstance.id))
            .where(SOPInstance.organization_id == org_id)
            .group_by(SOPInstance.status)
        )
        instance_status_distribution = {status.value: count for status, count in instance_status_result.all()}
        
        return SOPStatsResponse(
            total_templates=total_templates,
            active_templates=active_templates,
            total_instances=total_instances,
            active_instances=active_instances,
            completed_instances=completed_instances,
            failed_instances=failed_instances,
            today_instances_created=today_instances_created,
            today_instances_completed=today_instances_completed,
            today_tasks_executed=0,  # 需要从任务表统计
            today_success_rate=round(today_success_rate, 2),
            type_distribution=type_distribution,
            instance_status_distribution=instance_status_distribution,
            task_status_distribution={}  # 需要从任务表统计
        )
        
    except Exception as e:
        logger.error(f"获取SOP统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )


@router.get("/templates", response_model=List[SOPTemplateResponse])
async def get_sop_templates(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sop_type: Optional[SOPType] = Query(None, description="SOP类型筛选"),
    status: Optional[SOPStatus] = Query(None, description="状态筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取SOP模板列表"""
    try:
        # 构建查询条件
        query = select(SOPTemplate).where(
            SOPTemplate.organization_id == current_user.organization_id,
            SOPTemplate.is_active == True
        )
        
        # 应用筛选条件
        if sop_type:
            query = query.where(SOPTemplate.sop_type == sop_type)
        
        if status:
            query = query.where(SOPTemplate.status == status)
        
        if category:
            query = query.where(SOPTemplate.category == category)
        
        if search:
            query = query.where(
                or_(
                    SOPTemplate.name.ilike(f"%{search}%"),
                    SOPTemplate.description.ilike(f"%{search}%")
                )
            )
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(SOPTemplate.updated_at))
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return [SOPTemplateResponse.from_orm(template) for template in templates]
        
    except Exception as e:
        logger.error(f"获取SOP模板列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模板列表失败"
        )


@router.post("/templates", response_model=SOPTemplateResponse)
async def create_sop_template(
    template_data: SOPTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建SOP模板"""
    try:
        # 检查权限
        require_permission(current_user, "sop.create")
        
        # 验证步骤配置
        steps_data = [step.dict() for step in template_data.steps]
        
        # 创建模板
        template = SOPTemplate(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            name=template_data.name,
            description=template_data.description,
            sop_type=template_data.sop_type,
            category=template_data.category,
            tags=template_data.tags,
            steps=steps_data,
            trigger_config=template_data.trigger_config,
            target_config=template_data.target_config,
            is_shared=template_data.is_shared,
            status=SOPStatus.DRAFT
        )
        
        # 验证步骤
        validation_errors = template.validate_steps()
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"步骤配置错误: {'; '.join(validation_errors)}"
            )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"SOP模板创建成功: {template.id}")
        
        return SOPTemplateResponse.from_orm(template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建SOP模板失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建模板失败"
        )


@router.get("/templates/{template_id}", response_model=SOPTemplateResponse)
async def get_sop_template(
    template_id: str = Path(..., description="模板ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取SOP模板详情"""
    try:
        result = await db.execute(
            select(SOPTemplate)
            .where(
                SOPTemplate.id == template_id,
                SOPTemplate.organization_id == current_user.organization_id
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )
        
        return SOPTemplateResponse.from_orm(template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取SOP模板详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模板详情失败"
        )


@router.put("/templates/{template_id}", response_model=SOPTemplateResponse)
async def update_sop_template(
    template_id: str = Path(..., description="模板ID"),
    update_data: SOPTemplateUpdate = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新SOP模板"""
    try:
        # 检查权限
        require_permission(current_user, "sop.update")
        
        result = await db.execute(
            select(SOPTemplate)
            .where(
                SOPTemplate.id == template_id,
                SOPTemplate.organization_id == current_user.organization_id
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        
        # 特殊处理steps字段
        if "steps" in update_dict and update_dict["steps"]:
            steps_data = [step.dict() if hasattr(step, 'dict') else step for step in update_dict["steps"]]
            update_dict["steps"] = steps_data
            
            # 验证步骤
            template.steps = steps_data
            validation_errors = template.validate_steps()
            if validation_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"步骤配置错误: {'; '.join(validation_errors)}"
                )
        
        # 应用更新
        for field, value in update_dict.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"SOP模板更新成功: {template.id}")
        
        return SOPTemplateResponse.from_orm(template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新SOP模板失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新模板失败"
        )


@router.post("/templates/{template_id}/activate")
async def activate_sop_template(
    template_id: str = Path(..., description="模板ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """激活SOP模板"""
    try:
        # 检查权限
        require_permission(current_user, "sop.update")
        
        result = await db.execute(
            select(SOPTemplate)
            .where(
                SOPTemplate.id == template_id,
                SOPTemplate.organization_id == current_user.organization_id
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )
        
        # 验证模板可以激活
        validation_errors = template.validate_steps()
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模板配置错误，无法激活: {'; '.join(validation_errors)}"
            )
        
        template.status = SOPStatus.ACTIVE
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "模板已激活", "template_id": template_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活SOP模板失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活模板失败"
        )


@router.get("/instances", response_model=List[SOPInstanceResponse])
async def get_sop_instances(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    template_id: Optional[str] = Query(None, description="模板ID筛选"),
    status: Optional[TaskStatus] = Query(None, description="状态筛选"),
    wechat_account_id: Optional[str] = Query(None, description="微信账号ID筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取SOP实例列表"""
    try:
        # 构建查询条件
        query = select(SOPInstance).options(
            joinedload(SOPInstance.template),
            joinedload(SOPInstance.contact),
            joinedload(SOPInstance.wechat_account)
        ).where(SOPInstance.organization_id == current_user.organization_id)
        
        # 应用筛选条件
        if template_id:
            query = query.where(SOPInstance.template_id == template_id)
        
        if status:
            query = query.where(SOPInstance.status == status)
        
        if wechat_account_id:
            query = query.where(SOPInstance.wechat_account_id == wechat_account_id)
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(SOPInstance.created_at))
        
        result = await db.execute(query)
        instances = result.unique().scalars().all()
        
        # 构建响应数据
        instance_responses = []
        for instance in instances:
            instance_data = SOPInstanceResponse.from_orm(instance)
            # 添加关联信息
            if instance.template:
                instance_data.template_name = instance.template.name
            if instance.contact:
                instance_data.contact_name = instance.contact.display_name
            if instance.wechat_account:
                instance_data.account_nickname = instance.wechat_account.nickname
            
            instance_responses.append(instance_data)
        
        return instance_responses
        
    except Exception as e:
        logger.error(f"获取SOP实例列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取实例列表失败"
        )


@router.post("/instances", response_model=SOPInstanceResponse)
async def create_sop_instance(
    instance_data: SOPInstanceCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建SOP实例"""
    try:
        # 检查权限
        require_permission(current_user, "sop.execute")
        
        # 验证模板存在且激活
        template_result = await db.execute(
            select(SOPTemplate)
            .where(
                SOPTemplate.id == instance_data.template_id,
                SOPTemplate.organization_id == current_user.organization_id,
                SOPTemplate.status == SOPStatus.ACTIVE
            )
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在或未激活"
            )
        
        # 验证微信账号存在且在线
        account_result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.id == instance_data.wechat_account_id,
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.is_active == True
            )
        )
        account = account_result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="微信账号不存在"
            )
        
        if account.status != DeviceStatus.ONLINE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="微信账号未在线"
            )
        
        # 验证联系人存在
        contact_result = await db.execute(
            select(Contact)
            .where(
                Contact.id == instance_data.contact_id,
                Contact.organization_id == current_user.organization_id,
                Contact.wechat_account_id == account.id
            )
        )
        contact = contact_result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="联系人不存在"
            )
        
        # 检查是否已有活跃实例
        existing_result = await db.execute(
            select(SOPInstance)
            .where(
                SOPInstance.template_id == instance_data.template_id,
                SOPInstance.contact_id == instance_data.contact_id,
                SOPInstance.status.in_([TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.EXECUTING])
            )
        )
        existing_instance = existing_result.scalar_one_or_none()
        
        if existing_instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该联系人已有活跃的SOP实例"
            )
        
        # 创建实例
        instance = SOPInstance(
            template_id=template.id,
            organization_id=current_user.organization_id,
            wechat_account_id=account.id,
            contact_id=contact.id,
            instance_name=instance_data.instance_name or f"{template.name} - {contact.display_name}",
            variables=instance_data.variables,
            config=instance_data.config,
            current_step_id=template.steps[0]["id"] if template.steps else None,
            current_step_index=0
        )
        
        db.add(instance)
        
        # 更新模板统计
        template.total_instances += 1
        template.active_instances += 1
        template.last_used_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(instance)
        
        # 异步启动执行
        background_tasks.add_task(
            start_sop_execution,
            instance_id=str(instance.id)
        )
        
        logger.info(f"SOP实例创建成功: {instance.id}")
        
        return SOPInstanceResponse.from_orm(instance)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建SOP实例失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建实例失败"
        )


@router.post("/instances/batch", response_model=Dict[str, Any])
async def create_sop_instances_batch(
    batch_data: BatchCreateInstanceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """批量创建SOP实例"""
    try:
        # 检查权限
        require_permission(current_user, "sop.execute")
        
        # 验证模板
        template_result = await db.execute(
            select(SOPTemplate)
            .where(
                SOPTemplate.id == batch_data.template_id,
                SOPTemplate.organization_id == current_user.organization_id,
                SOPTemplate.status == SOPStatus.ACTIVE
            )
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在或未激活"
            )
        
        created_instances = []
        failed_targets = []
        
        for target in batch_data.targets:
            try:
                # 验证微信账号和联系人
                account_result = await db.execute(
                    select(WeChatAccount)
                    .where(
                        WeChatAccount.id == target["wechat_account_id"],
                        WeChatAccount.organization_id == current_user.organization_id,
                        WeChatAccount.is_active == True
                    )
                )
                account = account_result.scalar_one_or_none()
                
                contact_result = await db.execute(
                    select(Contact)
                    .where(
                        Contact.id == target["contact_id"],
                        Contact.organization_id == current_user.organization_id
                    )
                )
                contact = contact_result.scalar_one_or_none()
                
                if not account or not contact:
                    failed_targets.append({
                        "target": target,
                        "error": "微信账号或联系人不存在"
                    })
                    continue
                
                if account.status != DeviceStatus.ONLINE:
                    failed_targets.append({
                        "target": target,
                        "error": "微信账号未在线"
                    })
                    continue
                
                # 检查已有实例
                existing_result = await db.execute(
                    select(SOPInstance)
                    .where(
                        SOPInstance.template_id == template.id,
                        SOPInstance.contact_id == contact.id,
                        SOPInstance.status.in_([TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.EXECUTING])
                    )
                )
                existing_instance = existing_result.scalar_one_or_none()
                
                if existing_instance:
                    failed_targets.append({
                        "target": target,
                        "error": "已有活跃的SOP实例"
                    })
                    continue
                
                # 创建实例
                instance = SOPInstance(
                    template_id=template.id,
                    organization_id=current_user.organization_id,
                    wechat_account_id=account.id,
                    contact_id=contact.id,
                    instance_name=f"{template.name} - {contact.display_name}",
                    variables=batch_data.variables,
                    config=batch_data.config,
                    current_step_id=template.steps[0]["id"] if template.steps else None,
                    current_step_index=0
                )
                
                db.add(instance)
                created_instances.append(instance)
                
            except Exception as e:
                failed_targets.append({
                    "target": target,
                    "error": str(e)
                })
        
        # 更新模板统计
        if created_instances:
            template.total_instances += len(created_instances)
            template.active_instances += len(created_instances)
            template.last_used_at = datetime.utcnow()
        
        await db.commit()
        
        # 异步启动所有实例的执行
        for instance in created_instances:
            await db.refresh(instance)
            background_tasks.add_task(
                start_sop_execution,
                instance_id=str(instance.id)
            )
        
        logger.info(f"批量创建SOP实例: 成功{len(created_instances)}个，失败{len(failed_targets)}个")
        
        return {
            "success_count": len(created_instances),
            "failed_count": len(failed_targets),
            "created_instances": [str(instance.id) for instance in created_instances],
            "failed_targets": failed_targets
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量创建SOP实例失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量创建失败"
        )


@router.post("/instances/{instance_id}/pause")
async def pause_sop_instance(
    instance_id: str = Path(..., description="实例ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """暂停SOP实例"""
    try:
        # 检查权限
        require_permission(current_user, "sop.execute")
        
        result = await db.execute(
            select(SOPInstance)
            .where(
                SOPInstance.id == instance_id,
                SOPInstance.organization_id == current_user.organization_id
            )
        )
        instance = result.scalar_one_or_none()
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实例不存在"
            )
        
        if not instance.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="实例未在活跃状态"
            )
        
        # 暂停实例（这里可以扩展为更复杂的暂停逻辑）
        instance.status = TaskStatus.CANCELLED
        instance.completed_at = datetime.utcnow()
        instance.error_message = "用户手动暂停"
        
        await db.commit()
        
        # 发送WebSocket通知
        await websocket_manager.send_to_user(str(current_user.id), {
            "type": "sop_instance_paused",
            "instance_id": instance_id
        })
        
        return {"message": "实例已暂停", "instance_id": instance_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停SOP实例失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="暂停实例失败"
        )


@router.get("/instances/{instance_id}/tasks", response_model=List[SOPTaskResponse])
async def get_instance_tasks(
    instance_id: str = Path(..., description="实例ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取实例任务列表"""
    try:
        # 验证实例存在且属于当前组织
        instance_result = await db.execute(
            select(SOPInstance)
            .where(
                SOPInstance.id == instance_id,
                SOPInstance.organization_id == current_user.organization_id
            )
        )
        instance = instance_result.scalar_one_or_none()
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="实例不存在"
            )
        
        # 获取任务列表
        result = await db.execute(
            select(SOPTask)
            .where(SOPTask.instance_id == instance_id)
            .order_by(SOPTask.created_at)
        )
        tasks = result.scalars().all()
        
        return [SOPTaskResponse.from_orm(task) for task in tasks]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实例任务列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务列表失败"
        )


# ==================== 后台任务函数 ====================

async def start_sop_execution(instance_id: str):
    """启动SOP实例执行（后台任务）"""
    try:
        # 这里应该调用SOP执行器开始执行
        executor = SOPExecutor()
        await executor.execute_instance(instance_id)
        
        logger.info(f"SOP实例执行启动: {instance_id}")
        
    except Exception as e:
        logger.error(f"启动SOP实例执行失败: {instance_id}, {str(e)}")
        
        # 更新实例状态为失败
        async with get_db() as db:
            await db.execute(
                update(SOPInstance)
                .where(SOPInstance.id == instance_id)
                .values(
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()

