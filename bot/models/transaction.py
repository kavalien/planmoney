"""
Transaction model for the Telegram Finance Bot.

Represents a financial transaction (income or expense).
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    """Type of financial transaction."""
    INCOME = "income"
    EXPENSE = "expense"


class ExpenseCategory(Enum):
    """Categories for expenses."""
    FOOD = "Продукты питания"
    TRANSPORT = "Транспорт"
    ENTERTAINMENT = "Развлечения"
    CLOTHING = "Одежда"
    HEALTH = "Здоровье/медицина"
    UTILITIES = "Коммунальные услуги"
    OTHER_EXPENSE = "Прочие расходы"


class IncomeCategory(Enum):
    """Categories for income."""
    SALARY = "Зарплата"
    SIDE_JOB = "Подработка"
    OTHER_INCOME = "Прочие доходы"


@dataclass
class Transaction:
    """Represents a financial transaction."""
    
    user_id: int
    amount: Decimal
    transaction_type: TransactionType
    category: str
    description: Optional[str] = None
    currency: str = "RUB"
    date: Optional[datetime] = None
    telegram_message_id: Optional[int] = None
    spreadsheet_row: Optional[int] = None
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.date is None:
            self.date = datetime.now()
        
        # Ensure amount is positive for expenses (will be handled in display)
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))
        
        # Validate transaction type and category
        if isinstance(self.transaction_type, str):
            self.transaction_type = TransactionType(self.transaction_type)
    
    @property
    def amount_with_sign(self) -> Decimal:
        """Get amount with appropriate sign based on transaction type."""
        if self.transaction_type == TransactionType.EXPENSE:
            return -abs(self.amount)
        else:
            return abs(self.amount)
    
    @property
    def formatted_amount(self) -> str:
        """Get formatted amount string with currency."""
        return f"{self.amount:,.2f} {self.currency}"
    
    @property
    def formatted_amount_with_sign(self) -> str:
        """Get formatted amount with sign and currency."""
        amount_with_sign = self.amount_with_sign
        sign = "+" if amount_with_sign >= 0 else "-"
        return f"{sign}{abs(amount_with_sign):,.2f} {self.currency}"
    
    @property
    def type_emoji(self) -> str:
        """Get emoji representing transaction type."""
        return "💰" if self.transaction_type == TransactionType.INCOME else "💸"
    
    @property
    def category_emoji(self) -> str:
        """Get emoji for the category."""
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
        return category_emojis.get(self.category, "📝")
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "amount": str(self.amount),
            "transaction_type": self.transaction_type.value,
            "category": self.category,
            "description": self.description,
            "currency": self.currency,
            "date": self.date.isoformat() if self.date else None,
            "telegram_message_id": self.telegram_message_id,
            "spreadsheet_row": self.spreadsheet_row,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Create transaction from dictionary."""
        transaction_data = data.copy()
        
        # Convert string amount back to Decimal
        if transaction_data.get("amount"):
            transaction_data["amount"] = Decimal(transaction_data["amount"])
        
        # Convert datetime string back to datetime object
        if transaction_data.get("date"):
            transaction_data["date"] = datetime.fromisoformat(transaction_data["date"])
        
        return cls(**transaction_data)
    
    def to_spreadsheet_row(self) -> list:
        """Convert transaction to a row for Google Sheets."""
        return [
            self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else "",
            str(self.user_id),
            self.transaction_type.value,
            str(self.amount),
            self.category,
            self.description or "",
            str(self.telegram_message_id) if self.telegram_message_id else "",
        ]
    
    def __str__(self) -> str:
        """String representation for user display."""
        return (
            f"{self.type_emoji} {self.category_emoji} "
            f"{self.formatted_amount_with_sign} - {self.category}"
            f"{f' ({self.description})' if self.description else ''}"
        )
    
    def __repr__(self) -> str:
        return (
            f"Transaction("
            f"user_id={self.user_id}, "
            f"amount={self.amount}, "
            f"type={self.transaction_type.value}, "
            f"category={self.category!r}"
            f")"
        )