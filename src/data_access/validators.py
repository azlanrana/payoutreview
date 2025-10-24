"""Pre-validation module for trade data"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from dateutil import parser


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class PreValidator:
    """Pre-validation checks for trade data (fail-fast approach)"""
    
    REQUIRED_FIELDS = [
        'ticket',
        'open_time',
        'close_time',
        'pair',
        'direction',
        'lot_size',
        'profit',
        'balance',
        'account_type',
        'account_id'
    ]
    
    VALID_ACCOUNT_TYPES = ['1-step-algo', '2-step', 'evaluation']
    VALID_DIRECTIONS = ['BUY', 'SELL']
    
    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame) -> None:
        """
        Validate trade DataFrame before processing
        Raises ValidationError if any checks fail
        """
        if df.empty:
            raise ValidationError("Trade data is empty")
        
        # Check required fields
        cls._check_required_fields(df)
        
        # Check for duplicate tickets
        cls._check_duplicate_tickets(df)
        
        # Validate data types and values
        cls._validate_timestamps(df)
        cls._validate_numeric_fields(df)
        cls._validate_enum_fields(df)
        cls._validate_business_logic(df)
    
    @classmethod
    def _check_required_fields(cls, df: pd.DataFrame) -> None:
        """Ensure all required fields are present"""
        missing_fields = [field for field in cls.REQUIRED_FIELDS if field not in df.columns]
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}. "
                f"Required fields: {', '.join(cls.REQUIRED_FIELDS)}"
            )
    
    @classmethod
    def _check_duplicate_tickets(cls, df: pd.DataFrame) -> None:
        """Check for duplicate ticket IDs"""
        duplicates = df[df['ticket'].duplicated()]
        if not duplicates.empty:
            duplicate_tickets = duplicates['ticket'].tolist()
            raise ValidationError(
                f"Duplicate ticket IDs found: {', '.join(map(str, duplicate_tickets))}"
            )
    
    @classmethod
    def _validate_timestamps(cls, df: pd.DataFrame) -> None:
        """Validate timestamp fields"""
        # Check for null timestamps
        for field in ['open_time', 'close_time']:
            if df[field].isnull().any():
                null_count = df[field].isnull().sum()
                raise ValidationError(f"Found {null_count} null values in {field}")
        
        # Check if timestamps are parseable (already converted in sheets_client)
        for field in ['open_time', 'close_time']:
            if not pd.api.types.is_datetime64_any_dtype(df[field]):
                raise ValidationError(
                    f"{field} must be datetime type, got {df[field].dtype}"
                )
    
    @classmethod
    def _validate_numeric_fields(cls, df: pd.DataFrame) -> None:
        """Validate numeric fields"""
        numeric_fields = ['lot_size', 'profit', 'balance']
        
        for field in numeric_fields:
            # Check for nulls
            if df[field].isnull().any():
                null_count = df[field].isnull().sum()
                raise ValidationError(f"Found {null_count} null values in {field}")
            
            # Check if numeric
            if not pd.api.types.is_numeric_dtype(df[field]):
                raise ValidationError(f"{field} must be numeric, got {df[field].dtype}")
        
        # Validate lot_size > 0
        invalid_lots = df[df['lot_size'] <= 0]
        if not invalid_lots.empty:
            tickets = invalid_lots['ticket'].tolist()
            raise ValidationError(
                f"lot_size must be > 0. Invalid trades: {', '.join(map(str, tickets))}"
            )
    
    @classmethod
    def _validate_enum_fields(cls, df: pd.DataFrame) -> None:
        """Validate enum-type fields (direction, account_type)"""
        # Validate direction
        df['direction'] = df['direction'].str.upper()
        invalid_directions = df[~df['direction'].isin(cls.VALID_DIRECTIONS)]
        if not invalid_directions.empty:
            invalid_values = invalid_directions['direction'].unique().tolist()
            raise ValidationError(
                f"Invalid direction values: {', '.join(map(str, invalid_values))}. "
                f"Must be one of: {', '.join(cls.VALID_DIRECTIONS)}"
            )
        
        # Validate account_type
        invalid_account_types = df[~df['account_type'].isin(cls.VALID_ACCOUNT_TYPES)]
        if not invalid_account_types.empty:
            invalid_values = invalid_account_types['account_type'].unique().tolist()
            raise ValidationError(
                f"Invalid account_type values: {', '.join(map(str, invalid_values))}. "
                f"Must be one of: {', '.join(cls.VALID_ACCOUNT_TYPES)}"
            )
    
    @classmethod
    def _validate_business_logic(cls, df: pd.DataFrame) -> None:
        """Validate business logic rules"""
        # Ensure close_time > open_time
        invalid_times = df[df['close_time'] <= df['open_time']]
        if not invalid_times.empty:
            tickets = invalid_times['ticket'].tolist()
            raise ValidationError(
                f"close_time must be after open_time. Invalid trades: {', '.join(map(str, tickets))}"
            )
        
        # Ensure account_id is not empty
        empty_accounts = df[df['account_id'].isna() | (df['account_id'].astype(str).str.strip() == '')]
        if not empty_accounts.empty:
            tickets = empty_accounts['ticket'].tolist()
            raise ValidationError(
                f"account_id cannot be empty. Invalid trades: {', '.join(map(str, tickets))}"
            )
    
    @classmethod
    def get_validation_summary(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Get validation summary without raising errors"""
        summary = {
            'total_rows': len(df),
            'fields_present': df.columns.tolist(),
            'missing_fields': [f for f in cls.REQUIRED_FIELDS if f not in df.columns],
            'duplicate_tickets': df[df['ticket'].duplicated()]['ticket'].tolist(),
            'validation_passed': False,
            'errors': []
        }
        
        try:
            cls.validate_dataframe(df)
            summary['validation_passed'] = True
        except ValidationError as e:
            summary['errors'].append(str(e))
        
        return summary

