# 🚀 Деплой на Railway.app

## Подготовка к деплою

### 1. Настройка проекта на Railway

1. Зайдите на https://railway.app/dashboard
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo" 
4. Выберите репозиторий `kavalien/planmoney`

### 2. Настройка переменных окружения

В настройках проекта на Railway добавьте следующие переменные:

**Обязательные переменные:**
```
BOT_TOKEN=ваш_токен_бота_от_BotFather
AUTHORIZED_USER_1=400783137
AUTHORIZED_USER_2=269582027
GOOGLE_SPREADSHEET_ID=ваш_id_таблицы
ALLOW_GROUP_CHAT=true
AUTHORIZED_GROUP_ID=-4954808885
```

**Переменные Google Sheets (из service account JSON):**
```
GOOGLE_TYPE=service_account
GOOGLE_PROJECT_ID=ваш_project_id
GOOGLE_PRIVATE_KEY_ID=ваш_private_key_id
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nваш_private_key\n-----END PRIVATE KEY-----\n"
GOOGLE_CLIENT_EMAIL=ваш_service_account_email
GOOGLE_CLIENT_ID=ваш_client_id
GOOGLE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GOOGLE_CLIENT_X509_CERT_URL=ваш_cert_url
```

### 3. Настройка Google Service Account

1. Перейдите в Google Cloud Console
2. Создайте новый Service Account
3. Скачайте JSON ключ
4. Добавьте email service account в Google Sheets с правами редактора
5. Скопируйте данные из JSON в переменные окружения Railway

### 4. Деплой

1. После настройки переменных Railway автоматически запустит деплой
2. Проверьте логи в интерфейсе Railway
3. Railway автоматически предоставит URL для webhook

### 5. Настройка Webhook

Railway автоматически настроит webhook используя переменную `RAILWAY_STATIC_URL`.
Бот будет работать в webhook режиме для лучшей производительности.

## Мониторинг

- Логи доступны в Railway Dashboard
- Проверьте статус бота командой `/start`
- Мониторьте Google Sheets для проверки записи транзакций

## Troubleshooting

### Проблемы с Google Sheets
- Проверьте правильность всех переменных окружения
- Убедитесь что service account имеет доступ к таблице
- Проверьте формат GOOGLE_PRIVATE_KEY (должен содержать \n)

### Проблемы с ботом
- Проверьте BOT_TOKEN
- Убедитесь что все user ID корректны
- Проверьте логи Railway для ошибок

## Полезные команды

```bash
# Локальная разработка
python run.py

# Тестирование продакшен скрипта локально
python deploy.py

# Проверка переменных окружения
python -c "from bot.config import Config; print('Config OK')"
```