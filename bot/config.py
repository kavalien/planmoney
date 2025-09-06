"""
Configuration module for the Telegram Finance Bot.

Loads and validates configuration from environment variables.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Bot configuration loaded from environment variables."""
    
    # Telegram Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Authorized Users (Telegram IDs)
    AUTHORIZED_USER_1: int = int(os.getenv("AUTHORIZED_USER_1", "0"))
    AUTHORIZED_USER_2: int = int(os.getenv("AUTHORIZED_USER_2", "0"))
    
    @property
    def authorized_users(self) -> List[int]:
        """Get list of authorized user IDs."""
        users = []
        if self.AUTHORIZED_USER_1:
            users.append(self.AUTHORIZED_USER_1)
        if self.AUTHORIZED_USER_2:
            users.append(self.AUTHORIZED_USER_2)
        return users
    
    # Google Sheets Configuration
    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials/google_service_account.json")
    GOOGLE_SPREADSHEET_ID: str = os.getenv("GOOGLE_SPREADSHEET_ID", "")
    
    # Webhook Configuration (for production)
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8080"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "finance_bot.db")
    
    # Bot Configuration
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "RUB")
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Moscow")
    
    def validate(self) -> None:
        """Validate required configuration values."""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        
        if not self.authorized_users:
            raise ValueError("At least one authorized user must be configured")
        
        if not self.GOOGLE_SPREADSHEET_ID:
            raise ValueError("GOOGLE_SPREADSHEET_ID is required")
        
        if not os.path.exists(os.path.dirname(self.GOOGLE_CREDENTIALS_FILE)):
            # Create credentials directory if it doesn't exist
            os.makedirs(os.path.dirname(self.GOOGLE_CREDENTIALS_FILE), exist_ok=True)
    
    def __repr__(self) -> str:
        """String representation of config (without sensitive data)."""
        return (
            f"Config("
            f"authorized_users={len(self.authorized_users)}, "
            f"currency={self.DEFAULT_CURRENCY}, "
            f"timezone={self.TIMEZONE}, "
            f"log_level={self.LOG_LEVEL}"
            f")"
        )


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def validate_config() -> None:
    """Validate the global configuration."""
    config.validate()