"""
Categories utility for the Telegram Finance Bot.

Automatically determines categories for transactions based on keywords and patterns.
"""

import re
from typing import List, Dict, Optional, Tuple
from ..models.transaction import ExpenseCategory, IncomeCategory, TransactionType


class CategoryClassifier:
    """Classifies transactions into categories based on text analysis."""
    
    def __init__(self):
        """Initialize the category classifier with keyword mappings."""
        self.expense_keywords = {
            ExpenseCategory.FOOD.value: [
                "продукты", "еда", "ресторан", "кафе", "столовая", "пятёрочка", "магнит", 
                "перекрёсток", "ашан", "лента", "дикси", "макдональдс", "бургер", "пицца",
                "хлеб", "молоко", "мясо", "овощи", "фрукты", "кофе", "обед", "ужин", "завтрак",
                "супермаркет", "продмаг", "grocery", "food", "restaurant", "cafe"
            ],
            ExpenseCategory.TRANSPORT.value: [
                "такси", "автобус", "метро", "транспорт", "бензин", "топливо", "заправка",
                "проезд", "билет", "яндекс", "убер", "uber", "taxi", "gas", "fuel", "metro",
                "bus", "поезд", "электричка", "тролleybus", "трамвай", "парковка", "parking"
            ],
            ExpenseCategory.ENTERTAINMENT.value: [
                "кино", "театр", "концерт", "бар", "клуб", "развлечения", "игры", "боулинг",
                "кинотеатр", "cinema", "movie", "entertainment", "party", "concert", "music",
                "игра", "steam", "playstation", "xbox", "nintendo", "книги", "книга", "book"
            ],
            ExpenseCategory.CLOTHING.value: [
                "одежда", "обувь", "куртка", "платье", "рубашка", "джинсы", "костюм", "шорты",
                "футболка", "свитер", "пальто", "сапоги", "кроссовки", "туфли", "clothes",
                "clothing", "shoes", "shirt", "dress", "jacket", "pants", "zara", "h&m"
            ],
            ExpenseCategory.HEALTH.value: [
                "аптека", "лекарства", "врач", "больница", "поликлиника", "стоматолог", "анализы",
                "медицина", "health", "medicine", "doctor", "hospital", "pharmacy", "таблетки",
                "витамины", "лечение", "treatment", "медосмотр", "прививка", "vaccination"
            ],
            ExpenseCategory.UTILITIES.value: [
                "коммунальные", "жкх", "электричество", "газ", "вода", "интернет", "телефон",
                "мобильная связь", "квартплата", "аренда", "utilities", "electricity", "water",
                "gas", "internet", "phone", "rent", "heating", "отопление", "канализация"
            ]
        }
        
        self.income_keywords = {
            IncomeCategory.SALARY.value: [
                "зарплата", "оклад", "аванс", "премия", "salary", "wage", "payment", "pay",
                "зп", "получил", "перевод", "transfer", "работа", "work", "job"
            ],
            IncomeCategory.SIDE_JOB.value: [
                "подработка", "freelance", "фриланс", "заказ", "работа", "услуги", "service",
                "side job", "sidework", "дополнительная работа", "халтура", "проект", "project"
            ]
        }
        
        # Compile regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for keyword matching."""
        self.expense_patterns = {}
        self.income_patterns = {}
        
        for category, keywords in self.expense_keywords.items():
            pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\b'
            self.expense_patterns[category] = re.compile(pattern, re.IGNORECASE)
        
        for category, keywords in self.income_keywords.items():
            pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\b'
            self.income_patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def classify_expense(self, text: str) -> str:
        """
        Classify expense transaction based on text content.
        
        Args:
            text: Text to analyze for category determination
            
        Returns:
            Category name string
        """
        text = text.lower().strip()
        
        # Score each category based on keyword matches
        category_scores = {}
        
        for category, pattern in self.expense_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Score based on number of matches and their length
                score = len(matches) + sum(len(match) for match in matches) / 10
                category_scores[category] = score
        
        if category_scores:
            # Return category with highest score
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            return best_category
        
        # Default category if no matches found
        return ExpenseCategory.OTHER_EXPENSE.value
    
    def classify_income(self, text: str) -> str:
        """
        Classify income transaction based on text content.
        
        Args:
            text: Text to analyze for category determination
            
        Returns:
            Category name string
        """
        text = text.lower().strip()
        
        # Score each category based on keyword matches
        category_scores = {}
        
        for category, pattern in self.income_patterns.items():
            matches = pattern.findall(text)
            if matches:
                score = len(matches) + sum(len(match) for match in matches) / 10
                category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            return best_category
        
        # Default category if no matches found
        return IncomeCategory.OTHER_INCOME.value
    
    def classify_transaction(self, text: str, transaction_type: TransactionType) -> str:
        """
        Classify transaction based on type and text content.
        
        Args:
            text: Text to analyze
            transaction_type: Type of transaction (income or expense)
            
        Returns:
            Category name string
        """
        if transaction_type == TransactionType.EXPENSE:
            return self.classify_expense(text)
        else:
            return self.classify_income(text)
    
    def get_all_categories(self) -> Dict[TransactionType, List[str]]:
        """Get all available categories grouped by transaction type."""
        return {
            TransactionType.EXPENSE: [category.value for category in ExpenseCategory],
            TransactionType.INCOME: [category.value for category in IncomeCategory]
        }
    
    def get_category_suggestions(self, text: str, transaction_type: TransactionType, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Get top category suggestions with confidence scores.
        
        Args:
            text: Text to analyze
            transaction_type: Type of transaction
            top_n: Number of suggestions to return
            
        Returns:
            List of (category, confidence_score) tuples
        """
        text = text.lower().strip()
        category_scores = {}
        
        if transaction_type == TransactionType.EXPENSE:
            patterns = self.expense_patterns
        else:
            patterns = self.income_patterns
        
        for category, pattern in patterns.items():
            matches = pattern.findall(text)
            if matches:
                score = len(matches) + sum(len(match) for match in matches) / 10
                category_scores[category] = score
        
        # Sort by score and return top N
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_categories[:top_n]


# Global classifier instance
classifier = CategoryClassifier()


def classify_transaction_category(text: str, transaction_type: TransactionType) -> str:
    """
    Classify transaction category based on text and transaction type.
    
    Args:
        text: Text content to analyze
        transaction_type: Type of transaction
        
    Returns:
        Category name string
    """
    return classifier.classify_transaction(text, transaction_type)


def get_category_suggestions(text: str, transaction_type: TransactionType, top_n: int = 3) -> List[Tuple[str, float]]:
    """Get category suggestions with confidence scores."""
    return classifier.get_category_suggestions(text, transaction_type, top_n)


def get_all_categories() -> Dict[TransactionType, List[str]]:
    """Get all available categories."""
    return classifier.get_all_categories()