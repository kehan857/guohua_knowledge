"""
扩展配置文件 - 包含外部服务集成配置
"""

from pydantic import BaseSettings, Field
from typing import List, Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "熵变智元AI销售助手"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    LOG_LEVEL: str = "INFO"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT设置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # 外部服务配置
    # GeWe微信自动化服务
    GEWE_BASE_URL: str = "https://api.gewe.com"
    GEWE_API_KEY: str = ""
    GEWE_TIMEOUT: int = 30
    GEWE_RATE_LIMIT: int = 40  # 每分钟请求限制
    
    # FastGPT AI服务
    FASTGPT_BASE_URL: str = "https://api.fastgpt.com"
    FASTGPT_API_KEY: str = ""
    FASTGPT_TIMEOUT: int = 60
    FASTGPT_MAX_CONCURRENT: int = 10  # 最大并发请求数
    
    # 监控配置
    MONITORING_ENABLED: bool = True
    MONITORING_INTERVAL: int = 30  # 监控间隔（秒）
    METRICS_RETENTION_DAYS: int = 7  # 指标保留天数
    ALERT_RETENTION_DAYS: int = 30  # 告警保留天数
    
    # WebSocket配置
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # 心跳间隔（秒）
    WEBSOCKET_TIMEOUT: int = 60  # 连接超时（秒）
    WEBSOCKET_MAX_CONNECTIONS_PER_USER: int = 5  # 每用户最大连接数
    
    # 通知配置
    EMAIL_ENABLED: bool = False
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    
    SMS_ENABLED: bool = False
    SMS_API_KEY: str = ""
    SMS_API_SECRET: str = ""
    
    # 文件存储配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "text/plain",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # 安全配置
    CORS_ORIGINS: List[str] = ["*"]
    RATE_LIMIT_REQUESTS: int = 100  # 每分钟请求限制
    RATE_LIMIT_WINDOW: int = 60  # 时间窗口（秒）
    
    # 缓存配置
    CACHE_TTL: int = 300  # 默认缓存时间（秒）
    CACHE_PREFIX: str = "ai_sales_assistant"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def is_gewe_configured(self) -> bool:
        """检查GeWe是否已配置"""
        return bool(self.GEWE_BASE_URL and self.GEWE_API_KEY)
    
    @property
    def is_fastgpt_configured(self) -> bool:
        """检查FastGPT是否已配置"""
        return bool(self.FASTGPT_BASE_URL and self.FASTGPT_API_KEY)
    
    @property
    def is_email_configured(self) -> bool:
        """检查邮件是否已配置"""
        return bool(
            self.EMAIL_ENABLED and 
            self.EMAIL_SMTP_HOST and 
            self.EMAIL_USERNAME and 
            self.EMAIL_PASSWORD
        )
    
    @property
    def is_sms_configured(self) -> bool:
        """检查短信是否已配置"""
        return bool(
            self.SMS_ENABLED and 
            self.SMS_API_KEY and 
            self.SMS_API_SECRET
        )


# 创建全局设置实例
settings = Settings()

