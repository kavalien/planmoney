# 🔑 Создание Google Service Account - Пошаговая инструкция

## Шаг 1: Переход в Google Cloud Console
1. Откройте браузер
2. Перейдите на: https://console.cloud.google.com
3. Войдите под своей учетной записью Google

## Шаг 2: Создание или выбор проекта
1. В верхней части экрана нажмите на название проекта (или "Select a project")
2. Нажмите "NEW PROJECT"
3. Введите название: "planmoney-bot"
4. Нажмите "CREATE"
5. Дождитесь создания и выберите созданный проект

## Шаг 3: Включение Google Sheets API
1. В левом меню найдите "APIs & Services" → "Library"
2. В поиске введите "Google Sheets API"
3. Нажмите на "Google Sheets API"
4. Нажмите "ENABLE"

## Шаг 4: Создание Service Account
1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "CREATE CREDENTIALS" → "Service account"
3. Заполните:
   - Service account name: finance-bot-service
   - Service account ID: (автоматически)
   - Description: Bot for accessing Google Sheets
4. Нажмите "CREATE AND CONTINUE"
5. В "Role" выберите "Editor" или "Owner"
6. Нажмите "CONTINUE" → "DONE"

## Шаг 5: Создание JSON ключа
1. В списке Service Accounts найдите созданный аккаунт
2. Нажмите на email Service Account
3. Перейдите на вкладку "KEYS"
4. Нажмите "ADD KEY" → "Create new key"
5. Выберите "JSON"
6. Нажмите "CREATE"
7. Файл автоматически скачается на компьютер

## Шаг 6: Предоставление доступа к Google Sheets
1. Откройте скачанный JSON файл
2. Найдите строку "client_email" и скопируйте email адрес
3. Откройте вашу Google Таблицу для бота
4. Нажмите "Share" (Поделиться)
5. Вставьте email от Service Account
6. Выберите права "Editor"
7. Нажмите "Send"