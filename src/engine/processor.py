"""Main validation processor - orchestrates the entire validation flow"""

from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal

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
    
    def process(self, trades: List[Trade]) -> Dict[str, Any]:
        """
        Process trades and return validation results

        Args:
            trades: List of Trade objects to validate

        Returns:
            Complete validation result dictionary
        """
        # Extract metadata from trades
        trader_id = trades[0].account_id if trades else "unknown"
        account_id = trades[0].account_id if trades else "unknown"
        account_type = trades[0].account_type if trades else "unknown"

        # Calculate profit amounts
        raw_total_profit = sum(trade.profit for trade in trades)
        payout_cap_amount = self.config.payout_cap_amount
        capped_total_profit = min(raw_total_profit, payout_cap_amount)

        # Run all rules with capped profit
        rule_results = self._run_rules(trades, capped_total_profit)

        # Make decision
        decision, reason = DecisionEngine.make_decision(rule_results)

        # Get summary
        summary = DecisionEngine.get_summary(rule_results)

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

