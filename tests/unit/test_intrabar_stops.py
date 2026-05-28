"""
Unit tests for intrabar_stops.py
Real file: bot_ai/strategy/meta/intrabar_stops.py

Covers:
  - intrabar_abs_stop(): absolute stop from entry price
  - intrabar_hwm_stop(): high-watermark drawdown stop
  - intrabar_atr_trail(): ATR trailing stop (via trail_state stub)
  - edge cases: no entry_price, price above/below stop
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/stubs'))

pytestmark = pytest.mark.unit


# ── Mock strategy object ──────────────────────────────────────────────────────

class MockStrategy:
    """Minimal strategy object matching real bot attributes."""
    def __init__(self, entry_price=65000.0, abs_loss_stop_pct=-0.03,
                 max_price_since_entry=66000.0, hwm_drawdown_stop_pct=-0.05,
                 ema_fast=64500.0, atr_1h=800.0):
        self.entry_price           = entry_price
        self.abs_loss_stop_pct     = abs_loss_stop_pct       # -3% from entry
        self.max_price_since_entry = max_price_since_entry
        self.hwm_drawdown_stop_pct = hwm_drawdown_stop_pct   # -5% from HWM
        self.ema_fast              = ema_fast
        self.ema_fast_stop_mult    = 0.5
        self.atr_1h                = atr_1h
        self.trail_state           = None
        self._exit_intel_state     = None


class MockTrailState:
    def __init__(self, stop_price, atr_mult=2.0):
        self.stop_price = stop_price
        self.atr_mult   = atr_mult


# ── intrabar_abs_stop ─────────────────────────────────────────────────────────

class TestAbsStop:

    def test_no_trigger_above_stop(self):
        """Price well above stop — no trigger."""
        from intrabar_stops_stub import intrabar_abs_stop
        s = MockStrategy(entry_price=65000.0, abs_loss_stop_pct=-0.03)
        # stop = 65000 * 0.97 = 63050
        result = intrabar_abs_stop(s, low_price=64000.0)
        assert result is None

    def test_triggers_when_price_hits_stop(self):
        """Low price touches the absolute stop — triggers."""
        from intrabar_stops_stub import intrabar_abs_stop
        s = MockStrategy(entry_price=65000.0, abs_loss_stop_pct=-0.03)
        stop_price = 65000.0 * 0.97   # 63050
        result = intrabar_abs_stop(s, low_price=63000.0)
        assert result is not None
        assert result[0] == "ABS_STOP"
        assert abs(result[1] - stop_price) < 0.01

    def test_returns_none_when_no_entry_price(self):
        """If entry_price is None — no crash, returns None."""
        from intrabar_stops_stub import intrabar_abs_stop
        s = MockStrategy()
        s.entry_price = None
        result = intrabar_abs_stop(s, low_price=60000.0)
        assert result is None

    def test_stop_price_calculation(self):
        """stop_price = entry * (1 + abs_loss_stop_pct)."""
        from intrabar_stops_stub import intrabar_abs_stop
        s = MockStrategy(entry_price=100.0, abs_loss_stop_pct=-0.05)
        # stop = 95.0, low=94 → triggers
        result = intrabar_abs_stop(s, low_price=94.0)
        assert result is not None
        assert abs(result[1] - 95.0) < 0.001


# ── intrabar_hwm_stop ─────────────────────────────────────────────────────────

class TestHwmStop:

    def test_no_trigger_above_hwm_stop(self):
        """Price above HWM stop — no trigger."""
        from intrabar_stops_stub import intrabar_hwm_stop
        s = MockStrategy(max_price_since_entry=66000.0, hwm_drawdown_stop_pct=-0.05)
        # stop = 66000 * 0.95 = 62700
        result = intrabar_hwm_stop(s, low_price=64000.0)
        assert result is None

    def test_triggers_on_hwm_drawdown(self):
        """Price falls below HWM drawdown threshold."""
        from intrabar_stops_stub import intrabar_hwm_stop
        s = MockStrategy(max_price_since_entry=66000.0, hwm_drawdown_stop_pct=-0.05)
        result = intrabar_hwm_stop(s, low_price=62000.0)
        assert result is not None
        assert result[0] == "HWM_DRAWDOWN_STOP"

    def test_returns_none_when_no_hwm(self):
        """max_price_since_entry is None — no crash."""
        from intrabar_stops_stub import intrabar_hwm_stop
        s = MockStrategy()
        s.max_price_since_entry = None
        result = intrabar_hwm_stop(s, low_price=60000.0)
        assert result is None

    def test_hwm_stop_price_value(self):
        """stop_price = max_price * (1 + hwm_drawdown_stop_pct)."""
        from intrabar_stops_stub import intrabar_hwm_stop
        s = MockStrategy(max_price_since_entry=100.0, hwm_drawdown_stop_pct=-0.10)
        result = intrabar_hwm_stop(s, low_price=88.0)
        assert result is not None
        assert abs(result[1] - 90.0) < 0.001


# ── intrabar_atr_trail ────────────────────────────────────────────────────────

class TestAtrTrail:

    def test_no_trail_state_returns_none(self):
        """No trail_state set — returns None, no crash."""
        from intrabar_stops_stub import intrabar_atr_trail
        s = MockStrategy()
        s.trail_state = None
        result = intrabar_atr_trail(s, low_price=60000.0)
        assert result is None

    def test_triggers_when_below_trail_stop(self):
        """Price hits ATR trail stop."""
        from intrabar_stops_stub import intrabar_atr_trail
        s = MockStrategy()
        s.trail_state = MockTrailState(stop_price=63000.0)
        result = intrabar_atr_trail(s, low_price=62500.0)
        assert result is not None
        assert result[0] == "ATR_TRAIL"

    def test_no_trigger_above_trail_stop(self):
        """Price above ATR trail stop — no trigger."""
        from intrabar_stops_stub import intrabar_atr_trail
        s = MockStrategy()
        s.trail_state = MockTrailState(stop_price=63000.0)
        result = intrabar_atr_trail(s, low_price=64000.0)
        assert result is None


# ── backward compat stubs ─────────────────────────────────────────────────────

class TestBackwardCompat:

    def test_compute_adaptive_trail_mult_no_state(self):
        """Returns 2.0 default when no trail_state."""
        from intrabar_stops_stub import compute_adaptive_trail_mult
        s = MockStrategy()
        s.trail_state = None
        assert compute_adaptive_trail_mult(s) == 2.0

    def test_adjust_trailing_mult_is_passthrough(self):
        """adjust_trailing_mult_by_regime is a no-op."""
        from intrabar_stops_stub import adjust_trailing_mult_by_regime
        assert adjust_trailing_mult_by_regime(2.5, "high") == 2.5
