"""
User model for the Telegram Finance Bot.

Represents a user with their Telegram information and preferences.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """Represents a bot user."""
    
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = "ru"
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_seen is None:
            self.last_seen = datetime.now()
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.telegram_id}"
    
    @property
    def display_name(self) -> str:
        """Get user's display name for messages."""
        if self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.telegram_id}"
    
    def update_last_seen(self) -> None:
        """Update the last seen timestamp."""
        self.last_seen = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for serialization."""
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language_code": self.language_code,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create user from dictionary."""
        user_data = data.copy()
        
        # Convert datetime strings back to datetime objects
        if user_data.get("created_at"):
            user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
        if user_data.get("last_seen"):
            user_data["last_seen"] = datetime.fromisoformat(user_data["last_seen"])
        
        return cls(**user_data)
    
    @classmethod
    def from_telegram_user(cls, telegram_user) -> "User":
        """Create user from Telegram User object."""
        return cls(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
        )
    
    def __str__(self) -> str:
        return f"User({self.telegram_id}, {self.display_name})"
    
    def __repr__(self) -> str:
        return (
            f"User("
            f"telegram_id={self.telegram_id}, "
            f"username={self.username!r}, "
            f"first_name={self.first_name!r}, "
            f"is_active={self.is_active}"
            f")"
        )