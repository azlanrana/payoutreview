"""Google Sheets client for reading trade data and configuration"""

import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from typing import Tuple, Optional, List
from datetime import datetime
from dateutil import parser
import os

from ..models import Trade, Config
from .validators import PreValidator, ValidationError


class SheetsClient:
    """Client for interacting with Google Sheets"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets client
        
        Args:
            credentials_path: Path to service account JSON file
        """
        if credentials_path is None:
            credentials_path = os.getenv(
                'GOOGLE_SERVICE_ACCOUNT_FILE',
                'config/service_account.json'
            )
        
        try:
            self.gc = gspread.service_account(filename=credentials_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Google service account credentials not found at: {credentials_path}. "
                "Please ensure the file exists and GOOGLE_SERVICE_ACCOUNT_FILE is set correctly."
            )
    
    def read_sheet(self, sheet_url: str) -> Tuple[pd.DataFrame, Config]:
        """
        Read trade data and configuration from Google Sheet
        
        Args:
            sheet_url: URL of the Google Sheet
        
        Returns:
            Tuple of (trades_df, config)
        
        Raises:
            ValidationError: If data validation fails
        """
        # Open the spreadsheet
        try:
            spreadsheet = self.gc.open_by_url(sheet_url)
        except gspread.exceptions.APIError as e:
            raise ValidationError(f"Failed to access Google Sheet: {str(e)}")
        
        # Read trades
        trades_df = self._read_trades_tab(spreadsheet)
        
        # Read config (optional)
        config = self._read_config_tab(spreadsheet)
        
        return trades_df, config
    
    def _read_trades_tab(self, spreadsheet) -> pd.DataFrame:
        """Read and validate the Trades tab"""
        try:
            worksheet = spreadsheet.worksheet("Trades")
        except gspread.exceptions.WorksheetNotFound:
            raise ValidationError(
                "Sheet does not contain a 'Trades' tab. "
                "Please ensure the tab is named exactly 'Trades'."
            )
        
        # Read data
        df = get_as_dataframe(
            worksheet,
            evaluate_formulas=True,
            dtype=str  # Read everything as string first
        )
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        if df.empty:
            raise ValidationError("Trades tab is empty")
        
        # Preprocess data types
        df = self._preprocess_trades(df)
        
        # Validate
        PreValidator.validate_dataframe(df)
        
        return df
    
    def _read_config_tab(self, spreadsheet) -> Config:
        """Read configuration from Config tab (optional)"""
        try:
            worksheet = spreadsheet.worksheet("Config")
        except gspread.exceptions.WorksheetNotFound:
            # Config tab is optional, return defaults
            return Config()
        
        # Read as dataframe
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
        df = df.dropna(how='all')
        
        if df.empty:
            return Config()
        
        # Expect format: Parameter | Value
        # Convert to dict
        config_dict = {}
        if 'Parameter' in df.columns and 'Value' in df.columns:
            for _, row in df.iterrows():
                param = str(row['Parameter']).strip()
                value = row['Value']
                if pd.notna(param) and pd.notna(value):
                    config_dict[param] = value
        
        return Config.from_dict(config_dict)
    
    def _preprocess_trades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess trade data (type conversions, parsing)"""
        # Parse timestamps
        for time_field in ['open_time', 'close_time']:
            if time_field in df.columns:
                df[time_field] = pd.to_datetime(
                    df[time_field],
                    errors='coerce',
                    utc=True
                )
        
        # Convert numeric fields
        for numeric_field in ['lot_size', 'profit', 'balance']:
            if numeric_field in df.columns:
                df[numeric_field] = pd.to_numeric(df[numeric_field], errors='coerce')
        
        # Clean string fields
        for str_field in ['ticket', 'pair', 'direction', 'account_type', 'account_id']:
            if str_field in df.columns:
                df[str_field] = df[str_field].astype(str).str.strip()
        
        # Normalize direction to uppercase
        if 'direction' in df.columns:
            df['direction'] = df['direction'].str.upper()
        
        return df
    
    def trades_to_list(self, df: pd.DataFrame) -> List[Trade]:
        """Convert DataFrame to list of Trade objects"""
        trades = []
        for _, row in df.iterrows():
            trade = Trade(
                ticket=str(row['ticket']),
                open_time=row['open_time'].to_pydatetime(),
                close_time=row['close_time'].to_pydatetime(),
                pair=str(row['pair']),
                direction=str(row['direction']),
                lot_size=row['lot_size'],
                profit=row['profit'],
                balance=row['balance'],
                account_type=str(row['account_type']),
                account_id=str(row['account_id'])
            )
            trades.append(trade)
        
        return trades
    
    def write_results_tab(self, spreadsheet_url: str, results: dict) -> None:
        """
        Write validation results to a new 'Results' tab
        
        Args:
            spreadsheet_url: URL of the Google Sheet
            results: Validation results dictionary
        """
        spreadsheet = self.gc.open_by_url(spreadsheet_url)
        
        # Check if Results tab exists, delete if so
        try:
            worksheet = spreadsheet.worksheet("Results")
            spreadsheet.del_worksheet(worksheet)
        except gspread.exceptions.WorksheetNotFound:
            pass
        
        # Create new Results tab
        worksheet = spreadsheet.add_worksheet(title="Results", rows=100, cols=10)
        
        # Format results for display
        display_data = self._format_results_for_sheet(results)
        
        # Write to sheet
        worksheet.update('A1', display_data)
        
        # Format header row
        worksheet.format('A1:C1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
    
    def _format_results_for_sheet(self, results: dict) -> List[List[str]]:
        """Format results dictionary for Google Sheets display"""
        data = []
        
        # Header
        data.append(['Field', 'Value', 'Details'])
        data.append([])
        
        # Summary
        data.append(['Validation Date', results.get('validation_timestamp', ''), ''])
        data.append(['Account ID', results.get('account_id', ''), ''])
        data.append(['Overall Decision', results.get('recommendation', ''), ''])
        data.append([])
        
        # Rules
        data.append(['Rule', 'Status', 'Details'])
        
        rules = results.get('rules', {})
        rule_symbols = {
            'blue': '🟦 Lot Consistency',
            'red': '🟥 Profit Consistency',
            'orange': '🟧 Grid/Stacking',
            'yellow': '🟨 Martingale'
        }
        
        for rule_key, rule_name in rule_symbols.items():
            rule_result = rules.get(rule_key, {})
            status = rule_result.get('status', 'N/A')
            violation_count = rule_result.get('violation_count', 0)
            
            detail = f"No violations" if violation_count == 0 else f"{violation_count} violation(s)"
            
            # Add violation details if any
            if violation_count > 0 and rule_result.get('violations'):
                violations = rule_result['violations']
                if rule_key == 'red' and violations:
                    v = violations[0]
                    detail = f"Trade #{v.get('ticket')} = {v.get('contribution_pct')}% of profit"
                elif rule_key == 'yellow' and violations:
                    v = violations[0]
                    detail = f"{v.get('pair')}: Lot size increased in sequence"
            
            data.append([rule_name, status, detail])
        
        data.append([])
        data.append(['Decision Reason', results.get('decision_reason', ''), ''])
        
        return data

