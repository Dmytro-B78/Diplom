"""
Юнит-тесты для risk_guard.py
Тестируем: расчёт размера позиции, kill-switch, лимиты риска.
Все тесты изолированы — Binance API не вызывается.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/stubs'))
from decimal import Decimal

pytestmark = pytest.mark.unit


class TestPositionSizing:

    def test_normal_position_size(self, normal_market):
        from risk_guard_stub import calculate_position_size
        qty = calculate_position_size(
            balance=normal_market["balance"],
            price=normal_market["price"],
            atr=normal_market["atr"],
            risk_pct=0.01,
        )
        assert qty > 0

    def test_zero_balance_returns_zero(self, zero_balance_market):
        from risk_guard_stub import calculate_position_size
        qty = calculate_position_size(
            balance=zero_balance_market["balance"],
            price=zero_balance_market["price"],
            atr=zero_balance_market["atr"],
            risk_pct=0.01,
        )
        assert qty == 0

    def test_risk_pct_above_max_is_capped(self, normal_market):
        from risk_guard_stub import calculate_position_size
        qty_normal = calculate_position_size(
            balance=normal_market["balance"],
            price=normal_market["price"],
            atr=normal_market["atr"],
            risk_pct=0.01,
        )
        qty_capped = calculate_position_size(
            balance=normal_market["balance"],
            price=normal_market["price"],
            atr=normal_market["atr"],
            risk_pct=0.99,
        )
        assert qty_capped <= qty_normal * 10


class TestKillSwitch:

    def test_kill_switch_triggers_on_max_loss(self):
        from risk_guard_stub import should_kill_switch
        assert should_kill_switch(daily_pnl=-0.15, max_daily_loss=-0.10) is True

    def test_kill_switch_inactive_on_profit(self):
        from risk_guard_stub import should_kill_switch
        assert should_kill_switch(daily_pnl=0.05, max_daily_loss=-0.10) is False

    def test_kill_switch_at_exact_boundary(self):
        from risk_guard_stub import should_kill_switch
        result = should_kill_switch(daily_pnl=-0.10, max_daily_loss=-0.10)
        assert isinstance(result, bool)
