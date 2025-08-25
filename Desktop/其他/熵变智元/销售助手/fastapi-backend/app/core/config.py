"""
应用配置管理
使用Pydantic Settings进行环境变量管理
"""

from pydantic import BaseSettings, Field, validator
from typing import List, Optional, Union
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "熵变智元AI销售助手"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "基于AI的智能销售助手后端服务"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 允许的主机列表
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"],
        env="ALLOWED_HOSTS"
    )
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql://entropy_user:password@localhost:5432/entropy_ai_sales",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    
    # Redis配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(default=20, env="REDIS_POOL_SIZE")
    REDIS_RETRY_ON_TIMEOUT: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    
    # Elasticsearch配置
    ELASTICSEARCH_URL: str = Field(
        default="http://localhost:9200",
        env="ELASTICSEARCH_URL"
    )
    ELASTICSEARCH_INDEX_PREFIX: str = Field(
        default="entropy_ai",
        env="ELASTICSEARCH_INDEX_PREFIX"
    )
    
    # JWT配置
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_HOURS: int = Field(default=24, env="JWT_EXPIRE_HOURS")
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_EXPIRE_DAYS")
    
    # 密码加密配置
    PWD_CONTEXT_SCHEMES: List[str] = ["bcrypt"]
    PWD_CONTEXT_DEPRECATED: str = "auto"
    
    # 文件上传配置
    UPLOAD_PATH: str = Field(default="./uploads", env="UPLOAD_PATH")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp", 
                "video/mp4", "video/avi", "audio/mp3", "audio/wav",
                "application/pdf", "text/plain"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # GeWe平台配置
    GEWE_API_ENDPOINT: str = Field(
        default="https://gewe.cn/api/v1",
        env="GEWE_API_ENDPOINT"
    )
    GEWE_TOKEN_ID: Optional[str] = Field(default=None, env="GEWE_TOKEN_ID")
    GEWE_CALLBACK_SECRET: Optional[str] = Field(default=None, env="GEWE_CALLBACK_SECRET")
    GEWE_RATE_LIMIT_PER_MINUTE: int = Field(default=40, env="GEWE_RATE_LIMIT_PER_MINUTE")
    GEWE_RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="GEWE_RATE_LIMIT_PER_HOUR")
    GEWE_REQUEST_TIMEOUT: int = Field(default=30, env="GEWE_REQUEST_TIMEOUT")
    GEWE_MAX_RETRIES: int = Field(default=3, env="GEWE_MAX_RETRIES")
    
    # AI服务配置（FastGPT）
    AI_SERVICE_ENDPOINT: str = Field(
        default="https://your-fastgpt-instance.com/api/v1",
        env="AI_SERVICE_ENDPOINT"
    )
    AI_SERVICE_KEY: Optional[str] = Field(default=None, env="AI_SERVICE_KEY")
    AI_DEFAULT_MODEL: str = Field(default="doubao-pro-32k", env="AI_DEFAULT_MODEL")
    AI_REQUEST_TIMEOUT: int = Field(default=60, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=2, env="AI_MAX_RETRIES")
    
    # AI成本配置
    AI_MODELS_PRICING: dict = Field(
        default={
            "doubao-pro-32k": {
                "input_price_per_1k": 0.008,
                "output_price_per_1k": 0.024
            },
            "gpt-4o": {
                "input_price_per_1k": 0.005,
                "output_price_per_1k": 0.015
            },
            "gpt-3.5-turbo": {
                "input_price_per_1k": 0.001,
                "output_price_per_1k": 0.002
            }
        },
        env="AI_MODELS_PRICING"
    )
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_MAX_CONNECTIONS_PER_USER: int = Field(default=5, env="WS_MAX_CONNECTIONS_PER_USER")
    WS_MESSAGE_QUEUE_SIZE: int = Field(default=1000, env="WS_MESSAGE_QUEUE_SIZE")
    
    # 任务调度配置
    SCHEDULER_TIMEZONE: str = Field(default="Asia/Shanghai", env="SCHEDULER_TIMEZONE")
    SCHEDULER_MAX_WORKERS: int = Field(default=10, env="SCHEDULER_MAX_WORKERS")
    
    # 消息队列配置（使用Redis实现）
    TASK_QUEUE_PREFIX: str = Field(default="entropy_tasks", env="TASK_QUEUE_PREFIX")
    TASK_RESULT_EXPIRE: int = Field(default=3600, env="TASK_RESULT_EXPIRE")  # 1小时
    
    # 缓存配置
    CACHE_EXPIRE_TIME: int = Field(default=3600, env="CACHE_EXPIRE_TIME")  # 1小时
    CACHE_PREFIX: str = Field(default="entropy_cache", env="CACHE_PREFIX")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # 秒
    
    # 监控配置
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # 邮件配置
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    EMAIL_FROM: Optional[str] = Field(default=None, env="EMAIL_FROM")
    
    # 短信配置（可选）
    SMS_PROVIDER: Optional[str] = Field(default=None, env="SMS_PROVIDER")
    SMS_API_KEY: Optional[str] = Field(default=None, env="SMS_API_KEY")
    SMS_API_SECRET: Optional[str] = Field(default=None, env="SMS_API_SECRET")
    
    # 安全配置
    SECURITY_HEADERS_ENABLED: bool = Field(default=True, env="SECURITY_HEADERS_ENABLED")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    SESSION_COOKIE_SECURE: bool = Field(default=False, env="SESSION_COOKIE_SECURE")
    SESSION_COOKIE_HTTPONLY: bool = Field(default=True, env="SESSION_COOKIE_HTTPONLY")
    
    # 日志配置
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_FILE_PATH: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    LOG_MAX_BYTES: int = Field(default=10485760, env="LOG_MAX_BYTES")  # 10MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Sentry配置（错误监控）
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: Optional[str] = Field(default=None, env="SENTRY_ENVIRONMENT")
    
    # 验证器
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        valid_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v.lower()
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @validator("REDIS_URL")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a Redis URL")
        return v
    
    # 属性方法
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def upload_path_obj(self) -> Path:
        """上传路径对象"""
        path = Path(self.UPLOAD_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def database_config(self) -> dict:
        """数据库配置字典"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.DATABASE_POOL_TIMEOUT,
            "echo": self.DEBUG
        }
    
    @property
    def redis_config(self) -> dict:
        """Redis配置字典"""
        return {
            "url": self.REDIS_URL,
            "max_connections": self.REDIS_POOL_SIZE,
            "retry_on_timeout": self.REDIS_RETRY_ON_TIMEOUT,
            "decode_responses": True
        }
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 配置验证函数
def validate_config():
    """验证配置的完整性"""
    errors = []
    
    # 生产环境必须配置项检查
    if settings.is_production:
        required_prod_settings = [
            ("JWT_SECRET_KEY", "JWT密钥"),
            ("GEWE_TOKEN_ID", "GeWe Token"),
            ("AI_SERVICE_KEY", "AI服务密钥"),
        ]
        
        for setting_name, display_name in required_prod_settings:
            value = getattr(settings, setting_name)
            if not value or value == "your-secret-key-change-in-production":
                errors.append(f"生产环境必须配置 {display_name} ({setting_name})")
    
    # 邮件配置完整性检查
    if settings.SMTP_HOST:
        required_email_settings = ["SMTP_USER", "SMTP_PASSWORD", "EMAIL_FROM"]
        for setting_name in required_email_settings:
            if not getattr(settings, setting_name):
                errors.append(f"配置了SMTP_HOST，必须同时配置 {setting_name}")
    
    # 文件路径检查
    try:
        settings.upload_path_obj  # 触发路径创建
    except Exception as e:
        errors.append(f"无法创建上传目录: {e}")
    
    if errors:
        raise ValueError(f"配置验证失败:\n" + "\n".join(f"- {error}" for error in errors))
    
    return True


# 导出常用配置
__all__ = ["settings", "validate_config"]

