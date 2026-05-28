# ================================================================
# File: tests/unit/test_entry_engine.py
# Entry Engine v2.0 — unit tests (15 total)
# Key coverage: BUG-3 ABS_STOP cooldown, re-entry, breakout path.
# ================================================================
import pytest
from src.stubs.entry_engine_stub import compute_entry_signal


class MockStrategy:
    def __init__(
        self,
        position="NONE",
        last_exit_reason=None,
        last_exit_bar_index=None,
        bar_index=100,
    ):
        self.position            = position
        self.last_exit_reason    = last_exit_reason
        self.last_exit_bar_index = last_exit_bar_index
        self.bar_index           = bar_index


BASE_META = {
    "close":          50000.0,
    "confidence":     0.30,
    "atr_regime_1h":  "normal",
    "momentum":       0.15,
    "slope":          0.05,
    "trend_strength": 0.20,
    "mtf_bias_4h":    0.20,
    "mtf_4h_aligned": True,
    "daily_gate":     True,
}

_stage1_pass = lambda ms: (True,  {"reason": "stage1_pass"})
_stage1_fail = lambda ms: (False, {"reason": "low_confidence"})
_stage2_pass = lambda ms, ps: (True,  {"reason": "stage2_pass"})
_stage2_fail = lambda ms, ps: (False, {"reason": "stage2_fail"})
_bo_signal   = lambda s, ms: {"reason": "BO_HIGH", "atr_1h": 300.0, "bars_since_bo": 1}
_bo_none     = lambda s, ms: None


def _run(strategy=None, meta=None, **kw):
    if strategy is None:
        strategy = MockStrategy()
    if meta is None:
        meta = dict(BASE_META)
    dbg = {}
    result = compute_entry_signal(strategy, meta, dbg, **kw)
    return result, dbg


class TestAlreadyInLong:
    def test_long_position_returns_none(self):
        result, _ = _run(strategy=MockStrategy(position="LONG"))
        assert result is None


class TestAbsStopCooldown:
    def _abs_strategy(self, bars_since):
        return MockStrategy(
            last_exit_reason="ABS_STOP",
            last_exit_bar_index=100 - bars_since,
            bar_index=100,
        )

    def test_cooldown_active_at_1_bar(self):
        result, dbg = _run(strategy=self._abs_strategy(1))
        assert result is None
        assert dbg["abs_stop_cooldown"]["active"] is True

    def test_cooldown_active_at_7_bars(self):
        result, dbg = _run(strategy=self._abs_strategy(7))
        assert result is None
        assert dbg["abs_stop_cooldown"]["bars_remaining"] == 1

    def test_cooldown_inactive_at_8_bars(self):
        result, dbg = _run(
            strategy=self._abs_strategy(8),
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_signal,
        )
        assert dbg["abs_stop_cooldown"]["active"] is False
        assert result is not None
        assert result["signal"] == "OPEN_LONG"

    def test_cooldown_debug_bars_remaining(self):
        result, dbg = _run(strategy=self._abs_strategy(3))
        assert dbg["abs_stop_cooldown"]["bars_remaining"] == 5


class TestReEntry:
    def _ema_strategy(self, bars_since=5):
        return MockStrategy(
            last_exit_reason="EMA_STOP",
            last_exit_bar_index=100 - bars_since,
            bar_index=100,
        )

    def test_reentry_within_window_stage2_pass(self):
        result, dbg = _run(
            strategy=self._ema_strategy(5),
            stage2_fn=_stage2_pass,
        )
        assert result is not None
        assert result["reason"] == "REENTRY_EMA_STOP"
        assert result["signal"] == "OPEN_LONG"

    def test_reentry_outside_window_goes_to_breakout(self):
        result, dbg = _run(
            strategy=self._ema_strategy(13),
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_signal,
        )
        assert result["reason"] == "BO_HIGH"

    def test_reentry_stage2_fail_goes_to_breakout(self):
        result, dbg = _run(
            strategy=self._ema_strategy(5),
            stage2_fn=_stage2_fail,
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_signal,
        )
        assert result["reason"] == "BO_HIGH"

    def test_reentry_requires_positive_momentum(self):
        meta = dict(BASE_META, momentum=-0.01)
        result, dbg = _run(
            strategy=self._ema_strategy(5),
            meta=meta,
            stage2_fn=_stage2_pass,
            stage1_fn=_stage1_fail,
            breakout_fn=_bo_none,
        )
        assert result is None
        assert dbg["reentry_candidate"]["reentry_ok"] is False


class TestBreakoutPath:
    def _fresh_strategy(self):
        return MockStrategy(last_exit_reason=None, last_exit_bar_index=None)

    def test_stage1_fail_returns_none(self):
        result, _ = _run(
            strategy=self._fresh_strategy(),
            stage1_fn=_stage1_fail,
        )
        assert result is None

    def test_no_breakout_returns_none(self):
        result, _ = _run(
            strategy=self._fresh_strategy(),
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_none,
        )
        assert result is None

    def test_breakout_success_returns_signal(self):
        result, _ = _run(
            strategy=self._fresh_strategy(),
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_signal,
        )
        assert result is not None
        assert result["signal"] == "OPEN_LONG"
        assert result["reason"] == "BO_HIGH"

    def test_breakout_signal_contains_required_keys(self):
        result, _ = _run(
            strategy=self._fresh_strategy(),
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_signal,
        )
        for key in ("kind", "signal", "reason", "confidence", "_entry_price"):
            assert key in result, f"Missing key: {key}"


class TestNoBarsContext:
    def test_no_exit_index_skips_cooldown(self):
        strategy = MockStrategy(
            last_exit_reason="ABS_STOP",
            last_exit_bar_index=None,
        )
        result, dbg = _run(
            strategy=strategy,
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_signal,
        )
        assert dbg["abs_stop_cooldown"]["active"] is False
        assert result is not None

    def test_no_exit_index_skips_reentry(self):
        strategy = MockStrategy(
            last_exit_reason="EMA_STOP",
            last_exit_bar_index=None,
        )
        result, dbg = _run(
            strategy=strategy,
            stage2_fn=_stage2_pass,
            stage1_fn=_stage1_pass,
            breakout_fn=_bo_signal,
        )
        assert dbg["reentry_candidate"]["reentry_ok"] is False
