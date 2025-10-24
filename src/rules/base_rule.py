"""Base rule interface for all compliance rules"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from ..models import Trade, Config


class RuleSeverity(Enum):
    """Severity levels for rule violations"""
    PASS = "PASS"
    WARNING = "WARNING"
    BREACH = "BREACH"


@dataclass
class RuleResult:
    """Result of a rule check"""
    
    rule_name: str
    status: str  # "PASS", "WARNING", "FAIL"
    severity: Optional[str] = None  # "PASS", "WARNING", "BREACH"
    violation_count: int = 0
    violations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'name': self.rule_name,
            'status': self.status,
            'severity': self.severity,
            'violation_count': self.violation_count,
            'violations': self.violations
        }
    
    @property
    def is_breach(self) -> bool:
        """Check if this is a breach-level violation"""
        return self.severity == "BREACH"
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning-level violation"""
        return self.severity == "WARNING"
    
    @property
    def is_pass(self) -> bool:
        """Check if rule passed"""
        return self.status == "PASS"


class BaseRule(ABC):
    """Abstract base class for all compliance rules"""
    
    def __init__(self, config: Config):
        """
        Initialize rule with configuration
        
        Args:
            config: Configuration object with rule thresholds
        """
        self.config = config
    
    @abstractmethod
    def check(self, trades: List[Trade]) -> RuleResult:
        """
        Run the rule check on a list of trades
        
        Args:
            trades: List of Trade objects to check
        
        Returns:
            RuleResult with status and any violations
        """
        pass
    
    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Return the name of this rule"""
        pass
    
    @property
    @abstractmethod
    def rule_description(self) -> str:
        """Return a description of what this rule checks"""
        pass

