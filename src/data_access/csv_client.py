"""CSV file client for reading trade data"""

import pandas as pd
from typing import Tuple, List
from pathlib import Path

from ..models import Trade, Config
from .validators import PreValidator, ValidationError


class CSVClient:
    """Client for reading trade data from CSV files"""
    
    def read_csv(self, csv_path: str, config_path: str = None) -> Tuple[pd.DataFrame, Config]:
        """
        Read trade data from CSV file
        
        Args:
            csv_path: Path to CSV file with trade data
            config_path: Optional path to config CSV file
        
        Returns:
            Tuple of (trades_df, config)
        
        Raises:
            ValidationError: If data validation fails
        """
        # Check if file exists
        if not Path(csv_path).exists():
            raise ValidationError(f"CSV file not found: {csv_path}")
        
        # Read trades CSV (try tab-separated first, then comma-separated)
        try:
            # Try tab-separated first (common in MT4/MT5 exports)
            trades_df = pd.read_csv(csv_path, sep='\t')
            # If only one column, try comma-separated
            if len(trades_df.columns) == 1:
                trades_df = pd.read_csv(csv_path, sep=',')
        except Exception as e:
            raise ValidationError(f"Failed to read CSV file: {str(e)}")
        
        if trades_df.empty:
            raise ValidationError("CSV file is empty")
        
        # Preprocess data types (includes MT4/MT5 conversion)
        trades_df = self._preprocess_trades(trades_df)
        
        # Validate after conversion
        PreValidator.validate_dataframe(trades_df)
        
        # Read config if provided
        config = self._read_config_csv(config_path) if config_path else Config()
        
        return trades_df, config
    
    def _read_config_csv(self, config_path: str) -> Config:
        """Read configuration from CSV file"""
        if not Path(config_path).exists():
            return Config()
        
        try:
            df = pd.read_csv(config_path)
        except Exception:
            return Config()
        
        if df.empty or 'Parameter' not in df.columns or 'Value' not in df.columns:
            return Config()
        
        # Convert to dict
        config_dict = {}
        for _, row in df.iterrows():
            param = str(row['Parameter']).strip()
            value = row['Value']
            if pd.notna(param) and pd.notna(value):
                config_dict[param] = value
        
        return Config.from_dict(config_dict)
    
    def _preprocess_trades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess trade data (type conversions, parsing)"""
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Remove completely empty columns (common in Google Sheets exports)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
        df = df.dropna(axis=1, how='all')  # Remove columns that are all NaN
        
        # Check if this is MT4/MT5 format and convert if needed
        if 'Position' in df.columns and 'Time' in df.columns:
            df = self._convert_mt4_format(df)
        
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
                # Clean numeric strings (remove spaces, handle European number format)
                df[numeric_field] = df[numeric_field].astype(str).str.replace(' ', '').str.replace(',', '.')
                df[numeric_field] = pd.to_numeric(df[numeric_field], errors='coerce')
        
        # Clean string fields
        for str_field in ['ticket', 'pair', 'direction', 'account_type', 'account_id']:
            if str_field in df.columns:
                df[str_field] = df[str_field].astype(str).str.strip()
        
        # Normalize direction to uppercase
        if 'direction' in df.columns:
            df['direction'] = df['direction'].str.upper()
        
        return df
    
    def _convert_mt4_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert MT4/MT5 format to our standard format
        
        Args:
            df: DataFrame in MT4/MT5 format
            
        Returns:
            DataFrame in our standard format
        """
        # Create a copy to avoid modifying original
        converted_df = df.copy()
        
        # Map MT4/MT5 columns to our standard columns
        column_mapping = {
            'Position': 'ticket',
            'Time': 'open_time', 
            'Symbol': 'pair',
            'Type': 'direction',
            'Volume': 'lot_size',
            'Profit': 'profit'
        }
        
        # Rename columns
        converted_df = converted_df.rename(columns=column_mapping)
        
        # Handle close time - MT4/MT5 has two Time columns, second one is close time
        time_columns = [col for col in converted_df.columns if 'Time' in col]
        if len(time_columns) >= 2:
            # Rename the second Time column to close_time
            converted_df = converted_df.rename(columns={time_columns[1]: 'close_time'})
        elif 'Time.1' in converted_df.columns:
            # Handle pandas auto-renaming of duplicate columns
            converted_df = converted_df.rename(columns={'Time.1': 'close_time'})
        
        # Convert direction to uppercase
        if 'direction' in converted_df.columns:
            converted_df['direction'] = converted_df['direction'].str.upper()
        
        # Add missing required columns with default values
        converted_df['balance'] = 10000.0  # Default starting balance
        converted_df['account_type'] = '1-step-algo'  # Default account type
        converted_df['account_id'] = 'MT4-001'  # Default account ID
        
        # Convert ticket to string and filter out empty rows
        if 'ticket' in converted_df.columns:
            converted_df['ticket'] = converted_df['ticket'].astype(str)
            # Remove rows with empty or NaN tickets
            converted_df = converted_df[converted_df['ticket'].notna() & (converted_df['ticket'] != 'nan') & (converted_df['ticket'] != '')]
        
        # Parse timestamps with MT4/MT5 format
        for time_col in ['open_time', 'close_time']:
            if time_col in converted_df.columns:
                converted_df[time_col] = pd.to_datetime(
                    converted_df[time_col], 
                    format='%Y.%m.%d %H:%M:%S',
                    errors='coerce'
                )
        
        return converted_df
    
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
    
    @staticmethod
    def save_results_csv(results: dict, output_path: str) -> None:
        """
        Save validation results to CSV file
        
        Args:
            results: Validation results dictionary
            output_path: Path to output CSV file
        """
        # Build summary data
        rows = []

        rows.append(['Field', 'Value', 'Details'])
        rows.append(['', '', ''])
        rows.append(['Validation Date', results.get('validation_timestamp', ''), ''])
        rows.append(['Account ID', results.get('account_id', ''), ''])
        rows.append(['Account Type', results.get('account_type', ''), ''])

        # Add profit calculation info
        pc = results.get('profit_calculation', {})
        if pc:
            rows.append(['Raw Total Profit', f"${pc.get('raw_total_profit', 0):,.2f}", ''])
            rows.append(['Payout Cap Amount', f"${pc.get('payout_cap_amount', 0):,.2f}", ''])
            rows.append(['Capped Payout Amount', f"${pc.get('capped_total_profit', 0):,.2f}", f"Cap applied: {pc.get('cap_applied', False)}"])
            rows.append(['', '', ''])

        rows.append(['Overall Decision', results.get('recommendation', ''), ''])
        rows.append(['', '', ''])
        
        # Rules
        rows.append(['Rule', 'Status', 'Details'])
        
        rules = results.get('rules', {})
        rule_names = {
            'blue': 'Lot Consistency',
            'red': 'Profit Consistency',
            'orange': 'Grid/Stacking',
            'yellow': 'Martingale'
        }
        
        for rule_key, rule_name in rule_names.items():
            rule_result = rules.get(rule_key, {})
            status = rule_result.get('status', 'N/A')
            violation_count = rule_result.get('violation_count', 0)
            
            detail = f"No violations" if violation_count == 0 else f"{violation_count} violation(s)"
            rows.append([rule_name, status, detail])
        
        rows.append(['', '', ''])
        rows.append(['Decision Reason', results.get('decision_reason', ''), ''])
        
        # Create DataFrame and save
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, header=False)
    
    @staticmethod
    def save_colored_trades_csv(trades_df: pd.DataFrame, results: dict, output_path: str) -> None:
        """
        Save trades CSV with color-coded violations and summary metrics
        
        Args:
            trades_df: Original trades DataFrame
            results: Validation results dictionary
            output_path: Path to output CSV file
        """
        # Calculate summary metrics
        total_trades = len(trades_df)
        total_lots = trades_df['lot_size'].sum()
        net_profit = trades_df['profit'].sum()

        # Calculate gross profit (profit + commission + swap)
        commission_total = trades_df.get('commission', pd.Series([0] * len(trades_df))).sum()
        swap_total = trades_df.get('swap', pd.Series([0] * len(trades_df))).sum()
        gross_profit = net_profit + abs(commission_total) + abs(swap_total)

        # Get cap information from results
        payout_cap_amount = results.get('profit_calculation', {}).get('payout_cap_amount', 0)
        cap_applied = results.get('profit_calculation', {}).get('cap_applied', False)
        capped_profit = results.get('profit_calculation', {}).get('capped_total_profit', net_profit)
        
        # Get decision info
        decision = results.get('recommendation', 'UNKNOWN')
        decision_reason = results.get('decision_reason', '')
        
        # Create summary rows with proper spacing
        summary_rows = [
            ['=== TRADING ANALYSIS SUMMARY ===', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Total Trades:', total_trades, '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Total Lots Traded:', f"{total_lots:.2f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Raw Net Profit:', f"${net_profit:,.2f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Gross Profit (Net + Commissions + Swaps):', f"${gross_profit:,.2f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Commission Total:', f"${abs(commission_total):,.2f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Swap Total:', f"${abs(swap_total):,.2f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['=== PAYOUT CALCULATION ===', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Account Size:', f"${payout_cap_amount / 0.06:,.0f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Payout Cap (6%):', f"${payout_cap_amount:,.0f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Cap Applied:', 'YES' if cap_applied else 'NO', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Capped Payout Amount:', f"${capped_profit:,.2f}", '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['=== COMPLIANCE DECISION ===', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Decision:', decision, '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['Reason:', decision_reason, '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['=== RULE VIOLATIONS ===', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ]
        
        # Add rule violation summary
        rules = results.get('rules', {})
        rule_names = {
            'blue': 'Lot Consistency',
            'red': 'Profit Consistency', 
            'orange': 'Grid/Stacking',
            'yellow': 'Martingale'
        }
        
        for rule_key, rule_name in rule_names.items():
            rule_result = rules.get(rule_key, {})
            status = rule_result.get('status', 'N/A')
            violation_count = rule_result.get('violation_count', 0)
            
            if violation_count > 0:
                summary_rows.append([f"{rule_name}:", f"{violation_count} violation(s) - {status}", '', '', '', '', '', '', '', '', '', '', '', '', ''])
            else:
                summary_rows.append([f"{rule_name}:", f"PASS", '', '', '', '', '', '', '', '', '', '', '', '', ''])
        
        # Add consistency rule metrics
        consistency_metrics = results.get('consistency_metrics', {})
        summary_rows.extend([
            ['', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['=== CONSISTENCY RULE METRICS ===', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ])
        
        # Lot size consistency range
        lot_size_range = consistency_metrics.get('lot_size_range', {})
        if lot_size_range:
            bottom = lot_size_range.get('bottom', 0)
            top = lot_size_range.get('top', 0)
            average = lot_size_range.get('average', 0)
            summary_rows.append([
                'Lot Size Consistency Range:', 
                f"{bottom:.4f} - {top:.4f} (Average: {average:.4f})", 
                '', '', '', '', '', '', '', '', '', '', '', '', ''
            ])
        
        # Profit consistency threshold
        profit_threshold = consistency_metrics.get('profit_threshold', {})
        if profit_threshold:
            threshold_pct = profit_threshold.get('threshold_percentage', 0)
            threshold_amount = profit_threshold.get('threshold_amount', 0)
            summary_rows.append([
                'Profit Consistency Threshold:', 
                f"{threshold_pct:.1f}% (${threshold_amount:,.2f})", 
                '', '', '', '', '', '', '', '', '', '', '', '', ''
            ])
        
        summary_rows.extend([
            ['', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ['=== TRADE DETAILS ===', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
        ])
        
        # Create a copy of the original trades
        colored_df = trades_df.copy()
        
        # Add violation columns
        colored_df['violation_type'] = ''
        colored_df['violation_details'] = ''
        colored_df['rule_status'] = ''
        
        # Get violations from results
        rules = results.get('rules', {})
        
        # Track which trades have violations
        violation_tickets = set()
        
        # Process each rule's violations
        for rule_key, rule_result in rules.items():
            violations = rule_result.get('violations', [])
            rule_name = {
                'blue': 'Lot Consistency',
                'red': 'Profit Consistency', 
                'orange': 'Grid/Stacking',
                'yellow': 'Martingale'
            }.get(rule_key, rule_key)
            
            for violation in violations:
                if rule_key == 'blue':
                    # Blue rule: lot consistency
                    # Handle both individual trades and cumulative stacks
                    tickets = []
                    if 'ticket' in violation:
                        tickets.append(violation['ticket'])
                    if 'tickets' in violation:
                        tickets.extend(violation['tickets'])
                    
                    for ticket in tickets:
                        if ticket:
                            violation_tickets.add(ticket)
                            mask = colored_df['ticket'] == str(ticket)
                            colored_df.loc[mask, 'violation_type'] = 'Lot Consistency'
                            
                            # Create detailed violation message
                            if violation.get('violation_type') == 'individual_trade':
                                lot_size = violation.get('lot_size', 0)
                                bottom_range = violation.get('bottom_range', 0)
                                top_range = violation.get('top_range', 0)
                                colored_df.loc[mask, 'violation_details'] = f"Lot size {lot_size} outside range {bottom_range:.1f}-{top_range:.1f}"
                            elif violation.get('violation_type') == 'cumulative_stack':
                                cumulative_lots = violation.get('cumulative_lots', 0)
                                bottom_range = violation.get('bottom_range', 0)
                                top_range = violation.get('top_range', 0)
                                colored_df.loc[mask, 'violation_details'] = f"Cumulative {cumulative_lots} outside range {bottom_range:.1f}-{top_range:.1f}"
                            
                            colored_df.loc[mask, 'rule_status'] = 'WARNING'
                
                elif rule_key == 'red':
                    # Red rule: profit consistency
                    ticket = violation.get('ticket')
                    if ticket:
                        violation_tickets.add(ticket)
                        mask = colored_df['ticket'] == str(ticket)
                        colored_df.loc[mask, 'violation_type'] = 'Profit Consistency'
                        colored_df.loc[mask, 'violation_details'] = f"Profit: {violation.get('contribution_pct', 0):.1f}% of total"
                        colored_df.loc[mask, 'rule_status'] = 'BREACH'
                
                elif rule_key == 'orange':
                    # Orange rule: grid/stacking
                    ticket = violation.get('ticket')
                    if ticket:
                        violation_tickets.add(ticket)
                        mask = colored_df['ticket'] == str(ticket)
                        colored_df.loc[mask, 'violation_type'] = 'Grid/Stacking'
                        colored_df.loc[mask, 'violation_details'] = f"Concurrent trades: {violation.get('concurrent_count', 0)}"
                        colored_df.loc[mask, 'rule_status'] = 'BREACH' if violation.get('concurrent_count', 0) >= 5 else 'WARNING'
                
                elif rule_key == 'yellow':
                    # Yellow rule: martingale
                    sequence = violation.get('sequence', [])
                    for trade_info in sequence:
                        ticket = trade_info.get('ticket')
                        if ticket:
                            violation_tickets.add(ticket)
                            mask = colored_df['ticket'] == str(ticket)
                            colored_df.loc[mask, 'violation_type'] = 'Martingale'
                            colored_df.loc[mask, 'violation_details'] = f"Lot increase: {violation.get('lot_increase_factor', 0):.1f}x"
                            colored_df.loc[mask, 'rule_status'] = 'WARNING'
        
        # Mark non-violating trades
        no_violation_mask = ~colored_df['ticket'].isin(violation_tickets)
        colored_df.loc[no_violation_mask, 'rule_status'] = 'PASS'
        
        # Reorder columns to put violation info at the end
        base_columns = ['ticket', 'open_time', 'close_time', 'pair', 'direction', 'lot_size', 'profit', 'balance', 'account_type', 'account_id']
        violation_columns = ['violation_type', 'violation_details', 'rule_status']
        
        # Ensure all base columns exist
        for col in base_columns:
            if col not in colored_df.columns:
                colored_df[col] = ''
        
        # Reorder columns
        final_columns = base_columns + violation_columns
        colored_df = colored_df[final_columns]
        
        # Convert summary rows to DataFrame
        summary_df = pd.DataFrame(summary_rows)
        
        # Combine summary and trade data
        combined_df = pd.concat([summary_df, colored_df], ignore_index=True)
        
        # Save to CSV
        combined_df.to_csv(output_path, index=False, header=False)
        
        # Print summary
        total_trades = len(colored_df)
        violation_count = len(violation_tickets)
        pass_count = total_trades - violation_count
        
        print(f"\n📊 Trade Analysis Summary:")
        print(f"   Total trades: {total_trades}")
        print(f"   ✅ Passed: {pass_count}")
        print(f"   ⚠️ Violations: {violation_count}")
        print(f"   📁 Saved to: {output_path}")
        
        if violation_count > 0:
            print(f"\n🔍 Violation Breakdown:")
            for rule_key, rule_result in rules.items():
                violations = rule_result.get('violations', [])
                if violations:
                    rule_name = {
                        'blue': '🟦 Lot Consistency',
                        'red': '🟥 Profit Consistency',
                        'orange': '🟧 Grid/Stacking', 
                        'yellow': '🟨 Martingale'
                    }.get(rule_key, rule_key)
                    print(f"   {rule_name}: {len(violations)} violation(s)")

