"""Red Rule - Profit Consistency Check"""

from typing import List, Dict
from decimal import Decimal
from datetime import datetime, date
from collections import defaultdict

from .base_rule import BaseRule, RuleResult
from ..models import Trade, Config


class RedRule(BaseRule):
    """
    Red Rule: Profit Consistency (40% Daily Rule)
    
    The 40% profit consistency rule applies to a day's trading results. 
    Traders cannot have one trading day's returns equal more than 40% of the total account profit.
    
    Example: Total profit $2000, no single day can exceed $800 (40% of $2000).
    
    Severity: BREACH (auto-reject)
    """
    
    @property
    def rule_name(self) -> str:
        return "Profit Consistency"
    
    @property
    def rule_description(self) -> str:
        return (
            f"No single trading day can contribute ≥{float(self.config.red_profit_threshold) * 100}% "
            f"of total account profit"
        )
    
    def check(self, trades: List[Trade]) -> RuleResult:
        """
        Check for daily profit concentration violations

        Only applies to 1-step-algo accounts.
        Groups trades by trading day and checks if any day exceeds 40% of total profit.
        """
        # Use capped profit for calculations
        capped_total_profit = self.config.payout_cap_amount
        return self.check_with_capped_profit(trades, capped_total_profit)

    def check_with_capped_profit(self, trades: List[Trade], capped_total_profit: Decimal) -> RuleResult:
        """
        Check for daily profit concentration violations using capped profit

        Only applies to 1-step-algo accounts.
        Groups trades by trading day and checks if any day exceeds 40% of capped total profit.
        """
        violations = []

        # Check if this is a 1-step-algo account
        if not trades:
            return RuleResult(
                rule_name=self.rule_name,
                status="PASS",
                severity=None,
                violation_count=0,
                violations=[]
            )

        account_type = trades[0].account_type

        # Rule only applies to 1-step-algo accounts
        if account_type != "1-step-algo":
            return RuleResult(
                rule_name=self.rule_name,
                status="PASS",
                severity=None,
                violation_count=0,
                violations=[]
            )

        # Use capped total profit for threshold calculations
        total_profit = float(capped_total_profit)

        # Avoid division by zero
        if total_profit <= 0:
            return RuleResult(
                rule_name=self.rule_name,
                status="PASS",
                severity=None,
                violation_count=0,
                violations=[]
            )

        # Group trades by trading day (based on close_time)
        daily_trades = defaultdict(list)
        for trade in trades:
            # Use close_time to determine trading day
            trading_day = trade.close_time.date()
            daily_trades[trading_day].append(trade)

        # Check each trading day's profit
        for trading_day, day_trades in daily_trades.items():
            daily_profit = sum(float(trade.profit) for trade in day_trades)
            daily_contribution_pct = daily_profit / total_profit

            if daily_contribution_pct >= self.config.red_profit_threshold:
                violations.append({
                    'trading_day': trading_day.isoformat(),
                    'daily_profit': daily_profit,
                    'capped_total_profit': total_profit,
                    'contribution_pct': float(daily_contribution_pct * 100),
                    'threshold_pct': float(self.config.red_profit_threshold * 100),
                    'trades_count': len(day_trades),
                    'tickets': [trade.ticket for trade in day_trades]
                })

        # Determine status
        if violations:
            status = "FAIL"
            severity = "BREACH"
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

