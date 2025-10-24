"""Blue Rule - Lot Consistency Check"""

from typing import List, Dict, Tuple
from itertools import groupby
from decimal import Decimal
from datetime import timedelta

from .base_rule import BaseRule, RuleResult
from ..models import Trade, Config


class BlueRule(BaseRule):
    """
    Blue Rule: Lot Consistency
    
    Calculate average lot size = Total lots ÷ Number of trades
    Calculate range: Bottom = Average × 0.25, Top = Average × 2.00
    
    Group stacked trades within 3 minutes as one position for exposure calculation.
    Check both individual trades AND cumulative lots against the range.
    
    Severity: WARNING
    """
    
    @property
    def rule_name(self) -> str:
        return "Lot Consistency"
    
    @property
    def rule_description(self) -> str:
        return (
            "Trades must be within lot size range (Average × 0.25 to Average × 2.00). "
            "Stacked trades within 3 minutes are grouped for cumulative lot calculation."
        )
    
    def check(self, trades: List[Trade]) -> RuleResult:
        """
        Check for lot size consistency violations
        
        Algorithm:
        1. Calculate average lot size = Total lots ÷ Number of trades
        2. Calculate range: Bottom = Average × 0.25, Top = Average × 2.00
        3. Group stacked trades within 3 minutes as one position
        4. Check both individual trades AND cumulative lots against range
        """
        violations = []
        
        if not trades:
            return RuleResult(
                rule_name=self.rule_name,
                status="PASS",
                severity=None,
                violation_count=0,
                violations=[]
            )
        
        # Calculate average lot size
        total_lots = sum(float(trade.lot_size) for trade in trades)
        total_trades = len(trades)
        average_lot_size = total_lots / total_trades
        
        # Calculate range
        bottom_range = average_lot_size * 0.25
        top_range = average_lot_size * 2.00
        
        # Group trades by pair and direction, then sort by open_time
        trades_sorted = sorted(trades, key=lambda t: (t.pair, t.direction, t.open_time))
        
        for (pair, direction), group in groupby(trades_sorted, key=lambda t: (t.pair, t.direction)):
            group_list = list(group)
            
            # Group stacked trades within 3 minutes
            stacked_groups = self._group_stacked_trades(group_list, 3 * 60)  # 3 minutes in seconds
            
            # Check each stacked group
            for stack_group in stacked_groups:
                # Check individual trades in the stack
                for trade in stack_group:
                    if not (bottom_range <= float(trade.lot_size) <= top_range):
                        violations.append({
                            'ticket': trade.ticket,
                            'pair': pair,
                            'direction': direction,
                            'lot_size': float(trade.lot_size),
                            'violation_type': 'individual_trade',
                            'bottom_range': bottom_range,
                            'top_range': top_range,
                            'average_lot_size': average_lot_size
                        })
                
                # Check cumulative lots for the stack
                cumulative_lots = sum(float(trade.lot_size) for trade in stack_group)
                if not (bottom_range <= cumulative_lots <= top_range):
                    violations.append({
                        'tickets': [trade.ticket for trade in stack_group],
                        'pair': pair,
                        'direction': direction,
                        'cumulative_lots': cumulative_lots,
                        'violation_type': 'cumulative_stack',
                        'bottom_range': bottom_range,
                        'top_range': top_range,
                        'average_lot_size': average_lot_size,
                        'stack_size': len(stack_group)
                    })
        
        # Determine status
        if violations:
            status = "WARNING"
            severity = "WARNING"
        else:
            status = "PASS"
            severity = None
        
        return RuleResult(
            rule_name=self.rule_name,
            status=status,
            severity=severity,
            violation_count=len(violations),
            violations=violations
        )
    
    def _group_stacked_trades(self, trades: List[Trade], time_window_seconds: int) -> List[List[Trade]]:
        """
        Group trades that are stacked within the time window.
        
        Args:
            trades: List of trades sorted by open_time
            time_window_seconds: Time window for grouping (3 minutes = 180 seconds)
        
        Returns:
            List of trade groups, where each group contains stacked trades
        """
        if not trades:
            return []
        
        groups = []
        current_group = [trades[0]]
        
        for i in range(1, len(trades)):
            current_trade = trades[i]
            last_trade_in_group = current_group[-1]
            
            # Calculate time gap in seconds
            time_gap = (current_trade.open_time - last_trade_in_group.open_time).total_seconds()
            
            if time_gap <= time_window_seconds:
                # Add to current group (stacked)
                current_group.append(current_trade)
            else:
                # Start new group
                groups.append(current_group)
                current_group = [current_trade]
        
        # Add the last group
        groups.append(current_group)
        
        return groups

