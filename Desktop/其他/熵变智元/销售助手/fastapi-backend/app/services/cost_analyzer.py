"""
成本分析服务
负责成本数据分析、趋势预测、优化建议等功能
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from decimal import Decimal
from collections import defaultdict
import statistics
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.cost import CostRecord, CostModel, CostQuota, CostOptimization
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class CostTrend:
    """成本趋势数据"""
    period: str
    total_cost: float
    total_requests: int
    avg_cost_per_request: float
    change_percentage: float


@dataclass
class UsagePattern:
    """使用模式数据"""
    hour: int
    requests: int
    cost: float
    efficiency_score: float


class CostAnalyzer:
    """成本分析器"""
    
    def __init__(self):
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 1800  # 30分钟缓存
    
    async def generate_analytics(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        group_by: str = "day",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成成本分析报告"""
        try:
            # 设置默认时间范围
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            filters = filters or {}
            
            # 检查缓存
            cache_key = f"analytics:{organization_id}:{user_id}:{start_date.isoformat()}:{end_date.isoformat()}:{group_by}"
            cached_result = await self._get_cached_analytics(cache_key)
            if cached_result:
                return cached_result
            
            async with get_db() as db:
                # 构建基础查询
                base_query = select(CostRecord).options(
                    joinedload(CostRecord.cost_model),
                    joinedload(CostRecord.user)
                ).where(
                    CostRecord.organization_id == organization_id,
                    CostRecord.created_at >= start_date,
                    CostRecord.created_at <= end_date
                )
                
                # 应用用户筛选
                if user_id:
                    base_query = base_query.where(CostRecord.user_id == user_id)
                
                # 应用额外筛选
                if filters.get("model_name"):
                    base_query = base_query.where(CostRecord.model_name == filters["model_name"])
                
                if filters.get("provider"):
                    base_query = base_query.where(CostRecord.provider_name == filters["provider"])
                
                # 获取原始数据
                result = await db.execute(base_query.order_by(CostRecord.created_at))
                records = result.unique().scalars().all()
                
                # 生成各种分析
                analytics = {
                    "summary": await self._generate_summary(records, start_date, end_date),
                    "trends": await self._generate_trends(records, group_by),
                    "distributions": await self._generate_distributions(records),
                    "patterns": await self._generate_usage_patterns(records),
                    "efficiency": await self._generate_efficiency_metrics(records),
                    "forecasts": await self._generate_forecasts(records),
                    "comparisons": await self._generate_comparisons(organization_id, records, start_date, end_date),
                    "metadata": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "group_by": group_by,
                        "total_records": len(records),
                        "generated_at": datetime.utcnow().isoformat()
                    }
                }
                
                # 缓存结果
                await self._cache_analytics(cache_key, analytics)
                
                return analytics
        
        except Exception as e:
            logger.error(f"生成成本分析失败: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_summary(self, records: List[CostRecord], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成摘要统计"""
        if not records:
            return {
                "total_cost": 0.0,
                "total_requests": 0,
                "total_tokens": 0,
                "avg_cost_per_request": 0.0,
                "avg_cost_per_token": 0.0,
                "period_days": (end_date - start_date).days
            }
        
        total_cost = sum(float(record.total_cost) for record in records)
        total_requests = len(records)
        total_tokens = sum(record.total_units for record in records)
        
        avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0
        avg_cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0.0
        
        return {
            "total_cost": round(total_cost, 6),
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "avg_cost_per_request": round(avg_cost_per_request, 6),
            "avg_cost_per_token": round(avg_cost_per_token, 8),
            "period_days": (end_date - start_date).days,
            "daily_avg_cost": round(total_cost / max(1, (end_date - start_date).days), 6),
            "cost_range": {
                "min": round(min(float(record.total_cost) for record in records), 6),
                "max": round(max(float(record.total_cost) for record in records), 6),
                "median": round(statistics.median([float(record.total_cost) for record in records]), 6)
            }
        }
    
    async def _generate_trends(self, records: List[CostRecord], group_by: str) -> List[Dict[str, Any]]:
        """生成趋势数据"""
        if not records:
            return []
        
        # 按时间分组
        grouped_data = defaultdict(lambda: {"cost": 0.0, "requests": 0, "tokens": 0})
        
        for record in records:
            if group_by == "hour":
                key = record.created_at.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                key = record.created_at.strftime("%Y-%m-%d")
            elif group_by == "week":
                # 获取该周的周一日期
                monday = record.created_at - timedelta(days=record.created_at.weekday())
                key = monday.strftime("%Y-%m-%d")
            elif group_by == "month":
                key = record.created_at.strftime("%Y-%m")
            else:
                key = record.created_at.strftime("%Y-%m-%d")
            
            grouped_data[key]["cost"] += float(record.total_cost)
            grouped_data[key]["requests"] += 1
            grouped_data[key]["tokens"] += record.total_units
        
        # 转换为趋势列表
        trends = []
        sorted_keys = sorted(grouped_data.keys())
        
        for i, key in enumerate(sorted_keys):
            data = grouped_data[key]
            
            # 计算变化百分比
            change_percentage = 0.0
            if i > 0:
                prev_cost = grouped_data[sorted_keys[i-1]]["cost"]
                if prev_cost > 0:
                    change_percentage = ((data["cost"] - prev_cost) / prev_cost) * 100
            
            avg_cost_per_request = data["cost"] / data["requests"] if data["requests"] > 0 else 0.0
            
            trends.append({
                "period": key,
                "total_cost": round(data["cost"], 6),
                "total_requests": data["requests"],
                "total_tokens": data["tokens"],
                "avg_cost_per_request": round(avg_cost_per_request, 6),
                "change_percentage": round(change_percentage, 2)
            })
        
        return trends
    
    async def _generate_distributions(self, records: List[CostRecord]) -> Dict[str, Any]:
        """生成分布统计"""
        if not records:
            return {}
        
        # 按用户分布
        user_distribution = defaultdict(lambda: {"cost": 0.0, "requests": 0})
        for record in records:
            user_name = record.user.username if record.user else "Unknown"
            user_distribution[user_name]["cost"] += float(record.total_cost)
            user_distribution[user_name]["requests"] += 1
        
        # 按模型分布
        model_distribution = defaultdict(lambda: {"cost": 0.0, "requests": 0})
        for record in records:
            model_name = record.model_name or "Unknown"
            model_distribution[model_name]["cost"] += float(record.total_cost)
            model_distribution[model_name]["requests"] += 1
        
        # 按提供商分布
        provider_distribution = defaultdict(lambda: {"cost": 0.0, "requests": 0})
        for record in records:
            provider_name = record.provider_name or "Unknown"
            provider_distribution[provider_name]["cost"] += float(record.total_cost)
            provider_distribution[provider_name]["requests"] += 1
        
        # 按请求类型分布
        request_type_distribution = defaultdict(lambda: {"cost": 0.0, "requests": 0})
        for record in records:
            request_type = record.request_type or "Unknown"
            request_type_distribution[request_type]["cost"] += float(record.total_cost)
            request_type_distribution[request_type]["requests"] += 1
        
        return {
            "by_user": [
                {"name": name, **data}
                for name, data in sorted(user_distribution.items(), key=lambda x: x[1]["cost"], reverse=True)
            ],
            "by_model": [
                {"name": name, **data}
                for name, data in sorted(model_distribution.items(), key=lambda x: x[1]["cost"], reverse=True)
            ],
            "by_provider": [
                {"name": name, **data}
                for name, data in sorted(provider_distribution.items(), key=lambda x: x[1]["cost"], reverse=True)
            ],
            "by_request_type": [
                {"name": name, **data}
                for name, data in sorted(request_type_distribution.items(), key=lambda x: x[1]["cost"], reverse=True)
            ]
        }
    
    async def _generate_usage_patterns(self, records: List[CostRecord]) -> Dict[str, Any]:
        """生成使用模式分析"""
        if not records:
            return {}
        
        # 按小时分布
        hourly_pattern = defaultdict(lambda: {"cost": 0.0, "requests": 0})
        for record in records:
            hour = record.created_at.hour
            hourly_pattern[hour]["cost"] += float(record.total_cost)
            hourly_pattern[hour]["requests"] += 1
        
        # 按星期分布
        weekday_pattern = defaultdict(lambda: {"cost": 0.0, "requests": 0})
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for record in records:
            weekday = weekdays[record.created_at.weekday()]
            weekday_pattern[weekday]["cost"] += float(record.total_cost)
            weekday_pattern[weekday]["requests"] += 1
        
        # 计算效率分数
        total_cost = sum(float(record.total_cost) for record in records)
        total_requests = len(records)
        avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0
        
        # 小时模式数据
        hourly_data = []
        for hour in range(24):
            data = hourly_pattern[hour]
            efficiency_score = 1.0
            if data["requests"] > 0:
                hour_avg_cost = data["cost"] / data["requests"]
                if avg_cost_per_request > 0:
                    efficiency_score = 1.0 - (hour_avg_cost / avg_cost_per_request - 1.0)
                    efficiency_score = max(0.0, min(1.0, efficiency_score))
            
            hourly_data.append({
                "hour": hour,
                "cost": round(data["cost"], 6),
                "requests": data["requests"],
                "efficiency_score": round(efficiency_score, 3)
            })
        
        # 星期模式数据
        weekday_data = []
        for weekday in weekdays:
            data = weekday_pattern[weekday]
            weekday_data.append({
                "weekday": weekday,
                "cost": round(data["cost"], 6),
                "requests": data["requests"]
            })
        
        # 识别高峰时间
        peak_hours = sorted(
            [(hour, data["requests"]) for hour, data in hourly_pattern.items()],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            "hourly": hourly_data,
            "weekday": weekday_data,
            "peak_hours": [{"hour": hour, "requests": requests} for hour, requests in peak_hours],
            "insights": {
                "most_active_hour": peak_hours[0][0] if peak_hours else None,
                "most_efficient_hour": max(hourly_data, key=lambda x: x["efficiency_score"])["hour"] if hourly_data else None,
                "weekend_usage": sum(weekday_pattern[day]["requests"] for day in ["Saturday", "Sunday"]),
                "weekday_usage": sum(weekday_pattern[day]["requests"] for day in weekdays[:5])
            }
        }
    
    async def _generate_efficiency_metrics(self, records: List[CostRecord]) -> Dict[str, Any]:
        """生成效率指标"""
        if not records:
            return {}
        
        # 成本效率分析
        costs = [float(record.total_cost) for record in records]
        tokens = [record.total_units for record in records if record.total_units > 0]
        
        # 计算各种效率指标
        cost_per_token_ratios = []
        for record in records:
            if record.total_units > 0:
                ratio = float(record.total_cost) / record.total_units
                cost_per_token_ratios.append(ratio)
        
        # 识别低效请求（成本高于平均值2倍标准差）
        if cost_per_token_ratios:
            mean_ratio = statistics.mean(cost_per_token_ratios)
            std_ratio = statistics.stdev(cost_per_token_ratios) if len(cost_per_token_ratios) > 1 else 0
            threshold = mean_ratio + 2 * std_ratio
            
            inefficient_requests = sum(1 for ratio in cost_per_token_ratios if ratio > threshold)
        else:
            mean_ratio = 0
            inefficient_requests = 0
        
        # 模型效率排名
        model_efficiency = defaultdict(lambda: {"total_cost": 0.0, "total_tokens": 0, "requests": 0})
        for record in records:
            model_name = record.model_name or "Unknown"
            model_efficiency[model_name]["total_cost"] += float(record.total_cost)
            model_efficiency[model_name]["total_tokens"] += record.total_units
            model_efficiency[model_name]["requests"] += 1
        
        model_rankings = []
        for model, data in model_efficiency.items():
            if data["total_tokens"] > 0:
                efficiency = data["total_tokens"] / data["total_cost"]
                model_rankings.append({
                    "model": model,
                    "efficiency": round(efficiency, 2),
                    "cost_per_token": round(data["total_cost"] / data["total_tokens"], 8),
                    "requests": data["requests"]
                })
        
        model_rankings.sort(key=lambda x: x["efficiency"], reverse=True)
        
        return {
            "cost_statistics": {
                "mean_cost": round(statistics.mean(costs), 6) if costs else 0,
                "median_cost": round(statistics.median(costs), 6) if costs else 0,
                "std_cost": round(statistics.stdev(costs), 6) if len(costs) > 1 else 0
            },
            "token_efficiency": {
                "mean_cost_per_token": round(mean_ratio, 8) if cost_per_token_ratios else 0,
                "inefficient_requests": inefficient_requests,
                "inefficient_percentage": round((inefficient_requests / len(records)) * 100, 2) if records else 0
            },
            "model_rankings": model_rankings[:10],  # 前10个最高效的模型
            "recommendations": self._generate_efficiency_recommendations(model_rankings, inefficient_requests, len(records))
        }
    
    def _generate_efficiency_recommendations(self, model_rankings: List[Dict], inefficient_count: int, total_requests: int) -> List[str]:
        """生成效率建议"""
        recommendations = []
        
        if inefficient_count > total_requests * 0.1:  # 超过10%的请求低效
            recommendations.append("检测到较多低效请求，建议优化Prompt或选择更适合的模型")
        
        if len(model_rankings) > 1:
            best_model = model_rankings[0]
            worst_model = model_rankings[-1]
            
            if best_model["efficiency"] > worst_model["efficiency"] * 2:
                recommendations.append(f"建议优先使用高效模型「{best_model['model']}」替代低效模型「{worst_model['model']}」")
        
        if not recommendations:
            recommendations.append("当前使用效率良好，继续保持")
        
        return recommendations
    
    async def _generate_forecasts(self, records: List[CostRecord]) -> Dict[str, Any]:
        """生成预测数据"""
        if len(records) < 7:  # 数据不足，无法预测
            return {"error": "数据不足，无法生成预测"}
        
        # 按日分组计算每日成本
        daily_costs = defaultdict(float)
        for record in records:
            date_key = record.created_at.strftime("%Y-%m-%d")
            daily_costs[date_key] += float(record.total_cost)
        
        # 获取最近7天的数据进行简单线性预测
        sorted_dates = sorted(daily_costs.keys())
        recent_costs = [daily_costs[date] for date in sorted_dates[-7:]]
        
        # 简单移动平均预测
        if len(recent_costs) >= 3:
            # 计算趋势
            trend = (recent_costs[-1] - recent_costs[0]) / len(recent_costs)
            avg_cost = statistics.mean(recent_costs)
            
            # 预测未来7天
            forecasts = []
            for i in range(1, 8):
                predicted_cost = avg_cost + (trend * i)
                predicted_cost = max(0, predicted_cost)  # 确保非负
                
                forecasts.append({
                    "date": (datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "predicted_cost": round(predicted_cost, 6),
                    "confidence": max(0.1, 1.0 - (i * 0.1))  # 置信度随时间递减
                })
            
            # 计算月度预测
            monthly_prediction = sum(f["predicted_cost"] for f in forecasts) * 4.3  # 一个月约4.3周
            
            return {
                "daily_forecasts": forecasts,
                "monthly_prediction": round(monthly_prediction, 2),
                "trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
                "trend_rate": round(trend, 6),
                "confidence_level": "medium" if len(recent_costs) >= 5 else "low"
            }
        
        return {"error": "数据不足，无法生成可靠预测"}
    
    async def _generate_comparisons(self, organization_id: str, current_records: List[CostRecord], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成对比分析"""
        try:
            # 计算上一个周期的数据进行对比
            period_days = (end_date - start_date).days
            prev_start = start_date - timedelta(days=period_days)
            prev_end = start_date
            
            async with get_db() as db:
                # 获取上一周期数据
                prev_result = await db.execute(
                    select(CostRecord)
                    .where(
                        CostRecord.organization_id == organization_id,
                        CostRecord.created_at >= prev_start,
                        CostRecord.created_at < prev_end
                    )
                )
                prev_records = prev_result.scalars().all()
            
            # 计算当前周期统计
            current_cost = sum(float(record.total_cost) for record in current_records)
            current_requests = len(current_records)
            current_tokens = sum(record.total_units for record in current_records)
            
            # 计算上一周期统计
            prev_cost = sum(float(record.total_cost) for record in prev_records)
            prev_requests = len(prev_records)
            prev_tokens = sum(record.total_units for record in prev_records)
            
            # 计算变化百分比
            cost_change = ((current_cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0
            requests_change = ((current_requests - prev_requests) / prev_requests * 100) if prev_requests > 0 else 0
            tokens_change = ((current_tokens - prev_tokens) / prev_tokens * 100) if prev_tokens > 0 else 0
            
            # 效率对比
            current_efficiency = current_tokens / current_cost if current_cost > 0 else 0
            prev_efficiency = prev_tokens / prev_cost if prev_cost > 0 else 0
            efficiency_change = ((current_efficiency - prev_efficiency) / prev_efficiency * 100) if prev_efficiency > 0 else 0
            
            return {
                "period_comparison": {
                    "current_period": {
                        "cost": round(current_cost, 6),
                        "requests": current_requests,
                        "tokens": current_tokens
                    },
                    "previous_period": {
                        "cost": round(prev_cost, 6),
                        "requests": prev_requests,
                        "tokens": prev_tokens
                    },
                    "changes": {
                        "cost_change_percentage": round(cost_change, 2),
                        "requests_change_percentage": round(requests_change, 2),
                        "tokens_change_percentage": round(tokens_change, 2),
                        "efficiency_change_percentage": round(efficiency_change, 2)
                    }
                },
                "insights": [
                    f"成本{'增长' if cost_change > 0 else '下降' if cost_change < 0 else '持平'}{abs(cost_change):.1f}%",
                    f"请求量{'增长' if requests_change > 0 else '下降' if requests_change < 0 else '持平'}{abs(requests_change):.1f}%",
                    f"使用效率{'提升' if efficiency_change > 0 else '下降' if efficiency_change < 0 else '持平'}{abs(efficiency_change):.1f}%"
                ]
            }
        
        except Exception as e:
            logger.error(f"生成对比分析失败: {str(e)}")
            return {"error": "对比分析生成失败"}
    
    async def generate_optimization_suggestions(self, organization_id: str) -> List[Dict[str, Any]]:
        """生成优化建议"""
        try:
            suggestions = []
            
            async with get_db() as db:
                # 获取最近30天的数据
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                result = await db.execute(
                    select(CostRecord)
                    .options(joinedload(CostRecord.cost_model))
                    .where(
                        CostRecord.organization_id == organization_id,
                        CostRecord.created_at >= thirty_days_ago
                    )
                )
                records = result.unique().scalars().all()
                
                if not records:
                    return suggestions
                
                # 分析模型使用效率
                model_analysis = await self._analyze_model_efficiency(records)
                suggestions.extend(model_analysis)
                
                # 分析使用模式
                pattern_analysis = await self._analyze_usage_patterns(records)
                suggestions.extend(pattern_analysis)
                
                # 分析成本异常
                anomaly_analysis = await self._analyze_cost_anomalies(records)
                suggestions.extend(anomaly_analysis)
                
                # 分析配额使用
                quota_analysis = await self._analyze_quota_usage(organization_id)
                suggestions.extend(quota_analysis)
            
            return suggestions
        
        except Exception as e:
            logger.error(f"生成优化建议失败: {str(e)}")
            return []
    
    async def _analyze_model_efficiency(self, records: List[CostRecord]) -> List[Dict[str, Any]]:
        """分析模型效率"""
        suggestions = []
        
        # 按模型分组分析
        model_stats = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "requests": 0})
        
        for record in records:
            model_name = record.model_name or "unknown"
            model_stats[model_name]["cost"] += float(record.total_cost)
            model_stats[model_name]["tokens"] += record.total_units
            model_stats[model_name]["requests"] += 1
        
        # 计算每个模型的效率
        model_efficiency = []
        for model, stats in model_stats.items():
            if stats["tokens"] > 0:
                cost_per_token = stats["cost"] / stats["tokens"]
                tokens_per_dollar = stats["tokens"] / stats["cost"] if stats["cost"] > 0 else 0
                
                model_efficiency.append({
                    "model": model,
                    "cost_per_token": cost_per_token,
                    "tokens_per_dollar": tokens_per_dollar,
                    "total_cost": stats["cost"],
                    "usage_percentage": (stats["requests"] / len(records)) * 100
                })
        
        # 排序找出最低效的模型
        model_efficiency.sort(key=lambda x: x["cost_per_token"], reverse=True)
        
        if len(model_efficiency) > 1:
            worst_model = model_efficiency[0]
            best_model = model_efficiency[-1]
            
            if worst_model["cost_per_token"] > best_model["cost_per_token"] * 2:
                potential_savings = worst_model["total_cost"] * 0.5  # 假设能节省50%
                
                suggestions.append({
                    "title": "模型效率优化",
                    "description": f"模型「{worst_model['model']}」的成本效率较低，建议替换为更高效的模型",
                    "type": "model_optimization",
                    "current_cost": worst_model["total_cost"],
                    "potential_savings": potential_savings,
                    "savings_percentage": 50.0,
                    "recommendations": [
                        f"考虑将「{worst_model['model']}」替换为「{best_model['model']}」",
                        "优化Prompt以减少Token使用量",
                        "评估是否可以使用更小的模型完成相同任务"
                    ],
                    "effort": "medium",
                    "priority": "high" if potential_savings > 100 else "medium"
                })
        
        return suggestions
    
    async def _analyze_usage_patterns(self, records: List[CostRecord]) -> List[Dict[str, Any]]:
        """分析使用模式"""
        suggestions = []
        
        # 分析高峰时间使用
        hourly_usage = defaultdict(lambda: {"cost": 0.0, "requests": 0})
        for record in records:
            hour = record.created_at.hour
            hourly_usage[hour]["cost"] += float(record.total_cost)
            hourly_usage[hour]["requests"] += 1
        
        # 找出高峰时间
        peak_hours = sorted(hourly_usage.items(), key=lambda x: x[1]["cost"], reverse=True)[:3]
        total_cost = sum(float(record.total_cost) for record in records)
        
        peak_cost_percentage = sum(hour_data["cost"] for _, hour_data in peak_hours) / total_cost * 100
        
        if peak_cost_percentage > 60:  # 如果60%的成本集中在3小时内
            suggestions.append({
                "title": "使用时间优化",
                "description": "成本主要集中在高峰时段，建议优化使用时间分布",
                "type": "timing_optimization",
                "current_cost": total_cost,
                "potential_savings": total_cost * 0.15,  # 假设能节省15%
                "savings_percentage": 15.0,
                "recommendations": [
                    "将非紧急任务调度到低峰时段",
                    "实施请求缓存减少重复调用",
                    "考虑批量处理以提高效率"
                ],
                "effort": "low",
                "priority": "medium"
            })
        
        return suggestions
    
    async def _analyze_cost_anomalies(self, records: List[CostRecord]) -> List[Dict[str, Any]]:
        """分析成本异常"""
        suggestions = []
        
        costs = [float(record.total_cost) for record in records]
        
        if len(costs) > 10:
            mean_cost = statistics.mean(costs)
            std_cost = statistics.stdev(costs)
            
            # 识别异常高成本请求
            threshold = mean_cost + 3 * std_cost
            anomalies = [cost for cost in costs if cost > threshold]
            
            if len(anomalies) > len(costs) * 0.05:  # 超过5%的请求异常
                total_anomaly_cost = sum(anomalies)
                
                suggestions.append({
                    "title": "异常成本控制",
                    "description": f"检测到{len(anomalies)}个异常高成本请求，建议加强成本控制",
                    "type": "anomaly_control",
                    "current_cost": total_anomaly_cost,
                    "potential_savings": total_anomaly_cost * 0.8,  # 假设能减少80%的异常成本
                    "savings_percentage": 80.0,
                    "recommendations": [
                        "设置更严格的成本阈值告警",
                        "实施请求前成本预估",
                        "优化高成本场景的处理逻辑",
                        "考虑对异常请求进行人工审核"
                    ],
                    "effort": "medium",
                    "priority": "high"
                })
        
        return suggestions
    
    async def _analyze_quota_usage(self, organization_id: str) -> List[Dict[str, Any]]:
        """分析配额使用"""
        suggestions = []
        
        try:
            async with get_db() as db:
                result = await db.execute(
                    select(CostQuota)
                    .where(
                        CostQuota.organization_id == organization_id,
                        CostQuota.is_active == True
                    )
                )
                quotas = result.scalars().all()
                
                for quota in quotas:
                    usage_percentage = quota.usage_percentage
                    
                    if usage_percentage > 90:
                        suggestions.append({
                            "title": "配额调整建议",
                            "description": f"配额「{quota.name}」使用率过高({usage_percentage:.1f}%)，建议调整",
                            "type": "quota_adjustment",
                            "current_cost": float(quota.used_quota),
                            "potential_savings": 0,  # 配额调整不直接节省成本
                            "savings_percentage": 0.0,
                            "recommendations": [
                                "增加配额限制以避免服务中断",
                                "分析配额使用模式优化分配",
                                "考虑实施更细粒度的配额控制"
                            ],
                            "effort": "low",
                            "priority": "high" if usage_percentage > 95 else "medium"
                        })
        
        except Exception as e:
            logger.error(f"分析配额使用失败: {str(e)}")
        
        return suggestions
    
    async def _get_cached_analytics(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的分析结果"""
        try:
            cached_data = await redis_client.get(f"analytics_cache:{cache_key}")
            if cached_data:
                return json.loads(cached_data.decode())
        except Exception as e:
            logger.error(f"获取缓存分析结果失败: {str(e)}")
        
        return None
    
    async def _cache_analytics(self, cache_key: str, analytics: Dict[str, Any]):
        """缓存分析结果"""
        try:
            await redis_client.setex(
                f"analytics_cache:{cache_key}",
                self.cache_ttl,
                json.dumps(analytics, default=str)
            )
        except Exception as e:
            logger.error(f"缓存分析结果失败: {str(e)}")


# 全局成本分析器实例
cost_analyzer = CostAnalyzer()

