"""
设备状态监控服务
负责定期检查设备状态、处理掉线重连、风控检测等
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.device import WeChatAccount, DeviceStatus, DeviceLog
from app.services.gewe_service import GeWeService, GeWeAPIError
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class DeviceMonitor:
    """设备监控服务"""
    
    def __init__(self):
        self.gewe_service = GeWeService()
        self.notification_service = NotificationService()
        self.is_running = False
        self.check_interval = 30  # 30秒检查一次
        
    async def start(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("设备监控服务已在运行")
            return
        
        self.is_running = True
        logger.info("启动设备状态监控服务")
        
        # 启动监控任务
        asyncio.create_task(self._monitor_loop())
        asyncio.create_task(self._check_offline_devices())
        asyncio.create_task(self._detect_risk_events())
        asyncio.create_task(self._reset_daily_counters())
    
    async def stop(self):
        """停止监控服务"""
        self.is_running = False
        logger.info("停止设备状态监控服务")
    
    async def _monitor_loop(self):
        """主监控循环"""
        while self.is_running:
            try:
                await self._check_all_devices()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"设备监控循环异常: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_devices(self):
        """检查所有设备状态"""
        try:
            async with get_db() as db:
                # 获取所有活跃的微信账号
                result = await db.execute(
                    select(WeChatAccount)
                    .where(
                        WeChatAccount.is_active == True,
                        WeChatAccount.gewe_app_id.isnot(None)
                    )
                )
                accounts = result.scalars().all()
                
                logger.debug(f"检查{len(accounts)}个设备状态")
                
                # 并发检查设备状态
                tasks = []
                for account in accounts:
                    task = asyncio.create_task(
                        self._check_single_device(db, account)
                    )
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"检查设备状态失败: {str(e)}")
    
    async def _check_single_device(self, db: AsyncSession, account: WeChatAccount):
        """检查单个设备状态"""
        try:
            # 调用GeWe API获取设备状态
            status_data = await self.gewe_service.get_device_status(account.gewe_app_id)
            
            new_status = self._parse_device_status(status_data)
            old_status = account.status
            
            # 状态变化处理
            if new_status != old_status:
                await self._handle_status_change(db, account, old_status, new_status, status_data)
            
            # 更新最后检查时间
            account.last_seen_at = datetime.utcnow()
            
            # 如果在线，更新统计信息
            if new_status == DeviceStatus.ONLINE:
                await self._update_device_stats(account, status_data)
            
            await db.commit()
            
        except GeWeAPIError as e:
            # GeWe API错误，可能是设备真的离线了
            if e.status_code in [404, 500]:  # 设备不存在或服务错误
                await self._handle_device_unavailable(db, account)
        except Exception as e:
            logger.error(f"检查设备状态异常: {account.wxid}, {str(e)}")
    
    def _parse_device_status(self, status_data: Dict[str, Any]) -> DeviceStatus:
        """解析GeWe返回的设备状态"""
        status_map = {
            "online": DeviceStatus.ONLINE,
            "offline": DeviceStatus.OFFLINE,
            "initializing": DeviceStatus.INITIALIZING,
            "awaiting_login": DeviceStatus.AWAITING_RELOGIN,
            "risk_control": DeviceStatus.RISK_CONTROLLED,
            "banned": DeviceStatus.BANNED,
            "error": DeviceStatus.ERROR
        }
        
        gewe_status = status_data.get("status", "offline").lower()
        return status_map.get(gewe_status, DeviceStatus.OFFLINE)
    
    async def _handle_status_change(
        self,
        db: AsyncSession,
        account: WeChatAccount,
        old_status: DeviceStatus,
        new_status: DeviceStatus,
        status_data: Dict[str, Any]
    ):
        """处理设备状态变化"""
        logger.info(f"设备状态变化: {account.wxid} {old_status.value} -> {new_status.value}")
        
        # 更新账号状态
        account.status = new_status
        
        # 特殊状态处理
        if new_status == DeviceStatus.ONLINE:
            account.last_login_at = datetime.utcnow()
            if old_status in [DeviceStatus.OFFLINE, DeviceStatus.AWAITING_RELOGIN]:
                # 设备重新上线
                await self._handle_device_online(db, account, status_data)
        
        elif new_status == DeviceStatus.OFFLINE:
            if old_status == DeviceStatus.ONLINE:
                # 设备意外离线
                await self._handle_device_offline(db, account)
        
        elif new_status == DeviceStatus.RISK_CONTROLLED:
            # 触发风控
            await self._handle_risk_control(db, account, status_data)
        
        elif new_status == DeviceStatus.BANNED:
            # 账号被封
            await self._handle_account_banned(db, account, status_data)
        
        # 记录状态变化日志
        log_entry = DeviceLog(
            wechat_account_id=account.id,
            log_type="status_change",
            log_level="info",
            message=f"设备状态变化: {old_status.value} -> {new_status.value}",
            old_status=old_status.value,
            new_status=new_status.value,
            details=status_data
        )
        db.add(log_entry)
        
        # 发送状态变化通知
        await self._send_status_notification(account, old_status, new_status)
    
    async def _handle_device_online(
        self,
        db: AsyncSession,
        account: WeChatAccount,
        status_data: Dict[str, Any]
    ):
        """处理设备上线"""
        logger.info(f"设备上线: {account.wxid}")
        
        # 更新设备信息
        if "userInfo" in status_data:
            user_info = status_data["userInfo"]
            account.nickname = user_info.get("nickname", account.nickname)
            account.avatar = user_info.get("avatar", account.avatar)
        
        # 同步好友和群组数量
        try:
            friends = await self.gewe_service.get_friend_list(account.gewe_app_id)
            groups = await self.gewe_service.get_group_list(account.gewe_app_id)
            
            account.total_friends = len(friends)
            account.total_groups = len(groups)
            
        except Exception as e:
            logger.warning(f"同步好友群组信息失败: {account.wxid}, {str(e)}")
        
        # 清除旧的二维码
        await self._cleanup_expired_qrcodes(db, account.id)
    
    async def _handle_device_offline(self, db: AsyncSession, account: WeChatAccount):
        """处理设备离线"""
        logger.warning(f"设备离线: {account.wxid}")
        
        # 判断是否是"首夜掉线"情况
        if account.last_login_at:
            online_duration = datetime.utcnow() - account.last_login_at
            if online_duration < timedelta(hours=24):
                # 可能是首夜掉线，需要重新登录
                account.status = DeviceStatus.AWAITING_RELOGIN
                
                log_entry = DeviceLog(
                    wechat_account_id=account.id,
                    log_type="first_night_offline",
                    log_level="warning",
                    message="检测到首夜掉线，需要重新登录",
                    details={"online_duration_hours": online_duration.total_seconds() / 3600}
                )
                db.add(log_entry)
        
        # 添加风控事件记录
        account.add_risk_event(
            event_type="unexpected_offline",
            description="设备意外离线",
            severity="medium"
        )
    
    async def _handle_risk_control(
        self,
        db: AsyncSession,
        account: WeChatAccount,
        status_data: Dict[str, Any]
    ):
        """处理风控状态"""
        logger.warning(f"设备触发风控: {account.wxid}")
        
        risk_info = status_data.get("riskInfo", {})
        risk_type = risk_info.get("type", "unknown")
        risk_message = risk_info.get("message", "触发风控")
        
        # 添加风控事件
        account.add_risk_event(
            event_type=f"risk_control_{risk_type}",
            description=risk_message,
            severity="high"
        )
        
        # 记录详细日志
        log_entry = DeviceLog(
            wechat_account_id=account.id,
            log_type="risk_control",
            log_level="error",
            message=f"触发风控: {risk_message}",
            details=risk_info
        )
        db.add(log_entry)
        
        # 发送紧急通知
        await self.notification_service.send_urgent_notification(
            title="设备风控警告",
            message=f"设备 {account.nickname or account.wxid} 触发风控: {risk_message}",
            account_id=str(account.id)
        )
    
    async def _handle_account_banned(
        self,
        db: AsyncSession,
        account: WeChatAccount,
        status_data: Dict[str, Any]
    ):
        """处理账号被封"""
        logger.error(f"账号被封: {account.wxid}")
        
        ban_info = status_data.get("banInfo", {})
        ban_reason = ban_info.get("reason", "账号被封禁")
        ban_duration = ban_info.get("duration", "未知")
        
        # 添加封号事件
        account.add_risk_event(
            event_type="account_banned",
            description=f"账号被封: {ban_reason}",
            severity="high"
        )
        
        # 禁用账号
        account.is_active = False
        
        # 记录封号日志
        log_entry = DeviceLog(
            wechat_account_id=account.id,
            log_type="account_banned",
            log_level="critical",
            message=f"账号被封: {ban_reason}, 时长: {ban_duration}",
            details=ban_info
        )
        db.add(log_entry)
        
        # 发送紧急通知
        await self.notification_service.send_urgent_notification(
            title="账号被封警告",
            message=f"账号 {account.nickname or account.wxid} 被封禁: {ban_reason}",
            account_id=str(account.id)
        )
    
    async def _handle_device_unavailable(self, db: AsyncSession, account: WeChatAccount):
        """处理设备不可用情况"""
        if account.status != DeviceStatus.OFFLINE:
            logger.warning(f"设备变为不可用: {account.wxid}")
            account.status = DeviceStatus.OFFLINE
            
            log_entry = DeviceLog(
                wechat_account_id=account.id,
                log_type="device_unavailable",
                log_level="warning",
                message="设备API调用失败，标记为离线"
            )
            db.add(log_entry)
            
            await db.commit()
    
    async def _update_device_stats(self, account: WeChatAccount, status_data: Dict[str, Any]):
        """更新设备统计信息"""
        # 更新网络信息
        if "networkInfo" in status_data:
            network_info = status_data["networkInfo"]
            account.last_ip = network_info.get("ip")
            account.login_location = network_info.get("location")
    
    async def _send_status_notification(
        self,
        account: WeChatAccount,
        old_status: DeviceStatus,
        new_status: DeviceStatus
    ):
        """发送状态变化通知"""
        if new_status in [DeviceStatus.OFFLINE, DeviceStatus.RISK_CONTROLLED, DeviceStatus.BANNED]:
            # 重要状态变化需要通知
            await self.notification_service.send_status_notification(
                account_id=str(account.id),
                account_name=account.nickname or account.wxid,
                old_status=old_status.value,
                new_status=new_status.value
            )
    
    async def _check_offline_devices(self):
        """定期检查离线设备，尝试重连"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # 5分钟检查一次
                
                async with get_db() as db:
                    # 查询需要重连的设备
                    result = await db.execute(
                        select(WeChatAccount)
                        .where(
                            WeChatAccount.is_active == True,
                            WeChatAccount.status == DeviceStatus.AWAITING_RELOGIN,
                            WeChatAccount.gewe_app_id.isnot(None)
                        )
                    )
                    accounts = result.scalars().all()
                    
                    for account in accounts:
                        await self._attempt_auto_reconnect(db, account)
                        
            except Exception as e:
                logger.error(f"检查离线设备异常: {str(e)}")
    
    async def _attempt_auto_reconnect(self, db: AsyncSession, account: WeChatAccount):
        """尝试自动重连"""
        try:
            logger.info(f"尝试自动重连: {account.wxid}")
            
            # 生成重连二维码
            qr_data = await self.gewe_service.get_relogin_qrcode(account.gewe_app_id)
            
            # 存储二维码到Redis，供前端获取
            qr_key = f"relogin_qr:{account.id}"
            await redis_client.setex(qr_key, 300, qr_data["qr_code"])  # 5分钟过期
            
            # 发送重连通知
            await self.notification_service.send_reconnect_notification(
                account_id=str(account.id),
                account_name=account.nickname or account.wxid,
                qr_code_data=qr_data["qr_code"]
            )
            
            log_entry = DeviceLog(
                wechat_account_id=account.id,
                log_type="auto_reconnect_attempt",
                log_level="info",
                message="尝试自动重连，已生成二维码"
            )
            db.add(log_entry)
            await db.commit()
            
        except Exception as e:
            logger.error(f"自动重连失败: {account.wxid}, {str(e)}")
    
    async def _detect_risk_events(self):
        """风控事件检测"""
        while self.is_running:
            try:
                await asyncio.sleep(600)  # 10分钟检查一次
                
                async with get_db() as db:
                    # 查询高风险账号
                    result = await db.execute(
                        select(WeChatAccount)
                        .where(
                            WeChatAccount.is_active == True,
                            WeChatAccount.risk_level == "high"
                        )
                    )
                    high_risk_accounts = result.scalars().all()
                    
                    for account in high_risk_accounts:
                        await self._handle_high_risk_account(db, account)
                        
            except Exception as e:
                logger.error(f"风控检测异常: {str(e)}")
    
    async def _handle_high_risk_account(self, db: AsyncSession, account: WeChatAccount):
        """处理高风险账号"""
        # 暂停高风险账号的自动化操作
        if account.ai_enabled:
            account.ai_enabled = False
            account.auto_reply_enabled = False
            
            log_entry = DeviceLog(
                wechat_account_id=account.id,
                log_type="risk_mitigation",
                log_level="warning",
                message="高风险账号，暂停自动化功能"
            )
            db.add(log_entry)
            
            await db.commit()
            
            # 发送风险缓解通知
            await self.notification_service.send_risk_mitigation_notification(
                account_id=str(account.id),
                account_name=account.nickname or account.wxid
            )
    
    async def _reset_daily_counters(self):
        """重置每日计数器"""
        while self.is_running:
            try:
                # 等待到每天0点
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                wait_seconds = (tomorrow - now).total_seconds()
                
                await asyncio.sleep(wait_seconds)
                
                # 重置所有账号的每日计数器
                async with get_db() as db:
                    await db.execute(
                        update(WeChatAccount)
                        .where(WeChatAccount.is_active == True)
                        .values(daily_message_count=0)
                    )
                    await db.commit()
                
                logger.info("每日计数器重置完成")
                
            except Exception as e:
                logger.error(f"重置每日计数器异常: {str(e)}")
                await asyncio.sleep(3600)  # 出错时1小时后重试
    
    async def _cleanup_expired_qrcodes(self, db: AsyncSession, account_id: str):
        """清理过期的二维码"""
        from app.models.device import DeviceQRCode
        
        await db.execute(
            update(DeviceQRCode)
            .where(
                DeviceQRCode.wechat_account_id == account_id,
                DeviceQRCode.expires_at < datetime.utcnow()
            )
            .values(is_expired=True)
        )


# 全局设备监控实例
device_monitor = DeviceMonitor()

