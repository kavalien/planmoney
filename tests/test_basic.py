"""
Basic unit tests for the Telegram Finance Bot.

Tests for parser and categories functionality.
"""

import unittest
from decimal import Decimal
from datetime import datetime

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.utils.parser import MessageParser, parse_transaction_message, is_transaction_message
from bot.utils.categories import CategoryClassifier, classify_transaction_category
from bot.models.transaction import Transaction, TransactionType
from bot.utils.validators import TransactionValidator, validate_transaction_data


class TestMessageParser(unittest.TestCase):
    """Test cases for message parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = MessageParser()
    
    def test_parse_expense_messages(self):
        """Test parsing expense messages."""
        test_cases = [
            ("потратил 500 руб на продукты", 500, TransactionType.EXPENSE),
            ("купила кофе 150р", 150, TransactionType.EXPENSE),
            ("такси 300 рублей", 300, TransactionType.EXPENSE),
            ("500₽ продукты в Пятерочке", 500, TransactionType.EXPENSE),
            ("оплатил интернет 800 руб", 800, TransactionType.EXPENSE),
        ]
        
        for text, expected_amount, expected_type in test_cases:
            with self.subTest(text=text):
                parsed = self.parser.parse_message(text)
                self.assertEqual(parsed.amount, Decimal(str(expected_amount)))
                self.assertEqual(parsed.transaction_type, expected_type)
                self.assertIsNotNone(parsed.category)
    
    def test_parse_income_messages(self):
        """Test parsing income messages."""
        test_cases = [
            ("получил зарплату 50000 руб", 50000, TransactionType.INCOME),
            ("подработка 5000р", 5000, TransactionType.INCOME),
            ("+10000 руб премия", 10000, TransactionType.INCOME),
            ("заработал 15000 руб", 15000, TransactionType.INCOME),
        ]
        
        for text, expected_amount, expected_type in test_cases:
            with self.subTest(text=text):
                parsed = self.parser.parse_message(text)
                self.assertEqual(parsed.amount, Decimal(str(expected_amount)))
                self.assertEqual(parsed.transaction_type, expected_type)
                self.assertIsNotNone(parsed.category)
    
    def test_extract_amount(self):
        """Test amount extraction."""
        test_cases = [
            ("500 руб", 500),
            ("1500.50 рублей", 1500.50),
            ("999₽", 999),
            ("100.25р", 100.25),
            ("2000,75 руб", 2000.75),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                amount = self.parser.extract_amount(text)
                self.assertEqual(amount, Decimal(str(expected)))
    
    def test_transaction_type_detection(self):
        """Test transaction type detection."""
        expense_texts = [
            "потратил 500 руб",
            "купил хлеб",
            "заплатил за такси",
            "оплатил счет",
        ]
        
        income_texts = [
            "получил зарплату",
            "заработал деньги",
            "+1000 руб",
            "пришла премия",
        ]
        
        for text in expense_texts:
            with self.subTest(text=text):
                transaction_type = self.parser.determine_transaction_type(text)
                self.assertEqual(transaction_type, TransactionType.EXPENSE)
        
        for text in income_texts:
            with self.subTest(text=text):
                transaction_type = self.parser.determine_transaction_type(text)
                self.assertEqual(transaction_type, TransactionType.INCOME)
    
    def test_is_transaction_message(self):
        """Test transaction message detection."""
        transaction_messages = [
            "потратил 500 руб на продукты",
            "получил зарплату 50000 руб",
            "купил кофе 150р",
            "1000₽ на бензин",
        ]
        
        non_transaction_messages = [
            "привет",
            "как дела?",
            "спасибо",
            "завтра встречаемся",
        ]
        
        for text in transaction_messages:
            with self.subTest(text=text):
                self.assertTrue(is_transaction_message(text))
        
        for text in non_transaction_messages:
            with self.subTest(text=text):
                self.assertFalse(is_transaction_message(text))


class TestCategoryClassifier(unittest.TestCase):
    """Test cases for category classifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = CategoryClassifier()
    
    def test_expense_categorization(self):
        """Test expense category classification."""
        test_cases = [
            ("продукты в пятерочке", "Продукты питания"),
            ("такси до дома", "Транспорт"),
            ("билеты в кино", "Развлечения"),
            ("новая куртка", "Одежда"),
            ("лекарства в аптеке", "Здоровье/медицина"),
            ("оплата за интернет", "Коммунальные услуги"),
        ]
        
        for text, expected_category in test_cases:
            with self.subTest(text=text):
                category = self.classifier.classify_expense(text)
                self.assertEqual(category, expected_category)
    
    def test_income_categorization(self):
        """Test income category classification."""
        test_cases = [
            ("получил зарплату", "Зарплата"),
            ("фриланс проект", "Подработка"),
            ("подработка на выходных", "Подработка"),
        ]
        
        for text, expected_category in test_cases:
            with self.subTest(text=text):
                category = self.classifier.classify_income(text)
                self.assertEqual(category, expected_category)
    
    def test_category_suggestions(self):
        """Test category suggestions with confidence."""
        suggestions = self.classifier.get_category_suggestions(
            "купил продукты в магазине",
            TransactionType.EXPENSE,
            top_n=3
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Check that suggestions are tuples with category and score
        for category, score in suggestions:
            self.assertIsInstance(category, str)
            self.assertIsInstance(score, (int, float))
            self.assertGreater(score, 0)


class TestTransactionModel(unittest.TestCase):
    """Test cases for transaction model."""
    
    def test_transaction_creation(self):
        """Test transaction creation."""
        transaction = Transaction(
            user_id=123456789,
            amount=Decimal("500.50"),
            transaction_type=TransactionType.EXPENSE,
            category="Продукты питания",
            description="Продукты в Пятерочке"
        )
        
        self.assertEqual(transaction.user_id, 123456789)
        self.assertEqual(transaction.amount, Decimal("500.50"))
        self.assertEqual(transaction.transaction_type, TransactionType.EXPENSE)
        self.assertEqual(transaction.category, "Продукты питания")
        self.assertIsInstance(transaction.date, datetime)
    
    def test_amount_with_sign(self):
        """Test amount with sign calculation."""
        # Expense should be negative
        expense = Transaction(
            user_id=123,
            amount=Decimal("500"),
            transaction_type=TransactionType.EXPENSE,
            category="Test"
        )
        self.assertEqual(expense.amount_with_sign, Decimal("-500"))
        
        # Income should be positive
        income = Transaction(
            user_id=123,
            amount=Decimal("1000"),
            transaction_type=TransactionType.INCOME,
            category="Test"
        )
        self.assertEqual(income.amount_with_sign, Decimal("1000"))
    
    def test_formatted_amounts(self):
        """Test formatted amount strings."""
        transaction = Transaction(
            user_id=123,
            amount=Decimal("1500.75"),
            transaction_type=TransactionType.EXPENSE,
            category="Test"
        )
        
        self.assertEqual(transaction.formatted_amount, "1,500.75 RUB")
        self.assertEqual(transaction.formatted_amount_with_sign, "-1,500.75 RUB")
    
    def test_to_spreadsheet_row(self):
        """Test conversion to spreadsheet row."""
        transaction = Transaction(
            user_id=123456789,
            amount=Decimal("500"),
            transaction_type=TransactionType.EXPENSE,
            category="Продукты питания",
            description="Test description",
            telegram_message_id=12345
        )
        
        row = transaction.to_spreadsheet_row()
        
        self.assertIsInstance(row, list)
        self.assertEqual(len(row), 7)  # Expected number of columns
        self.assertEqual(row[1], "123456789")  # user_id
        self.assertEqual(row[2], "expense")    # transaction_type
        self.assertEqual(row[3], "500")        # amount
        self.assertEqual(row[4], "Продукты питания")  # category
        self.assertEqual(row[5], "Test description")  # description
        self.assertEqual(row[6], "12345")      # telegram_message_id


class TestValidators(unittest.TestCase):
    """Test cases for validators."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TransactionValidator()
    
    def test_amount_validation(self):
        """Test amount validation."""
        # Valid amounts
        valid_amounts = [Decimal("1"), Decimal("100.50"), Decimal("999999")]
        for amount in valid_amounts:
            with self.subTest(amount=amount):
                is_valid, error = self.validator.validate_amount(amount)
                self.assertTrue(is_valid)
                self.assertIsNone(error)
        
        # Invalid amounts
        invalid_amounts = [Decimal("0"), Decimal("-100"), Decimal("1000001")]
        for amount in invalid_amounts:
            with self.subTest(amount=amount):
                is_valid, error = self.validator.validate_amount(amount)
                self.assertFalse(is_valid)
                self.assertIsNotNone(error)
    
    def test_transaction_validation(self):
        """Test complete transaction validation."""
        # Valid transaction
        errors = validate_transaction_data(
            user_id=123456789,
            amount=Decimal("500"),
            transaction_type=TransactionType.EXPENSE,
            category="Продукты питания",
            description="Valid description"
        )
        self.assertEqual(len(errors), 0)
        
        # Invalid transaction (negative amount)
        errors = validate_transaction_data(
            user_id=123456789,
            amount=Decimal("-500"),
            transaction_type=TransactionType.EXPENSE,
            category="Продукты питания"
        )
        self.assertGreater(len(errors), 0)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestMessageParser,
        TestCategoryClassifier,
        TestTransactionModel,
        TestValidators,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("🧪 Running basic unit tests for Telegram Finance Bot")
    print("=" * 60)
    
    result = run_tests()
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} error(s) occurred")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")