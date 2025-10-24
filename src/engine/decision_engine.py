"""Decision logic engine for payout approval"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

from ..rules import RuleResult


class ValidationDecision(Enum):
    """Possible validation decisions"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


@dataclass
class DecisionEngine:
    """
    Aggregates rule results and determines final decision
    
    Decision Logic:
    - APPROVE: All rules pass
    - REJECT: Any BREACH-level violation
    - REVIEW: Only WARNING-level violations
    """
    
    @staticmethod
    def make_decision(rule_results: Dict[str, RuleResult]) -> tuple[ValidationDecision, str]:
        """
        Make final decision based on rule results
        
        Args:
            rule_results: Dictionary mapping rule key to RuleResult
        
        Returns:
            Tuple of (decision, reason)
        """
        # Check for BREACH violations
        breach_rules = []
        warning_rules = []
        
        for rule_key, result in rule_results.items():
            if result.is_breach:
                breach_rules.append((rule_key, result))
            elif result.is_warning:
                warning_rules.append((rule_key, result))
        
        # Decision logic
        if breach_rules:
            # Any breach = REJECT
            decision = ValidationDecision.REJECT
            reason = DecisionEngine._build_breach_reason(breach_rules)
        elif warning_rules:
            # Only warnings = REVIEW
            decision = ValidationDecision.REVIEW
            reason = DecisionEngine._build_warning_reason(warning_rules)
        else:
            # All pass = APPROVE
            decision = ValidationDecision.APPROVE
            reason = "All compliance rules passed - no violations detected"
        
        return decision, reason
    
    @staticmethod
    def _build_breach_reason(breach_rules: List[tuple]) -> str:
        """Build reason string for BREACH violations"""
        reasons = []
        
        for rule_key, result in breach_rules:
            if rule_key == "red":
                # Red Rule - Daily profit consistency
                if result.violations:
                    v = result.violations[0]
                    reasons.append(
                        f"Red Rule violation: Trading day {v['trading_day']} contributed "
                        f"{v['contribution_pct']:.1f}% of capped profit (threshold: {v['threshold_pct']:.1f}%)"
                    )
            elif rule_key == "orange":
                # Orange Rule - Grid trading
                max_concurrent = max(v['concurrent_count'] for v in result.violations) if result.violations else 0
                reasons.append(
                    f"Orange Rule violation: Excessive grid trading detected "
                    f"({max_concurrent} simultaneous trades on same pair)"
                )
        
        return ". ".join(reasons) if reasons else "BREACH-level violations detected"
    
    @staticmethod
    def _build_warning_reason(warning_rules: List[tuple]) -> str:
        """Build reason string for WARNING violations"""
        rule_names = []
        
        for rule_key, result in warning_rules:
            rule_names.append(result.rule_name)
        
        return f"Manual review required: {', '.join(rule_names)} violations detected"
    
    @staticmethod
    def get_summary(rule_results: Dict[str, RuleResult]) -> Dict[str, int]:
        """
        Get summary counts of rule results
        
        Returns:
            Dictionary with breach_count, warning_count, pass_count
        """
        breach_count = sum(1 for r in rule_results.values() if r.is_breach)
        warning_count = sum(1 for r in rule_results.values() if r.is_warning)
        pass_count = sum(1 for r in rule_results.values() if r.is_pass)
        
        return {
            'breach_count': breach_count,
            'warning_count': warning_count,
            'pass_count': pass_count
        }

