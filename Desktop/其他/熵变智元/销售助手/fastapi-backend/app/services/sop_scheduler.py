"""
SOP调度服务
负责定时任务调度、条件触发、批量执行等功能
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from croniter import croniter
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.redis import redis_client
from app.core.config import settings
from app.models.sop import (
    SOPTemplate, SOPInstance, SOPSchedule, SOPTask,
    SOPStatus, TaskStatus, SOPType, TriggerType
)
from app.models.device import WeChatAccount, DeviceStatus
from app.models.chat import Contact, ChatMessage, MessageType
from app.services.sop_executor import sop_executor
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class SOPScheduler:
    """SOP调度器"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.trigger_handlers: Dict[str, callable] = {
            "new_friend": self._handle_new_friend_trigger,
            "message_received": self._handle_message_received_trigger,
            "contact_added": self._handle_contact_added_trigger,
            "keyword_matched": self._handle_keyword_matched_trigger,
            "time_based": self._handle_time_based_trigger,
            "manual": self._handle_manual_trigger
        }
        
        # 调度间隔设置
        self.schedule_interval = 60  # 60秒检查一次
        self.max_concurrent_executions = 50  # 最大并发执行数
        
        # 统计信息
        self.stats = {
            "total_scheduled": 0,
            "total_executed": 0,
            "total_failed": 0,
            "active_schedules": 0
        }
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("SOP调度器已在运行")
            return
        
        self.is_running = True
        logger.info("启动SOP调度器")
        
        # 启动调度任务
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """停止调度器"""
        self.is_running = False
        logger.info("停止SOP调度器")
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                # 执行调度检查
                await self._check_scheduled_tasks()
                await self._check_trigger_conditions()
                await self._check_delayed_instances()
                await self._cleanup_expired_tasks()
                
                # 更新统计信息
                await self._update_stats()
                
                # 等待下次检查
                await asyncio.sleep(self.schedule_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环异常: {str(e)}")
                await asyncio.sleep(10)  # 异常时等待10秒
    
    async def _check_scheduled_tasks(self):
        """检查定时调度任务"""
        try:
            async with get_db() as db:
                # 获取活跃的调度配置
                result = await db.execute(
                    select(SOPSchedule)
                    .options(joinedload(SOPSchedule.template))
                    .where(
                        SOPSchedule.is_active == True,
                        or_(
                            SOPSchedule.next_execution_at.is_(None),
                            SOPSchedule.next_execution_at <= datetime.utcnow()
                        )
                    )
                )
                schedules = result.unique().scalars().all()
                
                for schedule in schedules:
                    await self._process_schedule(schedule, db)
                
        except Exception as e:
            logger.error(f"检查定时任务失败: {str(e)}")
    
    async def _process_schedule(self, schedule: SOPSchedule, db: AsyncSession):
        """处理单个调度任务"""
        try:
            # 检查模板是否可用
            if not schedule.template or schedule.template.status != SOPStatus.ACTIVE:
                logger.warning(f"调度模板不可用: {schedule.template_id}")
                return
            
            # 计算下次执行时间
            next_execution = self._calculate_next_execution(schedule)
            
            # 获取目标联系人
            targets = await self._get_schedule_targets(schedule, db)
            
            if not targets:
                logger.info(f"调度任务无目标: {schedule.name}")
                # 更新下次执行时间
                schedule.next_execution_at = next_execution
                await db.commit()
                return
            
            # 批量创建实例
            created_count = 0
            for target in targets:
                try:
                    # 检查是否已有活跃实例
                    existing_result = await db.execute(
                        select(SOPInstance)
                        .where(
                            SOPInstance.template_id == schedule.template_id,
                            SOPInstance.contact_id == target["contact_id"],
                            SOPInstance.status.in_([TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.EXECUTING])
                        )
                    )
                    existing_instance = existing_result.scalar_one_or_none()
                    
                    if existing_instance:
                        continue  # 跳过已有活跃实例的联系人
                    
                    # 创建新实例
                    instance = SOPInstance(
                        template_id=schedule.template.id,
                        organization_id=schedule.organization_id,
                        wechat_account_id=target["wechat_account_id"],
                        contact_id=target["contact_id"],
                        instance_name=f"{schedule.name} - {target['contact_name']}",
                        variables={"triggered_by": "schedule", "schedule_id": str(schedule.id)},
                        current_step_id=schedule.template.steps[0]["id"] if schedule.template.steps else None,
                        current_step_index=0
                    )
                    
                    db.add(instance)
                    created_count += 1
                    
                    # 启动执行
                    asyncio.create_task(
                        sop_executor.execute_instance(str(instance.id))
                    )
                    
                except Exception as e:
                    logger.error(f"创建调度实例失败: {str(e)}")
            
            # 更新调度统计
            schedule.execution_count += 1
            if created_count > 0:
                schedule.success_count += 1
            schedule.last_execution_at = datetime.utcnow()
            schedule.next_execution_at = next_execution
            
            # 更新模板统计
            schedule.template.total_instances += created_count
            schedule.template.active_instances += created_count
            
            await db.commit()
            
            self.stats["total_scheduled"] += created_count
            
            logger.info(f"调度任务执行完成: {schedule.name}, 创建实例: {created_count}")
            
        except Exception as e:
            logger.error(f"处理调度任务失败: {schedule.name}, {str(e)}")
    
    def _calculate_next_execution(self, schedule: SOPSchedule) -> Optional[datetime]:
        """计算下次执行时间"""
        try:
            if not schedule.cron_expression:
                return None
            
            cron = croniter(schedule.cron_expression, datetime.utcnow())
            return cron.get_next(datetime)
            
        except Exception as e:
            logger.error(f"计算下次执行时间失败: {schedule.cron_expression}, {str(e)}")
            return None
    
    async def _get_schedule_targets(self, schedule: SOPSchedule, db: AsyncSession) -> List[Dict[str, Any]]:
        """获取调度目标"""
        try:
            target_filter = schedule.target_filter or {}
            
            # 构建联系人查询
            query = select(Contact, WeChatAccount).join(
                WeChatAccount, Contact.wechat_account_id == WeChatAccount.id
            ).where(
                Contact.organization_id == schedule.organization_id,
                WeChatAccount.status == DeviceStatus.ONLINE,
                WeChatAccount.is_active == True
            )
            
            # 应用筛选条件
            if "tags" in target_filter:
                tags = target_filter["tags"]
                for tag in tags:
                    query = query.where(Contact.tags.contains([tag]))
            
            if "contact_type" in target_filter:
                query = query.where(Contact.contact_type == target_filter["contact_type"])
            
            if "wechat_accounts" in target_filter:
                account_ids = target_filter["wechat_accounts"]
                query = query.where(WeChatAccount.id.in_(account_ids))
            
            # 限制数量
            limit = target_filter.get("limit", 100)
            query = query.limit(limit)
            
            result = await db.execute(query)
            rows = result.all()
            
            targets = []
            for contact, account in rows:
                targets.append({
                    "contact_id": str(contact.id),
                    "contact_name": contact.display_name,
                    "wechat_account_id": str(account.id),
                    "account_nickname": account.nickname
                })
            
            return targets
            
        except Exception as e:
            logger.error(f"获取调度目标失败: {str(e)}")
            return []
    
    async def _check_trigger_conditions(self):
        """检查触发条件"""
        try:
            # 从Redis获取触发事件
            trigger_events = await redis_client.lrange("sop_trigger_events", 0, -1)
            
            for event_data in trigger_events:
                try:
                    event = json.loads(event_data.decode())
                    await self._process_trigger_event(event)
                except Exception as e:
                    logger.error(f"处理触发事件失败: {str(e)}")
            
            # 清空已处理的事件
            if trigger_events:
                await redis_client.delete("sop_trigger_events")
                
        except Exception as e:
            logger.error(f"检查触发条件失败: {str(e)}")
    
    async def _process_trigger_event(self, event: Dict[str, Any]):
        """处理触发事件"""
        try:
            event_type = event.get("type")
            handler = self.trigger_handlers.get(event_type)
            
            if handler:
                await handler(event)
            else:
                logger.warning(f"未知触发事件类型: {event_type}")
                
        except Exception as e:
            logger.error(f"处理触发事件失败: {str(e)}")
    
    async def _handle_new_friend_trigger(self, event: Dict[str, Any]):
        """处理新好友触发"""
        try:
            contact_id = event.get("contact_id")
            wechat_account_id = event.get("wechat_account_id")
            
            if not contact_id or not wechat_account_id:
                return
            
            async with get_db() as db:
                # 查找新好友欢迎类型的SOP模板
                result = await db.execute(
                    select(SOPTemplate)
                    .where(
                        SOPTemplate.sop_type == SOPType.WELCOME,
                        SOPTemplate.status == SOPStatus.ACTIVE,
                        or_(
                            SOPTemplate.trigger_config["auto_trigger"].astext == "true",
                            SOPTemplate.trigger_config.is_(None)
                        )
                    )
                )
                templates = result.scalars().all()
                
                for template in templates:
                    await self._create_triggered_instance(
                        template, wechat_account_id, contact_id, 
                        {"trigger_type": "new_friend", "event": event}, db
                    )
                
        except Exception as e:
            logger.error(f"处理新好友触发失败: {str(e)}")
    
    async def _handle_message_received_trigger(self, event: Dict[str, Any]):
        """处理收到消息触发"""
        try:
            message_data = event.get("message", {})
            contact_id = event.get("contact_id")
            wechat_account_id = event.get("wechat_account_id")
            message_content = message_data.get("content", "")
            
            if not contact_id or not wechat_account_id:
                return
            
            async with get_db() as db:
                # 查找关键词触发的SOP模板
                result = await db.execute(
                    select(SOPTemplate)
                    .where(
                        SOPTemplate.status == SOPStatus.ACTIVE
                    )
                )
                templates = result.scalars().all()
                
                for template in templates:
                    trigger_config = template.trigger_config or {}
                    keywords = trigger_config.get("keywords", [])
                    
                    # 检查关键词匹配
                    if keywords and any(keyword in message_content for keyword in keywords):
                        await self._create_triggered_instance(
                            template, wechat_account_id, contact_id,
                            {"trigger_type": "keyword_matched", "keywords": keywords, "message": message_content}, db
                        )
                
        except Exception as e:
            logger.error(f"处理消息触发失败: {str(e)}")
    
    async def _handle_contact_added_trigger(self, event: Dict[str, Any]):
        """处理联系人添加触发"""
        # 与新好友触发类似
        await self._handle_new_friend_trigger(event)
    
    async def _handle_keyword_matched_trigger(self, event: Dict[str, Any]):
        """处理关键词匹配触发"""
        # 与消息触发类似
        await self._handle_message_received_trigger(event)
    
    async def _handle_time_based_trigger(self, event: Dict[str, Any]):
        """处理基于时间的触发"""
        # 这个通过定时调度处理，此处为占位
        pass
    
    async def _handle_manual_trigger(self, event: Dict[str, Any]):
        """处理手动触发"""
        try:
            template_id = event.get("template_id")
            targets = event.get("targets", [])
            
            if not template_id or not targets:
                return
            
            async with get_db() as db:
                template_result = await db.execute(
                    select(SOPTemplate)
                    .where(SOPTemplate.id == template_id, SOPTemplate.status == SOPStatus.ACTIVE)
                )
                template = template_result.scalar_one_or_none()
                
                if not template:
                    return
                
                for target in targets:
                    await self._create_triggered_instance(
                        template, target["wechat_account_id"], target["contact_id"],
                        {"trigger_type": "manual", "event": event}, db
                    )
                
        except Exception as e:
            logger.error(f"处理手动触发失败: {str(e)}")
    
    async def _create_triggered_instance(
        self, 
        template: SOPTemplate, 
        wechat_account_id: str, 
        contact_id: str, 
        trigger_context: Dict[str, Any],
        db: AsyncSession
    ):
        """创建触发的实例"""
        try:
            # 检查是否已有活跃实例
            existing_result = await db.execute(
                select(SOPInstance)
                .where(
                    SOPInstance.template_id == template.id,
                    SOPInstance.contact_id == contact_id,
                    SOPInstance.status.in_([TaskStatus.PENDING, TaskStatus.SCHEDULED, TaskStatus.EXECUTING])
                )
            )
            existing_instance = existing_result.scalar_one_or_none()
            
            if existing_instance:
                logger.debug(f"联系人已有活跃SOP实例: {contact_id}")
                return
            
            # 获取联系人信息
            contact_result = await db.execute(
                select(Contact)
                .where(Contact.id == contact_id)
            )
            contact = contact_result.scalar_one_or_none()
            
            if not contact:
                logger.warning(f"联系人不存在: {contact_id}")
                return
            
            # 创建实例
            instance = SOPInstance(
                template_id=template.id,
                organization_id=template.organization_id,
                wechat_account_id=wechat_account_id,
                contact_id=contact_id,
                instance_name=f"{template.name} - {contact.display_name} (触发)",
                variables=trigger_context,
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
            
            # 启动执行
            asyncio.create_task(
                sop_executor.execute_instance(str(instance.id))
            )
            
            self.stats["total_executed"] += 1
            
            logger.info(f"触发SOP实例创建成功: {instance.id}")
            
        except Exception as e:
            logger.error(f"创建触发实例失败: {str(e)}")
            self.stats["total_failed"] += 1
    
    async def _check_delayed_instances(self):
        """检查延迟执行的实例"""
        try:
            async with get_db() as db:
                # 获取需要延迟执行的实例
                result = await db.execute(
                    select(SOPInstance)
                    .where(
                        SOPInstance.status == TaskStatus.SCHEDULED,
                        SOPInstance.next_execution_at <= datetime.utcnow()
                    )
                )
                instances = result.scalars().all()
                
                for instance in instances:
                    # 更新状态为待执行
                    instance.status = TaskStatus.PENDING
                    instance.next_execution_at = None
                    
                    # 启动执行
                    asyncio.create_task(
                        sop_executor.execute_instance(str(instance.id))
                    )
                
                if instances:
                    await db.commit()
                    logger.info(f"恢复执行延迟实例: {len(instances)}个")
                
        except Exception as e:
            logger.error(f"检查延迟实例失败: {str(e)}")
    
    async def _cleanup_expired_tasks(self):
        """清理过期任务"""
        try:
            async with get_db() as db:
                # 清理超时的等待回复实例
                timeout_time = datetime.utcnow() - timedelta(hours=48)  # 48小时超时
                
                result = await db.execute(
                    select(SOPInstance)
                    .where(
                        SOPInstance.status == TaskStatus.EXECUTING,
                        SOPInstance.started_at < timeout_time
                    )
                )
                timeout_instances = result.scalars().all()
                
                for instance in timeout_instances:
                    instance.status = TaskStatus.FAILED
                    instance.completed_at = datetime.utcnow()
                    instance.error_message = "执行超时"
                
                if timeout_instances:
                    await db.commit()
                    logger.info(f"清理超时实例: {len(timeout_instances)}个")
                
        except Exception as e:
            logger.error(f"清理过期任务失败: {str(e)}")
    
    async def _update_stats(self):
        """更新统计信息"""
        try:
            async with get_db() as db:
                # 统计活跃调度数
                result = await db.execute(
                    select(func.count(SOPSchedule.id))
                    .where(SOPSchedule.is_active == True)
                )
                self.stats["active_schedules"] = result.scalar() or 0
                
                # 存储统计到Redis
                await redis_client.setex(
                    "sop_scheduler_stats",
                    300,  # 5分钟过期
                    json.dumps(self.stats)
                )
                
        except Exception as e:
            logger.error(f"更新统计信息失败: {str(e)}")
    
    # ==================== 公共接口 ====================
    
    async def trigger_sop(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """手动触发SOP事件"""
        try:
            event = {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                **event_data
            }
            
            # 添加到触发事件队列
            await redis_client.lpush("sop_trigger_events", json.dumps(event))
            
            logger.info(f"SOP触发事件已添加: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"触发SOP事件失败: {event_type}, {str(e)}")
            return False
    
    async def create_schedule(
        self, 
        template_id: str, 
        name: str,
        cron_expression: str,
        target_filter: Dict[str, Any],
        organization_id: str
    ) -> Optional[str]:
        """创建调度配置"""
        try:
            async with get_db() as db:
                schedule = SOPSchedule(
                    template_id=template_id,
                    organization_id=organization_id,
                    name=name,
                    cron_expression=cron_expression,
                    target_filter=target_filter,
                    next_execution_at=self._calculate_next_execution_from_cron(cron_expression)
                )
                
                db.add(schedule)
                await db.commit()
                await db.refresh(schedule)
                
                logger.info(f"调度配置创建成功: {schedule.id}")
                return str(schedule.id)
                
        except Exception as e:
            logger.error(f"创建调度配置失败: {str(e)}")
            return None
    
    def _calculate_next_execution_from_cron(self, cron_expression: str) -> Optional[datetime]:
        """从cron表达式计算下次执行时间"""
        try:
            cron = croniter(cron_expression, datetime.utcnow())
            return cron.get_next(datetime)
        except:
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "schedule_interval": self.schedule_interval,
            "max_concurrent_executions": self.max_concurrent_executions
        }


# 全局调度器实例
sop_scheduler = SOPScheduler()

