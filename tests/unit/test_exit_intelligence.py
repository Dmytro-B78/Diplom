"""
Unit tests for exit_intelligence.py
Real file: bot_ai/strategy/meta/exit_intelligence.py

Covers:
  - evaluate_exits(): momentum flip, trend flip, regime exit, stagnation
  - _build_exit(): exit_price comes from meta_state["close"] (FIX v5.7)
  - ExitIntelState: counter resets, max_rr tracking
  - edge cases: not in LONG, missing data
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/stubs'))

pytestmark = pytest.mark.unit


# ── Mock strategy ─────────────────────────────────────────────────────────────

class MockStrategy:
    def __init__(self, position="LONG", entry_price=65000.0,
                 atr_1h=800.0, ema_fast=65500.0, ema_slow=64000.0):
        self.position    = position
        self.entry_price = entry_price
        self.atr_1h      = atr_1h
        self.ema_fast    = ema_fast
        self.ema_slow    = ema_slow
        self._exit_intel_state = None


def base_meta(close=65800.0, momentum=0.1, ema_fast=65500.0,
              mtf_bias_4h=0.5, global_regime="normal",
              atr_regime_1h="normal", atr_1h=800.0, confidence=0.15):
    """Helper: default healthy meta_state — no exit signals."""
    return {
        "close":          close,
        "momentum":       momentum,
        "ema_fast":       ema_fast,
        "mtf_bias_4h":    mtf_bias_4h,
        "global_regime":  global_regime,
        "atr_regime_1h":  atr_regime_1h,
        "atr_1h":         atr_1h,
        "confidence":      confidence,
    }


# ── Not in LONG ───────────────────────────────────────────────────────────────

class TestNotInLong:

    def test_no_position_returns_none(self):
        """evaluate_exits returns None when not in LONG."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy(position="FLAT")
        result = evaluate_exits(s, base_meta())
        assert result is None


# ── exit_price fix (Bug v5.7) ─────────────────────────────────────────────────

class TestExitPriceFix:

    def test_exit_price_is_close_not_trigger(self):
        """
        BUG v5.7: exit_price must be meta_state['close'] (actual fill),
        NOT a trigger_price computed elsewhere.
        _build_exit() uses meta_state['close'] directly.
        """
        from exit_intelligence_stub import _build_exit
        meta = base_meta(close=65950.0)
        result = _build_exit({"reason": "MOMENTUM_FLIP"}, meta)
        assert result["exit_price"] == 65950.0, (
            f"BUG: exit_price={result['exit_price']} expected 65950.0 (close)"
        )

    def test_exit_price_reflects_actual_close(self):
        """Different close prices produce different exit_price values."""
        from exit_intelligence_stub import _build_exit
        r1 = _build_exit({"reason": "TEST"}, base_meta(close=65000.0))
        r2 = _build_exit({"reason": "TEST"}, base_meta(close=66500.0))
        assert r1["exit_price"] != r2["exit_price"]

    def test_exit_signal_structure(self):
        """Exit signal has all required keys."""
        from exit_intelligence_stub import _build_exit
        result = _build_exit({"reason": "MOMENTUM_FLIP"}, base_meta())
        assert result["kind"]       == "meta_signal"
        assert result["signal"]     == "CLOSE_LONG"
        assert result["reason"]     == "MOMENTUM_FLIP"
        assert "exit_price"  in result
        assert "confidence"  in result
        assert "exit_detail" in result


# ── Momentum flip ─────────────────────────────────────────────────────────────

class TestMomentumFlip:

    def test_single_negative_bar_no_exit(self):
        """One bar below threshold — not enough, needs 2."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy()
        result = evaluate_exits(s, base_meta(momentum=-0.6))
        assert result is None

    def test_two_consecutive_negative_bars_trigger_exit(self):
        """Two consecutive bars below -0.5 → MOMENTUM_FLIP exit."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy()
        evaluate_exits(s, base_meta(momentum=-0.6))   # bar 1
        result = evaluate_exits(s, base_meta(momentum=-0.7))   # bar 2
        assert result is not None
        assert result["reason"] == "MOMENTUM_FLIP"

    def test_positive_bar_resets_counter(self):
        """Positive bar in between resets flip counter."""
        from exit_intelligence_stub import evaluate_exits, reset_exit_intel_state
        s = MockStrategy()
        evaluate_exits(s, base_meta(momentum=-0.6))   # bar 1
        evaluate_exits(s, base_meta(momentum=+0.3))   # reset
        result = evaluate_exits(s, base_meta(momentum=-0.6))   # bar 1 again
        assert result is None


# ── Trend flip ────────────────────────────────────────────────────────────────

class TestTrendFlip:

    def test_ema_fast_above_slow_no_exit(self):
        """ema_fast > ema_slow — no trend flip."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy(ema_fast=65500.0, ema_slow=64000.0)
        result = evaluate_exits(s, base_meta(ema_fast=65500.0))
        assert result is None

    def test_two_bars_ema_fast_below_slow_triggers(self):
        """ema_fast < ema_slow for 2 bars → TREND_FLIP."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy(ema_fast=63000.0, ema_slow=64000.0)
        meta = base_meta(ema_fast=63000.0)
        evaluate_exits(s, meta)          # bar 1
        result = evaluate_exits(s, meta) # bar 2
        assert result is not None
        assert result["reason"] == "TREND_FLIP"

    def test_missing_ema_slow_no_crash(self):
        """ema_slow=None — no crash, returns None."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy()
        s.ema_slow = None
        result = evaluate_exits(s, base_meta())
        assert result is None


# ── Stagnation ────────────────────────────────────────────────────────────────

class TestStagnation:

    def test_no_stagnation_before_12_bars(self):
        """Trade stagnates but < 12 bars — no exit yet."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy(entry_price=65000.0)
        meta = base_meta(close=65100.0, atr_1h=800.0)  # RR ~0.08, low
        for _ in range(10):
            result = evaluate_exits(s, meta)
        assert result is None

    def test_stagnation_triggers_after_12_bars_low_rr(self):
        """12 bars with max_rr < 0.5 → STAGNATION exit."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy(entry_price=65000.0)
        meta = base_meta(close=65100.0, atr_1h=800.0)  # RR ~0.08
        result = None
        for _ in range(12):
            result = evaluate_exits(s, meta)
        assert result is not None
        assert result["reason"] == "STAGNATION"

    def test_stagnation_disabled_when_rr_above_threshold(self):
        """If max_rr_seen >= 0.5 — stagnation exit is suppressed."""
        from exit_intelligence_stub import evaluate_exits
        s = MockStrategy(entry_price=65000.0)
        # First give a good RR bar: close=65600 → RR = 600/(800*1.5) = 0.5
        good_meta = base_meta(close=65600.0, atr_1h=800.0)
        stag_meta = base_meta(close=65100.0, atr_1h=800.0)
        evaluate_exits(s, good_meta)  # sets max_rr_seen >= 0.5
        result = None
        for _ in range(12):
            result = evaluate_exits(s, stag_meta)
        assert result is None or result["reason"] != "STAGNATION"


# ── reset ─────────────────────────────────────────────────────────────────────

class TestResetState:

    def test_reset_clears_counters(self):
        """reset_exit_intel_state() wipes all counters."""
        from exit_intelligence_stub import evaluate_exits, reset_exit_intel_state
        s = MockStrategy()
        evaluate_exits(s, base_meta(momentum=-0.6))  # starts counter
        reset_exit_intel_state(s)
        state = s._exit_intel_state
        assert state is not None
        assert state.momentum_flip_bars == 0
        assert state.bars_in_trade == 0
