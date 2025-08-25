"""
用户认证API路由
包含登录、注册、token刷新、密码重置等功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, EmailStr, Field
import logging

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token
)
from app.core.config import settings
from app.models.user import User, UserSession, UserLoginLog, UserStatus
from app.services.email_service import send_email
from app.utils.validators import validate_password_strength
from app.utils.location import get_location_from_ip

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


# ==================== Pydantic模型 ====================

class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    organization_name: Optional[str] = Field(None, max_length=100, description="组织名称")


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")
    device_name: Optional[str] = Field(None, description="设备名称")


class TokenResponse(BaseModel):
    """token响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user: Dict[str, Any] = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr = Field(..., description="邮箱地址")


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")


class UserProfile(BaseModel):
    """用户档案模型"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    avatar: Optional[str]
    role: str
    status: str
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    quota_usage_percentage: float
    
    class Config:
        from_attributes = True


# ==================== 依赖函数 ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    try:
        # 验证token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
        
        # 查询用户
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == True,
                User.status != UserStatus.DELETED
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"用户认证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败，请重新登录"
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号未激活或已被暂停"
        )
    return current_user


# ==================== API路由 ====================

@router.post("/register", response_model=Dict[str, str])
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    try:
        # 验证密码强度
        if not validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码强度不够，请包含大小写字母、数字和特殊字符"
            )
        
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            status=UserStatus.INACTIVE  # 需要邮箱验证
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # 发送验证邮箱
        verification_token = create_access_token(
            data={"sub": str(new_user.id), "type": "email_verification"},
            expires_delta=timedelta(hours=24)
        )
        
        # TODO: 发送验证邮件
        # await send_verification_email(new_user.email, verification_token)
        
        logger.info(f"用户注册成功: {new_user.username} ({new_user.email})")
        
        return {
            "message": "注册成功，请查收验证邮件",
            "user_id": str(new_user.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    try:
        # 查找用户（支持用户名或邮箱登录）
        result = await db.execute(
            select(User).where(
                (User.username == user_data.username) | 
                (User.email == user_data.username)
            )
        )
        user = result.scalar_one_or_none()
        
        # 获取客户端信息
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        location = get_location_from_ip(client_ip)
        
        # 记录登录尝试
        login_log = UserLoginLog(
            user_id=user.id if user else None,
            ip_address=client_ip,
            user_agent=user_agent,
            location=location,
            success=False
        )
        
        # 验证用户和密码
        if not user or not verify_password(user_data.password, user.hashed_password):
            login_log.failure_reason = "用户名或密码错误"
            db.add(login_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 检查用户状态
        if user.status == UserStatus.SUSPENDED:
            login_log.failure_reason = "账号已被暂停"
            db.add(login_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被暂停，请联系管理员"
            )
        
        if user.status == UserStatus.DELETED:
            login_log.failure_reason = "账号已被删除"
            db.add(login_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号不存在"
            )
        
        # 生成令牌
        expires_delta = timedelta(hours=settings.JWT_EXPIRE_HOURS)
        if user_data.remember_me:
            expires_delta = timedelta(days=30)  # 记住我30天
        
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=expires_delta
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
        )
        
        # 创建会话记录
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            device_name=user_data.device_name,
            user_agent=user_agent,
            ip_address=client_ip,
            expires_at=datetime.utcnow() + expires_delta
        )
        
        # 更新用户登录信息
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        user.login_count = (user.login_count or 0) + 1
        
        # 更新登录日志
        login_log.user_id = user.id
        login_log.success = True
        
        db.add(session)
        db.add(login_log)
        await db.commit()
        
        # 设置Cookie（可选）
        if user_data.remember_me:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
                httponly=True,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite="lax"
            )
        
        logger.info(f"用户登录成功: {user.username} from {client_ip}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(expires_delta.total_seconds()),
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "avatar": user.avatar,
                "is_verified": user.is_verified
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = verify_token(token_data.refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 查找用户和会话
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 查找会话
        result = await db.execute(
            select(UserSession).where(
                UserSession.refresh_token == token_data.refresh_token,
                UserSession.is_active == True
            )
        )
        session = result.scalar_one_or_none()
        
        if not session or session.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌已过期，请重新登录"
            )
        
        # 生成新的访问令牌
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(hours=settings.JWT_EXPIRE_HOURS)
        )
        
        # 更新会话
        session.session_token = access_token
        session.last_activity_at = datetime.utcnow()
        
        await db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=token_data.refresh_token,
            expires_in=settings.JWT_EXPIRE_HOURS * 3600,
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "avatar": user.avatar,
                "is_verified": user.is_verified
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌刷新失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌刷新失败，请重新登录"
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """用户登出"""
    try:
        # 获取当前会话令牌
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            
            # 禁用当前会话
            await db.execute(
                update(UserSession)
                .where(UserSession.session_token == token)
                .values(is_active=False)
            )
        
        # 清除Cookie
        response.delete_cookie("refresh_token")
        
        await db.commit()
        
        logger.info(f"用户登出: {current_user.username}")
        
        return {"message": "登出成功"}
        
    except Exception as e:
        logger.error(f"用户登出失败: {str(e)}")
        return {"message": "登出成功"}  # 即使失败也返回成功，避免泄露信息


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return UserProfile.from_orm(current_user)


@router.put("/me", response_model=UserProfile)
async def update_profile(
    update_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户资料"""
    try:
        # 允许更新的字段
        allowed_fields = ["full_name", "phone", "avatar"]
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(current_user, field):
                setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"用户资料更新: {current_user.username}")
        
        return UserProfile.from_orm(current_user)
        
    except Exception as e:
        logger.error(f"用户资料更新失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="资料更新失败"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    try:
        # 验证当前密码
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 验证新密码强度
        if not validate_password_strength(password_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密码强度不够，请包含大小写字母、数字和特殊字符"
            )
        
        # 更新密码
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.updated_at = datetime.utcnow()
        
        # 禁用所有现有会话（强制重新登录）
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == current_user.id)
            .values(is_active=False)
        )
        
        await db.commit()
        
        logger.info(f"用户密码修改: {current_user.username}")
        
        return {"message": "密码修改成功，请重新登录"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码修改失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )

