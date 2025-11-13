"""Main validation processor - orchestrates the entire validation flow"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import pandas as pd

from ..models import Trade, Config
from ..rules import BlueRule, RedRule, OrangeRule, YellowRule, RuleResult
from .decision_engine import DecisionEngine, ValidationDecision


class ValidationProcessor:
    """
    Main processor that orchestrates the validation flow
    
    Flow:
    1. Receive trades and config
    2. Run all rules
    3. Aggregate results
    4. Make decision
    5. Generate output
    """
    
    def __init__(self, config: Config):
        """
        Initialize processor with configuration
        
        Args:
            config: Configuration object with rule thresholds
        """
        self.config = config
        
        # Initialize rules
        self.rules = {
            'blue': BlueRule(config),
            'red': RedRule(config),
            'orange': OrangeRule(config),
            'yellow': YellowRule(config)
        }
    
    def process(self, trades: List[Trade], trades_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Process trades and return validation results

        Args:
            trades: List of Trade objects to validate
            trades_df: Optional DataFrame with trade data (used to calculate gross profit including swaps/commissions)

        Returns:
            Complete validation result dictionary
        """
        # Extract metadata from trades
        trader_id = trades[0].account_id if trades else "unknown"
        account_id = trades[0].account_id if trades else "unknown"
        account_type = trades[0].account_type if trades else "unknown"

        # Calculate profit amounts
        # Start with net profit from trades
        raw_total_profit = sum(trade.profit for trade in trades)
        
        # If DataFrame is provided, calculate gross profit (including swaps/commissions)
        if trades_df is not None:
            commission_total = trades_df.get('commission', pd.Series([0] * len(trades_df))).sum()
            swap_total = trades_df.get('swap', pd.Series([0] * len(trades_df))).sum()
            # Gross profit = net profit + commissions + swaps
            # Commissions and swaps are typically stored as negative values (costs),
            # so we use abs() to add them back to get gross profit
            raw_total_profit = raw_total_profit + abs(commission_total) + abs(swap_total)
        
        payout_cap_amount = self.config.payout_cap_amount
        capped_total_profit = min(raw_total_profit, payout_cap_amount)

        # Run all rules with capped profit
        rule_results = self._run_rules(trades, capped_total_profit)

        # Make decision
        decision, reason = DecisionEngine.make_decision(rule_results)

        # Get summary
        summary = DecisionEngine.get_summary(rule_results)

        # Calculate consistency rule metrics for export
        consistency_metrics = {}
        
        # Blue Rule: Lot size consistency range
        blue_result = rule_results.get('blue')
        if blue_result and blue_result.violations:
            # Extract range from first violation (all violations have same range)
            first_violation = blue_result.violations[0]
            if 'bottom_range' in first_violation and 'top_range' in first_violation:
                consistency_metrics['lot_size_range'] = {
                    'bottom': float(first_violation['bottom_range']),
                    'top': float(first_violation['top_range']),
                    'average': float(first_violation.get('average_lot_size', 0))
                }
        else:
            # Calculate range even if no violations (for display purposes)
            if trades:
                total_lots = sum(float(trade.lot_size) for trade in trades)
                total_trades = len(trades)
                average_lot_size = total_lots / total_trades if total_trades > 0 else 0
                consistency_metrics['lot_size_range'] = {
                    'bottom': float(average_lot_size * 0.25),
                    'top': float(average_lot_size * 2.00),
                    'average': float(average_lot_size)
                }
        
        # Red Rule: Profit consistency threshold
        consistency_metrics['profit_threshold'] = {
            'threshold_percentage': float(self.config.red_profit_threshold * 100),
            'threshold_amount': float(capped_total_profit * self.config.red_profit_threshold)
        }
        
        # Build complete result
        result = {
            'trader_id': trader_id,
            'account_id': account_id,
            'account_type': account_type,
            'validation_timestamp': datetime.utcnow().isoformat() + 'Z',
            'overall_status': decision.value,
            'recommendation': decision.value,
            'decision_reason': reason,
            'profit_calculation': {
                'raw_total_profit': float(raw_total_profit),
                'payout_cap_amount': float(payout_cap_amount),
                'capped_total_profit': float(capped_total_profit),
                'cap_applied': raw_total_profit > payout_cap_amount
            },
            'rules': {
                key: result.to_dict()
                for key, result in rule_results.items()
            },
            'consistency_metrics': consistency_metrics,
            'summary': {
                'total_trades': len(trades),
                'total_profit': float(capped_total_profit),  # Use capped profit for display
                **summary
            }
        }

        return result
    
    def _run_rules(self, trades: List[Trade], capped_total_profit: Decimal) -> Dict[str, RuleResult]:
        """
        Run all rules on the trades

        Args:
            trades: List of Trade objects
            capped_total_profit: The capped total profit amount for rule calculations

        Returns:
            Dictionary mapping rule key to RuleResult
        """
        results = {}

        for rule_key, rule in self.rules.items():
            try:
                # Pass capped profit to rules that need it (like Red Rule)
                if hasattr(rule, 'check_with_capped_profit'):
                    result = rule.check_with_capped_profit(trades, capped_total_profit)
                else:
                    result = rule.check(trades)
                results[rule_key] = result
            except Exception as e:
                # If a rule fails, create error result
                results[rule_key] = RuleResult(
                    rule_name=rule.rule_name,
                    status="ERROR",
                    severity=None,
                    violation_count=0,
                    violations=[{'error': str(e)}]
                )

        return results

