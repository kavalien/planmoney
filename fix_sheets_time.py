#!/usr/bin/env python3
"""
Фикс для Google Sheets с проблемой системного времени
"""

import json
import time
from datetime import datetime, timezone
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def fix_service_account_time():
    """Попытка исправить проблему времени в Service Account"""
    
    credentials_file = "credentials/google_service_account.json"
    
    if not os.path.exists(credentials_file):
        print(f"❌ Файл не найден: {credentials_file}")
        return False
    
    print("🔧 Попытка исправления проблемы времени...")
    
    try:
        # Читаем текущие credentials
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        print(f"✅ Service Account: {creds_data.get('client_email')}")
        print(f"✅ Project ID: {creds_data.get('project_id')}")
        
        # Проверяем реальное время через интернет
        import requests
        
        try:
            # Получаем реальное время от мирового API времени
            response = requests.get('http://worldtimeapi.org/api/timezone/UTC', timeout=5)
            if response.status_code == 200:
                real_time = response.json()
                real_datetime = datetime.fromisoformat(real_time['datetime'].replace('Z', '+00:00'))
                system_time = datetime.now(timezone.utc)
                
                time_diff = abs((real_datetime - system_time).total_seconds())
                
                print(f"🌐 Реальное время UTC: {real_datetime}")
                print(f"💻 Системное время UTC: {system_time}")
                print(f"⏰ Разница: {time_diff:.0f} секунд")
                
                if time_diff > 300:  # Больше 5 минут
                    print("❌ Системное время сильно отличается от реального!")
                    print("💡 Рекомендуется исправить системное время")
                    return False
                else:
                    print("✅ Время в норме")
        
        except Exception as e:
            print(f"⚠️ Не удалось проверить реальное время: {e}")
        
        # Попробуем альтернативный способ подключения
        print("\n🧪 Тестируем альтернативное подключение...")
        
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Создаем credentials без refresh
        credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Не обновляем токен, используем как есть
        gc = gspread.authorize(credentials)
        
        # Тестируем доступ к таблице
        spreadsheet_id = "1S0ifwdFSuqrxfumNQlgPKA-jd32_bOcrU3ufemJXGPM"
        
        try:
            spreadsheet = gc.open_by_key(spreadsheet_id)
            print(f"✅ Таблица открыта: {spreadsheet.title}")
            
            # Получаем первый лист
            worksheet = spreadsheet.sheet1
            print(f"✅ Лист доступен: {worksheet.title}")
            
            # Пробуем записать тестовое значение
            test_cell = f"Z1"  # Используем дальнюю колонку для теста
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.update(test_cell, f"Test {current_time}")
            
            # Читаем обратно
            value = worksheet.acell(test_cell).value
            print(f"✅ Тест записи/чтения: {value}")
            
            print("\n🎉 Google Sheets работает!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка доступа к таблице: {e}")
            
            if "insufficient" in str(e).lower() or "permission" in str(e).lower():
                print("\n💡 Решение:")
                print("1. Откройте Google Таблицу")
                print("2. Нажмите 'Поделиться'")
                print(f"3. Добавьте email: {creds_data.get('client_email')}")
                print("4. Установите права: 'Редактор'")
                
            return False
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = fix_service_account_time()
    if success:
        print("\n✅ Проблема с Google Sheets решена!")
    else:
        print("\n❌ Требуется дополнительная настройка")