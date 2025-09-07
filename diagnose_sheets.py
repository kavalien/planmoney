#!/usr/bin/env python3
"""
Диагностический скрипт для Google Sheets интеграции
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

try:
    from bot.services.google_sheets import GoogleSheetsService
    from bot.config import get_config
    import gspread
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError
    import structlog
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure virtual environment is activated")
    sys.exit(1)

logger = structlog.get_logger()

async def diagnose_google_sheets():
    """Полная диагностика Google Sheets интеграции."""
    
    print("🔍 Диагностика Google Sheets интеграции")
    print("=" * 50)
    
    # 1. Проверка конфигурации
    print("\n1️⃣ Проверка конфигурации...")
    try:
        config = get_config()
        print(f"✅ Credentials файл: {config.GOOGLE_CREDENTIALS_FILE}")
        print(f"✅ Spreadsheet ID: {config.GOOGLE_SPREADSHEET_ID}")
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False
    
    # 2. Проверка credentials файла
    print("\n2️⃣ Проверка credentials файла...")
    if not os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
        print(f"❌ Файл не найден: {config.GOOGLE_CREDENTIALS_FILE}")
        return False
    
    try:
        with open(config.GOOGLE_CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
        
        print(f"✅ Файл найден")
        print(f"📧 Service account: {creds_data.get('client_email')}")
        print(f"🆔 Project ID: {creds_data.get('project_id')}")
        print(f"🔑 Private key ID: {creds_data.get('private_key_id')}")
        
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False
    
    # 3. Тест создания credentials
    print("\n3️⃣ Тест создания credentials...")
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(
            config.GOOGLE_CREDENTIALS_FILE, 
            scopes=scope
        )
        print("✅ Credentials созданы успешно")
        print(f"📅 Действительны: {creds.valid}")
        print(f"⏰ Истекли: {creds.expired}")
        
        # Попытка обновления токена
        if creds.expired or not creds.valid:
            print("🔄 Обновление токена...")
            request = Request()
            creds.refresh(request)
            print("✅ Токен обновлен")
        
    except RefreshError as e:
        print(f"❌ Ошибка JWT токена: {e}")
        print("\n💡 Решение:")
        print("1. Проверьте системное время")
        print("2. Пересоздайте Service Account в Google Cloud Console")
        print("3. Скачайте новый JSON файл")
        return False
    except Exception as e:
        print(f"❌ Ошибка создания credentials: {e}")
        return False
    
    # 4. Тест подключения к gspread
    print("\n4️⃣ Тест подключения к gspread...")
    try:
        client = gspread.authorize(creds)
        print("✅ gspread клиент создан")
        
    except Exception as e:
        print(f"❌ Ошибка создания gspread клиента: {e}")
        return False
    
    # 5. Тест доступа к таблице
    print("\n5️⃣ Тест доступа к Google Sheets...")
    try:
        spreadsheet = client.open_by_key(config.GOOGLE_SPREADSHEET_ID)
        print(f"✅ Таблица найдена: {spreadsheet.title}")
        
        # Попробуем получить первый лист
        worksheet = spreadsheet.sheet1
        print(f"✅ Лист найден: {worksheet.title}")
        
        # Попробуем прочитать данные
        all_values = worksheet.get_all_values()
        print(f"✅ Данные прочитаны: {len(all_values)} строк")
        
    except Exception as e:
        print(f"❌ Ошибка доступа к таблице: {e}")
        print("\n💡 Проверьте:")
        print("1. Правильность Spreadsheet ID")
        print("2. Доступ Service Account к таблице (Share)")
        print("3. Права 'Редактор' для Service Account")
        return False
    
    # 6. Тест нашего сервиса
    print("\n6️⃣ Тест нашего Google Sheets сервиса...")
    try:
        service = GoogleSheetsService()
        await service.initialize()
        
        # Тест подключения
        connection_ok = await service.test_connection()
        if connection_ok:
            print("✅ Наш сервис работает!")
        else:
            print("❌ Наш сервис не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка нашего сервиса: {e}")
        return False
    
    print("\n🎉 Все тесты пройдены! Google Sheets готов к работе!")
    return True

def print_troubleshooting_guide():
    """Печать руководства по устранению неполадок."""
    print("\n" + "=" * 50)
    print("🛠️ Руководство по устранению неполадок")
    print("=" * 50)
    
    print("\n🔧 Если JWT токен недействителен:")
    print("1. Перейдите в Google Cloud Console")
    print("2. Найдите ваш проект: telegram-finance-bot-471311")
    print("3. IAM & Admin > Service Accounts")
    print("4. Найдите finance-bot-service")
    print("5. Нажмите Actions > Manage keys")
    print("6. Add key > Create new key > JSON")
    print("7. Скачайте и замените файл credentials/google_service_account.json")
    
    print("\n📊 Если нет доступа к таблице:")
    print("1. Откройте Google Sheets")
    print("2. Нажмите Share в правом верхнем углу")
    print("3. Добавьте email: finance-bot-service@telegram-finance-bot-471311.iam.gserviceaccount.com")
    print("4. Установите роль: Editor")
    print("5. Снимите галочку 'Notify people'")

async def main():
    """Main function."""
    success = await diagnose_google_sheets()
    
    if not success:
        print_troubleshooting_guide()
        print("\n❌ Диагностика не пройдена. Следуйте инструкциям выше.")
        sys.exit(1)
    else:
        print("\n✅ Диагностика успешна! Google Sheets готов к работе.")

if __name__ == "__main__":
    asyncio.run(main())