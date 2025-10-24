"""Orange Rule - Grid/Stacking Detection"""

from typing import List, Dict
from collections import defaultdict

from .base_rule import BaseRule, RuleResult
from ..models import Trade, Config


class OrangeRule(BaseRule):
    """
    Orange Rule: Grid/Stacking Detection
    
    Grid trading is when orders are designed to be placed above and below a set price, 
    creating a grid of orders that increase or decrease incrementally along with the chart price.
    
    Having two trades open at a time is not considered grid trading. However, once there are 
    three or more positions in the trading session, with each following order stacked as the 
    original position moves into drawdown, this classifies as grid trading.
    
    Grid trading and stacking is where excessive orders are opened on one pair, in the same 
    direction all running simultaneously.
    
    Severity: BREACH (3+ simultaneous trades on same pair)
    """
    
    @property
    def rule_name(self) -> str:
        return "Grid/Stacking"
    
    @property
    def rule_description(self) -> str:
        return (
            "3 or more simultaneous trades on same pair in same direction = grid trading breach"
        )
    
    def check(self, trades: List[Trade]) -> RuleResult:
        """
        Check for grid trading violations
        
        Algorithm:
        1. Group trades by pair and direction
        2. For each trade's open_time, count concurrent trades on same pair in same direction
        3. Flag if 3+ trades are running simultaneously
        """
        violations = []
        max_concurrent = 0
        
        # Group trades by pair and direction for efficiency
        trades_by_pair_direction = defaultdict(list)
        for trade in trades:
            key = (trade.pair, trade.direction)
            trades_by_pair_direction[key].append(trade)
        
        # Check each pair/direction combination independently
        for (pair, direction), pair_trades in trades_by_pair_direction.items():
            # For each trade, count how many others are open at its open_time
            for trade in pair_trades:
                concurrent_trades = []
                
                for other_trade in pair_trades:
                    if other_trade.ticket == trade.ticket:
                        continue
                    
                    # Check if other_trade is open when current trade opens
                    if other_trade.is_open_at(trade.open_time):
                        concurrent_trades.append(other_trade.ticket)
                
                concurrent_count = len(concurrent_trades) + 1  # +1 for the trade itself
                
                # Track maximum
                max_concurrent = max(max_concurrent, concurrent_count)
                
                # Flag if 3+ trades are running simultaneously (grid trading breach)
                if concurrent_count >= 3:
                    # Only add unique violations (by trade ticket)
                    existing_tickets = [v['ticket'] for v in violations]
                    if trade.ticket not in existing_tickets:
                        all_concurrent = [trade.ticket] + concurrent_trades
                        
                        violations.append({
                            'ticket': trade.ticket,
                            'pair': pair,
                            'direction': direction,
                            'open_time': trade.open_time.isoformat(),
                            'concurrent_count': concurrent_count,
                            'concurrent_tickets': sorted(all_concurrent)
                        })
        
        # Determine status and severity
        if not violations:
            status = "PASS"
            severity = None
        else:
            status = "FAIL"
            severity = "BREACH"
        
        return RuleResult(
            rule_name=self.rule_name,
            status=status,
            severity=severity,
            violation_count=len(violations),
            violations=violations
        )

