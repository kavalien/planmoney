#!/usr/bin/env python3
"""
Скрипт для создания листа со структурой по столбцам
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

def recreate_column_based_sheet():
    """Пересоздаем лист с структурой по столбцам"""
    
    print("🔄 Создание листа со структурой по столбцам...")
    
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
        
        # Delete existing temp sheet if exists
        temp_name = f"{current_month}-columns"
        try:
            temp_sheet = spreadsheet.worksheet(temp_name)
            spreadsheet.del_worksheet(temp_sheet)
            print(f"🗑️ Удален существующий временный лист '{temp_name}'")
            time.sleep(1)
        except gspread.WorksheetNotFound:
            pass
        
        # Create new sheet with temporary name
        print(f"📊 Создаем новый лист '{temp_name}' со структурой по столбцам...")
        worksheet = spreadsheet.add_worksheet(
            title=temp_name,
            rows=100,
            cols=30  # Enough columns for all sections
        )
        time.sleep(1)
        
        # Section 1: Detailed Transactions (Columns A-G)
        print("   📝 Секция 1: Детальные транзакции (столбцы A-G)")
        setup_transactions_columns(worksheet, start_col='A')
        
        # Section 2: Expense Categories (Columns I-Q)
        print("   💸 Секция 2: Расходы по категориям (столбцы I-Q)")
        setup_expense_columns(worksheet, start_col='I')
        
        # Section 3: Income Categories (Columns S-X) 
        print("   💰 Секция 3: Доходы по категориям (столбцы S-X)")
        setup_income_columns(worksheet, start_col='S')
        
        # Section 4: Daily Balance (Columns Z-AD)
        print("   ⚖️ Секция 4: Ежедневный баланс (столбцы Z-AD)")
        setup_balance_columns(worksheet, start_col='Z')
        
        # Delete old sheet and rename new one
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
        
        print("🎉 Лист успешно создан со структурой по столбцам!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def setup_transactions_columns(worksheet, start_col):
    """Setup detailed transactions in columns A-G"""
    headers = ["Дата", "Пользователь", "Тип", "Сумма", "Категория", "Описание", "Telegram ID"]
    
    # Section header in row 1
    worksheet.update('A1', "ДЕТАЛЬНЫЕ ТРАНЗАКЦИИ")
    time.sleep(0.5)
    
    # Column headers in row 2
    range_name = f'{start_col}2:G2'
    worksheet.update(range_name, [headers])
    time.sleep(0.5)
    
    # Format section header
    worksheet.format('A1:G1', {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format column headers
    worksheet.format('A2:G2', {
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
        'textFormat': {'bold': True}
    })

def setup_expense_columns(worksheet, start_col):
    """Setup expense categories in columns I-Q"""
    expense_categories = [
        "Продукты питания", "Транспорт", "Развлечения", "Покупки",
        "Здоровье", "Коммунальные услуги", "Образование", "Прочие расходы"
    ]
    
    headers = ["Дата"] + expense_categories + ["Итого"]
    
    # Section header in row 1 - span across all columns
    worksheet.update('I1', "РАСХОДЫ ПО КАТЕГОРИЯМ")
    time.sleep(0.5)
    
    # Column headers in row 2 - I to S (9 columns + 1 for total = 10)
    end_col = chr(ord(start_col) + len(headers) - 1)  # Calculate end column
    range_name = f'{start_col}2:{end_col}2'
    worksheet.update(range_name, [headers])
    time.sleep(0.5)
    
    # Add dates for entire month
    add_sample_dates(worksheet, start_col, 3)
    
    # Format section header
    worksheet.format(f'I1:{end_col}1', {
        'backgroundColor': {'red': 0.9, 'green': 0.4, 'blue': 0.4},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format column headers
    worksheet.format(f'I2:{end_col}2', {
        'backgroundColor': {'red': 0.9, 'green': 0.7, 'blue': 0.7},
        'textFormat': {'bold': True}
    })

def setup_income_columns(worksheet, start_col):
    """Setup income categories in columns S-X"""
    income_categories = [
        "Зарплата", "Фриланс", "Премия", "Подработка", "Прочие доходы"
    ]
    
    headers = ["Дата"] + income_categories + ["Итого"]
    
    # Section header in row 1
    worksheet.update('S1', "ДОХОДЫ ПО КАТЕГОРИЯМ")
    time.sleep(0.5)
    
    # Column headers in row 2
    end_col = chr(ord(start_col) + len(headers) - 1)  # Calculate end column
    range_name = f'{start_col}2:{end_col}2'
    worksheet.update(range_name, [headers])
    time.sleep(0.5)
    
    # Add dates for entire month
    add_sample_dates(worksheet, start_col, 3)
    
    # Format section header
    worksheet.format(f'S1:{end_col}1', {
        'backgroundColor': {'red': 0.4, 'green': 0.9, 'blue': 0.4},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format column headers
    worksheet.format(f'S2:{end_col}2', {
        'backgroundColor': {'red': 0.7, 'green': 0.9, 'blue': 0.7},
        'textFormat': {'bold': True}
    })

def setup_balance_columns(worksheet, start_col):
    """Setup daily balance in columns Z-AD"""
    headers = ["Дата", "Доходы", "Расходы", "Сальдо", "Накопительно"]
    
    # Section header in row 1
    worksheet.update('Z1', "ЕЖЕДНЕВНЫЙ БАЛАНС")
    time.sleep(0.5)
    
    # Column headers in row 2 (Z to AD = 5 columns)
    worksheet.update('Z2:AD2', [headers])
    time.sleep(0.5)
    
    # Add dates for entire month
    add_sample_dates(worksheet, start_col, 3)
    
    # Format section header
    worksheet.format('Z1:AD1', {
        'backgroundColor': {'red': 0.6, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format column headers
    worksheet.format('Z2:AD2', {
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.9},
        'textFormat': {'bold': True}
    })

def add_sample_dates(worksheet, start_col, start_row, max_days=None):
    """Add dates for the entire month to a column"""
    import calendar
    
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month
    
    # Получаем количество дней в текущем месяце
    days_in_month = calendar.monthrange(year, month)[1]
    
    # Если max_days указан, используем минимальное значение
    if max_days:
        days_to_add = min(days_in_month, max_days)
    else:
        days_to_add = days_in_month
    
    dates_data = []
    
    for day in range(1, days_to_add + 1):
        date_obj = datetime(year, month, day)
        day_str = date_obj.strftime("%d.%m")
        dates_data.append([day_str])
    
    # Convert column letter to range
    end_row = start_row + days_to_add - 1
    range_name = f'{start_col}{start_row}:{start_col}{end_row}'
    worksheet.update(range_name, dates_data)
    time.sleep(0.5)
    
    print(f"   ✓ Добавлено {days_to_add} дат в столбец {start_col} для {month}/{year}")

if __name__ == "__main__":
    success = recreate_column_based_sheet()
    if not success:
        sys.exit(1)