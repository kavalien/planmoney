"""
Logging middleware for the Telegram Finance Bot.

Logs all bot interactions and provides structured logging.
"""

import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineQuery
import structlog

logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging bot interactions."""
    
    def __init__(self):
        """Initialize logging middleware."""
        logger.info("Logging middleware initialized")
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Process incoming update and log the interaction.
        
        Args:
            handler: Next handler in the chain
            event: Telegram event
            data: Handler data
            
        Returns:
            Handler result
        """
        start_time = time.time()
        
        # Extract event information
        event_info = self._extract_event_info(event)
        
        # Log incoming request
        logger.info(
            "Incoming request",
            event_type=event_info["event_type"],
            user_id=event_info.get("user_id"),
            username=event_info.get("username"),
            chat_id=event_info.get("chat_id"),
            message_text=event_info.get("message_text", "")[:100] if event_info.get("message_text") else None,
            callback_data=event_info.get("callback_data")
        )
        
        try:
            # Process the event
            result = await handler(event, data)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log successful processing
            logger.info(
                "Request processed successfully",
                event_type=event_info["event_type"],
                user_id=event_info.get("user_id"),
                processing_time_ms=round(processing_time * 1000, 2),
                result_type=type(result).__name__ if result else None
            )
            
            return result
            
        except Exception as e:
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request processing failed",
                event_type=event_info["event_type"],
                user_id=event_info.get("user_id"),
                processing_time_ms=round(processing_time * 1000, 2),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            
            # Re-raise the exception
            raise
    
    def _extract_event_info(self, event: TelegramObject) -> Dict[str, Any]:
        """
        Extract relevant information from event for logging.
        
        Args:
            event: Telegram event
            
        Returns:
            Dictionary with event information
        """
        event_info = {
            "event_type": type(event).__name__
        }
        
        if isinstance(event, Message):
            event_info.update({
                "user_id": event.from_user.id if event.from_user else None,
                "username": event.from_user.username if event.from_user else None,
                "first_name": event.from_user.first_name if event.from_user else None,
                "chat_id": event.chat.id,
                "chat_type": event.chat.type,
                "message_id": event.message_id,
                "message_text": event.text,
                "content_type": event.content_type
            })
            
            # Add specific content type information
            if event.photo:
                event_info["has_photo"] = True
            if event.document:
                event_info["has_document"] = True
            if event.voice:
                event_info["has_voice"] = True
                
        elif isinstance(event, CallbackQuery):
            event_info.update({
                "user_id": event.from_user.id if event.from_user else None,
                "username": event.from_user.username if event.from_user else None,
                "callback_data": event.data,
                "message_id": event.message.message_id if event.message else None
            })
            
        elif isinstance(event, InlineQuery):
            event_info.update({
                "user_id": event.from_user.id if event.from_user else None,
                "username": event.from_user.username if event.from_user else None,
                "query": event.query
            })
        
        return event_info


class TransactionLoggingMiddleware(BaseMiddleware):
    """Specialized middleware for logging financial transactions."""
    
    def __init__(self):
        """Initialize transaction logging middleware."""
        logger.info("Transaction logging middleware initialized")
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Process transaction-related events with enhanced logging.
        
        Args:
            handler: Next handler in the chain
            event: Telegram event
            data: Handler data
            
        Returns:
            Handler result
        """
        # Check if this is a transaction-related message
        is_transaction = False
        if isinstance(event, Message) and event.text:
            # Simple check for transaction keywords
            transaction_keywords = ['потратил', 'потратила', 'купил', 'купила', 'получил', 'получила', 'руб', '₽']
            is_transaction = any(keyword in event.text.lower() for keyword in transaction_keywords)
        
        if is_transaction:
            logger.info(
                "Processing potential transaction message",
                user_id=event.from_user.id if event.from_user else None,
                message_text=event.text[:200] if event.text else None
            )
        
        # Process the event
        result = await handler(event, data)
        
        # If a transaction was created, log it
        if "transaction" in data:
            transaction = data["transaction"]
            logger.info(
                "Transaction processed",
                user_id=transaction.user_id,
                amount=str(transaction.amount),
                transaction_type=transaction.transaction_type.value,
                category=transaction.category,
                description=transaction.description
            )
        
        return result


def setup_logging():
    """Configure structured logging for the bot."""
    import logging
    from ..config import get_config
    
    config = get_config()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set up file logging
    import os
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Logging configured", log_level=config.LOG_LEVEL, log_file=config.LOG_FILE)