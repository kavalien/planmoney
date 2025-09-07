#!/usr/bin/env python3
"""
Production deployment script for Railway.app
Uses webhook mode instead of polling for better performance in production.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from bot.main import create_bot, setup_handlers, setup_middlewares
from bot.config import Config
from bot.services.google_sheets import GoogleSheetsService
import structlog

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def main():
    """Main function for production deployment"""
    
    print("🚀 Starting Telegram Finance Bot (Production Mode)")
    print("=" * 50)
    
    # Validate environment
    config = Config()
    
    # Create bot and dispatcher
    bot, dp = create_bot()
    
    # Setup middlewares and handlers
    setup_middlewares(dp, config)
    setup_handlers(dp)
    
    # Initialize Google Sheets service
    logger.info("Initializing Google Sheets service...")
    sheets_service = GoogleSheetsService()
    await sheets_service.initialize()
    
    # Test Google Sheets connection
    try:
        connection_ok = await sheets_service.test_connection()
        if connection_ok:
            logger.info("Google Sheets connection test passed")
        else:
            logger.warning("Google Sheets connection test failed - continuing without sheets")
    except Exception as e:
        logger.warning("Google Sheets service unavailable", error=str(e))
    
    # Get webhook settings from environment
    webhook_host = os.getenv('RAILWAY_STATIC_URL') or os.getenv('WEBHOOK_HOST')
    webhook_port = int(os.getenv('PORT', 8000))
    webhook_path = '/webhook'
    
    if webhook_host:
        # Production mode with webhook
        webhook_url = f"https://{webhook_host}{webhook_path}"
        
        logger.info("Starting bot in webhook mode", 
                   webhook_url=webhook_url, 
                   port=webhook_port)
        
        # Set webhook
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        # Start webhook server
        from aiohttp import web
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        
        app = web.Application()
        handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        handler.register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', webhook_port)
        await site.start()
        
        logger.info("Bot started successfully in webhook mode")
        print(f"✅ Bot running at: {webhook_url}")
        print("Press Ctrl+C to stop")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await runner.cleanup()
            await bot.delete_webhook()
            
    else:
        # Fallback to polling mode
        logger.info("Starting bot in polling mode (fallback)")
        
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)