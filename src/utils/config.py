"""Print Hub Configuration."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Print Hub"
    app_env: str = "development"  # development, staging, production
    debug: bool = False
    
    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    @property
    def redis_url(self) -> str:
        """Build Redis URL from components."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Telegram Bot
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")
    telegram_admin_ids: list[int] = Field(default_factory=list, description="List of admin Telegram IDs")
    
    @property
    def is_admin(self, telegram_id: int) -> bool:
        """Check if Telegram ID belongs to admin."""
        return telegram_id in self.telegram_admin_ids
    
    # Payment Provider
    payment_provider: str = "yookassa"  # yookassa, cloudpayments, etc.
    payment_secret_key: Optional[str] = Field(None, description="Payment provider secret key")
    payment_shop_id: Optional[str] = Field(None, description="Payment provider shop ID")
    payment_webhook_secret: Optional[str] = Field(None, description="Payment webhook verification secret")
    
    # File Storage
    file_storage_path: str = "/app/storage/files"
    max_file_size_mb: int = 50
    file_retention_days: int = 7
    
    # Print Agent
    print_agent_secret: str = Field(..., description="Secret for Print Agent authentication")
    print_agent_heartbeat_timeout_seconds: int = 60
    
    # Pricing (defaults, can be overridden via DB)
    default_price_bw_per_page: float = 10.0
    default_price_color_per_page: float = 15.0
    default_price_photo_per_page: float = 20.0
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT/signing")
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance (to be initialized after loading)
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings
