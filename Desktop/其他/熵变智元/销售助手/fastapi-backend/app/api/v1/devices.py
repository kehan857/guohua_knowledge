"""
设备管理API路由
负责微信账号的托管、状态监控、登录管理等核心功能
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, validator
import logging
import uuid

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.user import User
from app.models.device import (
    WeChatAccount, Device, DeviceLog, DeviceGroup, DeviceQRCode,
    DeviceStatus, DeviceType
)
from app.api.deps import get_current_user, get_current_active_user
from app.services.gewe_service import GeWeService
from app.services.device_monitor import DeviceMonitor
from app.utils.permissions import require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Pydantic模型 ====================

class WeChatAccountCreate(BaseModel):
    """微信账号创建请求"""
    nickname: Optional[str] = Field(None, max_length=100, description="微信昵称")
    device_name: str = Field(..., max_length=100, description="设备名称")
    device_type: DeviceType = Field(DeviceType.ANDROID, description="设备类型")
    group_id: Optional[str] = Field(None, description="分组ID")
    ai_enabled: bool = Field(True, description="是否启用AI")
    workflow_id: Optional[str] = Field(None, description="AI工作流ID")


class WeChatAccountUpdate(BaseModel):
    """微信账号更新请求"""
    nickname: Optional[str] = Field(None, max_length=100, description="微信昵称")
    ai_enabled: Optional[bool] = Field(None, description="是否启用AI")
    auto_reply_enabled: Optional[bool] = Field(None, description="是否启用自动回复")
    workflow_id: Optional[str] = Field(None, description="AI工作流ID")
    daily_message_limit: Optional[int] = Field(None, ge=0, description="每日消息限制")
    group_id: Optional[str] = Field(None, description="分组ID")


class WeChatAccountResponse(BaseModel):
    """微信账号响应模型"""
    id: str
    wxid: Optional[str]
    nickname: Optional[str]
    avatar: Optional[str]
    status: DeviceStatus
    is_active: bool
    is_primary: bool
    ai_enabled: bool
    auto_reply_enabled: bool
    workflow_id: Optional[str]
    
    # 状态信息
    last_seen_at: Optional[datetime]
    last_login_at: Optional[datetime]
    last_ip: Optional[str]
    login_location: Optional[str]
    uptime_hours: float
    
    # 统计信息
    total_friends: int
    total_groups: int
    daily_message_count: int
    daily_message_limit: int
    message_usage_percentage: float
    
    # 风控信息
    risk_level: str
    risk_events: List[Dict[str, Any]]
    
    # 时间字段
    created_at: datetime
    activated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """设备响应模型"""
    id: str
    device_name: str
    device_type: DeviceType
    device_model: Optional[str]
    device_brand: Optional[str]
    os_version: Optional[str]
    app_version: Optional[str]
    
    # 网络信息
    ip_address: Optional[str]
    location: Optional[str]
    network_type: Optional[str]
    
    # 状态信息
    is_active: bool
    is_online: bool
    last_heartbeat: Optional[datetime]
    
    # 容量信息
    max_accounts: int
    current_accounts: int
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeviceStatsResponse(BaseModel):
    """设备统计响应"""
    total_accounts: int
    online_accounts: int
    offline_accounts: int
    risk_accounts: int
    today_messages: int
    online_rate: float
    
    # 状态分布
    status_distribution: Dict[str, int]
    
    # 风险分布
    risk_distribution: Dict[str, int]


class QRCodeResponse(BaseModel):
    """二维码响应模型"""
    id: str
    qr_code_data: str
    qr_code_url: Optional[str]
    qr_type: str
    expires_at: datetime
    is_valid: bool
    
    class Config:
        from_attributes = True


class DeviceLogResponse(BaseModel):
    """设备日志响应"""
    id: str
    log_type: str
    log_level: str
    message: str
    details: Dict[str, Any]
    operation: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== API路由 ====================

@router.get("/stats", response_model=DeviceStatsResponse)
async def get_device_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取设备统计信息"""
    try:
        # 查询统计数据
        total_query = await db.execute(
            select(func.count(WeChatAccount.id))
            .where(
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.is_active == True
            )
        )
        total_accounts = total_query.scalar() or 0
        
        # 在线账号数
        online_query = await db.execute(
            select(func.count(WeChatAccount.id))
            .where(
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.status == DeviceStatus.ONLINE,
                WeChatAccount.is_active == True
            )
        )
        online_accounts = online_query.scalar() or 0
        
        # 离线账号数
        offline_accounts = total_accounts - online_accounts
        
        # 风险账号数
        risk_query = await db.execute(
            select(func.count(WeChatAccount.id))
            .where(
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.risk_level.in_(["medium", "high"]),
                WeChatAccount.is_active == True
            )
        )
        risk_accounts = risk_query.scalar() or 0
        
        # 今日消息数
        today_messages_query = await db.execute(
            select(func.sum(WeChatAccount.daily_message_count))
            .where(
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.is_active == True
            )
        )
        today_messages = today_messages_query.scalar() or 0
        
        # 状态分布
        status_query = await db.execute(
            select(WeChatAccount.status, func.count(WeChatAccount.id))
            .where(
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.is_active == True
            )
            .group_by(WeChatAccount.status)
        )
        status_distribution = {status.value: count for status, count in status_query.all()}
        
        # 风险分布
        risk_query = await db.execute(
            select(WeChatAccount.risk_level, func.count(WeChatAccount.id))
            .where(
                WeChatAccount.organization_id == current_user.organization_id,
                WeChatAccount.is_active == True
            )
            .group_by(WeChatAccount.risk_level)
        )
        risk_distribution = {level: count for level, count in risk_query.all()}
        
        # 在线率
        online_rate = (online_accounts / total_accounts * 100) if total_accounts > 0 else 0
        
        return DeviceStatsResponse(
            total_accounts=total_accounts,
            online_accounts=online_accounts,
            offline_accounts=offline_accounts,
            risk_accounts=risk_accounts,
            today_messages=today_messages,
            online_rate=round(online_rate, 2),
            status_distribution=status_distribution,
            risk_distribution=risk_distribution
        )
        
    except Exception as e:
        logger.error(f"获取设备统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )


@router.get("/accounts", response_model=List[WeChatAccountResponse])
async def get_wechat_accounts(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[DeviceStatus] = Query(None, description="状态筛选"),
    risk_level: Optional[str] = Query(None, description="风险等级筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    group_id: Optional[str] = Query(None, description="分组ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微信账号列表"""
    try:
        # 构建查询条件
        query = select(WeChatAccount).where(
            WeChatAccount.organization_id == current_user.organization_id,
            WeChatAccount.is_active == True
        )
        
        # 应用筛选条件
        if status:
            query = query.where(WeChatAccount.status == status)
        
        if risk_level:
            query = query.where(WeChatAccount.risk_level == risk_level)
        
        if search:
            query = query.where(
                or_(
                    WeChatAccount.nickname.ilike(f"%{search}%"),
                    WeChatAccount.wxid.ilike(f"%{search}%")
                )
            )
        
        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(WeChatAccount.created_at.desc())
        
        result = await db.execute(query)
        accounts = result.scalars().all()
        
        # 转换为响应模型
        account_responses = []
        for account in accounts:
            account_data = WeChatAccountResponse.from_orm(account)
            account_responses.append(account_data)
        
        return account_responses
        
    except Exception as e:
        logger.error(f"获取微信账号列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账号列表失败"
        )


@router.post("/accounts", response_model=WeChatAccountResponse)
async def create_wechat_account(
    account_data: WeChatAccountCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建微信账号"""
    try:
        # 检查权限
        require_permission(current_user, "devices.create")
        
        # 创建新账号
        new_account = WeChatAccount(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            nickname=account_data.nickname,
            ai_enabled=account_data.ai_enabled,
            workflow_id=account_data.workflow_id,
            status=DeviceStatus.INITIALIZING
        )
        
        db.add(new_account)
        await db.commit()
        await db.refresh(new_account)
        
        # 记录操作日志
        log_entry = DeviceLog(
            wechat_account_id=new_account.id,
            log_type="account_created",
            log_level="info",
            message="微信账号创建成功",
            operation="create",
            operator_id=current_user.id,
            new_status=DeviceStatus.INITIALIZING.value
        )
        db.add(log_entry)
        await db.commit()
        
        # 异步初始化GeWe连接
        background_tasks.add_task(
            initialize_gewe_account,
            account_id=str(new_account.id),
            device_name=account_data.device_name,
            device_type=account_data.device_type.value
        )
        
        logger.info(f"微信账号创建成功: {new_account.id}")
        
        return WeChatAccountResponse.from_orm(new_account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建微信账号失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建账号失败"
        )


@router.get("/accounts/{account_id}", response_model=WeChatAccountResponse)
async def get_wechat_account(
    account_id: str = Path(..., description="账号ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微信账号详情"""
    try:
        # 查询账号
        result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.id == account_id,
                WeChatAccount.organization_id == current_user.organization_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )
        
        return WeChatAccountResponse.from_orm(account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取微信账号详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账号详情失败"
        )


@router.put("/accounts/{account_id}", response_model=WeChatAccountResponse)
async def update_wechat_account(
    account_id: str = Path(..., description="账号ID"),
    update_data: WeChatAccountUpdate = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新微信账号配置"""
    try:
        # 检查权限
        require_permission(current_user, "devices.update")
        
        # 查询账号
        result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.id == account_id,
                WeChatAccount.organization_id == current_user.organization_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(account, field):
                setattr(account, field, value)
        
        account.updated_at = datetime.utcnow()
        
        # 记录操作日志
        log_entry = DeviceLog(
            wechat_account_id=account.id,
            log_type="account_updated",
            log_level="info",
            message="微信账号配置更新",
            operation="update",
            operator_id=current_user.id,
            details=update_dict
        )
        db.add(log_entry)
        
        await db.commit()
        await db.refresh(account)
        
        logger.info(f"微信账号更新成功: {account.id}")
        
        return WeChatAccountResponse.from_orm(account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新微信账号失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新账号失败"
        )


@router.post("/accounts/{account_id}/qrcode", response_model=QRCodeResponse)
async def get_login_qrcode(
    account_id: str = Path(..., description="账号ID"),
    qr_type: str = Query("login", description="二维码类型: login/relogin"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取登录二维码"""
    try:
        # 查询账号
        result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.id == account_id,
                WeChatAccount.organization_id == current_user.organization_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )
        
        # 调用GeWe服务获取二维码
        gewe_service = GeWeService()
        
        if qr_type == "relogin" and account.gewe_app_id:
            qr_data = await gewe_service.get_relogin_qrcode(account.gewe_app_id)
        else:
            qr_data = await gewe_service.get_login_qrcode()
        
        # 保存二维码记录
        qr_code = DeviceQRCode(
            wechat_account_id=account.id,
            qr_code_data=qr_data["qr_code"],
            qr_code_url=qr_data.get("qr_url"),
            qr_type=qr_type,
            expires_at=datetime.utcnow() + timedelta(minutes=5)  # 5分钟过期
        )
        
        db.add(qr_code)
        
        # 更新账号状态
        if qr_type == "relogin":
            account.status = DeviceStatus.AWAITING_RELOGIN
        else:
            account.status = DeviceStatus.INITIALIZING
        
        # 记录操作日志
        log_entry = DeviceLog(
            wechat_account_id=account.id,
            log_type="qrcode_generated",
            log_level="info",
            message=f"生成{qr_type}二维码",
            operation="get_qrcode",
            operator_id=current_user.id,
            details={"qr_type": qr_type}
        )
        db.add(log_entry)
        
        await db.commit()
        await db.refresh(qr_code)
        
        logger.info(f"二维码生成成功: {account.id}, type: {qr_type}")
        
        return QRCodeResponse.from_orm(qr_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取登录二维码失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取二维码失败"
        )


@router.post("/accounts/{account_id}/logout")
async def logout_wechat_account(
    account_id: str = Path(..., description="账号ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """强制下线微信账号"""
    try:
        # 检查权限
        require_permission(current_user, "devices.update")
        
        # 查询账号
        result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.id == account_id,
                WeChatAccount.organization_id == current_user.organization_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )
        
        # 调用GeWe服务下线账号
        if account.gewe_app_id:
            gewe_service = GeWeService()
            await gewe_service.logout_account(account.gewe_app_id)
        
        # 更新账号状态
        old_status = account.status
        account.status = DeviceStatus.OFFLINE
        account.last_seen_at = datetime.utcnow()
        
        # 记录操作日志
        log_entry = DeviceLog(
            wechat_account_id=account.id,
            log_type="account_logout",
            log_level="warning",
            message="账号被强制下线",
            operation="logout",
            operator_id=current_user.id,
            old_status=old_status.value,
            new_status=DeviceStatus.OFFLINE.value
        )
        db.add(log_entry)
        
        await db.commit()
        
        logger.info(f"微信账号强制下线: {account.id}")
        
        return {"message": "账号已下线"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"强制下线失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="下线操作失败"
        )


@router.get("/accounts/{account_id}/logs", response_model=List[DeviceLogResponse])
async def get_account_logs(
    account_id: str = Path(..., description="账号ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    log_type: Optional[str] = Query(None, description="日志类型筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取账号操作日志"""
    try:
        # 验证账号存在且属于当前组织
        result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.id == account_id,
                WeChatAccount.organization_id == current_user.organization_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )
        
        # 构建查询
        query = select(DeviceLog).where(DeviceLog.wechat_account_id == account_id)
        
        if log_type:
            query = query.where(DeviceLog.log_type == log_type)
        
        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(DeviceLog.created_at.desc())
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [DeviceLogResponse.from_orm(log) for log in logs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取账号日志失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取日志失败"
        )


@router.delete("/accounts/{account_id}")
async def delete_wechat_account(
    account_id: str = Path(..., description="账号ID"),
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除微信账号"""
    try:
        # 检查权限
        require_permission(current_user, "devices.delete")
        
        # 查询账号
        result = await db.execute(
            select(WeChatAccount)
            .where(
                WeChatAccount.id == account_id,
                WeChatAccount.organization_id == current_user.organization_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )
        
        # 检查是否可以删除
        if account.status == DeviceStatus.ONLINE and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账号在线中，请先下线或使用强制删除"
            )
        
        # 如果有GeWe连接，先断开
        if account.gewe_app_id:
            try:
                gewe_service = GeWeService()
                await gewe_service.logout_account(account.gewe_app_id)
            except Exception as e:
                logger.warning(f"断开GeWe连接失败: {str(e)}")
        
        # 软删除（设置为非激活状态）
        account.is_active = False
        account.status = DeviceStatus.OFFLINE
        account.updated_at = datetime.utcnow()
        
        # 记录操作日志
        log_entry = DeviceLog(
            wechat_account_id=account.id,
            log_type="account_deleted",
            log_level="warning",
            message="微信账号被删除",
            operation="delete",
            operator_id=current_user.id,
            details={"force": force}
        )
        db.add(log_entry)
        
        await db.commit()
        
        logger.info(f"微信账号删除成功: {account.id}")
        
        return {"message": "账号删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除微信账号失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除账号失败"
        )


# ==================== 后台任务函数 ====================

async def initialize_gewe_account(account_id: str, device_name: str, device_type: str):
    """初始化GeWe账号连接（后台任务）"""
    try:
        # 这里应该调用GeWe服务初始化账号
        gewe_service = GeWeService()
        
        # 创建设备
        device_result = await gewe_service.create_device(
            device_name=device_name,
            device_type=device_type
        )
        
        # 更新账号信息
        # 这里需要更新数据库中的gewe_app_id等信息
        
        logger.info(f"GeWe账号初始化成功: {account_id}")
        
    except Exception as e:
        logger.error(f"GeWe账号初始化失败: {account_id}, error: {str(e)}")
        
        # 更新账号状态为错误
        # 这里需要更新数据库状态

