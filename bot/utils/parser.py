"""
Message parser for the Telegram Finance Bot.

Extracts financial transaction information from natural language text messages.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from ..models.transaction import TransactionType
from .categories import classify_transaction_category


@dataclass
class ParsedTransaction:
    """Represents a parsed transaction from user message."""
    
    amount: Optional[Decimal] = None
    transaction_type: Optional[TransactionType] = None
    category: Optional[str] = None
    description: Optional[str] = None
    currency: str = "RUB"
    confidence: float = 0.0  # Confidence score (0-1)
    raw_text: str = ""


class MessageParser:
    """Parses transaction information from text messages."""
    
    def __init__(self):
        """Initialize the message parser with regex patterns."""
        # Amount patterns - matches numbers with various separators and currency symbols
        self.amount_patterns = [
            # Pattern: "потратил 500 руб", "500 рублей", "500р", "500₽"
            r'(?:потратил|потратила|купил|купила|заплатил|заплатила|потрачено)\s*(\d+(?:[.,]\d{1,2})?)\s*(?:руб|рубл|₽|р\b)',
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:руб|рубл|₽|р\b)',
            
            # Pattern: "получил 5000 руб", "+5000 руб"
            r'(?:получил|получила|заработал|заработала|доход|пришло)\s*(\d+(?:[.,]\d{1,2})?)\s*(?:руб|рубл|₽|р\b)',
            r'\+\s*(\d+(?:[.,]\d{1,2})?)\s*(?:руб|рубл|₽|р\b)',
            
            # Pattern: just numbers with currency
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:₽|руб|рубл)',
            
            # Pattern: numbers at the beginning or end
            r'^(\d+(?:[.,]\d{1,2})?)',
            r'(\d+(?:[.,]\d{1,2})?)$',
        ]
        
        # Income keywords that suggest this is income
        self.income_keywords = [
            'получил', 'получила', 'заработал', 'заработала', 'зарплата', 'доход', 
            'пришло', 'перевод', 'премия', 'аванс', 'подработка', 'фриланс'
        ]
        
        # Expense keywords that suggest this is an expense
        self.expense_keywords = [
            'потратил', 'потратила', 'купил', 'купила', 'заплатил', 'заплатила',
            'потрачено', 'потратили', 'оплатил', 'оплатила', 'покупка', 'трата'
        ]
        
        # Compile patterns for better performance
        self.compiled_amount_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.amount_patterns]
        self.income_pattern = re.compile(r'\b(?:' + '|'.join(self.income_keywords) + r')\b', re.IGNORECASE)
        self.expense_pattern = re.compile(r'\b(?:' + '|'.join(self.expense_keywords) + r')\b', re.IGNORECASE)
        self.plus_pattern = re.compile(r'^\s*\+', re.MULTILINE)
        self.minus_pattern = re.compile(r'^\s*-', re.MULTILINE)
    
    def extract_amount(self, text: str) -> Optional[Decimal]:
        """
        Extract monetary amount from text.
        
        Args:
            text: Text to parse
            
        Returns:
            Decimal amount or None if not found
        """
        text = text.strip()
        
        for pattern in self.compiled_amount_patterns:
            match = pattern.search(text)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    amount = Decimal(amount_str)
                    if amount > 0:
                        return amount
                except (InvalidOperation, ValueError):
                    continue
        
        return None
    
    def determine_transaction_type(self, text: str) -> Optional[TransactionType]:
        """
        Determine if transaction is income or expense based on keywords.
        
        Args:
            text: Text to analyze
            
        Returns:
            TransactionType or None if unclear
        """
        text = text.lower().strip()
        
        # Check for explicit plus/minus signs
        if self.plus_pattern.search(text):
            return TransactionType.INCOME
        if self.minus_pattern.search(text):
            return TransactionType.EXPENSE
        
        # Check for income keywords
        if self.income_pattern.search(text):
            return TransactionType.INCOME
        
        # Check for expense keywords
        if self.expense_pattern.search(text):
            return TransactionType.EXPENSE
        
        return None
    
    def clean_description(self, text: str, amount: Decimal, transaction_type: TransactionType) -> str:
        """
        Clean text to create a meaningful description.
        
        Args:
            text: Original text
            amount: Extracted amount
            transaction_type: Type of transaction
            
        Returns:
            Cleaned description string
        """
        # Remove amount and currency references
        cleaned = text
        
        # Remove amount patterns
        for pattern in self.compiled_amount_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Remove transaction type keywords
        if transaction_type == TransactionType.INCOME:
            cleaned = self.income_pattern.sub('', cleaned)
        else:
            cleaned = self.expense_pattern.sub('', cleaned)
        
        # Remove extra whitespace and common words
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\b(?:на|в|за|для|с|по|от|до|из|к|у|о|об|и|а|но|или|что|это|тот|та|то|те)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        # If description is too short or empty, return None
        if len(cleaned) < 2:
            return ""
        
        return cleaned
    
    def calculate_confidence(self, parsed: ParsedTransaction) -> float:
        """
        Calculate confidence score for parsed transaction.
        
        Args:
            parsed: Parsed transaction data
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0
        
        # Amount found
        if parsed.amount:
            confidence += 0.4
            
            # Amount seems reasonable
            if 1 <= parsed.amount <= 1000000:
                confidence += 0.1
        
        # Transaction type determined
        if parsed.transaction_type:
            confidence += 0.3
        
        # Category classified
        if parsed.category:
            confidence += 0.2
        
        # Description available
        if parsed.description and len(parsed.description) > 2:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def parse_message(self, text: str) -> ParsedTransaction:
        """
        Parse a message to extract transaction information.
        
        Args:
            text: Message text to parse
            
        Returns:
            ParsedTransaction object with extracted information
        """
        parsed = ParsedTransaction(raw_text=text)
        
        # Extract amount
        parsed.amount = self.extract_amount(text)
        
        # Determine transaction type
        parsed.transaction_type = self.determine_transaction_type(text)
        
        # If no explicit type found but amount exists, guess based on context
        if not parsed.transaction_type and parsed.amount:
            # Default to expense for most cases
            parsed.transaction_type = TransactionType.EXPENSE
        
        # Classify category if we have transaction type
        if parsed.transaction_type:
            parsed.category = classify_transaction_category(text, parsed.transaction_type)
        
        # Generate description
        if parsed.amount and parsed.transaction_type:
            parsed.description = self.clean_description(text, parsed.amount, parsed.transaction_type)
        
        # Calculate confidence
        parsed.confidence = self.calculate_confidence(parsed)
        
        return parsed
    
    def is_valid_transaction_message(self, text: str) -> bool:
        """
        Check if message contains transaction information.
        
        Args:
            text: Message text to check
            
        Returns:
            True if message appears to contain transaction info
        """
        parsed = self.parse_message(text)
        return parsed.amount is not None and parsed.confidence > 0.5


# Global parser instance
parser = MessageParser()


def parse_transaction_message(text: str) -> ParsedTransaction:
    """
    Parse transaction information from message text.
    
    Args:
        text: Message text to parse
        
    Returns:
        ParsedTransaction object
    """
    return parser.parse_message(text)


def is_transaction_message(text: str) -> bool:
    """
    Check if message contains transaction information.
    
    Args:
        text: Message text to check
        
    Returns:
        True if message appears to be a transaction
    """
    return parser.is_valid_transaction_message(text)