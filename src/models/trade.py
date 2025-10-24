"""Trade data model"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Trade:
    """Represents a single trade from the trader's history"""
    
    ticket: str
    open_time: datetime
    close_time: datetime
    pair: str
    direction: str  # "BUY" or "SELL"
    lot_size: Decimal
    profit: Decimal
    balance: Decimal
    account_type: str  # "1-step-algo", "2-step", "evaluation"
    account_id: str
    
    def __post_init__(self):
        """Validate trade data after initialization"""
        # Convert to Decimal if not already
        if not isinstance(self.lot_size, Decimal):
            self.lot_size = Decimal(str(self.lot_size))
        if not isinstance(self.profit, Decimal):
            self.profit = Decimal(str(self.profit))
        if not isinstance(self.balance, Decimal):
            self.balance = Decimal(str(self.balance))
        
        # Normalize direction to uppercase
        self.direction = self.direction.upper()
        
        # Validate direction
        if self.direction not in ("BUY", "SELL"):
            raise ValueError(f"Invalid direction: {self.direction}. Must be 'BUY' or 'SELL'")
        
        # Validate account type
        valid_account_types = ["1-step-algo", "2-step", "evaluation"]
        if self.account_type not in valid_account_types:
            raise ValueError(
                f"Invalid account_type: {self.account_type}. "
                f"Must be one of {valid_account_types}"
            )
        
        # Validate timestamps
        if self.close_time <= self.open_time:
            raise ValueError(
                f"Invalid trade times: close_time ({self.close_time}) "
                f"must be after open_time ({self.open_time})"
            )
        
        # Validate lot size
        if self.lot_size <= 0:
            raise ValueError(f"Invalid lot_size: {self.lot_size}. Must be > 0")
    
    @property
    def duration_seconds(self) -> float:
        """Calculate trade duration in seconds"""
        return (self.close_time - self.open_time).total_seconds()
    
    def is_overlapping(self, other: 'Trade') -> bool:
        """Check if this trade overlaps with another trade"""
        return (
            self.open_time < other.close_time and
            other.open_time < self.close_time
        )
    
    def is_open_at(self, timestamp: datetime) -> bool:
        """Check if trade was open at given timestamp"""
        return self.open_time <= timestamp < self.close_time
    
    def __repr__(self) -> str:
        return (
            f"Trade(ticket={self.ticket}, pair={self.pair}, "
            f"direction={self.direction}, lot={self.lot_size}, "
            f"profit={self.profit})"
        )

