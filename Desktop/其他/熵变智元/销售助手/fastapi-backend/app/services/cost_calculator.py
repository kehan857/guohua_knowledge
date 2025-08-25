"""
成本计算服务
负责实时成本计算、配额检查、使用量统计等功能
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.redis import redis_client
from app.core.config import settings
from app.models.cost import (
    CostModel, CostRecord, CostQuota, CostAlert,
    CostType, BillingUnit, AlertType
)
from app.models.user import User
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


@dataclass
class CostCalculationRequest:
    """成本计算请求"""
    organization_id: str
    user_id: str
    model_name: str
    provider: str
    request_type: str
    input_units: int = 0
    output_units: int = 0
    base_units: int = 0
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    wechat_account_id: Optional[str] = None
    sop_instance_id: Optional[str] = None


@dataclass
class CostCalculationResult:
    """成本计算结果"""
    success: bool
    total_cost: Decimal
    input_cost: Decimal
    output_cost: Decimal
    base_cost: Decimal
    total_units: int
    quota_exceeded: bool
    warnings: List[str]
    cost_record_id: Optional[str] = None
    error_message: Optional[str] = None


class CostCalculator:
    """成本计算器"""
    
    def __init__(self):
        # 模型缓存，减少数据库查询
        self.model_cache: Dict[str, CostModel] = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 配额缓存
        self.quota_cache: Dict[str, CostQuota] = {}
        
        # 统计缓存
        self.stats_cache: Dict[str, Dict[str, Any]] = {}
        
        # 实时使用量追踪
        self.usage_tracker: Dict[str, Dict[str, int]] = {}
    
    async def calculate_cost(self, request: CostCalculationRequest) -> CostCalculationResult:
        """计算成本"""
        try:
            # 1. 获取成本模型
            cost_model = await self._get_cost_model(
                request.organization_id, 
                request.model_name, 
                request.provider
            )
            
            if not cost_model:
                return CostCalculationResult(
                    success=False,
                    total_cost=Decimal('0.00'),
                    input_cost=Decimal('0.00'),
                    output_cost=Decimal('0.00'),
                    base_cost=Decimal('0.00'),
                    total_units=0,
                    quota_exceeded=False,
                    warnings=[],
                    error_message=f"成本模型不存在: {request.model_name}"
                )
            
            # 2. 计算成本
            input_cost = self._calculate_unit_cost(
                cost_model.input_price, request.input_units, cost_model.unit_size
            )
            
            output_cost = self._calculate_unit_cost(
                cost_model.output_price, request.output_units, cost_model.unit_size
            )
            
            base_cost = self._calculate_unit_cost(
                cost_model.base_price, request.base_units, cost_model.unit_size
            )
            
            total_cost = input_cost + output_cost + base_cost
            total_units = request.input_units + request.output_units + request.base_units
            
            # 3. 检查配额
            quota_check_result = await self._check_quotas(
                request.organization_id, 
                request.user_id, 
                total_cost
            )
            
            if quota_check_result["exceeded"]:
                return CostCalculationResult(
                    success=False,
                    total_cost=total_cost,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    base_cost=base_cost,
                    total_units=total_units,
                    quota_exceeded=True,
                    warnings=quota_check_result["warnings"],
                    error_message="超出配额限制"
                )
            
            # 4. 记录成本
            cost_record = await self._create_cost_record(
                request, cost_model, 
                input_cost, output_cost, base_cost, total_cost, total_units
            )
            
            # 5. 更新配额使用量
            await self._update_quota_usage(
                request.organization_id, 
                request.user_id, 
                total_cost
            )
            
            # 6. 更新实时统计
            await self._update_real_time_stats(request, total_cost, total_units)
            
            # 7. 检查告警条件
            await self._check_alert_conditions(
                request.organization_id, 
                request.user_id, 
                total_cost
            )
            
            return CostCalculationResult(
                success=True,
                total_cost=total_cost,
                input_cost=input_cost,
                output_cost=output_cost,
                base_cost=base_cost,
                total_units=total_units,
                quota_exceeded=False,
                warnings=quota_check_result["warnings"],
                cost_record_id=str(cost_record.id) if cost_record else None
            )
            
        except Exception as e:
            logger.error(f"成本计算失败: {str(e)}")
            return CostCalculationResult(
                success=False,
                total_cost=Decimal('0.00'),
                input_cost=Decimal('0.00'),
                output_cost=Decimal('0.00'),
                base_cost=Decimal('0.00'),
                total_units=0,
                quota_exceeded=False,
                warnings=[],
                error_message=str(e)
            )
    
    def _calculate_unit_cost(self, price: Optional[Decimal], units: int, unit_size: int) -> Decimal:
        """计算单位成本"""
        if not price or units == 0:
            return Decimal('0.00')
        
        # 计算成本：(单位数 / 计费单位大小) * 单价
        cost = (Decimal(str(units)) / Decimal(str(unit_size))) * price
        return cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    async def _get_cost_model(self, organization_id: str, model_name: str, provider: str) -> Optional[CostModel]:
        """获取成本模型"""
        try:
            # 先从缓存获取
            cache_key = f"{organization_id}:{model_name}:{provider}"
            
            if cache_key in self.model_cache:
                cached_model = self.model_cache[cache_key]
                # 检查缓存是否过期
                if (datetime.utcnow() - cached_model.updated_at).total_seconds() < self.cache_ttl:
                    return cached_model
            
            # 从数据库获取
            async with get_db() as db:
                result = await db.execute(
                    select(CostModel)
                    .where(
                        CostModel.organization_id == organization_id,
                        CostModel.model_type == model_name,
                        CostModel.provider == provider,
                        CostModel.is_active == True
                    )
                )
                cost_model = result.scalar_one_or_none()
                
                if cost_model:
                    # 更新缓存
                    self.model_cache[cache_key] = cost_model
                
                return cost_model
        
        except Exception as e:
            logger.error(f"获取成本模型失败: {str(e)}")
            return None
    
    async def _check_quotas(self, organization_id: str, user_id: str, cost: Decimal) -> Dict[str, Any]:
        """检查配额"""
        try:
            warnings = []
            exceeded = False
            
            async with get_db() as db:
                # 获取用户配额
                user_quota_result = await db.execute(
                    select(CostQuota)
                    .where(
                        CostQuota.organization_id == organization_id,
                        CostQuota.user_id == user_id,
                        CostQuota.is_active == True,
                        CostQuota.period_start <= datetime.utcnow(),
                        CostQuota.period_end >= datetime.utcnow()
                    )
                )
                user_quotas = user_quota_result.scalars().all()
                
                # 获取组织配额
                org_quota_result = await db.execute(
                    select(CostQuota)
                    .where(
                        CostQuota.organization_id == organization_id,
                        CostQuota.quota_type == "organization",
                        CostQuota.is_active == True,
                        CostQuota.period_start <= datetime.utcnow(),
                        CostQuota.period_end >= datetime.utcnow()
                    )
                )
                org_quotas = org_quota_result.scalars().all()
                
                # 检查所有配额
                all_quotas = list(user_quotas) + list(org_quotas)
                
                for quota in all_quotas:
                    new_used = quota.used_quota + cost
                    
                    # 检查是否超出配额
                    if new_used > quota.total_quota:
                        exceeded = True
                        warnings.append(f"配额「{quota.name}」将超出限制")
                        continue
                    
                    # 检查预警阈值
                    usage_percentage = float(new_used / quota.total_quota)
                    
                    if usage_percentage >= quota.warning_threshold:
                        warnings.append(f"配额「{quota.name}」使用量将达到{usage_percentage*100:.1f}%")
                    
                    # 检查小时限制
                    if quota.hourly_limit:
                        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                        hourly_usage = await self._get_hourly_usage(quota.id, current_hour)
                        
                        if hourly_usage + cost > quota.hourly_limit:
                            exceeded = True
                            warnings.append(f"配额「{quota.name}」小时限额将超出")
                            continue
                    
                    # 检查日限制
                    if quota.daily_limit:
                        current_day = datetime.utcnow().date()
                        daily_usage = await self._get_daily_usage(quota.id, current_day)
                        
                        if daily_usage + cost > quota.daily_limit:
                            exceeded = True
                            warnings.append(f"配额「{quota.name}」日限额将超出")
                            continue
            
            return {
                "exceeded": exceeded,
                "warnings": warnings
            }
        
        except Exception as e:
            logger.error(f"检查配额失败: {str(e)}")
            return {"exceeded": False, "warnings": []}
    
    async def _get_hourly_usage(self, quota_id: str, hour: datetime) -> Decimal:
        """获取小时使用量"""
        try:
            # 从Redis缓存获取
            cache_key = f"hourly_usage:{quota_id}:{hour.isoformat()}"
            cached_usage = await redis_client.get(cache_key)
            
            if cached_usage:
                return Decimal(cached_usage.decode())
            
            # 从数据库计算
            async with get_db() as db:
                result = await db.execute(
                    select(func.coalesce(func.sum(CostRecord.total_cost), 0))
                    .join(CostQuota, CostRecord.user_id == CostQuota.user_id)
                    .where(
                        CostQuota.id == quota_id,
                        CostRecord.created_at >= hour,
                        CostRecord.created_at < hour + timedelta(hours=1)
                    )
                )
                usage = result.scalar() or Decimal('0.00')
                
                # 缓存结果（1小时过期）
                await redis_client.setex(cache_key, 3600, str(usage))
                
                return usage
        
        except Exception as e:
            logger.error(f"获取小时使用量失败: {str(e)}")
            return Decimal('0.00')
    
    async def _get_daily_usage(self, quota_id: str, date: datetime.date) -> Decimal:
        """获取日使用量"""
        try:
            # 从Redis缓存获取
            cache_key = f"daily_usage:{quota_id}:{date.isoformat()}"
            cached_usage = await redis_client.get(cache_key)
            
            if cached_usage:
                return Decimal(cached_usage.decode())
            
            # 从数据库计算
            async with get_db() as db:
                result = await db.execute(
                    select(func.coalesce(func.sum(CostRecord.total_cost), 0))
                    .join(CostQuota, CostRecord.user_id == CostQuota.user_id)
                    .where(
                        CostQuota.id == quota_id,
                        func.date(CostRecord.created_at) == date
                    )
                )
                usage = result.scalar() or Decimal('0.00')
                
                # 缓存结果（24小时过期）
                await redis_client.setex(cache_key, 86400, str(usage))
                
                return usage
        
        except Exception as e:
            logger.error(f"获取日使用量失败: {str(e)}")
            return Decimal('0.00')
    
    async def _create_cost_record(
        self,
        request: CostCalculationRequest,
        cost_model: CostModel,
        input_cost: Decimal,
        output_cost: Decimal,
        base_cost: Decimal,
        total_cost: Decimal,
        total_units: int
    ) -> Optional[CostRecord]:
        """创建成本记录"""
        try:
            async with get_db() as db:
                cost_record = CostRecord(
                    organization_id=request.organization_id,
                    user_id=request.user_id,
                    cost_model_id=cost_model.id,
                    wechat_account_id=request.wechat_account_id,
                    session_id=request.session_id,
                    sop_instance_id=request.sop_instance_id,
                    request_id=request.request_id,
                    request_type=request.request_type,
                    request_data=request.metadata or {},
                    input_units=request.input_units,
                    output_units=request.output_units,
                    base_units=request.base_units,
                    total_units=total_units,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    base_cost=base_cost,
                    total_cost=total_cost,
                    model_name=request.model_name,
                    provider_name=request.provider,
                    metadata=request.metadata or {}
                )
                
                db.add(cost_record)
                await db.commit()
                await db.refresh(cost_record)
                
                return cost_record
        
        except Exception as e:
            logger.error(f"创建成本记录失败: {str(e)}")
            return None
    
    async def _update_quota_usage(self, organization_id: str, user_id: str, cost: Decimal):
        """更新配额使用量"""
        try:
            async with get_db() as db:
                # 更新用户配额
                await db.execute(
                    update(CostQuota)
                    .where(
                        CostQuota.organization_id == organization_id,
                        CostQuota.user_id == user_id,
                        CostQuota.is_active == True,
                        CostQuota.period_start <= datetime.utcnow(),
                        CostQuota.period_end >= datetime.utcnow()
                    )
                    .values(
                        used_quota=CostQuota.used_quota + cost,
                        remaining_quota=CostQuota.total_quota - CostQuota.used_quota - cost,
                        updated_at=datetime.utcnow()
                    )
                )
                
                # 更新组织配额
                await db.execute(
                    update(CostQuota)
                    .where(
                        CostQuota.organization_id == organization_id,
                        CostQuota.quota_type == "organization",
                        CostQuota.is_active == True,
                        CostQuota.period_start <= datetime.utcnow(),
                        CostQuota.period_end >= datetime.utcnow()
                    )
                    .values(
                        used_quota=CostQuota.used_quota + cost,
                        remaining_quota=CostQuota.total_quota - CostQuota.used_quota - cost,
                        updated_at=datetime.utcnow()
                    )
                )
                
                await db.commit()
        
        except Exception as e:
            logger.error(f"更新配额使用量失败: {str(e)}")
    
    async def _update_real_time_stats(self, request: CostCalculationRequest, cost: Decimal, units: int):
        """更新实时统计"""
        try:
            # 更新Redis中的实时统计
            today_key = f"cost_stats:daily:{request.organization_id}:{datetime.utcnow().date().isoformat()}"
            hour_key = f"cost_stats:hourly:{request.organization_id}:{datetime.utcnow().strftime('%Y-%m-%d:%H')}"
            user_key = f"cost_stats:user:{request.user_id}:{datetime.utcnow().date().isoformat()}"
            
            # 使用Redis pipeline提高性能
            async with redis_client.pipeline() as pipe:
                # 今日统计
                pipe.hincrbyfloat(today_key, "total_cost", float(cost))
                pipe.hincrby(today_key, "total_requests", 1)
                pipe.hincrby(today_key, "total_units", units)
                pipe.expire(today_key, 86400 * 7)  # 7天过期
                
                # 小时统计
                pipe.hincrbyfloat(hour_key, "total_cost", float(cost))
                pipe.hincrby(hour_key, "total_requests", 1)
                pipe.hincrby(hour_key, "total_units", units)
                pipe.expire(hour_key, 86400)  # 1天过期
                
                # 用户统计
                pipe.hincrbyfloat(user_key, "total_cost", float(cost))
                pipe.hincrby(user_key, "total_requests", 1)
                pipe.hincrby(user_key, "total_units", units)
                pipe.expire(user_key, 86400 * 7)  # 7天过期
                
                await pipe.execute()
            
            # 更新内存中的实时统计
            if request.organization_id not in self.usage_tracker:
                self.usage_tracker[request.organization_id] = {
                    "requests": 0,
                    "cost": 0.0,
                    "units": 0
                }
            
            self.usage_tracker[request.organization_id]["requests"] += 1
            self.usage_tracker[request.organization_id]["cost"] += float(cost)
            self.usage_tracker[request.organization_id]["units"] += units
        
        except Exception as e:
            logger.error(f"更新实时统计失败: {str(e)}")
    
    async def _check_alert_conditions(self, organization_id: str, user_id: str, cost: Decimal):
        """检查告警条件"""
        try:
            async with get_db() as db:
                # 获取相关配额
                result = await db.execute(
                    select(CostQuota)
                    .where(
                        CostQuota.organization_id == organization_id,
                        or_(
                            CostQuota.user_id == user_id,
                            CostQuota.quota_type == "organization"
                        ),
                        CostQuota.is_active == True,
                        CostQuota.period_start <= datetime.utcnow(),
                        CostQuota.period_end >= datetime.utcnow()
                    )
                )
                quotas = result.scalars().all()
                
                for quota in quotas:
                    usage_percentage = float(quota.used_quota / quota.total_quota)
                    
                    # 检查预警阈值
                    if usage_percentage >= quota.warning_threshold and usage_percentage < quota.critical_threshold:
                        await self._create_quota_alert(quota, AlertType.QUOTA_WARNING)
                    
                    # 检查严重阈值
                    elif usage_percentage >= quota.critical_threshold:
                        await self._create_quota_alert(quota, AlertType.QUOTA_EXCEEDED)
                    
                    # 检查超出配额
                    if quota.used_quota > quota.total_quota and not quota.is_exceeded:
                        quota.is_exceeded = True
                        await self._create_quota_alert(quota, AlertType.QUOTA_EXCEEDED)
                
                await db.commit()
        
        except Exception as e:
            logger.error(f"检查告警条件失败: {str(e)}")
    
    async def _create_quota_alert(self, quota: CostQuota, alert_type: AlertType):
        """创建配额告警"""
        try:
            # 检查是否已存在相同告警
            async with get_db() as db:
                existing_alert_result = await db.execute(
                    select(CostAlert)
                    .where(
                        CostAlert.quota_id == quota.id,
                        CostAlert.alert_type == alert_type,
                        CostAlert.is_active == True,
                        CostAlert.is_resolved == False,
                        CostAlert.created_at >= datetime.utcnow() - timedelta(hours=1)  # 1小时内
                    )
                )
                existing_alert = existing_alert_result.scalar_one_or_none()
                
                if existing_alert:
                    return  # 避免重复告警
                
                # 创建新告警
                level = "warning" if alert_type == AlertType.QUOTA_WARNING else "error"
                message = f"配额「{quota.name}」使用量已达到{quota.usage_percentage:.1f}%"
                
                alert = CostAlert(
                    organization_id=quota.organization_id,
                    user_id=quota.user_id,
                    quota_id=quota.id,
                    alert_type=alert_type,
                    title=f"配额{alert_type.value}",
                    message=message,
                    level=level,
                    trigger_value=quota.used_quota,
                    threshold_value=quota.total_quota,
                    trigger_condition={
                        "quota_id": str(quota.id),
                        "usage_percentage": quota.usage_percentage,
                        "threshold": quota.warning_threshold if alert_type == AlertType.QUOTA_WARNING else quota.critical_threshold
                    }
                )
                
                db.add(alert)
                await db.commit()
                
                # 发送实时通知
                await notification_service.send_cost_warning_notification(
                    user_id=str(quota.user_id) if quota.user_id else None,
                    current_usage=float(quota.used_quota),
                    quota_limit=float(quota.total_quota),
                    usage_percentage=quota.usage_percentage
                )
                
                # WebSocket推送
                await websocket_manager.send_to_user(str(quota.user_id) if quota.user_id else None, {
                    "type": "cost_alert",
                    "alert": {
                        "id": str(alert.id),
                        "type": alert_type.value,
                        "title": alert.title,
                        "message": alert.message,
                        "level": level
                    }
                })
        
        except Exception as e:
            logger.error(f"创建配额告警失败: {str(e)}")
    
    async def get_real_time_stats(self, organization_id: str) -> Dict[str, Any]:
        """获取实时统计"""
        try:
            today = datetime.utcnow().date().isoformat()
            current_hour = datetime.utcnow().strftime('%Y-%m-%d:%H')
            
            # 从Redis获取统计数据
            today_key = f"cost_stats:daily:{organization_id}:{today}"
            hour_key = f"cost_stats:hourly:{organization_id}:{current_hour}"
            
            today_stats = await redis_client.hgetall(today_key)
            hour_stats = await redis_client.hgetall(hour_key)
            
            # 处理数据
            today_data = {
                "total_cost": float(today_stats.get(b"total_cost", b"0").decode()),
                "total_requests": int(today_stats.get(b"total_requests", b"0").decode()),
                "total_units": int(today_stats.get(b"total_units", b"0").decode())
            }
            
            hour_data = {
                "total_cost": float(hour_stats.get(b"total_cost", b"0").decode()),
                "total_requests": int(hour_stats.get(b"total_requests", b"0").decode()),
                "total_units": int(hour_stats.get(b"total_units", b"0").decode())
            }
            
            # 计算平均值
            avg_cost_per_request = 0.0
            avg_cost_per_unit = 0.0
            
            if today_data["total_requests"] > 0:
                avg_cost_per_request = today_data["total_cost"] / today_data["total_requests"]
            
            if today_data["total_units"] > 0:
                avg_cost_per_unit = today_data["total_cost"] / today_data["total_units"]
            
            return {
                "today": today_data,
                "current_hour": hour_data,
                "averages": {
                    "cost_per_request": avg_cost_per_request,
                    "cost_per_unit": avg_cost_per_unit
                },
                "memory_stats": self.usage_tracker.get(organization_id, {
                    "requests": 0,
                    "cost": 0.0,
                    "units": 0
                })
            }
        
        except Exception as e:
            logger.error(f"获取实时统计失败: {str(e)}")
            return {}
    
    async def estimate_cost(
        self, 
        organization_id: str, 
        model_name: str, 
        provider: str,
        input_units: int = 0,
        output_units: int = 0,
        base_units: int = 0
    ) -> Dict[str, Any]:
        """预估成本"""
        try:
            cost_model = await self._get_cost_model(organization_id, model_name, provider)
            
            if not cost_model:
                return {
                    "success": False,
                    "error": f"成本模型不存在: {model_name}"
                }
            
            # 计算预估成本
            input_cost = self._calculate_unit_cost(
                cost_model.input_price, input_units, cost_model.unit_size
            )
            
            output_cost = self._calculate_unit_cost(
                cost_model.output_price, output_units, cost_model.unit_size
            )
            
            base_cost = self._calculate_unit_cost(
                cost_model.base_price, base_units, cost_model.unit_size
            )
            
            total_cost = input_cost + output_cost + base_cost
            total_units = input_units + output_units + base_units
            
            return {
                "success": True,
                "model_name": model_name,
                "provider": provider,
                "costs": {
                    "input_cost": float(input_cost),
                    "output_cost": float(output_cost),
                    "base_cost": float(base_cost),
                    "total_cost": float(total_cost)
                },
                "units": {
                    "input_units": input_units,
                    "output_units": output_units,
                    "base_units": base_units,
                    "total_units": total_units
                },
                "pricing": {
                    "input_price": float(cost_model.input_price) if cost_model.input_price else 0,
                    "output_price": float(cost_model.output_price) if cost_model.output_price else 0,
                    "base_price": float(cost_model.base_price) if cost_model.base_price else 0,
                    "unit_size": cost_model.unit_size
                }
            }
        
        except Exception as e:
            logger.error(f"预估成本失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clear_cache(self):
        """清空缓存"""
        self.model_cache.clear()
        self.quota_cache.clear()
        self.stats_cache.clear()
        logger.info("成本计算器缓存已清空")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "model_cache_size": len(self.model_cache),
            "quota_cache_size": len(self.quota_cache),
            "stats_cache_size": len(self.stats_cache),
            "usage_tracker_size": len(self.usage_tracker)
        }


# 全局成本计算器实例
cost_calculator = CostCalculator()

