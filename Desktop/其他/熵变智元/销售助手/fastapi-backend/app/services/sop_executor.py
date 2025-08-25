"""
SOP执行器服务
负责SOP实例的执行、任务调度、状态管理等核心功能
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.redis import redis_client
from app.core.config import settings
from app.models.sop import (
    SOPTemplate, SOPInstance, SOPTask, 
    SOPStatus, TaskStatus, ActionType, TriggerType
)
from app.models.device import WeChatAccount, DeviceStatus
from app.models.chat import Contact, MessageTemplate
from app.services.gewe_service import gewe_service
from app.services.ai_service import ai_service
from app.services.websocket_manager import websocket_manager
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """执行上下文"""
    instance: SOPInstance
    template: SOPTemplate
    wechat_account: WeChatAccount
    contact: Contact
    variables: Dict[str, Any]
    session: AsyncSession


class SOPExecutionError(Exception):
    """SOP执行异常"""
    pass


class SOPExecutor:
    """SOP执行器"""
    
    def __init__(self):
        self.running_instances: Dict[str, asyncio.Task] = {}
        self.action_handlers: Dict[ActionType, Callable] = {
            ActionType.SEND_MESSAGE: self._handle_send_message,
            ActionType.SEND_IMAGE: self._handle_send_image,
            ActionType.SEND_FILE: self._handle_send_file,
            ActionType.POST_MOMENTS: self._handle_post_moments,
            ActionType.ADD_TAG: self._handle_add_tag,
            ActionType.REMOVE_TAG: self._handle_remove_tag,
            ActionType.UPDATE_REMARK: self._handle_update_remark,
            ActionType.NOTIFY_MANUAL: self._handle_notify_manual,
            ActionType.WAIT_REPLY: self._handle_wait_reply,
            ActionType.CONDITION_CHECK: self._handle_condition_check
        }
    
    async def execute_instance(self, instance_id: str) -> bool:
        """执行SOP实例"""
        try:
            # 检查是否已在执行
            if instance_id in self.running_instances:
                logger.warning(f"SOP实例已在执行中: {instance_id}")
                return False
            
            # 创建执行任务
            task = asyncio.create_task(self._execute_instance_loop(instance_id))
            self.running_instances[instance_id] = task
            
            # 等待执行完成
            result = await task
            
            # 清理任务
            if instance_id in self.running_instances:
                del self.running_instances[instance_id]
            
            return result
            
        except Exception as e:
            logger.error(f"执行SOP实例失败: {instance_id}, {str(e)}")
            
            # 清理任务
            if instance_id in self.running_instances:
                del self.running_instances[instance_id]
            
            return False
    
    async def _execute_instance_loop(self, instance_id: str) -> bool:
        """SOP实例执行循环"""
        async with get_db() as db:
            try:
                # 获取实例及相关数据
                context = await self._load_execution_context(instance_id, db)
                if not context:
                    return False
                
                # 标记实例开始执行
                await self._mark_instance_started(context)
                
                # 执行步骤循环
                while context.instance.is_active:
                    # 获取当前步骤
                    current_step = context.instance.get_current_step()
                    if not current_step:
                        logger.warning(f"SOP实例没有可执行步骤: {instance_id}")
                        break
                    
                    # 创建任务记录
                    task = await self._create_task_record(context, current_step, db)
                    
                    # 执行步骤
                    success = await self._execute_step(context, current_step, task, db)
                    
                    if success:
                        # 步骤执行成功，前进到下一步
                        has_next = context.instance.advance_to_next_step()
                        if not has_next:
                            # 已完成所有步骤
                            await self._mark_instance_completed(context, db)
                            break
                    else:
                        # 步骤执行失败
                        if task.is_retryable:
                            logger.info(f"步骤将重试: {task.step_name} (重试次数: {task.retry_count})")
                            # 延迟重试
                            await asyncio.sleep(30)  # 30秒后重试
                            continue
                        else:
                            # 不可重试，标记实例失败
                            await self._mark_instance_failed(context, f"步骤执行失败: {task.step_name}", db)
                            break
                    
                    # 检查是否需要延迟
                    delay_minutes = current_step.get("delay_minutes", 0)
                    if delay_minutes > 0:
                        logger.info(f"步骤延迟等待: {delay_minutes}分钟")
                        await asyncio.sleep(delay_minutes * 60)
                    
                    # 提交中间状态
                    await db.commit()
                
                logger.info(f"SOP实例执行完成: {instance_id}")
                return True
                
            except asyncio.CancelledError:
                logger.info(f"SOP实例执行被取消: {instance_id}")
                return False
                
            except Exception as e:
                logger.error(f"SOP实例执行异常: {instance_id}, {str(e)}")
                
                # 标记实例失败
                try:
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
                except:
                    pass
                
                return False
    
    async def _load_execution_context(self, instance_id: str, db: AsyncSession) -> Optional[ExecutionContext]:
        """加载执行上下文"""
        try:
            # 获取实例及关联数据
            result = await db.execute(
                select(SOPInstance)
                .options(
                    joinedload(SOPInstance.template),
                    joinedload(SOPInstance.wechat_account),
                    joinedload(SOPInstance.contact)
                )
                .where(SOPInstance.id == instance_id)
            )
            instance = result.unique().scalar_one_or_none()
            
            if not instance:
                logger.error(f"SOP实例不存在: {instance_id}")
                return None
            
            if not instance.template:
                logger.error(f"SOP模板不存在: {instance.template_id}")
                return None
            
            if not instance.wechat_account:
                logger.error(f"微信账号不存在: {instance.wechat_account_id}")
                return None
            
            if not instance.contact:
                logger.error(f"联系人不存在: {instance.contact_id}")
                return None
            
            # 检查微信账号状态
            if instance.wechat_account.status != DeviceStatus.ONLINE:
                logger.error(f"微信账号未在线: {instance.wechat_account_id}")
                return None
            
            return ExecutionContext(
                instance=instance,
                template=instance.template,
                wechat_account=instance.wechat_account,
                contact=instance.contact,
                variables=instance.variables or {},
                session=db
            )
            
        except Exception as e:
            logger.error(f"加载执行上下文失败: {instance_id}, {str(e)}")
            return None
    
    async def _mark_instance_started(self, context: ExecutionContext):
        """标记实例开始执行"""
        context.instance.status = TaskStatus.EXECUTING
        context.instance.started_at = datetime.utcnow()
        
        # 发送WebSocket通知
        await websocket_manager.broadcast({
            "type": "sop_instance_started",
            "instance_id": str(context.instance.id),
            "template_name": context.template.name,
            "contact_name": context.contact.display_name
        })
        
        await context.session.commit()
    
    async def _mark_instance_completed(self, context: ExecutionContext, db: AsyncSession):
        """标记实例完成"""
        context.instance.status = TaskStatus.COMPLETED
        context.instance.completed_at = datetime.utcnow()
        context.instance.progress = 100
        
        # 更新模板统计
        context.template.active_instances = max(0, context.template.active_instances - 1)
        
        # 发送完成通知
        await notification_service.send_success_notification(
            title="SOP执行完成",
            message=f"SOP「{context.template.name}」对联系人「{context.contact.display_name}」的执行已完成",
            target_type="broadcast"
        )
        
        await db.commit()
        
        logger.info(f"SOP实例执行完成: {context.instance.id}")
    
    async def _mark_instance_failed(self, context: ExecutionContext, error_message: str, db: AsyncSession):
        """标记实例失败"""
        context.instance.status = TaskStatus.FAILED
        context.instance.completed_at = datetime.utcnow()
        context.instance.error_message = error_message
        
        # 更新模板统计
        context.template.active_instances = max(0, context.template.active_instances - 1)
        
        # 发送失败通知
        await notification_service.send_error_notification(
            title="SOP执行失败",
            message=f"SOP「{context.template.name}」对联系人「{context.contact.display_name}」的执行失败: {error_message}",
            target_type="broadcast"
        )
        
        await db.commit()
        
        logger.error(f"SOP实例执行失败: {context.instance.id}, {error_message}")
    
    async def _create_task_record(self, context: ExecutionContext, step: Dict[str, Any], db: AsyncSession) -> SOPTask:
        """创建任务记录"""
        task = SOPTask(
            instance_id=context.instance.id,
            step_id=step["id"],
            step_name=step["name"],
            action_type=ActionType(step["action_type"]),
            input_data=step,
            scheduled_at=datetime.utcnow()
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        return task
    
    async def _execute_step(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask, db: AsyncSession) -> bool:
        """执行单个步骤"""
        try:
            # 标记任务开始
            task.mark_started()
            await db.commit()
            
            # 发送WebSocket进度更新
            await websocket_manager.send_to_user(str(context.instance.user_id), {
                "type": "sop_step_started",
                "instance_id": str(context.instance.id),
                "step_name": step["name"],
                "progress": context.instance.progress
            })
            
            # 检查前置条件
            if not await self._check_step_conditions(context, step):
                task.mark_skipped("前置条件不满足")
                await db.commit()
                return True  # 跳过也算成功
            
            # 执行动作
            action_type = ActionType(step["action_type"])
            handler = self.action_handlers.get(action_type)
            
            if not handler:
                task.mark_failed(f"不支持的动作类型: {action_type}")
                await db.commit()
                return False
            
            # 调用处理器
            result = await handler(context, step, task)
            
            if result:
                task.mark_completed(result)
                logger.info(f"步骤执行成功: {step['name']}")
            else:
                task.mark_failed("处理器返回失败")
                logger.error(f"步骤执行失败: {step['name']}")
            
            await db.commit()
            return result is not False
            
        except Exception as e:
            logger.error(f"执行步骤异常: {step['name']}, {str(e)}")
            task.mark_failed(str(e))
            await db.commit()
            return False
    
    async def _check_step_conditions(self, context: ExecutionContext, step: Dict[str, Any]) -> bool:
        """检查步骤执行条件"""
        try:
            conditions = step.get("conditions", {})
            if not conditions:
                return True
            
            # 检查变量条件
            for key, expected_value in conditions.items():
                actual_value = context.variables.get(key)
                
                if isinstance(expected_value, dict):
                    # 复杂条件检查
                    operator = expected_value.get("operator", "eq")
                    value = expected_value.get("value")
                    
                    if operator == "eq" and actual_value != value:
                        return False
                    elif operator == "ne" and actual_value == value:
                        return False
                    elif operator == "in" and actual_value not in value:
                        return False
                    elif operator == "not_in" and actual_value in value:
                        return False
                    elif operator == "exists" and (actual_value is None) == value:
                        return False
                else:
                    # 简单相等检查
                    if actual_value != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查步骤条件失败: {str(e)}")
            return False
    
    # ==================== 动作处理器 ====================
    
    async def _handle_send_message(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理发送消息动作"""
        try:
            # 获取消息内容
            content = step.get("content")
            material_id = step.get("material_id")
            
            if material_id:
                # 从物料库获取内容
                content = await self._get_material_content(material_id, context.session)
                if not content:
                    raise SOPExecutionError(f"物料不存在: {material_id}")
            
            if not content:
                raise SOPExecutionError("消息内容为空")
            
            # 变量替换
            content = await self._replace_variables(content, context)
            
            # 发送消息
            result = await gewe_service.send_text_message(
                account_id=str(context.wechat_account.id),
                wxid=context.contact.wxid,
                message=content
            )
            
            if result.get("success"):
                # 更新变量
                context.variables["last_message_sent"] = content
                context.variables["last_message_time"] = datetime.utcnow().isoformat()
                context.instance.variables = context.variables
                
                return {
                    "message_sent": content,
                    "message_id": result.get("message_id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise SOPExecutionError(f"发送消息失败: {result.get('error', '未知错误')}")
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return None
    
    async def _handle_send_image(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理发送图片动作"""
        try:
            material_id = step.get("material_id")
            image_url = step.get("image_url")
            
            if material_id:
                # 从物料库获取图片URL
                image_url = await self._get_material_url(material_id, context.session)
                if not image_url:
                    raise SOPExecutionError(f"图片物料不存在: {material_id}")
            
            if not image_url:
                raise SOPExecutionError("图片URL为空")
            
            # 发送图片
            result = await gewe_service.send_image_message(
                account_id=str(context.wechat_account.id),
                wxid=context.contact.wxid,
                image_url=image_url
            )
            
            if result.get("success"):
                return {
                    "image_sent": image_url,
                    "message_id": result.get("message_id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise SOPExecutionError(f"发送图片失败: {result.get('error', '未知错误')}")
            
        except Exception as e:
            logger.error(f"发送图片失败: {str(e)}")
            return None
    
    async def _handle_send_file(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理发送文件动作"""
        try:
            material_id = step.get("material_id")
            file_url = step.get("file_url")
            
            if material_id:
                # 从物料库获取文件URL
                file_url = await self._get_material_url(material_id, context.session)
                if not file_url:
                    raise SOPExecutionError(f"文件物料不存在: {material_id}")
            
            if not file_url:
                raise SOPExecutionError("文件URL为空")
            
            # 发送文件
            result = await gewe_service.send_file_message(
                account_id=str(context.wechat_account.id),
                wxid=context.contact.wxid,
                file_url=file_url
            )
            
            if result.get("success"):
                return {
                    "file_sent": file_url,
                    "message_id": result.get("message_id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise SOPExecutionError(f"发送文件失败: {result.get('error', '未知错误')}")
            
        except Exception as e:
            logger.error(f"发送文件失败: {str(e)}")
            return None
    
    async def _handle_post_moments(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理发朋友圈动作"""
        try:
            content = step.get("content", "")
            images = step.get("images", [])
            
            # 变量替换
            content = await self._replace_variables(content, context)
            
            # 发朋友圈
            result = await gewe_service.post_moments(
                account_id=str(context.wechat_account.id),
                content=content,
                images=images
            )
            
            if result.get("success"):
                return {
                    "moments_posted": True,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise SOPExecutionError(f"发朋友圈失败: {result.get('error', '未知错误')}")
            
        except Exception as e:
            logger.error(f"发朋友圈失败: {str(e)}")
            return None
    
    async def _handle_add_tag(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理添加标签动作"""
        try:
            tag = step.get("tag")
            if not tag:
                raise SOPExecutionError("标签名称为空")
            
            # 添加标签到联系人
            current_tags = context.contact.tags or []
            if tag not in current_tags:
                current_tags.append(tag)
                context.contact.tags = current_tags
                await context.session.commit()
            
            return {
                "tag_added": tag,
                "current_tags": current_tags,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"添加标签失败: {str(e)}")
            return None
    
    async def _handle_remove_tag(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理移除标签动作"""
        try:
            tag = step.get("tag")
            if not tag:
                raise SOPExecutionError("标签名称为空")
            
            # 从联系人移除标签
            current_tags = context.contact.tags or []
            if tag in current_tags:
                current_tags.remove(tag)
                context.contact.tags = current_tags
                await context.session.commit()
            
            return {
                "tag_removed": tag,
                "current_tags": current_tags,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"移除标签失败: {str(e)}")
            return None
    
    async def _handle_update_remark(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理更新备注动作"""
        try:
            remark = step.get("remark")
            if not remark:
                raise SOPExecutionError("备注内容为空")
            
            # 变量替换
            remark = await self._replace_variables(remark, context)
            
            # 更新联系人备注
            old_remark = context.contact.remark
            context.contact.remark = remark
            await context.session.commit()
            
            return {
                "remark_updated": True,
                "old_remark": old_remark,
                "new_remark": remark,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"更新备注失败: {str(e)}")
            return None
    
    async def _handle_notify_manual(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理通知人工动作"""
        try:
            message = step.get("message", "需要人工处理")
            
            # 发送通知给用户
            await notification_service.send_warning_notification(
                title="SOP需要人工处理",
                message=f"SOP「{context.template.name}」在联系人「{context.contact.display_name}」处需要人工处理: {message}",
                target_type="user",
                target_id=str(context.instance.user_id),
                action_url=f"/sop/instances/{context.instance.id}"
            )
            
            return {
                "manual_notification_sent": True,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"发送人工通知失败: {str(e)}")
            return None
    
    async def _handle_wait_reply(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理等待回复动作"""
        try:
            timeout_minutes = step.get("timeout_minutes", 1440)  # 默认24小时
            
            # 设置等待回复状态
            context.variables["waiting_for_reply"] = True
            context.variables["wait_start_time"] = datetime.utcnow().isoformat()
            context.variables["wait_timeout"] = (datetime.utcnow() + timedelta(minutes=timeout_minutes)).isoformat()
            
            context.instance.variables = context.variables
            context.instance.next_execution_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
            
            return {
                "waiting_for_reply": True,
                "timeout_minutes": timeout_minutes,
                "timeout_at": context.variables["wait_timeout"]
            }
            
        except Exception as e:
            logger.error(f"设置等待回复失败: {str(e)}")
            return None
    
    async def _handle_condition_check(self, context: ExecutionContext, step: Dict[str, Any], task: SOPTask) -> Optional[Dict[str, Any]]:
        """处理条件检查动作"""
        try:
            conditions = step.get("conditions", {})
            result = await self._check_step_conditions(context, step)
            
            return {
                "condition_check_result": result,
                "conditions": conditions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"条件检查失败: {str(e)}")
            return None
    
    # ==================== 辅助方法 ====================
    
    async def _get_material_content(self, material_id: str, session: AsyncSession) -> Optional[str]:
        """从物料库获取内容"""
        try:
            # 这里应该查询物料表获取内容
            # 由于物料表模型未定义，暂时返回默认内容
            return f"[物料内容: {material_id}]"
            
        except Exception as e:
            logger.error(f"获取物料内容失败: {material_id}, {str(e)}")
            return None
    
    async def _get_material_url(self, material_id: str, session: AsyncSession) -> Optional[str]:
        """从物料库获取URL"""
        try:
            # 这里应该查询物料表获取URL
            # 由于物料表模型未定义，暂时返回默认URL
            return f"https://example.com/materials/{material_id}"
            
        except Exception as e:
            logger.error(f"获取物料URL失败: {material_id}, {str(e)}")
            return None
    
    async def _replace_variables(self, content: str, context: ExecutionContext) -> str:
        """替换内容中的变量"""
        try:
            # 基础变量
            variables = {
                "contact_name": context.contact.display_name,
                "contact_wxid": context.contact.wxid,
                "account_nickname": context.wechat_account.nickname,
                "current_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "current_date": datetime.utcnow().strftime("%Y-%m-%d"),
                **context.variables
            }
            
            # 简单变量替换
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                if placeholder in content:
                    content = content.replace(placeholder, str(value))
            
            return content
            
        except Exception as e:
            logger.error(f"变量替换失败: {str(e)}")
            return content
    
    async def stop_instance(self, instance_id: str) -> bool:
        """停止SOP实例执行"""
        try:
            if instance_id in self.running_instances:
                task = self.running_instances[instance_id]
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                del self.running_instances[instance_id]
                
                logger.info(f"SOP实例执行已停止: {instance_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"停止SOP实例失败: {instance_id}, {str(e)}")
            return False
    
    async def get_running_instances(self) -> List[str]:
        """获取正在运行的实例列表"""
        return list(self.running_instances.keys())
    
    async def get_execution_status(self, instance_id: str) -> Dict[str, Any]:
        """获取实例执行状态"""
        is_running = instance_id in self.running_instances
        
        # 从数据库获取实例状态
        async with get_db() as db:
            result = await db.execute(
                select(SOPInstance)
                .where(SOPInstance.id == instance_id)
            )
            instance = result.scalar_one_or_none()
            
            if not instance:
                return {"error": "实例不存在"}
            
            return {
                "instance_id": instance_id,
                "is_running": is_running,
                "status": instance.status.value,
                "progress": instance.progress,
                "current_step": instance.current_step_id,
                "started_at": instance.started_at.isoformat() if instance.started_at else None,
                "error_message": instance.error_message
            }


# 全局SOP执行器实例
sop_executor = SOPExecutor()

