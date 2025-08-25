"""
算力管理API路由
提供成本计量、配额管理、预算控制、优化建议等功能
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, validator
import logging
from decimal import Decimal
import calendar

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.user import User
from app.models.cost import (
    CostModel, CostRecord, CostQuota, CostBudget, CostAlert, CostStatistics, CostOptimization,
    CostType, BillingUnit, AlertType
)
from app.api.deps import get_current_user, get_current_active_user
from app.services.cost_calculator import cost_calculator
from app.services.cost_analyzer import cost_analyzer
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service
from app.utils.permissions import require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Pydantic模型 ====================

class CostModelCreate(BaseModel):
    """成本模型创建请求"""
    name: str = Field(..., max_length=200, description="模型名称")
    description: Optional[str] = Field(None, description="模型描述")
    provider: str = Field(..., max_length=100, description="服务提供商")
    model_type: str = Field(..., max_length=100, description="模型类型")
    cost_type: CostType = Field(..., description="成本类型")
    billing_unit: BillingUnit = Field(..., description="计费单位")
    input_price: Optional[Decimal] = Field(None, description="输入价格")
    output_price: Optional[Decimal] = Field(None, description="输出价格")
    base_price: Optional[Decimal] = Field(None, description="基础价格")
    unit_size: int = Field(1000, ge=1, description="计费单位大小")
    config: Optional[Dict[str, Any]] = Field({}, description="配置信息")


class CostModelResponse(BaseModel):
    """成本模型响应"""
    id: str
    name: str
    description: Optional[str]
    provider: str
    model_type: str
    cost_type: CostType
    billing_unit: BillingUnit
    input_price: Optional[Decimal]
    output_price: Optional[Decimal]
    base_price: Optional[Decimal]
    unit_size: int
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CostRecordResponse(BaseModel):
    """成本记录响应"""
    id: str
    request_id: Optional[str]
    request_type: str
    model_name: Optional[str]
    provider_name: Optional[str]
    input_units: int
    output_units: int
    total_units: int
    input_cost: Decimal
    output_cost: Decimal
    total_cost: Decimal
    created_at: datetime
    
    # 关联信息
    user_name: Optional[str] = None
    account_nickname: Optional[str] = None
    
    class Config:
        from_attributes = True


class CostQuotaCreate(BaseModel):
    """成本配额创建请求"""
    name: str = Field(..., max_length=200, description="配额名称")
    description: Optional[str] = Field(None, description="配额描述")
    quota_type: str = Field(..., description="配额类型")
    total_quota: Decimal = Field(..., ge=0, description="总配额")
    period_type: str = Field(..., description="周期类型")
    period_start: datetime = Field(..., description="周期开始")
    period_end: datetime = Field(..., description="周期结束")
    daily_limit: Optional[Decimal] = Field(None, description="日限额")
    hourly_limit: Optional[Decimal] = Field(None, description="小时限额")
    warning_threshold: float = Field(0.8, ge=0, le=1, description="预警阈值")
    critical_threshold: float = Field(0.95, ge=0, le=1, description="严重阈值")
    user_id: Optional[str] = Field(None, description="用户ID")
    config: Optional[Dict[str, Any]] = Field({}, description="配置信息")


class CostQuotaResponse(BaseModel):
    """成本配额响应"""
    id: str
    name: str
    description: Optional[str]
    quota_type: str
    total_quota: Decimal
    used_quota: Decimal
    remaining_quota: Decimal
    usage_percentage: float
    period_type: str
    period_start: datetime
    period_end: datetime
    daily_limit: Optional[Decimal]
    hourly_limit: Optional[Decimal]
    warning_threshold: float
    critical_threshold: float
    is_active: bool
    is_exceeded: bool
    is_warning: bool
    is_critical: bool
    
    # 关联信息
    user_name: Optional[str] = None
    
    # 时间
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CostDashboardResponse(BaseModel):
    """成本仪表板响应"""
    # 总览统计
    total_cost_today: Decimal
    total_cost_this_month: Decimal
    total_cost_last_month: Decimal
    cost_trend_percentage: float
    
    # 使用量统计
    total_requests_today: int
    total_tokens_today: int
    avg_cost_per_request: Decimal
    avg_cost_per_token: Decimal
    
    # 配额信息
    active_quotas: int
    exceeded_quotas: int
    warning_quotas: int
    
    # 成本分布
    cost_by_type: Dict[str, Decimal]
    cost_by_user: List[Dict[str, Any]]
    cost_by_model: List[Dict[str, Any]]
    
    # 趋势数据
    daily_cost_trend: List[Dict[str, Any]]
    hourly_usage_pattern: List[Dict[str, Any]]
    
    # 告警信息
    active_alerts: int
    recent_alerts: List[Dict[str, Any]]


class CostAnalyticsRequest(BaseModel):
    """成本分析请求"""
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    group_by: str = Field("day", description="分组方式")
    filters: Optional[Dict[str, Any]] = Field({}, description="筛选条件")


class CostOptimizationResponse(BaseModel):
    """成本优化响应"""
    id: str
    title: str
    description: str
    optimization_type: str
    current_cost: Decimal
    potential_savings: Decimal
    savings_percentage: float
    recommendations: List[Dict[str, Any]]
    implementation_effort: str
    priority: str
    status: str
    is_implemented: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== API路由 ====================

@router.get("/dashboard", response_model=CostDashboardResponse)
async def get_cost_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成本仪表板数据"""
    try:
        org_id = current_user.organization_id
        today = datetime.utcnow().date()
        this_month_start = datetime(today.year, today.month, 1)
        last_month_start = datetime(today.year, today.month - 1, 1) if today.month > 1 else datetime(today.year - 1, 12, 1)
        last_month_end = this_month_start - timedelta(days=1)
        
        # 今日成本
        today_cost_result = await db.execute(
            select(func.coalesce(func.sum(CostRecord.total_cost), 0))
            .where(
                CostRecord.organization_id == org_id,
                func.date(CostRecord.created_at) == today
            )
        )
        total_cost_today = today_cost_result.scalar() or Decimal('0.00')
        
        # 本月成本
        this_month_cost_result = await db.execute(
            select(func.coalesce(func.sum(CostRecord.total_cost), 0))
            .where(
                CostRecord.organization_id == org_id,
                CostRecord.created_at >= this_month_start
            )
        )
        total_cost_this_month = this_month_cost_result.scalar() or Decimal('0.00')
        
        # 上月成本
        last_month_cost_result = await db.execute(
            select(func.coalesce(func.sum(CostRecord.total_cost), 0))
            .where(
                CostRecord.organization_id == org_id,
                CostRecord.created_at >= last_month_start,
                CostRecord.created_at <= last_month_end
            )
        )
        total_cost_last_month = last_month_cost_result.scalar() or Decimal('0.00')
        
        # 计算趋势
        cost_trend_percentage = 0.0
        if total_cost_last_month > 0:
            cost_trend_percentage = float((total_cost_this_month - total_cost_last_month) / total_cost_last_month * 100)
        
        # 今日使用量统计
        today_usage_result = await db.execute(
            select(
                func.count(CostRecord.id),
                func.coalesce(func.sum(CostRecord.total_units), 0)
            )
            .where(
                CostRecord.organization_id == org_id,
                func.date(CostRecord.created_at) == today
            )
        )
        total_requests_today, total_tokens_today = today_usage_result.first() or (0, 0)
        
        # 平均成本
        avg_cost_per_request = Decimal('0.00')
        avg_cost_per_token = Decimal('0.00')
        if total_requests_today > 0:
            avg_cost_per_request = total_cost_today / total_requests_today
        if total_tokens_today > 0:
            avg_cost_per_token = total_cost_today / total_tokens_today
        
        # 配额统计
        quota_stats_result = await db.execute(
            select(
                func.count(CostQuota.id),
                func.sum(func.cast(CostQuota.is_exceeded, Integer)),
                func.sum(func.case(
                    (CostQuota.used_quota / CostQuota.total_quota >= CostQuota.warning_threshold, 1),
                    else_=0
                ))
            )
            .where(
                CostQuota.organization_id == org_id,
                CostQuota.is_active == True
            )
        )
        active_quotas, exceeded_quotas, warning_quotas = quota_stats_result.first() or (0, 0, 0)
        
        # 成本分布 - 按类型
        cost_by_type_result = await db.execute(
            select(
                CostModel.cost_type,
                func.coalesce(func.sum(CostRecord.total_cost), 0)
            )
            .join(CostModel, CostRecord.cost_model_id == CostModel.id)
            .where(
                CostRecord.organization_id == org_id,
                CostRecord.created_at >= this_month_start
            )
            .group_by(CostModel.cost_type)
        )
        cost_by_type = {cost_type.value: cost for cost_type, cost in cost_by_type_result.all()}
        
        # 成本分布 - 按用户
        cost_by_user_result = await db.execute(
            select(
                User.username,
                func.coalesce(func.sum(CostRecord.total_cost), 0)
            )
            .join(User, CostRecord.user_id == User.id)
            .where(
                CostRecord.organization_id == org_id,
                CostRecord.created_at >= this_month_start
            )
            .group_by(User.id, User.username)
            .order_by(desc(func.sum(CostRecord.total_cost)))
            .limit(10)
        )
        cost_by_user = [
            {"name": username, "cost": float(cost)}
            for username, cost in cost_by_user_result.all()
        ]
        
        # 成本分布 - 按模型
        cost_by_model_result = await db.execute(
            select(
                CostRecord.model_name,
                func.coalesce(func.sum(CostRecord.total_cost), 0)
            )
            .where(
                CostRecord.organization_id == org_id,
                CostRecord.created_at >= this_month_start,
                CostRecord.model_name.isnot(None)
            )
            .group_by(CostRecord.model_name)
            .order_by(desc(func.sum(CostRecord.total_cost)))
            .limit(10)
        )
        cost_by_model = [
            {"name": model_name, "cost": float(cost)}
            for model_name, cost in cost_by_model_result.all()
        ]
        
        # 每日成本趋势（最近30天）
        trend_start = datetime.utcnow() - timedelta(days=30)
        daily_trend_result = await db.execute(
            select(
                func.date(CostRecord.created_at),
                func.coalesce(func.sum(CostRecord.total_cost), 0)
            )
            .where(
                CostRecord.organization_id == org_id,
                CostRecord.created_at >= trend_start
            )
            .group_by(func.date(CostRecord.created_at))
            .order_by(func.date(CostRecord.created_at))
        )
        daily_cost_trend = [
            {"date": date.isoformat(), "cost": float(cost)}
            for date, cost in daily_trend_result.all()
        ]
        
        # 小时使用模式（今日）
        hourly_pattern_result = await db.execute(
            select(
                func.extract('hour', CostRecord.created_at),
                func.count(CostRecord.id),
                func.coalesce(func.sum(CostRecord.total_cost), 0)
            )
            .where(
                CostRecord.organization_id == org_id,
                func.date(CostRecord.created_at) == today
            )
            .group_by(func.extract('hour', CostRecord.created_at))
            .order_by(func.extract('hour', CostRecord.created_at))
        )
        hourly_usage_pattern = [
            {"hour": int(hour), "requests": requests, "cost": float(cost)}
            for hour, requests, cost in hourly_pattern_result.all()
        ]
        
        # 活跃告警
        active_alerts_result = await db.execute(
            select(func.count(CostAlert.id))
            .where(
                CostAlert.organization_id == org_id,
                CostAlert.is_active == True,
                CostAlert.is_resolved == False
            )
        )
        active_alerts = active_alerts_result.scalar() or 0
        
        # 最近告警
        recent_alerts_result = await db.execute(
            select(CostAlert)
            .where(
                CostAlert.organization_id == org_id,
                CostAlert.is_active == True
            )
            .order_by(desc(CostAlert.created_at))
            .limit(5)
        )
        recent_alerts = [
            {
                "id": str(alert.id),
                "title": alert.title,
                "level": alert.level,
                "created_at": alert.created_at.isoformat()
            }
            for alert in recent_alerts_result.scalars().all()
        ]
        
        return CostDashboardResponse(
            total_cost_today=total_cost_today,
            total_cost_this_month=total_cost_this_month,
            total_cost_last_month=total_cost_last_month,
            cost_trend_percentage=cost_trend_percentage,
            total_requests_today=total_requests_today,
            total_tokens_today=total_tokens_today,
            avg_cost_per_request=avg_cost_per_request,
            avg_cost_per_token=avg_cost_per_token,
            active_quotas=active_quotas or 0,
            exceeded_quotas=exceeded_quotas or 0,
            warning_quotas=warning_quotas or 0,
            cost_by_type=cost_by_type,
            cost_by_user=cost_by_user,
            cost_by_model=cost_by_model,
            daily_cost_trend=daily_cost_trend,
            hourly_usage_pattern=hourly_usage_pattern,
            active_alerts=active_alerts,
            recent_alerts=recent_alerts
        )
        
    except Exception as e:
        logger.error(f"获取成本仪表板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取仪表板数据失败"
        )


@router.get("/models", response_model=List[CostModelResponse])
async def get_cost_models(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    provider: Optional[str] = Query(None, description="提供商筛选"),
    cost_type: Optional[CostType] = Query(None, description="成本类型筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成本模型列表"""
    try:
        # 构建查询条件
        query = select(CostModel).where(
            CostModel.organization_id == current_user.organization_id,
            CostModel.is_active == True
        )
        
        # 应用筛选条件
        if provider:
            query = query.where(CostModel.provider.ilike(f"%{provider}%"))
        
        if cost_type:
            query = query.where(CostModel.cost_type == cost_type)
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(CostModel.updated_at))
        
        result = await db.execute(query)
        models = result.scalars().all()
        
        return [CostModelResponse.from_orm(model) for model in models]
        
    except Exception as e:
        logger.error(f"获取成本模型列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取模型列表失败"
        )


@router.post("/models", response_model=CostModelResponse)
async def create_cost_model(
    model_data: CostModelCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建成本模型"""
    try:
        # 检查权限
        require_permission(current_user, "cost.manage")
        
        # 创建模型
        cost_model = CostModel(
            organization_id=current_user.organization_id,
            name=model_data.name,
            description=model_data.description,
            provider=model_data.provider,
            model_type=model_data.model_type,
            cost_type=model_data.cost_type,
            billing_unit=model_data.billing_unit,
            input_price=model_data.input_price,
            output_price=model_data.output_price,
            base_price=model_data.base_price,
            unit_size=model_data.unit_size,
            config=model_data.config
        )
        
        db.add(cost_model)
        await db.commit()
        await db.refresh(cost_model)
        
        logger.info(f"成本模型创建成功: {cost_model.id}")
        
        return CostModelResponse.from_orm(cost_model)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建成本模型失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建成本模型失败"
        )


@router.get("/records", response_model=List[CostRecordResponse])
async def get_cost_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    model_name: Optional[str] = Query(None, description="模型名称筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成本记录列表"""
    try:
        # 构建查询条件
        query = select(CostRecord).options(
            joinedload(CostRecord.user),
            joinedload(CostRecord.wechat_account)
        ).where(CostRecord.organization_id == current_user.organization_id)
        
        # 非管理员只能查看自己的记录
        if not current_user.is_admin:
            query = query.where(CostRecord.user_id == current_user.id)
        elif user_id:
            query = query.where(CostRecord.user_id == user_id)
        
        # 应用时间筛选
        if start_date:
            query = query.where(CostRecord.created_at >= start_date)
        if end_date:
            query = query.where(CostRecord.created_at <= end_date)
        
        # 应用模型筛选
        if model_name:
            query = query.where(CostRecord.model_name.ilike(f"%{model_name}%"))
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(CostRecord.created_at))
        
        result = await db.execute(query)
        records = result.unique().scalars().all()
        
        # 构建响应数据
        record_responses = []
        for record in records:
            record_data = CostRecordResponse.from_orm(record)
            # 添加关联信息
            if record.user:
                record_data.user_name = record.user.username
            if record.wechat_account:
                record_data.account_nickname = record.wechat_account.nickname
            
            record_responses.append(record_data)
        
        return record_responses
        
    except Exception as e:
        logger.error(f"获取成本记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取成本记录失败"
        )


@router.get("/quotas", response_model=List[CostQuotaResponse])
async def get_cost_quotas(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成本配额列表"""
    try:
        # 构建查询条件
        query = select(CostQuota).options(
            joinedload(CostQuota.user)
        ).where(CostQuota.organization_id == current_user.organization_id)
        
        # 非管理员只能查看自己的配额
        if not current_user.is_admin:
            query = query.where(
                or_(
                    CostQuota.user_id == current_user.id,
                    CostQuota.quota_type == "organization"
                )
            )
        
        query = query.order_by(desc(CostQuota.created_at))
        
        result = await db.execute(query)
        quotas = result.unique().scalars().all()
        
        # 构建响应数据
        quota_responses = []
        for quota in quotas:
            quota_data = CostQuotaResponse.from_orm(quota)
            # 添加关联信息
            if quota.user:
                quota_data.user_name = quota.user.username
            
            quota_responses.append(quota_data)
        
        return quota_responses
        
    except Exception as e:
        logger.error(f"获取成本配额失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配额列表失败"
        )


@router.post("/quotas", response_model=CostQuotaResponse)
async def create_cost_quota(
    quota_data: CostQuotaCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建成本配额"""
    try:
        # 检查权限
        require_permission(current_user, "cost.manage")
        
        # 创建配额
        cost_quota = CostQuota(
            organization_id=current_user.organization_id,
            user_id=quota_data.user_id,
            name=quota_data.name,
            description=quota_data.description,
            quota_type=quota_data.quota_type,
            total_quota=quota_data.total_quota,
            remaining_quota=quota_data.total_quota,
            period_type=quota_data.period_type,
            period_start=quota_data.period_start,
            period_end=quota_data.period_end,
            daily_limit=quota_data.daily_limit,
            hourly_limit=quota_data.hourly_limit,
            warning_threshold=quota_data.warning_threshold,
            critical_threshold=quota_data.critical_threshold,
            config=quota_data.config
        )
        
        db.add(cost_quota)
        await db.commit()
        await db.refresh(cost_quota)
        
        logger.info(f"成本配额创建成功: {cost_quota.id}")
        
        return CostQuotaResponse.from_orm(cost_quota)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建成本配额失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建配额失败"
        )


@router.post("/quotas/{quota_id}/reset")
async def reset_cost_quota(
    quota_id: str = Path(..., description="配额ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重置成本配额"""
    try:
        # 检查权限
        require_permission(current_user, "cost.manage")
        
        result = await db.execute(
            select(CostQuota)
            .where(
                CostQuota.id == quota_id,
                CostQuota.organization_id == current_user.organization_id
            )
        )
        quota = result.scalar_one_or_none()
        
        if not quota:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配额不存在"
            )
        
        # 重置配额
        quota.reset_quota()
        quota.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # 发送通知
        await notification_service.send_info_notification(
            title="配额已重置",
            message=f"配额「{quota.name}」已重置",
            target_type="user",
            target_id=str(current_user.id)
        )
        
        return {"message": "配额重置成功", "quota_id": quota_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置配额失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置配额失败"
        )


@router.get("/analytics")
async def get_cost_analytics(
    analytics_request: CostAnalyticsRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成本分析数据"""
    try:
        # 使用成本分析器生成报告
        analytics_data = await cost_analyzer.generate_analytics(
            organization_id=str(current_user.organization_id),
            user_id=str(current_user.id) if not current_user.is_admin else None,
            start_date=analytics_request.start_date,
            end_date=analytics_request.end_date,
            group_by=analytics_request.group_by,
            filters=analytics_request.filters
        )
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"获取成本分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分析数据失败"
        )


@router.get("/optimizations", response_model=List[CostOptimizationResponse])
async def get_cost_optimizations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成本优化建议"""
    try:
        # 构建查询条件
        query = select(CostOptimization).where(
            CostOptimization.organization_id == current_user.organization_id
        ).order_by(desc(CostOptimization.potential_savings))
        
        result = await db.execute(query)
        optimizations = result.scalars().all()
        
        return [CostOptimizationResponse.from_orm(opt) for opt in optimizations]
        
    except Exception as e:
        logger.error(f"获取优化建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取优化建议失败"
        )


@router.post("/optimizations/generate")
async def generate_cost_optimizations(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成成本优化建议"""
    try:
        # 检查权限
        require_permission(current_user, "cost.analyze")
        
        # 异步生成优化建议
        background_tasks.add_task(
            generate_optimization_suggestions,
            organization_id=str(current_user.organization_id)
        )
        
        return {"message": "优化建议生成任务已启动", "status": "processing"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动优化建议生成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动优化建议生成失败"
        )


@router.get("/alerts")
async def get_cost_alerts(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    level: Optional[str] = Query(None, description="告警级别筛选"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取成本告警列表"""
    try:
        # 构建查询条件
        query = select(CostAlert).where(
            CostAlert.organization_id == current_user.organization_id,
            CostAlert.is_active == True
        )
        
        # 应用筛选条件
        if level:
            query = query.where(CostAlert.level == level)
        
        if is_resolved is not None:
            query = query.where(CostAlert.is_resolved == is_resolved)
        
        # 分页和排序
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(CostAlert.created_at))
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": str(alert.id),
                "alert_type": alert.alert_type.value,
                "title": alert.title,
                "message": alert.message,
                "level": alert.level,
                "trigger_value": float(alert.trigger_value) if alert.trigger_value else None,
                "threshold_value": float(alert.threshold_value) if alert.threshold_value else None,
                "is_read": alert.is_read,
                "is_resolved": alert.is_resolved,
                "created_at": alert.created_at.isoformat()
            })
        
        return alert_data
        
    except Exception as e:
        logger.error(f"获取成本告警失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取告警列表失败"
        )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_cost_alert(
    alert_id: str = Path(..., description="告警ID"),
    resolution_note: Optional[str] = Query(None, description="解决备注"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """解决成本告警"""
    try:
        result = await db.execute(
            select(CostAlert)
            .where(
                CostAlert.id == alert_id,
                CostAlert.organization_id == current_user.organization_id
            )
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在"
            )
        
        # 解决告警
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = current_user.id
        alert.resolution_note = resolution_note
        alert.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "告警已解决", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解决告警失败"
        )


# ==================== 后台任务函数 ====================

async def generate_optimization_suggestions(organization_id: str):
    """生成优化建议（后台任务）"""
    try:
        # 使用成本分析器生成优化建议
        suggestions = await cost_analyzer.generate_optimization_suggestions(organization_id)
        
        # 存储建议到数据库
        async with get_db() as db:
            for suggestion in suggestions:
                optimization = CostOptimization(
                    organization_id=organization_id,
                    title=suggestion["title"],
                    description=suggestion["description"],
                    optimization_type=suggestion["type"],
                    current_cost=suggestion["current_cost"],
                    potential_savings=suggestion["potential_savings"],
                    savings_percentage=suggestion["savings_percentage"],
                    recommendations=suggestion["recommendations"],
                    implementation_effort=suggestion["effort"],
                    priority=suggestion["priority"]
                )
                db.add(optimization)
            
            await db.commit()
        
        logger.info(f"优化建议生成完成: {organization_id}, {len(suggestions)}条建议")
        
    except Exception as e:
        logger.error(f"生成优化建议失败: {organization_id}, {str(e)}")


async def check_quota_thresholds(organization_id: str):
    """检查配额阈值（后台任务）"""
    try:
        async with get_db() as db:
            # 获取活跃配额
            result = await db.execute(
                select(CostQuota)
                .where(
                    CostQuota.organization_id == organization_id,
                    CostQuota.is_active == True
                )
            )
            quotas = result.scalars().all()
            
            for quota in quotas:
                usage_percentage = quota.usage_percentage / 100
                
                # 检查预警阈值
                if usage_percentage >= quota.warning_threshold and not quota.is_warning:
                    await create_quota_alert(
                        quota, AlertType.QUOTA_WARNING, 
                        f"配额「{quota.name}」使用量已达到{quota.usage_percentage:.1f}%"
                    )
                
                # 检查严重阈值
                if usage_percentage >= quota.critical_threshold and not quota.is_critical:
                    await create_quota_alert(
                        quota, AlertType.QUOTA_EXCEEDED,
                        f"配额「{quota.name}」使用量已达到{quota.usage_percentage:.1f}%"
                    )
            
            await db.commit()
        
    except Exception as e:
        logger.error(f"检查配额阈值失败: {organization_id}, {str(e)}")


async def create_quota_alert(quota: CostQuota, alert_type: AlertType, message: str):
    """创建配额告警"""
    try:
        alert = CostAlert(
            organization_id=quota.organization_id,
            user_id=quota.user_id,
            quota_id=quota.id,
            alert_type=alert_type,
            title=f"配额{alert_type.value}",
            message=message,
            level="warning" if alert_type == AlertType.QUOTA_WARNING else "error",
            trigger_value=quota.used_quota,
            threshold_value=quota.total_quota
        )
        
        # 发送实时通知
        await notification_service.send_warning_notification(
            title=alert.title,
            message=alert.message,
            target_type="user" if quota.user_id else "broadcast",
            target_id=str(quota.user_id) if quota.user_id else None
        )
        
        return alert
        
    except Exception as e:
        logger.error(f"创建配额告警失败: {str(e)}")
        return None

