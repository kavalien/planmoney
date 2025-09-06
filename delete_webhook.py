#!/usr/bin/env python3
"""
Script to delete webhook for Telegram bot
"""

import asyncio
from aiogram import Bot
import sys
import os

# Add project root to path
sys.path.insert(0, '.')

from bot.config import get_config

async def delete_webhook():
    """Delete the webhook for the bot."""
    try:
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        print("🔧 Удаляю webhook...")
        
        # Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        
        print("✅ Webhook удален успешно!")
        
        # Get bot info to verify
        me = await bot.get_me()
        print(f"🤖 Бот: @{me.username} ({me.first_name})")
        
        await bot.session.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(delete_webhook())