"""Tests for Red Rule (Profit Consistency)"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.models import Trade, Config
from src.rules import RedRule


@pytest.fixture
def config():
    """Default configuration"""
    return Config()


@pytest.fixture
def base_time():
    """Base timestamp for tests"""
    return datetime(2025, 1, 15, 10, 0, 0)


def create_trade(ticket, profit, account_type="1-step-algo", base_time=None):
    """Helper to create a trade"""
    if base_time is None:
        base_time = datetime(2025, 1, 15, 10, 0, 0)
    
    return Trade(
        ticket=ticket,
        open_time=base_time,
        close_time=base_time + timedelta(hours=1),
        pair="EURUSD",
        direction="BUY",
        lot_size=Decimal("0.5"),
        profit=Decimal(str(profit)),
        balance=Decimal("5000"),
        account_type=account_type,
        account_id="ACC-001"
    )


class TestRedRule:
    """Test Red Rule - Profit Consistency"""
    
    def test_pass_no_single_trade_exceeds_threshold(self, config):
        """Test that rule passes when no trade exceeds 40% of profit"""
        trades = [
            create_trade("1", 100),  # 25%
            create_trade("2", 100),  # 25%
            create_trade("3", 100),  # 25%
            create_trade("4", 100),  # 25%
        ]
        
        rule = RedRule(config)
        result = rule.check(trades)
        
        assert result.status == "PASS"
        assert result.violation_count == 0
        assert len(result.violations) == 0
    
    def test_fail_single_trade_exceeds_threshold(self, config):
        """Test that rule fails when one trade exceeds 40% of profit"""
        trades = [
            create_trade("1", 450),  # 45% - VIOLATION
            create_trade("2", 300),  # 30%
            create_trade("3", 250),  # 25%
        ]
        
        rule = RedRule(config)
        result = rule.check(trades)
        
        assert result.status == "FAIL"
        assert result.severity == "BREACH"
        assert result.violation_count == 1
        assert result.violations[0]['ticket'] == "1"
        assert result.violations[0]['contribution_pct'] == 45.0
    
    def test_fail_exactly_at_threshold(self, config):
        """Test that rule fails at exactly 40%"""
        trades = [
            create_trade("1", 400),  # Exactly 40%
            create_trade("2", 600),  # 60%
        ]
        
        rule = RedRule(config)
        result = rule.check(trades)
        
        assert result.status == "FAIL"
        assert result.violation_count == 1
    
    def test_pass_not_applicable_to_2step_accounts(self, config):
        """Test that rule doesn't apply to non-1-step-algo accounts"""
        trades = [
            create_trade("1", 900, account_type="2-step"),  # 90% - but rule doesn't apply
            create_trade("2", 100, account_type="2-step"),  # 10%
        ]
        
        rule = RedRule(config)
        result = rule.check(trades)
        
        assert result.status == "PASS"
        assert result.violation_count == 0
    
    def test_pass_with_negative_total_profit(self, config):
        """Test handling of negative total profit"""
        trades = [
            create_trade("1", -100),
            create_trade("2", -50),
        ]
        
        rule = RedRule(config)
        result = rule.check(trades)
        
        assert result.status == "PASS"
        assert result.violation_count == 0
    
    def test_multiple_violations(self, config):
        """Test multiple trades exceeding threshold"""
        trades = [
            create_trade("1", 450),  # 45%
            create_trade("2", 450),  # 45%
            create_trade("3", 100),  # 10%
        ]
        
        rule = RedRule(config)
        result = rule.check(trades)
        
        assert result.status == "FAIL"
        assert result.violation_count == 2
        assert len(result.violations) == 2
    
    def test_custom_threshold(self):
        """Test with custom profit threshold"""
        config = Config(red_profit_threshold=Decimal("0.30"))  # 30% threshold
        
        trades = [
            create_trade("1", 350),  # 35% - exceeds 30%
            create_trade("2", 650),  # 65%
        ]
        
        rule = RedRule(config)
        result = rule.check(trades)
        
        assert result.status == "FAIL"
        assert result.violation_count == 1
        assert result.violations[0]['threshold_pct'] == 30.0

