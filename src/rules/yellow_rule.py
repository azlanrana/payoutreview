"""Yellow Rule - Martingale Detection"""

from typing import List, Dict
from collections import defaultdict
from itertools import groupby

from .base_rule import BaseRule, RuleResult
from ..models import Trade, Config


class YellowRule(BaseRule):
    """
    Yellow Rule: Martingale Detection
    
    Martingale is a methodology that seeks to amplify the chance of recovering from a losing streak 
    by constantly increasing the lot size of new trades to circumvent any loss taken.
    
    Any increase in lot size on a subsequent position, on the same pair and in the same direction 
    as the original trade, with the trades running together is viewed as a martingale breach.
    
    Severity: WARNING
    """
    
    @property
    def rule_name(self) -> str:
        return "Martingale"
    
    @property
    def rule_description(self) -> str:
        return (
            "Any increase in lot size on overlapping trades (same pair and direction) "
            "indicates martingale behavior"
        )
    
    def check(self, trades: List[Trade]) -> RuleResult:
        """
        Check for martingale trading violations
        
        Algorithm:
        1. Group trades by pair and direction
        2. Sort by open_time
        3. Find overlapping trades
        4. Flag if ANY later trade has lot_size > earlier trade
        """
        violations = []
        
        # Group trades by pair and direction
        trades_sorted = sorted(trades, key=lambda t: (t.pair, t.direction, t.open_time))
        
        for (pair, direction), group in groupby(trades_sorted, key=lambda t: (t.pair, t.direction)):
            group_list = list(group)
            
            # Check all pairs of trades for overlap and lot increase
            for i in range(len(group_list)):
                for j in range(i + 1, len(group_list)):
                    trade_a = group_list[i]
                    trade_b = group_list[j]
                    
                    # Check if trades overlap (B opens while A is still open)
                    if trade_b.open_time < trade_a.close_time:
                        # Check if lot size increased (ANY increase = violation)
                        if trade_b.lot_size > trade_a.lot_size:
                            # Found a martingale sequence
                            violations.append({
                                'sequence': [
                                    {
                                        'ticket': trade_a.ticket,
                                        'lot_size': float(trade_a.lot_size),
                                        'open_time': trade_a.open_time.isoformat(),
                                        'close_time': trade_a.close_time.isoformat()
                                    },
                                    {
                                        'ticket': trade_b.ticket,
                                        'lot_size': float(trade_b.lot_size),
                                        'open_time': trade_b.open_time.isoformat(),
                                        'close_time': trade_b.close_time.isoformat()
                                    }
                                ],
                                'pair': pair,
                                'direction': direction,
                                'lot_increase': float(trade_b.lot_size - trade_a.lot_size),
                                'lot_increase_factor': float(trade_b.lot_size / trade_a.lot_size)
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

