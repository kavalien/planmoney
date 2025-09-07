#!/usr/bin/env python3
"""
Скрипт для пересоздания листа с правильной комплексной структурой
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import gspread
from google.oauth2.service_account import Credentials

def recreate_month_sheet():
    """Пересоздаем лист месяца с правильной структурой"""
    
    print("🔄 Пересоздание листа с комплексной структурой...")
    
    # Configuration
    credentials_file = "credentials/google_service_account.json"
    spreadsheet_id = "1S0ifwdFSuqrxfumNQlgPKA-jd32_bOcrU3ufemJXGPM"
    current_month = "2025-09"
    
    try:
        # Load credentials
        creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Connect to Google Sheets
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print(f"✅ Подключен к таблице: {spreadsheet.title}")
        
        # Create new comprehensive sheet with temporary name
        temp_name = f"{current_month}-new"
        print(f"📊 Создаем новый лист '{temp_name}' с комплексной структурой...")
        worksheet = spreadsheet.add_worksheet(
            title=temp_name,
            rows=200,
            cols=20
        )
        time.sleep(1)
        
        # Section 1: Transaction Details (rows 1-50)
        print("   📝 Секция 1: Детальные транзакции (строки 1-50)")
        setup_transactions_section(worksheet, 1)
        
        # Section 2: Expense Analytics (rows 55-85)
        print("   💸 Секция 2: Расходы по категориям (строки 55-85)")
        setup_expenses_section(worksheet, 55)
        
        # Section 3: Income Analytics (rows 90-120)
        print("   💰 Секция 3: Доходы по категориям (строки 90-120)")
        setup_income_section(worksheet, 90)
        
        # Section 4: Balance Summary (rows 125-155)
        print("   ⚖️ Секция 4: Ежедневный баланс (строки 125-155)")
        setup_balance_section(worksheet, 125)
        
        # Now delete old sheet and rename new one
        try:
            old_sheet = spreadsheet.worksheet(current_month)
            spreadsheet.del_worksheet(old_sheet)
            print(f"🗑️ Удален старый лист '{current_month}'")
            time.sleep(1)
        except gspread.WorksheetNotFound:
            print(f"ℹ️ Старый лист '{current_month}' не найден")
        
        # Rename new sheet
        worksheet.update_title(current_month)
        print(f"✏️ Лист переименован в '{current_month}'")
        
        print("🎉 Лист успешно создан с комплексной структурой!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def setup_transactions_section(worksheet, start_row):
    """Setup transaction details section."""
    headers = ["Дата", "Пользователь", "Тип", "Сумма", "Категория", "Описание", "Telegram ID"]
    
    # Section title
    worksheet.update(f'A{start_row}', "ДЕТАЛЬНЫЕ ТРАНЗАКЦИИ")
    time.sleep(0.5)
    
    # Headers
    headers_row = start_row + 1
    worksheet.update(f'A{headers_row}', [headers])
    time.sleep(0.5)
    
    # Format section
    worksheet.format(f'A{start_row}:G{start_row}', {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    })
    
    worksheet.format(f'A{headers_row}:G{headers_row}', {
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
        'textFormat': {'bold': True}
    })

def setup_expenses_section(worksheet, start_row):
    """Setup expenses analytics section."""
    expense_categories = [
        "Продукты питания", "Транспорт", "Развлечения", "Покупки",
        "Здоровье", "Коммунальные услуги", "Образование", "Прочие расходы"
    ]
    
    # Section title
    worksheet.update(f'A{start_row}', "РАСХОДЫ ПО КАТЕГОРИЯМ")
    time.sleep(0.5)
    
    # Headers
    headers = ["Дата"] + expense_categories + ["Итого"]
    headers_row = start_row + 1
    worksheet.update(f'A{headers_row}', [headers])
    time.sleep(0.5)
    
    # Add sample days
    add_month_days_template(worksheet, start_row + 2, len(headers))
    
    # Format section
    worksheet.format(f'A{start_row}:J{start_row}', {
        'backgroundColor': {'red': 0.9, 'green': 0.4, 'blue': 0.4},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    })
    
    worksheet.format(f'A{headers_row}:J{headers_row}', {
        'backgroundColor': {'red': 0.9, 'green': 0.7, 'blue': 0.7},
        'textFormat': {'bold': True}
    })

def setup_income_section(worksheet, start_row):
    """Setup income analytics section."""
    income_categories = [
        "Зарплата", "Фриланс", "Премия", "Подработка", "Прочие доходы"
    ]
    
    # Section title
    worksheet.update(f'A{start_row}', "ДОХОДЫ ПО КАТЕГОРИЯМ")
    time.sleep(0.5)
    
    # Headers
    headers = ["Дата"] + income_categories + ["Итого"]
    headers_row = start_row + 1
    worksheet.update(f'A{headers_row}', [headers])
    time.sleep(0.5)
    
    # Add sample days
    add_month_days_template(worksheet, start_row + 2, len(headers))
    
    # Format section
    worksheet.format(f'A{start_row}:G{start_row}', {
        'backgroundColor': {'red': 0.4, 'green': 0.9, 'blue': 0.4},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    })
    
    worksheet.format(f'A{headers_row}:G{headers_row}', {
        'backgroundColor': {'red': 0.7, 'green': 0.9, 'blue': 0.7},
        'textFormat': {'bold': True}
    })

def setup_balance_section(worksheet, start_row):
    """Setup balance summary section."""
    # Section title
    worksheet.update(f'A{start_row}', "ЕЖЕДНЕВНЫЙ БАЛАНС")
    time.sleep(0.5)
    
    # Headers
    headers = ["Дата", "Доходы", "Расходы", "Сальдо", "Накопительно"]
    headers_row = start_row + 1
    worksheet.update(f'A{headers_row}', [headers])
    time.sleep(0.5)
    
    # Add sample days
    add_month_days_template(worksheet, start_row + 2, len(headers))
    
    # Format section
    worksheet.format(f'A{start_row}:E{start_row}', {
        'backgroundColor': {'red': 0.6, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    })
    
    worksheet.format(f'A{headers_row}:E{headers_row}', {
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.9},
        'textFormat': {'bold': True}
    })

def add_month_days_template(worksheet, start_row, cols_count):
    """Add template days for current month."""
    current_date = datetime.now().replace(day=1)
    batch_data = []
    
    # Add first 7 days as template
    for i in range(7):
        day = current_date + timedelta(days=i)
        day_str = day.strftime("%d.%m")
        row_data = [day_str] + [''] * (cols_count - 1)
        batch_data.append(row_data)
    
    worksheet.update(f'A{start_row}', batch_data)
    time.sleep(0.5)
    
    # Add monthly total row
    total_row = start_row + 10
    worksheet.update(f'A{total_row}', "ИТОГО ЗА МЕСЯЦ")
    time.sleep(0.5)

if __name__ == "__main__":
    success = recreate_month_sheet()
    if not success:
        sys.exit(1)