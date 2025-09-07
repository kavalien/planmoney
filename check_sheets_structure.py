#!/usr/bin/env python3
"""
Скрипт для проверки и очистки структуры Google Sheets
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import gspread
from google.oauth2.service_account import Credentials

def check_and_clean_sheets():
    """Проверяем структуру листов и удаляем ненужные"""
    
    print("🔍 Проверка структуры Google Sheets...")
    
    # Configuration
    credentials_file = "credentials/google_service_account.json"
    spreadsheet_id = "1S0ifwdFSuqrxfumNQlgPKA-jd32_bOcrU3ufemJXGPM"
    
    if not os.path.exists(credentials_file):
        print(f"❌ Файл credentials не найден: {credentials_file}")
        return False
    
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
        print()
        
        # List all worksheets
        worksheets = spreadsheet.worksheets()
        print(f"📋 Текущие листы ({len(worksheets)}):")
        for i, ws in enumerate(worksheets):
            print(f"   {i+1}. '{ws.title}' (ID: {ws.id})")
        print()
        
        # Define what we need
        current_month = "2025-09"
        needed_sheets = [current_month]
        
        # Find sheets to delete
        sheets_to_delete = []
        sheets_to_keep = []
        
        for ws in worksheets:
            if ws.title in needed_sheets:
                sheets_to_keep.append(ws.title)
                print(f"✅ Оставляем: '{ws.title}'")
            elif ws.title == "Лист1":  # Default sheet, можно удалить если есть другие
                if len(worksheets) > 1:
                    sheets_to_delete.append((ws.title, ws.id))
                    print(f"🗑️ Удаляем: '{ws.title}' (дефолтный лист)")
                else:
                    print(f"⚠️ Оставляем: '{ws.title}' (единственный лист)")
            elif "Расходы-" in ws.title or "Доходы-" in ws.title or "Сальдо-" in ws.title:
                sheets_to_delete.append((ws.title, ws.id))
                print(f"🗑️ Удаляем: '{ws.title}' (старая структура)")
            else:
                print(f"❓ Неизвестный лист: '{ws.title}' - оставляем")
        
        print()
        
        # Delete unnecessary sheets
        if sheets_to_delete:
            print(f"🗑️ Удаляем {len(sheets_to_delete)} ненужных листов...")
            for sheet_name, sheet_id in sheets_to_delete:
                try:
                    spreadsheet.del_worksheet_by_id(sheet_id)
                    print(f"   ✅ Удален: '{sheet_name}'")
                except Exception as e:
                    print(f"   ❌ Ошибка удаления '{sheet_name}': {e}")
        else:
            print("✅ Нет листов для удаления")
        
        print()
        
        # Check structure of main sheet
        if current_month in [ws.title for ws in spreadsheet.worksheets()]:
            print(f"🔍 Проверяем структуру листа '{current_month}'...")
            worksheet = spreadsheet.worksheet(current_month)
            
            # Check key sections
            sections_to_check = [
                (1, "ДЕТАЛЬНЫЕ ТРАНЗАКЦИИ"),
                (55, "РАСХОДЫ ПО КАТЕГОРИЯМ"),
                (90, "ДОХОДЫ ПО КАТЕГОРИЯМ"),
                (125, "ЕЖЕДНЕВНЫЙ БАЛАНС")
            ]
            
            for row, expected_title in sections_to_check:
                try:
                    cell_value = worksheet.cell(row, 1).value
                    if cell_value == expected_title:
                        print(f"   ✅ Строка {row}: '{expected_title}'")
                    else:
                        print(f"   ❌ Строка {row}: ожидалось '{expected_title}', найдено '{cell_value}'")
                except Exception as e:
                    print(f"   ❌ Ошибка проверки строки {row}: {e}")
        else:
            print(f"❌ Основной лист '{current_month}' не найден!")
        
        print()
        print("🎉 Проверка завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = check_and_clean_sheets()
    if not success:
        sys.exit(1)