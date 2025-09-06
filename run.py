#!/usr/bin/env python3
"""
Startup script for the Telegram Finance Bot.

This script provides a convenient way to run the bot with various options.
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from bot.main import run_bot, create_bot
    from bot.config import get_config, validate_config
    from bot.services.google_sheets import get_sheets_service
    import structlog
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and have installed dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)

logger = structlog.get_logger()


async def test_bot_setup():
    """Test bot setup and configuration without starting."""
    print("🔧 Testing bot setup...")
    
    try:
        # Test configuration
        print("📋 Testing configuration...")
        config = get_config()
        validate_config()
        print(f"✅ Configuration valid: {config}")
        
        # Test bot creation
        print("🤖 Testing bot creation...")
        bot = await create_bot()
        print("✅ Bot created successfully")
        
        # Test Google Sheets connection
        print("📊 Testing Google Sheets connection...")
        sheets_service = await get_sheets_service()
        connection_ok = await sheets_service.test_connection()
        
        if connection_ok:
            print("✅ Google Sheets connection successful")
        else:
            print("⚠️ Google Sheets connection failed")
        
        await bot.stop()
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        sys.exit(1)


async def validate_environment():
    """Validate environment setup."""
    print("🔍 Validating environment...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️ .env file not found. Creating from template...")
        
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("📋 Created .env from .env.example")
            print("🔧 Please edit .env file with your actual values:")
            print("   - BOT_TOKEN")
            print("   - AUTHORIZED_USER_1 and AUTHORIZED_USER_2")
            print("   - GOOGLE_SPREADSHEET_ID")
            print("   - GOOGLE_CREDENTIALS_FILE path")
            return False
        else:
            print("❌ .env.example not found. Cannot create .env file.")
            return False
    
    # Check if logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs', exist_ok=True)
        print("📁 Created logs directory")
    
    # Check if credentials directory exists
    if not os.path.exists('credentials'):
        os.makedirs('credentials', exist_ok=True)
        print("📁 Created credentials directory")
        print("🔑 Please add your Google service account JSON file to credentials/")
    
    return True


def print_startup_info():
    """Print startup information."""
    print("🚀 Telegram Finance Bot")
    print("=" * 40)
    print("📖 This bot helps you track family finances")
    print("💰 It automatically categorizes your expenses and income")
    print("📊 All data is saved to Google Sheets")
    print("=" * 40)


def print_usage_examples():
    """Print usage examples."""
    print("\n💡 Usage examples after bot starts:")
    print("• Send to bot: 'потратил 500 руб на продукты'")
    print("• Send to bot: 'получил зарплату 50000 руб'")
    print("• Use commands: /start, /help, /stats, /balance")
    print("\n🔧 Bot commands:")
    print("• /start - Welcome message and instructions")
    print("• /help - Detailed help")
    print("• /stats - Monthly statistics") 
    print("• /categories - Available categories")
    print("• /balance - Current balance")


async def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Telegram Finance Bot - Track your family finances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                 # Run the bot normally
  python run.py --test          # Test setup without starting
  python run.py --validate      # Validate environment only
  python run.py --help          # Show this help
        """
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test bot setup and configuration without starting'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true', 
        help='Validate environment setup only'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Print startup info
    print_startup_info()
    
    # Validate environment first
    if not await validate_environment():
        print("\n❌ Environment validation failed.")
        print("Please configure your .env file and try again.")
        sys.exit(1)
    
    if args.validate:
        print("✅ Environment validation completed!")
        return
    
    if args.test:
        await test_bot_setup()
        return
    
    # Set verbose logging if requested
    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Print usage examples
    print_usage_examples()
    
    print("\n🚀 Starting bot...")
    print("Press Ctrl+C to stop the bot")
    print("-" * 40)
    
    try:
        # Run the bot
        await run_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)