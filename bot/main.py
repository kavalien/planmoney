"""
Main bot module for the Telegram Finance Bot.

Entry point for the bot with aiogram setup and configuration.
"""

import sys
import os
import asyncio
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import structlog

from bot.config import get_config, validate_config
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.logging import LoggingMiddleware, setup_logging
from bot.handlers.commands import commands_router
from bot.handlers.messages import messages_router
from bot.handlers.errors import errors_router
from bot.services.google_sheets import get_sheets_service

logger = structlog.get_logger()


class FinanceBot:
    """Main bot class managing the Telegram bot lifecycle."""
    
    def __init__(self):
        """Initialize the finance bot."""
        self.config = get_config()
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.running = False
        
        logger.info("Finance bot initialized")
    
    async def setup(self):
        """Setup bot components and validate configuration."""
        try:
            # Setup logging
            setup_logging()
            logger.info("Logging configured")
            
            # Validate configuration
            validate_config()
            logger.info("Configuration validated")
            
            # Create bot instance with default properties
            self.bot = Bot(
                token=self.config.BOT_TOKEN,
                default=DefaultBotProperties(
                    parse_mode=ParseMode.MARKDOWN,
                    protect_content=False
                )
            )
            
            # Create dispatcher
            self.dp = Dispatcher()
            
            # Setup middlewares
            await self._setup_middlewares()
            
            # Setup handlers
            await self._setup_handlers()
            
            # Test Google Sheets connection
            await self._test_google_sheets()
            
            logger.info("Bot setup completed successfully")
            
        except Exception as e:
            logger.error("Bot setup failed", error=str(e))
            raise
    
    async def _setup_middlewares(self):
        """Setup bot middlewares."""
        # Authentication middleware (applied to all routers)
        auth_middleware = AuthMiddleware()
        self.dp.message.middleware(auth_middleware)
        self.dp.callback_query.middleware(auth_middleware)
        
        # Logging middleware
        logging_middleware = LoggingMiddleware()
        self.dp.message.middleware(logging_middleware)
        self.dp.callback_query.middleware(logging_middleware)
        
        logger.info("Middlewares configured")
    
    async def _setup_handlers(self):
        """Setup bot handlers."""
        # Include routers in the dispatcher
        self.dp.include_router(errors_router)    # Error handlers first
        self.dp.include_router(commands_router)  # Command handlers
        self.dp.include_router(messages_router)  # Message handlers
        
        logger.info("Handlers configured")
    
    async def _test_google_sheets(self):
        """Test Google Sheets connection."""
        try:
            sheets_service = await get_sheets_service()
            connection_ok = await sheets_service.test_connection()
            
            if connection_ok:
                logger.info("Google Sheets connection test passed")
            else:
                logger.warning("Google Sheets connection test failed")
                
        except Exception as e:
            logger.error("Google Sheets connection test error", error=str(e))
            # Don't fail the bot startup for Sheets errors
    
    async def start_polling(self):
        """Start bot in polling mode."""
        if not self.bot or not self.dp:
            raise RuntimeError("Bot not properly setup. Call setup() first.")
        
        try:
            self.running = True
            logger.info("Starting bot in polling mode")
            
            # Get bot info
            bot_info = await self.bot.get_me()
            logger.info(
                "Bot started successfully",
                bot_id=bot_info.id,
                bot_username=bot_info.username,
                bot_first_name=bot_info.first_name
            )
            
            # Start polling
            await self.dp.start_polling(
                self.bot,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error("Error during polling", error=str(e))
            raise
        finally:
            self.running = False
    
    async def start_webhook(self, webhook_url: str, webhook_port: int = 8080):
        """
        Start bot in webhook mode.
        
        Args:
            webhook_url: Webhook URL
            webhook_port: Port for webhook server
        """
        if not self.bot or not self.dp:
            raise RuntimeError("Bot not properly setup. Call setup() first.")
        
        try:
            from aiohttp import web
            from aiohttp.web_app import Application
            from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
            
            self.running = True
            logger.info("Starting bot in webhook mode", webhook_url=webhook_url, port=webhook_port)
            
            # Set webhook
            await self.bot.set_webhook(webhook_url)
            
            # Create aiohttp application
            app = web.Application()
            
            # Create webhook request handler
            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=self.dp,
                bot=self.bot,
            )
            
            # Register webhook handler
            webhook_requests_handler.register(app, path="/webhook")
            
            # Setup application
            setup_application(app, self.dp, bot=self.bot)
            
            # Start web server
            runner = web.AppRunner(app)
            await runner.setup()
            
            site = web.TCPSite(runner, host="0.0.0.0", port=webhook_port)
            await site.start()
            
            logger.info("Webhook server started", port=webhook_port)
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error("Error during webhook mode", error=str(e))
            raise
        finally:
            self.running = False
    
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping bot...")
        self.running = False
        
        if self.bot:
            # Close bot session
            await self.bot.session.close()
            logger.info("Bot session closed")
        
        logger.info("Bot stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received signal", signal=signum)
            if self.running:
                asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def create_bot() -> FinanceBot:
    """
    Create and setup a new bot instance.
    
    Returns:
        Configured FinanceBot instance
    """
    bot = FinanceBot()
    await bot.setup()
    return bot


async def run_bot():
    """Run the bot (main entry point)."""
    bot = None
    
    try:
        # Create and setup bot
        bot = await create_bot()
        
        # Setup signal handlers
        bot.setup_signal_handlers()
        
        config = get_config()
        
        # Choose between polling and webhook based on configuration
        if config.WEBHOOK_URL:
            # Webhook mode
            await bot.start_webhook(config.WEBHOOK_URL, config.WEBHOOK_PORT)
        else:
            # Polling mode
            await bot.start_polling()
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot failed to start", error=str(e))
        sys.exit(1)
    finally:
        if bot:
            await bot.stop()


def main():
    """Main function to run the bot."""
    try:
        # Run the bot
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()