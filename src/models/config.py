"""Configuration model for rule thresholds"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any


@dataclass
class Config:
    """Configuration parameters for validation rules"""

    # Account settings
    account_size: Decimal = field(default_factory=lambda: Decimal("100000"))  # Default $100k account
    payout_cap_percentage: Decimal = field(default_factory=lambda: Decimal("0.06"))  # 6% cap

    # Blue Rule - Lot Consistency
    blue_time_window: int = 180  # seconds (3 minutes)
    blue_lot_tolerance: Decimal = field(default_factory=lambda: Decimal("0.10"))  # 10%

    # Red Rule - Profit Consistency
    red_profit_threshold: Decimal = field(default_factory=lambda: Decimal("0.40"))  # 40%

    # Orange Rule - Grid/Stacking
    orange_simultaneous_trades: int = 3  # minimum for grid detection
    orange_breach_threshold: int = 5  # 5+ simultaneous = BREACH

    # Yellow Rule - Martingale
    # Note: yellow_lot_multiplier is kept for backward compatibility but not used.
    # The rule flags ANY lot size increase on overlapping trades, not a specific multiplier.
    yellow_lot_multiplier: Decimal = field(default_factory=lambda: Decimal("1.5"))  # Not used - kept for compatibility
    
    def __post_init__(self):
        """Validate configuration values"""
        # Convert to Decimal if needed
        if not isinstance(self.account_size, Decimal):
            self.account_size = Decimal(str(self.account_size))
        if not isinstance(self.payout_cap_percentage, Decimal):
            self.payout_cap_percentage = Decimal(str(self.payout_cap_percentage))
        if not isinstance(self.blue_lot_tolerance, Decimal):
            self.blue_lot_tolerance = Decimal(str(self.blue_lot_tolerance))
        if not isinstance(self.red_profit_threshold, Decimal):
            self.red_profit_threshold = Decimal(str(self.red_profit_threshold))
        if not isinstance(self.yellow_lot_multiplier, Decimal):
            self.yellow_lot_multiplier = Decimal(str(self.yellow_lot_multiplier))

        # Validate ranges
        if self.account_size <= 0:
            raise ValueError("account_size must be positive")
        if not (0 < self.payout_cap_percentage <= 1):
            raise ValueError("payout_cap_percentage must be between 0 and 1")
        if self.blue_time_window <= 0:
            raise ValueError("blue_time_window must be positive")
        if not (0 < self.blue_lot_tolerance < 1):
            raise ValueError("blue_lot_tolerance must be between 0 and 1")
        if not (0 < self.red_profit_threshold < 1):
            raise ValueError("red_profit_threshold must be between 0 and 1")
        if self.orange_simultaneous_trades < 2:
            raise ValueError("orange_simultaneous_trades must be >= 2")
        if self.yellow_lot_multiplier <= 1:
            raise ValueError("yellow_lot_multiplier must be > 1")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from dictionary (from Google Sheets)"""
        # Handle empty or missing config
        if not data:
            return cls()

        # Map possible column name variations
        config_kwargs = {}

        for key in [
            'account_size',
            'payout_cap_percentage',
            'blue_time_window',
            'blue_lot_tolerance',
            'red_profit_threshold',
            'orange_simultaneous_trades',
            'orange_breach_threshold',
            'yellow_lot_multiplier'
        ]:
            if key in data and data[key] is not None:
                config_kwargs[key] = data[key]

        return cls(**config_kwargs)

    @property
    def payout_cap_amount(self) -> Decimal:
        """Calculate the maximum payout amount based on account size and cap percentage"""
        return self.account_size * self.payout_cap_percentage

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'account_size': float(self.account_size),
            'payout_cap_percentage': float(self.payout_cap_percentage),
            'payout_cap_amount': float(self.payout_cap_amount),
            'blue_time_window': self.blue_time_window,
            'blue_lot_tolerance': float(self.blue_lot_tolerance),
            'red_profit_threshold': float(self.red_profit_threshold),
            'orange_simultaneous_trades': self.orange_simultaneous_trades,
            'orange_breach_threshold': self.orange_breach_threshold,
            'yellow_lot_multiplier': float(self.yellow_lot_multiplier),
        }
    
    def __repr__(self) -> str:
        return (
            f"Config(account=${self.account_size}, cap={self.payout_cap_percentage*100}%, "
            f"blue_window={self.blue_time_window}s, red_threshold={self.red_profit_threshold})"
        )

