"""
Command handlers for the Telegram Finance Bot.

Handles bot commands like /start, /help, /stats, etc.
"""

from datetime import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import structlog

from ..models.user import User
from ..models.transaction import TransactionType, ExpenseCategory, IncomeCategory
from ..services.google_sheets import get_sheets_service
from ..utils.categories import get_all_categories

logger = structlog.get_logger()

# Create router for command handlers
commands_router = Router()


@commands_router.message(Command("start"))
async def cmd_start(message: Message, user: User):
    """
    Handle /start command - welcome new users.
    
    Args:
        message: Telegram message
        user: Authorized user
    """
    logger.info("Start command received", user_id=user.telegram_id)
    
    welcome_text = f"""
👋 Привет, {user.display_name}!

Добро пожаловать в бота для учета семейных финансов! 💰

🔍 **Как пользоваться:**
• Просто пишите о своих тратах: "потратил 500 руб на продукты"
• Или о доходах: "получил 25000 руб зарплата"
• Бот автоматически определит категорию и запишет в таблицу

📋 **Доступные команды:**
/help - справка по использованию
/stats - статистика за текущий месяц
/categories - список категорий
/balance - текущий баланс

💡 **Примеры сообщений:**
• "купил кофе 150р"
• "такси 300 рублей"
• "получил подработку 5000 руб"
• "500₽ продукты в Пятерочке"

Начинайте вести учет финансов прямо сейчас! 🚀
"""
    
    await message.answer(welcome_text)


@commands_router.message(Command("help"))
async def cmd_help(message: Message, user: User):
    """
    Handle /help command - show usage instructions.
    
    Args:
        message: Telegram message
        user: Authorized user
    """
    logger.info("Help command received", user_id=user.telegram_id)
    
    help_text = """
📖 **Справка по использованию бота**

🎯 **Основные функции:**
Бот автоматически распознает ваши сообщения о тратах и доходах, определяет категорию и сохраняет в Google Таблицы.

💸 **Примеры сообщений о тратах:**
• "потратил 500 руб на продукты"
• "купила кофе 150р"
• "такси 300 рублей"
• "500₽ продукты в Пятерочке"
• "оплатил интернет 800 руб"

💰 **Примеры сообщений о доходах:**
• "получил зарплату 50000 руб"
• "подработка 5000р"
• "+10000 руб премия"

🏷️ **Категории автоматически определяются:**
• Продукты питания 🛒
• Транспорт 🚗
• Развлечения 🎉
• Одежда 👕
• Здоровье/медицина 🏥
• Коммунальные услуги 🏠
• И другие...

📋 **Команды:**
/start - приветствие и инструкция
/help - эта справка
/stats - статистика за месяц
/categories - все категории
/balance - текущий баланс

❓ **Если бот не понял ваше сообщение:**
Попробуйте написать четче, указав сумму и описание.
Например: "потратил 1000 руб на еду"
"""
    
    await message.answer(help_text)


@commands_router.message(Command("categories"))
async def cmd_categories(message: Message, user: User):
    """
    Handle /categories command - show all available categories.
    
    Args:
        message: Telegram message
        user: Authorized user
    """
    logger.info("Categories command received", user_id=user.telegram_id)
    
    categories = get_all_categories()
    
    categories_text = "📂 **Доступные категории:**\n\n"
    
    # Expense categories
    categories_text += "💸 **Расходы:**\n"
    for category in categories[TransactionType.EXPENSE]:
        emoji = get_category_emoji(category)
        categories_text += f"• {emoji} {category}\n"
    
    categories_text += "\n💰 **Доходы:**\n"
    for category in categories[TransactionType.INCOME]:
        emoji = get_category_emoji(category)
        categories_text += f"• {emoji} {category}\n"
    
    categories_text += "\n💡 Категории определяются автоматически на основе ключевых слов в вашем сообщении."
    
    await message.answer(categories_text)


@commands_router.message(Command("stats"))
async def cmd_stats(message: Message, user: User):
    """
    Handle /stats command - show monthly statistics.
    
    Args:
        message: Telegram message
        user: Authorized user
    """
    logger.info("Stats command received", user_id=user.telegram_id)
    
    try:
        # Get current month stats
        now = datetime.now()
        sheets_service = await get_sheets_service()
        summary = await sheets_service.get_monthly_summary(now.year, now.month)
        
        if summary["transaction_count"] == 0:
            await message.answer("📊 Статистика за текущий месяц пуста.\nНачните добавлять транзакции!")
            return
        
        stats_text = f"📊 **Статистика за {now.strftime('%B %Y')}**\n\n"
        
        # Main stats
        stats_text += f"💰 Доходы: +{summary['total_income']:,.2f} ₽\n"
        stats_text += f"💸 Расходы: -{summary['total_expenses']:,.2f} ₽\n"
        stats_text += f"📈 Баланс: {summary['net_amount']:+,.2f} ₽\n"
        stats_text += f"📝 Операций: {summary['transaction_count']}\n\n"
        
        # Top categories
        if summary["categories"]:
            stats_text += "🏷️ **Топ категории:**\n"
            sorted_categories = sorted(
                summary["categories"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            for category, amount in sorted_categories:
                emoji = get_category_emoji(category)
                stats_text += f"• {emoji} {category}: {amount:,.2f} ₽\n"
        
        await message.answer(stats_text)
        
    except Exception as e:
        logger.error("Error getting stats", error=str(e))
        await message.answer("❌ Ошибка при получении статистики. Попробуйте позже.")


@commands_router.message(Command("balance"))
async def cmd_balance(message: Message, user: User):
    """
    Handle /balance command - show current balance.
    
    Args:
        message: Telegram message
        user: Authorized user
    """
    logger.info("Balance command received", user_id=user.telegram_id)
    
    try:
        # Get current month balance
        now = datetime.now()
        sheets_service = await get_sheets_service()
        summary = await sheets_service.get_monthly_summary(now.year, now.month)
        
        balance_text = f"💰 **Баланс за {now.strftime('%B %Y')}**\n\n"
        balance_text += f"📊 Текущий баланс: **{summary['net_amount']:+,.2f} ₽**\n\n"
        balance_text += f"💰 Доходы: +{summary['total_income']:,.2f} ₽\n"
        balance_text += f"💸 Расходы: -{summary['total_expenses']:,.2f} ₽\n"
        
        # Add emoji based on balance
        if summary['net_amount'] > 0:
            balance_text += "\n✅ Отличная работа! Доходы превышают расходы."
        elif summary['net_amount'] == 0:
            balance_text += "\n⚖️ Доходы равны расходам."
        else:
            balance_text += "\n⚠️ Расходы превышают доходы."
        
        await message.answer(balance_text)
        
    except Exception as e:
        logger.error("Error getting balance", error=str(e))
        await message.answer("❌ Ошибка при получении баланса. Попробуйте позже.")


def get_category_emoji(category: str) -> str:
    """
    Get emoji for category.
    
    Args:
        category: Category name
        
    Returns:
        Emoji string
    """
    category_emojis = {
        # Expense categories
        "Продукты питания": "🛒",
        "Транспорт": "🚗", 
        "Развлечения": "🎉",
        "Одежда": "👕",
        "Здоровье/медицина": "🏥",
        "Коммунальные услуги": "🏠",
        "Прочие расходы": "💳",
        # Income categories
        "Зарплата": "💼",
        "Подработка": "🔧",
        "Прочие доходы": "💰",
    }
    return category_emojis.get(category, "📝")