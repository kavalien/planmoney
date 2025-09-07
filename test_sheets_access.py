#!/usr/bin/env python3
"""
Simple Google Sheets access test
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

def test_sheets_access():
    """Test basic Google Sheets access"""
    
    # Configuration
    credentials_file = "credentials/google_service_account.json"
    spreadsheet_id = "1S0ifwdFSuqrxfumNQlgPKA-jd32_bOcrU3ufemJXGPM"
    
    print("🧪 Тест доступа к Google Sheets")
    print("=" * 50)
    
    # Check credentials file
    if not os.path.exists(credentials_file):
        print(f"❌ Файл credentials не найден: {credentials_file}")
        return False
    
    try:
        # Load credentials
        print("1️⃣ Загрузка credentials...")
        creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        print(f"✅ Service account: {creds.service_account_email}")
        
        # Try to refresh (this might fail)
        print("\n2️⃣ Попытка обновления токена...")
        try:
            request = Request()
            creds.refresh(request)
            print("✅ Токен обновлен успешно")
        except Exception as e:
            print(f"⚠️ Ошибка обновления токена: {e}")
            print("Продолжаем тест без обновления...")
        
        # Test gspread connection
        print("\n3️⃣ Подключение через gspread...")
        gc = gspread.authorize(creds)
        print("✅ gspread авторизован")
        
        # Try to open spreadsheet
        print(f"\n4️⃣ Открытие таблицы {spreadsheet_id}...")
        spreadsheet = gc.open_by_key(spreadsheet_id)
        print(f"✅ Таблица открыта: {spreadsheet.title}")
        
        # List worksheets
        print("\n5️⃣ Получение списка листов...")
        worksheets = spreadsheet.worksheets()
        print(f"✅ Найдено листов: {len(worksheets)}")
        for i, ws in enumerate(worksheets):
            print(f"   {i+1}. {ws.title}")
        
        # Try to read/write a test cell
        print("\n6️⃣ Тест записи в первый лист...")
        if worksheets:
            ws = worksheets[0]
            try:
                # Try to read cell A1
                value = ws.acell('A1').value
                print(f"✅ Значение A1: '{value}'")
                
                # Try to write to a test cell (B1)
                ws.update('B1', 'Test from bot')
                print("✅ Тест записи выполнен")
                
                # Read back the value
                test_value = ws.acell('B1').value
                print(f"✅ Проверка записи: '{test_value}'")
                
            except Exception as e:
                print(f"❌ Ошибка чтения/записи: {e}")
                return False
        
        print("\n🎉 Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_sheets_access()
    if not success:
        print("\n💡 Возможные решения:")
        print("1. Убедитесь, что таблица расшарена на email service account")
        print("2. Проверьте права доступа (Editor или выше)")
        print("3. Проверьте корректность Spreadsheet ID")
        sys.exit(1)