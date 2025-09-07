#!/usr/bin/env python3
"""
Test script to verify the updated Google Sheets service works with column structure
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import bot modules
from bot.models.transaction import Transaction, TransactionType
from bot.services.google_sheets import GoogleSheetsService

async def test_column_structure():
    """Test the updated Google Sheets service with column structure"""
    
    print("🧪 Testing Google Sheets service with column structure...")
    print("=" * 60)
    
    try:
        # Initialize Google Sheets service
        print("1️⃣ Initializing Google Sheets service...")
        sheets_service = GoogleSheetsService()
        await sheets_service.initialize()
        
        if not sheets_service.client:
            print("❌ Google Sheets service not available")
            return False
        
        print("✅ Google Sheets service initialized")
        
        # Test connection
        print("\n2️⃣ Testing connection...")
        connection_ok = await sheets_service.test_connection()
        if not connection_ok:
            print("❌ Connection test failed")
            return False
        
        print("✅ Connection test passed")
        
        # Create test transactions
        print("\n3️⃣ Creating test transactions...")
        
        test_transactions = [
            Transaction(
                user_id=1234567890,
                transaction_type=TransactionType.EXPENSE,
                amount=Decimal("250.50"),
                category="Продукты питания",
                description="Покупки в магазине",
                date=datetime.now(),
                telegram_message_id=1
            ),
            Transaction(
                user_id=1234567890,
                transaction_type=TransactionType.INCOME,
                amount=Decimal("5000.00"),
                category="Зарплата",
                description="Месячная зарплата",
                date=datetime.now(),
                telegram_message_id=2
            ),
            Transaction(
                user_id=1234567890,
                transaction_type=TransactionType.EXPENSE,
                amount=Decimal("120.00"),
                category="Транспорт",
                description="Проезд на автобусе",
                date=datetime.now(),
                telegram_message_id=3
            )
        ]
        
        print(f"✅ Created {len(test_transactions)} test transactions")
        
        # Add transactions to sheets
        print("\n4️⃣ Adding transactions to Google Sheets...")
        
        for i, transaction in enumerate(test_transactions):
            try:
                row_number = await sheets_service.add_transaction(transaction)
                print(f"   ✅ Transaction {i+1} added to row {row_number}")
                print(f"      {transaction.transaction_type.value}: {transaction.amount} - {transaction.category}")
            except Exception as e:
                print(f"   ❌ Failed to add transaction {i+1}: {e}")
                return False
        
        print("\n5️⃣ Testing sheet structure...")
        
        # Get current month sheet
        current_month = datetime.now().strftime("%Y-%m")
        try:
            worksheet = sheets_service.spreadsheet.worksheet(current_month)
            
            # Check section headers
            sections = [
                ('A1', "ДЕТАЛЬНЫЕ ТРАНЗАКЦИИ"),
                ('I1', "РАСХОДЫ ПО КАТЕГОРИЯМ"),
                ('S1', "ДОХОДЫ ПО КАТЕГОРИЯМ"),
                ('Z1', "ЕЖЕДНЕВНЫЙ БАЛАНС")
            ]
            
            for cell, expected in sections:
                value = worksheet.acell(cell).value
                if value == expected:
                    print(f"   ✅ {cell}: '{expected}'")
                else:
                    print(f"   ❌ {cell}: expected '{expected}', found '{value}'")
            
            # Check if transactions were added
            transactions_data = worksheet.get('A3:G10')
            non_empty_rows = [row for row in transactions_data if row and row[0]]
            print(f"   ✅ Found {len(non_empty_rows)} transaction rows")
            
            # Check analytics sections have data
            expense_data = worksheet.get('I3:R10')
            income_data = worksheet.get('S3:Y10')
            balance_data = worksheet.get('Z3:AD10')
            
            expense_rows = [row for row in expense_data if row and row[0]]
            income_rows = [row for row in income_data if row and row[0]]
            balance_rows = [row for row in balance_data if row and row[0]]
            
            print(f"   ✅ Found {len(expense_rows)} expense analytics rows")
            print(f"   ✅ Found {len(income_rows)} income analytics rows")
            print(f"   ✅ Found {len(balance_rows)} balance analytics rows")
            
        except Exception as e:
            print(f"   ❌ Error checking sheet structure: {e}")
            return False
        
        print("\n🎉 All tests passed! Column structure is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_column_structure())
    if not success:
        sys.exit(1)