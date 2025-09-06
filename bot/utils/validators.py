"""
Validators utility for the Telegram Finance Bot.

Provides validation functions for user input and transaction data.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Tuple
from datetime import datetime

from ..models.transaction import TransactionType, ExpenseCategory, IncomeCategory


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class TransactionValidator:
    """Validates transaction data and user input."""
    
    # Amount limits
    MIN_AMOUNT = Decimal('0.01')
    MAX_AMOUNT = Decimal('1000000.00')
    
    # Text length limits
    MAX_DESCRIPTION_LENGTH = 200
    MIN_DESCRIPTION_LENGTH = 1
    
    def __init__(self):
        """Initialize validator with patterns and rules."""
        # Valid currency codes
        self.valid_currencies = {'RUB', 'USD', 'EUR'}
        
        # Valid category names
        self.valid_expense_categories = {category.value for category in ExpenseCategory}
        self.valid_income_categories = {category.value for category in IncomeCategory}
        
        # Prohibited words/patterns
        self.prohibited_patterns = [
            re.compile(r'\b(?:спам|реклама|ссылка|http|www\.)\b', re.IGNORECASE),
            re.compile(r'[<>{}[\]\\]'),  # HTML/script-like characters
        ]
    
    def validate_amount(self, amount: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validate transaction amount.
        
        Args:
            amount: Amount to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(amount, Decimal):
            try:
                amount = Decimal(str(amount))
            except (InvalidOperation, ValueError):
                return False, "Сумма должна быть числом"
        
        if amount < self.MIN_AMOUNT:
            return False, f"Сумма должна быть не менее {self.MIN_AMOUNT} руб"
        
        if amount > self.MAX_AMOUNT:
            return False, f"Сумма должна быть не более {self.MAX_AMOUNT:,.0f} руб"
        
        # Check for reasonable decimal places
        if amount.as_tuple().exponent < -2:
            return False, "Сумма может содержать максимум 2 десятичных знака"
        
        return True, None
    
    def validate_transaction_type(self, transaction_type: TransactionType) -> Tuple[bool, Optional[str]]:
        """
        Validate transaction type.
        
        Args:
            transaction_type: Transaction type to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(transaction_type, TransactionType):
            return False, "Неверный тип транзакции"
        
        return True, None
    
    def validate_category(self, category: str, transaction_type: TransactionType) -> Tuple[bool, Optional[str]]:
        """
        Validate transaction category.
        
        Args:
            category: Category to validate
            transaction_type: Type of transaction
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not category or not isinstance(category, str):
            return False, "Категория обязательна"
        
        if transaction_type == TransactionType.EXPENSE:
            if category not in self.valid_expense_categories:
                return False, f"Неверная категория расхода: {category}"
        else:
            if category not in self.valid_income_categories:
                return False, f"Неверная категория дохода: {category}"
        
        return True, None
    
    def validate_description(self, description: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate transaction description.
        
        Args:
            description: Description to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if description is None:
            return True, None  # Description is optional
        
        if not isinstance(description, str):
            return False, "Описание должно быть текстом"
        
        description = description.strip()
        
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            return True, None  # Empty description is OK
        
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            return False, f"Описание слишком длинное (максимум {self.MAX_DESCRIPTION_LENGTH} символов)"
        
        # Check for prohibited content
        for pattern in self.prohibited_patterns:
            if pattern.search(description):
                return False, "Описание содержит недопустимые символы или слова"
        
        return True, None
    
    def validate_currency(self, currency: str) -> Tuple[bool, Optional[str]]:
        """
        Validate currency code.
        
        Args:
            currency: Currency code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not currency or not isinstance(currency, str):
            return False, "Валюта обязательна"
        
        currency = currency.upper()
        
        if currency not in self.valid_currencies:
            return False, f"Неподдерживаемая валюта: {currency}"
        
        return True, None
    
    def validate_user_id(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Validate Telegram user ID.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(user_id, int):
            return False, "ID пользователя должен быть числом"
        
        if user_id <= 0:
            return False, "ID пользователя должен быть положительным числом"
        
        # Telegram user IDs are typically large positive integers
        if user_id > 2**63 - 1:  # Max value for signed 64-bit integer
            return False, "Слишком большой ID пользователя"
        
        return True, None
    
    def validate_date(self, date: datetime) -> Tuple[bool, Optional[str]]:
        """
        Validate transaction date.
        
        Args:
            date: Date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(date, datetime):
            return False, "Дата должна быть объектом datetime"
        
        now = datetime.now()
        
        # Check if date is not too far in the future
        if date > now:
            time_diff = date - now
            if time_diff.total_seconds() > 3600:  # 1 hour tolerance
                return False, "Дата не может быть в будущем"
        
        # Check if date is not too far in the past (1 year)
        if date < datetime(now.year - 1, now.month, now.day):
            return False, "Дата слишком старая (максимум 1 год назад)"
        
        return True, None
    
    def validate_transaction(self, user_id: int, amount: Decimal, transaction_type: TransactionType, 
                           category: str, description: Optional[str] = None, 
                           currency: str = "RUB", date: Optional[datetime] = None) -> List[str]:
        """
        Validate complete transaction data.
        
        Args:
            user_id: User ID
            amount: Transaction amount
            transaction_type: Type of transaction
            category: Transaction category
            description: Optional description
            currency: Currency code
            date: Transaction date
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate each field
        validations = [
            self.validate_user_id(user_id),
            self.validate_amount(amount),
            self.validate_transaction_type(transaction_type),
            self.validate_category(category, transaction_type),
            self.validate_description(description),
            self.validate_currency(currency),
        ]
        
        if date:
            validations.append(self.validate_date(date))
        
        # Collect all errors
        for is_valid, error_message in validations:
            if not is_valid and error_message:
                errors.append(error_message)
        
        return errors
    
    def is_valid_transaction(self, user_id: int, amount: Decimal, transaction_type: TransactionType,
                           category: str, description: Optional[str] = None,
                           currency: str = "RUB", date: Optional[datetime] = None) -> bool:
        """
        Check if transaction data is valid.
        
        Args:
            user_id: User ID
            amount: Transaction amount
            transaction_type: Type of transaction
            category: Transaction category
            description: Optional description
            currency: Currency code
            date: Transaction date
            
        Returns:
            True if transaction is valid
        """
        errors = self.validate_transaction(user_id, amount, transaction_type, category, 
                                         description, currency, date)
        return len(errors) == 0


class MessageValidator:
    """Validates user messages and input."""
    
    def __init__(self):
        """Initialize message validator."""
        self.max_message_length = 1000
        self.min_message_length = 1
    
    def validate_text_message(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate text message.
        
        Args:
            text: Message text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not isinstance(text, str):
            return False, "Сообщение не может быть пустым"
        
        text = text.strip()
        
        if len(text) < self.min_message_length:
            return False, "Сообщение слишком короткое"
        
        if len(text) > self.max_message_length:
            return False, f"Сообщение слишком длинное (максимум {self.max_message_length} символов)"
        
        return True, None
    
    def is_command_message(self, text: str) -> bool:
        """
        Check if message is a bot command.
        
        Args:
            text: Message text
            
        Returns:
            True if message starts with /
        """
        return text.strip().startswith('/')


# Global validator instances
transaction_validator = TransactionValidator()
message_validator = MessageValidator()


def validate_transaction_data(user_id: int, amount: Decimal, transaction_type: TransactionType,
                            category: str, description: Optional[str] = None,
                            currency: str = "RUB", date: Optional[datetime] = None) -> List[str]:
    """
    Validate transaction data and return list of errors.
    
    Returns:
        List of error messages (empty if valid)
    """
    return transaction_validator.validate_transaction(user_id, amount, transaction_type, 
                                                    category, description, currency, date)


def is_valid_transaction_data(user_id: int, amount: Decimal, transaction_type: TransactionType,
                            category: str, description: Optional[str] = None,
                            currency: str = "RUB", date: Optional[datetime] = None) -> bool:
    """
    Check if transaction data is valid.
    
    Returns:
        True if transaction is valid
    """
    return transaction_validator.is_valid_transaction(user_id, amount, transaction_type,
                                                    category, description, currency, date)


def validate_message_text(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate message text.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    return message_validator.validate_text_message(text)