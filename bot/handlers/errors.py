"""
Error handlers for the Telegram Finance Bot.

Centralized error handling and user-friendly error messages.
"""

import traceback
from typing import Any
from aiogram import Router
from aiogram.types import ErrorEvent, Message
import structlog

from ..services.google_sheets import GoogleSheetsError
from ..utils.validators import ValidationError

logger = structlog.get_logger()

# Create router for error handlers
errors_router = Router()


@errors_router.error()
async def global_error_handler(event: ErrorEvent):
    """
    Global error handler for all unhandled exceptions.
    
    Args:
        event: Error event containing exception information
    """
    exception = event.exception
    update = event.update
    
    # Extract user information if available
    user_id = None
    chat_id = None
    message_text = None
    
    if update.message:
        if update.message.from_user:
            user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        message_text = update.message.text
    elif update.callback_query:
        if update.callback_query.from_user:
            user_id = update.callback_query.from_user.id
        if update.callback_query.message:
            chat_id = update.callback_query.message.chat.id
    
    # Log the error with context
    logger.error(
        "Unhandled bot error",
        error_type=type(exception).__name__,
        error_message=str(exception),
        user_id=user_id,
        chat_id=chat_id,
        message_text=message_text[:100] if message_text else None,
        traceback=traceback.format_exc()
    )
    
    # Try to send user-friendly error message
    if chat_id:
        try:
            await send_error_message(chat_id, exception, update)
        except Exception as send_error:
            logger.error(
                "Failed to send error message to user",
                chat_id=chat_id,
                send_error=str(send_error)
            )
    
    return True  # Mark error as handled


async def send_error_message(chat_id: int, exception: Exception, update: Any):
    """
    Send appropriate error message to user based on exception type.
    
    Args:
        chat_id: Chat ID to send message to
        exception: The exception that occurred
        update: Update object from Telegram
    """
    from aiogram import Bot
    from ..config import get_config
    
    config = get_config()
    bot = Bot(token=config.BOT_TOKEN)
    
    try:
        error_message = get_user_friendly_error_message(exception)
        await bot.send_message(chat_id, error_message)
    finally:
        await bot.session.close()


def get_user_friendly_error_message(exception: Exception) -> str:
    """
    Convert technical exception to user-friendly message.
    
    Args:
        exception: The exception that occurred
        
    Returns:
        User-friendly error message
    """
    exception_type = type(exception).__name__
    
    # Handle specific exception types
    if isinstance(exception, GoogleSheetsError):
        return (
            "📊 Ошибка при работе с Google Таблицами.\n\n"
            "Возможные причины:\n"
            "• Проблемы с подключением к интернету\n"
            "• Таблица недоступна\n"
            "• Превышен лимит запросов\n\n"
            "💡 Попробуйте повторить операцию через несколько минут."
        )
    
    elif isinstance(exception, ValidationError):
        return (
            f"❌ Ошибка валидации данных:\n{str(exception)}\n\n"
            "💡 Проверьте правильность введенных данных."
        )
    
    elif exception_type in ['NetworkError', 'TimeoutError', 'ConnectionError']:
        return (
            "🌐 Проблемы с сетью.\n\n"
            "💡 Проверьте подключение к интернету и попробуйте снова."
        )
    
    elif exception_type in ['PermissionError', 'Forbidden']:
        return (
            "🔒 Недостаточно прав для выполнения операции.\n\n"
            "💡 Обратитесь к администратору бота."
        )
    
    elif exception_type in ['ValueError', 'TypeError']:
        return (
            "📝 Ошибка в формате данных.\n\n"
            "💡 Проверьте правильность написания сообщения.\n"
            "Используйте команду /help для справки."
        )
    
    elif 'rate' in str(exception).lower() or 'limit' in str(exception).lower():
        return (
            "⏱️ Слишком много запросов.\n\n"
            "💡 Подождите немного и попробуйте снова."
        )
    
    else:
        # Generic error message for unknown exceptions
        return (
            "❌ Произошла неожиданная ошибка.\n\n"
            "💡 Попробуйте:\n"
            "• Повторить операцию\n"
            "• Перезапустить бота командой /start\n"
            "• Обратиться к администратору если проблема повторяется"
        )


class BotErrorHandler:
    """Class for handling bot-specific errors."""
    
    @staticmethod
    async def handle_transaction_error(message: Message, error: Exception):
        """
        Handle errors during transaction processing.
        
        Args:
            message: Original message
            error: Exception that occurred
        """
        logger.error(
            "Transaction processing error",
            user_id=message.from_user.id if message.from_user else None,
            error=str(error),
            error_type=type(error).__name__
        )
        
        if isinstance(error, GoogleSheetsError):
            error_text = (
                "📊 Не удалось сохранить транзакцию в Google Таблицы.\n\n"
                "💡 Ваши данные:\n"
                f"📝 {message.text}\n\n"
                "Попробуйте отправить снова через несколько минут."
            )
        elif isinstance(error, ValidationError):
            error_text = (
                f"❌ Ошибка в данных транзакции:\n{str(error)}\n\n"
                "💡 Попробуйте написать транзакцию по-другому."
            )
        else:
            error_text = (
                "❌ Ошибка при обработке транзакции.\n\n"
                "💡 Попробуйте:\n"
                "• Написать транзакцию заново\n"
                "• Проверить формат сообщения\n"
                "• Использовать команду /help"
            )
        
        await message.answer(error_text)
    
    @staticmethod
    async def handle_command_error(message: Message, error: Exception):
        """
        Handle errors during command processing.
        
        Args:
            message: Original message
            error: Exception that occurred
        """
        logger.error(
            "Command processing error",
            user_id=message.from_user.id if message.from_user else None,
            command=message.text,
            error=str(error),
            error_type=type(error).__name__
        )
        
        error_text = (
            f"❌ Ошибка при выполнении команды {message.text}.\n\n"
            "💡 Попробуйте выполнить команду снова или используйте /help."
        )
        
        await message.answer(error_text)
    
    @staticmethod
    async def handle_sheets_connection_error():
        """Handle Google Sheets connection errors."""
        logger.error("Google Sheets connection failed")
        return (
            "📊 Не удается подключиться к Google Таблицам.\n\n"
            "Возможные причины:\n"
            "• Проблемы с интернет-соединением\n"
            "• Неправильные настройки API\n"
            "• Таблица недоступна\n\n"
            "💡 Обратитесь к администратору."
        )


# Helper function to safely execute async operations
async def safe_execute(operation, error_handler=None, *args, **kwargs):
    """
    Safely execute an async operation with error handling.
    
    Args:
        operation: Async function to execute
        error_handler: Optional error handler function
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
    
    Returns:
        Operation result or None if error occurred
    """
    try:
        return await operation(*args, **kwargs)
    except Exception as e:
        logger.error(
            "Safe execution failed",
            operation=operation.__name__,
            error=str(e),
            error_type=type(e).__name__
        )
        
        if error_handler:
            await error_handler(e)
        
        return None


# Error categories for monitoring
class ErrorCategories:
    """Categories for error classification."""
    
    NETWORK = "network"
    VALIDATION = "validation"
    GOOGLE_SHEETS = "google_sheets"
    AUTHORIZATION = "authorization"
    PARSING = "parsing"
    UNKNOWN = "unknown"
    
    @classmethod
    def categorize_error(cls, exception: Exception) -> str:
        """
        Categorize exception into error categories.
        
        Args:
            exception: Exception to categorize
            
        Returns:
            Error category string
        """
        exception_type = type(exception).__name__.lower()
        error_message = str(exception).lower()
        
        if isinstance(exception, GoogleSheetsError):
            return cls.GOOGLE_SHEETS
        elif isinstance(exception, ValidationError):
            return cls.VALIDATION
        elif any(keyword in exception_type for keyword in ['network', 'connection', 'timeout']):
            return cls.NETWORK
        elif any(keyword in error_message for keyword in ['auth', 'permission', 'forbidden']):
            return cls.AUTHORIZATION
        elif any(keyword in exception_type for keyword in ['value', 'type', 'parse']):
            return cls.PARSING
        else:
            return cls.UNKNOWN