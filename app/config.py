"""
Application configuration management.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for automatic validation and type conversion.
    """
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://ecommerce_user:ecommerce_pass@localhost:5432/ecommerce_db",
        alias="DATABASE_URL"
    )
    
    # Webhook security
    webhook_secret: str = Field(
        default="dev_webhook_secret_key",
        alias="WEBHOOK_SECRET"
    )
    
    # Application settings
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    
    class Config:
        # Load from .env file
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()

