"""
Authentication middleware for the Telegram Finance Bot.

Ensures only authorized users can interact with the bot.
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import structlog

from ..config import get_config
from ..models.user import User

logger = structlog.get_logger()


class AuthMiddleware(BaseMiddleware):
    """Middleware for user authentication and authorization."""
    
    def __init__(self):
        """Initialize auth middleware."""
        self.config = get_config()
        self.authorized_users = set(self.config.authorized_users)
        logger.info("Auth middleware initialized", authorized_users_count=len(self.authorized_users))
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Process incoming update and check user authorization.
        
        Args:
            handler: Next handler in the chain
            event: Telegram event (Message, CallbackQuery, etc.)
            data: Handler data
            
        Returns:
            Handler result or None if user is not authorized
        """
        user_id = None
        telegram_user = None
        
        # Extract user information from different event types
        if isinstance(event, (Message, CallbackQuery)):
            if event.from_user:
                user_id = event.from_user.id
                telegram_user = event.from_user
        
        # If we couldn't get user ID, block the request
        if user_id is None:
            logger.warning("Could not extract user ID from event", event_type=type(event).__name__)
            return None
        
        # Check if user is authorized
        if user_id not in self.authorized_users:
            logger.warning(
                "Unauthorized access attempt",
                user_id=user_id,
                username=telegram_user.username if telegram_user else None,
                first_name=telegram_user.first_name if telegram_user else None
            )
            
            # Send unauthorized message for Message events
            if isinstance(event, Message):
                await event.answer(
                    "🚫 У вас нет доступа к этому боту.\n"
                    "Этот бот предназначен только для авторизованных пользователей."
                )
            
            return None
        
        # Create User object and add to data
        if telegram_user:
            user = User.from_telegram_user(telegram_user)
            user.update_last_seen()
            data["user"] = user
            
            logger.info(
                "Authorized user request",
                user_id=user_id,
                username=user.username,
                display_name=user.display_name
            )
        
        # User is authorized, continue to next handler
        return await handler(event, data)


class AdminMiddleware(BaseMiddleware):
    """Middleware for admin-only functionality (future use)."""
    
    def __init__(self, admin_user_ids: list = None):
        """
        Initialize admin middleware.
        
        Args:
            admin_user_ids: List of admin user IDs
        """
        self.admin_user_ids = set(admin_user_ids or [])
        logger.info("Admin middleware initialized", admin_count=len(self.admin_user_ids))
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Process incoming update and check admin authorization.
        
        Args:
            handler: Next handler in the chain
            event: Telegram event
            data: Handler data
            
        Returns:
            Handler result or None if user is not admin
        """
        user_id = None
        
        # Extract user ID
        if isinstance(event, (Message, CallbackQuery)):
            if event.from_user:
                user_id = event.from_user.id
        
        if user_id is None:
            return None
        
        # Check if user is admin
        if user_id not in self.admin_user_ids:
            logger.warning("Non-admin access attempt to admin function", user_id=user_id)
            
            if isinstance(event, Message):
                await event.answer("🔒 Эта функция доступна только администраторам.")
            
            return None
        
        # User is admin, continue
        data["is_admin"] = True
        return await handler(event, data)


def is_authorized_user(user_id: int) -> bool:
    """
    Check if user ID is in the authorized users list.
    
    Args:
        user_id: Telegram user ID to check
        
    Returns:
        True if user is authorized
    """
    config = get_config()
    return user_id in config.authorized_users


def get_authorized_users() -> list:
    """
    Get list of authorized user IDs.
    
    Returns:
        List of authorized user IDs
    """
    config = get_config()
    return config.authorized_users