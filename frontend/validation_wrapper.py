"""Wrapper to interface existing validation logic with Streamlit frontend"""

import io
import pandas as pd
from typing import Dict, Any, Tuple
from decimal import Decimal
import sys
import os

# Add the parent directory to Python path so we can import the existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_access.csv_client import CSVClient
from src.engine.processor import ValidationProcessor
from src.models.config import Config
from src.output.json_formatter import JSONFormatter


def validate_trades_csv(uploaded_file, account_size: float = 100000.0) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Validate trades from uploaded CSV file

    Args:
        uploaded_file: Streamlit uploaded file object
        account_size: Account size for payout cap calculation

    Returns:
        Tuple of (validation_results_dict, processed_dataframe)
    """
    try:
        # Save uploaded file to temporary location for processing
        import tempfile
        import os

        uploaded_file.seek(0)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write(uploaded_file.read().decode('utf-8'))
            temp_csv_path = temp_file.name

        try:
            # Initialize CSV client and config
            csv_client = CSVClient()
            config = Config()
            config.account_size = Decimal(str(account_size))

            # Use the full CSV client workflow (includes preprocessing)
            trades_df, _ = csv_client.read_csv(temp_csv_path)

            # Convert DataFrame to Trade objects
            trades = csv_client.trades_to_list(trades_df)

            # Initialize validation processor
            processor = ValidationProcessor(config)

            # Run validation
            results = processor.process(trades)

            # Create processed DataFrame with color coding
            processed_df = _add_violation_columns(trades_df, results)

            return results, processed_df

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_csv_path)
            except:
                pass  # Ignore cleanup errors

    except Exception as e:
        raise Exception(f"Validation failed: {str(e)}")


def _add_violation_columns(df: pd.DataFrame, results: Dict[str, Any]) -> pd.DataFrame:
    """
    Add violation columns to the DataFrame for color coding

    Args:
        df: Original trades DataFrame
        results: Validation results

    Returns:
        DataFrame with violation columns added
    """
    # Create a copy of the original DataFrame
    result_df = df.copy()

    # Add violation tracking columns
    result_df['violation_type'] = ''
    result_df['violation_details'] = ''
    result_df['rule_status'] = 'PASS'

    # Get rule results
    rules = results.get('rules', {})

    # For each rule, mark violations in the DataFrame
    for rule_key, rule_result in rules.items():
        violations = rule_result.get('violations', [])

        for violation in violations:
            # Find the corresponding row(s) in the DataFrame
            # This is a simplified approach - in practice you might need more sophisticated matching
            ticket = violation.get('ticket')
            if ticket and ticket in result_df['ticket'].values:
                idx = result_df[result_df['ticket'] == ticket].index[0]

                # Update violation info
                if result_df.at[idx, 'violation_type']:
                    result_df.at[idx, 'violation_type'] += f", {rule_key.upper()}"
                else:
                    result_df.at[idx, 'violation_type'] = rule_key.upper()

                if result_df.at[idx, 'violation_details']:
                    result_df.at[idx, 'violation_details'] += f"; {violation.get('message', '')}"
                else:
                    result_df.at[idx, 'violation_details'] = violation.get('message', '')

                # Set rule status based on severity
                severity = rule_result.get('severity', '').upper()
                if severity == 'BREACH':
                    result_df.at[idx, 'rule_status'] = 'BREACH'
                elif severity == 'WARNING' and result_df.at[idx, 'rule_status'] != 'BREACH':
                    result_df.at[idx, 'rule_status'] = 'WARNING'

    return result_df


def get_csv_download_content(df: pd.DataFrame, filename_prefix: str = "compliance_analysis") -> Tuple[str, str]:
    """
    Prepare CSV content for download

    Args:
        df: DataFrame to convert to CSV
        filename_prefix: Prefix for the download filename

    Returns:
        Tuple of (csv_content, filename)
    """
    # Create CSV content
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()

    # Create filename
    filename = f"{filename_prefix}_results.csv"

    return csv_content, filename


def get_validation_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key summary information from validation results

    Args:
        results: Full validation results

    Returns:
        Dictionary with key summary metrics
    """
    summary = results.get('summary', {})
    profit_calc = results.get('profit_calculation', {})

    return {
        'decision': results.get('recommendation', 'UNKNOWN'),
        'total_trades': summary.get('total_trades', 0),
        'total_profit': summary.get('total_profit', 0.0),
        'cap_applied': profit_calc.get('cap_applied', False),
        'payout_cap': profit_calc.get('payout_cap_amount', 0.0),
        'breach_count': summary.get('breach_count', 0),
        'warning_count': summary.get('warning_count', 0),
        'pass_count': summary.get('pass_count', 0)
    }
