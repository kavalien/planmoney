"""
Google Sheets service for the Telegram Finance Bot.

Handles integration with Google Sheets API for storing transaction data with comprehensive monthly sheets.
"""

import os
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
import structlog

from ..config import get_config
from ..models.transaction import Transaction

logger = structlog.get_logger()


class GoogleSheetsError(Exception):
    """Custom exception for Google Sheets operations."""
    pass


class GoogleSheetsService:
    """Service for Google Sheets integration with comprehensive monthly sheets."""
    
    def __init__(self):
        """Initialize Google Sheets service."""
        self.config = get_config()
        self.client = None
        self.spreadsheet = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Headers for the transaction section
        self.headers = [
            "Дата",
            "Пользователь", 
            "Тип",
            "Сумма",
            "Категория",
            "Описание",
            "Telegram ID"
        ]
        
        logger.info("Google Sheets service initialized")
    
    async def initialize(self) -> None:
        """Initialize connection to Google Sheets."""
        try:
            await self._connect()
            await self._setup_sheets()
            logger.info("Google Sheets service ready")
        except Exception as e:
            logger.error("Failed to initialize Google Sheets service", error=str(e))
            logger.warning("Bot will continue without Google Sheets functionality")
            self.client = None
            self.spreadsheet = None
    
    async def _connect(self) -> None:
        """Connect to Google Sheets API with retry logic."""
        def _sync_connect():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Define the scope
                    scope = [
                        'https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive'
                    ]
                    
                    # Try environment variables first (for Railway/production)
                    google_type = os.getenv('GOOGLE_TYPE')
                    if google_type == 'service_account':
                        # Use environment variables
                        service_account_info = {
                            "type": os.getenv('GOOGLE_TYPE'),
                            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                            "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
                            "private_key": os.getenv('GOOGLE_PRIVATE_KEY', '').replace('\\n', '\n'),
                            "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
                            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                            "auth_uri": os.getenv('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
                            "token_uri": os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
                            "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                            "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
                        }
                        
                        # Check if all required fields are present
                        required_fields = ['project_id', 'private_key', 'client_email']
                        missing_fields = [field for field in required_fields if not service_account_info.get(field)]
                        
                        if missing_fields:
                            raise GoogleSheetsError(f"Missing required environment variables: {missing_fields}")
                        
                        logger.info("Using Google Service Account from environment variables")
                        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
                        
                    else:
                        # Fallback to credentials file (for local development)
                        if not os.path.exists(self.config.GOOGLE_CREDENTIALS_FILE):
                            raise GoogleSheetsError(f"Credentials file not found: {self.config.GOOGLE_CREDENTIALS_FILE}")
                        
                        logger.info("Using Google Service Account from credentials file")
                        creds = Credentials.from_service_account_file(
                            self.config.GOOGLE_CREDENTIALS_FILE, 
                            scopes=scope
                        )
                    
                    # Only refresh credentials if they are actually expired
                    if creds.expired:
                        logger.info("Refreshing expired Google credentials")
                        request = Request()
                        creds.refresh(request)
                    elif not creds.valid:
                        logger.info("Refreshing invalid Google credentials")
                        request = Request()
                        creds.refresh(request)
                    
                    # Create client
                    self.client = gspread.authorize(creds)
                    
                    # Test connection by trying to open spreadsheet
                    self.spreadsheet = self.client.open_by_key(self.config.GOOGLE_SPREADSHEET_ID)
                    
                    logger.info("Google Sheets connection successful", attempt=attempt+1)
                    return True
                    
                except RefreshError as e:
                    logger.warning(f"JWT refresh error on attempt {attempt+1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise GoogleSheetsError(f"Failed to refresh JWT token after {max_retries} attempts: {e}")
                        
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt+1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise GoogleSheetsError(f"Failed to connect after {max_retries} attempts: {e}")
            
            return False
        
        await asyncio.get_event_loop().run_in_executor(self.executor, _sync_connect)
    
    async def _setup_sheets(self) -> None:
        """Setup required sheets and headers."""
        def _sync_setup():
            current_month = datetime.now().strftime("%Y-%m")
            self._setup_comprehensive_month_sheet(current_month)
            return True
        
        await asyncio.get_event_loop().run_in_executor(self.executor, _sync_setup)
    
    def _setup_comprehensive_month_sheet(self, month_name: str) -> None:
        """Setup comprehensive month sheet with column-based structure."""
        try:
            worksheet = self.spreadsheet.worksheet(month_name)
            logger.info("Using existing comprehensive sheet", sheet_name=month_name)
            return
        except gspread.WorksheetNotFound:
            pass
        
        # Create new comprehensive sheet with column-based structure
        worksheet = self.spreadsheet.add_worksheet(
            title=month_name,
            rows=100,  # Fewer rows needed with column structure
            cols=30    # More columns for different sections
        )
        
        # Section 1: Detailed Transactions (Columns A-G)
        self._setup_transactions_columns(worksheet)
        
        # Section 2: Expense Categories (Columns I-Q)
        self._setup_expense_columns(worksheet)
        
        # Section 3: Income Categories (Columns S-X)
        self._setup_income_columns(worksheet)
        
        # Section 4: Daily Balance (Columns Z-AD)
        self._setup_balance_columns(worksheet)
        
        logger.info("Created comprehensive month sheet with column structure", sheet_name=month_name)
    
    def _setup_transactions_columns(self, worksheet) -> None:
        """Setup detailed transactions in columns A-G."""
        # Section header in row 1
        worksheet.update('A1', "ДЕТАЛЬНЫЕ ТРАНЗАКЦИИ")
        time.sleep(0.5)
        
        # Column headers in row 2
        worksheet.update('A2:G2', [self.headers])
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
    
    def _setup_expense_columns(self, worksheet) -> None:
        """Setup expense categories in columns I-Q."""
        expense_categories = [
            "Продукты питания", "Транспорт", "Развлечения", "Покупки",
            "Здоровье", "Коммунальные услуги", "Образование", "Прочие расходы"
        ]
        
        headers = ["Дата"] + expense_categories + ["Итого"]
        
        # Section header in row 1
        worksheet.update('I1', "РАСХОДЫ ПО КАТЕГОРИЯМ")
        time.sleep(0.5)
        
        # Column headers in row 2 (I to R = 10 columns)
        worksheet.update('I2:R2', [headers])
        time.sleep(0.5)
        
        # Add dates for entire month
        self._add_sample_dates(worksheet, 'I', 3)
        
        # Format section header
        worksheet.format('I1:R1', {
            'backgroundColor': {'red': 0.9, 'green': 0.4, 'blue': 0.4},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        
        # Format column headers
        worksheet.format('I2:R2', {
            'backgroundColor': {'red': 0.9, 'green': 0.7, 'blue': 0.7},
            'textFormat': {'bold': True}
        })
    
    def _setup_income_columns(self, worksheet) -> None:
        """Setup income categories in columns S-X."""
        income_categories = [
            "Зарплата", "Фриланс", "Премия", "Подработка", "Прочие доходы"
        ]
        
        headers = ["Дата"] + income_categories + ["Итого"]
        
        # Section header in row 1
        worksheet.update('S1', "ДОХОДЫ ПО КАТЕГОРИЯМ")
        time.sleep(0.5)
        
        # Column headers in row 2 (S to Y = 7 columns)
        worksheet.update('S2:Y2', [headers])
        time.sleep(0.5)
        
        # Add dates for entire month
        self._add_sample_dates(worksheet, 'S', 3)
        
        # Format section header
        worksheet.format('S1:Y1', {
            'backgroundColor': {'red': 0.4, 'green': 0.9, 'blue': 0.4},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        
        # Format column headers
        worksheet.format('S2:Y2', {
            'backgroundColor': {'red': 0.7, 'green': 0.9, 'blue': 0.7},
            'textFormat': {'bold': True}
        })
    
    def _setup_balance_columns(self, worksheet) -> None:
        """Setup daily balance in columns Z-AD."""
        headers = ["Дата", "Доходы", "Расходы", "Сальдо", "Накопительно"]
        
        # Section header in row 1
        worksheet.update('Z1', "ЕЖЕДНЕВНЫЙ БАЛАНС")
        time.sleep(0.5)
        
        # Column headers in row 2 (Z to AD = 5 columns)
        worksheet.update('Z2:AD2', [headers])
        time.sleep(0.5)
        
        # Add dates for entire month
        self._add_sample_dates(worksheet, 'Z', 3)
        
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
    
    def _add_sample_dates(self, worksheet, start_col: str, start_row: int, max_days: int = None) -> None:
        """Add dates for the entire month to a column."""
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
        
        logger.info(f"Added {days_to_add} dates to column {start_col} for month {month}/{year}")
    
    async def add_transaction(self, transaction: Transaction) -> int:
        """Add transaction to Google Sheets."""
        if not self.client or not self.spreadsheet:
            logger.warning("Google Sheets not available, skipping transaction save")
            return 0
            
        try:
            def _sync_add():
                sheet_name = transaction.date.strftime("%Y-%m") if transaction.date else datetime.now().strftime("%Y-%m")
                
                try:
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                except gspread.WorksheetNotFound:
                    # Create new comprehensive sheet
                    self._setup_comprehensive_month_sheet(sheet_name)
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                
                # Add to transactions section (starting from row 3, columns A-G)
                row_data = transaction.to_spreadsheet_row()
                
                # Find next empty row in transactions section (rows 3-50, columns A-G)
                transactions_data = worksheet.get('A3:A50')
                next_row = 3
                for i, row in enumerate(transactions_data):
                    if not row or not row[0]:  # Empty row
                        next_row = 3 + i
                        break
                else:
                    next_row = 3 + len(transactions_data)
                
                # Add transaction to columns A-G
                worksheet.update(f'A{next_row}:G{next_row}', [row_data])
                
                # Update analytics sections in their respective columns
                self._update_analytics_in_columns(worksheet, transaction)
                
                return next_row
            
            row_number = await asyncio.get_event_loop().run_in_executor(
                self.executor, _sync_add
            )
            
            logger.info(
                "Transaction added to comprehensive sheet",
                row_number=row_number,
                user_id=transaction.user_id,
                amount=str(transaction.amount),
                category=transaction.category
            )
            
            return row_number
            
        except Exception as e:
            logger.error("Failed to add transaction to Google Sheets", error=str(e))
            raise GoogleSheetsError(f"Failed to add transaction: {e}")
    
    def _update_analytics_in_columns(self, worksheet, transaction: Transaction) -> None:
        """Update analytics sections in their respective columns."""
        transaction_date = transaction.date.strftime("%d.%m")
        
        try:
            # Update expenses section (columns I-R)
            if transaction.transaction_type.value == 'expense':
                self._update_expense_columns(worksheet, transaction, transaction_date)
            
            # Update income section (columns S-Y)  
            else:
                self._update_income_columns(worksheet, transaction, transaction_date)
            
            # Update balance section (columns Z-AD)
            self._update_balance_columns(worksheet, transaction_date)
            
        except Exception as e:
            logger.error(f"Failed to update analytics columns: {e}")
    
    def _update_expense_columns(self, worksheet, transaction: Transaction, date_str: str) -> None:
        """Update expense analytics in columns I-R."""
        try:
            # Find or create date row in expense section (starting from row 3)
            target_row = self._find_or_create_date_row(worksheet, date_str, 'I', 3, 50)
            
            # Get ALL headers from row 2 and extract the expense section
            all_headers = worksheet.row_values(2)
            logger.info(f"All headers row 2: {all_headers}")
            
            # Extract expense headers (should start from column I = index 8)
            # Expected: ["Дата", "Продукты питания", "Транспорт", ...]
            if len(all_headers) >= 18:  # Ensure we have enough columns
                expense_headers = all_headers[8:18]  # Columns I-R (8-17 in 0-based)
            else:
                # Fallback: get headers directly from expense section
                expense_headers = worksheet.range('I2:R2')
                expense_headers = [cell.value for cell in expense_headers]
            
            logger.info(f"Expense headers: {expense_headers}")
            logger.info(f"Looking for category: '{transaction.category}'")
            
            # Find matching category column
            category_col = None
            for i, header in enumerate(expense_headers):
                if header and header.strip() == transaction.category.strip():
                    category_col = 9 + i  # Column I is 9 (1-based)
                    logger.info(f"Found exact match: '{header}' at column {category_col}")
                    break
            
            if not category_col:
                # Try partial matching for "Продукты питания" variants
                for i, header in enumerate(expense_headers):
                    if header and ("продукт" in header.lower() and "продукт" in transaction.category.lower()):
                        category_col = 9 + i
                        logger.info(f"Found partial match (продукты): '{header}' at column {category_col}")
                        break
                    elif header and ("транспорт" in header.lower() and "транспорт" in transaction.category.lower()):
                        category_col = 9 + i
                        logger.info(f"Found partial match (транспорт): '{header}' at column {category_col}")
                        break
            
            if not category_col:
                # Find "Прочие расходы" as fallback
                for i, header in enumerate(expense_headers):
                    if header and "прочи" in header.lower():
                        category_col = 9 + i
                        logger.info(f"Using fallback category: '{header}' at column {category_col}")
                        break
            
            if category_col:
                # Update amount
                current_cell = worksheet.cell(target_row, category_col)
                current_value_str = str(current_cell.value) if current_cell.value else "0"
                # Handle comma as decimal separator
                current_value_str = current_value_str.replace(',', '.')
                try:
                    current_value = float(current_value_str)
                except (ValueError, TypeError):
                    current_value = 0.0
                
                new_value = current_value + float(transaction.amount)
                worksheet.update_cell(target_row, category_col, new_value)
                
                # Update total column (column R = 18)
                total_cell = worksheet.cell(target_row, 18)
                total_value_str = str(total_cell.value) if total_cell.value else "0"
                total_value_str = total_value_str.replace(',', '.')
                try:
                    total_value = float(total_value_str)
                except (ValueError, TypeError):
                    total_value = 0.0
                
                new_total = total_value + float(transaction.amount)
                worksheet.update_cell(target_row, 18, new_total)
                
                logger.info(f"Updated expense columns", row=target_row, col=category_col, amount=new_value, category=transaction.category)
            else:
                logger.error(f"Could not find column for expense category: '{transaction.category}'")
                
        except Exception as e:
            logger.error(f"Failed to update expense columns: {e}")
    
    def _update_income_columns(self, worksheet, transaction: Transaction, date_str: str) -> None:
        """Update income analytics in columns S-Y."""
        try:
            # Find or create date row in income section (starting from row 3)
            target_row = self._find_or_create_date_row(worksheet, date_str, 'S', 3, 50)
            
            # Get ALL headers from row 2 and extract the income section
            all_headers = worksheet.row_values(2)
            logger.info(f"All headers for income: {all_headers}")
            
            # Extract income headers (should start from column S = index 18)
            if len(all_headers) >= 25:  # Ensure we have enough columns
                income_headers = all_headers[18:25]  # Columns S-Y (18-24 in 0-based)
            else:
                # Fallback: get headers directly from income section
                income_headers = worksheet.range('S2:Y2')
                income_headers = [cell.value for cell in income_headers]
            
            logger.info(f"Income headers: {income_headers}")
            logger.info(f"Looking for income category: '{transaction.category}'")
            
            # Find matching category column
            category_col = None
            for i, header in enumerate(income_headers):
                if header and header.strip() == transaction.category.strip():
                    category_col = 19 + i  # Column S is 19 (1-based)
                    logger.info(f"Found exact income match: '{header}' at column {category_col}")
                    break
            
            if not category_col:
                # Try partial matching for income categories
                for i, header in enumerate(income_headers):
                    if header and ("зарплат" in header.lower() and "зарплат" in transaction.category.lower()):
                        category_col = 19 + i
                        logger.info(f"Found partial income match (зарплата): '{header}' at column {category_col}")
                        break
                    elif header and ("фриланс" in header.lower() and "фриланс" in transaction.category.lower()):
                        category_col = 19 + i
                        logger.info(f"Found partial income match (фриланс): '{header}' at column {category_col}")
                        break
            
            if not category_col:
                # Find "Прочие доходы" as fallback
                for i, header in enumerate(income_headers):
                    if header and "прочи" in header.lower():
                        category_col = 19 + i
                        logger.info(f"Using fallback income category: '{header}' at column {category_col}")
                        break
            
            if category_col:
                # Update amount
                current_cell = worksheet.cell(target_row, category_col)
                current_value_str = str(current_cell.value) if current_cell.value else "0"
                # Handle comma as decimal separator
                current_value_str = current_value_str.replace(',', '.')
                try:
                    current_value = float(current_value_str)
                except (ValueError, TypeError):
                    current_value = 0.0
                
                new_value = current_value + float(transaction.amount)
                worksheet.update_cell(target_row, category_col, new_value)
                
                # Update total column (column Y = 25)
                total_cell = worksheet.cell(target_row, 25)
                total_value_str = str(total_cell.value) if total_cell.value else "0"
                total_value_str = total_value_str.replace(',', '.')
                try:
                    total_value = float(total_value_str)
                except (ValueError, TypeError):
                    total_value = 0.0
                
                new_total = total_value + float(transaction.amount)
                worksheet.update_cell(target_row, 25, new_total)
                
                logger.info(f"Updated income columns", row=target_row, col=category_col, amount=new_value, category=transaction.category)
            else:
                logger.error(f"Could not find column for income category: '{transaction.category}'")
                
        except Exception as e:
            logger.error(f"Failed to update income columns: {e}")
    
    def _find_or_create_date_row(self, worksheet, date_str: str, date_col: str, start_row: int, end_row: int) -> int:
        """Find existing date row or create new one in specified column."""
        # Get date column data
        date_range = f'{date_col}{start_row}:{date_col}{end_row}'
        dates = worksheet.get(date_range)
        
        # Find existing date
        for i, date_row in enumerate(dates):
            if date_row and date_row[0] == date_str:
                return start_row + i
        
        # Create new date row
        new_row = start_row + len(dates)
        worksheet.update(f'{date_col}{new_row}', date_str)
        return new_row
    
    def _update_balance_columns(self, worksheet, date_str: str) -> None:
        """Update balance section by calculating from expense and income columns."""
        try:
            # Find or create date row in balance section (columns Z-AD)
            target_row = self._find_or_create_date_row(worksheet, date_str, 'Z', 3, 50)
            
            # Calculate daily totals from expense and income sections
            expense_total = 0.0
            income_total = 0.0
            
            # Get expense total from column R (18)
            try:
                expense_cell = worksheet.cell(target_row, 18)
                expense_total = float(expense_cell.value) if expense_cell.value else 0.0
            except:
                pass
            
            # Get income total from column Y (25)
            try:
                income_cell = worksheet.cell(target_row, 25)
                income_total = float(income_cell.value) if income_cell.value else 0.0
            except:
                pass
            
            # Update balance columns (Z=26, AA=27, AB=28, AC=29, AD=30)
            worksheet.update_cell(target_row, 27, income_total)   # AA: Доходы
            worksheet.update_cell(target_row, 28, expense_total)  # AB: Расходы
            
            # Calculate daily balance
            daily_balance = income_total - expense_total
            worksheet.update_cell(target_row, 29, daily_balance)  # AC: Сальдо
            
            # Calculate cumulative balance (simplified - would need previous days)
            worksheet.update_cell(target_row, 30, daily_balance)  # AD: Накопительно
            
            logger.info(f"Updated balance columns", row=target_row, income=income_total, expense=expense_total, balance=daily_balance)
                
        except Exception as e:
            logger.error(f"Failed to update balance columns: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Google Sheets."""
        if not self.client or not self.spreadsheet:
            return False
        return True


# Global service instance
_sheets_service = None

async def get_sheets_service() -> GoogleSheetsService:
    """Get the Google Sheets service instance."""
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = GoogleSheetsService()
        await _sheets_service.initialize()
    return _sheets_service

async def add_transaction_to_sheets(transaction: Transaction) -> int:
    """Add transaction to Google Sheets."""
    sheets_service = await get_sheets_service()
    return await sheets_service.add_transaction(transaction)