"""
Google Sheets service for the Telegram Finance Bot.

Handles integration with Google Sheets API for storing transaction data.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

import gspread
from google.oauth2.service_account import Credentials
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
            raise GoogleSheetsError(f"Initialization failed: {e}")
    
    async def _connect(self) -> None:
        """Connect to Google Sheets API."""
        def _sync_connect():
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            if not os.path.exists(self.config.GOOGLE_CREDENTIALS_FILE):
                raise GoogleSheetsError(f"Credentials file not found: {self.config.GOOGLE_CREDENTIALS_FILE}")
            
            creds = Credentials.from_service_account_file(
                self.config.GOOGLE_CREDENTIALS_FILE, 
                scopes=scope
            )
            
            # Create client
            self.client = gspread.authorize(creds)
            
            # Open spreadsheet
            self.spreadsheet = self.client.open_by_key(self.config.GOOGLE_SPREADSHEET_ID)
            
            return True
        
        # Run synchronous operation in thread pool
        await asyncio.get_event_loop().run_in_executor(
            self.executor, _sync_connect
        )
    
    async def _setup_sheets(self) -> None:
        """Setup required sheets and headers."""
        def _sync_setup():
            # Get current month sheet name
            current_month = datetime.now().strftime("%Y-%m")
            
            try:
                # Try to get existing sheet
                worksheet = self.spreadsheet.worksheet(current_month)
                logger.info("Using existing sheet", sheet_name=current_month)
            except gspread.WorksheetNotFound:
                # Create new sheet for current month
                worksheet = self.spreadsheet.add_worksheet(
                    title=current_month, 
                    rows=1000, 
                    cols=len(self.headers)
                )
                
                # Add headers
                worksheet.update('A1', [self.headers])
                logger.info("Created new sheet", sheet_name=current_month)
            
            # Ensure headers are correct
            current_headers = worksheet.row_values(1)
            if current_headers != self.headers:
                worksheet.update('A1', [self.headers])
                logger.info("Updated sheet headers", sheet_name=current_month)
            
            return worksheet
        
        await asyncio.get_event_loop().run_in_executor(
            self.executor, _sync_setup
        )
    
    async def add_transaction(self, transaction: Transaction) -> int:
        """
        Add transaction to Google Sheets.
        
        Args:
            transaction: Transaction to add
            
        Returns:
            Row number where transaction was added
        """
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