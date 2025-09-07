"""
Google Sheets service for the Telegram Finance Bot.

Handles integration with Google Sheets API for storing transaction data.
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
    """Service for Google Sheets integration."""
    
    def __init__(self):
        """Initialize Google Sheets service."""
        self.config = get_config()
        self.client = None
        self.spreadsheet = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Headers for the transaction sheet
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
            # Don't raise the error - let the bot continue without Sheets
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
                    
                    # Load credentials
                    if not os.path.exists(self.config.GOOGLE_CREDENTIALS_FILE):
                        raise GoogleSheetsError(f"Credentials file not found: {self.config.GOOGLE_CREDENTIALS_FILE}")
                    
                    # Create credentials with explicit token URI and additional claims
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
                        # Wait before retrying
                        time.sleep(2 ** attempt)  # Exponential backoff
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
        
        # Run synchronous operation in thread pool
        await asyncio.get_event_loop().run_in_executor(
            self.executor, _sync_connect
        )
    
    async def _setup_sheets(self) -> None:
        """Setup required sheets and headers."""
        def _sync_setup():
            # Get current month sheet name
            current_month = datetime.now().strftime("%Y-%m")
            
            # Setup comprehensive month sheet with all sections
            self._setup_comprehensive_month_sheet(current_month)
            
            return True
        
        await asyncio.get_event_loop().run_in_executor(
            self.executor, _sync_setup
        )
    
    def _setup_transactions_sheet(self, month_name: str) -> None:
        """Setup main transactions sheet for the month."""
        try:
            # Try to get existing sheet
            worksheet = self.spreadsheet.worksheet(month_name)
            logger.info("Using existing sheet", sheet_name=month_name)
        except gspread.WorksheetNotFound:
            # Create new sheet for current month
            worksheet = self.spreadsheet.add_worksheet(
                title=month_name, 
                rows=1000, 
                cols=len(self.headers)
            )
            
            # Add headers
            worksheet.update('A1', [self.headers])
            logger.info("Created new sheet", sheet_name=month_name)
        
        # Ensure headers are correct
        current_headers = worksheet.row_values(1)
        if current_headers != self.headers:
            worksheet.update('A1', [self.headers])
            logger.info("Updated sheet headers", sheet_name=month_name)
    
    def _setup_analytics_sheets(self, month_name: str) -> None:
        """Setup analytics sheets for expenses, income and balance."""
        
        # Categories for expenses and income
        expense_categories = [
            "Продукты питания", "Транспорт", "Развлечения", "Покупки", 
            "Здоровье", "Коммунальные услуги", "Образование", "Прочие расходы"
        ]
        
        income_categories = [
            "Зарплата", "Фриланс", "Премия", "Подработка", "Прочие доходы"
        ]
        
        # Setup expenses sheet
        self._setup_category_analysis_sheet(
            f"Расходы-{month_name}", 
            expense_categories,
            "Ежедневные расходы по категориям"
        )
        
        # Setup income sheet
        self._setup_category_analysis_sheet(
            f"Доходы-{month_name}", 
            income_categories,
            "Ежедневные доходы по категориям"
        )
        
        # Setup balance sheet
        self._setup_balance_sheet(f"Сальдо-{month_name}")
    
    def _setup_category_analysis_sheet(self, sheet_name: str, categories: List[str], description: str) -> None:
        """Setup sheet for category analysis (expenses or income)."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logger.info("Using existing analytics sheet", sheet_name=sheet_name)
            return
        except gspread.WorksheetNotFound:
            pass
        
        # Create new analytics sheet
        worksheet = self.spreadsheet.add_worksheet(
            title=sheet_name,
            rows=50,
            cols=len(categories) + 2  # Date + categories + Total
        )
        
        # Setup headers
        headers = ["Дата"] + categories + ["Итого"]
        worksheet.update('A1', [headers])
        time.sleep(1)  # Rate limit protection
        
        # Add description
        worksheet.update('A2', [[description]])
        time.sleep(1)  # Rate limit protection
        
        # Get current month dates (just for counting days)
        current_date = datetime.now().replace(day=1)
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1)
        
        # Add dates for current month (without formulas for now)
        row = 3
        current_day = current_date
        batch_data = []
        while current_day < next_month and len(batch_data) < 10:  # Limit to first 10 days to avoid quota
            day_str = current_day.strftime("%d.%m.%Y")
            batch_data.append([day_str] + [''] * len(categories) + [''])  # Empty cells for amounts
            current_day += timedelta(days=1)
        
        if batch_data:
            worksheet.update(f'A{row}', batch_data)
            time.sleep(1)  # Rate limit protection
        
        # Add monthly totals header (will be populated later)
        totals_row = row + len(batch_data)
        worksheet.update(f'A{totals_row}', "ИТОГО ЗА МЕСЯЦ")
        time.sleep(1)  # Rate limit protection
        
        # Format the sheet
        worksheet.format('A1:ZZ1', {
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
            'textFormat': {'bold': True}
        })
        
        worksheet.format(f'A{row}:ZZ{row}', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True}
        })
        
        logger.info("Created analytics sheet", sheet_name=sheet_name)
    
    def _setup_balance_sheet(self, sheet_name: str) -> None:
        """Setup balance sheet showing daily income vs expenses."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logger.info("Using existing balance sheet", sheet_name=sheet_name)
            return
        except gspread.WorksheetNotFound:
            pass
        
        # Create balance sheet
        worksheet = self.spreadsheet.add_worksheet(
            title=sheet_name,
            rows=50,
            cols=5  # Date, Income, Expenses, Balance, Cumulative
        )
        
        # Setup headers
        headers = ["Дата", "Доходы", "Расходы", "Сальдо", "Накопительный итог"]
        worksheet.update('A1', [headers])
        time.sleep(1)  # Rate limit protection
        
        # Add description
        worksheet.update('A2', [["Ежедневный баланс доходов и расходов"]])
        time.sleep(1)  # Rate limit protection
        
        # Add first few days as template
        current_date = datetime.now().replace(day=1)
        batch_data = []
        for i in range(min(7, 31)):  # First week as template
            day = current_date + timedelta(days=i)
            day_str = day.strftime("%d.%m.%Y")
            batch_data.append([day_str, '', '', '', ''])  # Empty values for now
        
        worksheet.update('A3', batch_data)
        time.sleep(1)  # Rate limit protection
        
        # Format the sheet
        worksheet.format('A1:E1', {
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
            'textFormat': {'bold': True}
        })
        
        worksheet.format(f'A{row}:E{row}', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True}
        })
        
        # Color positive balance green, negative red
        worksheet.format(f'D3:D{row-1}', {
            'numberFormat': {'type': 'CURRENCY', 'pattern': '#,##0.00 ₽'}
        })
        
        logger.info("Created balance sheet", sheet_name=sheet_name)
    
    def _update_analytics_sheets(self, transaction: Transaction, month_name: str) -> None:
        """Update analytics sheets when a new transaction is added."""
        try:
            # Determine transaction type and target sheet
            if transaction.transaction_type.value == 'expense':
                analytics_sheet_name = f"Расходы-{month_name}"
            else:
                analytics_sheet_name = f"Доходы-{month_name}"
            
            # Get the analytics sheet
            try:
                analytics_sheet = self.spreadsheet.worksheet(analytics_sheet_name)
            except gspread.WorksheetNotFound:
                logger.warning(f"Analytics sheet not found: {analytics_sheet_name}")
                return
            
            # Find the date row
            transaction_date = transaction.date.strftime("%d.%m.%Y")
            all_dates = analytics_sheet.col_values(1)  # Column A has dates
            
            date_row = None
            for i, date_cell in enumerate(all_dates):
                if date_cell == transaction_date:
                    date_row = i + 1  # gspread uses 1-based indexing
                    break
            
            if not date_row:
                logger.warning(f"Date not found in analytics sheet: {transaction_date}")
                return
            
            # Get category column
            headers = analytics_sheet.row_values(1)
            category_col = None
            for i, header in enumerate(headers):
                if header == transaction.category:
                    category_col = i + 1  # gspread uses 1-based indexing
                    break
            
            if not category_col:
                # Try to find "Прочие" category as fallback
                for i, header in enumerate(headers):
                    if "прочи" in header.lower():
                        category_col = i + 1
                        break
            
            if category_col:
                # Get current value and add transaction amount
                try:
                    current_value = analytics_sheet.cell(date_row, category_col).value
                    current_amount = float(current_value) if current_value else 0.0
                except (ValueError, TypeError):
                    current_amount = 0.0
                
                new_amount = current_amount + float(transaction.amount)
                analytics_sheet.update_cell(date_row, category_col, new_amount)
                
                logger.info(
                    "Updated analytics sheet",
                    sheet_name=analytics_sheet_name,
                    date=transaction_date,
                    category=transaction.category,
                    amount=float(transaction.amount)
                )
            else:
                logger.warning(
                    "Category not found in analytics sheet",
                    category=transaction.category,
                    available_categories=headers
                )
                
        except Exception as e:
            logger.error(f"Failed to update analytics sheets: {e}")
    
    async def add_transaction(self, transaction: Transaction) -> int:
        """
        Add transaction to Google Sheets.
        
        Args:
            transaction: Transaction to add
            
        Returns:
            Row number where transaction was added (0 if Sheets unavailable)
        """
        if not self.client or not self.spreadsheet:
            logger.warning("Google Sheets not available, skipping transaction save")
            return 0
            
        try:
            def _sync_add():
                # Get current month sheet
                sheet_name = transaction.date.strftime("%Y-%m") if transaction.date else datetime.now().strftime("%Y-%m")
                
                try:
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                except gspread.WorksheetNotFound:
                    # Create sheet if it doesn't exist
                    worksheet = self.spreadsheet.add_worksheet(
                        title=sheet_name,
                        rows=1000,
                        cols=len(self.headers)
                    )
                    worksheet.update('A1', [self.headers])
                
                # Prepare row data
                row_data = transaction.to_spreadsheet_row()
                
                # Add row
                worksheet.append_row(row_data)
                
                # Get the row number of the added transaction
                all_values = worksheet.get_all_values()
                row_number = len(all_values)
                
                # Create analytics sheets if they don't exist (first transaction of the month)
                if row_number == 2:  # First transaction (row 1 is headers)
                    self._setup_analytics_sheets(sheet_name)
                
                # Update analytics sheets
                self._update_analytics_sheets(transaction, sheet_name)
                
                return row_number
            
            row_number = await asyncio.get_event_loop().run_in_executor(
                self.executor, _sync_add
            )
            
            logger.info(
                "Transaction added to Google Sheets",
                row_number=row_number,
                user_id=transaction.user_id,
                amount=str(transaction.amount),
                category=transaction.category
            )
            
            return row_number
            
        except Exception as e:
            logger.error("Failed to add transaction to Google Sheets", error=str(e))
            raise GoogleSheetsError(f"Failed to add transaction: {e}")
    
    async def update_transaction(self, row_number: int, transaction: Transaction, sheet_name: Optional[str] = None) -> None:
        """
        Update existing transaction in Google Sheets.
        
        Args:
            row_number: Row number to update
            transaction: Updated transaction data
            sheet_name: Sheet name (defaults to current month)
        """
        try:
            def _sync_update():
                if sheet_name is None:
                    current_sheet_name = transaction.date.strftime("%Y-%m") if transaction.date else datetime.now().strftime("%Y-%m")
                else:
                    current_sheet_name = sheet_name
                
                worksheet = self.spreadsheet.worksheet(current_sheet_name)
                row_data = transaction.to_spreadsheet_row()
                
                # Update the specific row
                range_name = f"A{row_number}:{chr(ord('A') + len(self.headers) - 1)}{row_number}"
                worksheet.update(range_name, [row_data])
            
            await asyncio.get_event_loop().run_in_executor(
                self.executor, _sync_update
            )
            
            logger.info("Transaction updated in Google Sheets", row_number=row_number)
            
        except Exception as e:
            logger.error("Failed to update transaction in Google Sheets", error=str(e))
            raise GoogleSheetsError(f"Failed to update transaction: {e}")
    
    async def get_monthly_transactions(self, year: int, month: int) -> List[List[str]]:
        """
        Get all transactions for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            List of transaction rows
        """
        try:
            def _sync_get():
                sheet_name = f"{year}-{month:02d}"
                
                try:
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                    all_values = worksheet.get_all_values()
                    
                    # Return all rows except header
                    return all_values[1:] if len(all_values) > 1 else []
                except gspread.WorksheetNotFound:
                    return []
            
            transactions = await asyncio.get_event_loop().run_in_executor(
                self.executor, _sync_get
            )
            
            logger.info("Retrieved monthly transactions", year=year, month=month, count=len(transactions))
            return transactions
            
        except Exception as e:
            logger.error("Failed to get monthly transactions", error=str(e))
            raise GoogleSheetsError(f"Failed to get transactions: {e}")
    
    async def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get monthly summary statistics.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            transactions = await self.get_monthly_transactions(year, month)
            
            if not transactions:
                return {
                    "total_income": 0,
                    "total_expenses": 0,
                    "net_amount": 0,
                    "transaction_count": 0,
                    "categories": {}
                }
            
            total_income = 0
            total_expenses = 0
            categories = {}
            
            for row in transactions:
                if len(row) >= 5:  # Ensure we have enough columns
                    try:
                        transaction_type = row[2]  # Type column
                        amount = float(row[3])     # Amount column
                        category = row[4]          # Category column
                        
                        if transaction_type == "income":
                            total_income += amount
                        else:
                            total_expenses += amount
                        
                        # Count categories
                        if category in categories:
                            categories[category] += amount
                        else:
                            categories[category] = amount
                            
                    except (ValueError, IndexError):
                        continue  # Skip invalid rows
            
            summary = {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_amount": total_income - total_expenses,
                "transaction_count": len(transactions),
                "categories": categories
            }
            
            logger.info("Generated monthly summary", year=year, month=month, summary=summary)
            return summary
            
        except Exception as e:
            logger.error("Failed to generate monthly summary", error=str(e))
            raise GoogleSheetsError(f"Failed to generate summary: {e}")
    
    async def test_connection(self) -> bool:
        """
        Test connection to Google Sheets.
        
        Returns:
            True if connection is successful
        """
        try:
            def _sync_test():
                if self.spreadsheet:
                    # Try to get spreadsheet title
                    title = self.spreadsheet.title
                    return True
                return False
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _sync_test
            )
            
            logger.info("Google Sheets connection test", success=result)
            return result
            
        except Exception as e:
            logger.error("Google Sheets connection test failed", error=str(e))
            return False
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Global service instance
sheets_service = GoogleSheetsService()


async def get_sheets_service() -> GoogleSheetsService:
    """
    Get the global Google Sheets service instance.
    
    Returns:
        GoogleSheetsService instance
    """
    if sheets_service.client is None:
        await sheets_service.initialize()
    return sheets_service


async def add_transaction_to_sheets(transaction: Transaction) -> int:
    """
    Add transaction to Google Sheets.
    
    Args:
        transaction: Transaction to add
        
    Returns:
        Row number where transaction was added
    """
    service = await get_sheets_service()
    return await service.add_transaction(transaction)