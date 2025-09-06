# 💰 Telegram Finance Bot

A smart Telegram bot for tracking family finances. Automatically categorizes your expenses and income, and saves everything to Google Sheets for easy tracking and analysis.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Aiogram](https://img.shields.io/badge/aiogram-3.4+-orange.svg)

## 🌟 Features

- **🤖 Natural Language Processing**: Simply send messages like "потратил 500 руб на продукты"
- **🏷️ Automatic Categorization**: Smart category detection based on keywords
- **📊 Google Sheets Integration**: All transactions automatically saved to spreadsheets
- **👥 Multi-User Support**: Perfect for couples tracking finances together
- **🔐 Secure Authorization**: Only authorized users can access the bot
- **📱 User-Friendly Commands**: Easy-to-use commands for stats and help
- **🌍 Russian Language Support**: Designed for Russian-speaking users
- **💾 Data Validation**: Robust validation and error handling

## 📋 Supported Transaction Types

### 💸 Expenses
- 🛒 Продукты питания (Food)
- 🚗 Транспорт (Transportation)
- 🎉 Развлечения (Entertainment)
- 👕 Одежда (Clothing)
- 🏥 Здоровье/медицина (Health/Medicine)
- 🏠 Коммунальные услуги (Utilities)
- 💳 Прочие расходы (Other expenses)

### 💰 Income
- 💼 Зарплата (Salary)
- 🔧 Подработка (Side job)
- 💰 Прочие доходы (Other income)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Service Account credentials
- Google Sheets document

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd planmoney
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the bot**
   ```bash
   python run.py
   ```

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Authorized Users (Telegram IDs)
AUTHORIZED_USER_1=your_telegram_id_here
AUTHORIZED_USER_2=girlfriend_telegram_id_here

# Google Sheets Configuration
GOOGLE_CREDENTIALS_FILE=credentials/google_service_account.json
GOOGLE_SPREADSHEET_ID=your_google_spreadsheet_id_here

# Optional Settings
LOG_LEVEL=INFO
DEFAULT_CURRENCY=RUB
TIMEZONE=Europe/Moscow
```

### Google Sheets Setup

1. **Create a Google Service Account**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Sheets API
   - Create service account credentials
   - Download JSON key file

2. **Setup Google Sheet**
   - Create a new Google Sheets document
   - Share it with your service account email
   - Copy the spreadsheet ID from URL

3. **Place credentials**
   ```bash
   # Put your JSON key file here:
   credentials/google_service_account.json
   ```

## 💬 Usage Examples

### Adding Expenses
```
потратил 500 руб на продукты
купила кофе 150р
такси 300 рублей
500₽ продукты в Пятерочке
оплатил интернет 800 руб
```

### Adding Income
```
получил зарплату 50000 руб
подработка 5000р
+10000 руб премия
заработал 15000 руб
```

### Bot Commands
- `/start` - Welcome message and instructions
- `/help` - Detailed help and examples
- `/stats` - Monthly statistics
- `/categories` - List of available categories
- `/balance` - Current month balance

## 🏗️ Project Structure

```
planmoney/
├── bot/
│   ├── __init__.py
│   ├── main.py                    # Bot entry point
│   ├── config.py                  # Configuration management
│   ├── handlers/
│   │   ├── commands.py            # Command handlers
│   │   ├── messages.py            # Message handlers
│   │   └── errors.py              # Error handlers
│   ├── middlewares/
│   │   ├── auth.py                # User authorization
│   │   └── logging.py             # Request logging
│   ├── utils/
│   │   ├── parser.py              # Message parsing
│   │   ├── categories.py          # Category classification
│   │   └── validators.py          # Data validation
│   ├── services/
│   │   └── google_sheets.py       # Google Sheets integration
│   └── models/
│       ├── user.py                # User data model
│       └── transaction.py         # Transaction data model
├── tests/
│   └── test_basic.py              # Unit tests
├── credentials/                   # Google credentials (not in git)
├── logs/                         # Log files
├── .env                          # Environment variables (not in git)
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── run.py                        # Startup script
└── README.md                     # This file
```

## 🧪 Testing

Run the test suite:

```bash
# Activate virtual environment
venv\Scripts\activate

# Run tests
python tests/test_basic.py

# Test bot setup without starting
python run.py --test

# Validate environment
python run.py --validate
```

## 📊 Data Structure

### Google Sheets Columns
| Column | Description |
|--------|-------------|
| Дата | Transaction date and time |
| Пользователь | User Telegram ID |
| Тип | Transaction type (income/expense) |
| Сумма | Amount |
| Категория | Category |
| Описание | Description |
| Telegram ID | Message ID for reference |

### Monthly Sheets
The bot automatically creates separate sheets for each month (format: `YYYY-MM`).

## 🛡️ Security Features

- **User Authorization**: Only configured Telegram IDs can use the bot
- **Input Validation**: All user input is validated and sanitized
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: All activities are logged for monitoring
- **Rate Limiting**: Protection against spam and abuse

## 🚀 Deployment Options

### Local Development
```bash
python run.py
```

### Production Deployment

1. **Heroku**
   - Add buildpack for Python
   - Set environment variables
   - Deploy with webhook mode

2. **VPS/Cloud Server**
   - Use systemd service
   - Set up reverse proxy (nginx)
   - Configure SSL certificate

3. **Docker** (future enhancement)
   ```bash
   docker build -t finance-bot .
   docker run -d --env-file .env finance-bot
   ```

## 📈 Monitoring and Analytics

### Built-in Statistics
- Monthly income/expense totals
- Category breakdowns
- Transaction counts
- Balance calculations

### Logging
- All transactions logged
- Error tracking
- Performance monitoring
- User activity tracking

## 🔄 Future Enhancements

- [ ] Budget planning and alerts
- [ ] Export to different formats (Excel, CSV)
- [ ] Multiple currency support
- [ ] Banking integration
- [ ] Web dashboard
- [ ] Mobile app
- [ ] Advanced analytics and charts
- [ ] Recurring transaction templates
- [ ] Family member management
- [ ] Receipt photo processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Bot doesn't respond**
- Check BOT_TOKEN in .env
- Verify user IDs are correct
- Check bot logs for errors

**Google Sheets errors**
- Verify service account credentials
- Check spreadsheet permissions
- Ensure API is enabled

**Parsing issues**
- Use clear message format
- Include amount and currency
- Check supported keywords

### Getting Help

1. Check the logs in `logs/bot.log`
2. Run tests: `python tests/test_basic.py`
3. Validate setup: `python run.py --test`
4. Create an issue with error details

## 👨‍💻 Development

### Setting up Development Environment

```bash
# Clone and setup
git clone <repo-url>
cd planmoney
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Run tests
python tests/test_basic.py

# Start development
python run.py --verbose
```

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests for new features

---

Made with ❤️ for family finance tracking