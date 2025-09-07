"""
Message handlers for the Telegram Finance Bot.

Handles text messages for transaction processing.
"""

from aiogram.types import Message
from aiogram import Router
from decimal import Decimal
import structlog

from ..models.user import User
from ..models.transaction import Transaction, TransactionType
from ..utils.parser import parse_transaction_message, is_transaction_message
from ..utils.validators import validate_transaction_data
from ..services.google_sheets import add_transaction_to_sheets

logger = structlog.get_logger()

# Create router for message handlers
messages_router = Router()


@messages_router.message()
async def handle_text_message(message: Message, user: User, chat_type: str = None):
    """
    Handle text messages that might contain transaction information.
    
    Args:
        message: Telegram message
        user: Authorized user
        chat_type: Type of chat (private, group, supergroup)
    """
    # Only process text messages
    if not message.text:
        return await handle_other_messages(message, user, chat_type)
    
    text = message.text.strip()
    
    logger.info(
        "Processing text message", 
        user_id=user.telegram_id, 
        text_length=len(text),
        chat_type=chat_type
    )
    
    # Skip if message is empty or too short
    if len(text) < 3:
        return
    
    # Check if this looks like a transaction message
    if not is_transaction_message(text):
        logger.debug("Message does not appear to be a transaction", user_id=user.telegram_id)
        await handle_non_transaction_message(message, user, chat_type)
        return
    
    # Parse the transaction
    parsed = parse_transaction_message(text)
    
    logger.info(
        "Parsed transaction message",
        user_id=user.telegram_id,
        amount=str(parsed.amount) if parsed.amount else None,
        transaction_type=parsed.transaction_type.value if parsed.transaction_type else None,
        category=parsed.category,
        confidence=parsed.confidence
    )
    
    # Check if parsing was successful
    if not parsed.amount or not parsed.transaction_type:
        await handle_unclear_message(message, user, parsed, chat_type)
        return
    
    # Check if confidence is too low
    if parsed.confidence < 0.5:
        await handle_low_confidence_message(message, user, parsed, chat_type)
        return
    
    # Create transaction object
    transaction = Transaction(
        user_id=user.telegram_id,
        amount=parsed.amount,
        transaction_type=parsed.transaction_type,
        category=parsed.category or "Прочие",
        description=parsed.description,
        currency=parsed.currency,
        telegram_message_id=message.message_id
    )
    
    # Validate transaction data
    validation_errors = validate_transaction_data(
        transaction.user_id,
        transaction.amount,
        transaction.transaction_type,
        transaction.category,
        transaction.description,
        transaction.currency,
        transaction.date
    )
    
    if validation_errors:
        logger.warning("Transaction validation failed", errors=validation_errors)
        await message.answer(
            f"❌ Ошибка в данных транзакции:\n" + "\n".join(f"• {error}" for error in validation_errors)
        )
        return
    
    # Save to Google Sheets
    try:
        row_number = await add_transaction_to_sheets(transaction)
        transaction.spreadsheet_row = row_number
        
        if row_number > 0:
            # Send confirmation with Google Sheets info
            await send_transaction_confirmation(message, transaction, user, chat_type)
        else:
            # Send confirmation without Google Sheets (service unavailable)
            await send_transaction_confirmation_no_sheets(message, transaction, user, chat_type)
        
        # Transaction processed successfully
        logger.info(
            "Transaction processed successfully",
            user_id=user.telegram_id,
            amount=str(transaction.amount),
            category=transaction.category,
            row_number=row_number,
            sheets_available=row_number > 0
        )
        
    except Exception as e:
        logger.error("Failed to save transaction", error=str(e))
        await message.answer(
            "❌ Ошибка при сохранении транзакции в Google Таблицы.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def handle_non_transaction_message(message: Message, user: User, chat_type: str = None):
    """
    Handle messages that don't appear to be transactions.
    
    Args:
        message: Telegram message
        user: Authorized user
        chat_type: Type of chat
    """
    # For now, just ignore non-transaction messages in groups
    # In private chats, we might want to provide help
    logger.debug(
        "Ignoring non-transaction message", 
        user_id=user.telegram_id,
        chat_type=chat_type
    )


async def handle_unclear_message(message: Message, user: User, parsed, chat_type: str = None):
    """
    Handle messages where transaction parsing was unclear.
    
    Args:
        message: Telegram message
        user: Authorized user
        parsed: Parsed transaction data
        chat_type: Type of chat
    """
    logger.info("Handling unclear transaction message", user_id=user.telegram_id, chat_type=chat_type)
    
    unclear_text = "🤔 Не совсем понял ваше сообщение.\n\n"
    
    if not parsed.amount:
        unclear_text += "💰 Не удалось определить сумму. "
    if not parsed.transaction_type:
        unclear_text += "📊 Не удалось понять, это доход или расход. "
    
    unclear_text += "\n\n💡 **Примеры правильных сообщений:**\n"
    unclear_text += "• \"потратил 500 руб на продукты\"\n"
    unclear_text += "• \"получил зарплату 25000 руб\"\n"
    unclear_text += "• \"купил кофе 150р\"\n"
    unclear_text += "• \"такси 300 рублей\"\n\n"
    unclear_text += "Попробуйте написать четче, указав сумму и описание."
    
    await message.answer(unclear_text)


async def handle_low_confidence_message(message: Message, user: User, parsed, chat_type: str = None):
    """
    Handle messages with low confidence parsing.
    
    Args:
        message: Telegram message
        user: Authorized user
        parsed: Parsed transaction data
        chat_type: Type of chat
    """
    logger.info(
        "Handling low confidence transaction message", 
        user_id=user.telegram_id, 
        confidence=parsed.confidence,
        chat_type=chat_type
    )
    
    confirmation_text = f"❓ Правильно ли я понял?\n\n"
    
    if parsed.amount:
        confirmation_text += f"💰 Сумма: {parsed.amount} {parsed.currency}\n"
    if parsed.transaction_type:
        type_text = "доход" if parsed.transaction_type == TransactionType.INCOME else "расход"
        confirmation_text += f"📊 Тип: {type_text}\n"
    if parsed.category:
        confirmation_text += f"🏷️ Категория: {parsed.category}\n"
    if parsed.description:
        confirmation_text += f"📝 Описание: {parsed.description}\n"
    
    confirmation_text += "\n💡 Если неправильно, попробуйте написать четче."
    confirmation_text += "\nЕсли правильно, напишите \"да\" или \"подтверждаю\"."
    
    await message.answer(confirmation_text)


async def send_transaction_confirmation_no_sheets(message: Message, transaction: Transaction, user: User, chat_type: str = None):
    """
    Send confirmation message when Google Sheets is unavailable.
    
    Args:
        message: Original message
        transaction: Processed transaction
        user: User who made the transaction
        chat_type: Type of chat
    """
    # Add user info for group chats
    user_prefix = ""
    if chat_type in ["group", "supergroup"]:
        user_prefix = f"👤 {user.display_name}\n"
    
    confirmation_text = f"{user_prefix}✅ **Транзакция записана!**\n\n"
    confirmation_text += f"{transaction.type_emoji} {transaction.category_emoji} "
    confirmation_text += f"**{transaction.formatted_amount_with_sign}**\n"
    confirmation_text += f"🏷️ Категория: {transaction.category}\n"
    
    if transaction.description:
        confirmation_text += f"📝 Описание: {transaction.description}\n"
    
    confirmation_text += f"📅 Дата: {transaction.date.strftime('%d.%m.%Y %H:%M')}\n"
    confirmation_text += f"\n⚠️ Пока не сохранено в Google Таблицы"
    confirmation_text += f"\n🔧 Подключение восстановится автоматически"
    
    await message.answer(confirmation_text)


async def send_transaction_confirmation(message: Message, transaction: Transaction, user: User, chat_type: str = None):
    """
    Send confirmation message for successful transaction.
    
    Args:
        message: Original message
        transaction: Processed transaction
        user: User who made the transaction
        chat_type: Type of chat
    """
    # Add user info for group chats
    user_prefix = ""
    if chat_type in ["group", "supergroup"]:
        user_prefix = f"👤 {user.display_name}\n"
    
    confirmation_text = f"{user_prefix}✅ **Транзакция записана!**\n\n"
    confirmation_text += f"{transaction.type_emoji} {transaction.category_emoji} "
    confirmation_text += f"**{transaction.formatted_amount_with_sign}**\n"
    confirmation_text += f"🏷️ Категория: {transaction.category}\n"
    
    if transaction.description:
        confirmation_text += f"📝 Описание: {transaction.description}\n"
    
    confirmation_text += f"📅 Дата: {transaction.date.strftime('%d.%m.%Y %H:%M')}\n"
    
    if transaction.spreadsheet_row:
        confirmation_text += f"📊 Строка в таблице: {transaction.spreadsheet_row}"
    
    await message.answer(confirmation_text)


# Handle confirmation messages (placeholder for future implementation)


# Handle rejection messages (placeholder for future implementation)


@messages_router.message()
async def handle_other_messages(message: Message, user: User, chat_type: str = None):
    """
    Handle other types of messages (photos, documents, etc.).
    
    Args:
        message: Telegram message
        user: Authorized user
        chat_type: Type of chat
    """
    content_type = message.content_type
    
    logger.info(
        "Received non-text message", 
        user_id=user.telegram_id, 
        content_type=content_type,
        chat_type=chat_type
    )
    
    if content_type in ['photo', 'document']:
        await message.answer(
            "📷 Пока я умею обрабатывать только текстовые сообщения.\n\n"
            "💡 Напишите о своей трате или доходе текстом.\n"
            "Например: \"потратил 500 руб на продукты\""
        )
    elif content_type == 'voice':
        await message.answer(
            "🎤 Голосовые сообщения пока не поддерживаются.\n\n"
            "💡 Напишите текстом о своей трате или доходе.\n"
            "Например: \"получил зарплату 50000 руб\""
        )
    else:
        await message.answer(
            "❓ Не понимаю этот тип сообщения.\n\n"
            "💡 Напишите текстом о своих тратах или доходах.\n"
            "Используйте команду /help для справки."
        )