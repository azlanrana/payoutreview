"""Google Sheets output writer"""

import gspread
from typing import Dict, Any, List


class SheetsWriter:
    """Writes validation results to Google Sheets"""
    
    def __init__(self, gspread_client: gspread.Client):
        """
        Initialize writer with gspread client
        
        Args:
            gspread_client: Authenticated gspread client
        """
        self.gc = gspread_client
    
    def write_results_tab(self, spreadsheet_url: str, results: Dict[str, Any]) -> None:
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
        
        # Format header rows
        worksheet.format('A1:C1', {
            'textFormat': {'bold': True, 'fontSize': 12},
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        worksheet.format('A7:C7', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        # Apply color coding to Results tab
        self._apply_results_colors(worksheet, results)
    
    def write_colored_trades_tab(self, spreadsheet_url: str, trades_df, results: Dict[str, Any]) -> None:
        """
        Write trades with violation highlighting to a new 'Colored Trades' tab
        
        Args:
            spreadsheet_url: URL of the Google Sheet
            trades_df: Original trades DataFrame
            results: Validation results dictionary
        """
        spreadsheet = self.gc.open_by_url(spreadsheet_url)
        
        # Check if Colored Trades tab exists, delete if so
        try:
            worksheet = spreadsheet.worksheet("Colored Trades")
            spreadsheet.del_worksheet(worksheet)
        except gspread.exceptions.WorksheetNotFound:
            pass
        
        # Create new Colored Trades tab
        worksheet = spreadsheet.add_worksheet(title="Colored Trades", rows=1000, cols=15)
        
        # Prepare colored trades data
        colored_data = self._prepare_colored_trades_data(trades_df, results)
        
        # Write to sheet
        worksheet.update('A1', colored_data)
        
        # Apply color coding to trades
        self._apply_trades_colors(worksheet, results, len(trades_df))
    
    def _format_results_for_sheet(self, results: Dict[str, Any]) -> List[List[str]]:
        """Format results dictionary for Google Sheets display"""
        data = []
        
        # Header
        data.append(['Field', 'Value', 'Details'])
        data.append([])
        
        # Summary
        data.append(['Validation Date', results.get('validation_timestamp', ''), ''])
        data.append(['Account ID', results.get('account_id', ''), ''])
        data.append(['Account Type', results.get('account_type', ''), ''])

        # Profit calculation details
        pc = results.get('profit_calculation', {})
        if pc:
            data.append(['Raw Total Profit', f"${pc.get('raw_total_profit', 0):,.2f}", ''])
            data.append(['Payout Cap Amount', f"${pc.get('payout_cap_amount', 0):,.2f}", ''])
            data.append(['Capped Payout Amount', f"${pc.get('capped_total_profit', 0):,.2f}", f"Cap applied: {pc.get('cap_applied', False)}"])
            data.append([], [])

        # Decision with emoji
        decision = results.get('recommendation', '')
        decision_emoji = {
            'APPROVE': '✅ APPROVE',
            'REJECT': '❌ REJECT',
            'REVIEW': '⚠️ REVIEW'
        }.get(decision, decision)

        data.append(['Overall Decision', decision_emoji, ''])
        data.append([])
        
        # Rules header
        data.append(['Rule', 'Status', 'Details'])
        
        rules = results.get('rules', {})
        rule_info = {
            'blue': {'name': '🟦 Lot Consistency', 'key': 'blue'},
            'red': {'name': '🟥 Profit Consistency', 'key': 'red'},
            'orange': {'name': '🟧 Grid/Stacking', 'key': 'orange'},
            'yellow': {'name': '🟨 Martingale', 'key': 'yellow'}
        }
        
        for rule_key, rule_meta in rule_info.items():
            rule_result = rules.get(rule_key, {})
            status = rule_result.get('status', 'N/A')
            violation_count = rule_result.get('violation_count', 0)
            
            # Format status with emoji
            status_emoji = {
                'PASS': '✅ PASS',
                'WARNING': '🟡 WARNING',
                'FAIL': '❌ FAIL'
            }.get(status, status)
            
            # Build detail string
            if violation_count == 0:
                detail = "No violations"
            else:
                detail = f"{violation_count} violation(s)"
                
                # Add specific details for some rules
                violations = rule_result.get('violations', [])
                if rule_key == 'red' and violations:
                    v = violations[0]
                    detail = f"Trade #{v.get('ticket')} = {v.get('contribution_pct', 0):.1f}% of profit (threshold: {v.get('threshold_pct', 0):.1f}%)"
                elif rule_key == 'orange' and violations:
                    max_concurrent = max(v.get('concurrent_count', 0) for v in violations)
                    detail = f"{max_concurrent} simultaneous trades detected on same pair"
                elif rule_key == 'blue' and violations:
                    detail = f"{violation_count} lot size inconsistencies detected"
                elif rule_key == 'yellow' and violations:
                    detail = f"{violation_count} martingale sequences detected"
            
            data.append([rule_meta['name'], status_emoji, detail])
        
        data.append([])
        data.append(['Decision Reason', results.get('decision_reason', ''), ''])
        
        data.append([])
        data.append(['Summary', '', ''])
        summary = results.get('summary', {})
        data.append(['Total Trades', str(summary.get('total_trades', 0)), ''])
        data.append(['Total Profit (Capped)', f"${summary.get('total_profit', 0):.2f}", ''])
        data.append(['Breaches', str(summary.get('breach_count', 0)), ''])
        data.append(['Warnings', str(summary.get('warning_count', 0)), ''])
        
        return data
    
    def _apply_results_colors(self, worksheet, results: Dict[str, Any]) -> None:
        """Apply color coding to Results tab"""
        # Color code rule results (rows 8-11)
        rules = results.get('rules', {})
        rule_row = 8
        
        for rule_key in ['blue', 'red', 'orange', 'yellow']:
            rule_result = rules.get(rule_key, {})
            status = rule_result.get('status', 'N/A')
            
            # Determine color based on status
            if status == 'PASS':
                color = {'red': 0.8, 'green': 1.0, 'blue': 0.8}  # Light green
            elif status == 'WARNING':
                color = {'red': 1.0, 'green': 1.0, 'blue': 0.8}  # Light yellow
            elif status == 'FAIL':
                color = {'red': 1.0, 'green': 0.8, 'blue': 0.8}  # Light red
            else:
                color = {'red': 0.9, 'green': 0.9, 'blue': 0.9}  # Light gray
            
            # Apply color to the entire row
            worksheet.format(f'A{rule_row}:C{rule_row}', {
                'backgroundColor': color
            })
            
            rule_row += 1
        
        # Color the overall decision
        decision = results.get('recommendation', '')
        decision_row = 4  # Overall Decision row
        
        if decision == 'APPROVE':
            decision_color = {'red': 0.8, 'green': 1.0, 'blue': 0.8}  # Green
        elif decision == 'REJECT':
            decision_color = {'red': 1.0, 'green': 0.8, 'blue': 0.8}  # Red
        elif decision == 'REVIEW':
            decision_color = {'red': 1.0, 'green': 1.0, 'blue': 0.8}  # Yellow
        else:
            decision_color = {'red': 0.9, 'green': 0.9, 'blue': 0.9}  # Gray
        
        worksheet.format(f'A{decision_row}:C{decision_row}', {
            'backgroundColor': decision_color,
            'textFormat': {'bold': True, 'fontSize': 12}
        })
    
    def _prepare_colored_trades_data(self, trades_df, results: Dict[str, Any]) -> List[List[str]]:
        """Prepare trades data with violation highlighting"""
        import pandas as pd
        
        # Create a copy of the original trades
        colored_df = trades_df.copy()
        
        # Add violation columns
        colored_df['violation_type'] = ''
        colored_df['violation_details'] = ''
        colored_df['rule_status'] = ''
        
        # Get violations from results
        rules = results.get('rules', {})
        violation_tickets = set()
        
        # Process each rule's violations
        for rule_key, rule_result in rules.items():
            violations = rule_result.get('violations', [])
            
            for violation in violations:
                if rule_key == 'blue':
                    # Blue rule: lot consistency
                    tickets = [violation.get('trade_1'), violation.get('trade_2')]
                    for ticket in tickets:
                        if ticket:
                            violation_tickets.add(ticket)
                            mask = colored_df['ticket'] == str(ticket)
                            colored_df.loc[mask, 'violation_type'] = '🟦 Lot Consistency'
                            colored_df.loc[mask, 'violation_details'] = f"Lot diff: {violation.get('lot_difference_pct', 0)*100:.1f}%"
                            colored_df.loc[mask, 'rule_status'] = 'WARNING'
                
                elif rule_key == 'red':
                    # Red rule: profit consistency
                    ticket = violation.get('ticket')
                    if ticket:
                        violation_tickets.add(ticket)
                        mask = colored_df['ticket'] == str(ticket)
                        colored_df.loc[mask, 'violation_type'] = '🟥 Profit Consistency'
                        colored_df.loc[mask, 'violation_details'] = f"Profit: {violation.get('contribution_pct', 0):.1f}% of total"
                        colored_df.loc[mask, 'rule_status'] = 'BREACH'
                
                elif rule_key == 'orange':
                    # Orange rule: grid/stacking
                    ticket = violation.get('ticket')
                    if ticket:
                        violation_tickets.add(ticket)
                        mask = colored_df['ticket'] == str(ticket)
                        colored_df.loc[mask, 'violation_type'] = '🟧 Grid/Stacking'
                        colored_df.loc[mask, 'violation_details'] = f"Concurrent: {violation.get('concurrent_count', 0)}"
                        colored_df.loc[mask, 'rule_status'] = 'BREACH' if violation.get('concurrent_count', 0) >= 5 else 'WARNING'
                
                elif rule_key == 'yellow':
                    # Yellow rule: martingale
                    sequence = violation.get('sequence', [])
                    for trade_info in sequence:
                        ticket = trade_info.get('ticket')
                        if ticket:
                            violation_tickets.add(ticket)
                            mask = colored_df['ticket'] == str(ticket)
                            colored_df.loc[mask, 'violation_type'] = '🟨 Martingale'
                            colored_df.loc[mask, 'violation_details'] = f"Lot increase: {violation.get('lot_increase_factor', 0):.1f}x"
                            colored_df.loc[mask, 'rule_status'] = 'WARNING'
        
        # Mark non-violating trades
        no_violation_mask = ~colored_df['ticket'].isin(violation_tickets)
        colored_df.loc[no_violation_mask, 'rule_status'] = '✅ PASS'
        
        # Reorder columns
        base_columns = ['ticket', 'open_time', 'close_time', 'pair', 'direction', 'lot_size', 'profit', 'balance', 'account_type', 'account_id']
        violation_columns = ['violation_type', 'violation_details', 'rule_status']
        
        # Ensure all base columns exist
        for col in base_columns:
            if col not in colored_df.columns:
                colored_df[col] = ''
        
        # Reorder columns
        final_columns = base_columns + violation_columns
        colored_df = colored_df[final_columns]
        
        # Convert to list of lists for Google Sheets
        data = [colored_df.columns.tolist()] + colored_df.values.tolist()
        return data
    
    def _apply_trades_colors(self, worksheet, results: Dict[str, Any], num_trades: int) -> None:
        """Apply color coding to trades tab"""
        # Header row formatting
        worksheet.format('A1:M1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # Color code each trade row based on rule_status
        for row in range(2, num_trades + 2):  # Start from row 2 (after header)
            # Get the rule_status from column M (13th column)
            try:
                status_cell = f'M{row}'
                status_value = worksheet.acell(status_cell).value
                
                # Apply conditional formatting based on status
                if 'PASS' in str(status_value):
                    # Green for PASS
                    worksheet.format(f'A{row}:M{row}', {
                        'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}
                    })
                elif 'WARNING' in str(status_value):
                    # Yellow for WARNING
                    worksheet.format(f'A{row}:M{row}', {
                        'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.8}
                    })
                elif 'BREACH' in str(status_value):
                    # Red for BREACH
                    worksheet.format(f'A{row}:M{row}', {
                        'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                    })
            except Exception:
                # Skip if cell doesn't exist or can't be read
                continue

